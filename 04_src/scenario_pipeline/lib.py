"""Shared loaders and IO for scenario_pipeline.

Numbers live in config.py. This module only implements the data rules in
docs/00_data_facts.md and docs/02_stage_specs.md.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import config as cfg

CODE_FENCE = re.compile(r"^.*?```(?:json)?", re.S)
CODE_FENCE_END = re.compile(r"```.*$", re.S)
LIST_BLOB = re.compile(r"\[.*\]", re.S)


def ensure_out() -> Path:
    cfg.OUT.mkdir(parents=True, exist_ok=True)
    return cfg.OUT


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            buf = f.read(chunk)
            if not buf:
                break
            h.update(buf)
    return h.hexdigest()


def sha256_array(arr: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(arr).tobytes()).hexdigest()


def parse_year(value: Any) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if len(text) < 4:
        return None
    try:
        return int(text[:4])
    except ValueError:
        return None


def year_to_window(year: int | None) -> str:
    if year is None:
        return ""
    for name, (lo, hi) in cfg.WINDOWS.items():
        if lo <= year <= hi:
            return name
    if year < min(lo for lo, _ in cfg.WINDOWS.values()):
        return "pre2019"
    return "post2024"


def cpc_key(code: str) -> str:
    token = (code or "").strip()
    if cfg.CPC_LEVEL == "full":
        return token
    return token[:4]


def parse_cpc(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        return [p.strip() for p in raw.replace(",", ";").split(";") if p.strip()]
    if isinstance(raw, list):
        return [str(p).strip() for p in raw if str(p).strip()]
    return []


def coerce_list(raw: Any) -> list:
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    if not isinstance(raw, str):
        return []
    text = raw.strip()
    if "```" in text:
        text = CODE_FENCE.sub("", text)
        text = CODE_FENCE_END.sub("", text)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        match = LIST_BLOB.search(text)
        if not match:
            return []
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError:
            return []
    return parsed if isinstance(parsed, list) else []


def parse_triples(raw: Any) -> list[tuple[str, str, str]]:
    """Keep length-3 triples only. Length ≠ 3 is unstructured (docs §부록)."""
    out: list[tuple[str, str, str]] = []
    for item in coerce_list(raw):
        if isinstance(item, (list, tuple)) and len(item) == 3:
            out.append((str(item[0]).strip(), str(item[1]).strip(), str(item[2]).strip()))
    return out


def load_patents() -> list[dict]:
    files = sorted(cfg.PSE_KG_DIR.glob("*_pse_kn.json"))
    records: list[dict] = []
    for path in files:
        doc = json.loads(path.read_text(encoding="utf-8"))
        pub = doc.get("publication_number") or path.stem.replace("_pse_kn", "")
        pse = doc.get("pse") if isinstance(doc.get("pse"), dict) else {}
        filing_year = parse_year(doc.get(cfg.DATE_FIELD))
        pub_year = parse_year(doc.get("publication_date"))
        records.append(
            {
                "publication_number": str(pub),
                "title": "" if doc.get("title") is None else str(doc.get("title")),
                "assignee": "" if doc.get("assignee") is None else str(doc.get("assignee")),
                "filing_date": doc.get("filing_date") or "",
                "publication_date": doc.get("publication_date") or "",
                "filing_year": filing_year,
                "pub_year": pub_year,
                "window": year_to_window(filing_year),
                "pse": {slot: str(pse.get(slot) or "") for slot in cfg.PSE_SLOTS},
                "triples_v2": parse_triples(doc.get("knowledge_graph_v2")),
                "cpc": parse_cpc(doc.get("cpc_code")),
                "path": str(path),
            }
        )
        raw_kg = coerce_list(doc.get("knowledge_graph_v2"))
        records[-1]["n_dropped_triples"] = sum(
            0 if isinstance(item, (list, tuple)) and len(item) == 3 else 1 for item in raw_kg
        )
        records[-1]["dropped_triples"] = [
            item for item in raw_kg if not (isinstance(item, (list, tuple)) and len(item) == 3)
        ]
    records.sort(key=lambda r: r["publication_number"])
    pubs = [r["publication_number"] for r in records]
    if len(pubs) != len(set(pubs)):
        raise SystemExit("publication_number 중복이 있다. 단계 1 게이트 실패.")
    return records


def load_standardization() -> dict:
    return json.loads(cfg.STD_RESULTS.read_text(encoding="utf-8"))


def _index_with_casefold(keys: list[str]) -> tuple[dict[str, int], dict[str, int]]:
    exact = {key: i for i, key in enumerate(keys)}
    folded: dict[str, int] = {}
    for i, key in enumerate(keys):
        folded.setdefault(key.casefold(), i)
    return exact, folded


def lookup_index(key: str, exact: dict[str, int], folded: dict[str, int]) -> int | None:
    if key in exact:
        return exact[key]
    return folded.get(key.casefold())


def assert_embedding_alignment(
    entity_emb: np.ndarray,
    entity_mapping: dict[str, int],
    rel_emb: np.ndarray,
    rel_mapping: dict[str, int],
    n_pairs: int = 400,
) -> dict:
    """Key-order alignment check from docs/00_data_facts.md §5."""
    if entity_emb.shape[0] != len(entity_mapping):
        raise AssertionError(
            f"Entity_embeddings rows {entity_emb.shape[0]} != entity_mapping {len(entity_mapping)}"
        )
    if rel_emb.shape[0] != len(rel_mapping):
        raise AssertionError(
            f"Sub_Relation_embeddings rows {rel_emb.shape[0]} != sub_relation_mapping {len(rel_mapping)}"
        )
    if entity_emb.shape[1] != cfg.ST_DIM or rel_emb.shape[1] != cfg.ST_DIM:
        raise AssertionError(
            f"embedding dim {entity_emb.shape[1]}/{rel_emb.shape[1]} != ST_DIM {cfg.ST_DIM}"
        )

    by_cluster: dict[int, list[int]] = defaultdict(list)
    for i, cid in enumerate(entity_mapping.values()):
        by_cluster[int(cid)].append(i)
    multi = [c for c, idx in by_cluster.items() if len(idx) >= 2]
    if len(multi) < 2 or len(by_cluster) < 2:
        raise AssertionError("클러스터가 부족해 정렬 검증을 할 수 없다.")

    norms = np.linalg.norm(entity_emb, axis=1, keepdims=True)
    unit = entity_emb / np.clip(norms, 1e-12, None)
    rng = np.random.default_rng(cfg.SEED)
    multi_arr = np.array(multi, dtype=np.int64)
    all_c = np.array(list(by_cluster.keys()), dtype=np.int64)

    same: list[float] = []
    for _ in range(n_pairs):
        cid = int(rng.choice(multi_arr))
        i, j = rng.choice(by_cluster[cid], size=2, replace=False)
        same.append(float(unit[i] @ unit[j]))
    diff: list[float] = []
    for _ in range(n_pairs):
        c1, c2 = rng.choice(all_c, size=2, replace=False)
        i = int(rng.choice(by_cluster[int(c1)]))
        j = int(rng.choice(by_cluster[int(c2)]))
        diff.append(float(unit[i] @ unit[j]))

    same_m = float(np.mean(same))
    diff_m = float(np.mean(diff))
    if not (same_m > diff_m):
        raise AssertionError(
            f"임베딩 정렬 실패: same-cluster cosine {same_m:.3f} <= diff {diff_m:.3f}"
        )
    return {
        "same_cluster_cosine": same_m,
        "diff_cluster_cosine": diff_m,
        "n_pairs": n_pairs,
    }


def load_kg_assets() -> dict:
    std = load_standardization()
    entity_mapping = std["entity_mapping"]
    rel_mapping = std["sub_relation_mapping"]
    entity_keys = list(entity_mapping.keys())
    rel_keys = list(rel_mapping.keys())
    entity_emb = np.load(cfg.ENTITY_EMB).astype(np.float32, copy=False)
    rel_emb = np.load(cfg.SUBREL_EMB).astype(np.float32, copy=False)
    alignment = assert_embedding_alignment(entity_emb, entity_mapping, rel_emb, rel_mapping)
    ent_exact, ent_fold = _index_with_casefold(entity_keys)
    rel_exact, rel_fold = _index_with_casefold(rel_keys)
    cluster_of = {key: int(cid) for key, cid in entity_mapping.items()}
    cluster_of_fold = {}
    for key, cid in entity_mapping.items():
        cluster_of_fold.setdefault(key.casefold(), int(cid))
    return {
        "entity_mapping": entity_mapping,
        "rel_mapping": rel_mapping,
        "entity_emb": entity_emb,
        "rel_emb": rel_emb,
        "ent_exact": ent_exact,
        "ent_fold": ent_fold,
        "rel_exact": rel_exact,
        "rel_fold": rel_fold,
        "cluster_of": cluster_of,
        "cluster_of_fold": cluster_of_fold,
        "alignment": alignment,
        "input_hashes": {
            "final_standardization_results.json": sha256_file(cfg.STD_RESULTS),
            "Entity_embeddings.npy": sha256_file(cfg.ENTITY_EMB),
            "Sub_Relation_embeddings.npy": sha256_file(cfg.SUBREL_EMB),
        },
    }


def entity_cluster(name: str, assets: dict) -> int | None:
    if name in assets["cluster_of"]:
        return assets["cluster_of"][name]
    return assets["cluster_of_fold"].get(name.casefold())


def corpus_hash(patents: list[dict]) -> str:
    h = hashlib.sha256()
    h.update(str(len(patents)).encode())
    for rec in patents:
        h.update(rec["publication_number"].encode())
        h.update(b"\0")
        h.update(str(len(rec["triples_v2"])).encode())
        h.update(b"\0")
        h.update(str(len(rec["cpc"])).encode())
        h.update(b"\0")
        for slot in cfg.PSE_SLOTS:
            h.update(rec["pse"][slot].encode("utf-8", errors="replace"))
            h.update(b"\0")
    return h.hexdigest()


def zscore_block(block: np.ndarray) -> np.ndarray:
    mean = block.mean(axis=0)
    std = block.std(axis=0)
    std = np.where(std < 1e-12, 1.0, std)
    return (block - mean) / std


def l2_rows(block: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(block, axis=1, keepdims=True)
    return block / np.clip(norms, 1e-12, None)


def pool_kg(patents: list[dict], assets: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    """Mean-pool [e_h; e_r; e_t]. Empty graphs are missing and filled with the block mean."""
    n = len(patents)
    d = assets["entity_emb"].shape[1]
    raw = np.zeros((n, 3 * d), dtype=np.float64)
    n_used = np.zeros(n, dtype=np.int32)
    missing = np.zeros(n, dtype=np.int32)
    n_lookup_miss = 0
    n_valid = 0
    for i, rec in enumerate(patents):
        vecs: list[np.ndarray] = []
        for head, rel, tail in rec["triples_v2"]:
            n_valid += 1
            hi = lookup_index(head, assets["ent_exact"], assets["ent_fold"])
            ri = lookup_index(rel, assets["rel_exact"], assets["rel_fold"])
            ti = lookup_index(tail, assets["ent_exact"], assets["ent_fold"])
            if hi is None or ri is None or ti is None:
                n_lookup_miss += 1
                continue
            vecs.append(
                np.concatenate(
                    [
                        assets["entity_emb"][hi],
                        assets["rel_emb"][ri],
                        assets["entity_emb"][ti],
                    ]
                )
            )
        if not vecs:
            missing[i] = 1
            continue
        stacked = np.stack(vecs, axis=0).astype(np.float64, copy=False)
        raw[i] = stacked.mean(axis=0)
        n_used[i] = stacked.shape[0]
    observed = missing == 0
    if observed.any():
        fill = raw[observed].mean(axis=0)
        raw[~observed] = fill
    stats = {
        "n_valid_triples": int(n_valid),
        "n_lookup_miss": int(n_lookup_miss),
        "n_kg_missing": int(missing.sum()),
        "pool": cfg.KG_TRIPLE_POOL,
    }
    return raw, n_used, missing, stats


def build_cpc_block(patents: list[dict]) -> tuple[np.ndarray, list[str], np.ndarray]:
    keys: set[str] = set()
    for rec in patents:
        for code in rec["cpc"]:
            token = cpc_key(code)
            if token:
                keys.add(token)
    vocab = sorted(keys)
    n_flag = 1 if cfg.CPC_MISSING_FLAG else 0
    block = np.zeros((len(patents), len(vocab) + n_flag), dtype=np.float64)
    n_cpc = np.zeros(len(patents), dtype=np.int32)
    index = {key: j for j, key in enumerate(vocab)}
    for i, rec in enumerate(patents):
        n_cpc[i] = len(rec["cpc"])
        if not rec["cpc"]:
            if n_flag:
                block[i, -1] = 1.0
            continue
        for code in rec["cpc"]:
            j = index.get(cpc_key(code))
            if j is not None:
                block[i, j] = 1.0
    return block, vocab, n_cpc


def index_frame(
    patents: list[dict],
    n_triples: np.ndarray,
    n_cpc: np.ndarray,
    kg_missing: np.ndarray,
) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "row": np.arange(len(patents), dtype=np.int64),
            "publication_number": [r["publication_number"] for r in patents],
            "filing_year": [r["filing_year"] if r["filing_year"] is not None else "" for r in patents],
            "pub_year": [r["pub_year"] if r["pub_year"] is not None else "" for r in patents],
            "window": [r["window"] for r in patents],
            "assignee": [r["assignee"] for r in patents],
            "n_triples_v2": n_triples.astype(np.int64),
            "n_cpc": n_cpc.astype(np.int64),
            "kg_missing": kg_missing.astype(np.int64),
        }
    )


def pca_block_contributions(components: np.ndarray, slices: dict[str, slice], top: int = 10) -> list[dict]:
    rows = []
    n = min(top, components.shape[0])
    for k in range(n):
        loading = components[k]
        norms = {name: float(np.linalg.norm(loading[sl])) for name, sl in slices.items()}
        total = sum(norms.values()) or 1.0
        frac = {f"frac_{name}": val / total for name, val in norms.items()}
        rows.append({"component": k, **norms, **frac})
    return rows
