"""프롬프트와 출력 스키마를 조립한다.

- 카드 단계(card pass): 특허 본문을 읽고 과제와 무관한 정리본(card)을 낸다. 기능공간은 보여주지 않는다.
- 매핑 단계(card mapping): 저장해 둔 카드만 읽고 과제 기능공간에 대응시킨다.
  v5부터는 호출마다 F1–F4 채움 순서를 무작위로 넣어, 고정 순서에 따른 위치 편향을 줄인다.

Ollama는 출력 스키마를 형식 강제에만 쓰고 프롬프트에 넣어주지 않는다. 그래서 스키마의 선택지(enum)와 그 정의를
`labels_{버전}.json`에서 읽어 프롬프트의 {{OPTIONS}} 자리에 붙인다. 스키마와 정의 파일의 선택지가 다르면 멈춘다.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from config import PROMPT_DIR, PROMPT_VERSION, TASK

SUBFUNCTIONS = ("F1", "F2", "F3", "F4")


def _dir() -> Path:
    return PROMPT_DIR / PROMPT_VERSION


def _read(name: str) -> str:
    return (_dir() / name).read_text(encoding="utf-8").strip()


def _schema(name: str) -> dict:
    return json.loads(_read(name))


def enum_paths(schema: dict) -> dict[str, list[str]]:
    """선택지가 있는 칸의 경로 -> 선택지. $defs 안의 칸은 'def이름.칸'으로 적는다."""
    out: dict[str, list[str]] = {}

    def walk(node: dict, path: str) -> None:
        if "enum" in node:
            out[path] = node["enum"]
            return
        if node.get("type") == "array" and isinstance(node.get("items"), dict):
            walk(node["items"], path)
        for key, child in node.get("properties", {}).items():
            walk(child, f"{path}.{key}" if path else key)

    walk(schema, "")
    for name, body in schema.get("$defs", {}).items():
        walk(body, name)
    return out


def _options(schema: dict) -> str:
    labels = json.loads(_read(f"labels_{PROMPT_VERSION}.json"))
    blocks = []
    for path, values in enum_paths(schema).items():
        entry = labels.get(path)
        if entry is None or set(entry["values"]) != set(values):
            raise ValueError(f"선택지 정의가 스키마와 다르다: {path}")
        lines = [f"**{entry['title']}**"]
        lines += [f"- `{v}`: {entry['values'][v]}" for v in values]
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def card_pass() -> tuple[str, dict]:
    """(시스템 프롬프트, 카드 스키마)."""
    schema = _schema(f"card_{PROMPT_VERSION}.schema.json")
    system = _read("card_pass.md").replace("{{OPTIONS}}", _options(schema))
    return system, schema


def shuffle_fill_order(rng: random.Random | None = None) -> list[str]:
    """F1–F4 채움 순서를 한 번 섞는다."""
    order = list(SUBFUNCTIONS)
    (rng or random).shuffle(order)
    return order


def format_fill_order(order: list[str]) -> str:
    """프롬프트에 넣을 채움 순서 문구. 예: F2, then F4, then F1, then F3"""
    return ", then ".join(order)


def card_mapping(
    task: str = TASK,
    fill_order: list[str] | None = None,
    rng: random.Random | None = None,
) -> tuple[str, dict, list[str]]:
    """(시스템 프롬프트, 매핑 스키마, 이번 호출의 채움 순서).

    fill_order를 주지 않으면 호출마다 F1–F4 순서를 무작위로 정한다.
    """
    schema = _schema(f"mapping_{task}_{PROMPT_VERSION}.schema.json")
    order = list(fill_order) if fill_order is not None else shuffle_fill_order(rng)
    if sorted(order) != sorted(SUBFUNCTIONS):
        raise ValueError(f"채움 순서가 F1–F4가 아니다: {order}")
    system = (
        _read("card_mapping.md")
        .replace("{{FUNCTION_SPACE}}", _read(f"function_space_{task}.md"))
        .replace("{{OPTIONS}}", _options(schema))
        .replace("{{FILL_ORDER}}", format_fill_order(order))
    )
    return system, schema, order
