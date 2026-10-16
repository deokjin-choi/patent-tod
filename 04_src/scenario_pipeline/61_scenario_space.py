"""Stage 6-b — enumerate group subsets and score P(s).

Uses frozen pair(g1,g2) from 6-a and π̂ from stage 4. No new learning.
occ scatter waits for stage 7. Contract: docs/02_stage_specs.md 6-b.
"""

from __future__ import annotations

import math
import sys
from itertools import combinations
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager

import config as cfg
from lib import ensure_out, write_json


def _font():
    path = Path("/usr/share/fonts/truetype/unfonts-core/UnDotum.ttf")
    if path.exists():
        font_manager.fontManager.addfont(str(path))
        return font_manager.FontProperties(fname=str(path))
    return None


def _abbr(name: str, g: int) -> str:
    raw = str(name)
    if "(" in raw and raw.rfind(")") > raw.find("("):
        return raw[raw.find("(") + 1 : raw.rfind(")")]
    return f"G{g}"


def load_inputs() -> tuple[int, dict[int, float], dict[tuple[int, int], float], dict[int, str]]:
    pair_path = cfg.OUT / "60_pair_scores.csv"
    trend_path = cfg.OUT / "40_trend.csv"
    if not pair_path.exists():
        raise SystemExit("out/60_pair_scores.csv 가 없다. 먼저 60_pair_scores.py 를 실행하라.")
    if not trend_path.exists():
        raise SystemExit("out/40_trend.csv 가 없다. 먼저 40_group_time.py 를 실행하라.")
    pairs_df = pd.read_csv(pair_path)
    trend = pd.read_csv(trend_path)
    k = int(len(trend))
    pi = {int(row.group): float(row.pi_hat_next) for row in trend.itertuples(index=False)}
    names = {int(row.group): _abbr(row.name, int(row.group)) for row in trend.itertuples(index=False)}
    pair: dict[tuple[int, int], float] = {}
    for row in pairs_df.itertuples(index=False):
        a, b = int(row.g1), int(row.g2)
        pair[(min(a, b), max(a, b))] = float(row.pair_prob)
    expected_pairs = math.comb(k, 2)
    if len(pair) != expected_pairs:
        raise SystemExit(f"쌍 점수 {len(pair)}개, 기대 {expected_pairs}개 (K={k}).")
    missing = [g for g in range(k) if g not in pi]
    if missing:
        raise SystemExit(f"pi_hat_next 결측 그룹: {missing}")
    return k, pi, pair, names


def scenario_id(groups: tuple[int, ...]) -> str:
    return f"s{len(groups)}_" + "-".join(str(g) for g in groups)


def pair_values(groups: tuple[int, ...], pair: dict[tuple[int, int], float]) -> list[float]:
    return [pair[(a, b)] for a, b in combinations(groups, 2)]


def enumerate_scenarios(
    k: int,
    pi: dict[int, float],
    pair: dict[tuple[int, int], float],
    names: dict[int, str],
    beta: float,
) -> pd.DataFrame:
    rows = []
    for size in cfg.SCENARIO_SIZES:
        for groups in combinations(range(k), size):
            vals = pair_values(groups, pair)
            p_trend = float(np.prod([pi[g] for g in groups]))
            f_min = float(min(vals))
            f_mean = float(np.mean(vals))
            p_unnorm = p_trend * (f_min**beta)
            rows.append(
                {
                    "scenario_id": scenario_id(groups),
                    "groups": "|".join(str(g) for g in groups),
                    "names": "|".join(names[g] for g in groups),
                    "size": int(size),
                    "p_trend": p_trend,
                    "f_min": f_min,
                    "f_mean": f_mean,
                    "p_unnorm": p_unnorm,
                    "beta": float(beta),
                }
            )
    table = pd.DataFrame(rows)
    table["p_norm"] = np.nan
    table["rank_in_size"] = np.nan
    for size in cfg.SCENARIO_SIZES:
        mask = table["size"] == size
        mass = float(table.loc[mask, "p_unnorm"].sum())
        if mass <= 0:
            raise SystemExit(f"크기 {size} 의 p_unnorm 합이 0이다.")
        table.loc[mask, "p_norm"] = table.loc[mask, "p_unnorm"] / mass
        order = table.loc[mask, "p_unnorm"].rank(ascending=False, method="first").astype(int)
        table.loc[mask, "rank_in_size"] = order
    table["rank_in_size"] = table["rank_in_size"].astype(int)
    return table.sort_values(["size", "rank_in_size"]).reset_index(drop=True)


def expected_counts(k: int) -> dict[int, int]:
    return {int(size): int(math.comb(k, size)) for size in cfg.SCENARIO_SIZES}


def _jaccard(a: set[str], b: set[str]) -> float:
    union = len(a | b)
    return len(a & b) / union if union else 1.0


def _spearman(order_a: pd.Series, order_b: pd.Series) -> float:
    aligned = pd.concat([order_a, order_b], axis=1).dropna()
    if len(aligned) < 2:
        return float("nan")
    return float(aligned.iloc[:, 0].corr(aligned.iloc[:, 1], method="spearman"))


def beta_overlap(k: int, pi: dict[int, float], pair: dict[tuple[int, int], float], names: dict[int, str]) -> dict:
    ranked: dict[float, pd.DataFrame] = {}
    for beta in cfg.BETA_SENSITIVITY:
        ranked[float(beta)] = enumerate_scenarios(k, pi, pair, names, float(beta))
    top_n = 20
    top_k = 5
    overlap = {"top_n": top_n, "top_k_rank": top_k, "per_size": {}, "global_punorm": {}}
    for size in cfg.SCENARIO_SIZES:
        n = int(math.comb(k, size))
        sets_n, sets_k, ranks = {}, {}, {}
        for beta, table in ranked.items():
            sub = table[table["size"] == size].set_index("scenario_id")
            take_n = min(top_n, n)
            sets_n[str(beta)] = set(sub.nsmallest(take_n, "rank_in_size").index)
            sets_k[str(beta)] = set(sub.nsmallest(min(top_k, n), "rank_in_size").index)
            ranks[str(beta)] = sub["rank_in_size"]
        keys = list(sets_n)
        overlap["per_size"][str(size)] = {
            "n": n,
            "top20_is_full_set": n <= top_n,
            "jaccard_top20": {f"{a}∩{b}": _jaccard(sets_n[a], sets_n[b]) for i, a in enumerate(keys) for b in keys[i + 1 :]},
            "jaccard_top5": {f"{a}∩{b}": _jaccard(sets_k[a], sets_k[b]) for i, a in enumerate(keys) for b in keys[i + 1 :]},
            "spearman_rank": {f"{a}∩{b}": _spearman(ranks[a], ranks[b]) for i, a in enumerate(keys) for b in keys[i + 1 :]},
            "n_shared_top5_all_betas": int(len(set.intersection(*sets_k.values()))),
        }
    global_sets = {str(beta): set(table.nlargest(top_n, "p_unnorm")["scenario_id"]) for beta, table in ranked.items()}
    gkeys = list(global_sets)
    overlap["global_punorm"] = {
        "note": "p_unnorm 상위는 크기 2가 우세하다. 본순위는 size별 p_norm.",
        "jaccard": {f"{a}∩{b}": _jaccard(global_sets[a], global_sets[b]) for i, a in enumerate(gkeys) for b in gkeys[i + 1 :]},
        "n_shared_all_betas": int(len(set.intersection(*global_sets.values()))),
    }
    overlap["base_beta"] = float(cfg.BETA)
    return overlap


def draw_scatter(table: pd.DataFrame) -> None:
    fp = _font()
    fig, axes = plt.subplots(1, len(cfg.SCENARIO_SIZES), figsize=(12.6, 4.2), dpi=140, sharey=False)
    fig.patch.set_facecolor("#F6F3EE")
    colors = ["#2C5F5D", "#8B6914", "#6B3A3A"]
    for ax, size, color in zip(axes, cfg.SCENARIO_SIZES, colors):
        sub = table[table["size"] == size]
        ax.scatter(sub["f_min"], sub["p_trend"], c=color, s=36 + 80 * sub["p_norm"], alpha=0.85, edgecolors="#1C1917", linewidths=0.4)
        top = sub.nsmallest(3, "rank_in_size")
        for row in top.itertuples(index=False):
            ax.annotate(
                row.names.replace("|", "+"),
                (row.f_min, row.p_trend),
                textcoords="offset points",
                xytext=(4, 4),
                fontsize=6.5,
                fontproperties=fp,
            )
        ax.set_title(f"|s|={size}  (n={len(sub)})", fontproperties=fp, fontsize=11)
        ax.set_xlabel(r"$F_{\min}$ (관측 유사도)", fontproperties=fp, fontsize=9)
        ax.set_facecolor("#F6F3EE")
    axes[0].set_ylabel(r"$P_{\mathrm{trend}}$", fontproperties=fp, fontsize=10)
    fig.suptitle(
        r"시나리오 공간  —  $x=F_{\min}$, $y=P_{\mathrm{trend}}$  ·  occ는 단계 7",
        fontproperties=fp,
        fontsize=12,
        y=1.02,
    )
    fig.tight_layout()
    cfg.FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(cfg.FIG / "61_scenario_scatter.png", facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    ensure_out()
    if cfg.SEARCH_MODE != "enumerate":
        raise SystemExit("SEARCH_MODE 는 enumerate 이다. |s|>=5 확장 전에 mcmc 를 켜지 마라.")
    k, pi, pair, names = load_inputs()
    expect = expected_counts(k)
    print(f"[61] K={k} sizes={list(cfg.SCENARIO_SIZES)} expected={expect} beta={cfg.BETA}", flush=True)

    table = enumerate_scenarios(k, pi, pair, names, float(cfg.BETA))
    n_by_size = {int(s): int((table["size"] == s).sum()) for s in cfg.SCENARIO_SIZES}
    if n_by_size != expect:
        raise SystemExit(f"후보 수 불일치 observed={n_by_size} expected={expect}")

    out_cols = [
        "scenario_id",
        "groups",
        "names",
        "size",
        "p_trend",
        "f_min",
        "f_mean",
        "p_unnorm",
        "p_norm",
        "rank_in_size",
    ]
    table[out_cols].to_csv(cfg.OUT / "61_scenarios.csv", index=False)
    overlap = beta_overlap(k, pi, pair, names)
    z_size = {str(s): float(table.loc[table["size"] == s, "p_unnorm"].sum()) for s in cfg.SCENARIO_SIZES}
    write_json(
        cfg.OUT / "61_space_manifest.json",
        {
            "k": k,
            "n_scenarios": int(len(table)),
            "n_by_size": n_by_size,
            "expected_by_size": expect,
            "beta": float(cfg.BETA),
            "beta_sensitivity": list(cfg.BETA_SENSITIVITY),
            "search_mode": cfg.SEARCH_MODE,
            "mcmc": False,
            "norm_by_size": z_size,
            "f_min_range": [float(table["f_min"].min()), float(table["f_min"].max())],
            "pair_prob_is_observed_similarity": True,
            "occ_deferred_to_stage_7": True,
            "uses_mapping_ids": False,
            "beta_overlap": overlap,
            "gates": {
                "n_matches_enumeration": n_by_size == expect,
                "all_pass": n_by_size == expect,
            },
        },
    )
    draw_scatter(table)
    for size in cfg.SCENARIO_SIZES:
        top = table[table["size"] == size].nsmallest(3, "rank_in_size")
        preview = ", ".join(f"{r.names}({r.p_norm:.3f})" for r in top.itertuples(index=False))
        print(f"[61] size {size} top3: {preview}", flush=True)
    print(
        f"[61] wrote {cfg.OUT / '61_scenarios.csv'} and {cfg.FIG / '61_scenario_scatter.png'}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
