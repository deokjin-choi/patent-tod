"""분업 방식 패턴 점검과 저개발 기능 조합 탐색 (method.md 5절).

분석 단위는 범위 안 수확 장치(F3를 직접 수행)다. 작물군은 crop_groups.py, 분리 원리는 매핑 결과를 쓴다.

A. 분업 방식마다 구별되는 기술개발 패턴이 있는가
  A1 분업 방식별 프로필
  A2 분업 방식과 작물군·분리 원리·장치 형태·규모·출원 시기의 연관(크래머 V, 순열 검정).
     작물군 구성이 달라서 생긴 연관인지 보려고, 작물군 안에서만 섞는 조건부 검정을 함께 낸다
B. 그 패턴이 소농의 노동 문제와 이어지는가
  B1 기능별 기계 수행 비율을 장치 규모별로
  B2 장치 규모별로 사람 몫으로 남는 기능과, 특허가 스스로 내세운 노동·안전 문제의 비율
C. 저개발 칸 (method.md 5.2–5.7)
  C1 작물군 × 분리 원리 × 분업 방식 칸: 관측/기대, 공백·저개발, 출원 시기, 이웃 조건, 채울 수 있는지, 민감도
  C2 사다리 공백
  C3 규모 공백: 대규모형·로봇은 있는데 소농형은 없는 작물군 × 분업 방식

실행:
  conda run -n scenario-space python 80_gap.py --run mistral__mistral
  conda run -n scenario-space python 80_gap.py --run mistral__mistral --pilot --min-pair 1 --min-expected 0.3 --min-neighbor 1
  (파일럿은 코드 경로 시험용이다. 수확 장치 몇 건으로는 아무것도 판정할 수 없다)
"""

from __future__ import annotations

import argparse
import importlib
import math

import numpy as np
import pandas as pd

import crop_groups
from config import DATA, PROMPT_VERSION, TASK

agg = importlib.import_module("70_aggregate")

FUNCS = agg.FUNCS
MACHINE = agg.MACHINE
SMALL_FORMS = {"handheld_tool", "walk_behind_or_pushed"}
LARGE_FORMS = {"tractor_mounted_or_towed", "self_propelled_harvester", "stationary_installation"}
LARGE_POWER = {"tractor_pto_or_hydraulics"}
VAGUE_DETACH = {"not_specified", "not_applicable", "other"}
NO_CROP = {crop_groups.UNSPEC, "out_of_scope_crop"}
FUNC_WORK = {
    "F1": "수확할 작물을 찾고 고르는 일",
    "F2": "작물에 손이 닿도록 몸·사다리·도구를 옮기는 일",
    "F3": "따거나 자르는 반복 손동작",
    "F4": "딴 작물을 담고 나르는 일",
}
SCALES = ["소농형", "작업자 플랫폼", "이동 로봇", "대규모형", "불명"]


def scale(form: str, power: str) -> str:
    """동력원과 장치 형태로 나눈 장치 규모. 트랙터 동력이면 형태와 상관없이 대규모형."""
    if form in LARGE_FORMS or set(str(power).split(";")) & LARGE_POWER:
        return "대규모형"
    if form in SMALL_FORMS:
        return "소농형"
    if form == "mobile_robot":
        return "이동 로봇"
    if form == "worker_platform_or_cart":
        return "작업자 플랫폼"
    return "불명"


def machine_set(row) -> frozenset:
    return frozenset(k for k in FUNCS if row[f"{k}_rel"] != "not_mentioned" and row[f"{k}_actor"] in MACHINE)


def label(s: frozenset) -> str:
    return agg.combo([k for k in FUNCS if k in s])


def split(v) -> list[str]:
    return [x for x in str(v).split(";") if x and x != "nan"]


def load(args) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(범위 안 특허 전부, 그 가운데 수확 장치)."""
    run_dir = DATA / "llm_output" / f"mapping_{TASK}_{PROMPT_VERSION}" / args.run
    card_dir = DATA / "llm_output" / f"card_{PROMPT_VERSION}" / args.run.split("__")[0]
    ids = (pd.read_csv(DATA / "pilot.csv")["google_id"].tolist() if args.pilot
           else sorted(p.stem for p in run_dir.glob("*.json")))
    p = agg.patent_rows(run_dir, card_dir, ids)
    ins = p[p["in_scope"]].copy()
    ins["mset"] = ins.apply(machine_set, axis=1)
    ins["combo"] = ins["mset"].map(label)
    ins["level"] = ins["mset"].map(len)
    ins["scale"] = [scale(f, pw) for f, pw in zip(ins["form"], ins["power"])]
    ins["year"] = pd.to_numeric(ins["priority_year"], errors="coerce")
    ins["era"] = pd.cut(ins["year"], [0, 1999, 2009, 2019, 2100], labels=["~1999", "2000–09", "2010–19", "2020~"])
    types = ins["problem_types"].fillna("") + ";" + ins["effect_types"].fillna("")
    ins["labor"] = types.str.contains("labor_or_cost")
    ins["ergo"] = types.str.contains("safety_or_ergonomics")
    return ins, ins[ins["class"] == "harvest_device"].copy()


def md(df: pd.DataFrame, index: bool = False) -> str:
    if df.empty:
        return "(해당 없음)"
    if index:
        df = df.reset_index()
    head = "| " + " | ".join(map(str, df.columns)) + " |"
    sep = "|" + "---|" * len(df.columns)
    body = ["| " + " | ".join(map(str, r)) + " |" for r in df.itertuples(index=False)]
    return "\n".join([head, sep, *body])


def pct(x: float) -> str:
    return "–" if pd.isna(x) else f"{x:.0%}"


def top(s: pd.Series, ko: dict | None = None, k: int = 2) -> str:
    vc = s.value_counts()
    return ", ".join(f"{(ko or {}).get(i, i)} {v}" for i, v in vc.head(k).items()) or "–"


# ---------- A. 분업 방식 패턴 ----------

def profile(dev: pd.DataFrame, recent: int) -> pd.DataFrame:
    rows = []
    for c, g in sorted(dev.groupby("combo"), key=lambda kv: (kv[1]["level"].iloc[0], -len(kv[1]))):
        known_crop = g["crop_group"][~g["crop_group"].isin(NO_CROP)]
        known_det = g["detach"][~g["detach"].isin(VAGUE_DETACH)]
        rows.append({
            "분업 방식": c,
            "건수": len(g),
            "주요 작물군": top(known_crop, crop_groups.KO),
            "주요 분리 원리": top(known_det, agg.DETACH_KO),
            "주요 형태": top(g["form"], agg.FORM_KO),
            "소농형": pct((g["scale"] == "소농형").mean()),
            "대규모형": pct((g["scale"] == "대규모형").mean()),
            "우선일 중앙값": "–" if g["year"].isna().all() else int(g["year"].median()),
            f"{recent}년 이후": pct((g["year"] >= recent).mean()),
            "노동·비용 문제": pct(g["labor"].mean()),
            "안전·작업 자세 문제": pct(g["ergo"].mean()),
        })
    return pd.DataFrame(rows)


def cramers_v(a: np.ndarray, b: np.ndarray) -> float:
    t = pd.crosstab(a, b).to_numpy(float)
    if min(t.shape) < 2:
        return float("nan")
    n = t.sum()
    e = t.sum(1, keepdims=True) * t.sum(0, keepdims=True) / n
    chi2 = ((t - e) ** 2 / e).sum()
    return math.sqrt(chi2 / (n * (min(t.shape) - 1)))


def perm_p(lab: np.ndarray, attr: np.ndarray, strata: np.ndarray | None, n_perm: int, rng) -> tuple[float, float]:
    v0 = cramers_v(lab, attr)
    if math.isnan(v0):
        return v0, float("nan")
    groups = [np.where(strata == s)[0] for s in np.unique(strata)] if strata is not None else None
    hit = 0
    for _ in range(n_perm):
        if groups is None:
            perm = rng.permutation(lab)
        else:
            perm = lab.copy()
            for idx in groups:
                perm[idx] = rng.permutation(lab[idx])
        hit += cramers_v(perm, attr) >= v0 - 1e-12
    return v0, (hit + 1) / (n_perm + 1)


def association(dev: pd.DataFrame, min_combo: int, n_perm: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    d = dev.copy()
    big = d["combo"].value_counts()
    d["combo_m"] = d["combo"].where(d["combo"].map(big) >= min_combo, "기타 조합")
    attrs = [
        ("작물군", "crop_group", ~d["crop_group"].isin(NO_CROP)),
        ("분리 원리", "detach", ~d["detach"].isin(VAGUE_DETACH)),
        ("장치 형태", "form", ~d["form"].isin(["not_specified", "component_only"])),
        ("장치 규모", "scale", d["scale"] != "불명"),
        ("출원 시기", "era", d["era"].notna()),
    ]
    rows = []
    for name, col, ok in attrs:
        s = d[ok]
        lab = s["combo_m"].to_numpy()
        attr = s[col].astype(str).to_numpy()
        row = {"속성": name, "건수": len(s), "분업 방식 수": s["combo_m"].nunique()}
        if len(s) < 10 or s["combo_m"].nunique() < 2:
            rows.append(row | {"크래머 V": "–", "p": "건수 부족", "작물군 안 조건부 p": "–"})
            continue
        v, p = perm_p(lab, attr, None, n_perm, rng)
        row |= {"크래머 V": f"{v:.2f}", "p": f"{p:.3f}"}
        if col == "crop_group":
            row["작물군 안 조건부 p"] = "–"
        else:
            sc = s[~s["crop_group"].isin(NO_CROP)]
            if len(sc) < 10:
                row["작물군 안 조건부 p"] = "건수 부족"
            else:
                _, pc = perm_p(sc["combo_m"].to_numpy(), sc[col].astype(str).to_numpy(),
                               sc["crop_group"].to_numpy(), n_perm, rng)
                row["작물군 안 조건부 p"] = f"{pc:.3f} ({len(sc)}건)"
        rows.append(row)
    return pd.DataFrame(rows)


# ---------- B. 소농 노동과의 연결 ----------

def function_by_scale(dev: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for k in FUNCS:
        row = {"기능": k, "사람이 하던 일": FUNC_WORK[k]}
        for sc in SCALES:
            g = dev[dev["scale"] == sc]
            if len(g):
                n = g["mset"].map(lambda s: k in s).sum()
                row[f"{sc} ({len(g)})"] = f"{n} ({n / len(g):.0%})"
        rows.append(row)
    return pd.DataFrame(rows)


def labor_by_scale(dev: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for sc in SCALES:
        g = dev[dev["scale"] == sc]
        if g.empty:
            continue
        left = g["mset"].map(lambda s: label(frozenset(FUNCS) - s))
        rows.append({
            "장치 규모": sc,
            "건수": len(g),
            "기계 수행 기능 수(평균)": f"{g['level'].mean():.1f}",
            "사람 몫으로 남는 기능(흔한 순)": top(left, k=3),
            "노동·비용 문제": pct(g["labor"].mean()),
            "안전·작업 자세 문제": pct(g["ergo"].mean()),
        })
    return pd.DataFrame(rows)


# ---------- C. 저개발 칸 ----------

def explode_cells(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for r in df.itertuples():
        dets = [x for x in split(r.detach_all) if x not in VAGUE_DETACH]
        for c in split(r.crop_groups_all):
            if c in NO_CROP:
                continue
            for d in dets or [None]:
                rows.append({"gid": r.google_id, "crop": c, "detach": d, "mset": r.mset, "combo": r.combo,
                             "year": r.year, "confidence": r.confidence, "scale": r.scale})
    return pd.DataFrame(rows, columns=["gid", "crop", "detach", "mset", "combo", "year", "confidence", "scale"])


def fill_check(target: frozenset, existing: list[frozenset], providers: pd.DataFrame, crop: str, det: str):
    """같은 칸의 기존 조합 가운데 target에 포함되는 가장 큰 것을 바탕으로, 빠진 기능을 같은 작물군이나
    같은 분리 원리의 다른 특허(부품 기술 포함)가 기계로 수행하는지 본다."""
    if not target:
        return "–", "–", None
    subs = [s for s in existing if s <= target]
    base = max(subs, key=len) if subs else frozenset()
    missing = sorted(target - base)
    near = providers[(providers["crop"] == crop) | (providers["detach"] == det)]
    have = [k for k in missing if near["mset"].map(lambda s: k in s).any()]
    return label(base) if subs else "–", "·".join(missing), len(have) == len(missing)


def cells_table(dev: pd.DataFrame, providers: pd.DataFrame, a) -> pd.DataFrame:
    cells = explode_cells(dev).dropna(subset=["detach"])
    if cells.empty:
        return pd.DataFrame()
    pair_n = cells.groupby(["crop", "detach"])["gid"].nunique()
    feasible = pair_n[pair_n >= a.min_pair].index
    cf = cells.set_index(["crop", "detach"]).loc[lambda x: x.index.isin(feasible)].reset_index()
    if cf.empty:
        return pd.DataFrame()
    n_total = len(cf)
    n_pair = cf.groupby(["crop", "detach"]).size()
    n_combo = cf.groupby("combo").size()
    combo_sets = cf.drop_duplicates("combo").set_index("combo")["mset"]
    crop_n = cf.groupby("crop").size()
    rows = []
    for (c, d) in feasible:
        here = cf[(cf["crop"] == c) & (cf["detach"] == d)]
        existing = list(here.drop_duplicates("combo")["mset"])
        for combo, s in combo_sets.items():
            g = here[here["combo"] == combo]
            o = len(g)
            e = n_pair[(c, d)] * n_combo[combo] / n_total
            past = int((g["year"] < a.recent).sum())
            rec = int((g["year"] >= a.recent).sum())
            if o == 0 and e >= a.min_expected:
                status = "공백"
            elif o > 0 and e >= 2 * a.min_expected and o / e < a.low_ratio:
                status = "저개발"
            elif past >= 2 and rec == 0:
                status = "최근 끊김"
            else:
                status = ""
            other_crops = int(((cf["combo"] == combo) & (cf["crop"] != c)).sum())
            neighbor = (crop_n[c] - o) >= a.min_neighbor and other_crops >= a.min_neighbor
            row = {"작물군": crop_groups.KO[c], "분리 원리": agg.DETACH_KO.get(d, d), "분업 방식": combo, "관측": o,
                   "기대": round(e, 1), "관측/기대": round(o / e, 2) if e else "–",
                   f"{a.recent} 이전": past, f"{a.recent} 이후": rec, "판정": status,
                   "이웃 충분": "예" if neighbor else "아니오"}
            if status == "공백":
                base, missing, ok = fill_check(s, existing, providers, c, d)
                row |= {"가장 가까운 기존 조합": base, "빠진 기능": missing,
                        "채울 수 있음": "–" if ok is None else ("예(조합)" if ok else "아니오(개발 필요)")}
            rows.append(row)
    return pd.DataFrame(rows)


def ladder(dev: pd.DataFrame) -> pd.DataFrame:
    cells = explode_cells(dev).drop_duplicates(["gid", "crop"])
    level_of = dev.drop_duplicates("combo").set_index("combo")["level"]
    rows = []
    for c, g in cells.groupby("crop"):
        by_level = {lv: gg["combo"].value_counts() for lv, gg in g.groupby(g["mset"].map(len))}
        lo, hi = min(by_level), max(by_level)
        gaps = [lv for lv in range(lo, hi + 1) if lv not in by_level]
        elsewhere = sorted(x for x, lv in level_of.items() if lv in gaps)
        rows.append({
            "작물군": crop_groups.KO[c],
            "건수": g["gid"].nunique(),
            "있는 단(기계 수행 기능 수: 분업 방식)": " / ".join(
                f"{lv}: " + ", ".join(f"{k} {v}" for k, v in vc.items()) for lv, vc in sorted(by_level.items())),
            "빈 사이 단": ", ".join(map(str, gaps)) or "–",
            "다른 작물군에 있는 그 단의 조합": ", ".join(elsewhere) or "–",
        })
    return pd.DataFrame(rows)


def scale_gap(dev: pd.DataFrame) -> pd.DataFrame:
    cells = explode_cells(dev).drop_duplicates(["gid", "crop"])
    if cells.empty:
        return pd.DataFrame()
    t = pd.crosstab([cells["crop"], cells["combo"]], cells["scale"])
    for sc in SCALES:
        if sc not in t:
            t[sc] = 0
    big = t["대규모형"] + t["이동 로봇"]
    t = t[(big > 0) & (t["소농형"] == 0)][SCALES].reset_index()
    t["crop"] = t["crop"].map(crop_groups.KO)
    return t.rename(columns={"crop": "작물군", "combo": "분업 방식"})


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--min-pair", type=int, default=3, help="가능한 쌍으로 볼 작물군×분리 원리의 최소 특허 수")
    ap.add_argument("--min-expected", type=float, default=1.0, help="공백으로 판정할 최소 기대 건수")
    ap.add_argument("--low-ratio", type=float, default=0.5, help="저개발로 볼 관측/기대 상한")
    ap.add_argument("--min-neighbor", type=int, default=3, help="이웃 조건의 최소 건수")
    ap.add_argument("--min-combo", type=int, default=5, help="연관 검정에서 따로 셀 분업 방식의 최소 건수")
    ap.add_argument("--recent", type=int, default=2015)
    ap.add_argument("--perm", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()

    ins, dev = load(a)
    providers = explode_cells(ins)
    out = [f"# 분업 방식 패턴과 저개발 기능 조합 ({PROMPT_VERSION}, {a.run}{', 파일럿' if a.pilot else ''})\n",
           f"범위 안 특허 {len(ins)}건, 그 가운데 수확 장치 {len(dev)}건. 모두 LLM 판정이며 표본 검증 전이다.",
           f"사람 힘 장치라 수행 주체를 사람으로 고친 특허: {int(dev['actor_fixed'].sum())}건. "
           f"작물군 근거: {dev['crop_group_source'].value_counts().to_dict()}. "
           f"장치 규모: {dev['scale'].value_counts().to_dict()}.\n"]

    out.append("## A1. 분업 방식별 프로필 (수확 장치)\n")
    out.append(md(profile(dev, a.recent)))
    out.append("\n작물군·분리 원리는 미상·범위 밖을 빼고 센다. 노동·비용, 안전·작업 자세는 특허가 문제나 효과로 내세운 비율이다.\n")

    out.append("\n## A2. 분업 방식과 다른 속성의 연관\n")
    out.append(md(association(dev, a.min_combo, a.perm, a.seed)))
    out.append(f"\n{a.min_combo}건 미만인 분업 방식은 '기타 조합'으로 묶었다. p는 분업 방식 표지를 섞은 순열 검정({a.perm}회). "
               "조건부 p는 같은 작물군 안에서만 섞은 것으로, 이것도 작으면 그 연관이 작물군 구성 차이만으로 설명되지 않는다.\n")

    out.append("\n## B1. 기능별 기계 수행 비율, 장치 규모별 (수확 장치)\n")
    out.append(md(function_by_scale(dev)))
    out.append("\n규모: 소농형은 손 도구·밀거나 끄는 장치이면서 트랙터 동력이 아닌 것, 대규모형은 트랙터 부착·자주식·고정 설비이거나 트랙터 동력인 것.\n")

    out.append("\n## B2. 장치 규모별 사람 몫과 특허가 내세운 노동 문제 (수확 장치)\n")
    out.append(md(labor_by_scale(dev)))

    cells = cells_table(dev, providers, a)
    if not cells.empty:
        high = cells_table(dev[dev["confidence"] == "high"], providers, a)
        keep = set() if high.empty else set(map(tuple, high.loc[high["판정"] == "공백", ["작물군", "분리 원리", "분업 방식"]].to_numpy()))
        cells["신뢰도 high만 써도 공백"] = [
            ("예" if (r["작물군"], r["분리 원리"], r["분업 방식"]) in keep else "아니오") if r["판정"] == "공백" else ""
            for _, r in cells.iterrows()]
    out.append("\n## C1. 저개발 칸 (작물군 × 분리 원리 × 분업 방식)\n")
    flagged = cells[cells["판정"] != ""] if not cells.empty else cells
    out.append(md(flagged.sort_values(["판정", "기대"], ascending=[True, False]).fillna("")
                  if not flagged.empty else flagged))
    out.append(f"\n가능한 쌍: 분업 방식과 상관없이 수확 장치가 {a.min_pair}건 이상인 작물군×분리 원리. "
               f"공백: 관측 0이고 기대 {a.min_expected} 이상. 저개발: 관측/기대 {a.low_ratio} 미만이고 기대 {2 * a.min_expected} 이상. "
               f"최근 끊김: {a.recent}년 이전에 2건 이상 있었으나 이후에 없음. 이웃 충분: 같은 작물군의 다른 칸과 같은 분업 방식의 다른 작물군이 각각 "
               f"{a.min_neighbor}건 이상. 채울 수 있음: 빠진 기능을 같은 작물군이나 같은 분리 원리의 다른 특허(부품 기술 포함)가 기계로 수행함.\n")

    out.append("\n## C2. 사다리 공백 (작물군별)\n")
    out.append(md(ladder(dev)))
    out.append("\n단은 기계가 맡는 기능 수(0–4). 빈 사이 단은 아래 단과 위 단 사이에서 특허가 없는 단이다.\n")

    out.append("\n## C3. 규모 공백: 대규모형·로봇만 있고 소농형은 없는 작물군 × 분업 방식\n")
    out.append(md(scale_gap(dev)))

    text = "\n".join(out) + "\n"
    out_dir = DATA / "llm_output" / f"gap_{PROMPT_VERSION}_{a.run}{'_pilot' if a.pilot else ''}"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "gap.md").write_text(text, encoding="utf-8")
    if not cells.empty:
        cells.to_csv(out_dir / "cells.csv", index=False, encoding="utf-8-sig")
    dev.drop(columns=["mset"]).to_csv(out_dir / "devices.csv", index=False, encoding="utf-8-sig")
    print(text)
    print(f"저장: {out_dir}")


if __name__ == "__main__":
    main()
