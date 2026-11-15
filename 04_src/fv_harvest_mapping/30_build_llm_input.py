"""받은 특허 본문을 카드 단계 LLM 입력(시스템 프롬프트, 특허 본문, 출력 스키마)으로 만든다.

LLM 호출 없이 입력만 확인할 때 쓴다. 실제 호출은 40_run_card_pass.py가 같은 함수로 입력을 만든다.

실행:
  conda run -n scenario-space python 30_build_llm_input.py --ids US20110252760A1
  conda run -n scenario-space python 30_build_llm_input.py            # 받은 것 전부
"""

from __future__ import annotations

import argparse
import json

from config import FULLTEXT_DIR, INDEPENDENT_CLAIMS_IN_INPUT, LLM_INPUT_DIR, PROMPT_VERSION
from patent_text import render_patent
from prompt_build import card_pass


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", nargs="*", default=None)
    args = ap.parse_args()

    system, schema = card_pass()
    files = sorted(FULLTEXT_DIR.glob("*.json"))
    if args.ids:
        files = [f for f in files if f.stem in set(args.ids)]
    LLM_INPUT_DIR.mkdir(parents=True, exist_ok=True)

    for f in files:
        doc = json.loads(f.read_text(encoding="utf-8"))
        user, meta = render_patent(doc, with_claims=INDEPENDENT_CLAIMS_IN_INPUT)
        out = {
            "google_id": doc["google_id"],
            "prompt_version": PROMPT_VERSION,
            "system": system,
            "user": user,
            "schema": schema,
            "meta": meta,
        }
        (LLM_INPUT_DIR / f"{doc['google_id']}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        (LLM_INPUT_DIR / f"{doc['google_id']}.user.txt").write_text(user, encoding="utf-8")
        print(f"{doc['google_id']} 본문 {meta['chars']:,}자 배경 줄임 {meta['background_trimmed']} 잘림 {meta['truncated']}")
    print(f"시스템 프롬프트 {len(system):,}자")


if __name__ == "__main__":
    main()
