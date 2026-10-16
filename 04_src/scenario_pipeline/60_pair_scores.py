"""Stage 6-a — cross-group pair scores with the frozen feasibility scorer.

Unit is the surface entity string in v2 triples, not entity_mapping integers.
Distinctive entities: lift on responsibility-weighted u_g, then
dist(g1) × dist(g2) × R_cand. Near-paraphrase cosine and unique (h,t) still apply.
"""

from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from itertools import combinations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from pathlib import Path

import config as cfg
from lib import (
    ensure_out,
    load_kg_assets,
    load_patents,
    lookup_index,
    write_json,
)


def _font():
    path = Path("/usr/share/fonts/truetype/unfonts-core/UnDotum.ttf")
    if path.exists():
        font_manager.fontManager.addfont(str(path))
        return font_manager.FontProperties(fname=str(path))
    return None


def load_scorer():
    path = cfg.OUT / "51_model.npz"
    if not path.exists():
        raise SystemExit("out/51_model.npz 가 없다. 먼저 51_fit_feasibility.py 를 실행하라.")
    m = np.load(path)
    return {
        "components": m["pca_components"],
        "mean": m["pca_mean"],
        "coef": m["logreg_coef"].astype(np.float64),
        "intercept": float(m["logreg_intercept"][0]),
        "iso_x": m["iso_x"].astype(np.float64),
        "iso_y": m["iso_y"].astype(np.float64),
    }


def to64(vec768: np.ndarray, scorer: dict) -> np.ndarray:
    x = np.asarray(vec768, dtype=np.float64)
    if x.ndim == 1:
        x = x[None, :]
    return (x - scorer["mean"]) @ scorer["components"].T


def phi_and_prob(h: np.ndarray, r: np.ndarray, t: np.ndarray, scorer: dict) -> np.ndarray:
    blocks = {"hrt": h * r * t, "ht": h * t, "hr": h * r, "rt": r * t}
    phi = np.hstack([blocks[name] for name in cfg.FEAT_BLOCKS])
    score = phi @ scorer["coef"] + scorer["intercept"]
    return np.interp(score, scorer["iso_x"], scorer["iso_y"])


def relation_candidates(patents: list[dict], assets: dict) -> tuple[list[int], list[str], int, dict[int, int]]:
    counts: Counter = Counter()
    for rec in patents:
        for _h, rel, _t in rec["triples_v2"]:
            ri = lookup_index(rel, assets["rel_exact"], assets["rel_fold"])
            if ri is not None:
                counts[int(ri)] += 1
    if not counts:
        raise SystemExit("관계 빈도가 비었다.")
    ordered = counts.most_common()
    total = sum(n for _, n in ordered)
    picked, mass = [], 0
    for ri, n in ordered:
        picked.append(ri)
        mass += n
        if mass / total >= cfg.REL_MASS:
            break
    rel_keys = list(assets["rel_mapping"].keys())
    names = [rel_keys[i] for i in picked]
    return picked, names, total, {int(ri): int(n) for ri, n in counts.items()}


def group_surface_profiles(
    resp: np.ndarray, patents: list[dict], assets: dict
) -> tuple[list[Counter], dict[int, str]]:
    """u_g over embedding-row indices of v2 surface entities. Mapping IDs unused."""
    k = resp.shape[1]
    acc = [Counter() for _ in range(k)]
    spell: dict[int, Counter] = defaultdict(Counter)
    for i, rec in enumerate(patents):
        found: list[int] = []
        names: list[str] = []
        for head, _r, tail in rec["triples_v2"]:
            for name in (head, tail):
                if not name or not str(name).strip():
                    continue
                raw = str(name).strip()
                if len(raw) > cfg.PAIR_ENTITY_MAX_CHARS:
                    continue
                idx = lookup_index(raw, assets["ent_exact"], assets["ent_fold"])
                if idx is None:
                    continue
                found.append(int(idx))
                names.append(str(name))
        if not found:
            continue
        w = 1.0 / float(len(found))
        rg = resp[i]
        for idx, name in zip(found, names):
            spell[idx][name] += 1
            for g in range(k):
                acc[g][idx] += float(rg[g]) * w
    for g in range(k):
        tot = float(sum(acc[g].values()))
        if tot <= 0:
            continue
        for idx in list(acc[g]):
            acc[g][idx] /= tot
    canon = {idx: sp.most_common(1)[0][0] for idx, sp in spell.items()}
    return acc, canon


def select_distinctive_surface(
    acc: list[Counter], canon: dict[int, str]
) -> tuple[dict[int, list[int]], pd.DataFrame, dict[tuple[int, int], float]]:
    k = len(acc)
    vocab = sorted(set().union(*[set(c) for c in acc]))
    if not vocab:
        raise SystemExit("표면 엔티티 프로필이 비었다.")
    mean_u = {idx: float(sum(acc[g].get(idx, 0.0) for g in range(k)) / k) for idx in vocab}
    lifts: dict[tuple[int, int], float] = {}
    rows = []
    picked: dict[int, list[int]] = {}
    for g in range(k):
        scored = []
        for idx in vocab:
            u = float(acc[g].get(idx, 0.0))
            lift = u / max(mean_u[idx], 1e-12)
            lifts[(g, idx)] = lift
            scored.append((lift, u, idx))
        scored.sort(reverse=True)
        eligible = [(lift, u, idx) for lift, u, idx in scored if u >= cfg.PAIR_MASS_MIN and lift >= cfg.PAIR_LIFT_MIN]
        if not eligible:
            eligible = [(lift, u, idx) for lift, u, idx in scored if u >= cfg.PAIR_MASS_MIN]
        chosen = [idx for _lift, _u, idx in eligible[: cfg.TOP_CLUSTERS]]
        if not chosen:
            raise SystemExit(f"그룹 {g} 의 차별화 엔티티가 비었다.")
        picked[g] = chosen
        chosen_set = set(chosen)
        for lift, u, idx in scored:
            if u < cfg.PAIR_MASS_MIN and idx not in chosen_set:
                continue
            rows.append(
                {
                    "group": g,
                    "entity_idx": idx,
                    "entity": canon.get(idx, str(idx)),
                    "u": u,
                    "lift": lift,
                    "selected": int(idx in chosen_set),
                }
            )
    table = pd.DataFrame(rows).sort_values(["group", "selected", "lift"], ascending=[True, False, False])
    return picked, table, lifts


def score_direction(
    h_ids: list[int],
    t_ids: list[int],
    r_ids: list[int],
    e64: np.ndarray,
    r64: np.ndarray,
    scorer: dict,
    observed: set[tuple[int, int, int]],
    src_g: int,
    dst_g: int,
) -> pd.DataFrame:
    hh, tt, rr = np.meshgrid(
        np.arange(len(h_ids)), np.arange(len(t_ids)), np.arange(len(r_ids)), indexing="ij"
    )
    hi = np.array(h_ids, dtype=np.int32)[hh.ravel()]
    ti = np.array(t_ids, dtype=np.int32)[tt.ravel()]
    ri = np.array(r_ids, dtype=np.int32)[rr.ravel()]
    keep = hi != ti
    hi, ti, ri = hi[keep], ti[keep], ri[keep]
    cols = ["h_idx", "r_idx", "t_idx", "prob", "observed", "src_g", "dst_g"]
    if hi.size == 0:
        return pd.DataFrame(columns=cols)
    prob = phi_and_prob(e64[hi], r64[ri], e64[ti], scorer)
    obs = np.array([(int(a), int(b), int(c)) in observed for a, b, c in zip(hi, ri, ti)])
    return pd.DataFrame(
        {
            "h_idx": hi,
            "r_idx": ri,
            "t_idx": ti,
            "prob": prob,
            "observed": obs.astype(np.int8),
            "src_g": src_g,
            "dst_g": dst_g,
        }
    )


def _name_tokens(s: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", str(s).lower()) if t]


def _stem(tok: str) -> str:
    for stem in cfg.PAIR_SAME_NOUN_STEMS:
        if tok == stem or tok == stem + "s":
            return stem
    return tok


def same_head_noun(h: str, t: str) -> bool:
    """True if a reader would call h and t the same noun family."""
    ht, tt = _name_tokens(h), _name_tokens(t)
    if not ht or not tt:
        return False
    hs, ts = " ".join(ht), " ".join(tt)
    shorter, longer = (hs, ts) if len(hs) <= len(ts) else (ts, hs)
    if len(shorter) >= cfg.PAIR_NAME_CONTAIN_MIN and shorter in longer:
        return True
    cores = set(cfg.PAIR_SAME_NOUN_STEMS)
    h_core = {_stem(tok) for tok in ht} & cores
    t_core = {_stem(tok) for tok in tt} & cores
    return bool(h_core & t_core)


def _rel_generic(rel: str) -> bool:
    toks = _name_tokens(rel)
    stems = set(cfg.PAIR_GENERIC_REL_STEMS)
    return any(tok.startswith(stem) or stem.startswith(tok) for tok in toks for stem in stems)


def _has_role_stem(name: str) -> bool:
    cores = set(cfg.PAIR_SAME_NOUN_STEMS)
    return bool({_stem(tok) for tok in _name_tokens(name)} & cores)


def novelty_score(
    h: str,
    t: str,
    rel: str,
    h_lift: float,
    t_lift: float,
    cosine: float,
    prob: float,
    rel_count: float,
    rel_count_ref: float,
) -> tuple[float, float, float]:
    """Display novelty. F is a floor, not the rank. Returns (N, rel_pen, role_pen)."""
    if prob < cfg.PAIR_NOVEL_F_MIN:
        return 0.0, 1.0, 1.0
    rel_pen = 1.0 / (1.0 + np.log1p(max(rel_count, 0.0) / max(rel_count_ref, 1.0)))
    if _rel_generic(rel):
        rel_pen *= cfg.PAIR_GENERIC_REL_PENALTY
    role_pen = 1.0
    if _rel_generic(rel) and _has_role_stem(h) and _has_role_stem(t):
        role_pen = cfg.PAIR_ROLE_TEMPLATE_PENALTY
    n = float(h_lift) * float(t_lift) * (1.0 - min(float(cosine), 1.0)) * rel_pen * role_pen
    return max(n, 0.0), float(rel_pen), float(role_pen)


def filter_candidates(
    cand: pd.DataFrame, unit768: np.ndarray, canon: dict[int, str]
) -> tuple[pd.DataFrame, dict]:
    stats = {
        "n_raw": int(len(cand)),
        "n_dropped_paraphrase": 0,
        "n_dropped_same_noun": 0,
        "n_unique_ht": int(len(cand)),
    }
    if cand.empty:
        return cand, stats
    out = cand.copy()
    hi = out["h_idx"].to_numpy()
    ti = out["t_idx"].to_numpy()
    out["ht_cosine"] = (unit768[hi] * unit768[ti]).sum(axis=1)
    h_name = [canon.get(int(i), str(int(i))) for i in hi]
    t_name = [canon.get(int(i), str(int(i))) for i in ti]
    same = [same_head_noun(a, b) for a, b in zip(h_name, t_name)]
    out["same_noun"] = same
    drop_cos = out["ht_cosine"] >= cfg.PAIR_COS_MAX
    drop_noun = out["same_noun"].to_numpy()
    stats["n_dropped_paraphrase"] = int(drop_cos.sum())
    stats["n_dropped_same_noun"] = int(drop_noun.sum())
    keep = (~drop_cos) & (~out["same_noun"])
    out = out.loc[keep].reset_index(drop=True)
    if cfg.PAIR_UNIQUE_HT and len(out):
        out = (
            out.sort_values("prob", ascending=False)
            .drop_duplicates(["h_idx", "t_idx"], keep="first")
            .reset_index(drop=True)
        )
    stats["n_unique_ht"] = int(len(out))
    return out, stats


def _triple_row(g1, g2, rank, row, canon, name_of_rel, lifts, extra=None) -> dict:
    h_idx = int(row.h_idx)
    t_idx = int(row.t_idx)
    src = int(row.src_g)
    dst = int(row.dst_g)
    out = {
        "g1": g1,
        "g2": g2,
        "rank": rank,
        "h_idx": h_idx,
        "h": canon.get(h_idx, str(h_idx)),
        "r": name_of_rel.get(int(row.r_idx), str(int(row.r_idx))),
        "t_idx": t_idx,
        "t": canon.get(t_idx, str(t_idx)),
        "ht_cosine": float(row.ht_cosine),
        "h_lift": float(lifts.get((src, h_idx), np.nan)),
        "t_lift": float(lifts.get((dst, t_idx), np.nan)),
        "prob": float(row.prob),
        "observed": int(row.observed),
        "src_g": src,
        "dst_g": dst,
    }
    if extra is not None and hasattr(extra, "novelty"):
        out["novelty"] = float(extra.novelty)
        out["rel_pen"] = float(extra.rel_pen)
        out["role_pen"] = float(extra.role_pen)
    return out


def _with_novelty(pool: pd.DataFrame, canon, name_of_rel, lifts, rel_counts, rel_count_ref) -> pd.DataFrame:
    if pool.empty:
        out = pool.copy()
        out["novelty"] = []
        out["rel_pen"] = []
        out["role_pen"] = []
        return out
    nov, rel_pen, role_pen = [], [], []
    for row in pool.itertuples(index=False):
        h = canon.get(int(row.h_idx), str(int(row.h_idx)))
        t = canon.get(int(row.t_idx), str(int(row.t_idx)))
        rel = name_of_rel.get(int(row.r_idx), str(int(row.r_idx)))
        n, rp, ro = novelty_score(
            h,
            t,
            rel,
            float(lifts.get((int(row.src_g), int(row.h_idx)), 0.0)),
            float(lifts.get((int(row.dst_g), int(row.t_idx)), 0.0)),
            float(row.ht_cosine),
            float(row.prob),
            float(rel_counts.get(int(row.r_idx), rel_count_ref)),
            rel_count_ref,
        )
        nov.append(n)
        rel_pen.append(rp)
        role_pen.append(ro)
    out = pool.copy()
    out["novelty"] = nov
    out["rel_pen"] = rel_pen
    out["role_pen"] = role_pen
    return out


def main() -> int:
    ensure_out()
    cfg.FIG.mkdir(parents=True, exist_ok=True)
    resp_path = cfg.OUT / "20_resp.npy"
    if not resp_path.exists():
        raise SystemExit("단계 2 산출물이 없다.")
    resp = np.load(resp_path)
    k = resp.shape[1]
    print("[60] load patents + KG + scorer (surface entities, no mapping IDs)", flush=True)
    patents = load_patents()
    assets = load_kg_assets()
    scorer = load_scorer()
    if len(patents) != resp.shape[0]:
        raise SystemExit(f"특허 수 {len(patents)} != resp {resp.shape[0]}")

    e768 = assets["entity_emb"].astype(np.float64, copy=False)
    norms = np.clip(np.linalg.norm(e768, axis=1, keepdims=True), 1e-12, None)
    unit768 = e768 / norms
    e64 = to64(e768, scorer)
    r64 = to64(assets["rel_emb"], scorer)
    rel_ids, rel_names, rel_total, rel_counts = relation_candidates(patents, assets)
    name_of_rel = {i: n for i, n in zip(rel_ids, rel_names)}
    rel_count_ref = float(np.median(list(rel_counts.values()))) if rel_counts else 1.0

    acc, canon = group_surface_profiles(resp, patents, assets)
    if cfg.PAIR_CLUSTER_MODE not in {"lift_surface", "lift"}:
        raise SystemExit(f"PAIR_CLUSTER_MODE={cfg.PAIR_CLUSTER_MODE} 는 표면 엔티티 경로가 아니다.")
    entities, table, lifts = select_distinctive_surface(acc, canon)
    table.to_csv(cfg.OUT / "60_group_entities.csv", index=False)
    print(
        f"[60] K={k} mode=lift_surface |R_cand|={len(rel_ids)} "
        f"n_ent={[len(entities[g]) for g in range(k)]}",
        flush=True,
    )
    for g in range(k):
        preview = ", ".join(
            f"{canon.get(idx, idx)}(L={lifts[(g, idx)]:.1f})" for idx in entities[g][:5]
        )
        print(f"[60]   G{g} {preview}", flush=True)

    observed: set[tuple[int, int, int]] = set()
    triples_path = cfg.OUT / "50_triples.csv"
    if triples_path.exists():
        pos = pd.read_csv(triples_path)
        pos = pos[pos["pos_neg"] == "pos"]
        for row in pos.itertuples(index=False):
            observed.add((int(row.h_idx), int(row.r_idx), int(row.t_idx)))

    names = {}
    if (cfg.OUT / "30_group_names.csv").exists():
        for _, row in pd.read_csv(cfg.OUT / "30_group_names.csv").iterrows():
            raw = str(row["name"])
            abbr = raw[raw.find("(") + 1 : raw.rfind(")")] if "(" in raw else f"G{int(row['group'])}"
            names[int(row["group"])] = abbr
    else:
        names = {g: f"G{g}" for g in range(k)}

    pair_rows = []
    example_rows = []
    novel_rows = []
    typical_rows = []
    heat = np.full((k, k), np.nan)
    for g1, g2 in combinations(range(k), 2):
        d1 = score_direction(entities[g1], entities[g2], rel_ids, e64, r64, scorer, observed, g1, g2)
        d2 = score_direction(entities[g2], entities[g1], rel_ids, e64, r64, scorer, observed, g2, g1)
        cand = pd.concat([d1, d2], ignore_index=True)
        cand, stats = filter_candidates(cand, unit768, canon)
        n = stats["n_unique_ht"]
        n_obs = int(cand["observed"].sum()) if n else 0
        unused = cand[cand["observed"] == 0] if n else cand
        pool = unused if len(unused) >= cfg.TOPK_PAIR else cand
        top = pool.nlargest(min(cfg.TOPK_PAIR, len(pool)), "prob") if len(pool) else pool
        pair_prob = float(top["prob"].mean()) if len(top) else 0.0
        heat[g1, g2] = heat[g2, g1] = pair_prob
        pair_rows.append(
            {
                "g1": g1,
                "g2": g2,
                "name_g1": names[g1],
                "name_g2": names[g2],
                "pair_prob": pair_prob,
                "topk_mean": pair_prob,
                "n_candidates": n,
                "n_raw": stats["n_raw"],
                "n_dropped_paraphrase": stats["n_dropped_paraphrase"],
                "n_dropped_same_noun": stats["n_dropped_same_noun"],
                "observed_overlap": n_obs,
                "n_used_for_topk": int(len(top)),
            }
        )
        for rank, row in enumerate(top.itertuples(index=False), start=1):
            example_rows.append(_triple_row(g1, g2, rank, row, canon, name_of_rel, lifts))
        if n:
            scored = _with_novelty(pool, canon, name_of_rel, lifts, rel_counts, rel_count_ref)
            above = scored[scored["novelty"] > 0]
            novel = above.nlargest(min(cfg.PAIR_NOVEL_TOPK, len(above)), "novelty") if len(above) else above
            typical = above.nsmallest(min(cfg.PAIR_NOVEL_TOPK, len(above)), "novelty") if len(above) else above
            for rank, row in enumerate(novel.itertuples(index=False), start=1):
                novel_rows.append(_triple_row(g1, g2, rank, row, canon, name_of_rel, lifts, extra=row))
            for rank, row in enumerate(typical.itertuples(index=False), start=1):
                typical_rows.append(_triple_row(g1, g2, rank, row, canon, name_of_rel, lifts, extra=row))
            preview = ""
            if len(novel):
                nr = novel.iloc[0]
                preview = (
                    f" novel1={canon.get(int(nr.h_idx))}--{name_of_rel.get(int(nr.r_idx))}-->"
                    f"{canon.get(int(nr.t_idx))} N={float(nr.novelty):.2f}"
                )
        else:
            preview = ""
        print(
            f"[60] pair {g1}-{g2} raw={stats['n_raw']} drop_cos={stats['n_dropped_paraphrase']} "
            f"drop_noun={stats['n_dropped_same_noun']} unique_ht={n} obs={n_obs} "
            f"topk={pair_prob:.4f}{preview}",
            flush=True,
        )

    pd.DataFrame(pair_rows).to_csv(cfg.OUT / "60_pair_scores.csv", index=False)
    pd.DataFrame(example_rows).to_csv(cfg.OUT / "60_pair_examples.csv", index=False)
    pd.DataFrame(novel_rows).to_csv(cfg.OUT / "60_pair_novel.csv", index=False)
    pd.DataFrame(typical_rows).to_csv(cfg.OUT / "60_pair_typical.csv", index=False)
    write_json(
        cfg.OUT / "60_manifest.json",
        {
            "k": k,
            "n_rel_cand": len(rel_ids),
            "rel_mass": cfg.REL_MASS,
            "top_entities": cfg.TOP_CLUSTERS,
            "pair_cluster_mode": "lift_surface",
            "pair_mass_min": cfg.PAIR_MASS_MIN,
            "pair_lift_min": cfg.PAIR_LIFT_MIN,
            "pair_entity_max_chars": cfg.PAIR_ENTITY_MAX_CHARS,
            "topk": cfg.TOPK_PAIR,
            "exclude_intra": cfg.EXCLUDE_INTRA_GROUP,
            "pair_cos_max": cfg.PAIR_COS_MAX,
            "pair_unique_ht": cfg.PAIR_UNIQUE_HT,
            "pair_name_contain_min": cfg.PAIR_NAME_CONTAIN_MIN,
            "pair_same_noun_stems": list(cfg.PAIR_SAME_NOUN_STEMS),
            "pair_generic_rel_stems": list(cfg.PAIR_GENERIC_REL_STEMS),
            "pair_generic_rel_penalty": cfg.PAIR_GENERIC_REL_PENALTY,
            "pair_role_template_penalty": cfg.PAIR_ROLE_TEMPLATE_PENALTY,
            "pair_novel_f_min": cfg.PAIR_NOVEL_F_MIN,
            "pair_novel_topk": cfg.PAIR_NOVEL_TOPK,
            "n_pairs": len(pair_rows),
            "uses_mapping_ids": False,
            "note": "단위는 v2 표면 엔티티. pair_prob 는 F 상위 평균. 삽화 새로움은 60_pair_novel.csv.",
        },
    )

    fp = _font()
    fig, ax = plt.subplots(figsize=(7.2, 6.2), dpi=140)
    fig.patch.set_facecolor("#F6F3EE")
    im = ax.imshow(heat, cmap="YlOrBr", vmin=np.nanmin(heat), vmax=np.nanmax(heat))
    labels = [f"G{g} {names[g]}" for g in range(k)]
    ax.set_xticks(range(k))
    ax.set_yticks(range(k))
    ax.set_xticklabels(labels, fontproperties=fp, fontsize=8, rotation=35, ha="right")
    ax.set_yticklabels(labels, fontproperties=fp, fontsize=8)
    for i in range(k):
        for j in range(k):
            if i == j or np.isnan(heat[i, j]):
                continue
            ax.text(j, i, f"{heat[i, j]:.2f}", ha="center", va="center", fontsize=8, color="#1C1917")
    ax.set_title(
        f"그룹 쌍 pair(g1,g2)  —  표면 엔티티 lift  ·  top-{cfg.TOPK_PAIR}  ·  cos<{cfg.PAIR_COS_MAX:g}",
        fontproperties=fp,
        fontsize=11,
    )
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(cfg.FIG / "60_pair_heatmap.png", facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    print(f"[60] wrote {cfg.OUT / '60_pair_scores.csv'} and {cfg.FIG / '60_pair_heatmap.png'}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
