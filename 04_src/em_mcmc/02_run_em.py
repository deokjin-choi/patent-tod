"""EM: map each patent to scenario cells with a multinomial mixture.

Latent variable z_i = cell (combination of the three axis levels).
Observed x_i = keyword count vector.
Axes/levels are fixed by the dictionary; EM does not invent new axes.
"""

from __future__ import annotations

import numpy as np

from config import EM_MAX_ITER, EM_SMOOTH, EM_TOL, OUT
from lib import (
    all_cells,
    axis_order,
    cell_name,
    ensure_out,
    load_dictionary,
    logsumexp,
    vocab_entries,
    write_csv,
)


def main() -> None:
    ensure_out()
    d = load_dictionary()
    axes = axis_order(d)
    cells = all_cells(d)
    vocab = vocab_entries(d)
    X = np.load(OUT / "01_counts.npy")
    n, v = X.shape
    k = len(cells)
    names = [cell_name(axes, c) for c in cells]

    # Seed: cell (l1,l2,l3) prefers phrases tagged with those levels.
    axis_index = {a: i for i, a in enumerate(axes)}
    prior = np.ones((k, v)) * EM_SMOOTH
    for ki, cell in enumerate(cells):
        for j, item in enumerate(vocab):
            ai = axis_index[item["axis"]]
            if cell[ai] == item["level"]:
                prior[ki, j] += 4.0
    theta = prior / prior.sum(axis=1, keepdims=True)
    pi = np.ones(k) / k

    ll_hist = []
    r = np.full((n, k), 1.0 / k)
    for it in range(EM_MAX_ITER):
        log_theta = np.log(np.clip(theta, 1e-12, 1.0))
        # log p(x|z=k) for multinomial counts: sum_w x_w log theta_kw
        log_lik = X @ log_theta.T  # n x k
        log_joint = log_lik + np.log(np.clip(pi, 1e-12, 1.0))
        log_norm = logsumexp(log_joint, axis=1, keepdims=True)
        r = np.exp(log_joint - log_norm)
        # empty documents stay uniform
        empty = X.sum(axis=1) == 0
        r[empty] = 1.0 / k
        ll = float(np.sum(log_norm[~empty]))
        ll_hist.append({"iter": it, "loglik": ll, "n_empty": int(empty.sum())})

        pi = r.mean(axis=0)
        pi = pi / pi.sum()
        weighted = r.T @ X  # k x v
        theta = weighted + EM_SMOOTH
        theta = theta / theta.sum(axis=1, keepdims=True)

        if it > 0 and abs(ll_hist[-1]["loglik"] - ll_hist[-2]["loglik"]) < EM_TOL:
            break

    empty = X.sum(axis=1) == 0
    hard = r.argmax(axis=1)
    resp_rows = []
    for i in range(n):
        if empty[i]:
            hard_cell, hard_prob = "unmapped", round(1.0 / k, 4)
        else:
            hard_cell, hard_prob = names[int(hard[i])], round(float(r[i, hard[i]]), 4)
        rec = {
            "row": i,
            "hard_cell": hard_cell,
            "hard_prob": hard_prob,
            "n_tokens": int(X[i].sum()),
            "entropy": round(float(-np.sum(r[i] * np.log(np.clip(r[i], 1e-12, 1)))), 4),
        }
        for ki, name in enumerate(names):
            rec[name] = round(float(r[i, ki]), 4)
        resp_rows.append(rec)

    # attach display keys
    from config import PATENTS
    from lib import read_csv

    patents = read_csv(PATENTS)
    for i, rec in enumerate(resp_rows):
        rec["display_key"] = patents[i]["display_key"]

    occ = r.sum(axis=0)
    occ_ne = r[~empty].sum(axis=0) if (~empty).any() else np.zeros(k)
    occ_rows = []
    for ki, cell in enumerate(cells):
        occ_rows.append(
            {
                "cell": names[ki],
                **{axes[j]: cell[j] for j in range(len(axes))},
                "expected_occupancy": round(float(occ[ki]), 3),
                "expected_occupancy_nonempty": round(float(occ_ne[ki]), 3),
                "hard_count": int(((hard == ki) & (~empty)).sum()),
                "pi": round(float(pi[ki]), 4),
            }
        )

    theta_rows = []
    for ki, name in enumerate(names):
        for j, item in enumerate(vocab):
            theta_rows.append(
                {
                    "cell": name,
                    "kw_id": f"kw_{j:03d}",
                    "phrase": item["phrase"],
                    "origin": item["origin"],
                    "prob": round(float(theta[ki, j]), 6),
                }
            )

    fields_resp = ["display_key", "row", "n_tokens", "hard_cell", "hard_prob", "entropy", *names]
    write_csv(OUT / "02_em_responsibilities.csv", fields_resp, resp_rows)
    write_csv(
        OUT / "02_em_occupancy.csv",
        ["cell", *axes, "expected_occupancy", "expected_occupancy_nonempty", "hard_count", "pi"],
        occ_rows,
    )
    write_csv(OUT / "02_em_theta.csv", ["cell", "kw_id", "phrase", "origin", "prob"], theta_rows)
    write_csv(OUT / "02_em_loglik.csv", ["iter", "loglik", "n_empty"], ll_hist)
    np.save(OUT / "02_em_r.npy", r)
    np.save(OUT / "02_em_pi.npy", pi)
    np.save(OUT / "02_em_theta.npy", theta)

    print(f"EM iters={len(ll_hist)} final_ll={ll_hist[-1]['loglik']:.1f} empty={ll_hist[-1]['n_empty']}")
    print("expected occupancy")
    for row in occ_rows:
        print(f"  {row['cell']:40s}  E={row['expected_occupancy_nonempty']:7.2f}  hard={row['hard_count']}")


if __name__ == "__main__":
    main()
