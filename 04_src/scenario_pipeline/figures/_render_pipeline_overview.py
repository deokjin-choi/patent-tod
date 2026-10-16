"""README 대표 그림: latent-group 시나리오 공간 파이프라인."""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

ROOT = Path(__file__).resolve().parent
FONT = "/usr/share/fonts/truetype/unfonts-core/UnDotum.ttf"
FONT_B = "/usr/share/fonts/truetype/unfonts-core/UnDotumBold.ttf"
font_manager.fontManager.addfont(FONT)
font_manager.fontManager.addfont(FONT_B)
REG = font_manager.FontProperties(fname=FONT)
BOLD = font_manager.FontProperties(fname=FONT_B)

BG = "#F6F3EE"
INK = "#1C1917"
MUTED = "#57534E"
LINE = "#D6D0C6"
CARD = "#FFFcf7"
WHITE = "#FFFFFF"

PHASES = [
    {
        "no": "1",
        "title": "그룹 발견",
        "blurb": "임베딩 → 베이지안 GMM",
        "color": "#2C5F5D",
        "tint": "#E7F0EF",
        "stages": [
            ("01", "벡터 입력  x", "P/S/E + KG pooling + CPC\n→ PCA 30d", "10_build_features.py"),
            ("02", "Latent tech group", "Bayesian GMM  ·  r_ig", "20_fit_bgmm.py"),
            ("04", "시간축 부착", "창별 soft membership  π_g(w)", "40_group_time.py"),
        ],
        "aside": ("03", "그룹 명명", "LLM · 라벨 전용 · 수식 밖", "30_name_groups.py"),
    },
    {
        "no": "2",
        "title": "Feasibility",
        "blurb": "상세 KG로 F(·) 학습",
        "color": "#3D4F6F",
        "tint": "#E8ECF3",
        "stages": [
            ("05a", "KG 데이터셋", "트리플 · 표면 관계 단위", "50_build_kg_dataset.py"),
            ("05b", "F 스코어러", "고정 768d + 로지스틱\nisotonic 캘리브레이션", "51_fit_feasibility.py"),
        ],
        "aside": None,
    },
    {
        "no": "3",
        "title": "시나리오 공간",
        "blurb": "그룹 조합을 전수 열거",
        "color": "#8B6914",
        "tint": "#F6EFD9",
        "stages": [
            ("06a", "쌍 점수", "교차 후보 top-10 평균", "60_pair_scores.py"),
            ("06b", "P(s) 평가", "P ∝ P_trend · F_min^β\n|s| ∈ {2,3,4}", "61_scenario_space.py"),
        ],
        "aside": None,
    },
    {
        "no": "4",
        "title": "사분면 해석",
        "blurb": "현재 점유 × 확률",
        "color": "#6B3A3A",
        "tint": "#F3E8E6",
        "stages": [
            ("07", "사분면 분류", "occ = 엔티티 클러스터 공유", "70_quadrants.py"),
        ],
        "aside": None,
        "quad": True,
    },
    {
        "no": "5",
        "title": "슬라이딩 검증",
        "blurb": "창 2개 · 누수 금지",
        "color": "#3A5A40",
        "tint": "#E7EFE8",
        "stages": [
            ("08", "윈도우 검증", "≤W1→W2, ≤W2→W3\nno_F / no_trend 대조", "80_sliding_window.py"),
        ],
        "aside": None,
        "windows": True,
    },
]


def rounded(ax, x, y, w, h, fc, ec, lw=0.8, r=0.08, z=2, ls="-"):
    p = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle=f"round,pad=0,rounding_size={r}",
        facecolor=fc,
        edgecolor=ec,
        linewidth=lw,
        linestyle=ls,
        mutation_aspect=0.6,
        zorder=z,
    )
    ax.add_patch(p)
    return p


def txt(ax, x, y, s, *, fp, size, color=INK, ha="left", va="center", z=5):
    ax.text(x, y, s, fontproperties=fp, fontsize=size, color=color, ha=ha, va=va, zorder=z)


def main():
    fig_w, fig_h = 18.0, 10.0
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=160)
    fig.patch.set_facecolor(BG)
    ax.set_xlim(0, fig_w)
    ax.set_ylim(0, fig_h)
    ax.axis("off")
    ax.set_facecolor(BG)

    # title
    txt(ax, 0.45, 9.52, "Latent Group 기반 시나리오 공간 파이프라인", fp=BOLD, size=20)
    txt(
        ax,
        0.45,
        9.10,
        "키워드 축을 고정하지 않는다  ·  임베딩으로 그룹을 찾고 조합을 전수 열거한다  ·  단계 3은 라벨 전용",
        fp=REG,
        size=10.5,
        color=MUTED,
    )

    # input chips
    inputs = [
        ("PSE 특허  1,412건", "P / S / E 텍스트"),
        ("상세 KG", "엔티티 · 관계 트리플"),
        ("CPC subclass", "113d + 결측 플래그"),
        ("인코더", "all-mpnet-base-v2  768d"),
    ]
    chip_w, chip_h, gap = 3.95, 0.72, 0.18
    x0 = 0.45
    y_chip = 8.15
    for i, (a, b) in enumerate(inputs):
        x = x0 + i * (chip_w + gap)
        rounded(ax, x, y_chip, chip_w, chip_h, WHITE, LINE, lw=0.7, r=0.07)
        ax.add_patch(Rectangle((x, y_chip), 0.09, chip_h, facecolor="#2C5F5D", edgecolor="none", zorder=3))
        txt(ax, x + 0.26, y_chip + 0.47, a, fp=BOLD, size=9.5)
        txt(ax, x + 0.26, y_chip + 0.22, b, fp=REG, size=8, color=MUTED)

    # down arrow into phases
    ax.annotate(
        "",
        xy=(9.0, 7.88),
        xytext=(9.0, 8.10),
        arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.1),
        zorder=4,
    )

    # five phase columns
    left, right, top, bot = 0.35, 17.65, 7.82, 1.55
    n = 5
    g = 0.20
    col_w = (right - left - (n - 1) * g) / n

    for i, ph in enumerate(PHASES):
        x = left + i * (col_w + g)
        card = rounded(ax, x, bot, col_w, top - bot, WHITE, LINE, lw=0.8, r=0.10, z=1)
        header = Rectangle((x, top - 0.62), col_w, 0.62, facecolor=ph["color"], edgecolor="none", zorder=2)
        header.set_clip_path(card)
        ax.add_patch(header)
        txt(ax, x + 0.18, top - 0.22, f"({ph['no']})", fp=BOLD, size=10, color="#F4EFE6")
        txt(ax, x + 0.62, top - 0.22, ph["title"], fp=BOLD, size=13, color=WHITE)
        txt(ax, x + 0.18, top - 0.48, ph["blurb"], fp=REG, size=8.4, color="#E8E4DC")

        y = top - 0.82
        for sid, name, desc, script in ph["stages"]:
            h = 1.18
            rounded(ax, x + 0.14, y - h, col_w - 0.28, h, ph["tint"], ph["color"], lw=0.7, r=0.07, z=3)
            # number badge
            rounded(ax, x + 0.24, y - 0.38, 0.52, 0.26, ph["color"], ph["color"], lw=0, r=0.05, z=4)
            txt(ax, x + 0.50, y - 0.25, sid, fp=BOLD, size=7.5, color=WHITE, ha="center")
            txt(ax, x + 0.84, y - 0.25, name, fp=BOLD, size=10)
            txt(ax, x + 0.26, y - 0.68, desc, fp=REG, size=8, color=MUTED, va="top")
            txt(ax, x + 0.26, y - h + 0.16, script, fp=REG, size=7.4, color=ph["color"], va="center")
            y -= h + 0.12

        if ph.get("aside"):
            sid, name, desc, script = ph["aside"]
            h = 0.92
            rounded(
                ax,
                x + 0.14,
                y - h,
                col_w - 0.28,
                h,
                "#F3F1EC",
                MUTED,
                lw=0.9,
                r=0.07,
                z=3,
                ls=(0, (2.2, 1.6)),
            )
            rounded(ax, x + 0.24, y - 0.34, 0.52, 0.24, MUTED, MUTED, lw=0, r=0.05, z=4)
            txt(ax, x + 0.50, y - 0.22, sid, fp=BOLD, size=7.5, color=WHITE, ha="center")
            txt(ax, x + 0.84, y - 0.22, name, fp=BOLD, size=10, color=MUTED)
            txt(ax, x + 0.26, y - 0.52, desc, fp=REG, size=7.8, color=MUTED, va="top")
            txt(ax, x + 0.26, y - h + 0.14, script, fp=REG, size=7.2, color=MUTED)
            y -= h + 0.10

        if ph.get("quad"):
            # 2x2 legend
            qx, qy, qw, qh = x + 0.28, bot + 0.28, col_w - 0.56, 2.05
            cells = [
                (0, 1, "검토", "occ 높 · P 낮"),
                (1, 1, "기존 기술", "occ 높 · P 높"),
                (0, 0, "모순", "occ 낮 · P 낮"),
                (1, 0, "미래 기회", "occ 낮 · P 높"),
            ]
            cw, ch = (qw - 0.08) / 2, (qh - 0.36) / 2
            txt(ax, x + col_w / 2, qy + qh - 0.02, "occ  ×  P(s)   (삼분위, 중간 보류)", fp=REG, size=7.2, color=MUTED, ha="center")
            accent = {
                "검토": "#8A7A6A",
                "기존 기술": "#4A5560",
                "모순": "#7A4A4A",
                "미래 기회": ph["color"],
            }
            for cx, cy, lab, sub in cells:
                xx = qx + cx * (cw + 0.08)
                yy = qy + cy * (ch + 0.08)
                fill = "#E8F0E9" if lab == "미래 기회" else "#F4F1EC"
                rounded(ax, xx, yy, cw, ch, fill, accent[lab], lw=0.8 if lab == "미래 기회" else 0.6, r=0.05, z=3)
                txt(ax, xx + cw / 2, yy + ch * 0.62, lab, fp=BOLD, size=8.5, color=accent[lab], ha="center")
                txt(ax, xx + cw / 2, yy + ch * 0.30, sub, fp=REG, size=6.6, color=MUTED, ha="center")

        if ph.get("windows"):
            wx, wy, ww = x + 0.22, bot + 0.32, col_w - 0.44
            bars = [
                ("W1  2019–20", "#9BB39E"),
                ("W2  2021–22", "#6E9173"),
                ("W3  2023–24", "#3A5A40"),
            ]
            txt(ax, x + col_w / 2, wy + 2.05, "학습 창 → 평가 창", fp=BOLD, size=8.4, color=ph["color"], ha="center")
            for j, (lab, c) in enumerate(bars):
                rounded(ax, wx, wy + 1.42 - j * 0.48, ww, 0.40, c, c, lw=0, r=0.05, z=3)
                txt(ax, wx + ww / 2, wy + 1.62 - j * 0.48, lab, fp=BOLD, size=8.2, color=WHITE, ha="center")
            txt(ax, x + col_w / 2, wy + 0.12, "창마다 PCA · BGMM · F 재적합", fp=REG, size=7.2, color=MUTED, ha="center")

        # arrows between phase columns
        if i < n - 1:
            ax.annotate(
                "",
                xy=(x + col_w + g - 0.02, (top + bot) / 2),
                xytext=(x + col_w + 0.02, (top + bot) / 2),
                arrowprops=dict(arrowstyle="-|>", color=ph["color"], lw=1.4, mutation_scale=12),
                zorder=6,
            )

    # footer
    rounded(ax, 0.35, 0.22, 17.30, 1.16, WHITE, LINE, lw=0.8, r=0.08, z=1)
    txt(ax, 0.58, 1.08, "계산 경로", fp=BOLD, size=9.5, color=INK)
    path = "1  벡터 x    →    2  BGMM    →    4  시간축    →    5  F(·)    →    6  조합 P(s)    →    7  사분면    →    8  검증"
    txt(ax, 0.58, 0.74, path, fp=REG, size=10, color=INK)
    txt(
        ax,
        0.58,
        0.42,
        "P(s)  ∝  P_trend(s) · F_min(s)^β    ·    β = 1    ·    전수 열거 (이 단계를 MCMC라 부르지 않는다)    ·    단계 3은 건너뛴다",
        fp=REG,
        size=8.6,
        color=MUTED,
    )

    out = ROOT / "pipeline_overview.png"
    fig.savefig(out, dpi=160, facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.18)
    plt.close(fig)
    print(out, out.stat().st_size)


if __name__ == "__main__":
    main()
