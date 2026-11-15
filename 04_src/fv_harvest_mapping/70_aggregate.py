"""기능·분업 방식 분포 집계.

매핑 결과를 특허 한 건 한 줄의 표(patents.csv)로 펼치고, 범위 안 특허에 대해 아래 표를 만든다(tables.md).

1. F1–F4 관계 비율(직접 수행, 지원, 언급 없음)과 수행 주체가 기계인 비율
2. 수확 장치·부품 기술 구분
3. 분업 방식(기계가 맡는 기능 조합). 수확 장치만
4. 분업 방식 × 작물군, 분업 방식 × 분리 원리, 작물군 × 분리 원리, 분업 방식 × 장치 형태
5. 분업 방식 × CPC 그룹. CPC는 LLM 판정이 아니어서 작물군 판정을 대조하는 기준이 된다

수행 주체는 동력원으로 정한다. 카드의 동력원이 사람 힘뿐인데 LLM이 수행 주체를 발명(invention)이나 둘 다(both)로
적은 경우는 모터가 없으므로 사람(human)으로 고친다(actor_fixed).
작물군은 LLM이 붙인 분류(crop) 대신 대상 이름을 코드 사전으로 묶은 값(crop_group, crop_groups.py)을 쓴다.
작물군과 분리 원리는 여러 값을 가질 수 있다. 교차표에는 첫 값(대표값)만 쓰고, 값이 여럿인 건수는 표 아래에 적는다.

실행:
  conda run -n scenario-space python 70_aggregate.py --run mistral__mistral
  conda run -n scenario-space python 70_aggregate.py --run mistral__mistral --pilot   # 파일럿 8건으로 시험
"""

from __future__ import annotations

import argparse
import importlib
import json

import pandas as pd

import crop_groups
from config import DATA, FULLTEXT_DIR, PROMPT_VERSION, SCOPE_CSV, TASK

derive = importlib.import_module("60_check_output").derive

FUNCS = ("F1", "F2", "F3", "F4")
MACHINE = ("invention", "host_machine", "both")
IN_SCOPE = "fruit_or_vegetable_harvest"
VAGUE = ("not_specified", "not_applicable", "other")
CROP_KO = {
    "tree_fruit": "나무 과일", "vine_or_bush_fruit": "덩굴·관목 과일", "fruiting_vegetable": "열매채소",
    "leafy_vegetable": "잎·줄기채소", "root_vegetable": "뿌리채소", "other_vegetable": "기타 채소",
    "tree_nut": "견과", "grain_or_oilseed": "곡물·유지작물", "forage_or_grass": "사료·잔디",
    "fiber_crop": "섬유작물", "industrial_crop": "공업용 작물", "other": "기타", "not_specified": "명시 없음",
}
DETACH_KO = {
    "cutting": "절단", "twisting": "비틀기", "pulling": "당김", "shaking_or_vibration": "진동",
    "suction_or_pneumatic": "흡입", "digging_or_lifting": "캐기", "combing_or_stripping": "훑기",
    "other": "기타", "not_specified": "명시 없음", "not_applicable": "해당 없음",
}
FORM_KO = {
    "handheld_tool": "손 도구", "walk_behind_or_pushed": "밀거나 끄는 장치", "worker_platform_or_cart": "작업자 플랫폼",
    "tractor_mounted_or_towed": "트랙터 부착", "self_propelled_harvester": "자주식 수확기", "mobile_robot": "이동 로봇",
    "stationary_installation": "고정 설비", "component_only": "부품", "not_specified": "명시 없음",
}
CLASS_KO = {"harvest_device": "수확 장치", "component": "부품 기술", "unmapped": "대응 없음"}
REL_KO = {"direct": "직접 수행", "support": "지원", "not_mentioned": "언급 없음"}


def primary(values: list[str]) -> str:
    """구체적인 첫 값. 구체적인 값이 없으면 첫 값."""
    for v in values:
        if v not in VAGUE:
            return v
    return values[0] if values else "not_specified"


def combo(keys: list[str]) -> str:
    return "F1–F4" if len(keys) == 4 else ("·".join(keys) if keys else "기계 없음")


def patent_rows(run_dir, card_dir, ids) -> pd.DataFrame:
    scope = pd.read_csv(SCOPE_CSV).set_index("google_id")
    rows = []
    for gid in ids:
        mp = run_dir / f"{gid}.json"
        if not mp.exists():
            continue
        mrec = json.loads(mp.read_text(encoding="utf-8"))
        m = mrec["output"]
        card = mrec.get("card_used") or json.loads((card_dir / f"{gid}.json").read_text(encoding="utf-8"))["output"]
        if m is None or card is None:
            continue
        f = m["functions"]
        cls, _ = derive(m)
        human_only = set(card["power_source"]) == {"human_power"}
        if human_only:
            f = {k: v | {"actor": "human"} if v["actor"] in ("invention", "both") else v for k, v in f.items()}
        machine = [k for k in FUNCS if f[k]["relation"] != "not_mentioned" and f[k]["actor"] in MACHINE]
        human = [k for k in FUNCS if f[k]["relation"] != "not_mentioned" and f[k]["actor"] == "human"]
        crops = card["target_categories"]
        detach = m["detachment_principle"]["values"]
        doc = json.loads((FULLTEXT_DIR / f"{gid}.json").read_text(encoding="utf-8"))
        groups, group_src = crop_groups.assign(card["target_objects"], doc)
        s = scope.loc[gid] if gid in scope.index else None
        rows.append({
            "google_id": gid,
            "title": doc["title"],
            "priority_year": str(s["Earliest Priority Date"])[:4] if s is not None else "",
            "cpc_groups": s["scope_groups"] if s is not None else "",
            "scope": m["scope"]["category"],
            "in_scope": m["scope"]["category"] == IN_SCOPE,
            **{f"{k}_rel": f[k]["relation"] for k in FUNCS},
            **{f"{k}_actor": f[k]["actor"] for k in FUNCS},
            "class": cls,
            "machine_does": combo(machine),
            "human_does": combo(human) if human else "",
            "crop": primary(crops),
            "crops_all": ";".join(crops),
            "target_objects": ";".join(card["target_objects"]),
            "crop_group": groups[0],
            "crop_groups_all": ";".join(groups),
            "crop_group_source": group_src,
            "problem_types": ";".join(sorted({x["type"] for x in card["problems"]})),
            "effect_types": ";".join(sorted({x["type"] for x in card["effects"]})),
            "detach": primary(detach),
            "detach_all": ";".join(detach),
            "form": card["form_factor"],
            "power": ";".join(card["power_source"]),
            "actor_fixed": human_only and any(v["actor"] in ("invention", "both") for v in m["functions"].values()),
            "confidence": m["overall_confidence"],
        })
    return pd.DataFrame(rows)


def md(df: pd.DataFrame) -> str:
    df = df.reset_index()
    head = "| " + " | ".join(map(str, df.columns)) + " |"
    sep = "|" + "---|" * len(df.columns)
    body = ["| " + " | ".join(map(str, r)) + " |" for r in df.itertuples(index=False)]
    return "\n".join([head, sep, *body])


LABEL = {"machine_does": "분업 방식", "crop": "작물군(LLM)", "crop_group": "작물군", "detach": "분리 원리", "form": "장치 형태", "cpc": "CPC 그룹", "class": "구분"}


def crosstab(df: pd.DataFrame, row: str, col: str, row_map=None, col_map=None) -> pd.DataFrame:
    """행은 건수가 많은 순, 합계 행은 맨 아래."""
    t = pd.crosstab(df[row].map(row_map or (lambda x: x)), df[col].map(col_map or (lambda x: x)), margins=True, margins_name="합계")
    body = t.drop(index="합계").sort_values("합계", ascending=False)
    t = pd.concat([body, t.loc[["합계"]]])
    t.index.name = LABEL.get(row, row)
    return t


def counts(s: pd.Series, name: str) -> pd.DataFrame:
    t = s.value_counts().rename("건수").to_frame()
    t["비율"] = (t["건수"] / t["건수"].sum() * 100).round(1).astype(str) + "%"
    t.index.name = name
    return t


def tables(p: pd.DataFrame) -> str:
    out = []
    n_all = len(p)
    ins = p[p["in_scope"]]
    dev = ins[ins["class"] == "harvest_device"]
    out.append(f"# 기능·분업 방식 분포 ({PROMPT_VERSION})\n")
    out.append(f"매핑된 특허 {n_all}건 가운데 범위 안 {len(ins)}건, 그 가운데 수확 장치 {len(dev)}건. 모두 LLM 판정이며 표본 검증 전이다.\n")

    out.append("## 0. 범위 판정\n")
    out.append(md(counts(p["scope"], "범위 분류")))

    out.append("\n## 1. F1–F4 관계 비율 (범위 안)\n")
    rel = pd.DataFrame({k: ins[f"{k}_rel"].value_counts() for k in FUNCS}).T.reindex(columns=list(REL_KO)).fillna(0).astype(int)
    rel.columns = [REL_KO[c] for c in rel.columns]
    share = (rel.div(rel.sum(axis=1), axis=0) * 100).round(1)
    rel_tbl = rel.astype(str) + " (" + share.astype(str) + "%)"
    rel_tbl["기계 수행"] = [
        f"{((ins[f'{k}_rel'] != 'not_mentioned') & ins[f'{k}_actor'].isin(MACHINE)).sum()}" for k in FUNCS
    ]
    rel_tbl.index.name = "기능"
    out.append(md(rel_tbl))
    out.append("\n기계 수행: 직접 수행 또는 지원이면서 수행 주체가 기계(발명 또는 발명이 달리는 기계)인 건수.\n")

    out.append("\n## 2. 수확 장치·부품 기술 (범위 안)\n")
    out.append(md(counts(ins["class"].map(CLASS_KO), "구분")))

    out.append("\n## 3. 분업 방식 (수확 장치, 기계가 맡는 기능 조합)\n")
    out.append(md(counts(dev["machine_does"], "분업 방식")))

    out.append("\n## 4-1. 분업 방식 × 작물군 (수확 장치)\n")
    out.append(md(crosstab(dev, "machine_does", "crop_group", col_map=crop_groups.KO.get)))
    src = dev["crop_group_source"].value_counts().to_dict()
    out.append(f"\n작물군이 여럿인 특허: {(dev['crop_groups_all'].str.count(';') > 0).sum()}건(첫 값으로 셈). "
               f"작물군 근거: {src}('본문'은 대상 이름이 'fruit'처럼 일반어여서 본문의 작물 이름 빈도로 정한 것).\n")

    out.append("\n## 4-2. 분업 방식 × 분리 원리 (수확 장치)\n")
    out.append(md(crosstab(dev, "machine_does", "detach", col_map=DETACH_KO.get)))
    out.append(f"\n분리 원리가 여럿인 특허: {(dev['detach_all'].str.count(';') > 0).sum()}건(첫 값으로 셈).\n")

    out.append("\n## 4-3. 작물군 × 분리 원리 (수확 장치)\n")
    out.append(md(crosstab(dev, "crop_group", "detach", row_map=crop_groups.KO.get, col_map=DETACH_KO.get)))

    out.append("\n## 4-4. 분업 방식 × 장치 형태 (수확 장치)\n")
    out.append(md(crosstab(dev, "machine_does", "form", col_map=FORM_KO.get)))

    out.append("\n## 5. CPC 그룹별 (범위 안)\n")
    cpc = ins.assign(cpc=ins["cpc_groups"].str.split(";")).explode("cpc").reset_index(drop=True)
    out.append(md(crosstab(cpc, "cpc", "class", col_map=CLASS_KO.get)))
    out.append("\n두 그룹 이상에 걸친 특허는 각 그룹에 한 번씩 센다.\n")
    out.append("\n## 5-1. CPC 그룹 × 작물군 (범위 안). 작물군 판정 대조용\n")
    out.append(md(crosstab(cpc, "cpc", "crop_group", col_map=crop_groups.KO.get)))
    return "\n".join(out) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, help="매핑 폴더 이름, 예: mistral__mistral")
    ap.add_argument("--pilot", action="store_true", help="파일럿 8건만")
    args = ap.parse_args()
    run_dir = DATA / "llm_output" / f"mapping_{TASK}_{PROMPT_VERSION}" / args.run
    card_dir = DATA / "llm_output" / f"card_{PROMPT_VERSION}" / args.run.split("__")[0]
    ids = (pd.read_csv(DATA / "pilot.csv")["google_id"].tolist() if args.pilot
           else sorted(p.stem for p in run_dir.glob("*.json")))

    p = patent_rows(run_dir, card_dir, ids)
    out_dir = DATA / "llm_output" / f"aggregate_{PROMPT_VERSION}_{args.run}{'_pilot' if args.pilot else ''}"
    out_dir.mkdir(parents=True, exist_ok=True)
    p.to_csv(out_dir / "patents.csv", index=False, encoding="utf-8-sig")
    text = tables(p)
    (out_dir / "tables.md").write_text(text, encoding="utf-8")
    print(text)
    print(f"저장: {out_dir}")


if __name__ == "__main__":
    main()
