"""Stage 1 — vector input x.

P/S/E 5-slot embeddings + KG mean pooling + CPC subclass, then
block z-score → L2 → weights → PCA. Contract: docs/02_stage_specs.md,
docs/03_locked_spec.md. All numbers come from config.py.
"""

from __future__ import annotations

# Import order: scipy / sklearn before torch (D4). Opposite order breaks
# scipy extensions with CXXABI_1.3.15 on this machine.
import json
import sys

import numpy as np
from sklearn.decomposition import PCA, TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer

import config as cfg
from lib import (
    build_cpc_block,
    corpus_hash,
    ensure_out,
    index_frame,
    l2_rows,
    load_kg_assets,
    load_patents,
    pca_block_contributions,
    pool_kg,
    sha256_array,
    write_json,
    zscore_block,
)


def _resolve_device() -> str:
    try:
        import torch
    except (OSError, ImportError) as exc:
        raise SystemExit(
            "torch 를 import 할 수 없다. conda 환경 scenario-space 의 CUDA/cuDNN 설치를 확인하라. "
            f"원인: {exc}"
        ) from exc

    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def encode_sentence_transformer(patents: list[dict]) -> tuple[np.ndarray, dict]:
    from sentence_transformers import SentenceTransformer

    device = _resolve_device()
    try:
        model = SentenceTransformer(cfg.ST_MODEL, device=device)
        used = cfg.ST_MODEL
    except Exception as exc:
        print(f"[10] primary encoder failed ({exc}); fallback {cfg.ST_FALLBACK}", flush=True)
        model = SentenceTransformer(cfg.ST_FALLBACK, device=device)
        used = cfg.ST_FALLBACK

    parts: list[np.ndarray] = []
    for slot in cfg.PSE_SLOTS:
        texts = [rec["pse"][slot] for rec in patents]
        print(f"[10] encoding slot={slot} n={len(texts)} device={device}", flush=True)
        emb = model.encode(
            texts,
            batch_size=cfg.ST_BATCH,
            normalize_embeddings=cfg.ST_NORMALIZE,
            show_progress_bar=True,
            convert_to_numpy=True,
        )
        parts.append(np.asarray(emb, dtype=np.float64))
    txt = np.concatenate(parts, axis=1)
    meta = {
        "encoder": "sentence_transformer",
        "model": used,
        "device": device,
        "normalize": cfg.ST_NORMALIZE,
        "batch": cfg.ST_BATCH,
        "slot_dim": int(parts[0].shape[1]),
        "txt_dim": int(txt.shape[1]),
        "cuda_available": device == "cuda",
    }
    return txt, meta


def encode_tfidf_svd(patents: list[dict]) -> tuple[np.ndarray, dict]:
    parts: list[np.ndarray] = []
    slot_rank: dict[str, int] = {}
    for slot in cfg.PSE_SLOTS:
        texts = [rec["pse"][slot] for rec in patents]
        vectorizer = TfidfVectorizer(
            min_df=cfg.TFIDF_MIN_DF,
            max_df=cfg.TFIDF_MAX_DF,
            ngram_range=cfg.TFIDF_NGRAM,
        )
        sparse = vectorizer.fit_transform(texts)
        n_comp = min(cfg.TXT_DIM, max(1, sparse.shape[1] - 1), max(1, sparse.shape[0] - 1))
        svd = TruncatedSVD(n_components=n_comp, random_state=cfg.SEED)
        parts.append(svd.fit_transform(sparse).astype(np.float64, copy=False))
        slot_rank[slot] = n_comp
    txt = np.concatenate(parts, axis=1)
    meta = {
        "encoder": "tfidf_svd",
        "model": "tfidf_svd",
        "device": "cpu",
        "txt_dim": int(txt.shape[1]),
        "slot_rank": slot_rank,
        "min_df": cfg.TFIDF_MIN_DF,
        "max_df": cfg.TFIDF_MAX_DF,
        "ngram": list(cfg.TFIDF_NGRAM),
    }
    return txt, meta


def load_or_encode_txt(patents: list[dict], input_hash: str) -> tuple[np.ndarray, dict, bool]:
    cache_path = cfg.OUT / "10_txt_cache.npz"
    if cache_path.exists():
        cached = np.load(cache_path, allow_pickle=True)
        meta = json.loads(str(cached["meta"][0]))
        same_input = meta.get("input_hash") == input_hash
        same_enc = meta.get("encoder") == cfg.TEXT_ENCODER
        same_model = meta.get("model") == (
            cfg.ST_MODEL if cfg.TEXT_ENCODER == "sentence_transformer" else "tfidf_svd"
        )
        if same_input and same_enc and same_model:
            print(f"[10] reuse TXT cache {cache_path}", flush=True)
            return np.asarray(cached["txt"], dtype=np.float64), meta, True

    if cfg.TEXT_ENCODER == "tfidf_svd":
        txt, meta = encode_tfidf_svd(patents)
    elif cfg.TEXT_ENCODER == "sentence_transformer":
        txt, meta = encode_sentence_transformer(patents)
    else:
        raise SystemExit(f"unknown TEXT_ENCODER={cfg.TEXT_ENCODER!r}")

    meta = {**meta, "input_hash": input_hash, "txt_sha256": sha256_array(txt)}
    ensure_out()
    np.savez_compressed(cache_path, txt=txt, meta=np.array([json.dumps(meta, ensure_ascii=False)]))
    return txt, meta, False


def reduce_kg(raw: np.ndarray, missing: np.ndarray) -> tuple[np.ndarray, dict]:
    observed = missing == 0
    n_comp = min(cfg.KG_DIM, raw.shape[1], max(1, int(observed.sum()) - 1))
    pca = PCA(n_components=n_comp, random_state=cfg.SEED)
    if observed.any():
        pca.fit(raw[observed])
        reduced = pca.transform(raw)
    else:
        reduced = np.zeros((raw.shape[0], n_comp), dtype=np.float64)
    return reduced.astype(np.float64, copy=False), {
        "kg_raw_dim": int(raw.shape[1]),
        "kg_dim": int(reduced.shape[1]),
        "kg_explained_variance": float(pca.explained_variance_ratio_.sum()) if observed.any() else 0.0,
        "kg_fit_on_nonmissing": True,
    }


def assemble_x(
    txt: np.ndarray,
    kg: np.ndarray,
    cpc: np.ndarray,
) -> tuple[np.ndarray, dict]:
    blocks = {
        "TXT": l2_rows(zscore_block(txt)) * float(cfg.BLOCK_WEIGHTS["TXT"]),
        "KG": l2_rows(zscore_block(kg)) * float(cfg.BLOCK_WEIGHTS["KG"]),
        "CPC": l2_rows(zscore_block(cpc)) * float(cfg.BLOCK_WEIGHTS["CPC"]),
    }
    concat = np.hstack([blocks["TXT"], blocks["KG"], blocks["CPC"]])
    n_comp = min(cfg.PCA_DIM, concat.shape[0] - 1, concat.shape[1])
    pca = PCA(n_components=n_comp, random_state=cfg.SEED)
    x = pca.fit_transform(concat).astype(np.float64, copy=False)
    slices = {
        "TXT": slice(0, blocks["TXT"].shape[1]),
        "KG": slice(blocks["TXT"].shape[1], blocks["TXT"].shape[1] + blocks["KG"].shape[1]),
        "CPC": slice(blocks["TXT"].shape[1] + blocks["KG"].shape[1], concat.shape[1]),
    }
    contrib = pca_block_contributions(pca.components_, slices, top=10)
    explained = float(pca.explained_variance_ratio_.sum())
    txt_only = all(row["frac_TXT"] >= 0.90 for row in contrib) if contrib else False
    return x, {
        "block_dims": {name: int(arr.shape[1]) for name, arr in blocks.items()},
        "concat_dim": int(concat.shape[1]),
        "pca_dim": int(x.shape[1]),
        "pca_explained_variance": explained,
        "pca_explained_variance_ratio": pca.explained_variance_ratio_.astype(float).tolist(),
        "pca_block_contributions_top10": contrib,
        "txt_dominates_top10": txt_only,
        "block_weights": dict(cfg.BLOCK_WEIGHTS),
    }


def evaluate_gates(n: int, pubs_unique: bool, pca_meta: dict, alignment_ok: bool) -> dict:
    explained_ok = pca_meta["pca_explained_variance"] >= cfg.PCA_MIN_EXPLAINED
    block_ok = not pca_meta["txt_dominates_top10"]
    n_ok = n == 1412
    gates = {
        "n_equals_1412": {"pass": n_ok, "value": n},
        "publication_number_unique": {"pass": pubs_unique, "value": pubs_unique},
        "pca_explained_ge_min": {
            "pass": explained_ok,
            "value": pca_meta["pca_explained_variance"],
            "min": cfg.PCA_MIN_EXPLAINED,
        },
        "top10_not_txt_only": {
            "pass": block_ok,
            "value": pca_meta["txt_dominates_top10"],
        },
        "embedding_alignment": {"pass": alignment_ok, "value": alignment_ok},
    }
    gates["all_pass"] = all(item["pass"] for item in gates.values() if isinstance(item, dict))
    return gates


def main() -> int:
    ensure_out()
    print("[10] load patents", flush=True)
    patents = load_patents()
    input_hash = corpus_hash(patents)
    print(f"[10] n={len(patents)} corpus_hash={input_hash[:12]}", flush=True)

    print("[10] load KG embeddings + alignment assert", flush=True)
    assets = load_kg_assets()
    kg_raw, n_used, kg_missing, kg_stats = pool_kg(patents, assets)
    kg, kg_pca_meta = reduce_kg(kg_raw, kg_missing)
    cpc, cpc_vocab, n_cpc = build_cpc_block(patents)
    print(
        f"[10] KG missing={int(kg_missing.sum())} "
        f"lookup_miss={kg_stats['n_lookup_miss']} CPC vocab={len(cpc_vocab)}",
        flush=True,
    )

    n_triples = np.array([len(r["triples_v2"]) for r in patents], dtype=np.int64)
    txt, enc_meta, from_cache = load_or_encode_txt(patents, input_hash)
    print(
        f"[10] TXT shape={txt.shape} encoder={enc_meta.get('model')} "
        f"device={enc_meta.get('device')} cache={from_cache}",
        flush=True,
    )

    x, pca_meta = assemble_x(txt, kg, cpc)
    index = index_frame(patents, n_triples, n_cpc, kg_missing)
    gates = evaluate_gates(
        n=len(patents),
        pubs_unique=index["publication_number"].is_unique,
        pca_meta=pca_meta,
        alignment_ok=True,
    )

    np.save(cfg.OUT / "10_x.npy", x)
    index.to_csv(cfg.OUT / "10_index.csv", index=False)
    np.savez_compressed(
        cfg.OUT / "10_blocks.npz",
        txt=txt,
        kg=kg,
        cpc=cpc,
        kg_raw=kg_raw,
        kg_missing=kg_missing,
        cpc_vocab=np.array(cpc_vocab),
    )
    manifest = {
        "n": len(patents),
        "seed": cfg.SEED,
        "text_encoder": cfg.TEXT_ENCODER,
        "encoding": enc_meta,
        "encoding_from_cache": from_cache,
        "txt_sha256": enc_meta.get("txt_sha256") or sha256_array(txt),
        "x_sha256": sha256_array(x),
        "input_hashes": {
            "pse_corpus": input_hash,
            **assets["input_hashes"],
        },
        "alignment": assets["alignment"],
        "kg": {**kg_stats, **kg_pca_meta},
        "cpc": {
            "level": cfg.CPC_LEVEL,
            "n_codes": len(cpc_vocab),
            "missing_flag": cfg.CPC_MISSING_FLAG,
            "n_missing_cpc": int((n_cpc == 0).sum()),
        },
        **pca_meta,
        "gates": gates,
    }
    write_json(cfg.OUT / "10_manifest.json", manifest)

    print(
        f"[10] wrote x={x.shape} explained={pca_meta['pca_explained_variance']:.4f} "
        f"txt_dominates_top10={pca_meta['txt_dominates_top10']}",
        flush=True,
    )
    if not gates["all_pass"]:
        failed = [k for k, v in gates.items() if isinstance(v, dict) and not v["pass"]]
        print(f"[10] GATE FAIL: {failed}", file=sys.stderr, flush=True)
        print("[10] 블록 표준화 / BLOCK_WEIGHTS / PCA_DIM 을 재검토할 것.", file=sys.stderr, flush=True)
        return 1
    print("[10] gates passed", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
