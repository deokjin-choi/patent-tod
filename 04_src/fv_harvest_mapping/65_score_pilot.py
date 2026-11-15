"""파일럿 8건의 매핑 결과를 정답(pilot_gold.json)과 대조해 확장초록 4.2절과 같은 모양의 표로 낸다.

칸마다 O(맞음), X(틀림), –(범위 밖 특허라 채점 안 함)를 붙인다. 기능 칸은 관계와 수행 주체(기계/사람)가 모두 맞아야 O다.
구분과 분업 방식은 60_check_output.derive와 같은 규칙으로 계산한다.

실행:
  conda run -n scenario-space python 65_score_pilot.py --version v3 --run mistral__mistral
  conda run -n scenario-space python 65_score_pilot.py --version v2 --run mistral__mistral
"""

from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path

from config import DATA, FULLTEXT_DIR, TASK

derive = importlib.import_module("60_check_output").derive

FUNCS = ("F1", "F2", "F3", "F4")
NAMES = {"F1": "F1 대상 식별", "F2": "F2 위치 조정", "F3": "F3 분리·채취", "F4": "F4 수집·이송"}
REL = {"direct": "직접 수행", "support": "지원", "not_mentioned": "언급 없음"}
ACTOR = {"invention": "기계", "host_machine": "탑재 기계", "human": "사람", "both": "기계+사람", "not_specified": ""}
ACTOR_GROUP = {"invention": "machine", "host_machine": "machine", "both": "machine", "human": "human"}
CLASS = {"harvest_device": "수확 장치", "component": "부품 기술", "unmapped": "대응 없음"}
SCOPE = {
    "industrial_crop": "공업용 작물", "grain_forage_or_grass": "곡물·사료·잔디", "tree_nut_only": "견과 전용",
    "non_harvest_task": "수확 외 작업", "post_harvest_handling": "수확 뒤 작업", "unclear": "불분명",
}
IN_SCOPE = "fruit_or_vegetable_harvest"
GOLD = Path(__file__).with_name("pilot_gold.json")


def ox(ok: bool | None) -> str:
    return "–" if ok is None else ("O" if ok else "X")


def cell_ok(pred: dict, gold: list) -> bool:
    if pred["relation"] != gold[0]:
        return False
    return gold[0] == "not_mentioned" or ACTOR_GROUP.get(pred["actor"]) == gold[1]


def fmt_rel(pred: dict) -> str:
    actor = ACTOR[pred["actor"]]
    return REL[pred["relation"]] + (f"({actor})" if actor and pred["relation"] != "not_mentioned" else "")


def fmt_split(f: dict) -> str:
    def join(ks):
        return "F1–F4" if len(ks) == 4 else "·".join(ks)
    machine = [k for k in FUNCS if f[k]["relation"] != "not_mentioned" and ACTOR_GROUP.get(f[k]["actor"]) == "machine"]
    human = [k for k in FUNCS if f[k]["relation"] != "not_mentioned" and f[k]["actor"] == "human"]
    parts = ([f"기계가 {join(machine)}"] if machine else ["기계가 맡는 기능 없음"]) + ([f"사람이 {join(human)}"] if human else [])
    return ", ".join(parts)


def gold_derive(g: dict) -> tuple[str, set]:
    f = {k: {"relation": r, "actor": "invention" if a == "machine" else (a or "not_specified")} for k, (r, a) in g["F"].items()}
    cls, machine = derive({"functions": f})
    return cls, set(machine.split("·")) - {""}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True, help="프롬프트 버전, 예: v3")
    ap.add_argument("--run", required=True, help="매핑 폴더 이름, 예: mistral__mistral")
    args = ap.parse_args()
    run_dir = DATA / "llm_output" / f"mapping_{TASK}_{args.version}" / args.run
    gold = json.loads(GOLD.read_text(encoding="utf-8"))

    head = ["특허", "범위", *NAMES.values(), "구분", "분업 방식 또는 역할", "비고"]
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    score = {"scope": [0, 0], "F": [0, 0], "class": [0, 0], "split": [0, 0]}

    for gid in gold["order"]:
        g = gold["patents"][gid]
        title = json.loads((FULLTEXT_DIR / f"{gid}.json").read_text(encoding="utf-8"))["title"].capitalize()
        rec = json.loads((run_dir / f"{gid}.json").read_text(encoding="utf-8"))
        m = rec["output"]
        if m is None:
            lines.append(f"| {gid} {title} | 출력 없음 |" + " |" * (len(head) - 2))
            continue
        cat, f = m["scope"]["category"], m["functions"]
        in_gold = g["scope"] == "in"

        if cat == IN_SCOPE:
            scope_ok = in_gold
            scope_cell = f"범위 안 {ox(scope_ok)}"
        elif in_gold:
            scope_ok = False
            scope_cell = f"범위 밖(사유: {SCOPE[cat]}) X"
        else:
            scope_ok = True
            scope_cell = f"범위 밖 O (사유: {SCOPE[cat]} {ox(cat in g['scope_ok'])})"
        score["scope"][0] += scope_ok
        score["scope"][1] += 1

        cells = []
        for k in FUNCS:
            ok = cell_ok(f[k], g["F"][k]) if in_gold else None
            if ok is not None:
                score["F"][0] += ok
                score["F"][1] += 1
            cells.append(f"{fmt_rel(f[k])} {ox(ok)}")

        cls, machine = derive(m)
        machine_set = set(machine.split("·")) - {""}
        if in_gold:
            g_cls, g_machine = gold_derive(g)
            cls_ok, split_ok = cls == g_cls, machine_set == g_machine
            score["class"][0] += cls_ok
            score["class"][1] += 1
            score["split"][0] += split_ok
            score["split"][1] += 1
        else:
            cls_ok = split_ok = None

        row = [f"{gid} {title}", scope_cell, *cells, f"{CLASS[cls]} {ox(cls_ok)}", f"{fmt_split(f)} {ox(split_ok)}", g["note"]]
        lines.append("| " + " | ".join(row) + " |")

    summary = (
        f"범위 {score['scope'][0]}/{score['scope'][1]}, F1–F4 {score['F'][0]}/{score['F'][1]}칸, "
        f"구분 {score['class'][0]}/{score['class'][1]}, 분업 방식 {score['split'][0]}/{score['split'][1]}"
    )
    text = "\n".join(lines) + f"\n\n{summary}\n"
    print(text)
    (DATA / "llm_output" / f"score_{args.version}_{args.run}.md").write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
