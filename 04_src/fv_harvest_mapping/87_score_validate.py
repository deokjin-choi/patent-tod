"""표본 검증 정답과 LLM 판정을 대조한다.

실행:
  conda run -n scenario-space python 87_score_validate.py --run mistral__mistral
"""

from __future__ import annotations

import argparse
import importlib

import pandas as pd

from config import DATA, PROMPT_VERSION

gap = importlib.import_module("80_gap")

KEYS = ["scope_ok", "class_ok", "form_ok", "scale_ok", "F1_ok", "F2_ok", "F3_ok", "F4_ok"]
LABELS = {
    "scope_ok": "범위", "class_ok": "구분(수확장치/부품)", "form_ok": "장치 형태", "scale_ok": "장치 규모",
    "F1_ok": "F1", "F2_ok": "F2", "F3_ok": "F3", "F4_ok": "F4",
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    a = ap.parse_args()
    out = DATA / "llm_output" / f"validate_{PROMPT_VERSION}_{a.run}"
    sample = pd.read_csv(out / "sample.csv")
    gold = pd.read_csv(out / "gold.csv")
    df = sample.merge(gold, on="google_id")
    df["gold_scale"] = [gap.scale(f, pw) for f, pw in zip(df["gold_form"], df["power"])]

    rec = []
    for _, r in df.iterrows():
        llm_scope = "in" if r["scope"] == "fruit_or_vegetable_harvest" else "out"
        rec.append({
            "google_id": r.google_id,
            "title": str(r.title)[:50],
            "scope_ok": llm_scope == r.gold_scope,
            "class_ok": r["class"] == r.gold_class,
            "form_ok": r.form == r.gold_form,
            "scale_ok": r.scale == r.gold_scale,
            "F1_ok": r.F1_rel == r.gold_F1,
            "F2_ok": r.F2_rel == r.gold_F2,
            "F3_ok": r.F3_rel == r.gold_F3,
            "F4_ok": r.F4_rel == r.gold_F4,
            "llm_scope": llm_scope, "gold_scope": r.gold_scope,
            "llm_class": r["class"], "gold_class": r.gold_class,
            "llm_form": r.form, "gold_form": r.gold_form,
            "llm_scale": r.scale, "gold_scale": r.gold_scale,
            "llm_F1": r.F1_rel, "gold_F1": r.gold_F1,
            "llm_F2": r.F2_rel, "gold_F2": r.gold_F2,
            "llm_F3": r.F3_rel, "gold_F3": r.gold_F3,
            "llm_F4": r.F4_rel, "gold_F4": r.gold_F4,
            "note": r.gold_note,
        })
    s = pd.DataFrame(rec)
    s.to_csv(out / "score.csv", index=False, encoding="utf-8-sig")

    print(f"## 표본 {len(s)}건 일치율 (LLM vs 수작업 정답)")
    for k in KEYS:
        print(f"{LABELS[k]}: {s[k].sum()}/{len(s)} ({s[k].mean():.0%})")
    fsum = int(s[["F1_ok", "F2_ok", "F3_ok", "F4_ok"]].sum().sum())
    print(f"F1–F4 칸 합: {fsum}/160 ({fsum / 160:.0%})")
    ins = s[s.scope_ok]
    print(f"범위가 맞은 건만 form: {ins.form_ok.sum()}/{len(ins)} ({ins.form_ok.mean():.0%})")
    print(f"범위가 맞은 건만 scale: {ins.scale_ok.sum()}/{len(ins)} ({ins.scale_ok.mean():.0%})")
    print(f"범위가 맞은 건만 class: {ins.class_ok.sum()}/{len(ins)} ({ins.class_ok.mean():.0%})")
    ghd = s[(s.gold_scope == "in") & (s.gold_class == "harvest_device")]
    print(f"\n정답이 '범위 안 수확 장치'인 {len(ghd)}건")
    for k in KEYS:
        print(f"  {LABELS[k]}: {ghd[k].sum()}/{len(ghd)} ({ghd[k].mean():.0%})")

    print("\n## 틀린 칸")
    for _, r in s.iterrows():
        bad = [LABELS[k] for k in KEYS if not r[k]]
        if bad:
            print(f"{r.google_id}: {', '.join(bad)} | {str(r.note)[:70]}")

    md = [
        f"# 표본 검증 결과 (v4, {len(s)}건)\n",
        "범위 안으로 판정된 수확 장치 320건에서 장치 규모 비율로 층화 추출. 정답은 독립청구항·카드·매핑 패킷을 보고 수작업 판정.\n",
        "## 일치율\n",
        "| 항목 | 일치 | 비율 |",
        "|---|---|---|",
    ]
    for k in KEYS:
        md.append(f"| {LABELS[k]} | {s[k].sum()}/{len(s)} | {s[k].mean():.0%} |")
    md += [
        "", "## 건별\n",
        "| 특허 | 범위 | 구분 | 형태 | 규모 | F1 | F2 | F3 | F4 | 비고 |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for _, r in s.iterrows():
        m = lambda v: "O" if v else "X"
        md.append(
            f"| {r.google_id} | {m(r.scope_ok)} | {m(r.class_ok)} | {m(r.form_ok)} | {m(r.scale_ok)} | "
            f"{m(r.F1_ok)} | {m(r.F2_ok)} | {m(r.F3_ok)} | {m(r.F4_ok)} | {str(r.note)[:40]} |"
        )
    (out / "score.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"\n저장: {out / 'score.md'}")


if __name__ == "__main__":
    main()
