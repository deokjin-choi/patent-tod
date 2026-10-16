"""One-shot board: quadrants × size with the n-partite display graph."""

from __future__ import annotations

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import config as cfg

QUAD_ORDER = (
    ("review", "검토", "occ 높음 · P 낮음"),
    ("existing", "기존 기술", "occ 높음 · P 높음"),
    ("contradiction", "모순", "occ 낮음 · P 낮음"),
    ("opportunity", "기회", "occ 낮음 · P 높음"),
)
QUAD_BG = {
    "review": "#F3E6C8",
    "existing": "#D9E2EC",
    "contradiction": "#EDD8D4",
    "opportunity": "#D5E6E2",
}
QUAD_EDGE = {
    "review": "#8B6914",
    "existing": "#3D4F6F",
    "contradiction": "#6B3A3A",
    "opportunity": "#2C5F5D",
}


def _font():
    path = Path("/usr/share/fonts/truetype/unfonts-core/UnDotum.ttf")
    if path.exists():
        font_manager.fontManager.addfont(str(path))
        fp = font_manager.FontProperties(fname=str(path))
        plt.rcParams["font.family"] = fp.get_name()
        plt.rcParams["axes.unicode_minus"] = False
        return fp
    return None


def shorten(s: str, n: int = 36) -> str:
    s = str(s).replace("|", " + ")
    return s if len(s) <= n else s[: n - 1] + "…"


def board_rows(quad: pd.DataFrame, kg: pd.DataFrame, nodes: pd.DataFrame) -> dict[str, dict[int, list[dict]]]:
    out: dict[str, dict[int, list[dict]]] = {q: {2: [], 3: [], 4: []} for q, *_ in QUAD_ORDER}
    corners = quad[quad["quadrant"].isin([q for q, *_ in QUAD_ORDER])]
    for qname, subq in corners.groupby("quadrant"):
        for row in subq.sort_values(["size", "p_norm"], ascending=[True, False]).itertuples(index=False):
            nd = nodes[nodes["scenario_id"] == row.scenario_id].sort_values("group")
            ed = kg[kg["scenario_id"] == row.scenario_id]
            if nd.empty or ed.empty:
                continue
            node_txt = "   ".join(
                f"{shorten(str(r.group_label), 8)}:{shorten(str(r.entity), 22)}" for r in nd.itertuples(index=False)
            )
            edge_txt = "   ".join(
                f"{shorten(str(r.src_label), 8)}—{r.r}→{shorten(str(r.dst_label), 8)}"
                + ("†" if str(getattr(r, "edge_role", "joint")) == "evidence" else "")
                for r in ed.itertuples(index=False)
            )
            out[str(qname)][int(row.size)].append(
                {
                    "names": str(row.names).replace("|", " + "),
                    "p": float(row.p_norm),
                    "nodes": node_txt,
                    "edges": edge_txt,
                }
            )
    return out


def draw(board: dict) -> None:
    fp = _font()
    fig, axes = plt.subplots(2, 2, figsize=(17.2, 14.0), dpi=140)
    fig.patch.set_facecolor("#F6F3EE")
    axes = axes.ravel()
    for ax, (key, title, axis) in zip(axes, QUAD_ORDER):
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        ax.set_facecolor(QUAD_BG[key])
        for sp in ax.spines.values():
            sp.set_visible(True)
            sp.set_color(QUAD_EDGE[key])
            sp.set_linewidth(1.4)
        ax.set_title(f"{title}   ({axis})", fontproperties=fp, fontsize=13, color=QUAD_EDGE[key], pad=8)
        y = 0.97
        n_all = sum(len(board[key][s]) for s in (2, 3, 4))
        if n_all == 0:
            ax.text(0.5, 0.5, "해당 크기 없음", ha="center", va="center", fontproperties=fp, fontsize=12, color="#78716C")
            continue
        for size in (2, 3, 4):
            items = board[key][size]
            ax.text(0.03, y, f"|s| = {size}   n={len(items)}", fontproperties=fp, fontsize=10, color="#44403C", va="top")
            y -= 0.038
            if not items:
                ax.text(0.05, y, "(없음)", fontproperties=fp, fontsize=8.5, color="#A8A29E", va="top")
                y -= 0.042
                continue
            for item in items:
                ax.text(
                    0.05,
                    y,
                    f"{shorten(item['names'], 48)}   P={item['p']:.2f}",
                    fontproperties=fp,
                    fontsize=8.4,
                    color="#1C1917",
                    va="top",
                    fontweight="bold",
                )
                y -= 0.032
                ax.text(0.07, y, item["nodes"], fontproperties=fp, fontsize=6.8, color="#44403C", va="top")
                y -= 0.028
                ax.text(0.07, y, item["edges"], fontproperties=fp, fontsize=6.8, color="#57534E", va="top")
                y -= 0.040
                if y < 0.03:
                    break
            if y < 0.03:
                break
    fig.suptitle(
        "사분면 조합 지식그래프   ·   |s|=n 이면 그룹당 노드 1개   ·   기존/검토=전형  기회/모순=새로움   ·   점수 P(s)는 그대로",
        fontproperties=fp,
        fontsize=13,
        y=0.995,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    cfg.FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(cfg.FIG / "71_quadrant_kg_board.png", facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {cfg.FIG / '71_quadrant_kg_board.png'}")


def main() -> None:
    quad = pd.read_csv(cfg.OUT / "70_quadrants.csv")
    kg = pd.read_csv(cfg.OUT / "71_quadrant_kg.csv")
    nodes_path = cfg.OUT / "71_scenario_nodes.csv"
    if not nodes_path.exists():
        raise SystemExit("out/71_scenario_nodes.csv 가 없다. 71_quadrant_kg.py 를 먼저 실행하라.")
    nodes = pd.read_csv(nodes_path)
    board = board_rows(quad, kg, nodes)
    draw(board)


if __name__ == "__main__":
    main()
