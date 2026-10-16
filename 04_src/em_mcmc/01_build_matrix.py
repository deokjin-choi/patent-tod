"""Build the basic data structure: sparse-ish keyword count matrix + CPC flags.

Row = patent. Column = dictionary phrase count, then CPC 0/1, then cited_by.
This is the 'keyword frequency vector' the note starts from. No embeddings.
"""

from __future__ import annotations

import json

import numpy as np

from config import CONSTRAINTS, OUT, PATENTS
from lib import (
    cpc_flags,
    compile_phrase,
    count_phrase,
    ensure_out,
    load_dictionary,
    load_json,
    patent_text,
    read_csv,
    vocab_entries,
    write_csv,
)


def main() -> None:
    ensure_out()
    d = load_dictionary()
    patents = read_csv(PATENTS)
    vocab = vocab_entries(d)
    prefixes = d["cpc_prefixes"]
    pats = [compile_phrase(v["phrase"]) for v in vocab]

    counts = np.zeros((len(patents), len(vocab)), dtype=float)
    sig_rows = []
    feat_rows = []
    hit_patents = 0

    for i, row in enumerate(patents):
        text = patent_text(row)
        hits = []
        for j, (v, pat) in enumerate(zip(vocab, pats)):
            c = count_phrase(text, pat)
            counts[i, j] = c
            if c:
                hits.append(f"{v['origin']}x{int(c)}")
        if counts[i].sum() > 0:
            hit_patents += 1
        flags = cpc_flags(row.get("cpc") or "", prefixes)
        try:
            cited = int(float(row.get("cited_by") or 0))
        except ValueError:
            cited = 0
        rec = {
            "display_key": row["display_key"],
            "priority_year": row.get("priority_year") or "",
            "n_keyword_hits": int(counts[i].sum()),
            "n_keyword_types": int((counts[i] > 0).sum()),
            "cited_by": cited,
            **flags,
        }
        for j, v in enumerate(vocab):
            rec[f"kw_{j:03d}"] = int(counts[i, j])
        feat_rows.append(rec)
        sig = "".join("1" if x > 0 else "0" for x in counts[i])
        sig_rows.append(
            {
                "display_key": row["display_key"],
                "signature": sig,
                "n_types": int((counts[i] > 0).sum()),
                "origins": "|".join(hits),
            }
        )

    vocab_rows = []
    for j, v in enumerate(vocab):
        vocab_rows.append(
            {
                "kw_id": f"kw_{j:03d}",
                "index": j,
                **v,
                "docs_with_term": int((counts[:, j] > 0).sum()),
                "total_count": int(counts[:, j].sum()),
            }
        )

    kw_fields = [f"kw_{j:03d}" for j in range(len(vocab))]
    cpc_fields = [f"cpc_{p}" for p in prefixes]
    write_csv(
        OUT / "01_vocab.csv",
        ["kw_id", "index", "term_id", "axis", "level", "origin", "phrase", "docs_with_term", "total_count"],
        vocab_rows,
    )
    write_csv(
        OUT / "01_feature_matrix.csv",
        ["display_key", "priority_year", "n_keyword_hits", "n_keyword_types", "cited_by", *cpc_fields, *kw_fields],
        feat_rows,
    )
    write_csv(
        OUT / "01_signatures.csv",
        ["display_key", "signature", "n_types", "origins"],
        sig_rows,
    )
    np.save(OUT / "01_counts.npy", counts)

    cons = load_json(CONSTRAINTS)
    (OUT / "01_constraints_copy.json").write_text(
        json.dumps(cons, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"n={len(patents)} vocab={len(vocab)} docs_with_any_keyword={hit_patents}")
    print("wrote", OUT / "01_feature_matrix.csv")


if __name__ == "__main__":
    main()
