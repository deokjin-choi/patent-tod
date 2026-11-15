"""대상 작물 이름을 작물군으로 묶는 사전.

LLM이 붙인 작물군(target_categories)은 파일럿 8건 중 3건이 틀려서, 카드의 대상 이름(target_objects)을 코드로 묶는다.
'fruit', 'plants'처럼 작물을 특정하지 않은 이름은 '미상'으로 둔다.

실행(사전 범위 점검):
  conda run -n scenario-space python crop_groups.py --card-run mistral
"""

from __future__ import annotations

import re

GROUPS: list[tuple[str, str, list[str]]] = [
    ("fruiting_vegetable", "열매채소", [
        r"strawberr", r"tomato", r"pepper", r"cucumber", r"eggplant", r"aubergine", r"melon", r"watermelon",
        r"pumpkin", r"squash", r"zucchini", r"okra", r"pineapple", r"paprika", r"chil(?:i|e|li)",
    ]),
    ("vine_bush_fruit", "덩굴·관목 과일", [
        r"grapes?\b", r"grapevine", r"berr", r"blueberr", r"raspberr", r"blackberr", r"currant", r"cranberr", r"kiwi", r"gooseberr",
    ]),
    ("tree_fruit", "나무 과일", [
        r"apples?\b", r"pears?\b", r"cherr", r"peach", r"plums?\b", r"apricot", r"citrus", r"orange", r"lemon",
        r"limes?\b", r"mandarin", r"grapefruit", r"olive", r"date palm", r"dates?\b", r"mango", r"avocado",
        r"coconut", r"stone fruit", r"tree fruit", r"persimmon", r"figs?\b", r"pomegranate", r"lychee", r"papaya",
        r"banana", r"jujube", r"tree crop",
    ]),
    ("leaf_stem_vegetable", "잎·줄기·꽃채소", [
        r"lettuce", r"cabbage", r"spinach", r"broccoli", r"cauliflower", r"asparagus", r"rapini", r"endive",
        r"celery", r"artichoke", r"leek", r"kale", r"chard", r"leafy", r"brussels",
    ]),
    ("root_vegetable", "뿌리·땅속 작물", [
        r"potato", r"beets?\b", r"carrot", r"onion", r"garlic", r"turnip", r"radish", r"lotus root", r"root crop",
        r"root vegetable", r"cassava", r"yams?\b", r"parsnip", r"peanut", r"tuber", r"ginger",
    ]),
    ("legume_vegetable", "콩·꼬투리 채소", [r"beans?\b", r"peas\b", r"pea\b", r"pods?\b"]),
    ("tree_nut", "견과", [
        r"almond", r"walnut", r"pecan", r"hazelnut", r"pistachio", r"macadamia", r"chestnut", r"nuts?\b", r"acorn",
        r"butternut", r"hickory",
    ]),
    ("out_of_scope_crop", "범위 밖 작물", [
        r"cotton", r"grain", r"corn\b", r"maize", r"sorghum", r"millet", r"wheat", r"rice\b", r"soybean",
        r"sunflower", r"sugar ?beet", r"sugarcane", r"cane\b", r"hemp", r"cannabis", r"marijuana", r"hops?\b",
        r"tobacco", r"sod\b", r"grass", r"hay\b", r"forage", r"flower", r"blossom", r"tea\b",
    ]),
]
UNSPEC = "unspecified"
KO = {key: ko for key, ko, _ in GROUPS} | {UNSPEC: "미상"}

# 본문에서는 작물이 아닌 뜻으로 흔히 쓰이는 말이라 세지 않는다(lock nut, filing date, orange color 등).
AMBIGUOUS_IN_TEXT = {
    r"nuts?\b", r"dates?\b", r"orange", r"pods?\b", r"grain", r"cane\b", r"flower", r"blossom", r"tree crop",
    r"limes?\b", r"figs?\b", r"tea\b", r"sod\b", r"hay\b", r"grass", r"pea\b",
}
TEXT_MIN_HITS = 3
TEXT_MIN_SHARE = 0.6

# 범위 밖 작물을 먼저 본다. 'sugar beets'가 뿌리채소로 가지 않게 하려는 것이다.
_ORDER = [GROUPS[-1], *GROUPS[:-1]]
_PATTERNS = [(key, re.compile(r"\b(?:" + "|".join(pats) + ")", re.I)) for key, _, pats in _ORDER]
_TEXT_PATTERNS = [
    (key, re.compile(r"\b(?:" + "|".join(p for p in pats if p not in AMBIGUOUS_IN_TEXT) + ")", re.I))
    for key, _, pats in GROUPS
]


def group_of(name: str) -> str:
    for key, pat in _PATTERNS:
        if pat.search(name):
            return key
    return UNSPEC


def groups_of(names: list[str]) -> list[str]:
    """이름 순서대로, 중복 없이. 구체적인 작물군이 하나라도 있으면 '미상'은 뺀다."""
    out = []
    for n in names:
        g = group_of(n)
        if g not in out:
            out.append(g)
    specific = [g for g in out if g != UNSPEC]
    return specific or [UNSPEC]


def text_group(doc: dict) -> str:
    """대상 이름으로 작물을 특정하지 못한 특허에 쓴다. 제목·청구항·본문에서 작물 이름을 세어, 한 작물군이
    TEXT_MIN_HITS번 이상이고 전체의 TEXT_MIN_SHARE 이상이면 그 작물군, 아니면 '미상'."""
    parts = [doc.get("title", "")] + [c["text"] for c in doc.get("claims", [])] + [b["text"] for b in doc["description"]]
    text = re.sub(r"cherry[- ]picker", " ", " ".join(parts), flags=re.I)
    hits = {key: len(pat.findall(text)) for key, pat in _TEXT_PATTERNS}
    total = sum(hits.values())
    key, top = max(hits.items(), key=lambda kv: kv[1])
    if top >= TEXT_MIN_HITS and top >= TEXT_MIN_SHARE * total:
        return key
    return UNSPEC


def assign(names: list[str], doc: dict | None) -> tuple[list[str], str]:
    """(작물군 목록, 근거). 근거는 '이름', '본문', '미상'."""
    gs = groups_of(names)
    if gs != [UNSPEC]:
        return gs, "이름"
    if doc is not None:
        g = text_group(doc)
        if g != UNSPEC:
            return [g], "본문"
    return [UNSPEC], "미상"


def main() -> None:
    import argparse
    import collections
    import json

    from config import DATA, FULLTEXT_DIR, PROMPT_VERSION

    ap = argparse.ArgumentParser()
    ap.add_argument("--card-run", default="mistral")
    args = ap.parse_args()
    card_dir = DATA / "llm_output" / f"card_{PROMPT_VERSION}" / args.card_run
    first = collections.Counter()
    source = collections.Counter()
    by_text = []
    for f in sorted(card_dir.glob("*.json")):
        out = json.loads(f.read_text(encoding="utf-8")).get("output")
        if not out:
            continue
        doc = json.loads((FULLTEXT_DIR / f.name).read_text(encoding="utf-8"))
        gs, src = assign(out["target_objects"], doc)
        first[KO[gs[0]]] += 1
        source[src] += 1
        if src == "본문":
            by_text.append((f.stem, ";".join(out["target_objects"]), KO[gs[0]], doc["title"][:70]))
    total = sum(first.values())
    print(f"카드 {total}건의 대표 작물군. 근거: {dict(source)}")
    for k, v in first.most_common():
        print(f"  {k}: {v} ({v / total:.0%})")
    print("\n본문 빈도로 정한 특허")
    for row in by_text:
        print("  ", " | ".join(row))


if __name__ == "__main__":
    main()
