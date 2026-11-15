"""표본 특허마다 사람이 보기 쉬운 검증 패킷을 만든다.

실행:
  conda run -n scenario-space python 86_validate_pack.py --run mistral__mistral
"""

from __future__ import annotations

import argparse
import json
import textwrap

import pandas as pd

from config import DATA, FULLTEXT_DIR, PROMPT_VERSION, TASK
from patent_text import independent_claims


def pack(gid: str, row, card, mapping, doc) -> str:
    claims = independent_claims(doc)
    claim_txt = "\n".join(f"{t} {textwrap.shorten(c, 280, placeholder='…')}" for t, c in claims[:3]) or "(독립청구항 없음)"
    funcs = "\n".join(
        f"  {fn['id']}. {fn['verb']} {fn['object']} | actor={fn['actor']} claim={fn.get('claim')} means={textwrap.shorten(fn.get('means',''), 80)}"
        for fn in card["functions"][:10]
    )
    mf = mapping["functions"]
    map_lines = "\n".join(
        f"  {k}: {mf[k]['relation']} / {mf[k]['actor']} / card={mf[k].get('card_functions')} / "
        f"{textwrap.shorten((mf[k].get('evidence') or [{}])[0].get('quote',''), 100)}"
        for k in ("F1", "F2", "F3", "F4")
    )
    problems = "; ".join(p["statement"] for p in card.get("problems", [])[:2])
    return f"""# {gid}  {doc['title']}
LLM: scope={mapping['scope']['category']} | class={row['class']} | machine={row['machine_does']} | form={row['form']} | power={row['power']} | scale={row['scale']} | crop={row['crop_group']}({row['crop_group_source']}) | detach={row['detach']} | conf={row['confidence']}
targets={card['target_objects']} | LLM crop cats={card['target_categories']}
problems: {problems}

## 독립청구항
{claim_txt}

## 카드 기능
{funcs}

## 매핑
{map_lines}
scope reason: {textwrap.shorten(mapping['scope'].get('reason',''), 240)}
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    a = ap.parse_args()
    out_dir = DATA / "llm_output" / f"validate_{PROMPT_VERSION}_{a.run}"
    sample = pd.read_csv(out_dir / "sample.csv")
    card_dir = DATA / "llm_output" / f"card_{PROMPT_VERSION}" / a.run.split("__")[0]
    map_dir = DATA / "llm_output" / f"mapping_{TASK}_{PROMPT_VERSION}" / a.run
    packs = []
    for r in sample.itertuples():
        mrec = json.loads((map_dir / f"{r.google_id}.json").read_text(encoding="utf-8"))
        card = mrec.get("card_used") or json.loads((card_dir / f"{r.google_id}.json").read_text(encoding="utf-8"))["output"]
        mapping = mrec["output"]
        doc = json.loads((FULLTEXT_DIR / f"{r.google_id}.json").read_text(encoding="utf-8"))
        packs.append(pack(r.google_id, sample.loc[r.Index], card, mapping, doc))
    text = "\n---\n".join(packs)
    (out_dir / "packs.md").write_text(text, encoding="utf-8")
    print(f"{len(packs)}건 → {out_dir / 'packs.md'} ({len(text):,}자)")


if __name__ == "__main__":
    main()
