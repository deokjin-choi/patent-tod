"""Figures for KG v1 head review."""

from __future__ import annotations

import csv

import matplotlib.pyplot as plt
import numpy as np

from config import FIG_KG, OUT_KG

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

ORDER = ["Addresses_Problem", "Comprises_Component", "Implemented_By", "Achieves_Effect"]
SHORT = {
    "Addresses_Problem": "problem",
    "Comprises_Component": "structure",
    "Implemented_By": "how it runs",
    "Achieves_Effect": "effect",
}


def read(name):
    with (OUT_KG / name).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def save(fig, name):
    FIG_KG.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(FIG_KG / name, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("wrote", name)


def fig_hapax():
    rows = {r["slot"]: r for r in read("12_head_summary.csv")}
    labels = [SHORT[s] for s in ORDER]
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    ax.bar(x - 0.18, [float(rows[s]["hapax_full_pct"]) for s in ORDER], 0.36, label="full object string", color="#c0392b")
    ax.bar(x + 0.18, [float(rows[s]["hapax_head_pct"]) for s in ORDER], 0.36, label="head (last 1–2 tokens)", color="#3d6b99")
    ax.set_xticks(x, labels)
    ax.set_ylim(0, 110)
    ax.set_ylabel("% of unique items that appear once")
    ax.set_title("Same v1 objects: whole string vs head")
    ax.legend(frameon=False)
    save(fig, "12_hapax_full_vs_head.png")


def fig_tops():
    rows = read("12_head_top.csv")
    fig, axes = plt.subplots(2, 2, figsize=(11.2, 8.0))
    for ax, slot in zip(axes.ravel(), ORDER):
        sub = [r for r in rows if r["slot"] == slot][:12]
        sub = list(reversed(sub))
        ax.barh([r["head"][:40] for r in sub], [int(r["n_patents"]) for r in sub], color="#3d6b99")
        ax.set_title(SHORT[slot])
        ax.tick_params(axis="y", labelsize=8)
        ax.set_xlabel("patents")
    fig.suptitle("Repeated heads of v1 objects (templates dropped)", y=1.01)
    save(fig, "12_head_top.png")


def fig_unique_counts():
    rows = {r["slot"]: r for r in read("12_head_summary.csv")}
    labels = [SHORT[s] for s in ORDER]
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    ax.bar(x - 0.18, [int(rows[s]["unique_full_strings"]) for s in ORDER], 0.36, label="unique full strings", color="#8e5a2b")
    ax.bar(x + 0.18, [int(rows[s]["unique_heads"]) for s in ORDER], 0.36, label="unique heads", color="#3d6b99")
    ax.set_xticks(x, labels)
    ax.set_ylabel("distinct items")
    ax.set_title("How far the vocabulary shrinks after taking heads")
    ax.legend(frameon=False)
    save(fig, "12_unique_full_vs_head.png")


def main():
    fig_hapax()
    fig_unique_counts()
    fig_tops()


if __name__ == "__main__":
    main()
