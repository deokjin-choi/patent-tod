"""Count v1 knowledge-graph objects by relation. Review whether slots look like axes."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from config import ENTITY_STD, OUT_PSE, PSE_MODIFY
from lib import write_csv, write_json

SLOTS = [
    "Addresses_Problem",
    "Comprises_Component",
    "Implemented_By",
    "Achieves_Effect",
]

SLOT_LABEL = {
    "Addresses_Problem": "problem (what is wrong)",
    "Comprises_Component": "structure (where / what parts)",
    "Implemented_By": "implementation (how it runs)",
    "Achieves_Effect": "effect (what got better)",
}

REL_ALIASES = {
    "comprises_component": "Comprises_Component",
    "composes_component": "Comprises_Component",
    "compose_component": "Comprises_Component",
    "addresses_problem": "Addresses_Problem",
    "address_problem": "Addresses_Problem",
    "implemented_by": "Implemented_By",
    "implements": "Implemented_By",
    "implementedby": "Implemented_By",
    "achieves_effect": "Achieves_Effect",
    "achieve_effect": "Achieves_Effect",
    "achieveseffect": "Achieves_Effect",
}

GENERIC_OBJ = re.compile(
    r"^(the\s+)?(proposed\s+)?(present\s+)?(system|method|apparatus|device|invention)s?$",
    re.I,
)
WS = re.compile(r"\s+")


def norm_rel(rel: str) -> str:
    key = (rel or "").strip().replace(" ", "_").replace("-", "_").lower()
    key = re.sub(r"_+", "_", key)
    return REL_ALIASES.get(key, rel.strip() if rel else "other")


def norm_obj(text: str) -> str:
    s = WS.sub(" ", (text or "").strip().strip('"').strip("'"))
    s = s.strip(" .,;:")
    return s.casefold()


def parse_kg(raw):
    if raw is None:
        return []
    if isinstance(raw, str):
        s = raw.strip()
        if "```" in s:
            s = re.sub(r"^.*?```(?:json)?", "", s, flags=re.S)
            s = re.sub(r"```.*$", "", s, flags=re.S)
        try:
            raw = json.loads(s)
        except json.JSONDecodeError:
            m = re.search(r"\[.*\]", s, re.S)
            if not m:
                return []
            try:
                raw = json.loads(m.group(0))
            except json.JSONDecodeError:
                return []
    if not isinstance(raw, list):
        return []
    triples = []
    for item in raw:
        if isinstance(item, (list, tuple)) and len(item) >= 3:
            triples.append((str(item[0]).strip(), str(item[1]).strip(), str(item[2]).strip()))
    return triples


def load_cluster_lookup() -> dict[str, int]:
    if not ENTITY_STD.exists():
        return {}
    std = json.loads(ENTITY_STD.read_text(encoding="utf-8"))
    em = std.get("entity_mapping") or {}
    out = {}
    for surface, cid in em.items():
        if not surface:
            continue
        out[surface.casefold()] = int(cid)
    return out


def main() -> None:
    OUT_PSE.mkdir(parents=True, exist_ok=True)
    clusters = load_cluster_lookup()

    files = sorted(PSE_MODIFY.glob("*_pse_kn.json"))
    file_rows = []
    obj_rows = []
    rel_all = Counter()
    slot_obj = {s: Counter() for s in SLOTS}
    slot_obj["other"] = Counter()
    slot_cluster = {s: Counter() for s in SLOTS}
    slot_cluster["other"] = Counter()
    n_kg_list = n_kg_empty = n_parse_fail = 0
    n_pse_ok = 0

    for path in files:
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            n_parse_fail += 1
            continue
        pub = doc.get("publication_number") or path.stem.replace("_pse_kn", "")
        pse = doc.get("pse") or {}
        if isinstance(pse, dict) and pse.get("problem"):
            n_pse_ok += 1
        triples = parse_kg(doc.get("knowledge_graph"))
        if not triples:
            n_kg_empty += 1
        else:
            n_kg_list += 1

        slot_hit = {s: 0 for s in SLOTS}
        other_n = 0
        long_n = 0
        for subj, rel, obj in triples:
            slot = norm_rel(rel)
            if slot not in SLOTS:
                slot = "other"
            rel_all[slot] += 1
            key = norm_obj(obj)
            if not key:
                continue
            n_words = len(key.split())
            if n_words >= 8:
                long_n += 1
            generic = bool(GENERIC_OBJ.match(key))
            cid = clusters.get(obj.casefold(), clusters.get(key))
            slot_obj[slot][key] += 1
            if cid is not None:
                slot_cluster[slot][cid] += 1
            if slot in slot_hit:
                slot_hit[slot] += 1
            else:
                other_n += 1
            obj_rows.append(
                {
                    "publication_number": pub,
                    "slot": slot,
                    "relation_raw": rel,
                    "subject": subj[:180],
                    "object_raw": obj[:240],
                    "object_norm": key[:240],
                    "n_words": n_words,
                    "generic": int(generic),
                    "cluster_id": cid if cid is not None else "",
                }
            )

        file_rows.append(
            {
                "publication_number": pub,
                "title": (doc.get("title") or "")[:180],
                "n_triples": len(triples),
                "n_problem": slot_hit["Addresses_Problem"],
                "n_structure": slot_hit["Comprises_Component"],
                "n_implement": slot_hit["Implemented_By"],
                "n_effect": slot_hit["Achieves_Effect"],
                "n_other": other_n,
                "n_long_objects": long_n,
                "has_pse": int(bool(isinstance(pse, dict) and pse.get("problem"))),
                "has_kg": int(bool(triples)),
            }
        )

    n = len(file_rows)
    write_csv(
        OUT_PSE / "10_patent_slots.csv",
        [
            "publication_number",
            "title",
            "n_triples",
            "n_problem",
            "n_structure",
            "n_implement",
            "n_effect",
            "n_other",
            "n_long_objects",
            "has_pse",
            "has_kg",
        ],
        file_rows,
    )
    write_csv(
        OUT_PSE / "10_objects.csv",
        [
            "publication_number",
            "slot",
            "relation_raw",
            "subject",
            "object_raw",
            "object_norm",
            "n_words",
            "generic",
            "cluster_id",
        ],
        obj_rows,
    )

    patents_for = defaultdict(set)
    for r in obj_rows:
        patents_for[(r["slot"], r["object_norm"])].add(r["publication_number"])

    def top_rows(counter: Counter, slot: str, kind: str, limit: int = 40) -> list[dict]:
        rows = []
        for rank, (term, c) in enumerate(counter.most_common(limit), 1):
            n_pat = (
                len(patents_for[(slot, str(term))])
                if kind == "string"
                else c
            )
            rows.append(
                {
                    "slot": slot,
                    "kind": kind,
                    "rank": rank,
                    "term": str(term)[:200],
                    "count": c,
                    "n_patents": n_pat,
                    "share_of_patents_pct": round(100 * n_pat / n, 2) if n else 0,
                }
            )
        return rows

    freq_rows = []
    summary_slot = []
    for slot in SLOTS + ["other"]:
        ctr = slot_obj[slot]
        total = sum(ctr.values())
        uniq = len(ctr)
        long = sum(c for t, c in ctr.items() if len(t.split()) >= 8)
        generic = sum(c for t, c in ctr.items() if GENERIC_OBJ.match(t))
        hapax = sum(1 for t, c in ctr.items() if c == 1)
        patents_with = sum(1 for r in file_rows if r[{"Addresses_Problem": "n_problem", "Comprises_Component": "n_structure", "Implemented_By": "n_implement", "Achieves_Effect": "n_effect", "other": "n_other"}[slot]] > 0)
        summary_slot.append(
            {
                "slot": slot,
                "label": SLOT_LABEL.get(slot, "other / leftover relations"),
                "n_patents_with_slot": patents_with,
                "pct_patents": round(100 * patents_with / n, 1) if n else 0,
                "n_mentions": total,
                "n_unique_strings": uniq,
                "type_token_ratio": round(uniq / total, 3) if total else 0,
                "pct_hapax": round(100 * hapax / uniq, 1) if uniq else 0,
                "pct_long_mentions": round(100 * long / total, 1) if total else 0,
                "pct_generic_mentions": round(100 * generic / total, 1) if total else 0,
                "top1": ctr.most_common(1)[0][0][:80] if ctr else "",
                "top1_count": ctr.most_common(1)[0][1] if ctr else 0,
            }
        )
        freq_rows.extend(top_rows(ctr, slot, "string"))
        freq_rows.extend(top_rows(slot_cluster[slot], slot, "cluster_id"))

    write_csv(
        OUT_PSE / "10_slot_summary.csv",
        list(summary_slot[0].keys()),
        summary_slot,
    )
    write_csv(
        OUT_PSE / "10_slot_top.csv",
        ["slot", "kind", "rank", "term", "count", "n_patents", "share_of_patents_pct"],
        freq_rows,
    )

    n_all4 = sum(
        1
        for r in file_rows
        if r["n_problem"] and r["n_structure"] and r["n_implement"] and r["n_effect"]
    )
    n_any = sum(1 for r in file_rows if r["has_kg"])
    triples = [r["n_triples"] for r in file_rows]
    manifest = {
        "n_files": len(files),
        "n_read": n,
        "n_parse_fail": n_parse_fail,
        "n_with_pse": n_pse_ok,
        "n_with_kg_v1": n_any,
        "n_empty_kg": n_kg_empty,
        "n_with_all_four_slots": n_all4,
        "mean_triples": round(sum(triples) / n, 2) if n else 0,
        "median_triples": sorted(triples)[n // 2] if n else 0,
        "source": str(PSE_MODIFY),
        "note": "v1 knowledge_graph only. v2 ignored. Counts are object strings after light normalize.",
    }
    write_json(OUT_PSE / "10_manifest.json", manifest)

    print("files", n, "kg", n_any, "empty", n_kg_empty, "all4", n_all4, "mean triples", manifest["mean_triples"])
    for row in summary_slot:
        print(
            f"  {row['slot']:22s} patents={row['n_patents_with_slot']:4d} ({row['pct_patents']:5.1f}%)  "
            f"uniq={row['n_unique_strings']:4d}/{row['n_mentions']:4d}  hapax={row['pct_hapax']:5.1f}%  "
            f"long={row['pct_long_mentions']:4.1f}%  top={row['top1'][:40]!r} x{row['top1_count']}"
        )


if __name__ == "__main__":
    main()
