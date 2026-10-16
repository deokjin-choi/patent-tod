"""Stage 4 — attach time axis to latent groups.

Window occupancy π_g(w) = mean r_ig inside window w (sums to 1 per window).
Trend π̂_g from last window with Dirichlet smoothing. Labels from stage 3
are figure-only. Contract: docs/02_stage_specs.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager

import config as cfg
from lib import ensure_out, write_json

WINDOW_ORDER = list(cfg.WINDOWS.keys())
EXPECTED_N = {"W1": 250, "W2": 507, "W3": 594}


def _font() -> font_manager.FontProperties | None:
    path = Path("/usr/share/fonts/truetype/unfonts-core/UnDotum.ttf")
    if path.exists():
        font_manager.fontManager.addfont(str(path))
        return font_manager.FontProperties(fname=str(path))
    return None


def _require() -> tuple[np.ndarray, pd.DataFrame]:
    resp_path = cfg.OUT / "20_resp.npy"
    idx_path = cfg.OUT / "10_index.csv"
    if not resp_path.exists() or not idx_path.exists():
        raise SystemExit("단계 1–2 산출물이 없다. 10 과 20 을 먼저 실행하라.")
    resp = np.load(resp_path)
    index = pd.read_csv(idx_path)
    if resp.shape[0] != len(index):
        raise SystemExit(f"행 수 불일치 resp={resp.shape[0]} index={len(index)}")
    return resp, index


def _optional_names(k: int) -> dict[int, str]:
    path = cfg.OUT / "30_group_names.csv"
    if not path.exists():
        return {g: f"G{g}" for g in range(k)}
    names = pd.read_csv(path)
    out = {g: f"G{g}" for g in range(k)}
    for _, row in names.iterrows():
        out[int(row["group"])] = str(row["name"])
    return out


def occupancy(resp: np.ndarray, mask: np.ndarray) -> tuple[np.ndarray, int]:
    n = int(mask.sum())
    if n == 0:
        return np.zeros(resp.shape[1], dtype=np.float64), 0
    pi = resp[mask].mean(axis=0)
    s = float(pi.sum())
    if s > 0:
        pi = pi / s
    return pi.astype(np.float64), n


def main() -> int:
    ensure_out()
    cfg.FIG.mkdir(parents=True, exist_ok=True)
    resp, index = _require()
    k = resp.shape[1]
    names = _optional_names(k)
    windows = index["window"].astype(str).to_numpy()
    years = pd.to_numeric(index["filing_year"], errors="coerce")

    rows = []
    pi_by_w: dict[str, np.ndarray] = {}
    n_by_w: dict[str, int] = {}
    for w in WINDOW_ORDER:
        pi, n = occupancy(resp, windows == w)
        pi_by_w[w] = pi
        n_by_w[w] = n
        rows.append((w, n, pi))

    pi_mat = np.vstack([pi_by_w[w] for w in WINDOW_ORDER])  # (W, K)
    row_sum = pi_mat.sum(axis=0)
    row_norm = pi_mat / np.clip(row_sum, 1e-15, None)

    time_rows = []
    n_cells_below = 0
    groups_any_below: set[int] = set()
    for wi, w in enumerate(WINDOW_ORDER):
        n = n_by_w[w]
        for g in range(k):
            expected = n * float(pi_mat[wi, g])
            if expected < 10:
                n_cells_below += 1
                groups_any_below.add(g)
            time_rows.append(
                {
                    "group": g,
                    "window": w,
                    "n_patents": n,
                    "pi_window": float(pi_mat[wi, g]),
                    "pi_row_normalized": float(row_norm[wi, g]),
                    "n_expected": expected,
                }
            )
    time_df = pd.DataFrame(time_rows)
    time_df.to_csv(cfg.OUT / "40_group_time.csv", index=False)

    year_rows = []
    for year in sorted(y for y in years.dropna().unique()):
        yi = int(year)
        mask = years == yi
        pi, n = occupancy(resp, mask.to_numpy())
        if n == 0:
            continue
        for g in range(k):
            year_rows.append(
                {
                    "group": g,
                    "year": yi,
                    "n_patents": n,
                    "pi_window": float(pi[g]),
                    "pi_row_normalized": None,
                }
            )
    year_df = pd.DataFrame(year_rows)
    if not year_df.empty:
        piv = year_df.pivot(index="year", columns="group", values="pi_window")
        row_y = piv.div(piv.sum(axis=0).replace(0, np.nan), axis=1)
        year_df["pi_row_normalized"] = [
            float(row_y.loc[r["year"], r["group"]]) if r["year"] in row_y.index else np.nan
            for _, r in year_df.iterrows()
        ]
    year_df.to_csv(cfg.OUT / "40_group_year.csv", index=False)

    last = cfg.TREND_WINDOW_LAST
    mask_last = windows == last
    n_last = int(mask_last.sum())
    alpha = float(cfg.DIRICHLET_ALPHA0)
    sum_r = resp[mask_last].sum(axis=0) if n_last else np.zeros(k)
    pi_hat = (alpha / k + sum_r) / (alpha + n_last)
    pi_hat = pi_hat / pi_hat.sum()

    x_idx = np.arange(len(WINDOW_ORDER), dtype=np.float64)
    trend_rows = []
    for g in range(k):
        y = pi_mat[:, g]
        slope = float(np.polyfit(x_idx, y, 1)[0]) if len(WINDOW_ORDER) >= 2 else 0.0
        trend_rows.append(
            {
                "group": g,
                "name": names[g],
                "pi_W3": float(pi_by_w["W3"][g]),
                "pi_hat_next": float(pi_hat[g]),
                "slope_linear": slope,
            }
        )
    trend_df = pd.DataFrame(trend_rows)
    trend_df.to_csv(cfg.OUT / "40_trend.csv", index=False)

    sum_err = {w: float(abs(pi_by_w[w].sum() - 1.0)) for w in WINDOW_ORDER}
    n_ok = {w: n_by_w[w] == EXPECTED_N[w] for w in WINDOW_ORDER}
    gates = {
        "pi_sums_to_one": {"pass": all(e < 1e-9 for e in sum_err.values()), "error": sum_err},
        "window_n": {
            "pass": all(n_ok.values()),
            "observed": n_by_w,
            "expected": EXPECTED_N,
        },
        "all_pass": all(e < 1e-9 for e in sum_err.values()),
    }

    write_json(
        cfg.OUT / "40_manifest.json",
        {
            "windows": WINDOW_ORDER,
            "n_by_window": n_by_w,
            "excluded": {
                "pre2019": int((windows == "pre2019").sum()),
                "post2024": int((windows == "post2024").sum()),
            },
            "dirichlet_alpha0": alpha,
            "trend_mode": cfg.TREND_MODE,
            "trend_window_last": last,
            "k": k,
            "n_cells_expected_lt_10": n_cells_below,
            "n_groups_with_cell_lt_10": len(groups_any_below),
            "groups_with_cell_lt_10": sorted(groups_any_below),
            "gates": gates,
        },
    )

    _draw_figure(pi_mat, names, n_by_w)
    print(
        f"[40] n_window={n_by_w} cells<10={n_cells_below} "
        f"groups_any<10={sorted(groups_any_below)}",
        flush=True,
    )
    print("[40] pi_hat_next=" + ", ".join(f"{g}:{pi_hat[g]:.3f}" for g in range(k)), flush=True)
    if not gates["all_pass"]:
        print(f"[40] GATE FAIL: {gates}", file=sys.stderr, flush=True)
        return 1
    if not all(n_ok.values()):
        print(f"[40] WARN window n != expected {EXPECTED_N}: {n_by_w}", flush=True)
    print("[40] gates passed", flush=True)
    return 0


def _draw_figure(pi_mat: np.ndarray, names: dict[int, str], n_by_w: dict[str, int]) -> None:
    fp = _font()
    k = pi_mat.shape[1]
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.2), dpi=140)
    fig.patch.set_facecolor("#F6F3EE")
    colors = ["#2C5F5D", "#3D4F6F", "#8B6914", "#6B3A3A", "#3A5A40", "#5C4A7A"]
    colors = [colors[i % len(colors)] for i in range(k)]

    ax = axes[0]
    x = np.arange(len(WINDOW_ORDER))
    bottom = np.zeros(len(WINDOW_ORDER))
    for g in range(k):
        ax.bar(x, pi_mat[:, g], bottom=bottom, color=colors[g], width=0.62, label=f"G{g}")
        bottom += pi_mat[:, g]
    ax.set_xticks(x)
    ax.set_xticklabels(
        [f"{w}\nn={n_by_w[w]}" for w in WINDOW_ORDER],
        fontproperties=fp,
        fontsize=9,
    )
    ax.set_ylim(0, 1)
    ax.set_ylabel("π_g(w)", fontproperties=fp)
    ax.set_title("창별 점유 (합=1)", fontproperties=fp, fontsize=11)
    ax.set_facecolor("#FFFcf7")
    ax.legend(loc="upper right", fontsize=8, frameon=False)

    ax = axes[1]
    for g in range(k):
        ax.plot(
            x,
            pi_mat[:, g],
            marker="o",
            color=colors[g],
            label=f"G{g}  {names[g][:42]}",
            linewidth=1.8,
        )
    ax.set_xticks(x)
    ax.set_xticklabels(WINDOW_ORDER, fontproperties=fp)
    ax.set_ylabel("π_g(w)", fontproperties=fp)
    ax.set_title("그룹별 시계열", fontproperties=fp, fontsize=11)
    ax.set_facecolor("#FFFcf7")
    ax.legend(loc="best", fontsize=7, frameon=False)
    ax.set_ylim(0, max(0.45, float(pi_mat.max()) * 1.15))

    fig.tight_layout()
    fig.savefig(cfg.FIG / "40_group_time.png", facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    print(f"[40] wrote {cfg.FIG / '40_group_time.png'}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
