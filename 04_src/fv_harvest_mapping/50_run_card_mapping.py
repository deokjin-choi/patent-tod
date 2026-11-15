"""매핑 단계: 저장해 둔 카드만 LLM에 넣어 과제 기능공간(F1–F4)에 대응시킨다.

카드를 만든 모델과 매핑하는 모델이 달라도 된다. 입력이 짧아서 생각 모드를 켤 여유가 있다.
v4부터는 카드의 청구항 표시를 원문 독립 청구항과 대조해 바로잡은 뒤 넘긴다. 바로잡은 내역과 넘긴 카드를 출력에 함께 남긴다.
v5는 매핑 프롬프트만 바뀌므로, 이미 만든 v4 카드를 `--card-version v4`로 다시 쓸 수 있다.
특허마다 F1–F4 채움 순서를 무작위로 넣어 프롬프트를 다시 조립한다(`fill_order`로 기록).

실행:
  conda run -n scenario-space python 50_run_card_mapping.py --card-run mistral --pilot --model mistral
  conda run -n scenario-space python 50_run_card_mapping.py --card-run mistral --card-version v4 --pilot --model mistral --overwrite --seed 42
"""

from __future__ import annotations

import argparse
import json
import random

import pandas as pd

from claim_check import verify_claims
from config import DATA, FULLTEXT_DIR, PROMPT_VERSION, TASK, VERIFY_CLAIM_TAGS
from llm_ollama import OllamaRunner, progress, run_name
from prompt_build import card_mapping

OUT_ROOT = DATA / "llm_output" / f"mapping_{TASK}_{PROMPT_VERSION}"


def card_message(gid: str, title: str, card: dict) -> str:
    return f"PATENT {gid}\nTITLE: {title}\n\nPATENT CARD\n{json.dumps(card, ensure_ascii=False, indent=1)}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--card-run", required=True, help="card_{버전} 아래 카드 폴더 이름, 예: mistral")
    ap.add_argument("--card-version", default=PROMPT_VERSION, help="카드를 읽을 프롬프트 버전. v5 매핑에 v4 카드를 쓰려면 v4")
    ap.add_argument("--ids", nargs="*", default=None)
    ap.add_argument("--pilot", action="store_true", help="pilot.csv의 특허")
    ap.add_argument("--model", default="mistral")
    ap.add_argument("--num-ctx", type=int, default=7168)
    ap.add_argument("--num-predict", type=int, default=1536)
    ap.add_argument("--think", choices=["on", "off"], default=None, help="생각 모드가 있는 모델에서만 지정")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--seed", type=int, default=None, help="채움 순서 난수 시드. 주면 특허마다 seed+공개번호로 순서를 정해 재현 가능하다")
    args = ap.parse_args()
    think = None if args.think is None else args.think == "on"

    card_dir = DATA / "llm_output" / f"card_{args.card_version}" / args.card_run
    if args.pilot:
        ids = pd.read_csv(DATA / "pilot.csv")["google_id"].tolist()
    elif args.ids:
        ids = args.ids
    else:
        ids = sorted(p.stem for p in card_dir.glob("*.json"))

    # 스키마는 버전마다 같으므로 한 번만 읽고, 시스템 문구의 채움 순서만 특허마다 바꾼다.
    _, schema, _ = card_mapping()
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
        doc = json.loads((FULLTEXT_DIR / f"{gid}.json").read_text(encoding="utf-8"))
        extra = {}
        if VERIFY_CLAIM_TAGS:
            card, changes = verify_claims(card, doc)
            extra = {"claim_fixes": changes, "card_used": card}
        rng = random.Random(f"{args.seed}:{gid}") if args.seed is not None else None
        system, _, fill_order = card_mapping(rng=rng)
        try:
            rec = runner.run(system, card_message(gid, doc["title"], card))
        except Exception as exc:  # 한 건의 호출 실패로 긴 실행 전체가 멈추지 않게 한다. 다시 돌리면 이 건부터 이어 간다.
            print(f"[{i}/{len(ids)}] {gid} 호출 실패: {exc}")
            continue
        rec = {
            "google_id": gid,
            "prompt_version": PROMPT_VERSION,
            "task": TASK,
            "card_run": args.card_run,
            "card_version": args.card_version,
            "fill_order": fill_order,
        } | extra | rec
        out_path.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        print(progress(i, len(ids), gid, rec), f"채움 {'.'.join(fill_order)}")


if __name__ == "__main__":
    main()
