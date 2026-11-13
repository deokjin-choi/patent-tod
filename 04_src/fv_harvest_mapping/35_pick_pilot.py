"""파일럿 특허를 CPC 하위 그룹마다 한 건씩 고른다.

실행: conda run -n scenario-space python 35_pick_pilot.py
"""

from __future__ import annotations

import pandas as pd

from config import DATA, FETCH_LOG, SCOPE_CSV

PILOT_CSV = DATA / "pilot.csv"
SEED = 42
MAX_CHARS = 40_000

# (층 이름, a01d_codes에서 찾을 접두, 고정할 특허). 앞의 층에 뽑힌 특허는 뒤에서 다시 뽑지 않는다.
STRATA = [
    ("robotic", "A01D46/30", "US20110252760A1"),
    ("manual_tool", "A01D46/247", None),
    ("portable_motorised", "A01D46/253", None),
    ("tree_shaker", "A01D46/26", None),
    ("worker_platform", "A01D46/20", None),
    ("vegetable", "A01D45/2", None),
    ("root_crop", "A01D25/", None),
    ("ground_gathering", "A01D51/00", None),
]


def main() -> None:
    scope = pd.read_csv(SCOPE_CSV)
    log = pd.read_csv(FETCH_LOG)
    ok = log[log["status"] == "ok"][["google_id", "chars"]]
    pool = scope.merge(ok, on="google_id")
    pool = pool[pool["chars"] <= MAX_CHARS]

    rows, used = [], set()
    for name, prefix, fixed in STRATA:
        cand = pool[pool["a01d_codes"].fillna("").str.contains(prefix, regex=False) & ~pool["google_id"].isin(used)]
        pick = cand[cand["google_id"] == fixed] if fixed else cand.sample(1, random_state=SEED) if len(cand) else cand
        if pick.empty:
            print(f"{name}: 후보 없음")
            continue
        r = pick.iloc[0]
        used.add(r["google_id"])
        rows.append({"stratum": name, "google_id": r["google_id"], "title": r["Title"], "chars": r["chars"]})

    out = pd.DataFrame(rows)
    out.to_csv(PILOT_CSV, index=False, encoding="utf-8")
    print(out.to_string(index=False))
    print(f"-> {PILOT_CSV}")


if __name__ == "__main__":
    main()
