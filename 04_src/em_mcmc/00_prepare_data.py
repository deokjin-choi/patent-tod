"""Draw a small Edge AI subset. Does not use the FL pilot folder."""

from __future__ import annotations

import csv
import random
from datetime import datetime, timezone

from config import MANIFEST, N_PATENTS, PATENTS, SEED, SOURCE_PATENTS
from lib import write_csv, write_json

KEEP = [
    ("Display Key", "display_key"),
    ("Lens ID", "lens_id"),
    ("Jurisdiction", "jurisdiction"),
    ("Publication Year", "publication_year"),
    ("Earliest Priority Date", "priority_date"),
    ("Title", "title"),
    ("Abstract", "abstract"),
    ("CPC Classifications", "cpc"),
    ("IPCR Classifications", "ipc"),
    ("Cited by Patent Count", "cited_by"),
    ("Cites Patent Count", "cites_patent"),
    ("Simple Family Size", "family_size"),
]


def parse_year(s: str) -> str:
    s = (s or "").strip()
    return s[:4] if len(s) >= 4 and s[:4].isdigit() else ""


def main() -> None:
    if not SOURCE_PATENTS.exists():
        raise SystemExit(f"missing source CSV: {SOURCE_PATENTS}")

    rng = random.Random(SEED)
    sample: list[dict[str, str]] = []
    n_seen = 0
    n_total = 0
    n_no_abstract = 0

    with SOURCE_PATENTS.open(encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            n_total += 1
            abstract = (raw.get("Abstract") or "").strip()
            if not abstract:
                n_no_abstract += 1
                continue
            n_seen += 1
            row = {dst: (raw.get(src) or "").replace("\n", " ").strip() for src, dst in KEEP}
            row["priority_year"] = parse_year(row["priority_date"]) or parse_year(
                row["publication_year"]
            )
            if len(sample) < N_PATENTS:
                sample.append(row)
            else:
                j = rng.randrange(n_seen)
                if j < N_PATENTS:
                    sample[j] = row

    sample.sort(key=lambda r: (r.get("priority_year") or "9999", r.get("display_key") or ""))
    fields = [dst for _, dst in KEEP] + ["priority_year"]
    write_csv(PATENTS, fields, sample)

    write_json(
        MANIFEST,
        {
            "source": str(SOURCE_PATENTS),
            "n_source_rows": n_total,
            "n_with_abstract": n_seen,
            "n_no_abstract": n_no_abstract,
            "n_kept": len(sample),
            "seed": SEED,
            "method": "reservoir sample among rows with a non-empty abstract",
            "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "note": "This file is the working corpus for EM/MCMC. It is not a FL slice.",
        },
    )
    years = {}
    for r in sample:
        years[r["priority_year"] or "missing"] = years.get(r["priority_year"] or "missing", 0) + 1
    print(f"source rows={n_total} with_abstract={n_seen} kept={len(sample)}")
    print("priority years", dict(sorted(years.items())))
    print("wrote", PATENTS)


if __name__ == "__main__":
    main()
