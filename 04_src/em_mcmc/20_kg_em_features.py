"""Build per-axis count matrices from v1 triples + matching essay fields.

Axes are the four closed v1 relations. Features are object heads, structure
subject heads, and essay unigrams. Templates are dropped.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import numpy as np

from config import KG_EM_MAX_ESSAY, KG_EM_MAX_HEADS, KG_EM_MIN_DF, OUT_KG_EM, PSE_MODIFY

MIN_DF_HEAD = 3
from lib import write_csv, write_json

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
    "from", "via", "using", "based", "its", "their", "this", "that", "as",
    "is", "are", "be", "been", "being", "at", "into", "over", "under",
    "can", "may", "will", "not", "no", "such", "more", "than", "also",
    "which", "where", "when", "how", "one", "two", "first", "second",
}

SLOT_LABEL = {
    "Addresses_Problem": "problem",
    "Comprises_Component": "structure",
    "Implemented_By": "how it runs",
    "Achieves_Effect": "effect",
}

PSE_FIELDS = {
    "Addresses_Problem": ("problem",),
    "Comprises_Component": ("solution_structure",),
    "Implemented_By": ("solution_function", "solution_implementation"),
    "Achieves_Effect": ("effect",),
}


def tokens(text: str) -> list[str]:
    s = re.sub(r"\([^)]*\)", " ", text or "")
    return [t for t in re.split(r"[^a-z0-9]+", s.lower()) if t and t not in STOP_TOKENS and len(t) > 1]


def head2(text: str) -> str:
    toks = tokens(text)
    if not toks:
        return ""
    if len(toks) >= 2:
        return " ".join(toks[-2:])
    return toks[0]


def is_stop(obj_norm: str, head: str) -> bool:
    return obj_norm in STOP_OBJ or head in STOP_OBJ


def main() -> None:
    OUT_KG_EM.mkdir(parents=True, exist_ok=True)
    files = sorted(PSE_MODIFY.glob("*_pse_kn.json"))
    pubs = []
    bag = {s: [] for s in SLOTS}
    n_fail = 0
    n_empty_kg = 0
    n_pse = 0

    for path in files:
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            n_fail += 1
            continue
        pub = doc.get("publication_number") or path.stem.replace("_pse_kn", "")
        pubs.append(pub)
        counts = {s: Counter() for s in SLOTS}
        triples = parse_kg(doc.get("knowledge_graph"))
        if not triples:
            n_empty_kg += 1
        for subj, rel, obj in triples:
            slot = norm_rel(rel)
            if slot not in SLOTS:
                continue
            key = norm_obj(obj)
            h = head2(key)
            if key and h and not is_stop(key, h):
                counts[slot][f"h:{h}"] += 1
            if slot == "Comprises_Component":
                sh = head2(norm_obj(subj))
                if sh and not is_stop(norm_obj(subj), sh):
                    counts[slot][f"s:{sh}"] += 1
        pse = doc.get("pse") if isinstance(doc.get("pse"), dict) else {}
        if pse:
            n_pse += 1
        for slot, fields in PSE_FIELDS.items():
            for field in fields:
                for tok in tokens(str(pse.get(field) or "")):
                    counts[slot][f"p:{tok}"] += 1
        for s in SLOTS:
            bag[s].append(counts[s])

    n = len(pubs)
    summary_rows = []
    for slot in SLOTS:
        df = Counter()
        for c in bag[slot]:
            df.update(c.keys())
        # Graph heads first (the repeating objects). Essay tokens fill the rest.
        heads = [
            t
            for t, d in df.most_common()
            if t.startswith(("h:", "s:")) and d >= MIN_DF_HEAD
        ][:KG_EM_MAX_HEADS]
        essays = [
            t
            for t, d in df.most_common()
            if t.startswith("p:") and KG_EM_MIN_DF <= d <= 0.45 * n
        ][:KG_EM_MAX_ESSAY]
        vocab = heads + essays
        vmap = {t: j for j, t in enumerate(vocab)}
        X = np.zeros((n, len(vocab)), dtype=np.float64)
        n_tokens = []
        for i, c in enumerate(bag[slot]):
            tot = 0
            for t, k in c.items():
                j = vmap.get(t)
                if j is not None:
                    X[i, j] = k
                    tot += k
            n_tokens.append(tot)
        np.save(OUT_KG_EM / f"20_X_{slot}.npy", X)
        write_json(OUT_KG_EM / f"20_vocab_{slot}.json", vocab)
        n_empty = int((X.sum(axis=1) == 0).sum())
        n_head = sum(1 for t in vocab if t.startswith("h:"))
        n_subj = sum(1 for t in vocab if t.startswith("s:"))
        n_pse_t = sum(1 for t in vocab if t.startswith("p:"))
        summary_rows.append(
            {
                "slot": slot,
                "label": SLOT_LABEL[slot],
                "n_vocab": len(vocab),
                "n_head_terms": n_head,
                "n_subject_terms": n_subj,
                "n_essay_terms": n_pse_t,
                "n_empty": n_empty,
                "pct_empty": round(100 * n_empty / n, 1) if n else 0,
                "mean_tokens": round(float(np.mean(n_tokens)), 2) if n else 0,
            }
        )

    write_json(OUT_KG_EM / "20_pubs.json", pubs)
    write_csv(OUT_KG_EM / "20_feature_summary.csv", list(summary_rows[0].keys()), summary_rows)
    write_json(
        OUT_KG_EM / "20_manifest.json",
        {
            "n_files": len(files),
            "n_read": n,
            "n_parse_fail": n_fail,
            "n_empty_kg": n_empty_kg,
            "n_with_essay": n_pse,
            "min_df_essay": KG_EM_MIN_DF,
            "min_df_head": MIN_DF_HEAD,
            "max_heads": KG_EM_MAX_HEADS,
            "max_essay": KG_EM_MAX_ESSAY,
            "axes": SLOTS,
            "pse_fields": {k: list(v) for k, v in PSE_FIELDS.items()},
        },
    )
    print("patents", n, "essay", n_pse, "empty kg", n_empty_kg)
    for row in summary_rows:
        print(
            f"  {row['label']:12s} V={row['n_vocab']:3d}  "
            f"h/s/p={row['n_head_terms']}/{row['n_subject_terms']}/{row['n_essay_terms']}  "
            f"empty={row['n_empty']}"
        )


if __name__ == "__main__":
    main()
