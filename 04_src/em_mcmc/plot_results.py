"""Save result charts under figures/. Reads out/ CSVs only. Does not rerun EM/MCMC."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import beta as beta_dist

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"
FIG = ROOT / "figures"
FIG.mkdir(parents=True, exist_ok=True)

plt.rcParams.update(
    {
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.grid": True,
        "grid.alpha": 0.28,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "font.size": 10,
        "axes.titlesize": 11,
        "figure.dpi": 120,
    }
)

SHORT = {
    "power=low|footprint=compact|latency=realtime": "low | compact | realtime",
    "power=low|footprint=compact|latency=batch": "low | compact | batch",
    "power=low|footprint=full|latency=realtime": "low | full | realtime",
    "power=low|footprint=full|latency=batch": "low | full | batch",
    "power=high|footprint=compact|latency=realtime": "high | compact | realtime",
    "power=high|footprint=compact|latency=batch": "high | compact | batch",
    "power=high|footprint=full|latency=realtime": "high | full | realtime",
    "power=high|footprint=full|latency=batch": "high | full | batch",
}
CELL_ORDER = list(SHORT.keys())


def read_csv(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def save(fig: plt.Figure, name: str) -> None:
    fig.tight_layout()
    dest = FIG / name
    fig.savefig(dest, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("wrote", dest.name)


def fig_keyword_hits():
    rows = read_csv("01_feature_matrix.csv")
    hits = np.array([int(r["n_keyword_hits"]) for r in rows])
    n = len(hits)
    n0 = int((hits == 0).sum())
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.6))

    axes[0].bar(["no keyword", "≥1 keyword"], [n0, n - n0], color=["#9aa0a6", "#3d6b99"])
    axes[0].set_ylabel("patents")
    axes[0].set_title(f"Dictionary hit rate  ({n0}/{n} unmapped)")
    for i, v in enumerate([n0, n - n0]):
        axes[0].text(i, v + 4, str(v), ha="center")

    pos = hits[hits > 0]
    bins = np.arange(0.5, max(pos.max() if len(pos) else 1, 1) + 1.5, 1)
    axes[1].hist(pos, bins=bins, color="#3d6b99", edgecolor="white")
    axes[1].set_xlabel("keyword token count (hit patents only)")
    axes[1].set_ylabel("patents")
    axes[1].set_title("How many tokens on the 89 that hit")
    save(fig, "01_keyword_hits.png")


def fig_vocab():
    rows = read_csv("01_vocab.csv")
    by_origin: dict[str, int] = defaultdict(int)
    live = []
    for r in rows:
        d = int(r["docs_with_term"])
        by_origin[r["origin"]] += d
        if d > 0:
            live.append(r)
    live.sort(key=lambda r: int(r["docs_with_term"]))

    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.4), gridspec_kw={"width_ratios": [1.1, 1.4]})
    origins = ["power:low", "power:high", "footprint:compact", "footprint:full", "latency:realtime", "latency:batch"]
    colors = ["#4c8c4a", "#c0392b", "#3d6b99", "#8e5a2b", "#7b4ea3", "#7f8c8d"]
    axes[0].barh(origins, [by_origin[o] for o in origins], color=colors)
    axes[0].set_xlabel("document hits (a doc can hit several phrases)")
    axes[0].set_title("Which dictionary buckets fired")

    phrases = [r["phrase"] for r in live]
    vals = [int(r["docs_with_term"]) for r in live]
    axes[1].barh(phrases, vals, color="#3d6b99")
    axes[1].set_xlabel("patents with this phrase")
    axes[1].set_title("Phrases that actually appeared")
    axes[1].tick_params(axis="y", labelsize=8)
    save(fig, "01_vocab_hits.png")


def fig_em_loglik():
    rows = read_csv("02_em_loglik.csv")
    it = [int(r["iter"]) for r in rows]
    ll = [float(r["loglik"]) for r in rows]
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    ax.plot(it, ll, color="#3d6b99", marker="o", markersize=3)
    ax.set_xlabel("EM iteration")
    ax.set_ylabel("log-likelihood (mapped docs)")
    ax.set_title(f"EM rose then flattened  ({ll[0]:.0f} → {ll[-1]:.0f})")
    save(fig, "02_em_loglik.png")


def fig_em_occupancy():
    rows = read_csv("02_em_occupancy.csv")
    by = {r["cell"]: r for r in rows}
    labels = [SHORT[c] for c in CELL_ORDER]
    hard = [int(by[c]["hard_count"]) for c in CELL_ORDER]
    exp = [float(by[c]["expected_occupancy_nonempty"]) for c in CELL_ORDER]
    y = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    ax.barh(y + 0.18, hard, height=0.35, color="#3d6b99", label="hard (argmax)")
    ax.barh(y - 0.18, exp, height=0.35, color="#d4a017", label="expected occupancy")
    ax.set_yticks(y, labels)
    ax.set_xlabel("patents with ≥1 keyword  (n=89)")
    ax.set_title("EM cell placement — unmapped 311 excluded")
    ax.legend(frameon=False)
    save(fig, "02_em_occupancy.png")


def fig_em_confidence():
    rows = read_csv("02_em_responsibilities.csv")
    mapped = [r for r in rows if r["hard_cell"] != "unmapped"]
    p = np.array([float(r["hard_prob"]) for r in mapped])
    h = np.array([float(r["entropy"]) for r in mapped])
    fig, axes = plt.subplots(1, 2, figsize=(8.8, 3.5))
    axes[0].hist(p, bins=np.linspace(0, 1, 11), color="#3d6b99", edgecolor="white")
    axes[0].set_xlabel("P(best cell)")
    axes[0].set_ylabel("mapped patents")
    axes[0].set_title("How sure is the hard map?")
    axes[1].hist(h, bins=12, color="#7b4ea3", edgecolor="white")
    axes[1].axvline(np.log(8), color="#c0392b", ls="--", lw=1, label="uniform (ln 8)")
    axes[1].set_xlabel("entropy of r_i")
    axes[1].set_title("Spread across the 8 cells")
    axes[1].legend(frameon=False, fontsize=8)
    save(fig, "02_em_confidence.png")


def fig_admixture():
    rows = read_csv("03_admixture_q.csv")
    m = [r for r in rows if int(r["n_tokens"]) > 0]
    qp = np.array([float(r["q_power"]) for r in m])
    qf = np.array([float(r["q_footprint"]) for r in m])
    ql = np.array([float(r["q_latency"]) for r in m])
    fig, axes = plt.subplots(1, 2, figsize=(8.8, 3.7))
    axes[0].bar(
        ["power", "footprint", "latency"],
        [qp.mean(), qf.mean(), ql.mean()],
        color=["#4c8c4a", "#3d6b99", "#7b4ea3"],
    )
    axes[0].set_ylim(0, 0.55)
    axes[0].set_ylabel("mean q  (89 patents with tokens)")
    axes[0].set_title("Average mix of technical origins")
    sc = axes[1].scatter(qp, qf, c=ql, cmap="viridis", s=28, alpha=0.75, edgecolors="none")
    axes[1].plot([0, 1], [1, 0], color="#999", lw=0.8, ls="--")
    axes[1].set_xlabel("q_power")
    axes[1].set_ylabel("q_footprint")
    axes[1].set_xlim(-0.02, 1.02)
    axes[1].set_ylim(-0.02, 1.02)
    axes[1].set_title("Each point is a patent  (color = q_latency)")
    fig.colorbar(sc, ax=axes[1], fraction=0.046, pad=0.04)
    save(fig, "03_admixture_q.png")


def fig_admixture_trace():
    rows = read_csv("03_admixture_trace.csv")
    it = [int(r["iter"]) for r in rows]
    fig, ax = plt.subplots(figsize=(6.6, 3.4))
    ax.plot(it, [float(r["mean_q_power"]) for r in rows], label="power", color="#4c8c4a")
    ax.plot(it, [float(r["mean_q_footprint"]) for r in rows], label="footprint", color="#3d6b99")
    ax.plot(it, [float(r["mean_q_latency"]) for r in rows], label="latency", color="#7b4ea3")
    ax.axhline(1 / 3, color="#999", ls=":", lw=1)
    ax.set_xlabel("Gibbs iteration (after burn-in, thinned)")
    ax.set_ylabel("mean q across patents")
    ax.set_ylim(0.25, 0.42)
    ax.set_title("Admixture chain is walking, not collapsing")
    ax.legend(frameon=False, ncol=3)
    save(fig, "03_admixture_trace.png")


def fig_constraints():
    rows = read_csv("03_constraint_posterior.csv")
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.7))
    labels = [r["id"].replace("_", "\n") for r in rows]
    x = np.arange(len(rows))
    w = 0.25
    axes[0].bar(x - w, [int(r["n_a"]) for r in rows], w, label="n with A", color="#4c8c4a")
    axes[0].bar(x, [int(r["n_b"]) for r in rows], w, label="n with B", color="#3d6b99")
    axes[0].bar(x + w, [int(r["n_both"]) for r in rows], w, label="n both", color="#c0392b")
    axes[0].set_xticks(x, labels, fontsize=8)
    axes[0].set_ylabel("patents in the 400")
    axes[0].set_title("Co-occurrence evidence")
    axes[0].legend(frameon=False, fontsize=8)

    xs = np.linspace(0, 0.04, 400)
    for r, c in zip(rows, ["#c0392b", "#8e5a2b"]):
        a, b = float(r["beta_a"]), float(r["beta_b"])
        axes[1].plot(xs, beta_dist.pdf(xs, a, b), color=c, label=r["id"][:22])
    axes[1].axvline(0.01, color="#333", ls="--", lw=1, label="ban cutoff 0.01")
    axes[1].set_xlabel("p = P(a patent shows both levels)")
    axes[1].set_ylabel("posterior density")
    axes[1].set_title("Beta posterior on co-occurrence rate")
    axes[1].legend(frameon=False, fontsize=7)
    save(fig, "03_constraint_posterior.png")


def fig_em_vs_mcmc():
    em = {r["cell"]: float(r["expected_occupancy_nonempty"]) for r in read_csv("02_em_occupancy.csv")}
    em_sum = sum(em.values()) or 1.0
    mc = {r["cell"]: float(r["mcmc_share"]) for r in read_csv("03_cell_sample_freq.csv")}
    labels = [SHORT[c] for c in CELL_ORDER]
    em_p = [em[c] / em_sum for c in CELL_ORDER]
    mc_p = [mc[c] for c in CELL_ORDER]
    y = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(7.8, 4.5))
    ax.barh(y + 0.18, em_p, height=0.35, color="#d4a017", label="EM expected share (n=89)")
    ax.barh(y - 0.18, mc_p, height=0.35, color="#c0392b", label="MCMC feasible-sample share")
    ax.set_yticks(y, labels)
    ax.set_xlabel("share of mass")
    ax.set_xlim(0, 0.38)
    ax.set_title("Where mass goes once hypothesized bans can fire")
    ax.legend(frameon=False, loc="lower right")
    save(fig, "03_em_vs_mcmc.png")


def fig_ban_draws():
    rows = read_csv("03_feasible_samples.csv")
    cnt = Counter(int(r["n_active_bans"]) for r in rows)
    xs = [0, 1, 2]
    fig, ax = plt.subplots(figsize=(5.4, 3.4))
    ax.bar(xs, [cnt.get(i, 0) for i in xs], color="#3d6b99")
    ax.set_xticks(xs)
    ax.set_xlabel("how many of the 2 hypothesized bans fired")
    ax.set_ylabel("MCMC draws (of 400)")
    ax.set_title("Bans are on in most draws")
    save(fig, "03_ban_draws.png")


def fig_quality():
    rows = read_csv("04_quality.csv")
    labels = {
        "em_hard_nonempty": "EM hard\n(mapped)",
        "em_expected_nonempty": "EM expected\n(mapped)",
        "em_expected_all_incl_empty": "EM expected\n(+ empty)",
        "mcmc_feasible_samples": "MCMC\nfeasible",
    }
    names = [labels[r["source"]] for r in rows]
    x = np.arange(len(rows))
    fig, ax = plt.subplots(figsize=(7.6, 3.8))
    ax.bar(x - 0.25, [float(r["coverage"]) for r in rows], 0.24, label="Coverage", color="#3d6b99")
    ax.bar(x, [float(r["balance_norm_entropy"]) for r in rows], 0.24, label="Balance", color="#d4a017")
    ax.bar(
        x + 0.25,
        [float(r["diversity_mean_hamming"]) / 3.0 for r in rows],
        0.24,
        label="Diversity / 3",
        color="#7b4ea3",
    )
    ax.set_xticks(x, names)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("index (diversity scaled to 0–1)")
    ax.set_title("Same 8 cells, three ways of putting mass on them")
    ax.legend(frameon=False, ncol=3, loc="upper right")
    save(fig, "04_quality.png")


def fig_missing():
    rows = read_csv("04_missing_species.csv")
    r = rows[0]
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.5))
    axes[0].bar(
        ["observed\nsignatures", "Chao1\nestimate"],
        [int(r["s_obs"]), float(r["chao1"])],
        color=["#3d6b99", "#c0392b"],
    )
    axes[0].set_ylabel("keyword-pattern types")
    axes[0].set_title("Unseen combinations (open signature space)")
    axes[1].bar(
        ["singletons f1", "doubletons f2"],
        [int(r["f1_singletons"]), int(r["f2_doubletons"])],
        color=["#8e5a2b", "#7f8c8d"],
    )
    axes[1].set_title(f"Good-Turing P(new) = {float(r['good_turing_p_new']):.2f}")
    save(fig, "04_missing_species.png")


def main() -> None:
    fig_keyword_hits()
    fig_vocab()
    fig_em_loglik()
    fig_em_occupancy()
    fig_em_confidence()
    fig_admixture()
    fig_admixture_trace()
    fig_constraints()
    fig_em_vs_mcmc()
    fig_ban_draws()
    fig_quality()
    fig_missing()
    print("figures ->", FIG)


if __name__ == "__main__":
    main()
