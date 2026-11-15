"""카드·매핑 출력 점검.

- 카드: 근거 인용이 원문에 있는지, 기능 번호가 1부터 차례인지, 같은 동사를 되풀이하는지, 인용이 빠졌는지.
- 매핑: 인용이 카드에서 그대로 옮겨졌는지. 범위, 수확 장치/부품 기술 구분, 분업 방식을 규칙으로 붙인다.

실행:
  conda run -n scenario-space python 60_check_output.py --card-run mistral
  conda run -n scenario-space python 60_check_output.py --card-run mistral --mapping-run mistral__mistral
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter

import pandas as pd

from config import DATA, FULLTEXT_DIR, PROMPT_VERSION, TASK
from patent_text import location_index

FUNCS = ("F1", "F2", "F3", "F4")
MACHINE_ACTORS = ("invention", "host_machine", "both")
IN_SCOPE = "fruit_or_vegetable_harvest"
LLM_OUT = DATA / "llm_output"


def norm(s: str) -> str:
    """공백을 모두 지우고 비교한다. 원문의 "camera ( 10 )"를 모델이 "camera (10)"로 옮기는 경우가 많다."""
    return re.sub(r"\s+", "", s.lower()).strip(".,;:…\"'")


def _adjacent(a: str, b: str) -> bool:
    """같은 종류(본문 P, 청구항 C)에서 번호가 하나 차이."""
    return a[:2] == b[:2] and abs(int(re.sub(r"\D", "", a) or -9) - int(re.sub(r"\D", "", b) or -9)) == 1


def iter_evidence(node, path=""):
    if isinstance(node, dict):
        if "loc" in node and "quote" in node:
            yield path, node
            return
        for k, v in node.items():
            yield from iter_evidence(v, f"{path}/{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from iter_evidence(v, f"{path}/{i}")


def check_quotes(output: dict, doc: dict) -> list[dict]:
    """exact: 지정한 문단에 있음. adjacent: 바로 앞뒤 문단에 있음. wrong_loc: 다른 문단에 있음. not_found: 원문에 없음."""
    idx = {k: norm(v) for k, v in location_index(doc).items()}
    rows = []
    for path, ev in iter_evidence(output):
        q = norm(ev["quote"])
        found = [k for k, v in idx.items() if q and q in v]
        if ev["loc"] in found:
            hit = "exact"
        elif not found:
            hit = "not_found"
        elif any(_adjacent(k, ev["loc"]) for k in found):
            hit = "adjacent"
        else:
            hit = "wrong_loc"
        rows.append({"path": path, "loc": ev["loc"], "found_at": ";".join(found), "hit": hit, "quote": ev["quote"]})
    return rows


def card_row(card: dict) -> dict:
    fns = card["functions"]
    ids = [f["id"] for f in fns]
    verbs = Counter(f["verb"] for f in fns)
    return {
        "subject": card["subject"]["phrase"][:50],
        "host": card["host_machine"][:30],
        "n_func": len(fns),
        "ids_ok": ids == list(range(1, len(fns) + 1)),
        "max_same_verb": max(verbs.values(), default=0),
        "no_quote": sum(not f["evidence"] for f in fns),
        "claimed_func": sum(f.get("claim", "none") != "none" for f in fns),
        "actors": ",".join(sorted({f["actor"] for f in fns})),
        "n_prob": len(card["problems"]),
        "n_eff": len(card["effects"]),
        "targets": ",".join(card["target_categories"]),
        "form": card["form_factor"],
        "power": ",".join(card["power_source"]),
    }


def derive(m: dict) -> tuple[str, str]:
    """(구분, 기계가 맡는 기능). 범위와 따로, 범위 밖 판정을 받은 특허에도 계산한다.

    기계가 맡는 기능은 발명이 직접 수행하거나 지원하는 기능 가운데 수행 주체가 기계(발명 또는 발명이 달리는 기계)인 것이다.
    """
    f = m["functions"]
    machine = "·".join(
        k for k in FUNCS if f[k]["relation"] != "not_mentioned" and f[k]["actor"] in MACHINE_ACTORS
    )
    if f["F3"]["relation"] == "direct":
        return "harvest_device", machine
    if any(f[k]["relation"] != "not_mentioned" for k in FUNCS):
        return "component", machine
    return "unmapped", machine


def direct_unclaimed(m: dict, card: dict) -> str:
    """direct로 판정했는데 연결한 카드 기능이 모두 청구항 밖(claim none)인 하위 기능. v2 카드에는 claim 칸이 없다."""
    claim = {fn["id"]: fn.get("claim") for fn in card["functions"]}
    if None in claim.values():
        return ""
    f = m["functions"]
    return ",".join(
        k for k in FUNCS
        if f[k]["relation"] == "direct" and all(claim.get(i, "none") == "none" for i in f[k]["card_functions"])
    )


def mapping_row(m: dict, card: dict) -> dict:
    card_quotes = {(e["loc"], e["quote"]) for _, e in iter_evidence(card)}
    copied = [(e["loc"], e["quote"]) in card_quotes for _, e in iter_evidence(m)]
    cls, machine = derive(m)
    f = m["functions"]
    return {
        "scope": m["scope"]["category"],
        "in_scope": m["scope"]["category"] == IN_SCOPE,
        **{k: f"{f[k]['relation'][:3]}/{f[k]['actor'][:5]}/{f[k]['card_functions']}" for k in FUNCS},
        "class": cls,
        "machine_does": machine,
        "direct_unclaimed": direct_unclaimed(m, card),
        "detach": ",".join(m["detachment_principle"]["values"]),
        "conf": m["overall_confidence"],
        "quotes_copied": f"{sum(copied)}/{len(copied)}",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--card-run", required=True)
    ap.add_argument("--mapping-run", default=None, help="mapping 폴더 이름, 예: mistral__mistral")
    args = ap.parse_args()
    card_dir = LLM_OUT / f"card_{PROMPT_VERSION}" / args.card_run
    map_dir = LLM_OUT / f"mapping_{TASK}_{PROMPT_VERSION}" / args.mapping_run if args.mapping_run else None

    rows, quotes = [], []
    for p in sorted(card_dir.glob("*.json")):
        rec = json.loads(p.read_text(encoding="utf-8"))
        gid, card = rec["google_id"], rec["output"]
        row = {"google_id": gid, "sec": rec["seconds"], "in_tok": rec["prompt_tokens"], "out_tok": rec["output_tokens"],
               "done": rec["done_reason"], "ctx_full": rec["ctx_full"], "schema_err": len(rec["schema_errors"]),
               "trunc": rec["input_meta"]["truncated"]}
        if card is not None:
            doc = json.loads((FULLTEXT_DIR / f"{gid}.json").read_text(encoding="utf-8"))
            q = check_quotes(card, doc)
            quotes += [r | {"google_id": gid} for r in q]
            row |= card_row(card)
            row["exact%"] = round(100 * sum(r["hit"] == "exact" for r in q) / max(len(q), 1))
            row["missing%"] = round(100 * sum(r["hit"] == "not_found" for r in q) / max(len(q), 1))
            if map_dir is not None and (map_dir / f"{gid}.json").exists():
                mrec = json.loads((map_dir / f"{gid}.json").read_text(encoding="utf-8"))
                row["map_sec"] = mrec["seconds"]
                row["map_schema_err"] = len(mrec["schema_errors"])
                row["claim_fixes"] = len(mrec.get("claim_fixes", []))
                if mrec["output"] is not None:
                    row |= mapping_row(mrec["output"], mrec.get("card_used", card))
        rows.append(row)

    s = pd.DataFrame(rows)
    pd.set_option("display.width", 300)
    pd.set_option("display.max_columns", 50)
    print(s.to_string(index=False))
    stem = args.mapping_run or args.card_run
    s.to_csv(LLM_OUT / f"check_{PROMPT_VERSION}_{stem}.csv", index=False, encoding="utf-8-sig")
    qd = pd.DataFrame(quotes)
    qd.to_csv(LLM_OUT / f"check_{PROMPT_VERSION}_{args.card_run}_card_quotes.csv", index=False, encoding="utf-8-sig")
    if len(qd):
        print("\n카드 인용 대조:", qd["hit"].value_counts().to_dict())


if __name__ == "__main__":
    main()
