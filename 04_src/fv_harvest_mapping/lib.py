"""공용 함수: CPC 판정, Lens 번호 변환."""

from __future__ import annotations

import re

import pandas as pd

from config import SCOPE_GROUPS


def split_codes(cpc: object, ipc: object) -> list[str]:
    """Lens의 CPC·IPCR 칸을 합쳐 공백 없는 분류 기호 목록으로 만든다."""
    codes: list[str] = []
    for cell in (cpc, ipc):
        if isinstance(cell, str) and cell:
            codes.extend(c.strip().replace(" ", "") for c in cell.split(";;") if c.strip())
    return sorted(set(codes))


def scope_groups_of(codes: list[str]) -> list[str]:
    """분류 기호 목록이 속하는 범위 그룹 이름들. 제외 접두에 걸린 기호는 세지 않는다."""
    hits = []
    for name, rule in SCOPE_GROUPS.items():
        for code in codes:
            if any(code.startswith(p) for p in rule["exclude"]):
                continue
            if any(code.startswith(p) for p in rule["include"]):
                hits.append(name)
                break
    return hits


_APP = re.compile(r"^US (\d{4})/(\d{7}) ([A-Z]\d?)$")
_OTHER = re.compile(r"^US ((?:PP|RE|D)?\d+) ([A-Z]\d?)$")


def lens_to_google(display_key: str) -> str:
    """Lens Display Key를 Google Patents 공개번호로 바꾼다.

    US 2024/0415055 A1 -> US20240415055A1
    US 11234567 B2     -> US11234567B2
    US PP12345 P2      -> USPP12345P2
    US D912345 S       -> USD912345S
    """
    key = display_key.strip()
    m = _APP.match(key)
    if m:
        return f"US{m.group(1)}{m.group(2)}{m.group(3)}"
    m = _OTHER.match(key)
    if m:
        return f"US{m.group(1)}{m.group(2)}"
    raise ValueError(f"알 수 없는 번호 형식: {display_key!r}")


def read_source(path) -> pd.DataFrame:
    cols = [
        "Lens ID", "Display Key", "Kind", "Document Type", "Title", "Abstract",
        "Applicants", "Earliest Priority Date", "Publication Date", "Has Full Text",
        "Simple Family Size", "CPC Classifications", "IPCR Classifications",
    ]
    return pd.read_csv(path, usecols=cols, low_memory=False)
