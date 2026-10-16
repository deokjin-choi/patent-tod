"""Figures for per-axis mixture + product-cell soft map."""

from __future__ import annotations

import csv
import json

import matplotlib.pyplot as plt
import numpy as np

from config import FIG_KG_EM, OUT_KG_EM

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

SLOTS = [
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


def load_json(name):
    return json.loads((OUT_KG_EM / name).read_text(encoding="utf-8"))


def read_csv(name):
    with (OUT_KG_EM / name).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def save(fig, name):
    FIG_KG_EM.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(FIG_KG_EM / name, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("wrote", name)


def fig_features():
    rows = read_csv("20_feature_summary.csv")
    labels = [r["label"] for r in rows]
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(7.4, 3.6))
    ax.bar(x - 0.2, [int(r["n_head_terms"]) for r in rows], 0.2, label="graph object head", color="#3d6b99")
    ax.bar(x, [int(r["n_subject_terms"]) for r in rows], 0.2, label="graph subject head", color="#6b8f3d")
    ax.bar(x + 0.2, [int(r["n_essay_terms"]) for r in rows], 0.2, label="essay unigram", color="#c0392b")
    ax.set_xticks(x, labels)
    ax.set_ylabel("terms kept in vocab")
    ax.set_title("What the mixture actually sees on each axis")
    ax.legend(frameon=False, fontsize=8)
    save(fig, "20_feature_mix.png")


def fig_k_select():
    rows = read_csv("21_k_selection.csv")
    fig, axes = plt.subplots(2, 2, figsize=(8.4, 6.4))
    for ax, slot in zip(axes.ravel(), SLOTS):
        sub = [r for r in rows if r["slot"] == slot]
        ks = [int(r["k"]) for r in sub]
        y = [float(r["heldout_ll_per_doc"]) for r in sub]
        chosen = next(int(r["k"]) for r in sub if r["chosen"] == "1")
        ax.plot(ks, y, marker="o", color="#3d6b99")
        ax.axvline(chosen, color="#c0392b", ls="--", lw=1)
        ax.set_title(f"{SHORT[slot]}  (K={chosen})")
        ax.set_xlabel("K")
        ax.set_ylabel("held-out loglik / doc")
    fig.suptitle("Level count chosen from the corpus, not a codebook", y=1.01)
    save(fig, "21_k_selection.png")


def fig_levels():
    rows = read_csv("21_levels.csv")
    fig, axes = plt.subplots(2, 2, figsize=(11.2, 8.2))
    for ax, slot in zip(axes.ravel(), SLOTS):
        sub = [r for r in rows if r["slot"] == slot]
        labels = [r["tag"].replace("L" + r["level"] + ":", "")[:42] for r in sub]
        ax.barh(labels[::-1], [float(r["soft_occupancy"]) for r in sub][::-1], color="#3d6b99")
        ax.set_title(SHORT[slot])
        ax.set_xlabel("expected patents (soft)")
        ax.tick_params(axis="y", labelsize=8)
    fig.suptitle("Levels = mixture components. Labels are top words, not human names.", y=1.01)
    save(fig, "21_level_occupancy.png")


def fig_level_words():
    fig, axes = plt.subplots(2, 2, figsize=(11.4, 8.4))
    for ax, slot in zip(axes.ravel(), SLOTS):
        model = load_json(f"21_model_{slot}.json")
        ax.axis("off")
        ax.set_title(SHORT[slot] + f"  K={model['k']}", loc="left")
        lines = []
        for ki, terms in enumerate(model["top_terms"]):
            words = ", ".join(
                (("·" if t["source"] != "p" else "") + t["display"]) for t in terms[:6]
            )
            lines.append(f"L{ki}  {words}")
        ax.text(0.0, 0.92, "\n\n".join(lines), va="top", ha="left", fontsize=9, family="monospace", transform=ax.transAxes)
    fig.suptitle("Leading dot = graph head/subject; unmarked = essay token", y=1.01)
    save(fig, "21_level_words.png")


def fig_confidence():
    fig, axes = plt.subplots(2, 2, figsize=(8.4, 6.4))
    for ax, slot in zip(axes.ravel(), SLOTS):
        r = np.load(OUT_KG_EM / f"21_r_{slot}.npy")
        X = np.load(OUT_KG_EM / f"20_X_{slot}.npy")
        ok = X.sum(axis=1) > 0
        mx = r[ok].max(axis=1)
        ax.hist(mx, bins=np.linspace(0, 1, 21), color="#3d6b99", edgecolor="white")
        ax.set_title(f"{SHORT[slot]}  mean max={mx.mean():.2f}")
        ax.set_xlabel("P(best level | patent)")
        ax.set_ylabel("patents")
    fig.suptitle("Soft membership on each axis (empty docs excluded)", y=1.01)
    save(fig, "21_axis_confidence.png")


def fig_pair():
    pair = np.load(OUT_KG_EM / "21_pair_structure_effect.npy")
    s_model = load_json("21_model_Comprises_Component.json")
    e_model = load_json("21_model_Achieves_Effect.json")
    fig, ax = plt.subplots(figsize=(8.6, 5.8))
    im = ax.imshow(pair, cmap="Blues")
    ax.set_yticks(range(len(s_model["levels"])), [t.split(":", 1)[-1][:28] for t in s_model["levels"]], fontsize=8)
    ax.set_xticks(
        range(len(e_model["levels"])),
        [t.split(":", 1)[-1][:22] for t in e_model["levels"]],
        fontsize=8,
        rotation=35,
        ha="right",
    )
    ax.set_ylabel("structure level")
    ax.set_xlabel("effect level")
    ax.set_title("Expected co-occupancy  (sum of P(struct)×P(effect))")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    save(fig, "21_pair_structure_effect.png")


def fig_cells():
    rows = read_csv("21_cells.csv")[:18]
    labels = [r["short"] + "  " + r["cell"][:52] for r in rows]
    fig, ax = plt.subplots(figsize=(10.4, 7.2))
    ax.barh(labels[::-1], [float(r["soft_occupancy"]) for r in rows][::-1], color="#3d6b99")
    ax.set_xlabel("expected patents")
    ax.set_title("Top cells of the product space (soft occupancy)")
    ax.tick_params(axis="y", labelsize=7)
    save(fig, "21_top_cells.png")


def fig_empty():
    rows = read_csv("20_feature_summary.csv")
    labels = [r["label"] for r in rows]
    fig, ax = plt.subplots(figsize=(6.6, 3.4))
    ax.bar(labels, [int(r["n_empty"]) for r in rows], color="#8e5a2b")
    ax.set_ylabel("patents with no kept tokens")
    ax.set_title("Empty on an axis → uniform over that axis's levels")
    save(fig, "20_empty_axis.png")


def main():
    fig_features()
    fig_empty()
    fig_k_select()
    fig_levels()
    fig_level_words()
    fig_confidence()
    fig_pair()
    fig_cells()


if __name__ == "__main__":
    main()
