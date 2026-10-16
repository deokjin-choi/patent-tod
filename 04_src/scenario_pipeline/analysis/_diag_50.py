"""One-shot: three diagnostics on the 50-scenario space. Not on the score path."""

from __future__ import annotations

import sys
from collections import Counter
from importlib.machinery import SourceFileLoader

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, spearmanr

from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import config as cfg

m = SourceFileLoader("kg71", str(cfg.HERE / "71_quadrant_kg.py")).load_module()

G_LARGE = {2, 4}
ROLE = tuple(s.lower() for s in cfg.PAIR_SAME_NOUN_STEMS)
GREL = tuple(s.lower() for s in cfg.PAIR_GENERIC_REL_STEMS)
KO = {
    "existing": "기존",
    "opportunity": "기회",
    "contradiction": "모순",
    "review": "검토",
    "undecided": "보류",
}


def parse(g: str) -> set[int]:
    return {int(x) for x in str(g).split("|") if str(x).strip() != ""}


def cramers_v(a: pd.Series, b: pd.Series) -> tuple[float, pd.DataFrame]:
    tab = pd.crosstab(a, b)
    chi2, _, _, _ = chi2_contingency(tab)
    n = int(tab.to_numpy().sum())
    r, k = tab.shape
    v = float(np.sqrt(chi2 / (n * min(r - 1, k - 1)))) if min(r, k) > 1 and n else float("nan")
    return v, tab


def roleish(text: str) -> bool:
    t = text.lower()
    return any(s in t for s in ROLE)


def generic_rel(rel: str) -> bool:
    t = rel.lower()
    return any(s in t for s in GREL)


def main() -> int:
    quad = pd.read_csv(cfg.OUT / "70_quadrants.csv")
    scen = pd.read_csv(cfg.OUT / "61_scenarios.csv")
    df = quad.merge(scen[["scenario_id", "p_trend"]], on="scenario_id")
    df["n_large"] = df["groups"].map(lambda g: len(parse(g) & G_LARGE))
    df["has_G2"] = df["groups"].map(lambda g: 2 in parse(g))
    df["has_G4"] = df["groups"].map(lambda g: 4 in parse(g))

    print("=" * 72)
    print("숫자 1.  상위 P가 큰 그룹(ECRAO=G2, ECAD=G4)을 넣는가")
    print("=" * 72)
    rho_pt, _ = spearmanr(df["p_norm"], df["p_trend"])
    rho_nl, _ = spearmanr(df["p_norm"], df["n_large"])
    print(f"  Spearman(P, P_trend) = {rho_pt:.3f}")
    print(f"  Spearman(P, n_large) = {rho_nl:.3f}   n_large = |s ∩ {{ECRAO,ECAD}}|")
    print("  크기별 P 상위 삼분위:")
    for size, sub in df.groupby("size"):
        hi = sub[sub["p_tercile"] == "high"]
        both = (hi["has_G2"] & hi["has_G4"]).mean()
        either = (hi["has_G2"] | hi["has_G4"]).mean()
        print(
            f"    |s|={int(size)} n_high={len(hi)}  "
            f"G2={hi['has_G2'].mean():.0%}  G4={hi['has_G4'].mean():.0%}  "
            f"둘다={both:.0%}  둘중하나={either:.0%}"
        )
    hi = df[df["p_tercile"] == "high"]
    print(
        f"  high 전체 n={len(hi)}  "
        f"G2={hi['has_G2'].mean():.0%}  G4={hi['has_G4'].mean():.0%}  "
        f"둘다={(hi['has_G2'] & hi['has_G4']).mean():.0%}  "
        f"둘중하나={(hi['has_G2'] | hi['has_G4']).mean():.0%}"
    )
    print("  크기별 P 1등:")
    for size, sub in df.groupby("size"):
        top = sub.sort_values("p_norm", ascending=False).iloc[0]
        print(f"    |s|={int(size)}  {top.names}  n_large={int(top.n_large)}  P={top.p_norm:.3f}")
    print("  크기별 Spearman(P, P_trend):")
    for size, sub in df.groupby("size"):
        r, _ = spearmanr(sub["p_norm"], sub["p_trend"])
        print(f"    |s|={int(size)}  {r:.3f}")

    print()
    print("=" * 72)
    print("숫자 2.  다른 s가 같은 (h,r,t)를 얼마나 쓰는가")
    print("=" * 72)
    novel = pd.read_csv(cfg.OUT / "60_pair_novel.csv")
    typical = pd.read_csv(cfg.OUT / "60_pair_typical.csv")
    selected = m.selected_by_group(cfg.OUT / "60_group_entities.csv")
    k = int(cfg.PAIR_GRAPH_CANDIDATES)

    def triples_of(row) -> list[tuple[str, str, str]]:
        prefer_high = row.quadrant in ("opportunity", "contradiction")
        source = novel if prefer_high else typical
        found = m.joint_graph(m.parse_groups(row.groups), source, prefer_high, selected, k)
        if found is None:
            return []
        _nodes, edges, _u = found
        return [(str(e["h"]), str(e["r"]), str(e["t"])) for e in edges]

    scen_triples: dict[str, list[tuple[str, str, str]]] = {}
    for row in df.itertuples(index=False):
        scen_triples[row.scenario_id] = triples_of(row)

    all_t = [t for ts in scen_triples.values() for t in ts]
    n_edges = len(all_t)
    n_unique = len(set(all_t))
    role_n = sum(1 for h, r, t in all_t if roleish(h) and roleish(t) and generic_rel(r))
    print(f"  표시 트리플 {n_edges}개 / 서로 다른 (h,r,t) {n_unique}개")
    print(f"  재사용률 (1 - unique/total) = {1 - n_unique / n_edges:.0%}")
    print(f"  역할틀 비율 = {role_n}/{n_edges} = {role_n / n_edges:.0%}")

    ids = list(scen_triples)
    share = 0
    for a in ids:
        sa = set(scen_triples[a])
        if any(sa & set(scen_triples[b]) for b in ids if b != a):
            share += 1
    print(f"  다른 s와 트리플 1개 이상 공유 = {share}/{len(ids)} = {share / len(ids):.0%}")
    fps = [" || ".join(sorted(f"{h}--{r}-->{t}" for h, r, t in scen_triples[i])) for i in ids]
    print(f"  그래프 지문이 다른 시나리오 = {len(set(fps))}/{len(ids)}")
    print("  최다 재사용 트리플:")
    for (h, r, t), c in Counter(all_t).most_common(5):
        print(f"    {c:2d}×  {h} --{r}--> {t}")

    print()
    print("=" * 72)
    print("숫자 3.  사분면이 ECRAO/ECAD 유무와 얼마나 같은가")
    print("=" * 72)
    order_q = ["existing", "opportunity", "contradiction", "review", "undecided"]
    tab = (
        pd.crosstab(df["quadrant"], df["n_large"])
        .reindex(index=order_q, columns=[0, 1, 2])
        .fillna(0)
        .astype(int)
    )
    print("  칸 × n_large (0=둘다없음, 1=하나만, 2=둘다)")
    print(tab.to_string())
    v, _ = cramers_v(df["quadrant"], df["n_large"])
    print(f"  Cramer's V(사분면, n_large) = {v:.2f}")
    corners = df[df["quadrant"].isin(["existing", "opportunity", "contradiction", "review"])]
    v2, _ = cramers_v(corners["quadrant"], corners["n_large"])
    print(f"  보류 제외 21칸: Cramer's V = {v2:.2f}")
    print("  칸별:")
    for q in order_q:
        sub = df[df["quadrant"] == q]
        if sub.empty:
            continue
        print(
            f"    {KO[q]:4s} n={len(sub):2d}  n_large평균={sub.n_large.mean():.2f}  "
            f"G2={sub.has_G2.mean():.0%}  G4={sub.has_G4.mean():.0%}"
        )
    mode = corners.groupby("n_large")["quadrant"].agg(lambda s: s.value_counts().idxmax())
    pred = corners["n_large"].map(mode)
    acc = float((pred == corners["quadrant"]).mean())
    print(f"  n_large→최빈칸 매핑 { {int(k): v for k, v in mode.items()} }")
    print(f"  그 규칙 정확도 {acc:.0%}  ({int((pred == corners['quadrant']).sum())}/{len(corners)})")
    rho_occ, _ = spearmanr(df["occ_ent"], df["n_large"])
    print(f"  Spearman(occ, n_large) = {rho_occ:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
