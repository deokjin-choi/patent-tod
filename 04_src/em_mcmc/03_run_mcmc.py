"""MCMC in two small pieces that the note actually needs.

1) Admixture (STRUCTURE analogue): each patent is a mix of the three origins
   (power / footprint / latency). Gibbs assigns every keyword token an origin.
2) Constraint + feasible cells: Beta posterior on each hypothesized ban,
   then sample cells that survive the drawn bans (tiny 8-cell space, enumerated).
"""

from __future__ import annotations

import numpy as np

from config import (
    ADMIXTURE_ALPHA,
    ADMIXTURE_BETA,
    CONSTRAINT_A,
    CONSTRAINT_B,
    CONSTRAINTS,
    MCMC_BURNIN,
    MCMC_ITERS,
    MCMC_THIN,
    OUT,
    PATENTS,
    SEED,
)
from lib import (
    all_cells,
    axis_order,
    cell_name,
    ensure_out,
    load_dictionary,
    load_json,
    read_csv,
    vocab_entries,
    write_csv,
)


def expand_tokens(X: np.ndarray) -> list[list[int]]:
    """Document -> list of word indices, repeated by count."""
    docs = []
    for i in range(X.shape[0]):
        toks = []
        for w, c in enumerate(X[i]):
            c = int(c)
            if c:
                toks.extend([w] * c)
        docs.append(toks)
    return docs


def run_admixture(X, vocab, rng):
    """Uncollapsed Gibbs for a 3-origin admixture. Origins = the three axes."""
    origins = []
    for item in vocab:
        if item["axis"] not in origins:
            origins.append(item["axis"])
    k = len(origins)
    origin_of_word = np.array([origins.index(item["axis"]) for item in vocab], dtype=int)
    n, v = X.shape
    docs = expand_tokens(X)

    # z[i][t] origin of token t in doc i. Seed by dictionary axis of that word.
    z = []
    ndk = np.zeros((n, k), dtype=int)  # doc-origin counts
    nkw = np.zeros((k, v), dtype=int)  # origin-word counts
    nk = np.zeros(k, dtype=int)
    for i, toks in enumerate(docs):
        zi = []
        for w in toks:
            o = int(origin_of_word[w])
            zi.append(o)
            ndk[i, o] += 1
            nkw[o, w] += 1
            nk[o] += 1
        z.append(zi)

    alpha = ADMIXTURE_ALPHA
    beta = ADMIXTURE_BETA
    trace = []
    q_accum = np.zeros((n, k))
    phi_accum = np.zeros((k, v))
    n_keep = 0

    for it in range(MCMC_ITERS):
        for i, toks in enumerate(docs):
            for t, w in enumerate(toks):
                o = z[i][t]
                ndk[i, o] -= 1
                nkw[o, w] -= 1
                nk[o] -= 1
                logp = np.log(ndk[i] + alpha) + np.log(nkw[:, w] + beta) - np.log(nk + beta * v)
                logp = logp - logp.max()
                p = np.exp(logp)
                p = p / p.sum()
                o2 = int(rng.choice(k, p=p))
                z[i][t] = o2
                ndk[i, o2] += 1
                nkw[o2, w] += 1
                nk[o2] += 1
        if it >= MCMC_BURNIN and (it - MCMC_BURNIN) % MCMC_THIN == 0:
            q = ndk + alpha
            q = q / q.sum(axis=1, keepdims=True)
            phi = nkw + beta
            phi = phi / phi.sum(axis=1, keepdims=True)
            q_accum += q
            phi_accum += phi
            n_keep += 1
            trace.append(
                {
                    "iter": it,
                    "mean_q_power": round(float(q[:, origins.index("power")].mean()), 4)
                    if "power" in origins
                    else 0.0,
                    "mean_q_footprint": round(float(q[:, origins.index("footprint")].mean()), 4)
                    if "footprint" in origins
                    else 0.0,
                    "mean_q_latency": round(float(q[:, origins.index("latency")].mean()), 4)
                    if "latency" in origins
                    else 0.0,
                    "n_tokens": int(nk.sum()),
                }
            )

    q_mean = q_accum / max(n_keep, 1)
    phi_mean = phi_accum / max(n_keep, 1)
    return origins, q_mean, phi_mean, trace, ndk


def pair_counts(X, vocab, pair, axes):
    """How many patents have at least one phrase from each of the two levels."""
    a_idx = [j for j, v in enumerate(vocab) if v["axis"] == pair["axis_a"] and v["level"] == pair["level_a"]]
    b_idx = [j for j, v in enumerate(vocab) if v["axis"] == pair["axis_b"] and v["level"] == pair["level_b"]]
    has_a = X[:, a_idx].sum(axis=1) > 0 if a_idx else np.zeros(X.shape[0], dtype=bool)
    has_b = X[:, b_idx].sum(axis=1) > 0 if b_idx else np.zeros(X.shape[0], dtype=bool)
    both = int(np.sum(has_a & has_b))
    n_a = int(np.sum(has_a))
    n_b = int(np.sum(has_b))
    n = X.shape[0]
    return n, n_a, n_b, both


def cell_violates(cell, axes, pair) -> bool:
    ia = axes.index(pair["axis_a"])
    ib = axes.index(pair["axis_b"])
    return cell[ia] == pair["level_a"] and cell[ib] == pair["level_b"]


def run_constraints(X, vocab, d, rng):
    axes = axis_order(d)
    cells = all_cells(d)
    names = [cell_name(axes, c) for c in cells]
    cons = load_json(CONSTRAINTS)
    pi = np.load(OUT / "02_em_pi.npy") if (OUT / "02_em_pi.npy").exists() else np.ones(len(cells)) / len(cells)

    pair_rows = []
    posteriors = []
    for pair in cons["pairs"]:
        n, n_a, n_b, both = pair_counts(X, vocab, pair, axes)
        # p = P(a patent shows both levels). Posterior Beta(a+both, b+n-both).
        a_post = CONSTRAINT_A + both
        b_post = CONSTRAINT_B + (n - both)
        draws = rng.beta(a_post, b_post, size=2000)
        # 'forbidden' if co-occurrence rate is below a small cutoff
        p_forb = float(np.mean(draws < 0.01))
        pair_rows.append(
            {
                "id": pair["id"],
                "axis_a": pair["axis_a"],
                "level_a": pair["level_a"],
                "axis_b": pair["axis_b"],
                "level_b": pair["level_b"],
                "n": n,
                "n_a": n_a,
                "n_b": n_b,
                "n_both": both,
                "beta_a": round(a_post, 3),
                "beta_b": round(b_post, 3),
                "p_mean": round(float(a_post / (a_post + b_post)), 4),
                "p_forbidden_rate_lt_0.01": round(p_forb, 4),
                "rationale": pair.get("rationale") or "",
            }
        )
        posteriors.append((pair, a_post, b_post, p_forb))

    # Sample: draw which bans fire, then sample a cell from EM pi restricted to survivors.
    samples = []
    n_samp = 400
    for s in range(n_samp):
        active = []
        for pair, a_post, b_post, _ in posteriors:
            p = rng.beta(a_post, b_post)
            fire = p < 0.01
            if fire:
                active.append(pair["id"])
        mask = np.ones(len(cells), dtype=bool)
        for pair, *_ in posteriors:
            if pair["id"] in active:
                for ki, cell in enumerate(cells):
                    if cell_violates(cell, axes, pair):
                        mask[ki] = False
        w = np.where(mask, pi, 0.0)
        if w.sum() <= 0:
            w = mask.astype(float)
        w = w / w.sum()
        ki = int(rng.choice(len(cells), p=w))
        samples.append(
            {
                "draw": s,
                "cell": names[ki],
                "n_active_bans": len(active),
                "active_bans": "|".join(active) if active else "",
            }
        )
    return pair_rows, samples, names, cells, axes


def main() -> None:
    ensure_out()
    rng = np.random.default_rng(SEED)
    d = load_dictionary()
    vocab = vocab_entries(d)
    X = np.load(OUT / "01_counts.npy")
    patents = read_csv(PATENTS)

    origins, q_mean, phi_mean, trace, ndk = run_admixture(X, vocab, rng)
    q_rows = []
    for i, row in enumerate(patents):
        rec = {
            "display_key": row["display_key"],
            "n_tokens": int(X[i].sum()),
            "top_origin": origins[int(q_mean[i].argmax())] if X[i].sum() else "",
        }
        for oi, o in enumerate(origins):
            rec[f"q_{o}"] = round(float(q_mean[i, oi]), 4)
        q_rows.append(rec)
    write_csv(
        OUT / "03_admixture_q.csv",
        ["display_key", "n_tokens", "top_origin", *[f"q_{o}" for o in origins]],
        q_rows,
    )
    phi_rows = []
    for oi, o in enumerate(origins):
        for j, item in enumerate(vocab):
            phi_rows.append(
                {
                    "origin": o,
                    "kw_id": f"kw_{j:03d}",
                    "phrase": item["phrase"],
                    "dict_axis": item["axis"],
                    "prob": round(float(phi_mean[oi, j]), 6),
                }
            )
    write_csv(OUT / "03_admixture_phi.csv", ["origin", "kw_id", "phrase", "dict_axis", "prob"], phi_rows)
    write_csv(OUT / "03_admixture_trace.csv", list(trace[0].keys()) if trace else ["iter"], trace)

    pair_rows, samples, names, cells, axes = run_constraints(X, vocab, d, rng)
    write_csv(OUT / "03_constraint_posterior.csv", list(pair_rows[0].keys()), pair_rows)
    write_csv(OUT / "03_feasible_samples.csv", ["draw", "cell", "n_active_bans", "active_bans"], samples)

    from collections import Counter

    freq = Counter(s["cell"] for s in samples)
    freq_rows = [{"cell": name, "mcmc_count": freq.get(name, 0), "mcmc_share": round(freq.get(name, 0) / len(samples), 4)} for name in names]
    write_csv(OUT / "03_cell_sample_freq.csv", ["cell", "mcmc_count", "mcmc_share"], freq_rows)

    has_tok = X.sum(axis=1) > 0
    print("admixture mean q (all)", {o: round(float(q_mean[:, i].mean()), 3) for i, o in enumerate(origins)})
    print("admixture mean q (nonempty)", {o: round(float(q_mean[has_tok, i].mean()), 3) for i, o in enumerate(origins)})
    print("constraint pairs")
    for r in pair_rows:
        print(f"  {r['id']}: both={r['n_both']} p_mean={r['p_mean']} P(rate<0.01)={r['p_forbidden_rate_lt_0.01']}")
    print("feasible-sample top cells", freq.most_common(4))


if __name__ == "__main__":
    main()
