"""Stage 8 — sliding-window validation of group-subset scenarios.

Object is s = subset of latent groups. Later realization is occupancy
change of that subset, not string match of display triples.
Refits PCA, BGMM, F, π̂, occ per window. Encoder stays frozen.
Contract: docs/02_stage_specs.md stage 8, docs/03_locked_spec.md.
"""

from __future__ import annotations

import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib import pyplot as plt
from scipy.optimize import linear_sum_assignment
from sklearn.decomposition import PCA
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

import config as cfg
from lib import (
    ensure_out,
    l2_rows,
    load_kg_assets,
    load_patents,
    lookup_index,
    write_json,
    zscore_block,
)
from importlib.machinery import SourceFileLoader

_s20 = SourceFileLoader("s20", str(cfg.HERE / "20_fit_bgmm.py")).load_module()
_s40 = SourceFileLoader("s40", str(cfg.HERE / "40_group_time.py")).load_module()
_s50 = SourceFileLoader("s50", str(cfg.HERE / "50_build_kg_dataset.py")).load_module()
_s51 = SourceFileLoader("s51", str(cfg.HERE / "51_fit_feasibility.py")).load_module()
_s60 = SourceFileLoader("s60", str(cfg.HERE / "60_pair_scores.py")).load_module()
_s61 = SourceFileLoader("s61", str(cfg.HERE / "61_scenario_space.py")).load_module()
_s70 = SourceFileLoader("s70", str(cfg.HERE / "70_quadrants.py")).load_module()

WINDOW_ORDER = list(cfg.WINDOWS.keys())
ABLATIONS = tuple(cfg.ABLATIONS)


def _font():
    path = Path("/usr/share/fonts/truetype/unfonts-core/UnDotum.ttf")
    if path.exists():
        font_manager.fontManager.addfont(str(path))
        fp = font_manager.FontProperties(fname=str(path))
        plt.rcParams["font.family"] = fp.get_name()
        plt.rcParams["axes.unicode_minus"] = False
        return fp
    return None


def mask_upto(index: pd.DataFrame, last: str) -> np.ndarray:
    allowed = WINDOW_ORDER[: WINDOW_ORDER.index(last) + 1]
    return index["window"].astype(str).isin(allowed).to_numpy()


def mask_window(index: pd.DataFrame, window: str) -> np.ndarray:
    return (index["window"].astype(str) == window).to_numpy()


def _weighted_blocks(blocks: dict, rows: np.ndarray, stats: dict[str, tuple[np.ndarray, np.ndarray]] | None):
    parts = []
    fitted: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for name, weight in (("txt", "TXT"), ("kg", "KG"), ("cpc", "CPC")):
        raw = np.asarray(blocks[name][rows], dtype=np.float64)
        if stats is None:
            mean = raw.mean(axis=0)
            std = raw.std(axis=0)
            std = np.where(std < 1e-12, 1.0, std)
            fitted[name] = (mean, std)
        else:
            mean, std = stats[name]
        z = (raw - mean) / std
        parts.append(l2_rows(z) * float(cfg.BLOCK_WEIGHTS[weight]))
    concat = np.hstack(parts)
    return concat, (fitted if stats is None else stats)


def assemble_train(blocks: dict, rows: np.ndarray) -> tuple[np.ndarray, PCA, dict]:
    concat, stats = _weighted_blocks(blocks, rows, None)
    n_comp = min(cfg.PCA_DIM, concat.shape[0] - 1, concat.shape[1])
    pca = PCA(n_components=n_comp, random_state=cfg.SEED)
    x = pca.fit_transform(concat).astype(np.float64, copy=False)
    return x, pca, stats


def assemble_apply(blocks: dict, rows: np.ndarray, pca: PCA, stats: dict) -> np.ndarray:
    concat, _ = _weighted_blocks(blocks, rows, stats)
    return pca.transform(concat).astype(np.float64, copy=False)


def frozen_concat(blocks: dict, rows: np.ndarray) -> np.ndarray:
    """Matching space: frozen encoder blocks, not window PCA."""
    parts = [
        l2_rows(np.asarray(blocks[name][rows], dtype=np.float64))
        for name in ("txt", "kg", "cpc")
    ]
    return np.hstack(parts)


def fit_groups(x: np.ndarray):
    model = _s20.fit_bgmm(x, cfg.SEED)
    full = model.predict_proba(x)
    resp, valid, _n_hard = _s20.filter_valid(full, model.weights_)
    return resp, valid, model


def predict_groups(model, x: np.ndarray, valid: np.ndarray) -> np.ndarray:
    kept = model.predict_proba(x)[:, valid]
    row_sum = kept.sum(axis=1, keepdims=True)
    empty = row_sum[:, 0] < 1e-15
    if empty.any():
        kept[empty] = 1.0 / max(kept.shape[1], 1)
        row_sum = kept.sum(axis=1, keepdims=True)
    return kept / np.clip(row_sum, 1e-15, None)


def centroids(emb: np.ndarray, resp: np.ndarray) -> np.ndarray:
    mass = resp.sum(axis=0)
    cents = (resp.T @ emb) / np.clip(mass[:, None], 1e-15, None)
    nrm = np.clip(np.linalg.norm(cents, axis=1, keepdims=True), 1e-15, None)
    return cents / nrm


def hungarian(train_c: np.ndarray, eval_c: np.ndarray) -> tuple[dict[int, int], pd.DataFrame]:
    sim = train_c @ eval_c.T
    cost = 1.0 - sim
    r, c = linear_sum_assignment(cost)
    mapping: dict[int, int] = {}
    rows = []
    matched_eval = set()
    for i, j in zip(r, c):
        mapping[int(i)] = int(j)
        matched_eval.add(int(j))
        rows.append(
            {
                "train_group": int(i),
                "eval_group": int(j),
                "cosine": float(sim[i, j]),
                "unmatched": 0,
            }
        )
    for i in range(train_c.shape[0]):
        if i not in mapping:
            rows.append(
                {
                    "train_group": int(i),
                    "eval_group": -1,
                    "cosine": float("nan"),
                    "unmatched": 1,
                }
            )
            mapping[int(i)] = -1
    return mapping, pd.DataFrame(rows)


def pi_hat(resp: np.ndarray, windows: np.ndarray, last: str) -> dict[int, float]:
    mask = windows == last
    n_last = int(mask.sum())
    k = resp.shape[1]
    alpha = float(cfg.DIRICHLET_ALPHA0)
    sum_r = resp[mask].sum(axis=0) if n_last else np.zeros(k)
    hat = (alpha / k + sum_r) / (alpha + max(n_last, 1))
    hat = hat / hat.sum()
    return {g: float(hat[g]) for g in range(k)}


def build_train_triples(patents: list[dict], assets: dict) -> pd.DataFrame:
    rng = np.random.default_rng(cfg.SEED)
    rel_keys = list(assets["rel_mapping"].keys())
    entity_keys = list(assets["entity_mapping"].keys())
    entity_clusters = np.array([int(c) for c in assets["entity_mapping"].values()], dtype=np.int32)
    rel_bucket = np.array([int(assets["rel_mapping"][k]) for k in rel_keys], dtype=np.int32)
    n_ent = assets["entity_emb"].shape[0]
    n_rel = assets["rel_emb"].shape[0]
    positives = []
    for rec in patents:
        for head, rel, tail in rec["triples_v2"]:
            hi = lookup_index(head, assets["ent_exact"], assets["ent_fold"])
            ri = lookup_index(rel, assets["rel_exact"], assets["rel_fold"])
            ti = lookup_index(tail, assets["ent_exact"], assets["ent_fold"])
            if hi is None or ri is None or ti is None:
                continue
            hc = assets["cluster_of"].get(head) or assets["cluster_of_fold"].get(head.casefold())
            tc = assets["cluster_of"].get(tail) or assets["cluster_of_fold"].get(tail.casefold())
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
                }
            )
    if not positives:
        raise SystemExit("학습 창 양 트리플이 0이다.")
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
    ent_p = freq / max(freq.sum(), 1.0)
    ent_idx = np.arange(n_ent)
    rel_idx = np.arange(n_rel)
    other_rels = [rel_idx[rel_bucket != b] for b in range(int(rel_bucket.max()) + 1)]

    def sample_entity(forbid: set[int]) -> int:
        for _ in range(40):
            j = int(rng.choice(ent_idx, p=ent_p))
            if j not in forbid:
                return j
        return int(rng.integers(0, n_ent))

    negatives = []
    for p in positives:
        for _ in range(cfg.NEG_RATIO):
            kind = _s50._pick_corrupt(rng)
            hi, ri, ti = p["h_idx"], p["r_idx"], p["t_idx"]
            hc, rs, tc = p["h_cluster"], p["r_std"], p["t_cluster"]
            nh, nr, nt = p["h"], p["r"], p["t"]
            chi, cri, cti, chc, crs, ctc = hi, ri, ti, hc, rs, tc
            ch, cr, ct = nh, nr, nt
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
                hit_s = (chi, cri, cti) in observed_surface
                hit_b = hc >= 0 and tc >= 0 and (chc, crs, ctc) in observed_std
                if not (cfg.NEG_FILTERED and (hit_s or hit_b)):
                    break
            negatives.append(
                {
                    "h": ch,
                    "r": cr,
                    "t": ct,
                    "h_idx": int(chi),
                    "r_idx": int(cri),
                    "t_idx": int(cti),
                    "pos_neg": "neg",
                }
            )
    pos_rows = [{**p, "pos_neg": "pos"} for p in positives]
    return pd.DataFrame(pos_rows + negatives)


def fit_scorer(df: pd.DataFrame, assets: dict) -> dict:
    ent768 = assets["entity_emb"].astype(np.float64)
    rel768 = assets["rel_emb"].astype(np.float64)
    pca = PCA(n_components=min(cfg.EMB_DIM, ent768.shape[0] + rel768.shape[0] - 1), random_state=cfg.SEED)
    pca.fit(np.vstack([ent768, rel768]))
    e64 = pca.transform(ent768)
    r64 = pca.transform(rel768)
    y = (df["pos_neg"] == "pos").to_numpy().astype(np.int32)
    phi = _s51.phi_from_idx(
        df["h_idx"].to_numpy(),
        df["r_idx"].to_numpy(),
        df["t_idx"].to_numpy(),
        e64,
        r64,
    )
    clf = LogisticRegression(C=cfg.LOGREG_C, max_iter=cfg.LOGREG_MAX_ITER, solver="lbfgs")
    clf.fit(phi, y)
    score = clf.decision_function(phi)
    rng = np.random.default_rng(cfg.SEED)
    idx = np.arange(len(y))
    rng.shuffle(idx)
    n_cal = max(100, int(0.2 * len(idx)))
    cal = idx[:n_cal]
    iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
    if len(np.unique(y[cal])) >= 2:
        iso.fit(score[cal], y[cal])
        iso_x = np.asarray(iso.X_thresholds_, dtype=np.float64)
        iso_y = np.asarray(iso.y_thresholds_, dtype=np.float64)
    else:
        iso_x = np.array([float(score.min()), float(score.max())], dtype=np.float64)
        iso_y = np.array([0.0, 1.0], dtype=np.float64)
    return {
        "components": pca.components_,
        "mean": pca.mean_,
        "coef": clf.coef_.ravel().astype(np.float64),
        "intercept": float(clf.intercept_[0]),
        "iso_x": iso_x,
        "iso_y": iso_y,
    }


def pair_matrix(resp: np.ndarray, patents: list[dict], assets: dict, scorer: dict) -> dict[tuple[int, int], float]:
    k = resp.shape[1]
    e768 = assets["entity_emb"].astype(np.float64, copy=False)
    unit768 = e768 / np.clip(np.linalg.norm(e768, axis=1, keepdims=True), 1e-12, None)
    e64 = _s60.to64(e768, scorer)
    r64 = _s60.to64(assets["rel_emb"], scorer)
    rel_ids, _names, _tot, _counts = _s60.relation_candidates(patents, assets)
    acc, canon = _s60.group_surface_profiles(resp, patents, assets)
    entities, _table, _lifts = _s60.select_distinctive_surface(acc, canon)
    observed: set[tuple[int, int, int]] = set()
    for rec in patents:
        for head, rel, tail in rec["triples_v2"]:
            hi = lookup_index(head, assets["ent_exact"], assets["ent_fold"])
            ri = lookup_index(rel, assets["rel_exact"], assets["rel_fold"])
            ti = lookup_index(tail, assets["ent_exact"], assets["ent_fold"])
            if hi is not None and ri is not None and ti is not None:
                observed.add((int(hi), int(ri), int(ti)))
    pair: dict[tuple[int, int], float] = {}
    for g1, g2 in combinations(range(k), 2):
        d1 = _s60.score_direction(entities[g1], entities[g2], rel_ids, e64, r64, scorer, observed, g1, g2)
        d2 = _s60.score_direction(entities[g2], entities[g1], rel_ids, e64, r64, scorer, observed, g2, g1)
        cand = pd.concat([d1, d2], ignore_index=True)
        cand, _stats = _s60.filter_candidates(cand, unit768, canon)
        unused = cand[cand["observed"] == 0] if len(cand) else cand
        pool = unused if len(unused) >= cfg.TOPK_PAIR else cand
        top = pool.nlargest(min(cfg.TOPK_PAIR, len(pool)), "prob") if len(pool) else pool
        pair[(g1, g2)] = float(top["prob"].mean()) if len(top) else 0.0
    return pair


def enumerate_for_k(k: int, pi: dict[int, float], pair: dict[tuple[int, int], float], beta: float) -> pd.DataFrame:
    names = {g: f"G{g}" for g in range(k)}
    sizes = [s for s in cfg.SCENARIO_SIZES if s <= k]
    if k < 2 or not sizes or not pair:
        return pd.DataFrame()
    saved = cfg.SCENARIO_SIZES
    try:
        cfg.SCENARIO_SIZES = tuple(sizes)
        return _s61.enumerate_scenarios(k, pi, pair, names, beta)
    finally:
        cfg.SCENARIO_SIZES = saved


def score_table(k: int, pi: dict[int, float], pair: dict[tuple[int, int], float], ablation: str) -> pd.DataFrame:
    if ablation == "no_F":
        pair_use = {key: 1.0 for key in pair}
        beta = 1.0
    elif ablation == "no_trend":
        pair_use = pair
        pi = {g: 1.0 / k for g in range(k)}
        beta = float(cfg.BETA)
    else:
        pair_use = pair
        beta = float(cfg.BETA)
    return enumerate_for_k(k, pi, pair_use, beta)


def occ_of(profile: np.ndarray, groups: tuple[int, ...]) -> float:
    return _s70.occ_share(profile, groups)


def lift_at_k(p: np.ndarray, delta: np.ndarray, k: int) -> float:
    n = len(p)
    if n == 0:
        return float("nan")
    take = min(k, n)
    order = np.argsort(-p)[:take]
    num = float(delta[order].mean())
    den = float(delta.mean())
    if abs(den) < 1e-15:
        return float("nan")
    return num / den


def metrics_from(df: pd.DataFrame, k_list: tuple[int, ...]) -> dict[str, float]:
    p = df["p_norm"].to_numpy(dtype=np.float64)
    delta = df["delta_occ"].to_numpy(dtype=np.float64)
    y = (delta > 0).astype(np.int32)
    n = len(df)
    ks = tuple(sorted({int(k) for k in k_list} | {1, 2, 3, n}))
    out: dict[str, float] = {}
    for k in ks:
        if k <= 0:
            continue
        out[f"lift_at_{k}"] = lift_at_k(p, delta, int(k))
    opp = df[df["quadrant"] == "opportunity"]
    con = df[df["quadrant"] == "contradiction"]
    out["n_opportunity"] = float(len(opp))
    out["n_contradiction"] = float(len(con))
    out["opportunity_realization"] = float((opp["delta_occ"] > 0).mean()) if len(opp) else float("nan")
    out["contradiction_intrusion"] = float((con["delta_occ"] > 0).mean()) if len(con) else float("nan")
    if y.min() == y.max() or len(np.unique(p)) < 2:
        out["auc"] = float("nan")
    else:
        out["auc"] = float(roc_auc_score(y, p))
    out["n_scenarios"] = float(len(df))
    return out


def bootstrap_ci(df: pd.DataFrame, metric: str, rng: np.random.Generator) -> tuple[float, float]:
    vals = []
    n = len(df)
    if n == 0:
        return float("nan"), float("nan")
    for _ in range(cfg.BOOTSTRAP_N):
        idx = rng.integers(0, n, size=n)
        m = metrics_from(df.iloc[idx], cfg.LIFT_KS)
        vals.append(m[metric])
    arr = np.asarray(vals, dtype=np.float64)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return float("nan"), float("nan")
    return float(np.quantile(arr, 0.025)), float(np.quantile(arr, 0.975))


def one_split(
    train_last: str,
    eval_w: str,
    index: pd.DataFrame,
    patents: list[dict],
    blocks: dict,
    assets: dict,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    train_m = mask_upto(index, train_last)
    eval_m = mask_window(index, eval_w)
    train_rows = np.where(train_m)[0]
    eval_rows = np.where(eval_m)[0]
    print(f"[80] split train≤{train_last} n={len(train_rows)}  eval={eval_w} n={len(eval_rows)}", flush=True)
    x_tr, pca_tr, stats_tr = assemble_train(blocks, train_rows)
    x_ev_ind, pca_ev, _stats_ev = assemble_train(blocks, eval_rows)
    x_ev_pred = assemble_apply(blocks, eval_rows, pca_tr, stats_tr)
    print(f"[80]   PCA train {x_tr.shape} eval-ind {x_ev_ind.shape}", flush=True)
    resp_tr, valid_tr, model_tr = fit_groups(x_tr)
    resp_ev_ind, _valid_ev, _model_ev = fit_groups(x_ev_ind)
    resp_ev = predict_groups(model_tr, x_ev_pred, valid_tr)
    k_tr, k_ev = resp_tr.shape[1], resp_ev_ind.shape[1]
    print(f"[80]   K_train={k_tr} K_eval_ind={k_ev} (점유는 학습 그룹을 평가창에 투영)", flush=True)
    emb_tr = frozen_concat(blocks, train_rows)
    emb_ev = frozen_concat(blocks, eval_rows)
    _map, match_df = hungarian(centroids(emb_tr, resp_tr), centroids(emb_ev, resp_ev_ind))
    match_df.insert(0, "train_window", train_last)
    match_df.insert(1, "eval_window", eval_w)
    if k_tr < 2:
        print("[80]   유효 그룹 < 2 → 이 창은 조합을 열거하지 않는다.", flush=True)
        empty = pd.DataFrame()
        meta = {
            "k_train": k_tr,
            "k_eval_independent": k_ev,
            "n_train": int(len(train_rows)),
            "n_eval": int(len(eval_rows)),
            "skipped": "k_train_lt_2",
            "assignment": "predict_train_groups_on_eval",
            "match_cosine_median": float(np.nanmedian(match_df.loc[match_df["unmatched"] == 0, "cosine"]))
            if (match_df["unmatched"] == 0).any()
            else float("nan"),
        }
        return empty, match_df, meta
    train_pats = [patents[i] for i in train_rows]
    eval_pats = [patents[i] for i in eval_rows]
    print("[80]   fit F on train triples", flush=True)
    triples = build_train_triples(train_pats, assets)
    scorer = fit_scorer(triples, assets)
    print("[80]   pair scores", flush=True)
    pair = pair_matrix(resp_tr, train_pats, assets, scorer)
    windows_tr = index.loc[train_rows, "window"].astype(str).to_numpy()
    pi = pi_hat(resp_tr, windows_tr, train_last)
    idx_tr = index.iloc[train_rows].reset_index(drop=True)
    idx_ev = index.iloc[eval_rows].reset_index(drop=True)
    u_tr = _s70.entity_profiles(resp_tr, train_pats, idx_tr, assets)
    u_ev = _s70.entity_profiles(resp_ev, eval_pats, idx_ev, assets)

    outcome_rows = []
    for ablation in ABLATIONS:
        table = score_table(k_tr, pi, pair, ablation)
        if table.empty:
            continue
        occ_train = []
        occ_eval = []
        for row in table.itertuples(index=False):
            groups = _s70.parse_groups(row.groups)
            occ_train.append(occ_of(u_tr, groups))
            occ_eval.append(occ_of(u_ev, groups))
        table = table.copy()
        table["occ_train"] = occ_train
        table["occ_eval"] = occ_eval
        table["delta_occ"] = table["occ_eval"] - table["occ_train"]
        _occ_t, _p_t, q = _s70.classify(table, "occ_train", "p_norm")
        table["occ_tercile"] = _occ_t.to_numpy()
        table["p_tercile"] = _p_t.to_numpy()
        table["quadrant"] = q.to_numpy()
        for rec in table.itertuples(index=False):
            outcome_rows.append(
                {
                    "train_window": train_last,
                    "eval_window": eval_w,
                    "ablation": ablation,
                    "scenario_id": rec.scenario_id,
                    "groups": rec.groups,
                    "size": int(rec.size),
                    "p_norm": float(rec.p_norm),
                    "p_trend": float(rec.p_trend),
                    "f_min": float(rec.f_min),
                    "occ_train": float(rec.occ_train),
                    "occ_eval": float(rec.occ_eval),
                    "delta_occ": float(rec.delta_occ),
                    "quadrant": rec.quadrant,
                    "k_train": k_tr,
                    "k_eval_independent": k_ev,
                }
            )
    meta = {
        "k_train": k_tr,
        "k_eval_independent": k_ev,
        "n_train": int(len(train_rows)),
        "n_eval": int(len(eval_rows)),
        "n_scenarios": int(len(outcome_rows) // max(len(ABLATIONS), 1)),
        "assignment": "predict_train_groups_on_eval",
        "match_cosine_median": float(np.nanmedian(match_df.loc[match_df["unmatched"] == 0, "cosine"]))
        if (match_df["unmatched"] == 0).any()
        else float("nan"),
    }
    return pd.DataFrame(outcome_rows), match_df, meta


def draw_lift(metrics: pd.DataFrame) -> None:
    fp = _font()
    splits = list(metrics[["train_window", "eval_window"]].drop_duplicates().itertuples(index=False))
    nax = max(len(splits), 1)
    fig, axes = plt.subplots(1, nax, figsize=(5.6 * nax, 4.2), dpi=140)
    fig.patch.set_facecolor("#F6F3EE")
    if nax == 1:
        axes = [axes]
    colors = {"full": "#2C5F5D", "no_F": "#8B6914", "no_trend": "#6B3A3A"}
    ks = sorted(
        int(m.replace("lift_at_", ""))
        for m in metrics["metric"].unique()
        if str(m).startswith("lift_at_")
    )
    if not ks:
        ks = list(cfg.LIFT_KS)
    for ax, (tr, ev) in zip(axes, splits):
        ax.set_facecolor("#F6F3EE")
        sub = metrics[(metrics["train_window"] == tr) & (metrics["eval_window"] == ev)]
        for ab in ABLATIONS:
            ys = []
            for k in ks:
                hit = sub[(sub["ablation"] == ab) & (sub["metric"] == f"lift_at_{k}")]
                ys.append(float(hit["value"].iloc[0]) if len(hit) else float("nan"))
            ax.plot(ks, ys, marker="o", color=colors[ab], label=ab, linewidth=1.6)
        ax.axhline(1.0, color="#A8A29E", linestyle="--", linewidth=0.8)
        ax.set_title(f"학습 ≤{tr} → 평가 {ev}", fontproperties=fp, fontsize=11)
        ax.set_xlabel("k", fontproperties=fp)
        ax.set_ylabel("lift@k", fontproperties=fp)
        ax.legend(frameon=False, fontsize=8)
    fig.suptitle("점유 증가 lift  ·  그룹 묶음 s  ·  문장 매칭 아님", fontproperties=fp, fontsize=12, y=1.02)
    fig.tight_layout()
    cfg.FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(cfg.FIG / "80_lift_curve.png", facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    ensure_out()
    idx_path = cfg.OUT / "10_index.csv"
    blk_path = cfg.OUT / "10_blocks.npz"
    if not idx_path.exists() or not blk_path.exists():
        raise SystemExit("단계 1 산출물이 없다. 10_build_features.py 를 먼저 실행하라.")
    index = pd.read_csv(idx_path)
    blocks = np.load(blk_path)
    patents = load_patents()
    if len(patents) != len(index):
        raise SystemExit(f"특허 {len(patents)} != index {len(index)}")
    assets = load_kg_assets()
    rng = np.random.default_rng(cfg.SEED)

    all_out = []
    all_match = []
    all_metrics = []
    split_meta = []
    for train_last, eval_w in cfg.SLIDING:
        outcomes, match, meta = one_split(train_last, eval_w, index, patents, blocks, assets)
        all_match.append(match)
        split_meta.append({"train": train_last, "eval": eval_w, **meta})
        if outcomes.empty:
            print(f"[80] {train_last}->{eval_w} skipped ({meta.get('skipped')})", flush=True)
            continue
        all_out.append(outcomes)
        for ablation, sub in outcomes.groupby("ablation"):
            m = metrics_from(sub, cfg.LIFT_KS)
            for name, val in m.items():
                lo, hi = (float("nan"), float("nan"))
                if name.startswith("lift_at_") or name in {
                    "opportunity_realization",
                    "contradiction_intrusion",
                    "auc",
                }:
                    lo, hi = bootstrap_ci(sub, name, rng)
                all_metrics.append(
                    {
                        "train_window": train_last,
                        "eval_window": eval_w,
                        "metric": name,
                        "value": val,
                        "ci_lo": lo,
                        "ci_hi": hi,
                        "ablation": ablation,
                    }
                )
    if not all_out:
        match_df = pd.concat(all_match, ignore_index=True) if all_match else pd.DataFrame()
        match_df.to_csv(cfg.OUT / "80_group_matching.csv", index=False)
        write_json(cfg.OUT / "80_manifest.json", {"splits": split_meta, "error": "no_enumerable_split"})
        raise SystemExit("모든 창에서 유효 그룹이 2 미만이다. 조합을 열거하지 못했다.")
    out_df = pd.concat(all_out, ignore_index=True)
    match_df = pd.concat(all_match, ignore_index=True)
    met_df = pd.DataFrame(all_metrics)
    out_df.to_csv(cfg.OUT / "80_scenario_outcomes.csv", index=False)
    match_df.to_csv(cfg.OUT / "80_group_matching.csv", index=False)
    met_df.to_csv(cfg.OUT / "80_window_metrics.csv", index=False)
    draw_lift(met_df)

    def pick(tr, ev, ab, name):
        hit = met_df[
            (met_df["train_window"] == tr)
            & (met_df["eval_window"] == ev)
            & (met_df["ablation"] == ab)
            & (met_df["metric"] == name)
        ]
        return float(hit["value"].iloc[0]) if len(hit) else float("nan")

    no_f_notes = []
    for tr, ev in cfg.SLIDING:
        if not ((met_df["train_window"] == tr) & (met_df["eval_window"] == ev)).any():
            print(f"[80] {tr}->{ev}  (열거 없음)", flush=True)
            continue
        full_l = pick(tr, ev, "full", "lift_at_10")
        nof_l = pick(tr, ev, "no_F", "lift_at_10")
        improved = bool(np.isfinite(full_l) and np.isfinite(nof_l) and full_l > nof_l)
        no_f_notes.append({"split": f"{tr}->{ev}", "full_lift10": full_l, "no_F_lift10": nof_l, "full_beats_no_F": improved})
        opp_r = pick(tr, ev, "full", "opportunity_realization")
        con_r = pick(tr, ev, "full", "contradiction_intrusion")
        n_opp = pick(tr, ev, "full", "n_opportunity")
        print(
            f"[80] {tr}->{ev}  lift@10 full={full_l:.3f} no_F={nof_l:.3f} "
            f"no_trend={pick(tr, ev, 'no_trend', 'lift_at_10'):.3f}",
            flush=True,
        )
        print(
            f"[80]   기회실현={opp_r:.3f} n_opp={n_opp:.0f}  모순침범={con_r:.3f}  "
            f"AUC={pick(tr, ev, 'full', 'auc'):.3f}",
            flush=True,
        )
        if not improved:
            print("[80]   no_F 대비 개선 없음 → 단계 5 기여를 주장하지 않는다.", flush=True)
        if not (np.isfinite(opp_r) and np.isfinite(con_r) and con_r < opp_r):
            print("[80]   모순 침범 ≥ 기회 실현 → 사분면 해석을 주장하지 않는다.", flush=True)

    write_json(
        cfg.OUT / "80_manifest.json",
        {
            "protocol": [{"train_upto": a, "eval": b} for a, b in cfg.SLIDING],
            "object": "group_subset_occupancy_delta",
            "not_validated": "display_triple_string_match",
            "known_leakage": list(cfg.KNOWN_LEAKAGE),
            "frozen": list(cfg.FROZEN_ACROSS_WINDOWS),
            "refit": list(cfg.REFIT_PER_WINDOW),
            "ablations": list(ABLATIONS),
            "bootstrap_n": cfg.BOOTSTRAP_N,
            "matching": "hungarian_cosine_on_frozen_block_concat",
            "splits": split_meta,
            "no_F_gate": no_f_notes,
            "tfidf_sensitivity": "not_run",
        },
    )
    print(f"[80] wrote {cfg.OUT / '80_window_metrics.csv'}", flush=True)
    print(f"[80] wrote {cfg.FIG / '80_lift_curve.png'}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
