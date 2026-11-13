"""과일·채소 수확 CPC 범위에 드는 특허를 골라 scope.csv로 저장한다.

실행: conda run -n scenario-space python 10_select_scope.py
"""

from __future__ import annotations

from config import DATA, SCOPE_CSV, SCOPE_GROUPS, SOURCE_CSV
from lib import lens_to_google, read_source, scope_groups_of, split_codes


def main() -> None:
    df = read_source(SOURCE_CSV)
    codes = [split_codes(c, i) for c, i in zip(df["CPC Classifications"], df["IPCR Classifications"])]
    df["scope_groups"] = [";".join(scope_groups_of(c)) for c in codes]
    df["a01d_codes"] = [";".join(c for c in cs if c.startswith("A01D")) for cs in codes]

    scope = df[df["scope_groups"] != ""].copy()
    scope["google_id"] = scope["Display Key"].map(lens_to_google)
    scope = scope.drop(columns=["CPC Classifications", "IPCR Classifications"])
    scope = scope.sort_values(["scope_groups", "Earliest Priority Date"]).reset_index(drop=True)

    DATA.mkdir(parents=True, exist_ok=True)
    scope.to_csv(SCOPE_CSV, index=False, encoding="utf-8")

    print(f"원본 {len(df):,}건 중 범위 안 {len(scope):,}건 -> {SCOPE_CSV}")
    for name in SCOPE_GROUPS:
        n = scope["scope_groups"].str.split(";").map(lambda g: name in g).sum()
        print(f"  {name:20s} {n:5,}")
    multi = (scope["scope_groups"].str.count(";") > 0).sum()
    print(f"  두 그룹 이상          {multi:5,}")
    print("문헌 종류:", scope["Document Type"].value_counts().to_dict())
    print("본문 있음(Lens):", (scope["Has Full Text"] == "yes").sum())


if __name__ == "__main__":
    main()
