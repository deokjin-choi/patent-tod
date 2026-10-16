"""Quality numbers from EM occupancy, MCMC samples, and missing-species on signatures."""

from __future__ import annotations

from collections import Counter

import numpy as np

from config import OUT
from lib import all_cells, axis_order, cell_name, entropy, ensure_out, hamming, load_dictionary, write_csv


def chao1(freq_of_freq: dict[int, int], s_obs: int) -> float:
    f1 = freq_of_freq.get(1, 0)
    f2 = freq_of_freq.get(2, 0)
    if f2 > 0:
        return s_obs + (f1 * f1) / (2.0 * f2)
    return s_obs + f1 * (f1 - 1) / 2.0


def good_turing_unseen(freq_of_freq: dict[int, int], n_tokens: int) -> float:
    """P(next draw is a new species) ~ f1 / N."""
    if n_tokens <= 0:
        return 0.0
    return freq_of_freq.get(1, 0) / n_tokens


def occupancy_metrics(weights: np.ndarray, cells: list[tuple], label: str) -> dict:
    k = len(cells)
    w = np.asarray(weights, dtype=float)
    s = w.sum()
    p = w / s if s > 0 else np.ones(k) / k
    occupied = p > (1.0 / (k * 20))  # tiny mass does not count as coverage
    cov = float(occupied.mean())
    bal = entropy(p) / np.log(k) if k > 1 else 0.0
    # diversity: expected Hamming distance between two independent draws
    div = 0.0
    for i, a in enumerate(cells):
        for j, b in enumerate(cells):
            div += p[i] * p[j] * hamming(a, b)
    return {
        "source": label,
        "n_cells": k,
        "coverage": round(cov, 4),
        "n_occupied": int(occupied.sum()),
        "balance_norm_entropy": round(float(bal), 4),
        "diversity_mean_hamming": round(float(div), 4),
        "mass_sum": round(float(s), 3),
    }


def ascii_bar(x: float, width: int = 20) -> str:
    n = int(round(max(0.0, min(1.0, x)) * width))
    return "#" * n + "." * (width - n)


def main() -> None:
    ensure_out()
    d = load_dictionary()
    axes = axis_order(d)
    cells = all_cells(d)
    names = [cell_name(axes, c) for c in cells]

    r = np.load(OUT / "02_em_r.npy")
    X = np.load(OUT / "01_counts.npy")
    nonempty = X.sum(axis=1) > 0
    em_occ_all = r.sum(axis=0)
    em_occ_ne = r[nonempty].sum(axis=0)

    import csv

    sample_w = np.zeros(len(cells))
    with (OUT / "03_cell_sample_freq.csv").open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row["cell"] in names:
                sample_w[names.index(row["cell"])] = float(row["mcmc_count"])

    hard = r.argmax(axis=1)
    hard_w = np.bincount(hard[nonempty], minlength=len(cells)).astype(float)

    rows = [
        occupancy_metrics(hard_w, cells, "em_hard_nonempty"),
        occupancy_metrics(em_occ_ne, cells, "em_expected_nonempty"),
        occupancy_metrics(em_occ_all, cells, "em_expected_all_incl_empty"),
        occupancy_metrics(sample_w, cells, "mcmc_feasible_samples"),
    ]
    write_csv(
        OUT / "04_quality.csv",
        ["source", "n_cells", "coverage", "n_occupied", "balance_norm_entropy", "diversity_mean_hamming", "mass_sum"],
        rows,
    )

    # Missing-species on keyword signatures (open space), not on the 8 closed cells.
    sig_count = Counter()
    with (OUT / "01_signatures.csv").open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if int(row["n_types"]) == 0:
                continue
            sig_count[row["signature"]] += 1
    ff = Counter(sig_count.values())
    s_obs = len(sig_count)
    n_docs = sum(sig_count.values())
    miss = {
        "species": "keyword_presence_signature",
        "s_obs": s_obs,
        "n_docs_with_keywords": n_docs,
        "f1_singletons": ff.get(1, 0),
        "f2_doubletons": ff.get(2, 0),
        "chao1": round(chao1(ff, s_obs), 2),
        "good_turing_p_new": round(good_turing_unseen(ff, n_docs), 4),
        "note": "Closed 8-cell space is the wrong place for missing-species. Signatures are open.",
    }
    write_csv(OUT / "04_missing_species.csv", list(miss.keys()), [miss])

    # ASCII report
    lines = []
    lines.append("EM / MCMC skeleton — what the numbers are saying")
    lines.append("=" * 60)
    lines.append("")
    lines.append("Cell occupancy (EM expected vs MCMC feasible samples)")
    lines.append("")
    em_p = em_occ_ne / em_occ_ne.sum() if em_occ_ne.sum() else em_occ_ne
    mc_p = sample_w / sample_w.sum() if sample_w.sum() else sample_w
    lines.append(f"{'cell':42s}  {'EM':22s}        {'MCMC':22s}")
    for i, name in enumerate(names):
        lines.append(
            f"{name:42s}  {ascii_bar(float(em_p[i]))} {em_p[i]:.3f}  {ascii_bar(float(mc_p[i]))} {mc_p[i]:.3f}"
        )
    lines.append("")
    lines.append("Quality")
    for row in rows:
        lines.append(
            f"  {row['source']:24s} coverage={row['coverage']} "
            f"({row['n_occupied']}/{row['n_cells']})  "
            f"balance={row['balance_norm_entropy']}  "
            f"diversity={row['diversity_mean_hamming']}"
        )
    lines.append("")
    lines.append("Missing-species (keyword signatures, not cells)")
    lines.append(f"  observed signatures {miss['s_obs']}")
    lines.append(f"  singletons f1={miss['f1_singletons']}  doubletons f2={miss['f2_doubletons']}")
    lines.append(f"  Chao1 estimate of total signature types {miss['chao1']}")
    lines.append(f"  Good-Turing P(next patent has a new signature) {miss['good_turing_p_new']}")
    lines.append("")
    lines.append("How to read this")
    lines.append("  coverage  : share of the 8 designed cells that received mass")
    lines.append("  balance   : 1 = even occupancy, 0 = all mass in one cell")
    lines.append("  diversity : expected Hamming distance of two random draws (0 to 3)")
    lines.append("  Chao1     : how many more keyword-combination types may exist")
    lines.append("  EM empty docs stay uniform — they inflate coverage; check n_tokens=0")
    text = "\n".join(lines) + "\n"
    (OUT / "04_report.txt").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
