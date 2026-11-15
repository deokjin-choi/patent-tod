"""받은 특허 JSON을 위치 표시가 붙은 프롬프트 본문으로 만든다.

입력은 제목, (v3부터) 독립 청구항, 본문(description)이다. 초록과 종속 청구항은 넣지 않는다.
독립 청구항마다 [C1], 본문 문단마다 [P0023] 같은 표시가 붙고, LLM이 낸 근거 인용은 이 표시로 원문과 대조한다.
"""

from __future__ import annotations

import re

from config import BACKGROUND_HEADINGS, BACKGROUND_KEEP_CHARS, CLAIMS_MAX_CHARS, MAX_PATENT_CHARS


def independent_claims(doc: dict) -> list[tuple[str, str]]:
    """(위치 표시, 청구항 문장). 취소된 청구항은 뺀다. 문장 앞의 '1 .' 같은 번호는 지운다."""
    out = []
    for c in doc.get("claims", []):
        if c["dependent"] or "(canceled)" in c["text"].lower():
            continue
        text = re.sub(r"^\s*\d+\s*\.\s*", "", c["text"]).strip()
        out.append((f"[C{c['num']}]", text))
    return out


def claims_lines(doc: dict, cap: int = CLAIMS_MAX_CHARS) -> list[str]:
    lines, used = ["INDEPENDENT CLAIMS"], 0
    for tag, text in independent_claims(doc):
        if used + len(text) > cap:
            lines.append(f"{tag} {text[: max(cap - used, 0)]} [TRUNCATED]")
            break
        lines.append(f"{tag} {text}")
        used += len(text)
    return lines + [""]


def description_lines(blocks: list[dict], background_cap: int | None = None) -> list[str]:
    """background_cap이 있으면 배경기술 절은 그 글자 수까지만 넣는다."""
    lines, in_background, used = [], False, 0
    for b in blocks:
        if b["type"] == "heading":
            in_background = b["text"].upper().startswith(BACKGROUND_HEADINGS)
            lines.append(f"## {b['text']}")
            continue
        if in_background and background_cap is not None:
            if used >= background_cap:
                continue
            used += len(b["text"])
        tag = f"[P{b['num']}] " if b["num"] else ""
        lines.append(f"{tag}{b['text']}")
    return lines


def render_patent(doc: dict, max_chars: int = MAX_PATENT_CHARS, with_claims: bool = False) -> tuple[str, dict]:
    """전체가 max_chars를 넘으면 배경기술 절을 앞부분만 남기고, 그래도 넘으면 본문 뒤를 자른다. 청구항은 자르지 않는다."""
    head = [f"PATENT {doc['google_id']}", f"TITLE: {doc['title']}", ""]
    if with_claims:
        head += claims_lines(doc)
    head += ["DESCRIPTION"]

    meta = {"background_trimmed": False, "truncated": False, "with_claims": with_claims}
    text = "\n".join(head + description_lines(doc["description"]))
    if len(text) > max_chars:
        text = "\n".join(head + description_lines(doc["description"], BACKGROUND_KEEP_CHARS))
        meta["background_trimmed"] = True
    if len(text) > max_chars:
        text = text[:max_chars] + "\n[TRUNCATED]"
        meta["truncated"] = True
    meta["chars"] = len(text)
    return text, meta


def location_index(doc: dict) -> dict[str, str]:
    """위치 표시 -> 원문. 근거 인용 대조에 쓴다."""
    idx = {f"[P{b['num']}]": b["text"] for b in doc["description"] if b["type"] == "para" and b["num"]}
    return idx | dict(independent_claims(doc))
