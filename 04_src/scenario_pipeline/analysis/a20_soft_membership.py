"""결과 분석 — GMM 책임도의 뾰족함과 경계 특허.

방법론 스크립트(10–80)를 수정하지 않는다. `out/20_resp.npy` 만 읽는다.
혼합의 정의: 두 번째 책임도 > MIXED_SECOND (기본 0.05).
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager

HERE = Path(__file__).resolve().parent
PIPE = HERE.parent
OUT = PIPE / "out"
FIG = HERE / "figures"
FIG.mkdir(parents=True, exist_ok=True)

MIXED_SECOND = 0.05
SHORT = {0: "G0 FL-opt", 1: "G1 Resilience", 2: "G2 Resource", 3: "G3 Non-IID FL", 4: "G4 Anomaly", 5: "G5 BMC"}
BG = "#F6F3EE"
INK = "#1C1917"
MUTED = "#57534E"
CARD = "#FFFcf7"
ACCENT = "#6B3A3A"
TEAL = "#2C5F5D"
GOLD = "#8B6914"


def _font() -> font_manager.FontProperties | None:
    path = Path("/usr/share/fonts/truetype/unfonts-core/UnDotum.ttf")
    if path.exists():
        font_manager.fontManager.addfont(str(path))
        return font_manager.FontProperties(fname=str(path))
    return None


def load() -> tuple[np.ndarray, dict]:
    resp = np.load(OUT / "20_resp.npy")
    names_path = OUT / "30_group_names.csv"
    short = dict(SHORT)
    if names_path.exists():
        names = pd.read_csv(names_path)
        for _, row in names.iterrows():
            g = int(row["group"])
            raw = str(row["name"])
            if "(" in raw and ")" in raw:
                abbr = raw[raw.find("(") + 1 : raw.rfind(")")]
            else:
                abbr = f"G{g}"
            short[g] = f"G{g} {abbr}"
    return resp, short


def stats(resp: np.ndarray) -> dict:
    mx = resp.max(axis=1)
    second = np.partition(resp, -2, axis=1)[:, -2]
    hard = resp.argmax(axis=1)
    mixed = second > MIXED_SECOND
    overlap = resp.T @ resp
    pairs: dict[str, int] = {}
    for i in np.where(mixed)[0]:
        a, b = np.argsort(-resp[i])[:2]
        key = f"{int(a)}-{int(b)}"
        pairs[key] = pairs.get(key, 0) + 1
    n24 = 0
    for i in np.where(mixed)[0]:
        top2 = set(np.argsort(-resp[i])[:2].tolist())
        if top2 == {2, 4}:
            n24 += 1
    return {
        "n": int(resp.shape[0]),
        "k": int(resp.shape[1]),
        "mean_max": float(mx.mean()),
        "median_max": float(np.median(mx)),
        "n_max_ge_0.99": int((mx >= 0.99).sum()),
        "n_max_ge_0.95": int((mx >= 0.95).sum()),
        "n_mixed": int(mixed.sum()),
        "n_mixed_2_and_4": n24,
        "hard_counts": np.bincount(hard, minlength=resp.shape[1]).astype(int).tolist(),
        "pair_counts": pairs,
        "overlap": overlap.tolist(),
        "mixed_threshold_second": MIXED_SECOND,
    }


def draw(resp: np.ndarray, short: dict, info: dict) -> Path:
    fp = _font()
    mx = resp.max(axis=1)
    second = np.partition(resp, -2, axis=1)[:, -2]
    mixed = second > MIXED_SECOND
    overlap = np.array(info["overlap"])
    k = resp.shape[1]
    labels = [short.get(g, f"G{g}") for g in range(k)]

    fig = plt.figure(figsize=(13.6, 8.6), dpi=150)
    fig.patch.set_facecolor(BG)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.05, 1.15], hspace=0.38, wspace=0.32)

    fig.suptitle(
        "GMM 책임도는 거의 분할이다 — 혼합은 80건, 그중 대부분이 G2–G4",
        fontproperties=fp,
        fontsize=14,
        color=INK,
        y=0.98,
    )
    fig.text(
        0.5,
        0.935,
        f"N=1,412,  K=6,  max r ≥ 0.99 인 특허 {info['n_max_ge_0.99']}건  ·  "
        f"두 번째 r > {MIXED_SECOND:g} 인 혼합 {info['n_mixed']}건  ·  "
        f"G2(Resource)×G4(Anomaly) {info['n_mixed_2_and_4']}건",
        ha="center",
        fontproperties=fp,
        fontsize=9.5,
        color=MUTED,
    )

    ax = fig.add_subplot(gs[0, 0])
    ax.set_facecolor(CARD)
    bins = np.linspace(0.5, 1.0, 51)
    ax.hist(mx[~mixed], bins=bins, color=TEAL, label="단일 그룹", edgecolor="none")
    ax.hist(mx[mixed], bins=bins, color=GOLD, label="혼합 (2nd r > 0.05)", edgecolor="none")
    ax.axvline(0.99, color=ACCENT, ls="--", lw=1.0)
    ax.text(0.99, ax.get_ylim()[1] * 0.92 if ax.get_ylim()[1] else 1, "  0.99", color=ACCENT, fontsize=8, va="top")
    ax.set_xlim(0.5, 1.0)
    ax.set_xlabel("해당 특허의 최대 책임도  max r_ig", fontproperties=fp, fontsize=9)
    ax.set_ylabel("특허 수", fontproperties=fp, fontsize=9)
    ax.set_title("A. 대부분의 특허는 한 그룹에 붙어 있다", fontproperties=fp, fontsize=11, loc="left")
    ax.legend(frameon=False, prop=fp, fontsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax = fig.add_subplot(gs[0, 1])
    ax.set_facecolor(CARD)
    vis = overlap.copy()
    np.fill_diagonal(vis, np.nan)
    im = ax.imshow(vis, cmap="YlOrBr", origin="upper")
    ax.set_xticks(range(k))
    ax.set_yticks(range(k))
    ax.set_xticklabels(labels, fontproperties=fp, fontsize=7.5, rotation=35, ha="right")
    ax.set_yticklabels(labels, fontproperties=fp, fontsize=7.5)
    for i in range(k):
        for j in range(k):
            if i == j:
                ax.text(j, i, f"{overlap[i, j]:.0f}", ha="center", va="center", color=MUTED, fontsize=7)
            elif overlap[i, j] >= 1:
                ax.text(j, i, f"{overlap[i, j]:.1f}", ha="center", va="center", color=INK, fontsize=7.5)
    ax.set_title("B. 그룹 쌍 겹침  Σ r_i,g r_i,h  (대각=거의 n_hard)", fontproperties=fp, fontsize=11, loc="left")
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
    cbar.ax.tick_params(labelsize=7)
    cbar.set_label("off-diagonal mass", fontsize=8)

    ax = fig.add_subplot(gs[1, :])
    ax.set_facecolor(CARD)
    r2, r4 = resp[:, 2], resp[:, 4]
    ax.scatter(r2[~mixed], r4[~mixed], s=10, alpha=0.25, c=TEAL, linewidths=0, label="나머지 1,332건")
    ax.scatter(r2[mixed], r4[mixed], s=28, alpha=0.9, c=GOLD, edgecolors=INK, linewidths=0.3, label=f"혼합 {info['n_mixed']}건")
    ax.plot([0, 1], [1, 0], ls=":", color=MUTED, lw=1.0)
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.set_aspect("equal")
    ax.set_xlabel("G2 Resource (ECRAO)  책임도", fontproperties=fp, fontsize=10)
    ax.set_ylabel("G4 Anomaly (ECAD)  책임도", fontproperties=fp, fontsize=10)
    ax.set_title(
        "C. 혼합 80건은 거의 G2–G4 선 위에 있다  (한 특허가 두 주제를 동시에 듦)",
        fontproperties=fp,
        fontsize=11,
        loc="left",
    )
    ax.legend(frameon=False, prop=fp, fontsize=9, loc="upper right")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.text(
        0.02,
        0.08,
        "점선: r2 + r4 = 1. 이 선 근처는 다른 그룹 확률이 거의 0.",
        fontproperties=fp,
        fontsize=8,
        color=MUTED,
    )

    out = FIG / "a20_soft_membership.png"
    fig.savefig(out, facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    return out


def main() -> None:
    resp, short = load()
    info = stats(resp)
    (HERE / "a20_soft_membership_stats.json").write_text(
        json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    path = draw(resp, short, info)
    print(
        f"n={info['n']}  max>=0.99: {info['n_max_ge_0.99']}  "
        f"mixed: {info['n_mixed']}  of which G2-G4: {info['n_mixed_2_and_4']}"
    )
    print(path)


if __name__ == "__main__":
    main()
