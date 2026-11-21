"""Phase A. Audit the harmonized LSMS-ISA files and build one row per
household-season for agricultural households.

The household file holds consumption, demographics, and sales.
Labor, land, harvest, assets, and machinery sit on the plot file and are
repeated household attributes (farm size, asset index, tractor) or plot
attributes (area, labor days, harvest). This script checks that those
household attributes really are constant within a household-season before
collapsing plots.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from config import (
    AREA_MAX_HA,
    AREA_MIN_HA,
    FAMILY_DAYS_MAX,
    FARM_MAX_HA,
    FARM_MIN_HA,
    FRAME_PATH,
    HH_KEYS,
    HH_PATH,
    OUT_DIR,
    PLOT_KEYS,
    PLOT_PATH,
    TABLE_DIR,
)

HH_COLS = [
    "country", "wave", "season", "hh_id_obs", "ea_id_obs", "strataid", "pw",
    "urban", "hh_size", "hh_shock", "hh_dependency_ratio", "nonfarm_enterprise",
    "nb_plots", "nb_fallow_plots", "share_kg_sold", "totcons_USD", "cons_quint",
    "hh_asset_index", "HDDS", "hh_electricity_access", "hh_formal_education",
]
PLOT_COLS = [
    "country", "wave", "season", "hh_id_obs", "plot_id_obs", "ea_id_obs",
    "strataid", "pw", "urban", "plot_area_GPS", "farm_size",
    "harvest_kg", "harvest_value_USD", "yield_kg", "yield_value_USD",
    "total_labor_days", "total_hired_labor_days", "total_family_labor_days",
    "inorganic_fertilizer", "organic_fertilizer", "used_pesticides",
    "irrigated", "tractor", "female_manager", "ag_asset_index", "main_crop",
    "livestock", "intercropped",
]


def _plain(df: pd.DataFrame) -> pd.DataFrame:
    """Drop Stata categorical dtypes so groupby and merge keys stay stable."""
    out = df.copy()
    for col in out.columns:
        if isinstance(out[col].dtype, pd.CategoricalDtype):
            out[col] = out[col].astype(object)
    return out


def _num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def _bin(s: pd.Series) -> pd.Series:
    """Map yes/no categories and 0/1 codes onto {0, 1}. Other codes stay missing."""
    if isinstance(s.dtype, pd.CategoricalDtype) or s.dtype == object:
        mapped = s.astype("string").str.strip().str.lower()
        out = pd.Series(np.nan, index=s.index, dtype="float64")
        out[mapped.isin(["yes", "y", "1", "1.0", "true"])] = 1.0
        out[mapped.isin(["no", "n", "0", "0.0", "false"])] = 0.0
        out[s.isna()] = np.nan
        return out
    num = pd.to_numeric(s, errors="coerce")
    return num.where(num.isin([0, 1]))


def _rate(s: pd.Series) -> float:
    s = _num(s)
    if s.notna().sum() == 0:
        return np.nan
    return float((s.fillna(0) > 0).mean()) if False else float(s.notna().mean())


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    print("reading household", flush=True)
    hh = _plain(pd.read_stata(HH_PATH, columns=HH_COLS))
    print("reading plot", hh.shape, flush=True)
    plot = _plain(pd.read_stata(PLOT_PATH, columns=PLOT_COLS))
    print("plot", plot.shape, flush=True)
    return hh, plot


def _miss_table(df: pd.DataFrame, cols: list[str], keys: list[str]) -> pd.DataFrame:
    rows = []
    for key, g in df.groupby(keys, dropna=False):
        rec = dict(zip(keys, key if isinstance(key, tuple) else (key,)))
        rec["n"] = int(len(g))
        for c in cols:
            rec[f"miss_{c}"] = float(g[c].isna().mean())
        rows.append(rec)
    return pd.DataFrame(rows)


def _within_nunique(df: pd.DataFrame, col: str) -> pd.Series:
    return df.groupby(HH_KEYS, dropna=False)[col].nunique(dropna=True)


def audit(hh: pd.DataFrame, plot: pd.DataFrame) -> dict:
    summary: dict = {}
    summary["hh_rows"] = int(len(hh))
    summary["plot_rows"] = int(len(plot))
    summary["hh_dup_keys"] = int(hh.duplicated(HH_KEYS).sum())
    summary["plot_dup_keys"] = int(plot.duplicated(PLOT_KEYS).sum())

    hh_key = hh[HH_KEYS].drop_duplicates()
    plot_key = plot[HH_KEYS].drop_duplicates()
    merged = plot_key.merge(hh_key, on=HH_KEYS, how="outer", indicator=True)
    summary["hh_seasons_only_in_plot"] = int((merged["_merge"] == "left_only").sum())
    summary["hh_seasons_only_in_hh"] = int((merged["_merge"] == "right_only").sum())
    summary["hh_seasons_in_both"] = int((merged["_merge"] == "both").sum())

    # Household attributes that the dictionary says are not plot-specific.
    const_cols = ["farm_size", "ag_asset_index", "tractor", "livestock", "pw"]
    const = {}
    for col in const_cols:
        nunq = _within_nunique(plot, col)
        const[col] = {
            "share_hh_season_with_2plus_values": float((nunq > 1).mean()),
            "n_hh_season_with_2plus": int((nunq > 1).sum()),
            "n_hh_season": int(nunq.shape[0]),
        }
    summary["within_hh_season_constancy"] = const

    # Seasons per household-wave. Uganda is the only bimodal survey.
    seas = (
        plot.groupby(["country", "wave", "hh_id_obs"], dropna=False)["season"]
        .nunique(dropna=True)
    )
    summary["share_hh_wave_with_2_seasons"] = (
        plot.groupby("country", dropna=False)
        .apply(
            lambda g: float(
                (
                    g.groupby(["wave", "hh_id_obs"])["season"].nunique(dropna=True) > 1
                ).mean()
            ),
            include_groups=False,
        )
        .round(4)
        .to_dict()
    )
    summary["n_hh_wave_with_2_seasons"] = int((seas > 1).sum())

    countries = sorted(hh["country"].dropna().unique().tolist())
    summary["countries"] = [str(c) for c in countries]
    waves = (
        hh.groupby("country", dropna=False)["wave"]
        .agg(lambda s: sorted(set(int(x) for x in s.dropna())))
        .to_dict()
    )
    summary["waves"] = {str(k): v for k, v in waves.items()}

    hh_miss_cols = [
        "totcons_USD", "cons_quint", "hh_size", "hh_dependency_ratio",
        "share_kg_sold", "hh_asset_index", "HDDS", "pw", "nonfarm_enterprise",
        "hh_shock",
    ]
    plot_miss_cols = [
        "plot_area_GPS", "farm_size", "total_family_labor_days",
        "total_hired_labor_days", "harvest_kg", "harvest_value_USD",
        "ag_asset_index", "tractor", "main_crop", "irrigated", "used_pesticides",
        "inorganic_fertilizer",
    ]
    hh_miss = _miss_table(hh, hh_miss_cols, ["country", "wave"])
    plot_miss = _miss_table(plot, plot_miss_cols, ["country", "wave"])
    hh_miss.to_csv(OUT_DIR / "audit_hh_missing.csv", index=False)
    plot_miss.to_csv(OUT_DIR / "audit_plot_missing.csv", index=False)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    hh_miss.to_csv(TABLE_DIR / "audit_hh_missing_by_wave.csv", index=False)
    plot_miss.to_csv(TABLE_DIR / "audit_plot_missing_by_wave.csv", index=False)

    # Extremes on the plot file, unweighted.
    area = _num(plot["plot_area_GPS"])
    farm = _num(plot["farm_size"])
    fam = _num(plot["total_family_labor_days"])
    yld = _num(plot["yield_kg"])
    summary["plot_area"] = _dist(area)
    summary["farm_size_plotrows"] = _dist(farm)
    summary["family_days_plot"] = _dist(fam)
    summary["yield_kg_plot"] = _dist(yld)
    summary["share_area_le_0"] = float((area.notna() & (area <= 0)).mean())
    summary["share_area_lt_0_05"] = float((area.notna() & (area < AREA_MIN_HA)).mean())
    summary["share_area_gt_10"] = float((area.notna() & (area > AREA_MAX_HA)).mean())
    summary["share_family_days_gt_cap"] = float((fam.notna() & (fam > FAMILY_DAYS_MAX)).mean())
    summary["share_family_days_eq_0"] = float((fam.notna() & (fam == 0)).mean())
    summary["share_yield_gt_50000"] = float((yld.notna() & (yld > 50000)).mean())
    return summary


def _dist(s: pd.Series) -> dict:
    s = s.dropna()
    if s.empty:
        return {}
    qs = s.quantile([0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99]).to_dict()
    return {
        "n": int(s.shape[0]),
        "mean": float(s.mean()),
        "min": float(s.min()),
        "max": float(s.max()),
        **{f"p{int(k*100):02d}": float(v) for k, v in qs.items()},
    }


def _first_valid(s: pd.Series):
    s = s.dropna()
    if s.empty:
        return np.nan
    return s.iloc[0]


def _sum_min1(s: pd.Series) -> float:
    """Sum that stays missing when every value is missing, instead of returning 0."""
    return float(s.sum(min_count=1))


def build_household_season(hh: pd.DataFrame, plot: pd.DataFrame) -> pd.DataFrame:
    p = plot.copy()
    for col in [
        "plot_area_GPS", "farm_size", "harvest_kg", "harvest_value_USD",
        "yield_kg", "yield_value_USD", "total_labor_days",
        "total_hired_labor_days", "total_family_labor_days",
        "ag_asset_index", "pw",
    ]:
        p[col] = _num(p[col])
    for col in [
        "inorganic_fertilizer", "organic_fertilizer", "used_pesticides",
        "irrigated", "tractor", "female_manager", "livestock",
        "intercropped", "urban",
    ]:
        p[col] = _bin(p[col])

    p["area_ok"] = p["plot_area_GPS"].between(AREA_MIN_HA, AREA_MAX_HA)
    p["fam_ok"] = p["total_family_labor_days"].between(0, FAMILY_DAYS_MAX)
    p["eligible"] = p["area_ok"] & p["fam_ok"]
    # Intensity with a floor, using every plot that has both area and labor,
    # so the screen above is a sensitivity choice rather than the only one.
    p["area_pos"] = p["plot_area_GPS"].where(p["plot_area_GPS"] > 0)
    p["area_floored"] = p["area_pos"].clip(lower=AREA_MIN_HA, upper=AREA_MAX_HA)
    p["fam_raw_ok"] = p["total_family_labor_days"].notna() & p["area_pos"].notna()
    p["fam_for_floor"] = p["total_family_labor_days"].where(p["fam_raw_ok"]).clip(lower=0, upper=FAMILY_DAYS_MAX)
    p["area_for_floor"] = p["area_floored"].where(p["fam_raw_ok"])

    p["elig_area"] = p["plot_area_GPS"].where(p["eligible"])
    p["elig_fam"] = p["total_family_labor_days"].where(p["eligible"])
    # Hired days are missing, not zero, when the plot has no hired-labor record.
    p["hired_obs"] = p["eligible"] & p["total_hired_labor_days"].notna()
    p["elig_hired"] = p["total_hired_labor_days"].where(p["hired_obs"])
    p["elig_harv_kg"] = p["harvest_kg"].where(p["eligible"])
    p["elig_harv_usd"] = p["harvest_value_USD"].where(p["eligible"])
    p["harv_kg_pos"] = p["harvest_kg"].where(p["plot_area_GPS"] > 0)
    p["harv_usd_pos"] = p["harvest_value_USD"].where(p["plot_area_GPS"] > 0)
    p["area_pos_sum"] = p["plot_area_GPS"].where(p["plot_area_GPS"] > 0)

    # Value-weighted main crop: accumulate harvest value by crop, pick the max.
    p["crop_value"] = p["harvest_value_USD"].where(p["harvest_value_USD"] > 0)
    crop = (
        p.dropna(subset=["main_crop"])
        .groupby(HH_KEYS + ["main_crop"], dropna=False)["crop_value"]
        .sum(min_count=1)
        .reset_index()
    )
    crop = crop.sort_values("crop_value", ascending=False)
    main = crop.drop_duplicates(HH_KEYS)[HH_KEYS + ["main_crop"]].rename(
        columns={"main_crop": "hh_main_crop"}
    )

    agg = p.groupby(HH_KEYS, dropna=False).agg(
        n_plots=("plot_id_obs", "size"),
        n_eligible=("eligible", "sum"),
        farm_size=("farm_size", "median"),
        farm_size_nunique=("farm_size", "nunique"),
        ag_asset_index=("ag_asset_index", "median"),
        tractor_any=("tractor", "max"),
        livestock_any=("livestock", "max"),
        pw_plot=("pw", "median"),
        urban_plot=("urban", "max"),
        ea_id_obs=("ea_id_obs", _first_valid),
        strataid=("strataid", _first_valid),
        labor_area=("elig_area", _sum_min1),
        family_days=("elig_fam", _sum_min1),
        hired_days=("elig_hired", _sum_min1),
        n_hired_obs=("hired_obs", "sum"),
        harvest_kg=("elig_harv_kg", _sum_min1),
        harvest_usd=("elig_harv_usd", _sum_min1),
        family_days_floor=("fam_for_floor", _sum_min1),
        labor_area_floor=("area_for_floor", _sum_min1),
        area_sum_pos=("area_pos_sum", _sum_min1),
        harvest_kg_all=("harv_kg_pos", _sum_min1),
        harvest_usd_all=("harv_usd_pos", _sum_min1),
        any_inorg=("inorganic_fertilizer", "max"),
        any_organic=("organic_fertilizer", "max"),
        any_pest=("used_pesticides", "max"),
        any_irrig=("irrigated", "max"),
        any_female_mgr=("female_manager", "max"),
        any_intercrop=("intercropped", "max"),
        n_main_crop=("main_crop", "nunique"),
    ).reset_index()

    agg = agg.merge(main, on=HH_KEYS, how="left")
    agg["days_per_ha"] = agg["family_days"] / agg["labor_area"].where(agg["labor_area"] > 0)
    agg["days_per_ha_floor"] = agg["family_days_floor"] / agg["labor_area_floor"].where(
        agg["labor_area_floor"] > 0
    )
    agg["yield_kg_ha"] = agg["harvest_kg"] / agg["labor_area"].where(agg["labor_area"] > 0)
    agg["yield_usd_ha"] = agg["harvest_usd"] / agg["labor_area"].where(agg["labor_area"] > 0)
    denom_days = (agg["family_days"] + agg["hired_days"]).where(
        (agg["family_days"] + agg["hired_days"]) > 0
    )
    agg["hired_share_days"] = agg["hired_days"] / denom_days
    agg["any_hired"] = np.where(
        agg["n_hired_obs"] > 0, (agg["hired_days"] > 0).astype(float), np.nan
    )
    agg["usd_per_family_day"] = agg["harvest_usd"] / agg["family_days"].where(agg["family_days"] > 0)
    agg["kg_per_family_day"] = agg["harvest_kg"] / agg["family_days"].where(agg["family_days"] > 0)

    h = hh.copy()
    for col in [
        "pw", "hh_size", "hh_shock", "hh_dependency_ratio",
        "nonfarm_enterprise", "nb_plots", "nb_fallow_plots", "share_kg_sold",
        "totcons_USD", "cons_quint", "hh_asset_index", "HDDS",
        "hh_formal_education",
    ]:
        h[col] = _num(h[col])
    for col in ["urban", "hh_electricity_access"]:
        h[col] = _bin(h[col])
    h["hh_shock"] = h["hh_shock"].where(h["hh_shock"].isin([0, 1]))
    h["nonfarm_enterprise"] = h["nonfarm_enterprise"].where(h["nonfarm_enterprise"].isin([0, 1]))
    h["hh_formal_education"] = h["hh_formal_education"].where(h["hh_formal_education"].isin([0, 1]))
    # share_kg_sold above 1 is already set to missing in the source notes,
    # but guard against a 0-100 coding.
    sold = h["share_kg_sold"]
    if sold.dropna().quantile(0.99) > 1.5:
        h["share_kg_sold"] = sold.where(sold <= 100) / 100.0
    h["share_kg_sold"] = h["share_kg_sold"].where(h["share_kg_sold"].between(0, 1))

    keep_hh = HH_KEYS + [
        "ea_id_obs", "strataid", "pw", "urban", "hh_size", "hh_shock",
        "hh_dependency_ratio", "nonfarm_enterprise", "nb_plots", "nb_fallow_plots",
        "share_kg_sold", "totcons_USD", "cons_quint", "hh_asset_index", "HDDS",
        "hh_electricity_access", "hh_formal_education",
    ]
    # Household file can theoretically repeat a key; keep the first.
    h = h[keep_hh].drop_duplicates(HH_KEYS, keep="first")
    out = agg.merge(h, on=HH_KEYS, how="left", suffixes=("", "_hh"))
    # Prefer the household-file weight and EA when present.
    out["pw"] = out["pw"].fillna(out["pw_plot"])
    out["urban"] = out["urban"].fillna(out["urban_plot"])
    out["ea_id_obs"] = out["ea_id_obs"].fillna(out["ea_id_obs_hh"]) if "ea_id_obs_hh" in out.columns else out["ea_id_obs"]

    out["ag_hh"] = (
        (out["n_plots"] >= 1)
        & out["farm_size"].between(FARM_MIN_HA, FARM_MAX_HA)
    )
    out["has_labor"] = out["days_per_ha"].notna()
    out["has_cons"] = out["totcons_USD"].notna() & out["cons_quint"].notna()
    # Adults implied by the dependency ratio if the ratio is dependents/non-dependents.
    # Checked later; stored as a candidate, not used until the ratio's scale is known.
    out["adults_from_depratio"] = out["hh_size"] / (1.0 + out["hh_dependency_ratio"])
    out["family_days_per_adult"] = out["family_days"] / out["adults_from_depratio"].where(
        out["adults_from_depratio"] > 0
    )
    return out


def wave_screen(frame: pd.DataFrame) -> pd.DataFrame:
    """Country-wave availability for the joint land-consumption-labor analysis."""
    ag = frame[frame["ag_hh"]].copy()
    rows = []
    for (country, wave), g in ag.groupby(["country", "wave"], dropna=False):
        rows.append({
            "country": country,
            "wave": int(wave),
            "n_ag": int(len(g)),
            "n_hh": int(g["hh_id_obs"].nunique()),
            "share_has_labor": float(g["has_labor"].mean()),
            "share_has_cons": float(g["has_cons"].mean()),
            "share_both": float((g["has_labor"] & g["has_cons"]).mean()),
            "n_both": int((g["has_labor"] & g["has_cons"]).sum()),
            "median_farm": float(g["farm_size"].median()),
            "median_days_ha": float(g.loc[g["has_labor"], "days_per_ha"].median()) if g["has_labor"].any() else np.nan,
            "median_cons": float(g.loc[g["has_cons"], "totcons_USD"].median()) if g["has_cons"].any() else np.nan,
        })
    tab = pd.DataFrame(rows).sort_values(["country", "wave"])
    tab.to_csv(OUT_DIR / "wave_availability.csv", index=False)
    tab.to_csv(TABLE_DIR / "wave_availability.csv", index=False)
    return tab


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    hh, plot = load()
    summary = audit(hh, plot)
    frame = build_household_season(hh, plot)
    frame.to_pickle(FRAME_PATH)
    summary["frame_rows"] = int(len(frame))
    summary["frame_ag"] = int(frame["ag_hh"].sum())
    summary["frame_ag_labor_cons"] = int((frame["ag_hh"] & frame["has_labor"] & frame["has_cons"]).sum())
    # Dependency ratio scale, to see whether adults = hh_size/(1+ratio) is usable.
    dep = frame.loc[frame["ag_hh"], "hh_dependency_ratio"]
    summary["dependency_ratio"] = _dist(dep)
    summary["dependency_share_gt_5"] = float((dep.dropna() > 5).mean())
    summary["dependency_share_between_0_and_1"] = float(dep.dropna().between(0, 1).mean())
    (OUT_DIR / "audit_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps({k: summary[k] for k in [
        "hh_rows", "plot_rows", "hh_dup_keys", "plot_dup_keys",
        "hh_seasons_only_in_plot", "hh_seasons_only_in_hh", "hh_seasons_in_both",
        "within_hh_season_constancy", "share_hh_wave_with_2_seasons",
        "countries", "waves", "frame_rows", "frame_ag", "frame_ag_labor_cons",
        "share_area_le_0", "share_area_lt_0_05", "share_family_days_gt_cap",
        "dependency_ratio",
    ]}, indent=2, default=str))
    wave_screen(frame)
    print("wrote", FRAME_PATH)


if __name__ == "__main__":
    main()
