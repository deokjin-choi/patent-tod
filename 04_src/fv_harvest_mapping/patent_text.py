"""받은 특허 JSON을 위치 표시가 붙은 프롬프트 본문으로 만든다.

입력은 제목과 본문(description)만 쓴다. 초록과 청구항은 넣지 않는다.
본문 문단마다 [P0023] 같은 표시가 붙고, LLM이 낸 근거 인용은 이 표시로 원문과 대조한다.
"""

from __future__ import annotations

from config import BACKGROUND_HEADINGS, BACKGROUND_KEEP_CHARS, MAX_PATENT_CHARS


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


def render_patent(doc: dict, max_chars: int = MAX_PATENT_CHARS) -> tuple[str, dict]:
    """본문이 max_chars를 넘으면 배경기술 절을 앞부분만 남기고, 그래도 넘으면 뒤를 자른다."""
    head = [f"PATENT {doc['google_id']}", f"TITLE: {doc['title']}", "", "DESCRIPTION"]

    meta = {"background_trimmed": False, "truncated": False}
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
    return {f"[P{b['num']}]": b["text"] for b in doc["description"] if b["type"] == "para" and b["num"]}
