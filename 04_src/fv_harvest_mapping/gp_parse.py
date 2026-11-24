"""Google Patents 특허 페이지 HTML에서 서지, 초록, 청구항, 본문을 뽑는다."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup, Tag

_WS = re.compile(r"\s+")
_PARA_CLASSES = {"description-paragraph", "description-line"}


def _text(node: Tag) -> str:
    return _WS.sub(" ", node.get_text(" ", strip=True)).strip()


def _itemprop(soup: BeautifulSoup, name: str) -> str:
    node = soup.find(attrs={"itemprop": name})
    if node is None:
        return ""
    return (node.get("datetime") or _text(node)).strip()


def _claim_num(raw: str) -> str:
    """'00003' -> '3', '001-8' -> '1-8'. 삭제된 청구항은 범위로 묶여 올 때가 있다."""
    parts = [p.lstrip("0") or "0" for p in raw.split("-")]
    return "-".join(parts)


def _claims(soup: BeautifulSoup) -> list[dict]:
    section = soup.find("section", attrs={"itemprop": "claims"})
    if section is None:
        return []
    nodes = [n for n in section.find_all("div", class_="claim") if n.get("num")]
    strip_src = False
    if not nodes:
        # 중국어 원문과 영어 번역이 <claim>으로 올 때는 div.claim이 없다.
        nodes = [n for n in section.find_all("claim") if n.get("num")]
        strip_src = True
    out = []
    for node in nodes:
        if strip_src:
            for src in node.select(".google-src-text"):
                src.decompose()
        refs = sorted({r.get("idref", "") for r in node.find_all("claim-ref") if r.get("idref")})
        text = _text(node)
        dependent = bool(refs) or "according to claim" in text.lower()
        out.append({
            "num": _claim_num(node.get("num")),
            "text": text,
            "dependent": dependent,
            "refs": [_claim_num(r.split("-", 1)[-1]) for r in refs if r.startswith("CLM-")],
        })
    return out


def _para_num(raw: str | None) -> str | None:
    """'0045', 'p-0045' -> '0045'. 소제목에 붙는 '0000'과 'h-0003'은 번호 없음으로 둔다(번호가 겹친다)."""
    if not raw or raw.startswith("h-"):
        return None
    digits = re.sub(r"\D", "", raw)
    return digits if digits and set(digits) != {"0"} else None


def _description(soup: BeautifulSoup) -> list[dict]:
    section = soup.find("section", attrs={"itemprop": "description"})
    if section is None:
        return []
    blocks: list[dict] = []
    for node in section.find_all(["heading", "div"]):
        if node.name == "heading":
            blocks.append({"type": "heading", "num": None, "text": _text(node)})
            continue
        classes = set(node.get("class") or [])
        if not classes & _PARA_CLASSES:
            continue
        if node.find_parent("div", class_=list(_PARA_CLASSES)) is not None:
            continue
        blocks.append({"type": "para", "num": _para_num(node.get("num")), "text": _text(node)})
    if not blocks:
        text = _text(section)
        if text:
            blocks.append({"type": "para", "num": None, "text": text})
    return blocks


def parse_patent_html(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    title_node = soup.find("span", attrs={"itemprop": "title"})
    abstract_node = soup.find("section", attrs={"itemprop": "abstract"})
    abstract = ""
    if abstract_node is not None:
        inner = abstract_node.find("div", class_="abstract")
        abstract = _text(inner or abstract_node)
    return {
        "publication_number": _itemprop(soup, "publicationNumber"),
        "title": _text(title_node) if title_node else "",
        "priority_date": _itemprop(soup, "priorityDate"),
        "filing_date": _itemprop(soup, "filingDate"),
        "publication_date": _itemprop(soup, "publicationDate"),
        "assignee_original": _itemprop(soup, "assigneeOriginal"),
        "abstract": abstract,
        "claims": _claims(soup),
        "description": _description(soup),
    }
