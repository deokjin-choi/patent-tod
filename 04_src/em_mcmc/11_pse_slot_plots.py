"""Charts for the PSE / KG v1 slot inventory."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from config import FIG_PSE, OUT_PSE

plt.rcParams.update(
    {
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.grid": True,
        "grid.alpha": 0.28,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "font.size": 10,
    }
)

SLOT_ORDER = [
    "Addresses_Problem",
    "Comprises_Component",
    "Implemented_By",
    "Achieves_Effect",
]
SHORT = {
    "Addresses_Problem": "problem",
    "Comprises_Component": "structure",
    "Implemented_By": "how it runs",
    "Achieves_Effect": "effect",
}


def read(name: str) -> list[dict]:
    with (OUT_PSE / name).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def save(fig, name: str) -> None:
    FIG_PSE.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(FIG_PSE / name, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("wrote", name)


def fig_coverage():
    rows = {r["slot"]: r for r in read("10_slot_summary.csv")}
    labels = [SHORT[s] for s in SLOT_ORDER]
    pct = [float(rows[s]["pct_patents"]) for s in SLOT_ORDER]
    fig, ax = plt.subplots(figsize=(6.6, 3.5))
    ax.bar(labels, pct, color="#3d6b99")
    ax.set_ylim(0, 100)
    ax.set_ylabel("% of 1,412 patents with ≥1 object in this slot")
    ax.set_title("Does every patent fill every ballot box?")
    for i, v in enumerate(pct):
        ax.text(i, v + 1.5, f"{v:.0f}%", ha="center")
    save(fig, "10_slot_coverage.png")


def fig_repeat():
    rows = {r["slot"]: r for r in read("10_slot_summary.csv") if r["slot"] in SHORT}
    labels = [SHORT[s] for s in SLOT_ORDER]
    hapax = [float(rows[s]["pct_hapax"]) for s in SLOT_ORDER]
    longp = [float(rows[s]["pct_long_mentions"]) for s in SLOT_ORDER]
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    ax.bar(x - 0.18, hapax, 0.36, label="% unique strings that appear once", color="#c0392b")
    ax.bar(x + 0.18, longp, 0.36, label="% mentions that are ≥8 words", color="#8e5a2b")
    ax.set_xticks(x, labels)
    ax.set_ylim(0, 110)
    ax.set_ylabel("percent")
    ax.set_title("If these are high, the slot is essays, not multiple-choice answers")
    ax.legend(frameon=False, fontsize=8)
    save(fig, "10_slot_repeat.png")


def fig_tops():
    rows = [r for r in read("10_slot_top.csv") if r["kind"] == "string" and r["slot"] in SHORT]
    fig, axes = plt.subplots(2, 2, figsize=(11.2, 8.2))
    for ax, slot in zip(axes.ravel(), SLOT_ORDER):
        sub = [r for r in rows if r["slot"] == slot][:12]
        sub = list(reversed(sub))
        terms = [r["term"][:42] for r in sub]
        vals = [int(r["n_patents"]) for r in sub]
        ax.barh(terms, vals, color="#3d6b99")
        ax.set_title(SHORT[slot])
        ax.tick_params(axis="y", labelsize=8)
        ax.set_xlabel("patents")
    fig.suptitle("Most repeated answers in each box (normalized string)", y=1.01)
    save(fig, "10_slot_top_terms.png")


def fig_triples():
    rows = read("10_patent_slots.csv")
    n = np.array([int(r["n_triples"]) for r in rows])
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    ax.hist(n, bins=range(0, min(int(n.max()) + 2, 40)), color="#3d6b99", edgecolor="white")
    ax.set_xlabel("v1 triples per patent")
    ax.set_ylabel("patents")
    ax.set_title(f"How much graph each patent got  (median {int(np.median(n))})")
    save(fig, "10_triples_per_patent.png")


def main() -> None:
    fig_coverage()
    fig_repeat()
    fig_tops()
    fig_triples()


if __name__ == "__main__":
    main()
