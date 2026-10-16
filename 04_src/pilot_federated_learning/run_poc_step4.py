"""Step 4 POC: score aggregation/privacy/location pairs. Flag suspects, do not forbid."""

from __future__ import annotations

import csv
from collections import Counter
from itertools import combinations, product
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
MAP = ROOT / "out" / "02_mapping.csv"
OUT = ROOT / "out"
FIG = OUT / "figures"

UNKNOWN = "unknown"
AXES = {
    "aggregation": ["central", "hierarchical", "decentralized"],
    "privacy": ["dp", "crypto", "tee"],
    "location": ["device", "edge", "cloud"],
}
PAIRS = [
    ("aggregation", "location"),
    ("aggregation", "privacy"),
    ("privacy", "location"),
]
MIN_BOTH = 70
RARE_COUNT = 2
LOW_LIFT = 0.5


def flag_of(count: int, lift: float) -> str:
    if count == 0:
        return "unobserved"
    if count <= RARE_COUNT:
        return "rare_count"
    if lift < LOW_LIFT:
        return "low_lift"
    return "ok"


def load_mapped() -> list[dict[str, str]]:
    with MAP.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def score_pair(rows: list[dict], a: str, b: str) -> tuple[list[dict], dict]:
    both = [r for r in rows if r[a] != UNKNOWN and r[b] != UNKNOWN]
    n = len(both)
    joint = Counter((r[a], r[b]) for r in both)
    marg_a = Counter(r[a] for r in both)
    marg_b = Counter(r[b] for r in both)
    scored = []
    for la, lb in product(AXES[a], AXES[b]):
        c = joint[(la, lb)]
        ca, cb = marg_a[la], marg_b[lb]
        lift = (n * c / (ca * cb)) if ca and cb and n else 0.0
        flag = flag_of(c, lift)
        titles = [r["title"] for r in both if r[a] == la and r[b] == lb][:8]
        scored.append(
            {
                "axis_a": a,
                "level_a": la,
                "axis_b": b,
                "level_b": lb,
                "count": c,
                "count_a": ca,
                "count_b": cb,
                "n_both_known": n,
                "lift": round(lift, 3),
                "flag": flag,
                "example_titles": " || ".join(titles),
            }
        )
    meta = {"axis_a": a, "axis_b": b, "n_both_known": n, "used": n >= MIN_BOTH}
    return scored, meta


def heatmap_count(ax, rows, cols, mat, flags, title):
    mat = np.array(mat, dtype=float)
    im = ax.imshow(mat, cmap="Blues", vmin=0)
    ax.set_xticks(range(len(cols)), cols, rotation=25, ha="right")
    ax.set_yticks(range(len(rows)), rows)
    ax.set_title(title)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            v = int(mat[i, j])
            flag = flags[i][j]
            txt = f"{v}*" if flag != "ok" else str(v)
            color = "white" if mat[i, j] > mat.max() * 0.65 else "black"
            ax.text(j, i, txt, ha="center", va="center", color=color, fontsize=9)
            if flag != "ok":
                ax.add_patch(
                    plt.Rectangle(
                        (j - 0.5, i - 0.5),
                        1,
                        1,
                        fill=False,
                        edgecolor="#c0392b",
                        linewidth=2,
                    )
                )
    fig = ax.figure
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)


def heatmap_lift(ax, rows, cols, mat, flags, title):
    mat = np.array(mat, dtype=float)
    im = ax.imshow(mat, cmap="RdYlGn", vmin=0.3, vmax=1.7)
    ax.set_xticks(range(len(cols)), cols, rotation=25, ha="right")
    ax.set_yticks(range(len(rows)), rows)
    ax.set_title(title)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            color = "black"
            ax.text(j, i, f"{mat[i, j]:.2f}", ha="center", va="center", color=color, fontsize=8)
            if flags[i][j] != "ok":
                ax.add_patch(
                    plt.Rectangle(
                        (j - 0.5, i - 0.5),
                        1,
                        1,
                        fill=False,
                        edgecolor="#c0392b",
                        linewidth=2,
                    )
                )
    ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04)


def grid_of(scored: list[dict], a: str, b: str):
    rows, cols = AXES[a], AXES[b]
    lookup = {(r["level_a"], r["level_b"]): r for r in scored}
    counts, lifts, flags = [], [], []
    for la in rows:
        cr, lr, fr = [], [], []
        for lb in cols:
            r = lookup[(la, lb)]
            cr.append(r["count"])
            lr.append(r["lift"])
            fr.append(r["flag"])
        counts.append(cr)
        lifts.append(lr)
        flags.append(fr)
    return rows, cols, counts, lifts, flags


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    rows = load_mapped()
    all_scored = []
    metas = []
    for a, b in PAIRS:
        scored, meta = score_pair(rows, a, b)
        all_scored.extend(scored)
        metas.append(meta)

    write_csv(
        OUT / "04_pairs_scored.csv",
        [
            "axis_a",
            "level_a",
            "axis_b",
            "level_b",
            "count",
            "count_a",
            "count_b",
            "n_both_known",
            "lift",
            "flag",
            "example_titles",
        ],
        all_scored,
    )
    suspects = [r for r in all_scored if r["flag"] != "ok"]
    write_csv(
        OUT / "04_suspects.csv",
        [
            "axis_a",
            "level_a",
            "axis_b",
            "level_b",
            "count",
            "count_a",
            "count_b",
            "lift",
            "flag",
            "n_both_known",
            "example_titles",
        ],
        suspects,
    )

    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "font.size": 9,
        }
    )

    fig, axes = plt.subplots(2, 3, figsize=(13.5, 7.2))
    for col, (a, b) in enumerate(PAIRS):
        subset = [r for r in all_scored if r["axis_a"] == a and r["axis_b"] == b]
        rlab, clab, counts, lifts, flags = grid_of(subset, a, b)
        n = subset[0]["n_both_known"]
        heatmap_count(
            axes[0, col],
            rlab,
            clab,
            counts,
            flags,
            f"{a} x {b}\ncount (n={n})",
        )
        heatmap_lift(
            axes[1, col],
            rlab,
            clab,
            lifts,
            flags,
            f"{a} x {b}\nlift (1 = as expected)",
        )
    fig.suptitle(
        "Step 4: red box = suspect (rare or low lift), not a ban. * = flagged count.",
        y=1.01,
    )
    fig.tight_layout()
    fig.savefig(FIG / "07_step4_suspects.png", dpi=140, bbox_inches="tight")
    plt.close(fig)

    print("n mapped", len(rows))
    print("metas", metas)
    print("suspects", len(suspects))
    for r in suspects:
        print(f"  {r['flag']:12s} {r['level_a']}+{r['level_b']}  n={r['count']} lift={r['lift']}")


if __name__ == "__main__":
    main()
