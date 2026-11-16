"""로컬 Ollama 호출과 결과 기록. 카드 단계와 매핑 단계가 함께 쓴다."""

from __future__ import annotations

import copy
import json
import time

import requests
from jsonschema import Draft202012Validator

OLLAMA_URL = "http://localhost:11434/api/chat"


def inline_refs(schema: dict) -> dict:
    """$ref를 $defs 내용으로 펼친다. Ollama의 형식 강제가 $ref를 다 처리한다고 보장할 수 없어서다."""
    defs = schema.get("$defs", {})

    def walk(node):
        if isinstance(node, dict):
            if "$ref" in node:
                return walk(copy.deepcopy(defs[node["$ref"].split("/")[-1]]))
            return {k: walk(v) for k, v in node.items() if k not in ("$defs", "$schema")}
        if isinstance(node, list):
            return [walk(v) for v in node]
        return node

    return walk(schema)


class OllamaRunner:
    def __init__(self, model: str, schema: dict, num_ctx: int, num_predict: int, think: bool | None = None, temperature: float = 0.2, repeat_penalty: float | None = None):
        self.model, self.num_ctx, self.num_predict, self.think = model, num_ctx, num_predict, think
        self.temperature = temperature
        self.repeat_penalty = repeat_penalty
        self.validator = Draft202012Validator(schema)
        self.format = inline_refs(schema)

    def run(self, system: str, user: str) -> dict:
        options = {"temperature": self.temperature, "num_ctx": self.num_ctx, "num_predict": self.num_predict, "seed": 42}
        if self.repeat_penalty is not None:
            options["repeat_penalty"] = self.repeat_penalty
        body = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "format": self.format,
            "stream": False,
            "options": options,
        }
        if self.think is not None:  # 생각 모드가 있는 모델(qwen3 등)에만 보낸다. 없는 모델에 보내면 오류가 난다.
            body["think"] = self.think
        t0 = time.time()
        r = requests.post(OLLAMA_URL, json=body, timeout=1800)
        r.raise_for_status()
        res = r.json()
        sec = time.time() - t0

        content = res.get("message", {}).get("content", "")
        parsed, errors = None, []
        try:
            parsed = json.loads(content)
            errors = [f"{'/'.join(map(str, e.path))}: {e.message}" for e in self.validator.iter_errors(parsed)]
        except json.JSONDecodeError as exc:
            errors = [f"JSON 해석 실패: {exc}"]
        prompt_tokens, output_tokens = res.get("prompt_eval_count") or 0, res.get("eval_count") or 0
        return {
            "model": self.model,
            "options": {"num_ctx": self.num_ctx, "num_predict": self.num_predict, "think": self.think, "temperature": self.temperature, "repeat_penalty": self.repeat_penalty},
            "seconds": round(sec, 1),
            "prompt_tokens": prompt_tokens,
            "output_tokens": output_tokens,
            "done_reason": res.get("done_reason"),
            # Ollama는 문맥을 넘는 입력을 알리지 않고 잘라내므로, 입력+출력이 문맥에 닿았는지 따로 남긴다.
            "ctx_full": prompt_tokens + output_tokens >= self.num_ctx - 16,
            "schema_errors": errors,
            "output": parsed,
            "raw": content if parsed is None else None,
            "thinking": res.get("message", {}).get("thinking"),
        }


def run_name(model: str, think: bool | None) -> str:
    return model.replace(":", "_") + ("_think" if think else "")


def progress(i: int, n: int, gid: str, rec: dict) -> str:
    return (f"[{i}/{n}] {gid} {rec['seconds']:.0f}초 입력 {rec['prompt_tokens']} 출력 {rec['output_tokens']} "
            f"종료 {rec['done_reason']} 문맥 초과 {rec['ctx_full']} 스키마 오류 {len(rec['schema_errors'])}")
