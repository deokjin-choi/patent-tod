"""POC steps 1-3: corpus, title/abstract mapping, occupancy CSVs."""

from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from itertools import combinations, product
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "patents_slim.csv"
OUT = ROOT / "out"

UNKNOWN = "unknown"

# axis -> ordered levels -> regex (title+abstract, case-insensitive)
AXES: dict[str, dict[str, re.Pattern[str]]] = {
    "partition": {
        "horizontal": re.compile(
            r"horizontal\s+(?:federat|fl\b)|federated\s+horizontal|横向"
        ),
        "vertical": re.compile(
            r"vertical\s+(?:federat|fl\b)|federated\s+vertical|纵向|垂直联邦"
        ),
    },
    "aggregation": {
        "central": re.compile(
            r"central(?:ized)?\s+(?:server|aggregat)|parameter\s+server|"
            r"central\s+aggregat|cloud\s+aggregat"
        ),
        "hierarchical": re.compile(r"hierarch"),
        "decentralized": re.compile(
            r"decentral|peer[\s-]*to[\s-]*peer|\bp2p\b|gossip"
        ),
    },
    "privacy": {
        "dp": re.compile(r"differential\s+privac"),
        "crypto": re.compile(
            r"homomorphic|secure\s+multi[\s-]*party|secret\s+shar|\bsmc\b|"
            r"secure\s+aggregat"
        ),
        "tee": re.compile(r"trusted\s+execution|\btee\b|\bsgx\b"),
    },
    "location": {
        "device": re.compile(
            r"on[\s-]*device|end[\s-]*device|client\s+device|user\s+equipment|"
            r"\bues\b|mobile\s+terminal"
        ),
        "edge": re.compile(
            r"\bedge\s+(?:server|node|computing|device|train)|"
            r"\bmec\b|multi[\s-]*access\s+edge|mobile\s+edge"
        ),
        "cloud": re.compile(r"\bcloud\b"),
    },
}

AXIS_ORDER = ["partition", "aggregation", "privacy", "location"]


def parse_year(date_str: str) -> str:
    s = (date_str or "").strip()
    if len(s) >= 4 and s[:4].isdigit():
        return s[:4]
    return ""


def assign_level(text: str, levels: dict[str, re.Pattern[str]]) -> tuple[str, int, str]:
    """Return (primary_level, n_hits, all_hits_joined). Primary = earliest match."""
    hits: list[tuple[int, str]] = []
    for level, pat in levels.items():
        m = pat.search(text)
        if m:
            hits.append((m.start(), level))
    if not hits:
        return UNKNOWN, 0, ""
    hits.sort()
    unique = []
    for _, level in hits:
        if level not in unique:
            unique.append(level)
    return unique[0], len(unique), "|".join(unique)


def load_rows() -> list[dict[str, str]]:
    with SRC.open(encoding="utf-8", errors="replace", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    raw = load_rows()
    n = len(raw)

    # --- 1. corpus ---
    years = Counter()
    miss_abs = miss_date = miss_cpc = 0
    title_hit = 0
    for row in raw:
        y = parse_year(row.get("Earliest Priority Date") or "")
        years[y or "missing"] += 1
        if not (row.get("Abstract") or "").strip():
            miss_abs += 1
        if not y:
            miss_date += 1
        if not (row.get("CPC Classifications") or "").strip():
            miss_cpc += 1
        if (row.get("title_hit") or "") == "1":
            title_hit += 1

    corpus_rows = [{"table": "status", "item": "n_patents", "count": n}]
    corpus_rows += [
        {"table": "status", "item": k, "count": v}
        for k, v in [
            ("missing_abstract", miss_abs),
            ("missing_priority_date", miss_date),
            ("missing_cpc", miss_cpc),
            ("title_hit", title_hit),
            ("abstract_only_hit", n - title_hit),
        ]
    ]
    for y, c in sorted(years.items()):
        corpus_rows.append({"table": "priority_year", "item": y, "count": c})
    write_csv(OUT / "01_corpus.csv", ["table", "item", "count"], corpus_rows)

    # --- 2. mapping ---
    mapped: list[dict] = []
    known_hist = Counter()
    for row in raw:
        text = f"{row.get('Title') or ''}\n{row.get('Abstract') or ''}".lower()
        rec = {
            "display_key": row.get("Display Key") or "",
            "priority_date": row.get("Earliest Priority Date") or "",
            "priority_year": parse_year(row.get("Earliest Priority Date") or ""),
            "publication_year": row.get("Publication Year") or "",
            "jurisdiction": row.get("Jurisdiction") or "",
            "title": (row.get("Title") or "").replace("\n", " "),
        }
        n_known = 0
        multi_axes = []
        for axis in AXIS_ORDER:
            level, n_hits, all_hits = assign_level(text, AXES[axis])
            rec[axis] = level
            rec[f"{axis}_hits"] = all_hits
            rec[f"{axis}_n_hits"] = n_hits
            if level != UNKNOWN:
                n_known += 1
            if n_hits > 1:
                multi_axes.append(axis)
        rec["n_known"] = n_known
        rec["multi_axis"] = "|".join(multi_axes)
        known_hist[n_known] += 1
        mapped.append(rec)

    map_fields = [
        "display_key",
        "priority_date",
        "priority_year",
        "publication_year",
        "jurisdiction",
        "title",
        *AXIS_ORDER,
        *[f"{a}_hits" for a in AXIS_ORDER],
        *[f"{a}_n_hits" for a in AXIS_ORDER],
        "n_known",
        "multi_axis",
    ]
    write_csv(OUT / "02_mapping.csv", map_fields, mapped)

    # --- 3. occupancy ---
    axis_count_rows = []
    for axis in AXIS_ORDER:
        levels = list(AXES[axis].keys()) + [UNKNOWN]
        cnt = Counter(r[axis] for r in mapped)
        known_n = n - cnt[UNKNOWN]
        for level in levels:
            axis_count_rows.append(
                {
                    "axis": axis,
                    "level": level,
                    "count": cnt[level],
                    "share_pct": round(100 * cnt[level] / n, 1) if n else 0,
                    "axis_known_n": known_n,
                    "axis_known_pct": round(100 * known_n / n, 1) if n else 0,
                }
            )
    for k in range(0, len(AXIS_ORDER) + 1):
        axis_count_rows.append(
            {
                "axis": "_n_known",
                "level": str(k),
                "count": known_hist[k],
                "share_pct": round(100 * known_hist[k] / n, 1) if n else 0,
                "axis_known_n": "",
                "axis_known_pct": "",
            }
        )
    write_csv(
        OUT / "03_axis_counts.csv",
        ["axis", "level", "count", "share_pct", "axis_known_n", "axis_known_pct"],
        axis_count_rows,
    )

    pair_rows = []
    for a, b in combinations(AXIS_ORDER, 2):
        levels_a = list(AXES[a].keys())
        levels_b = list(AXES[b].keys())
        both = [
            r
            for r in mapped
            if r[a] != UNKNOWN and r[b] != UNKNOWN
        ]
        cnt = Counter((r[a], r[b]) for r in both)
        for la, lb in product(levels_a, levels_b):
            pair_rows.append(
                {
                    "axis_a": a,
                    "level_a": la,
                    "axis_b": b,
                    "level_b": lb,
                    "count": cnt[(la, lb)],
                    "n_both_known": len(both),
                }
            )
    pair_rows.sort(key=lambda r: (-r["n_both_known"], r["axis_a"], r["axis_b"], -r["count"]))
    write_csv(
        OUT / "04_pairs.csv",
        ["axis_a", "level_a", "axis_b", "level_b", "count", "n_both_known"],
        pair_rows,
    )

    full = [r for r in mapped if r["n_known"] == len(AXIS_ORDER)]
    cell_cnt: dict[tuple, int] = defaultdict(int)
    for r in full:
        key = tuple(r[a] for a in AXIS_ORDER)
        cell_cnt[key] += 1
    cell_rows = [
        {
            **{axis: key[i] for i, axis in enumerate(AXIS_ORDER)},
            "count": c,
        }
        for key, c in sorted(cell_cnt.items(), key=lambda x: -x[1])
    ]
    cell_rows.append(
        {
            **{axis: "_TOTAL_FULLY_MAPPED" for axis in AXIS_ORDER},
            "count": len(full),
        }
    )
    write_csv(OUT / "05_cells.csv", AXIS_ORDER + ["count"], cell_rows)

    print(f"n={n}")
    print("known hist", dict(sorted(known_hist.items())))
    print("axis known", {a: n - Counter(r[a] for r in mapped)[UNKNOWN] for a in AXIS_ORDER})
    print("fully mapped", len(full))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
