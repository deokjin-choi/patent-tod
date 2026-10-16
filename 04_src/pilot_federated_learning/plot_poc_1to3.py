"""Save POC 1-3 charts as PNG under out/figures."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

OUT = Path(__file__).resolve().parent / "out" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update(
    {
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.grid": True,
        "grid.alpha": 0.25,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "font.size": 10,
    }
)


def save(fig, name: str) -> None:
    fig.tight_layout()
    fig.savefig(OUT / name, dpi=140)
    plt.close(fig)


# 1. years
years = ["2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025"]
year_n = [6, 117, 524, 846, 1078, 925, 696, 269]
fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(years, year_n, color="#3b6ea8")
ax.set_title("Patents by earliest priority year (n=4,467)")
ax.set_xlabel("Earliest priority year")
ax.set_ylabel("Patents")
save(fig, "01_priority_year.png")

# 2. axis known vs unknown (stacked %)
axes = ["partition", "aggregation", "privacy", "location"]
known = np.array([2.1, 14.3, 11.4, 19.2])
unknown = 100 - known
fig, ax = plt.subplots(figsize=(8, 3.8))
y = np.arange(len(axes))
ax.barh(y, known, color="#3b6ea8", label="level found")
ax.barh(y, unknown, left=known, color="#d0d5dd", label="unknown")
ax.set_yticks(y, axes)
ax.set_xlim(0, 100)
ax.set_xlabel("Share of 4,467 patents (%)")
ax.set_title("How often title+abstract fills each axis")
ax.legend(loc="lower right")
save(fig, "02_axis_known.png")

# 3. n_known
fig, ax = plt.subplots(figsize=(6, 4))
cats = ["0", "1", "2", "3", "4"]
vals = [2687, 1472, 295, 13, 0]
ax.bar(cats, vals, color="#3b6ea8")
ax.set_title("How many axes are filled per patent")
ax.set_xlabel("Axes with a known level")
ax.set_ylabel("Patents")
for i, v in enumerate(vals):
    ax.text(i, v + 40, str(v), ha="center", va="bottom", fontsize=9)
save(fig, "03_n_known.png")

# 4. level mix excluding unknown
level_groups = {
    "partition": (["horizontal", "vertical"], [37, 57]),
    "aggregation": (["central", "hierarchical", "decentralized"], [389, 121, 129]),
    "privacy": (["dp", "crypto", "tee"], [231, 239, 41]),
    "location": (["device", "edge", "cloud"], [242, 361, 254]),
}
fig, axes_g = plt.subplots(2, 2, figsize=(8, 6))
for ax, (name, (labs, nums)) in zip(axes_g.ravel(), level_groups.items()):
    ax.bar(labs, nums, color="#3b6ea8")
    ax.set_title(name)
    ax.set_ylabel("Patents")
    ax.tick_params(axis="x", rotation=20)
fig.suptitle("Level mix among patents that are not unknown")
save(fig, "04_level_mix.png")


def heatmap(ax, rows, cols, mat, title, cmap="Blues"):
    mat = np.array(mat, dtype=float)
    im = ax.imshow(mat, cmap=cmap, vmin=0)
    ax.set_xticks(range(len(cols)), cols, rotation=30, ha="right")
    ax.set_yticks(range(len(rows)), rows)
    ax.set_title(title)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            val = int(mat[i, j])
            ax.text(j, i, str(val), ha="center", va="center", color="black" if mat[i, j] < mat.max() * 0.65 else "white")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)


fig, axes_h = plt.subplots(1, 3, figsize=(13, 3.8))
heatmap(
    axes_h[0],
    ["central", "hierarchical", "decentralized"],
    ["device", "edge", "cloud"],
    [[20, 39, 10], [5, 28, 23], [7, 10, 4]],
    "aggregation x location\n(n both known = 146)",
)
heatmap(
    axes_h[1],
    ["central", "hierarchical", "decentralized"],
    ["dp", "crypto", "tee"],
    [[44, 21, 2], [9, 3, 1], [4, 4, 2]],
    "aggregation x privacy\n(n both known = 90)",
)
heatmap(
    axes_h[2],
    ["dp", "crypto", "tee"],
    ["device", "edge", "cloud"],
    [[6, 13, 12], [5, 15, 18], [1, 1, 3]],
    "privacy x location\n(n both known = 74)",
)
fig.suptitle("Pair occupancy (zeros are rare, not yet constraints)", y=1.02)
save(fig, "05_pair_heatmaps.png")

fig, axes_h = plt.subplots(1, 3, figsize=(13, 3.6))
heatmap(
    axes_h[0],
    ["horizontal", "vertical"],
    ["dp", "crypto", "tee"],
    [[1, 5, 0], [4, 4, 0]],
    "partition x privacy\n(n both known = 14)",
)
heatmap(
    axes_h[1],
    ["horizontal", "vertical"],
    ["central", "hierarchical", "decentralized"],
    [[1, 1, 0], [3, 0, 1]],
    "partition x aggregation\n(n both known = 6)",
)
heatmap(
    axes_h[2],
    ["horizontal", "vertical"],
    ["device", "edge", "cloud"],
    [[0, 1, 2], [1, 0, 0]],
    "partition x location\n(n both known = 4)",
)
fig.suptitle("Partition pairs are almost empty (title+abstract rarely says H/V)", y=1.02)
save(fig, "06_partition_heatmaps.png")

print("wrote", list(p.name for p in sorted(OUT.glob("*.png"))))
