"""Glance figures for poc_results_3to4.md"""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

FIG = Path(__file__).resolve().parent / "out" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

plt.rcParams.update(
    {
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "font.size": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": False,
        "axes.spines.bottom": False,
    }
)

# colors
C_ERR = "#c5c9d1"
C_USE = "#3b6ea8"
C_GAP = "#c47b2b"
C_WEAK = "#8aa0b8"
TXT = "#1b1f24"
MUTED = "#5c6570"


def card(ax, x, y, w, h, face, title, lines, edge=None):
    box = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.02,rounding_size=0.04",
        facecolor=face,
        edgecolor=edge or face,
        linewidth=1.2,
        transform=ax.transAxes,
        clip_on=False,
    )
    ax.add_patch(box)
    ax.text(
        x + 0.03,
        y + h - 0.07,
        title,
        transform=ax.transAxes,
        fontsize=11,
        fontweight="bold",
        color="white" if face in (C_USE, C_GAP) else TXT,
        va="top",
    )
    ax.text(
        x + 0.03,
        y + h - 0.22,
        "\n".join(lines),
        transform=ax.transAxes,
        fontsize=9,
        color="white" if face in (C_USE, C_GAP) else MUTED,
        va="top",
        linespacing=1.35,
    )


def fig_verdict():
    fig, ax = plt.subplots(figsize=(11.2, 5.6))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.suptitle("Suspect cells after reading title+abstract  (not a ban)", fontsize=13, fontweight="bold", y=0.98)
    ax.text(0.02, 0.90, "6 red cells  →  3 are mapping noise, 2 are real uses, 1 is almost-empty feasible", transform=ax.transAxes, color=MUTED)

    # legend
    ax.text(0.02, 0.82, "■ actual use", transform=ax.transAxes, color=C_USE, fontweight="bold", fontsize=9)
    ax.text(0.18, 0.82, "■ coding error / weak", transform=ax.transAxes, color=MUTED, fontweight="bold", fontsize=9)
    ax.text(0.42, 0.82, "■ almost-empty feasible (gap candidate)", transform=ax.transAxes, color=C_GAP, fontweight="bold", fontsize=9)

    cards = [
        (0.02, 0.42, C_GAP, "hierarchical + device", ["n=5 docs → 1 invention", "3 coding errors", "1 RAN family: UE or BS", "not contradiction"]),
        (0.35, 0.42, C_USE, "central + tee", ["n=2, both real", "TEE at client", "+ central aggregator", "rare because TEE is rare"]),
        (0.68, 0.42, C_USE, "decentralized + tee", ["n=2 docs = 1 invention", "aggregators inside TEEs", "lift 3.6  (typical design)", "not a gap"]),
        (0.02, 0.04, C_ERR, "hierarchical + tee", ["n=1, same as tee+edge", "hierarchical protection", "not aggregation topology", "mapping artifact"]),
        (0.35, 0.04, C_ERR, "tee + device", ["n=1", "TEE is on coordinator", "device = participating UEs", "not TEE-on-device"]),
        (0.68, 0.04, C_WEAK, "tee + edge", ["n=1, same patent as", "hierarchical+tee", "edge cluster is real", "TEE mention is thin"]),
    ]
    for x, y, face, title, lines in cards:
        card(ax, x, y, 0.30, 0.34, face, title, lines)

    fig.savefig(FIG / "08_suspect_verdict.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_h_device():
    fig, ax = plt.subplots(figsize=(11.2, 4.4))
    ax.axis("off")
    fig.suptitle("hierarchical + device  —  5 documents", fontsize=13, fontweight="bold", y=0.98)

    rows = [
        (C_ERR, "CN 116567824 A", "2023", "coding error", "hierarchical edge network;\nUE word → device"),
        (C_ERR, "CN 118018178 A", "2023", "coding error", "UE → satellite/edge → central;\ndevice matched first"),
        (C_ERR, "CN 120196640 A", "2025", "coding error", "hierarchical knowledge\ndistillation, not topology"),
        (C_GAP, "WO 2023/093238 A1", "2021", "1 family", "hierarchical FL in RAN;\ndeploy at UE or BS"),
        (C_GAP, "WO 2023/093235 A1", "2021", "same family", "same priority date;\nsame architecture"),
    ]
    for i, (face, key, year, tag, note) in enumerate(rows):
        y = 0.78 - i * 0.16
        box = FancyBboxPatch((0.02, y), 0.96, 0.14, boxstyle="round,pad=0.01,rounding_size=0.03", facecolor=face, edgecolor=face, transform=ax.transAxes)
        ax.add_patch(box)
        tc = "white" if face == C_GAP else TXT
        ax.text(0.04, y + 0.09, key, transform=ax.transAxes, fontsize=10, fontweight="bold", color=tc, va="center")
        ax.text(0.36, y + 0.09, year, transform=ax.transAxes, fontsize=10, color=tc, va="center")
        ax.text(0.46, y + 0.09, tag, transform=ax.transAxes, fontsize=10, fontweight="bold", color=tc, va="center")
        ax.text(0.62, y + 0.07, note, transform=ax.transAxes, fontsize=8.5, color=tc, va="center", linespacing=1.25)

    fig.savefig(FIG / "09_hdevice_patents.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_tee_cells():
    fig, ax = plt.subplots(figsize=(11.2, 5.0))
    ax.axis("off")
    fig.suptitle("TEE suspect cells  —  documents after reading", fontsize=13, fontweight="bold", y=0.98)

    rows = [
        (C_USE, "central + tee", "CN 120146158 A", "2025", "actual use", "client TEE + TFHE → central server"),
        (C_USE, "central + tee", "CN 119248878 A", "2024", "actual use", "participant TEE + central aggregator"),
        (C_USE, "decentralized + tee", "US 2022/0374763 A1", "2021", "actual use", "many aggregators, each in a TEE"),
        (C_USE, "decentralized + tee", "WO 2022/243871 A1", "2021", "same invention", "same abstract as the US case"),
        (C_ERR, "hierarchical + tee\n& tee + edge", "CN 120342739 A", "2025", "error / weak", "hierarchical protection; edge cluster OK"),
        (C_ERR, "tee + device", "WO 2021/051629 A1", "2019", "coding error", "TEE on coordinator, not on device"),
    ]
    for i, (face, cell, key, year, tag, note) in enumerate(rows):
        y = 0.82 - i * 0.13
        box = FancyBboxPatch((0.02, y), 0.96, 0.115, boxstyle="round,pad=0.01,rounding_size=0.03", facecolor=face, edgecolor=face, transform=ax.transAxes)
        ax.add_patch(box)
        tc = "white" if face == C_USE else TXT
        ax.text(0.04, y + 0.055, cell, transform=ax.transAxes, fontsize=8.5, fontweight="bold", color=tc, va="center")
        ax.text(0.28, y + 0.055, key, transform=ax.transAxes, fontsize=9, fontweight="bold", color=tc, va="center")
        ax.text(0.54, y + 0.055, year, transform=ax.transAxes, fontsize=9, color=tc, va="center")
        ax.text(0.62, y + 0.055, tag, transform=ax.transAxes, fontsize=9, fontweight="bold", color=tc, va="center")
        ax.text(0.76, y + 0.055, note, transform=ax.transAxes, fontsize=8, color=tc, va="center")

    fig.savefig(FIG / "10_tee_patents.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    fig_verdict()
    fig_h_device()
    fig_tee_cells()
    print("wrote 08 09 10")
