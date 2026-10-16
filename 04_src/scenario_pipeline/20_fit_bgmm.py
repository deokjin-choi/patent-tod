"""Stage 2 — Bayesian GMM latent tech groups.

sklearn BayesianGaussianMixture, diag covariance, DP prior.
Valid groups: π_g ≥ 1/(2 K_max) and hard-assign count ≥ MIN_GROUP_PATENTS.
Contract: docs/02_stage_specs.md, docs/03_locked_spec.md.
"""

from __future__ import annotations

# Import order: sklearn before any torch-adjacent import.
import sys
from collections import Counter
from itertools import combinations

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score
from sklearn.mixture import BayesianGaussianMixture

import config as cfg
from lib import (
    cpc_key,
    entity_cluster,
    ensure_out,
    load_kg_assets,
    load_patents,
    write_json,
)


def _require_stage1() -> tuple[np.ndarray, pd.DataFrame]:
    x_path = cfg.OUT / "10_x.npy"
    idx_path = cfg.OUT / "10_index.csv"
    if not x_path.exists() or not idx_path.exists():
        raise SystemExit("단계 1 산출물이 없다. 먼저 python 10_build_features.py 를 실행하라.")
    x = np.load(x_path)
    index = pd.read_csv(idx_path)
    if x.shape[0] != len(index):
        raise SystemExit(f"10_x.npy rows {x.shape[0]} != 10_index.csv {len(index)}")
    return x, index


def fit_bgmm(x: np.ndarray, seed: int) -> BayesianGaussianMixture:
    model = BayesianGaussianMixture(
        n_components=cfg.K_MAX,
        covariance_type=cfg.COVARIANCE_TYPE,
        weight_concentration_prior_type=cfg.WEIGHT_CONCENTRATION_PRIOR_TYPE,
        weight_concentration_prior=cfg.WEIGHT_CONCENTRATION_PRIOR,
        n_init=cfg.N_INIT,
        max_iter=cfg.MAX_ITER,
        tol=cfg.TOL,
        random_state=seed,
    )
    model.fit(x)
    return model


def filter_valid(resp: np.ndarray, weights: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    hard = resp.argmax(axis=1)
    n_hard = np.bincount(hard, minlength=resp.shape[1])
    valid = (weights >= cfg.MIN_GROUP_WEIGHT) & (n_hard >= cfg.MIN_GROUP_PATENTS)
    if not valid.any():
        raise SystemExit("유효 그룹이 0개다. MIN_GROUP_* 또는 d 를 재검토.")
    kept = resp[:, valid]
    row_sum = kept.sum(axis=1, keepdims=True)
    empty = row_sum[:, 0] < 1e-15
    if empty.any():
        kept[empty] = 1.0 / max(kept.shape[1], 1)
        row_sum = kept.sum(axis=1, keepdims=True)
    kept = kept / np.clip(row_sum, 1e-15, None)
    return kept, valid, n_hard


def hard_labels(resp: np.ndarray) -> np.ndarray:
    return resp.argmax(axis=1)


def group_profiles(
    resp: np.ndarray,
    patents: list[dict],
    index: pd.DataFrame,
    assets: dict,
) -> pd.DataFrame:
    k = resp.shape[1]
    hard = hard_labels(resp)
    weights = resp.mean(axis=0)
    pub_to_i = {pub: i for i, pub in enumerate(index["publication_number"].astype(str))}
    n_clusters = 1 + max(int(c) for c in assets["entity_mapping"].values())

    cpc_by_group: list[Counter] = [Counter() for _ in range(k)]
    cluster_mass = np.zeros((k, n_clusters), dtype=np.float64)
    for rec in patents:
        i = pub_to_i.get(rec["publication_number"])
        if i is None:
            continue
        g = int(hard[i])
        for code in rec["cpc"]:
            key = cpc_key(code)
            if key:
                cpc_by_group[g][key] += 1
        clusters = []
        for head, _rel, tail in rec["triples_v2"]:
            for name in (head, tail):
                cid = entity_cluster(name, assets)
                if cid is not None and 0 <= cid < n_clusters:
                    clusters.append(cid)
        if clusters:
            uniq, counts = np.unique(np.array(clusters, dtype=np.int64), return_counts=True)
            cluster_mass[np.arange(k)[:, None], uniq] += resp[i][:, None] * counts[None, :]

    rows = []
    max_resp = resp.max(axis=1)
    for g in range(k):
        members = hard == g
        top_cpc = [code for code, _ in cpc_by_group[g].most_common(5)]
        order = np.argsort(-cluster_mass[g])
        top_clusters = [int(c) for c in order[:5] if cluster_mass[g, c] > 0]
        rows.append(
            {
                "group": g,
                "weight": float(weights[g]),
                "n_hard": int(members.sum()),
                "mean_max_resp": float(max_resp[members].mean()) if members.any() else 0.0,
                "top_cpc_subclass": "|".join(top_cpc),
                "top_entity_clusters": "|".join(str(c) for c in top_clusters),
            }
        )
    return pd.DataFrame(rows)


def stability_labels(x: np.ndarray, seeds: tuple[int, ...], cache: dict[int, np.ndarray]) -> dict[int, np.ndarray]:
    labels: dict[int, np.ndarray] = {}
    for seed in seeds:
        if seed in cache:
            labels[seed] = cache[seed]
            continue
        print(f"[20] stability fit seed={seed}", flush=True)
        model = fit_bgmm(x, seed)
        resp, _, _ = filter_valid(model.predict_proba(x), model.weights_)
        labels[seed] = hard_labels(resp)
    return labels


def evaluate_gates(k_eff: int, n: int, d: int, median_ari: float, mean_max_resp: float) -> dict:
    k_cap = n / (4.0 * d) if d else float("inf")
    k_ok = k_eff <= k_cap
    ari_ok = median_ari >= cfg.ARI_GATE
    return {
        "k_eff_le_n_over_4d": {"pass": k_ok, "k_eff": k_eff, "cap": k_cap},
        "median_ari_ge_gate": {"pass": ari_ok, "value": median_ari, "gate": cfg.ARI_GATE},
        "mean_max_resp": {
            "value": mean_max_resp,
            "d1_collapse_risk": mean_max_resp >= 0.90,
            "note": "0.9 이상이면 soft-product occupancy 는 쓰지 않는다 (D1).",
        },
        "all_pass": k_ok and ari_ok,
    }


def main() -> int:
    ensure_out()
    x, index = _require_stage1()
    n, d = x.shape
    print(f"[20] x={x.shape} K_MAX={cfg.K_MAX} cov={cfg.COVARIANCE_TYPE}", flush=True)

    print(f"[20] fit official seed={cfg.SEED}", flush=True)
    model = fit_bgmm(x, cfg.SEED)
    resp_full = model.predict_proba(x)
    resp, valid, n_hard_full = filter_valid(resp_full, model.weights_)
    removed = [int(i) for i, keep in enumerate(valid) if not keep]
    k_eff = int(resp.shape[1])
    official_hard = hard_labels(resp)
    mean_max_resp = float(resp.max(axis=1).mean())

    print("[20] load patents for group descriptors", flush=True)
    patents = load_patents()
    assets = load_kg_assets()
    groups = group_profiles(resp, patents, index, assets)

    cache = {cfg.SEED: official_hard}
    labels = stability_labels(x, cfg.STABILITY_SEEDS, cache)
    stab_rows = []
    aris = []
    for a, b in combinations(cfg.STABILITY_SEEDS, 2):
        ari = float(adjusted_rand_score(labels[a], labels[b]))
        aris.append(ari)
        stab_rows.append({"seed_a": int(a), "seed_b": int(b), "ari": ari})
    stab = pd.DataFrame(stab_rows)
    median_ari = float(np.median(aris)) if aris else 0.0

    gates = evaluate_gates(k_eff, n, d, median_ari, mean_max_resp)
    lower_bound = float(getattr(model, "lower_bound_", float("nan")))

    np.save(cfg.OUT / "20_resp.npy", resp.astype(np.float64, copy=False))
    groups.to_csv(cfg.OUT / "20_groups.csv", index=False)
    stab.to_csv(cfg.OUT / "20_seed_stability.csv", index=False)
    write_json(
        cfg.OUT / "20_model.json",
        {
            "k_max": cfg.K_MAX,
            "k_effective": k_eff,
            "removed_components": removed,
            "n_hard_before_filter": n_hard_full.astype(int).tolist(),
            "weights_before_filter": model.weights_.astype(float).tolist(),
            "weights_after_filter": groups["weight"].astype(float).tolist(),
            "mean_max_responsibility": mean_max_resp,
            "lower_bound": lower_bound,
            "converged": bool(getattr(model, "converged_", False)),
            "n_iter": int(getattr(model, "n_iter_", 0)),
            "hyperparameters": {
                "covariance_type": cfg.COVARIANCE_TYPE,
                "weight_concentration_prior_type": cfg.WEIGHT_CONCENTRATION_PRIOR_TYPE,
                "weight_concentration_prior": cfg.WEIGHT_CONCENTRATION_PRIOR,
                "n_init": cfg.N_INIT,
                "max_iter": cfg.MAX_ITER,
                "tol": cfg.TOL,
                "random_state": cfg.SEED,
                "min_group_weight": cfg.MIN_GROUP_WEIGHT,
                "min_group_patents": cfg.MIN_GROUP_PATENTS,
                "stability_seeds": list(cfg.STABILITY_SEEDS),
            },
            "median_ari": median_ari,
            "gates": gates,
        },
    )

    print(
        f"[20] K_eff={k_eff} removed={removed} mean_max_resp={mean_max_resp:.4f} "
        f"median_ARI={median_ari:.4f} lower_bound={lower_bound:.4f}",
        flush=True,
    )
    if gates["mean_max_resp"]["d1_collapse_risk"]:
        print("[20] WARN: mean max responsibility >= 0.9 — D1 soft-product occupancy 붕괴 위험.", flush=True)
    if not gates["all_pass"]:
        print("[20] GATE FAIL — d 또는 K_MAX 를 낮추고 D5 로 복귀.", file=sys.stderr, flush=True)
        return 1
    print("[20] gates passed", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
