"""Per-axis multinomial mixtures, then cell soft map as a product of levels.

K is chosen by held-out log-likelihood on the current corpus (not a human codebook).
Axes stay the four v1 relations; this script does not invent new axes.
"""

from __future__ import annotations

from itertools import product

import numpy as np

from config import (
    EM_MAX_ITER,
    EM_SMOOTH,
    EM_TOL,
    KG_EM_HOLDOUT,
    KG_EM_K_MAX,
    KG_EM_K_MIN,
    KG_EM_N_INIT,
    KG_EM_SEED,
    OUT_KG_EM,
)
from lib import logsumexp, write_csv, write_json

SLOTS = [
    "Addresses_Problem",
    "Comprises_Component",
    "Implemented_By",
    "Achieves_Effect",
]
SLOT_LABEL = {
    "Addresses_Problem": "problem",
    "Comprises_Component": "structure",
    "Implemented_By": "how it runs",
    "Achieves_Effect": "effect",
}


def fit_one(X: np.ndarray, k: int, rng: np.random.Generator) -> dict:
    empty = X.sum(axis=1) == 0
    Xn = X[~empty]
    n_obs, v = Xn.shape
    if n_obs < k:
        k = max(1, n_obs)
    seeds = rng.choice(n_obs, size=k, replace=False)
    theta = Xn[seeds] + EM_SMOOTH
    theta = theta / theta.sum(axis=1, keepdims=True)
    pi = np.ones(k) / k
    ll = None
    r = None
    prev = None
    it = 0
    for it in range(EM_MAX_ITER):
        log_theta = np.log(np.clip(theta, 1e-12, 1.0))
        log_lik = Xn @ log_theta.T
        log_joint = log_lik + np.log(np.clip(pi, 1e-12, 1.0))
        log_norm = logsumexp(log_joint, axis=1, keepdims=True)
        r = np.exp(log_joint - log_norm)
        ll = float(np.sum(log_norm))
        pi = r.mean(axis=0)
        pi = pi / pi.sum()
        theta = r.T @ Xn + EM_SMOOTH
        theta = theta / theta.sum(axis=1, keepdims=True)
        if prev is not None and abs(prev - ll) < EM_TOL:
            break
        prev = ll
    r_full = np.full((X.shape[0], k), 1.0 / k)
    r_full[~empty] = r
    return {"ll": ll, "pi": pi, "theta": theta, "r": r_full, "k": k, "iters": it + 1}


def heldout_ll(X_te: np.ndarray, pi: np.ndarray, theta: np.ndarray) -> float:
    empty = X_te.sum(axis=1) == 0
    if empty.all():
        return 0.0
    log_theta = np.log(np.clip(theta, 1e-12, 1.0))
    log_lik = X_te[~empty] @ log_theta.T
    log_joint = log_lik + np.log(np.clip(pi, 1e-12, 1.0))
    return float(np.sum(logsumexp(log_joint, axis=1)))


def fit_k(X: np.ndarray, k: int, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    best = None
    for _ in range(KG_EM_N_INIT):
        cand = fit_one(X, k, rng)
        if best is None or cand["ll"] > best["ll"]:
            best = cand
    return best


def top_terms(theta: np.ndarray, vocab: list[str], n: int = 8) -> list[list[dict]]:
    out = []
    for ki in range(theta.shape[0]):
        idx = np.argsort(theta[ki])[::-1][:n]
        out.append(
            [
                {
                    "term": vocab[j],
                    "p": round(float(theta[ki, j]), 4),
                    "display": vocab[j].split(":", 1)[-1],
                    "source": vocab[j].split(":", 1)[0],
                }
                for j in idx
                if theta[ki, j] > 0
            ]
        )
    return out


def level_tag(terms: list[dict], ki: int) -> str:
    words = [t["display"].replace(" ", "-") for t in terms[:3]]
    return f"L{ki}:" + "+".join(words) if words else f"L{ki}"


def main() -> None:
    pubs = json_load(OUT_KG_EM / "20_pubs.json")
    n = len(pubs)
    rng = np.random.default_rng(KG_EM_SEED)
    empty_mask = {}
    axis_r = {}
    axis_meta = []
    model_rows = []
    level_rows = []

    for slot in SLOTS:
        X = np.load(OUT_KG_EM / f"20_X_{slot}.npy")
        vocab = json_load(OUT_KG_EM / f"20_vocab_{slot}.json")
        nonempty = np.where(X.sum(axis=1) > 0)[0]
        n_obs = len(nonempty)
        n_hold = max(1, int(round(KG_EM_HOLDOUT * n_obs)))
        hold_idx = rng.choice(nonempty, size=min(n_hold, n_obs), replace=False)
        train_mask = np.ones(n, dtype=bool)
        train_mask[hold_idx] = False
        # empty docs stay in neither train likelihood nor holdout
        X_tr = X.copy()
        X_tr[hold_idx] = 0
        X_te = X[hold_idx]

        k_rows = []
        best_k, best_te = None, -np.inf
        for k in range(KG_EM_K_MIN, KG_EM_K_MAX + 1):
            fitted = fit_k(X_tr, k, KG_EM_SEED + 17 * (SLOTS.index(slot) + 1) + k)
            te = heldout_ll(X_te, fitted["pi"], fitted["theta"])
            k_rows.append(
                {
                    "slot": slot,
                    "k": k,
                    "train_ll": round(fitted["ll"], 2),
                    "heldout_ll": round(te, 2),
                    "heldout_ll_per_doc": round(te / max(len(hold_idx), 1), 4),
                }
            )
            if te > best_te:
                best_te, best_k = te, k

        full = fit_k(X, best_k, KG_EM_SEED + 100 + SLOTS.index(slot))
        tops = top_terms(full["theta"], vocab)
        tags = [level_tag(tops[ki], ki) for ki in range(best_k)]
        r = full["r"]
        empty = X.sum(axis=1) == 0
        empty_mask[slot] = empty
        axis_r[slot] = r
        hard = r.argmax(axis=1)
        maxp = r.max(axis=1)
        occ = r[~empty].sum(axis=0) if (~empty).any() else r.sum(axis=0)

        np.save(OUT_KG_EM / f"21_r_{slot}.npy", r)
        write_json(
            OUT_KG_EM / f"21_model_{slot}.json",
            {
                "slot": slot,
                "k": best_k,
                "pi": [round(float(x), 4) for x in full["pi"]],
                "levels": tags,
                "top_terms": tops,
                "n_empty": int(empty.sum()),
                "heldout_best": round(float(best_te), 2),
                "full_ll": round(full["ll"], 2),
                "iters": full["iters"],
            },
        )
        for row in k_rows:
            row["chosen"] = int(row["k"] == best_k)
            model_rows.append(row)
        for ki, tag in enumerate(tags):
            level_rows.append(
                {
                    "slot": slot,
                    "label": SLOT_LABEL[slot],
                    "level": ki,
                    "tag": tag,
                    "pi": round(float(full["pi"][ki]), 4),
                    "soft_occupancy": round(float(occ[ki]), 1),
                    "hard_n": int(((hard == ki) & ~empty).sum()),
                    "top": ", ".join(t["display"] for t in tops[ki][:6]),
                }
            )
        axis_meta.append(
            {
                "slot": slot,
                "label": SLOT_LABEL[slot],
                "k": best_k,
                "n_empty": int(empty.sum()),
                "mean_max_r": round(float(maxp[~empty].mean()) if (~empty).any() else 0, 3),
                "pct_max_r_ge_0.8": round(
                    100 * float((maxp[~empty] >= 0.8).mean()) if (~empty).any() else 0, 1
                ),
                "levels": tags,
            }
        )
        print(
            f"{SLOT_LABEL[slot]:12s} K={best_k}  empty={int(empty.sum())}  "
            f"mean max r={axis_meta[-1]['mean_max_r']}  "
            + " | ".join(tag.split(":", 1)[-1][:40] for tag in tags)
        )

    write_csv(OUT_KG_EM / "21_k_selection.csv", list(model_rows[0].keys()), model_rows)
    write_csv(OUT_KG_EM / "21_levels.csv", list(level_rows[0].keys()), level_rows)
    write_json(OUT_KG_EM / "21_axis_meta.json", axis_meta)

    # Cell = product of per-axis levels. Soft mass = product of responsibilities.
    ks = [m["k"] for m in axis_meta]
    labels = [json_load(OUT_KG_EM / f"21_model_{s}.json")["levels"] for s in SLOTS]
    cell_index = list(product(*[range(k) for k in ks]))
    n_cells = len(cell_index)
    # occupancy without materializing n x n_cells if large; 6^4=1296 is fine
    r_list = [axis_r[s] for s in SLOTS]
    occ = np.ones(n_cells)
    # compute occupancy as sum_i prod_d r_i[l_d] via successive outer products would
    # still need per-patent. Loop patents; n=1412, n_cells<=1296 is OK-ish.
    # Faster: occupancy of product mixture = not closed form from margins unless indep
    # which we assume by construction. E[prod r] = we still need the product per patent.
    occ = np.zeros(n_cells)
    max_r = np.zeros(n)
    hard = np.zeros(n, dtype=int)
    any_empty = np.zeros(n, dtype=bool)
    for s in SLOTS:
        any_empty |= empty_mask[s]

    # chunked product
    for i in range(n):
        if any_empty[i]:
            max_r[i] = np.nan
            hard[i] = -1
            continue
        vec = np.array([1.0])
        for r in r_list:
            vec = np.outer(vec, r[i]).ravel()
        occ += vec
        hard[i] = int(vec.argmax())
        max_r[i] = float(vec.max())

    mapped = ~any_empty
    cell_rows = []
    for j, combo in enumerate(cell_index):
        name = " | ".join(labels[d][combo[d]] for d in range(4))
        short = " | ".join(SLOT_LABEL[SLOTS[d]][0] + str(combo[d]) for d in range(4))
        cell_rows.append(
            {
                "cell_id": j,
                "short": short,
                "cell": name,
                "soft_occupancy": round(float(occ[j]), 2),
                "hard_n": int(((hard == j) & mapped).sum()),
                "share_pct": round(100 * float(occ[j]) / max(float(occ.sum()), 1e-9), 2),
            }
        )
    cell_rows.sort(key=lambda r: -r["soft_occupancy"])
    write_csv(OUT_KG_EM / "21_cells.csv", list(cell_rows[0].keys()), cell_rows)

    # pairwise expected co-occupancy for structure x effect
    rs = axis_r["Comprises_Component"]
    re = axis_r["Achieves_Effect"]
    em_s = empty_mask["Comprises_Component"]
    em_e = empty_mask["Achieves_Effect"]
    ok = ~(em_s | em_e)
    pair = rs[ok].T @ re[ok]
    np.save(OUT_KG_EM / "21_pair_structure_effect.npy", pair)

    n_mapped = int(mapped.sum())
    write_json(
        OUT_KG_EM / "21_manifest.json",
        {
            "n": n,
            "n_mapped_all_axes": n_mapped,
            "n_cells": n_cells,
            "ks": {SLOT_LABEL[s]: m["k"] for s, m in zip(SLOTS, axis_meta)},
            "mean_max_cell_r": round(float(np.nanmean(max_r[mapped])), 3) if n_mapped else 0,
            "pct_cell_r_ge_0.25": round(
                100 * float(np.mean(max_r[mapped] >= 0.25)) if n_mapped else 0, 1
            ),
            "top_cell": cell_rows[0]["cell"] if cell_rows else "",
            "top_cell_share_pct": cell_rows[0]["share_pct"] if cell_rows else 0,
            "n_cells_with_soft_ge_1": int(sum(1 for r in cell_rows if r["soft_occupancy"] >= 1)),
        },
    )
    print(
        "cells", n_cells, "mapped", n_mapped,
        "top share", cell_rows[0]["share_pct"] if cell_rows else None,
    )


def json_load(path):
    import json

    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
