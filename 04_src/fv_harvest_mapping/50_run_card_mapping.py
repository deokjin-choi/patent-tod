"""매핑 단계: 저장해 둔 카드만 LLM에 넣어 과제 기능공간(F1–F4)에 대응시킨다.

카드를 만든 모델과 매핑하는 모델이 달라도 된다. 입력이 짧아서 생각 모드를 켤 여유가 있다.

실행:
  conda run -n scenario-space python 50_run_card_mapping.py --card-run mistral --pilot --model mistral
  conda run -n scenario-space python 50_run_card_mapping.py --card-run qwen3_8b --pilot --model qwen3:8b --think on --num-ctx 7168
"""

from __future__ import annotations

import argparse
import json

import pandas as pd

from config import DATA, FULLTEXT_DIR, PROMPT_VERSION, TASK
from llm_ollama import OllamaRunner, progress, run_name
from prompt_build import card_mapping

CARD_ROOT = DATA / "llm_output" / f"card_{PROMPT_VERSION}"
OUT_ROOT = DATA / "llm_output" / f"mapping_{TASK}_{PROMPT_VERSION}"


def card_message(gid: str, title: str, card: dict) -> str:
    return f"PATENT {gid}\nTITLE: {title}\n\nPATENT CARD\n{json.dumps(card, ensure_ascii=False, indent=1)}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--card-run", required=True, help="card_v2 아래 카드 폴더 이름, 예: mistral")
    ap.add_argument("--ids", nargs="*", default=None)
    ap.add_argument("--pilot", action="store_true", help="pilot.csv의 특허")
    ap.add_argument("--model", default="mistral")
    ap.add_argument("--num-ctx", type=int, default=7168)
    ap.add_argument("--num-predict", type=int, default=1536)
    ap.add_argument("--think", choices=["on", "off"], default=None, help="생각 모드가 있는 모델에서만 지정")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()
    think = None if args.think is None else args.think == "on"

    card_dir = CARD_ROOT / args.card_run
    if args.pilot:
        ids = pd.read_csv(DATA / "pilot.csv")["google_id"].tolist()
    elif args.ids:
        ids = args.ids
    else:
        ids = sorted(p.stem for p in card_dir.glob("*.json"))

    system, schema = card_mapping()
    runner = OllamaRunner(args.model, schema, args.num_ctx, args.num_predict, think)
    out_dir = OUT_ROOT / f"{args.card_run}__{run_name(args.model, think)}"
    out_dir.mkdir(parents=True, exist_ok=True)

    for i, gid in enumerate(ids, 1):
        out_path = out_dir / f"{gid}.json"
        if out_path.exists() and not args.overwrite:
            print(f"[{i}/{len(ids)}] {gid} 이미 있음")
            continue
        card = json.loads((card_dir / f"{gid}.json").read_text(encoding="utf-8"))["output"]
        if card is None:
            print(f"[{i}/{len(ids)}] {gid} 카드가 없음(카드 단계 실패)")
            continue
        title = json.loads((FULLTEXT_DIR / f"{gid}.json").read_text(encoding="utf-8"))["title"]
        rec = runner.run(system, card_message(gid, title, card))
        rec = {"google_id": gid, "prompt_version": PROMPT_VERSION, "task": TASK, "card_run": args.card_run} | rec
        out_path.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        print(progress(i, len(ids), gid, rec))


if __name__ == "__main__":
    main()
