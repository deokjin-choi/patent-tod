"""범위 안 수확 장치에서 표본 검증용 특허를 층화로 뽑는다.

장치 규모(소농형·대규모형·작업자 플랫폼·이동 로봇·불명) 비율에 맞춰 뽑고,
같은 규모 안에서는 장치 형태가 고르게 들어가게 한다.

실행:
  conda run -n scenario-space python 85_pick_validate.py --run mistral__mistral --n 40
"""

from __future__ import annotations

import argparse
import importlib

import numpy as np
import pandas as pd

from config import DATA, PROMPT_VERSION

gap = importlib.import_module("80_gap")

SCALES = ["소농형", "대규모형", "작업자 플랫폼", "이동 로봇", "불명"]
COLS = [
    "google_id", "title", "priority_year", "cpc_groups", "scope", "class", "machine_does",
    "F1_rel", "F1_actor", "F2_rel", "F2_actor", "F3_rel", "F3_actor", "F4_rel", "F4_actor",
    "crop_group", "target_objects", "detach", "form", "power", "scale", "confidence", "crop_group_source",
]


def allocate(counts: pd.Series, n: int) -> dict[str, int]:
    present = [s for s in SCALES if counts.get(s, 0)]
    raw = {s: max(2 if counts[s] >= 2 else 1, round(n * counts[s] / counts.sum())) for s in present}
    raw = {s: min(raw[s], int(counts[s])) for s in raw}
    while sum(raw.values()) > n:
        k = max(raw, key=raw.get)
        if raw[k] > (2 if counts[k] >= 2 else 1):
            raw[k] -= 1
        else:
            break
    while sum(raw.values()) < n:
        room = [s for s in raw if raw[s] < counts[s]]
        if not room:
            break
        k = max(room, key=lambda s: counts[s] - raw[s])
        raw[k] += 1
    return raw


def pick_in_scale(pool: pd.DataFrame, k: int, rng: np.random.Generator) -> list:
    if k >= len(pool):
        return pool.index.tolist()
    forms = pool["form"].value_counts()
    take, leftover = [], k
    for form, n_form in forms.items():
        if leftover <= 0:
            break
        sub = pool[pool["form"] == form]
        n = min(len(sub), leftover, max(1, round(k * n_form / len(pool))))
        idx = rng.choice(sub.index.to_numpy(), size=n, replace=False)
        take.extend(idx.tolist())
        leftover -= n
    if leftover > 0:
        left = pool.loc[~pool.index.isin(take)]
        if len(left):
            idx = rng.choice(left.index.to_numpy(), size=min(leftover, len(left)), replace=False)
            take.extend(idx.tolist())
    return take


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)

    p = pd.read_csv(DATA / "llm_output" / f"aggregate_{PROMPT_VERSION}_{a.run}" / "patents.csv")
    ins = p[p["in_scope"]].copy()
    ins["scale"] = [gap.scale(f, pw) for f, pw in zip(ins["form"], ins["power"])]
    dev = ins[ins["class"] == "harvest_device"].copy()
    counts = dev["scale"].value_counts()
    alloc = allocate(counts, a.n)

    picked = []
    for s, k in alloc.items():
        picked.extend(pick_in_scale(dev[dev["scale"] == s], k, rng))
    sample = dev.loc[sorted(set(picked))].copy()
    if len(sample) < a.n:
        extra = dev.loc[~dev.index.isin(sample.index)]
        need = min(a.n - len(sample), len(extra))
        if need:
            idx = rng.choice(extra.index.to_numpy(), size=need, replace=False)
            sample = pd.concat([sample, extra.loc[idx]])

    sample["scale"] = [gap.scale(f, pw) for f, pw in zip(sample["form"], sample["power"])]
    out_dir = DATA / "llm_output" / f"validate_{PROMPT_VERSION}_{a.run}"
    out_dir.mkdir(parents=True, exist_ok=True)
    sample[COLS].to_csv(out_dir / "sample.csv", index=False, encoding="utf-8-sig")
    print(f"모집단 수확 장치 {len(dev)}건에서 {len(sample)}건. 배분 {alloc}")
    print("규모:", sample["scale"].value_counts().to_dict())
    print("형태:", sample["form"].value_counts().to_dict())
    print("분업:", sample["machine_does"].value_counts().to_dict())
    print(f"저장: {out_dir / 'sample.csv'}")
    for r in sample.itertuples():
        print(f"{r.google_id}\t{r.scale}\t{r.form}\t{r.power}\t{r.machine_does}\t{r.crop_group}\t{r.title[:55]}")


if __name__ == "__main__":
    main()
