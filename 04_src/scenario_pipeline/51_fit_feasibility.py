"""Stage 5-b — feasibility scorer (path A) and cluster-PMI baseline (path C).

Frozen 768d → PCA 64 → φ=[h⊙r⊙t; h⊙t; h⊙r; r⊙t] → logistic, then isotonic.
"""

from __future__ import annotations

import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.decomposition import PCA
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    roc_auc_score,
)

import config as cfg
from lib import ensure_out, load_kg_assets, write_json


def phi_from_idx(
    h_idx: np.ndarray,
    r_idx: np.ndarray,
    t_idx: np.ndarray,
    e64: np.ndarray,
    r64: np.ndarray,
) -> np.ndarray:
    h, r, t = e64[h_idx], r64[r_idx], e64[t_idx]
    blocks = {
        "hrt": h * r * t,
        "ht": h * t,
        "hr": h * r,
        "rt": r * t,
    }
    return np.hstack([blocks[name] for name in cfg.FEAT_BLOCKS]).astype(np.float64, copy=False)


def ece_score(y: np.ndarray, p: np.ndarray, n_bins: int = 15) -> float:
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    idx = np.digitize(p, bins) - 1
    idx = np.clip(idx, 0, n_bins - 1)
    ece = 0.0
    n = len(y)
    for b in range(n_bins):
        m = idx == b
        if not m.any():
            continue
        ece += (m.sum() / n) * abs(float(y[m].mean()) - float(p[m].mean()))
    return float(ece)


def pmi_table(train_pos: pd.DataFrame) -> dict:
    hc = train_pos["h_cluster"].to_numpy()
    rs = train_pos["r_std"].to_numpy()
    tc = train_pos["t_cluster"].to_numpy()
    ok = (hc >= 0) & (tc >= 0)
    hc, rs, tc = hc[ok], rs[ok], tc[ok]
    n = max(int(ok.sum()), 1)
    joint: dict[tuple[int, int, int], int] = {}
    ch: dict[int, int] = {}
    cr: dict[int, int] = {}
    ct: dict[int, int] = {}
    for a, b, c in zip(hc, rs, tc):
        key = (int(a), int(b), int(c))
        joint[key] = joint.get(key, 0) + 1
        ch[int(a)] = ch.get(int(a), 0) + 1
        cr[int(b)] = cr.get(int(b), 0) + 1
        ct[int(c)] = ct.get(int(c), 0) + 1
    return {"n": n, "joint": joint, "ch": ch, "cr": cr, "ct": ct}


def pmi_score(df: pd.DataFrame, tab: dict) -> np.ndarray:
    n = tab["n"]
    out = np.zeros(len(df), dtype=np.float64)
    for i, row in enumerate(df.itertuples(index=False)):
        a, b, c = int(row.h_cluster), int(row.r_std), int(row.t_cluster)
        j = tab["joint"].get((a, b, c), 0)
        # add-1 smoothing
        num = (j + 1) * n
        den = (tab["ch"].get(a, 0) + 1) * (tab["cr"].get(b, 0) + 1) * (tab["ct"].get(c, 0) + 1)
        out[i] = np.log(num / den)
    return out


def ranking_metrics(scores_true: np.ndarray, scores_neg: np.ndarray) -> dict:
    """One true vs its negatives. scores_neg shape (n, k)."""
    ranks = 1 + (scores_neg >= scores_true[:, None]).sum(axis=1)
    rr = 1.0 / ranks
    return {
        "mrr": float(rr.mean()),
        "hits@1": float((ranks <= 1).mean()),
        "hits@3": float((ranks <= 3).mean()),
        "hits@10": float((ranks <= 10).mean()),
    }


def main() -> int:
    ensure_out()
    cfg.FIG.mkdir(parents=True, exist_ok=True)
    path = cfg.OUT / "50_triples.csv"
    if not path.exists():
        raise SystemExit("out/50_triples.csv 가 없다. 먼저 python 50_build_kg_dataset.py")
    print("[51] load triples + embeddings", flush=True)
    df = pd.read_csv(path)
    assets = load_kg_assets()
    ent768 = assets["entity_emb"].astype(np.float64)
    rel768 = assets["rel_emb"].astype(np.float64)
    stacked = np.vstack([ent768, rel768])
    pca = PCA(n_components=cfg.EMB_DIM, random_state=cfg.SEED)
    pca.fit(stacked)
    e64 = pca.transform(ent768)
    r64 = pca.transform(rel768)

    y = (df["pos_neg"] == "pos").to_numpy().astype(np.int32)
    phi = phi_from_idx(
        df["h_idx"].to_numpy(),
        df["r_idx"].to_numpy(),
        df["t_idx"].to_numpy(),
        e64,
        r64,
    )
    train = (df["split"] == "train").to_numpy()
    ev = (df["split"] == "eval").to_numpy()
    print(f"[51] train={int(train.sum())} eval={int(ev.sum())} phi={phi.shape}", flush=True)

    clf = LogisticRegression(
        C=cfg.LOGREG_C,
        max_iter=cfg.LOGREG_MAX_ITER,
        solver="lbfgs",
    )
    clf.fit(phi[train], y[train])
    score = clf.decision_function(phi)
    raw_prob = clf.predict_proba(phi)[:, 1]

    # isotonic on a slice of train (no eval leak)
    rng = np.random.default_rng(cfg.SEED)
    train_i = np.where(train)[0]
    rng.shuffle(train_i)
    n_cal = max(100, int(0.2 * len(train_i)))
    cal_i, fit_note = train_i[:n_cal], "isotonic_on_20pct_train"
    iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
    iso.fit(score[cal_i], y[cal_i])
    prob = iso.predict(score)

    y_e, s_e, p_e = y[ev], score[ev], prob[ev]
    prauc_a = float(average_precision_score(y_e, s_e))
    rocauc_a = float(roc_auc_score(y_e, s_e))
    brier = float(brier_score_loss(y_e, p_e))
    ece = ece_score(y_e, p_e)

    train_pos = df[train & (df["pos_neg"] == "pos")]
    tab = pmi_table(train_pos)
    c_score = pmi_score(df, tab)
    prauc_c = float(average_precision_score(y_e, c_score[ev]))
    rocauc_c = float(roc_auc_score(y_e, c_score[ev]))

    # filtered-style ranking: each eval pos vs the 5 negs sharing its row-group
    ev_pos = df[ev & (df["pos_neg"] == "pos")].reset_index()
    ev_neg = df[ev & (df["pos_neg"] == "neg")]
    true_s, neg_s = [], []
    for row in ev_pos.itertuples():
        s_true = float(score[int(row.index)])
        pool = ev_neg[ev_neg["publication_number"] == row.publication_number]
        # take negatives spawned from same triple via matching h,r of original when possible
        same = df.loc[ev & (df["pos_neg"] == "neg") & (df["publication_number"] == row.publication_number)]
        # use the 5 negs that follow this positive in construction: same pub and nearby — fallback all pub negs sample
        ns = score[same.index.to_numpy()] if len(same) else np.array([])
        if ns.size < 5:
            extra = ev_neg.sample(n=min(5, len(ev_neg)), random_state=cfg.SEED)
            ns = score[extra.index.to_numpy()]
        else:
            ns = ns[:5]
        true_s.append(s_true)
        neg_s.append(ns[:5])
    # pad
    neg_mat = np.vstack([np.pad(a, (0, 5 - len(a)), constant_values=-1e9) if len(a) < 5 else a[:5] for a in neg_s])
    rank = ranking_metrics(np.array(true_s), neg_mat)

    gates = {
        "prauc_ge_gate": {"pass": prauc_a >= cfg.PRAUC_GATE, "value": prauc_a, "gate": cfg.PRAUC_GATE},
        "beats_path_c": {"pass": prauc_a > prauc_c, "prauc_a": prauc_a, "prauc_c": prauc_c},
        "ece_le_gate": {"pass": ece <= cfg.ECE_GATE, "value": ece, "gate": cfg.ECE_GATE},
        "audit_recorded": {"pass": (cfg.OUT / "50_audit_sample.csv").exists(), "status": "pending_human"},
    }
    gates["all_pass"] = bool(
        gates["prauc_ge_gate"]["pass"] and gates["beats_path_c"]["pass"] and gates["ece_le_gate"]["pass"]
    )

    np.savez(
        cfg.OUT / "51_model.npz",
        pca_components=pca.components_,
        pca_mean=pca.mean_,
        logreg_coef=clf.coef_.ravel(),
        logreg_intercept=np.array([clf.intercept_[0]]),
        iso_x=np.asarray(iso.X_thresholds_, dtype=np.float64),
        iso_y=np.asarray(iso.y_thresholds_, dtype=np.float64),
        emb_dim=np.array([cfg.EMB_DIM]),
    )
    dist = pd.DataFrame(
        {
            "split": df["split"],
            "pos_neg": df["pos_neg"],
            "score": score,
            "prob": prob,
            "score_c": c_score,
        }
    )
    dist.to_csv(cfg.OUT / "51_score_dist.csv", index=False)

    eval_json = {
        "path": cfg.FEAS_PATH,
        "n_train": int(train.sum()),
        "n_eval": int(ev.sum()),
        "pca_explained": float(pca.explained_variance_ratio_.sum()),
        "prauc": prauc_a,
        "rocauc": rocauc_a,
        "prauc_c": prauc_c,
        "rocauc_c": rocauc_c,
        "prauc_lift_vs_c": prauc_a - prauc_c,
        "brier": brier,
        "ece": ece,
        "calibration": {"method": cfg.CALIBRATION, "fit": fit_note},
        **rank,
        "gates": gates,
        "note": "F는 임베딩 기하의 어울림이다. (C)를 못 넘으면 기술적 가능성이라 부르지 않는다.",
    }
    write_json(cfg.OUT / "51_eval.json", eval_json)

    frac_pos, mean_pred = calibration_curve(y_e, p_e, n_bins=10, strategy="uniform")
    fig, ax = plt.subplots(figsize=(5.2, 5.0), dpi=130)
    ax.plot([0, 1], [0, 1], ls="--", color="#8A7A6A", lw=1)
    ax.plot(mean_pred, frac_pos, marker="o", color="#2C5F5D")
    ax.set_xlabel("predicted prob")
    ax.set_ylabel("empirical positive rate")
    ax.set_title(f"calibration  ECE={ece:.3f}")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    fig.tight_layout()
    fig.savefig(cfg.FIG / "51_calibration.png", bbox_inches="tight")
    plt.close(fig)

    print(
        f"[51] PR-AUC A={prauc_a:.3f} C={prauc_c:.3f} lift={prauc_a - prauc_c:.3f} "
        f"ECE={ece:.3f} MRR={rank['mrr']:.3f}",
        flush=True,
    )
    if not gates["all_pass"]:
        failed = [k for k, v in gates.items() if isinstance(v, dict) and not v.get("pass", True)]
        print(f"[51] GATE FAIL: {failed}", file=sys.stderr, flush=True)
        return 1
    print("[51] gates passed (human audit of negatives still pending)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
