"""카드의 청구항 표시(claim)를 원문 독립 청구항과 대조해 바로잡는다(v4부터).

모델은 본문에만 나오는 부품에도 청구항 번호를 붙인다. 그래서 매핑 전에 코드로 다시 판정한다.
부품 이름(기능은 means, 구성요소는 name)의 내용어 가운데 절반 이상이 한 독립 청구항에 있으면 청구항 안으로 보고,
아니면 none으로 바꾼다. "system", "unit"처럼 어디에나 붙는 말은 내용어로 치지 않는다.
부품 이름에 내용어가 없을 때("by hand" 등)만 근거 인용이 독립 청구항 문장 안에 그대로 있는지로 판정한다.
인용만으로 판정하지 않는 까닭은, 모델이 청구항 첫머리 문장을 아무 기능의 근거로나 끌어오기 때문이다.

청구항 안으로 볼 때는 실제로 맞은 청구항 번호로 고쳐 적는다.
"""

from __future__ import annotations

import copy
import re

from patent_text import independent_claims

STOPWORDS = {
    "the", "and", "for", "with", "from", "into", "onto", "its", "their", "each", "one", "two",
    "by", "of", "a", "an", "to", "in", "on", "at", "or", "not", "specified", "hand", "means",
    "system", "unit", "device", "assembly", "member", "element", "apparatus", "mechanism", "portion", "part",
}


def _norm(s: str) -> str:
    return re.sub(r"\s+", "", s.lower())


def _stem(w: str) -> str:
    return w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w


def _words(s: str) -> set[str]:
    return {_stem(w) for w in re.findall(r"[a-z]+", s.lower()) if len(w) >= 3 and w not in STOPWORDS}


def _match(part: str, evidence: list[dict], claims: list[tuple[str, str]]) -> str:
    """맞는 청구항 번호, 없으면 'none'."""
    words = _words(part)
    if words:
        for tag, text in claims:
            if len(words & _words(text)) * 2 >= len(words):
                return tag
        return "none"
    for ev in evidence:
        q = _norm(ev["quote"])
        for tag, text in claims:
            if q and q in _norm(text):
                return tag
    return "none"


def verify_claims(card: dict, doc: dict) -> tuple[dict, list[dict]]:
    """(바로잡은 카드, 바뀐 항목 기록)."""
    claims = independent_claims(doc)
    out, changes = copy.deepcopy(card), []
    for f in out["functions"]:
        new = _match(f["means"], f["evidence"], claims)
        if new != f["claim"]:
            changes.append({"where": f"function {f['id']}", "part": f["means"], "from": f["claim"], "to": new})
            f["claim"] = new
    for c in out["components"]:
        new = _match(c["name"], [], claims)
        if new != c["claim"]:
            changes.append({"where": "component", "part": c["name"], "from": c["claim"], "to": new})
            c["claim"] = new
    return out, changes
