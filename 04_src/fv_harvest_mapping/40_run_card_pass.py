"""카드 단계: 특허 본문(v3부터 독립 청구항 포함)을 LLM에 넣어 과제와 무관한 정리본(card)을 받는다.

실행:
  conda run -n scenario-space python 40_run_card_pass.py --pilot --model mistral
  conda run -n scenario-space python 40_run_card_pass.py --all --model mistral
  conda run -n scenario-space python 40_run_card_pass.py --ids US20110252760A1 --model qwen3:8b --think off --num-ctx 7168
"""

from __future__ import annotations

import argparse
import json

import pandas as pd

from config import DATA, FULLTEXT_DIR, INDEPENDENT_CLAIMS_IN_INPUT, PROMPT_VERSION
from llm_ollama import OllamaRunner, progress, run_name
from patent_text import render_patent
from prompt_build import card_pass

OUT_ROOT = DATA / "llm_output" / f"card_{PROMPT_VERSION}"


def pick_ids(args, ap) -> list[str]:
    if args.pilot:
        return pd.read_csv(DATA / "pilot.csv")["google_id"].tolist()
    if args.ids:
        return args.ids
    if args.all:
        return sorted(p.stem for p in FULLTEXT_DIR.glob("*.json"))
    ap.error("--pilot, --ids, --all 가운데 하나가 필요하다")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", nargs="*", default=None)
    ap.add_argument("--pilot", action="store_true", help="pilot.csv의 특허")
    ap.add_argument("--all", action="store_true", help="본문을 받은 특허 전부")
    ap.add_argument("--model", default="mistral")
    # RTX 4060 8GB에서 전부 GPU에 올라가는 최대 문맥: mistral 10240, llama3 8192, qwen3:8b 7168.
    ap.add_argument("--num-ctx", type=int, default=10240)
    # 카드가 2,048토큰에서 잘리는 특허가 있어 출력을 늘리고, 그만큼 입력을 줄여 mistral 문맥 10240 안에 맞춘다.
    ap.add_argument("--num-predict", type=int, default=2560)
    ap.add_argument("--max-chars", type=int, default=13_000, help="프롬프트에 넣을 특허 텍스트(청구항+본문) 최대 글자 수")
    ap.add_argument("--think", choices=["on", "off"], default=None, help="생각 모드가 있는 모델에서만 지정")
    ap.add_argument("--temperature", type=float, default=0.2)
    ap.add_argument("--repeat-penalty", type=float, default=None)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()
    ids = pick_ids(args, ap)
    think = None if args.think is None else args.think == "on"

    system, schema = card_pass()
    runner = OllamaRunner(args.model, schema, args.num_ctx, args.num_predict, think, args.temperature, args.repeat_penalty)
    out_dir = OUT_ROOT / run_name(args.model, think)
    out_dir.mkdir(parents=True, exist_ok=True)

    for i, gid in enumerate(ids, 1):
        out_path = out_dir / f"{gid}.json"
        if out_path.exists() and not args.overwrite:
            print(f"[{i}/{len(ids)}] {gid} 이미 있음")
            continue
        doc = json.loads((FULLTEXT_DIR / f"{gid}.json").read_text(encoding="utf-8"))
        user, meta = render_patent(doc, max_chars=args.max_chars, with_claims=INDEPENDENT_CLAIMS_IN_INPUT)
        try:
            rec = runner.run(system, user)
        except Exception as exc:  # 한 건의 호출 실패로 긴 실행 전체가 멈추지 않게 한다. 다시 돌리면 이 건부터 이어 간다.
            print(f"[{i}/{len(ids)}] {gid} 호출 실패: {exc}")
            continue
        rec = {"google_id": gid, "prompt_version": PROMPT_VERSION, "input_meta": meta | {"max_chars": args.max_chars}} | rec
        out_path.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        print(progress(i, len(ids), gid, rec))


if __name__ == "__main__":
    main()
