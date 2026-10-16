"""Stage 7 — occupancy × P(s) quadrants.

Primary occ is D1 130-cluster share (not 6-a surface entities).
Terciles are by |s|. Contract: docs/02_stage_specs.md stage 7.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib.lines import Line2D

import config as cfg
from lib import cpc_key, entity_cluster, ensure_out, load_kg_assets, load_patents, write_json

OCC_COL = {
    "entity_cluster": "occ_ent",
    "assignee": "occ_asg",
    "cpc": "occ_cpc",
    "soft_product": "occ_soft",
}

QUAD_LABEL = {
    "existing": "기존 기술",
    "review": "이상·오류 검토",
    "contradiction": "모순 공간",
    "opportunity": "미래 기회",
    "undecided": "보류",
}

QUAD_COLOR = {
    "existing": "#3D4F6F",
    "review": "#8B6914",
    "contradiction": "#6B3A3A",
    "opportunity": "#2C5F5D",
    "undecided": "#A8A29E",
}

CORNERS = ("existing", "review", "contradiction", "opportunity")


def _font():
    path = Path("/usr/share/fonts/truetype/unfonts-core/UnDotum.ttf")
    if path.exists():
        font_manager.fontManager.addfont(str(path))
        fp = font_manager.FontProperties(fname=str(path))
        plt.rcParams["font.family"] = fp.get_name()
        plt.rcParams["axes.unicode_minus"] = False
        return fp
    return None


def parse_groups(raw: str) -> tuple[int, ...]:
    return tuple(int(x) for x in str(raw).split("|") if str(x).strip() != "")


def assign_terciles(values: pd.Series) -> pd.Series:
    n = len(values)
    order = np.lexsort((values.index.to_numpy(), values.to_numpy()))
    ranks = np.empty(n, dtype=int)
    ranks[order] = np.arange(n)
    n_low = n // 3
    n_high = n // 3
    labels = np.full(n, "mid", dtype=object)
    labels[ranks < n_low] = "low"
    labels[ranks >= n - n_high] = "high"
    return pd.Series(labels, index=values.index)


def tercile_cuts(values: pd.Series) -> tuple[float, float] | None:
    n = len(values)
    n_low = n // 3
    n_high = n // 3
    if n_low == 0 or n_high == 0 or n_low + n_high >= n:
        return None
    order = np.lexsort((values.index.to_numpy(), values.to_numpy()))
    sorted_vals = values.to_numpy()[order]
    cut_low = 0.5 * (float(sorted_vals[n_low - 1]) + float(sorted_vals[n_low]))
    cut_high = 0.5 * (float(sorted_vals[n - n_high - 1]) + float(sorted_vals[n - n_high]))
    return cut_low, cut_high


def terciles(df: pd.DataFrame, col: str) -> pd.Series:
    out = pd.Series(index=df.index, dtype=object)
    if cfg.TERCILE_BY_SIZE:
        for _, idx in df.groupby("size").groups.items():
            out.loc[idx] = assign_terciles(df.loc[idx, col]).to_numpy()
    else:
        out.loc[df.index] = assign_terciles(df[col]).to_numpy()
    return out


def quadrant_of(occ_t: str, p_t: str) -> str:
    if occ_t == "mid" or p_t == "mid":
        return "undecided"
    if occ_t == "high" and p_t == "high":
        return "existing"
    if occ_t == "high" and p_t == "low":
        return "review"
    if occ_t == "low" and p_t == "low":
        return "contradiction"
    return "opportunity"


def occ_share(profile: np.ndarray, groups: tuple[int, ...]) -> float:
    return float(profile[list(groups)].min(axis=0).sum())


def entity_profiles(resp: np.ndarray, patents: list[dict], index: pd.DataFrame, assets: dict) -> np.ndarray:
    n_clusters = 1 + max(int(c) for c in assets["entity_mapping"].values())
    k = resp.shape[1]
    mass = np.zeros((k, n_clusters), dtype=np.float64)
    pub_to_i = {str(p): i for i, p in enumerate(index["publication_number"].astype(str))}
    for rec in patents:
        i = pub_to_i.get(rec["publication_number"])
        if i is None:
            continue
        clusters = []
        for head, _rel, tail in rec["triples_v2"]:
            for name in (head, tail):
                cid = entity_cluster(name, assets)
                if cid is not None and 0 <= cid < n_clusters:
                    clusters.append(cid)
        if not clusters:
            continue
        uniq, counts = np.unique(np.array(clusters, dtype=np.int64), return_counts=True)
        mass[:, uniq] += resp[i][:, None] * counts[None, :]
    tot = mass.sum(axis=1, keepdims=True)
    return mass / np.clip(tot, 1e-15, None)


def cpc_profiles(resp: np.ndarray, patents: list[dict], index: pd.DataFrame) -> np.ndarray:
    keys = sorted({cpc_key(code) for rec in patents for code in rec["cpc"] if cpc_key(code)})
    key_i = {key: j for j, key in enumerate(keys)}
    k = resp.shape[1]
    mass = np.zeros((k, len(keys)), dtype=np.float64)
    pub_to_i = {str(p): i for i, p in enumerate(index["publication_number"].astype(str))}
    for rec in patents:
        i = pub_to_i.get(rec["publication_number"])
        if i is None:
            continue
        seen = {cpc_key(code) for code in rec["cpc"] if cpc_key(code) in key_i}
        if not seen:
            continue
        cols = np.array([key_i[key] for key in seen], dtype=np.int64)
        mass[:, cols] += resp[i][:, None]
    tot = mass.sum(axis=1, keepdims=True)
    return mass / np.clip(tot, 1e-15, None)


def assignee_groups(resp: np.ndarray, index: pd.DataFrame) -> dict[str, set[int]]:
    hard = resp.argmax(axis=1)
    out: dict[str, set[int]] = defaultdict(set)
    excluded = {str(x) for x in cfg.ASSIGNEE_EXCLUDE}
    for i, raw in enumerate(index["assignee"].astype(str)):
        name = raw.strip()
        if not name or name in excluded:
            continue
        out[name].add(int(hard[i]))
    return dict(out)


def spearman(a: pd.Series, b: pd.Series) -> float:
    if a.nunique() < 2 or b.nunique() < 2:
        return float("nan")
    return float(a.corr(b, method="spearman"))


def classify(df: pd.DataFrame, occ_col: str, p_col: str = "p_norm") -> tuple[pd.Series, pd.Series, pd.Series]:
    occ_t = terciles(df, occ_col)
    p_t = terciles(df, p_col)
    quad = pd.Series([quadrant_of(o, p) for o, p in zip(occ_t, p_t)], index=df.index)
    return occ_t, p_t, quad


def count_cells(quad: pd.Series, sizes: pd.Series) -> pd.DataFrame:
    rows = []
    for size in sorted(sizes.unique()):
        sub = quad[sizes == size]
        for name in list(CORNERS) + ["undecided"]:
            rows.append({"size": int(size), "quadrant": name, "n": int((sub == name).sum())})
    for name in list(CORNERS) + ["undecided"]:
        rows.append({"size": "all", "quadrant": name, "n": int((quad == name).sum())})
    return pd.DataFrame(rows)


def tercile_span(sub: pd.DataFrame, value_col: str, tercile_col: str) -> tuple[float, float] | None:
    mid = sub.loc[sub[tercile_col] == "mid", value_col]
    if mid.empty:
        return None
    return float(mid.min()), float(mid.max())


def _draw_tercile_guides(ax, sub: pd.DataFrame, occ_col: str, fp) -> None:
    x_cuts = tercile_cuts(sub[occ_col])
    y_cuts = tercile_cuts(sub["p_norm"])
    if x_cuts:
        ax.axvspan(x_cuts[0], x_cuts[1], color="#D6D3D1", alpha=0.38, zorder=0)
        for x in x_cuts:
            ax.axvline(x, color="#57534E", linestyle="--", linewidth=1.05, zorder=1)
    if y_cuts:
        ax.axhspan(y_cuts[0], y_cuts[1], color="#D6D3D1", alpha=0.38, zorder=0)
        for y in y_cuts:
            ax.axhline(y, color="#57534E", linestyle="--", linewidth=1.05, zorder=1)
    if x_cuts and y_cuts:
        x0, x1 = x_cuts
        y0, y1 = y_cuts
        xr = ax.get_xlim()
        yr = ax.get_ylim()
        labels = (
            ((xr[0] + x0) / 2, (y1 + yr[1]) / 2, "미래 기회"),
            ((x1 + xr[1]) / 2, (y1 + yr[1]) / 2, "기존 기술"),
            ((xr[0] + x0) / 2, (yr[0] + y0) / 2, "모순"),
            ((x1 + xr[1]) / 2, (yr[0] + y0) / 2, "검토"),
        )
        for x, y, text in labels:
            ax.text(
                x,
                y,
                text,
                ha="center",
                va="center",
                fontsize=7.5,
                color="#57534E",
                alpha=0.85,
                fontproperties=fp,
                zorder=1,
            )


def draw_figure(df: pd.DataFrame, occ_col: str, occ_axis: str) -> None:
    fp = _font()
    fig = plt.figure(figsize=(12.8, 5.8), dpi=140)
    fig.patch.set_facecolor("#F6F3EE")
    gs = fig.add_gridspec(2, 3, height_ratios=[3.2, 1.15], hspace=0.42, wspace=0.28)
    axes = [fig.add_subplot(gs[0, i]) for i in range(3)]
    bar_ax = fig.add_subplot(gs[1, :])
    for ax, size in zip(axes, cfg.SCENARIO_SIZES):
        sub = df[df["size"] == size]
        n_hold = int((sub["quadrant"] == "undecided").sum())
        ax.set_title(f"|s|={size}  n={len(sub)}  보류 {n_hold}", fontproperties=fp, fontsize=11)
        for q, color in QUAD_COLOR.items():
            bit = sub[sub["quadrant"] == q]
            ax.scatter(
                bit[occ_col],
                bit["p_norm"],
                c=color,
                s=42 if q != "undecided" else 22,
                alpha=0.92 if q != "undecided" else 0.4,
                edgecolors="#1C1917",
                linewidths=0.35,
                zorder=3 if q != "undecided" else 2,
            )
        _draw_tercile_guides(ax, sub, occ_col, fp)
        bits = [sub.nlargest(1, "p_norm")]
        opp = sub[sub["quadrant"] == "opportunity"]
        if len(opp):
            bits.append(opp.nsmallest(min(2, len(opp)), occ_col))
        labeled = pd.concat(bits).drop_duplicates(subset=["scenario_id"])
        for row in labeled.itertuples(index=False):
            ax.annotate(
                str(row.names).replace("|", "+"),
                (getattr(row, occ_col), row.p_norm),
                textcoords="offset points",
                xytext=(4, 4),
                fontsize=6.5,
                fontproperties=fp,
            )
        ax.set_xlabel("occ  (현재 점유)", fontproperties=fp, fontsize=9)
        ax.set_facecolor("#F6F3EE")
    axes[0].set_ylabel("P(s)  (크기별 정규화)", fontproperties=fp, fontsize=10)
    order = ["opportunity", "existing", "contradiction", "review", "undecided"]
    counts = [int((df["quadrant"] == q).sum()) for q in order]
    bars = bar_ax.bar(
        [QUAD_LABEL[q] for q in order],
        counts,
        color=[QUAD_COLOR[q] for q in order],
        edgecolor="#1C1917",
        width=0.62,
    )
    for rect, n in zip(bars, counts):
        bar_ax.text(rect.get_x() + rect.get_width() / 2, n + 0.4, str(n), ha="center", va="bottom", fontsize=9, fontproperties=fp)
    bar_ax.set_ylim(0, max(counts) + 6)
    bar_ax.set_ylabel("시나리오 수", fontproperties=fp, fontsize=9)
    for label in bar_ax.get_xticklabels():
        label.set_fontproperties(fp)
    bar_ax.set_title(
        "점선 = 크기별 1/3 경계. 회색 띠 = 중간 1/3(보류). 한쪽이라도 중간이면 칸에 넣지 않음.",
        fontproperties=fp,
        fontsize=10,
    )
    bar_ax.set_facecolor("#F6F3EE")
    handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=QUAD_COLOR[q], markeredgecolor="#1C1917", markersize=7, label=QUAD_LABEL[q])
        for q in order
    ]
    fig.legend(handles=handles, loc="upper center", ncol=5, frameon=False, prop=fp, bbox_to_anchor=(0.5, 1.04))
    fig.suptitle(
        f"사분면  —  x=occ({occ_axis}), y=P(s)  ·  점선은 크기별 삼분위(1/3) 구분선",
        fontproperties=fp,
        fontsize=12,
        y=1.08,
    )
    cfg.FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(cfg.FIG / "70_quadrants.png", facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    ensure_out()
    if "--figure" in sys.argv:
        path = cfg.OUT / "70_quadrants.csv"
        if not path.exists():
            raise SystemExit("out/70_quadrants.csv 가 없다.")
        df = pd.read_csv(path)
        occ_axis = str(df["occ_axis_used"].iloc[0]) if "occ_axis_used" in df.columns else "entity_cluster"
        occ_col = OCC_COL.get(occ_axis, "occ_ent")
        draw_figure(df, occ_col, occ_axis)
        print(f"[70] redrew {cfg.FIG / '70_quadrants.png'}", flush=True)
        return 0
    scen_path = cfg.OUT / "61_scenarios.csv"
    resp_path = cfg.OUT / "20_resp.npy"
    idx_path = cfg.OUT / "10_index.csv"
    if not scen_path.exists():
        raise SystemExit("out/61_scenarios.csv 가 없다. 먼저 61_scenario_space.py 를 실행하라.")
    if not resp_path.exists() or not idx_path.exists():
        raise SystemExit("단계 1–2 산출물이 없다.")
    scenarios = pd.read_csv(scen_path)
    resp = np.load(resp_path)
    index = pd.read_csv(idx_path)
    if resp.shape[0] != len(index):
        raise SystemExit(f"resp {resp.shape[0]} != index {len(index)}")
    print("[70] load patents + KG assets (D1 130-cluster occ, not 6-a surface)", flush=True)
    patents = load_patents()
    assets = load_kg_assets()
    u_ent = entity_profiles(resp, patents, index, assets)
    u_cpc = cpc_profiles(resp, patents, index)
    asg = assignee_groups(resp, index)
    np.save(cfg.OUT / "70_u_ent.npy", u_ent)

    rows = []
    for row in scenarios.itertuples(index=False):
        groups = parse_groups(row.groups)
        prod = np.prod(resp[:, list(groups)], axis=1)
        rows.append(
            {
                "scenario_id": row.scenario_id,
                "groups": row.groups,
                "names": row.names,
                "size": int(row.size),
                "p_norm": float(row.p_norm),
                "p_trend": float(row.p_trend),
                "f_min": float(row.f_min),
                "occ_ent": occ_share(u_ent, groups),
                "occ_asg": float(sum(1 for gs in asg.values() if set(groups) <= gs)),
                "occ_cpc": occ_share(u_cpc, groups),
                "occ_soft": float(prod.sum()),
            }
        )
    df = pd.DataFrame(rows)

    occ_t_ent, p_t, q_ent = classify(df, "occ_ent")
    occ_t_asg, _, q_asg = classify(df, "occ_asg")
    occ_t_cpc, _, q_cpc = classify(df, "occ_cpc")
    df["p_tercile"] = p_t.to_numpy()
    df["occ_tercile_ent"] = occ_t_ent.to_numpy()
    df["occ_tercile_asg"] = occ_t_asg.to_numpy()
    df["occ_tercile_cpc"] = occ_t_cpc.to_numpy()
    df["quadrant_ent"] = q_ent.to_numpy()
    df["quadrant_asg"] = q_asg.to_numpy()
    df["quadrant_cpc"] = q_cpc.to_numpy()

    rho_ent_f = spearman(df["occ_ent"], df["f_min"])
    rho_ent_asg = spearman(df["occ_ent"], df["occ_asg"])
    rho_ent_cpc = spearman(df["occ_ent"], df["occ_cpc"])
    rho_asg_cpc = spearman(df["occ_asg"], df["occ_cpc"])
    rho_ent_p = spearman(df["occ_ent"], df["p_norm"])
    rho_soft_max = float(df["occ_soft"].max())
    rho_soft_med = float(df["occ_soft"].median())
    primary = cfg.OCC_PRIMARY
    reason = "config"
    if np.isfinite(rho_ent_f) and abs(rho_ent_f) > 0.7:
        primary = "assignee"
        reason = f"|spearman(occ_ent, f_min)|={rho_ent_f:.3f}>0.7 → occ_asg"
    occ_col = OCC_COL[primary]
    if primary == "entity_cluster":
        df["occ_tercile"] = df["occ_tercile_ent"]
        df["quadrant"] = df["quadrant_ent"]
    elif primary == "assignee":
        df["occ_tercile"] = df["occ_tercile_asg"]
        df["quadrant"] = df["quadrant_asg"]
    else:
        df["occ_tercile"] = df["occ_tercile_cpc"]
        df["quadrant"] = df["quadrant_cpc"]
    df["occ_axis_used"] = primary

    agreement_rows = [
        {"metric_a": "occ_ent", "metric_b": "occ_asg", "spearman": rho_ent_asg},
        {"metric_a": "occ_ent", "metric_b": "occ_cpc", "spearman": rho_ent_cpc},
        {"metric_a": "occ_asg", "metric_b": "occ_cpc", "spearman": rho_asg_cpc},
        {"metric_a": "occ_ent", "metric_b": "occ_soft", "spearman": spearman(df["occ_ent"], df["occ_soft"])},
        {"metric_a": "occ_ent", "metric_b": "f_min", "spearman": rho_ent_f},
        {"metric_a": "occ_asg", "metric_b": "f_min", "spearman": spearman(df["occ_asg"], df["f_min"])},
        {"metric_a": "occ_ent", "metric_b": "p_norm", "spearman": rho_ent_p},
        {"metric_a": "occ_asg", "metric_b": "p_norm", "spearman": spearman(df["occ_asg"], df["p_norm"])},
    ]
    for row in agreement_rows:
        row["n"] = int(len(df))
    agreement = pd.DataFrame(agreement_rows)

    counts_ent = count_cells(df["quadrant_ent"], df["size"]).assign(occ_axis="entity_cluster")
    counts_asg = count_cells(df["quadrant_asg"], df["size"]).assign(occ_axis="assignee")
    counts_cpc = count_cells(df["quadrant_cpc"], df["size"]).assign(occ_axis="cpc")
    counts = pd.concat([counts_ent, counts_asg, counts_cpc], ignore_index=True)

    pooled = {q: int((df["quadrant"] == q).sum()) for q in CORNERS}
    empty = [q for q, n in pooled.items() if n == 0]
    short = [q for q, n in pooled.items() if n < cfg.MIN_CELL_CANDIDATES]
    two_versions = bool(np.isfinite(rho_ent_asg) and rho_ent_asg < 0.3)
    gates = {
        "cells_nonempty": len(empty) == 0,
        "cells_min_n": len(short) == 0,
        "occ_soft_collapsed": rho_soft_med < 1e-12,
        "occ_ent_fmin_abs_spearman": None if not np.isfinite(rho_ent_f) else float(abs(rho_ent_f)),
        "promote_assignee_for_fmin_corr": reason.startswith("|spearman"),
        "report_both_occ_versions": two_versions,
        "all_pass": len(empty) == 0 and len(short) == 0,
    }

    out_cols = [
        "scenario_id",
        "groups",
        "names",
        "size",
        "occ_ent",
        "occ_asg",
        "occ_cpc",
        "occ_soft",
        "p_norm",
        "f_min",
        "occ_tercile",
        "p_tercile",
        "quadrant",
        "occ_axis_used",
        "quadrant_ent",
        "quadrant_asg",
        "quadrant_cpc",
    ]
    df[out_cols].to_csv(cfg.OUT / "70_quadrants.csv", index=False)
    counts.to_csv(cfg.OUT / "70_quadrant_counts.csv", index=False)
    agreement.to_csv(cfg.OUT / "70_occ_agreement.csv", index=False)
    write_json(
        cfg.OUT / "70_manifest.json",
        {
            "n_scenarios": int(len(df)),
            "k": int(resp.shape[1]),
            "n_clusters": int(u_ent.shape[1]),
            "n_assignees_used": int(len(asg)),
            "occ_primary_config": cfg.OCC_PRIMARY,
            "occ_axis_used": primary,
            "occ_axis_reason": reason,
            "rho_occ_ent_f_min": None if not np.isfinite(rho_ent_f) else float(rho_ent_f),
            "rho_occ_ent_asg": None if not np.isfinite(rho_ent_asg) else float(rho_ent_asg),
            "occ_soft_max": rho_soft_max,
            "occ_soft_median": rho_soft_med,
            "pooled_counts": pooled,
            "empty_cells": empty,
            "short_cells": short,
            "min_cell_candidates": cfg.MIN_CELL_CANDIDATES,
            "note_min_cell": "MIN_CELL=10 은 K≈15·후보 ~1925 규모. K=6·50후보면 독립 시 칸당 ~6.",
            "uses_mapping_ids_for_occ_ent_only": True,
            "pair_unit_still_surface_entities": True,
            "gates": gates,
        },
    )
    draw_figure(df, occ_col, primary)
    print(
        f"[70] axis={primary} ({reason}) occ_ent~f_min ρ={rho_ent_f:.3f} "
        f"occ_ent~asg ρ={rho_ent_asg:.3f} occ_soft_max={rho_soft_max:.2e}",
        flush=True,
    )
    for q in CORNERS:
        n = pooled[q]
        preview = ", ".join(df.loc[df["quadrant"] == q, "names"].head(3).str.replace("|", "+", regex=False))
        print(f"[70]   {q} n={n}  {preview}", flush=True)
    if empty:
        print(f"[70] GATE: empty cells {empty}", flush=True)
    if short:
        print(f"[70] GATE: cells < {cfg.MIN_CELL_CANDIDATES}: {short} {pooled}", flush=True)
    print(f"[70] wrote {cfg.OUT / '70_quadrants.csv'} and {cfg.FIG / '70_quadrants.png'}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
