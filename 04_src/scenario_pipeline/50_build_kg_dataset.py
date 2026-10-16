"""Stage 5-a — build surface KG triples and filtered negatives.

Observed (h,r,t) are positive. Head / tail / relation corruptions are
negative (D9). All numbers come from config.py.
"""

from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

import config as cfg
from lib import ensure_out, load_kg_assets, load_patents, lookup_index, write_json


def _split(year: int | None) -> str:
    if year is None:
        return "train"
    return "train" if year <= cfg.KG_SPLIT_TRAIN_MAX_YEAR else "eval"


def _pick_corrupt(kind_rng: np.random.Generator) -> str:
    kinds = list(cfg.NEG_MIX.keys())
    probs = np.array([cfg.NEG_MIX[k] for k in kinds], dtype=np.float64)
    probs = probs / probs.sum()
    return str(kind_rng.choice(kinds, p=probs))


def main() -> int:
    ensure_out()
    rng = np.random.default_rng(cfg.SEED)
    print("[50] load patents + KG assets", flush=True)
    patents = load_patents()
    assets = load_kg_assets()
    ent_exact, ent_fold = assets["ent_exact"], assets["ent_fold"]
    rel_exact, rel_fold = assets["rel_exact"], assets["rel_fold"]
    cluster_of = assets["cluster_of"]
    cluster_of_fold = assets["cluster_of_fold"]
    rel_keys = list(assets["rel_mapping"].keys())
    entity_keys = list(assets["entity_mapping"].keys())
    entity_clusters = np.array([int(c) for c in assets["entity_mapping"].values()], dtype=np.int32)
    rel_bucket = np.array([int(assets["rel_mapping"][k]) for k in rel_keys], dtype=np.int32)
    n_ent = assets["entity_emb"].shape[0]
    n_rel = assets["rel_emb"].shape[0]

    positives: list[dict] = []
    dropped_rows: list[dict] = []
    for rec in patents:
        for item in rec.get("dropped_triples") or []:
            dropped_rows.append(
                {
                    "publication_number": rec["publication_number"],
                    "filing_year": rec["filing_year"] if rec["filing_year"] is not None else "",
                    "raw": json.dumps(item, ensure_ascii=False)[:500],
                }
            )
        for head, rel, tail in rec["triples_v2"]:
            hi = lookup_index(head, ent_exact, ent_fold)
            ri = lookup_index(rel, rel_exact, rel_fold)
            ti = lookup_index(tail, ent_exact, ent_fold)
            if hi is None or ri is None or ti is None:
                dropped_rows.append(
                    {
                        "publication_number": rec["publication_number"],
                        "filing_year": rec["filing_year"] if rec["filing_year"] is not None else "",
                        "raw": json.dumps([head, rel, tail], ensure_ascii=False),
                    }
                )
                continue
            hc = cluster_of.get(head)
            if hc is None:
                hc = cluster_of_fold.get(head.casefold())
            tc = cluster_of.get(tail)
            if tc is None:
                tc = cluster_of_fold.get(tail.casefold())
            positives.append(
                {
                    "h": head,
                    "r": rel,
                    "t": tail,
                    "h_idx": int(hi),
                    "r_idx": int(ri),
                    "t_idx": int(ti),
                    "h_cluster": int(hc) if hc is not None else -1,
                    "r_std": int(rel_bucket[ri]),
                    "t_cluster": int(tc) if tc is not None else -1,
                    "publication_number": rec["publication_number"],
                    "filing_year": rec["filing_year"] if rec["filing_year"] is not None else "",
                    "window": rec["window"],
                    "split": _split(rec["filing_year"]),
                }
            )

    print(f"[50] positives={len(positives)} dropped={len(dropped_rows)}", flush=True)
    observed_surface = {(p["h_idx"], p["r_idx"], p["t_idx"]) for p in positives}
    observed_std = {
        (p["h_cluster"], p["r_std"], p["t_cluster"])
        for p in positives
        if p["h_cluster"] >= 0 and p["t_cluster"] >= 0
    }

    freq = np.zeros(n_ent, dtype=np.float64)
    for p in positives:
        freq[p["h_idx"]] += 1
        freq[p["t_idx"]] += 1
    if freq.sum() <= 0:
        raise SystemExit("엔티티 빈도가 0이다.")
    ent_p = freq / freq.sum()
    ent_idx = np.arange(n_ent)
    rel_idx = np.arange(n_rel)
    other_rels = []
    for b in range(int(rel_bucket.max()) + 1):
        other_rels.append(rel_idx[rel_bucket != b])

    def sample_entity(forbid: set[int]) -> int:
        for _ in range(40):
            j = int(rng.choice(ent_idx, p=ent_p))
            if j not in forbid:
                return j
        return int(rng.integers(0, n_ent))

    def is_filtered(hi: int, ri: int, ti: int, hc: int, rs: int, tc: int) -> bool:
        if not cfg.NEG_FILTERED:
            return False
        if (hi, ri, ti) in observed_surface:
            return True
        if hc >= 0 and tc >= 0 and (hc, rs, tc) in observed_std:
            return True
        return False

    negatives: list[dict] = []
    n_retry_fail = 0
    for p in positives:
        for _ in range(cfg.NEG_RATIO):
            kind = _pick_corrupt(rng)
            hi, ri, ti = p["h_idx"], p["r_idx"], p["t_idx"]
            hc, rs, tc = p["h_cluster"], p["r_std"], p["t_cluster"]
            nh, nr, nt = p["h"], p["r"], p["t"]
            ok = False
            for _try in range(40):
                chi, cri, cti = hi, ri, ti
                chc, crs, ctc = hc, rs, tc
                ch, cr, ct = nh, nr, nt
                if kind == "tail":
                    cti = sample_entity({ti})
                    ct = entity_keys[cti]
                    ctc = int(entity_clusters[cti])
                elif kind == "head":
                    chi = sample_entity({hi})
                    ch = entity_keys[chi]
                    chc = int(entity_clusters[chi])
                else:
                    pool = other_rels[rs] if cfg.NEG_EXCLUDE_SAME_STD_BUCKET else rel_idx[rel_idx != ri]
                    if pool.size == 0:
                        pool = rel_idx[rel_idx != ri]
                    cri = int(rng.choice(pool))
                    cr = rel_keys[cri]
                    crs = int(rel_bucket[cri])
                if not is_filtered(chi, cri, cti, chc, crs, ctc):
                    ok = True
                    break
            if not ok:
                n_retry_fail += 1
            negatives.append(
                {
                    "h": ch,
                    "r": cr,
                    "t": ct,
                    "h_idx": int(chi),
                    "r_idx": int(cri),
                    "t_idx": int(cti),
                    "h_cluster": int(chc),
                    "r_std": int(crs),
                    "t_cluster": int(ctc),
                    "publication_number": p["publication_number"],
                    "filing_year": p["filing_year"],
                    "window": p["window"],
                    "split": p["split"],
                    "pos_neg": "neg",
                    "corrupt_type": kind,
                }
            )

    pos_rows = [{**p, "pos_neg": "pos", "corrupt_type": ""} for p in positives]
    triples = pd.DataFrame(pos_rows + negatives)
    triples.to_csv(cfg.OUT / "50_triples.csv", index=False)
    triples[triples["pos_neg"] == "neg"].to_csv(cfg.OUT / "50_negatives.csv", index=False)
    pd.DataFrame(dropped_rows).to_csv(cfg.OUT / "50_dropped.csv", index=False)

    audit = triples[triples["pos_neg"] == "neg"].sample(
        n=min(cfg.NEG_AUDIT_SAMPLE, (triples["pos_neg"] == "neg").sum()),
        random_state=cfg.SEED,
    )
    audit.to_csv(cfg.OUT / "50_audit_sample.csv", index=False)

    n_pos = int((triples["pos_neg"] == "pos").sum())
    n_neg = int((triples["pos_neg"] == "neg").sum())
    write_json(
        cfg.OUT / "50_manifest.json",
        {
            "n_pos": n_pos,
            "n_neg": n_neg,
            "n_dropped": len(dropped_rows),
            "neg_ratio": cfg.NEG_RATIO,
            "neg_mix": dict(cfg.NEG_MIX),
            "filtered": cfg.NEG_FILTERED,
            "n_retry_fail": n_retry_fail,
            "split_counts": {
                f"{a}_{b}": int(v)
                for (a, b), v in triples.groupby(["split", "pos_neg"]).size().items()
            },
            "audit_sample": cfg.NEG_AUDIT_SAMPLE,
            "audit_status": "pending_human",
        },
    )
    print(
        f"[50] wrote triples pos={n_pos} neg={n_neg} dropped={len(dropped_rows)} "
        f"retry_fail={n_retry_fail}",
        flush=True,
    )
    print("[50] WARN: 50_audit_sample.csv 100건은 사람이 '말이 안 되는지' 봐야 D9가 닫힌다.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
