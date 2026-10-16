"""Shared helpers: IO, keyword counts, cell encoding, numeric utils."""

from __future__ import annotations

import csv
import json
import math
import re
from itertools import product
from pathlib import Path
from typing import Any

import numpy as np

from config import DATA, DICTIONARY, OUT


def ensure_out() -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    return OUT


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", errors="replace", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def load_dictionary() -> dict:
    return load_json(DICTIONARY)


def axis_order(d: dict) -> list[str]:
    return list(d["axes"].keys())


def levels_of(d: dict, axis: str) -> list[str]:
    return list(d["axes"][axis]["levels"].keys())


def all_cells(d: dict) -> list[tuple[str, ...]]:
    axes = axis_order(d)
    return list(product(*(levels_of(d, a) for a in axes)))


def cell_name(axes: list[str], cell: tuple[str, ...]) -> str:
    return "|".join(f"{a}={v}" for a, v in zip(axes, cell))


def vocab_entries(d: dict) -> list[dict]:
    """Flat list: one row per phrase, tagged with axis, level, origin."""
    rows = []
    for axis, spec in d["axes"].items():
        for level, lv in spec["levels"].items():
            origin = f"{axis}:{level}"
            for phrase in lv["phrases"]:
                rows.append(
                    {
                        "term_id": f"{axis}.{level}.{phrase}",
                        "axis": axis,
                        "level": level,
                        "origin": origin,
                        "phrase": phrase,
                    }
                )
    return rows


def compile_phrase(phrase: str) -> re.Pattern[str]:
    """Short tokens use word boundaries; multi-word phrases use escaped substring."""
    p = phrase.lower().strip()
    if " " in p or "-" in p:
        return re.compile(re.escape(p), re.IGNORECASE)
    return re.compile(r"\b" + re.escape(p) + r"\b", re.IGNORECASE)


def count_phrase(text: str, pat: re.Pattern[str]) -> int:
    return len(pat.findall(text))


def patent_text(row: dict) -> str:
    return f"{row.get('title') or ''}\n{row.get('abstract') or ''}"


def cpc_flags(cpc_field: str, prefixes: list[str]) -> dict[str, int]:
    codes = [c.strip() for c in (cpc_field or "").replace(",", ";;").split(";;") if c.strip()]
    flags = {f"cpc_{p}": 0 for p in prefixes}
    for code in codes:
        for p in prefixes:
            if code.startswith(p):
                flags[f"cpc_{p}"] = 1
    return flags


def logsumexp(a: np.ndarray, axis: int | None = None, keepdims: bool = False) -> np.ndarray:
    a = np.asarray(a, dtype=float)
    m = np.max(a, axis=axis, keepdims=True)
    out = m + np.log(np.sum(np.exp(a - m), axis=axis, keepdims=True))
    if not keepdims and axis is not None:
        out = np.squeeze(out, axis=axis)
    return out


def entropy(p: np.ndarray) -> float:
    q = np.asarray(p, dtype=float)
    q = q[q > 0]
    if q.size == 0:
        return 0.0
    q = q / q.sum()
    return float(-np.sum(q * np.log(q)))


def hamming(a: tuple, b: tuple) -> int:
    return sum(x != y for x, y in zip(a, b))
