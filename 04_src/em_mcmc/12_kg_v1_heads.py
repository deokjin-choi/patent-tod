"""KG v1 only: collapse objects to heads, rank level candidates. Does not read pse."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict

from config import OUT_KG, PSE_MODIFY
from lib import write_csv, write_json

# import parsers without running main
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_spec = spec_from_file_location("pse_inv", Path(__file__).resolve().parent / "10_pse_slot_inventory.py")
_mod = module_from_spec(_spec)
_spec.loader.exec_module(_mod)
parse_kg = _mod.parse_kg
norm_rel = _mod.norm_rel
norm_obj = _mod.norm_obj
SLOTS = _mod.SLOTS

STOP_OBJ = {
    "core problem concept",
    "core operation logic",
    "primary benefit",
    "key component 1",
    "key component 2",
    "main technology entity",
    "n/a",
    "na",
}

STOP_TOKENS = {
    "the", "a", "an", "of", "and", "or", "for", "to", "in", "on", "with", "by",
    "from", "via", "using", "based", "its", "their", "this", "that",
}

SLOT_LABEL = {
    "Addresses_Problem": "problem",
    "Comprises_Component": "structure",
    "Implemented_By": "how it runs",
    "Achieves_Effect": "effect",
}


def tokens(text: str) -> list[str]:
    s = re.sub(r"\([^)]*\)", " ", text)
    return [t for t in re.split(r"[^a-z0-9]+", s.lower()) if t and t not in STOP_TOKENS]


def head2(text: str) -> str:
    toks = tokens(text)
    if not toks:
        return ""
    if len(toks) >= 2:
        return " ".join(toks[-2:])
    return toks[0]


def is_stop(obj_norm: str, head: str) -> bool:
    return obj_norm in STOP_OBJ or head in STOP_OBJ


def hapax_pct(counter: Counter) -> float:
    if not counter:
        return 0.0
    h = sum(1 for _, c in counter.items() if c == 1)
    return round(100 * h / len(counter), 1)


def main() -> None:
    OUT_KG.mkdir(parents=True, exist_ok=True)
    files = sorted(PSE_MODIFY.glob("*_pse_kn.json"))

    n_read = n_fail = n_empty = 0
    rel_n = Counter()
    full_ctr = {s: Counter() for s in SLOTS}
    head_ctr = {s: Counter() for s in SLOTS}
    full_pats = defaultdict(set)
    head_pats = defaultdict(set)
    subj_n = []
    n_subj = []
    n_obj = []
    n_triples = []
    slot_pat = {s: set() for s in SLOTS}
    other_n = 0
    rows_head = []
    n_stop = {s: 0 for s in SLOTS}

    for path in files:
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            n_fail += 1
            continue
        n_read += 1
        pub = doc.get("publication_number") or path.stem.replace("_pse_kn", "")
        triples = parse_kg(doc.get("knowledge_graph"))
        if not triples:
            n_empty += 1
        n_triples.append(len(triples))
        subjects = set()
        objects = set()
        for subj, rel, obj in triples:
            slot = norm_rel(rel)
            rel_n[slot] += 1
            if slot not in SLOTS:
                other_n += 1
                continue
            key = norm_obj(obj)
            if not key:
                continue
            h = head2(key)
            subjects.add(norm_obj(subj))
            objects.add(key)
            slot_pat[slot].add(pub)
            stop = is_stop(key, h)
            if stop:
                n_stop[slot] += 1
                continue
            full_ctr[slot][key] += 1
            full_pats[(slot, key)].add(pub)
            if h:
                head_ctr[slot][h] += 1
                head_pats[(slot, h)].add(pub)
                rows_head.append(
                    {
                        "publication_number": pub,
                        "slot": slot,
                        "object_norm": key[:240],
                        "head": h,
                        "n_words": len(key.split()),
                        "subject": subj[:160],
                    }
                )
        n_subj.append(len(subjects))
        n_obj.append(len(objects))

    n = n_read
    write_csv(
        OUT_KG / "12_heads.csv",
        ["publication_number", "slot", "object_norm", "head", "n_words", "subject"],
        rows_head,
    )

    top_rows = []
    summary = []
    for slot in SLOTS:
        fc, hc = full_ctr[slot], head_ctr[slot]
        n_ment_h = sum(hc.values())
        summary.append(
            {
                "slot": slot,
                "label": SLOT_LABEL[slot],
                "n_patents_with_slot": len(slot_pat[slot]),
                "pct_patents": round(100 * len(slot_pat[slot]) / n, 1) if n else 0,
                "n_mentions_kept": n_ment_h,
                "n_templates_dropped": n_stop[slot],
                "unique_full_strings": len(fc),
                "hapax_full_pct": hapax_pct(fc),
                "unique_heads": len(hc),
                "hapax_head_pct": hapax_pct(hc),
                "top_head": hc.most_common(1)[0][0] if hc else "",
                "top_head_patents": len(head_pats[(slot, hc.most_common(1)[0][0])]) if hc else 0,
            }
        )
        for rank, (term, c) in enumerate(hc.most_common(40), 1):
            npats = len(head_pats[(slot, term)])
            top_rows.append(
                {
                    "slot": slot,
                    "rank": rank,
                    "head": term,
                    "mentions": c,
                    "n_patents": npats,
                    "share_of_patents_pct": round(100 * npats / n, 2) if n else 0,
                }
            )

    write_csv(OUT_KG / "12_head_summary.csv", list(summary[0].keys()), summary)
    write_csv(
        OUT_KG / "12_head_top.csv",
        ["slot", "rank", "head", "mentions", "n_patents", "share_of_patents_pct"],
        top_rows,
    )

    all4 = sum(1 for pub in set().union(*slot_pat.values()) if all(pub in slot_pat[s] for s in SLOTS))
    # patents that appear in all 4 - compute properly
    if slot_pat[SLOTS[0]]:
        inter = set(slot_pat[SLOTS[0]])
        for s in SLOTS[1:]:
            inter &= slot_pat[s]
        all4 = len(inter)
    else:
        all4 = 0

    manifest = {
        "source": str(PSE_MODIFY),
        "field_used": "knowledge_graph (v1) only",
        "pse_used": False,
        "v2_used": False,
        "n_files": len(files),
        "n_read": n,
        "n_parse_fail": n_fail,
        "n_empty_kg": n_empty,
        "n_with_all_four_v1_slots": all4,
        "mean_triples": round(sum(n_triples) / n, 2) if n else 0,
        "median_triples": sorted(n_triples)[n // 2] if n else 0,
        "mean_unique_subjects": round(sum(n_subj) / n, 2) if n else 0,
        "median_unique_subjects": sorted(n_subj)[n // 2] if n else 0,
        "mean_unique_objects": round(sum(n_obj) / n, 2) if n else 0,
        "n_other_relations": other_n,
        "relation_counts": dict(rel_n),
        "head_rule": "last 1-2 content tokens of the object, parentheses stripped, templates dropped",
    }
    write_json(OUT_KG / "12_manifest.json", manifest)

    print("read", n, "empty", n_empty, "all4", all4, "subj/patent", manifest["mean_unique_subjects"])
    for row in summary:
        print(
            f"  {row['label']:12s} full hapax {row['hapax_full_pct']:5.1f}%  "
            f"head hapax {row['hapax_head_pct']:5.1f}%  "
            f"unique heads {row['unique_heads']:4d}  "
            f"top={row['top_head']!r} ({row['top_head_patents']} pats)"
        )


if __name__ == "__main__":
    main()
