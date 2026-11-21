"""Phases B–F. Identify small, low-consumption, high family-labor households
and compare them with agricultural households that do not meet that definition.

The labor flag used in the preferred target is the residual of log(days/ha)
on log(farm size), within country. Raw days/ha is also reported, because it
rises mechanically as the denominator shrinks. Differences in the variables
that define a group are described as composition, not as findings.
"""

from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from config import FIG_DIR, FRAME_PATH, OUT_DIR, TABLE_DIR

# Latest wave in each country that still has both consumption and family labor.
# Malawi wave 2 and Mali wave 1 are the only waves with a consumption aggregate.
# Nigeria wave 5 and Uganda wave 7 fail the labor or consumption screen.
LATEST_WAVE = {
    "Ethiopia": 5,
    "Malawi": 2,
    "Mali": 1,
    "Niger": 2,
    "Nigeria": 4,
    "Tanzania": 5,
    "Uganda": 8,
}

GROUPS = [
    "target",
    "naive_target",
    "rest",
    "larger_hired_asset",
    "small_poor_low_labor",
    "all_ag",
]


def _sum1(s: pd.Series) -> float:
    return float(s.sum(min_count=1))


def _first(s: pd.Series):
    s = s.dropna()
    return s.iloc[0] if len(s) else np.nan


def collapse_to_household(season: pd.DataFrame) -> pd.DataFrame:
    """One row per household-wave. Intensity is total days over total area,
    so Uganda's two seasons do not double the days/ha ratio."""
    keys = ["country", "wave", "hh_id_obs"]
    ranked = season.assign(_harv=season["harvest_usd"].fillna(-1)).sort_values("_harv", ascending=False)
    crop = ranked.drop_duplicates(keys)[keys + ["hh_main_crop", "ea_id_obs"]]
    summed = ["n_plots", "n_eligible", "labor_area", "family_days", "hired_days",
              "n_hired_obs", "harvest_kg", "harvest_usd", "labor_area_floor", "family_days_floor"]
    med = ["farm_size", "ag_asset_index", "pw", "hh_size", "hh_dependency_ratio",
           "share_kg_sold", "totcons_USD", "cons_quint", "hh_asset_index", "HDDS",
           "adults_from_depratio"]
    mx = ["tractor_any", "livestock_any", "urban", "any_inorg", "any_organic", "any_pest",
          "any_irrig", "any_female_mgr", "any_intercrop", "hh_shock", "nonfarm_enterprise",
          "hh_electricity_access"]
    named = {}
    for c in summed:
        named[c] = pd.NamedAgg(c, _sum1)
    for c in med:
        named[c] = pd.NamedAgg(c, "median")
    for c in mx:
        named[c] = pd.NamedAgg(c, "max")
    named["n_seasons"] = pd.NamedAgg("season", "nunique")
    out = season.groupby(keys, dropna=False).agg(**named).reset_index()
    out = out.merge(crop, on=keys, how="left")
    out = out.rename(columns={"adults_from_depratio": "adults"})
    out["days_per_ha"] = out["family_days"] / out["labor_area"].where(out["labor_area"] > 0)
    out["days_per_ha_floor"] = out["family_days_floor"] / out["labor_area_floor"].where(out["labor_area_floor"] > 0)
    out["yield_kg_ha"] = out["harvest_kg"] / out["labor_area"].where(out["labor_area"] > 0)
    out["yield_usd_ha"] = out["harvest_usd"] / out["labor_area"].where(out["labor_area"] > 0)
    both = (out["family_days"].fillna(0) + out["hired_days"].fillna(0)).where(
        (out["family_days"].notna()) | (out["hired_days"].notna())
    )
    out["hired_share_days"] = out["hired_days"] / both.where(both > 0)
    out["any_hired"] = np.where(out["n_hired_obs"] > 0, (out["hired_days"].fillna(0) > 0).astype(float), np.nan)
    out["usd_per_family_day"] = out["harvest_usd"] / out["family_days"].where(out["family_days"] > 0)
    out["kg_per_family_day"] = out["harvest_kg"] / out["family_days"].where(out["family_days"] > 0)
    out["family_days_per_adult"] = out["family_days"] / out["adults"].where(out["adults"] > 0)
    out["sold_any"] = np.where(out["share_kg_sold"].notna(), (out["share_kg_sold"] > 0).astype(float), np.nan)
    return out


def select_latest(frame: pd.DataFrame) -> pd.DataFrame:
    season = frame[frame["ag_hh"]].copy()
    mask = False
    for country, wave in LATEST_WAVE.items():
        mask = mask | ((season["country"] == country) & (season["wave"] == wave))
    season = season.loc[mask]
    hh = collapse_to_household(season)
    hh = hh[hh["farm_size"].between(0.01, 100)].copy()
    hh["in_sample"] = hh["days_per_ha"].notna() & hh["totcons_USD"].notna() & hh["cons_quint"].notna()
    return hh


def _within_flag(s: pd.Series, q: float, how: str) -> pd.Series:
    cut = s.quantile(q)
    if how == "le":
        return s <= cut
    return s >= cut


def add_definitions(df: pd.DataFrame) -> pd.DataFrame:
    """Flags are computed inside the analysis sample, separately by country."""
    d = df.copy()
    sample = d["in_sample"]
    d["small_rel"] = False
    d["low_p25"] = False
    d["low_p40"] = False
    d["high_days"] = False
    d["high_days_floor"] = False
    d["high_total_days"] = False
    d["high_days_per_adult"] = False
    d["labor_resid"] = np.nan
    d["size_q"] = np.nan
    d["high_within_size"] = False

    for country, idx in d.groupby("country").groups.items():
        idx = list(idx)
        sub = d.loc[idx]
        m = sub["in_sample"]
        if m.sum() < 50:
            continue
        d.loc[idx, "small_rel"] = False
        d.loc[sub.index[m], "small_rel"] = _within_flag(sub.loc[m, "farm_size"], 0.25, "le").to_numpy()
        d.loc[sub.index[m], "low_p25"] = _within_flag(sub.loc[m, "totcons_USD"], 0.25, "le").to_numpy()
        d.loc[sub.index[m], "low_p40"] = _within_flag(sub.loc[m, "totcons_USD"], 0.40, "le").to_numpy()
        d.loc[sub.index[m], "high_days"] = _within_flag(sub.loc[m, "days_per_ha"], 0.75, "ge").to_numpy()
        floor = sub.loc[m, "days_per_ha_floor"]
        if floor.notna().sum() > 50:
            d.loc[sub.index[m], "high_days_floor"] = _within_flag(floor, 0.75, "ge").fillna(False).to_numpy()
        d.loc[sub.index[m], "high_total_days"] = _within_flag(sub.loc[m, "family_days"], 0.75, "ge").to_numpy()
        per_ad = sub.loc[m, "family_days_per_adult"]
        ok = per_ad.notna()
        flag = pd.Series(False, index=sub.index[m])
        if ok.sum() > 50:
            flag.loc[ok] = _within_flag(per_ad[ok], 0.75, "ge")
        d.loc[sub.index[m], "high_days_per_adult"] = flag.to_numpy()

        use = m & (sub["days_per_ha"] > 0) & (sub["farm_size"] > 0)
        if use.sum() > 50:
            y = np.log(sub.loc[use, "days_per_ha"].to_numpy())
            x = np.column_stack([np.ones(use.sum()), np.log(sub.loc[use, "farm_size"].to_numpy())])
            beta, *_ = np.linalg.lstsq(x, y, rcond=None)
            fitted = x @ beta
            d.loc[sub.index[use], "labor_resid"] = y - fitted

        sq = pd.Series(np.nan, index=sub.index)
        try:
            sq.loc[m] = pd.qcut(sub.loc[m, "farm_size"], 4, labels=False, duplicates="drop")
        except ValueError:
            pass
        d.loc[idx, "size_q"] = sq
        for q, qidx in sub[m].groupby(sq[m]).groups.items():
            if pd.isna(q):
                continue
            d.loc[qidx, "high_within_size"] = _within_flag(d.loc[qidx, "days_per_ha"], 0.75, "ge").to_numpy()

    d["small_abs"] = d["farm_size"] < 1
    # National quintiles are not usable in Nigeria wave 4: the variable only
    # takes values 1 and 2. Low consumption in the preferred definition is the
    # bottom 40 percent of per-capita consumption among agricultural households
    # in the same country, which is the within-agriculture analogue of the
    # bottom two quintiles.
    n_quint = d.groupby("country")["cons_quint"].transform(lambda s: s.nunique(dropna=True))
    d["low_nat"] = d["in_sample"] & d["cons_quint"].isin([1, 2]) & (n_quint >= 5)
    d["low_q"] = d["low_p40"].fillna(False).astype(bool)
    resid_cut = d.groupby("country")["labor_resid"].transform(lambda s: s.quantile(0.75))
    d["high_resid"] = d["labor_resid"].notna() & (d["labor_resid"] >= resid_cut)
    low_cut = d.groupby("country")["labor_resid"].transform(lambda s: s.quantile(0.50))
    d["low_resid"] = d["labor_resid"].notna() & (d["labor_resid"] <= low_cut)

    # Preferred target: small and poor, and labor-intensive given farm size.
    d["target"] = d["in_sample"] & d["small_rel"] & d["low_q"] & d["high_resid"]
    # Naive target uses raw days/ha and therefore re-selects small farms.
    d["naive_target"] = d["in_sample"] & d["small_rel"] & d["low_q"] & d["high_days"]
    d["within_target"] = d["in_sample"] & d["small_rel"] & d["low_q"] & d["high_within_size"]
    d["abs_target"] = d["in_sample"] & d["small_abs"] & d["low_q"] & d["high_resid"]
    d["target_nat"] = d["in_sample"] & d["small_rel"] & d["low_nat"] & d["high_resid"]

    # Cutoffs use the analysis sample only, so households missing labor or
    # consumption do not move the farm-size or asset thresholds.
    sample = d["in_sample"]
    asset_med = pd.Series(np.nan, index=d.index)
    farm_p75 = pd.Series(np.nan, index=d.index)
    for _, idx in d.loc[sample].groupby("country").groups.items():
        asset_med.loc[idx] = d.loc[idx, "ag_asset_index"].quantile(0.50)
        farm_p75.loc[idx] = d.loc[idx, "farm_size"].quantile(0.75)
    d["larger_hired_asset"] = (
        d["in_sample"]
        & ~d["target"]
        & (d["farm_size"] >= farm_p75)
        & (d["any_hired"] == 1)
        & d["ag_asset_index"].notna()
        & (d["ag_asset_index"] >= asset_med)
    )
    d["small_poor_low_labor"] = (
        d["in_sample"] & d["small_rel"] & d["low_q"] & d["low_resid"] & ~d["target"]
    )
    d["rest"] = d["in_sample"] & ~d["target"]
    d["all_ag"] = d["in_sample"]
    return d


def _eq_country_median(s: pd.DataFrame, col: str) -> float:
    v = s.groupby("country")[col].median()
    return float(v.mean()) if len(v) else np.nan


def _eq_country_mean(s: pd.DataFrame, col: str) -> float:
    v = s.groupby("country")[col].mean()
    return float(v.mean()) if len(v) else np.nan


def profile_table(d: pd.DataFrame) -> pd.DataFrame:
    median_cols = [
        "farm_size", "totcons_USD", "days_per_ha", "family_days",
        "family_days_per_adult", "hired_days", "yield_kg_ha", "yield_usd_ha",
        "usd_per_family_day", "share_kg_sold", "ag_asset_index", "hh_size",
        "hh_dependency_ratio", "HDDS", "harvest_usd", "labor_area",
    ]
    share_cols = [
        "any_hired", "tractor_any", "any_inorg", "any_organic", "any_pest",
        "any_irrig", "any_female_mgr", "sold_any", "livestock_any",
        "nonfarm_enterprise", "hh_shock", "hh_electricity_access", "urban",
        "any_intercrop",
    ]
    rows = []
    masks = {name: d[name] if name != "all_ag" else d["all_ag"] for name in GROUPS}
    for group, mask in masks.items():
        for country, g in d.loc[mask].groupby("country"):
            rec = {"group": group, "country": country, "n": int(len(g))}
            w = g["pw"]
            rec["weight_sum"] = float(w.sum(min_count=1)) if w.notna().any() else np.nan
            for col in median_cols:
                rec[f"med_{col}"] = float(g[col].median()) if g[col].notna().any() else np.nan
            for col in share_cols:
                rec[f"share_{col}"] = float(g[col].mean()) if g[col].notna().any() else np.nan
                rec[f"n_{col}"] = int(g[col].notna().sum())
            rows.append(rec)
        # Equal-country summary row.
        g = d.loc[mask]
        rec = {"group": group, "country": "_equal_country_mean", "n": int(len(g))}
        for col in median_cols:
            rec[f"med_{col}"] = _eq_country_median(g, col)
        for col in share_cols:
            rec[f"share_{col}"] = _eq_country_mean(g, col)
        rows.append(rec)
    return pd.DataFrame(rows)


def definition_overlap(d: pd.DataFrame) -> pd.DataFrame:
    s = d[d["in_sample"]]
    flags = {
        "small_rel": "small_rel",
        "small_abs_lt1ha": "small_abs",
        "low_cons_p40_within_ag": "low_q",
        "low_cons_p25": "low_p25",
        "low_national_quintile_1_2": "low_nat",
        "high_days_per_ha": "high_days",
        "high_residual_labor": "high_resid",
        "high_within_size_quartile": "high_within_size",
        "high_total_family_days": "high_total_days",
        "high_days_per_adult": "high_days_per_adult",
        "target_resid": "target",
        "target_naive_days": "naive_target",
        "target_within_size": "within_target",
        "target_abs_land": "abs_target",
        "target_national_quintile": "target_nat",
        "larger_hired_asset": "larger_hired_asset",
        "small_poor_low_labor": "small_poor_low_labor",
    }
    rows = []
    for label, col in flags.items():
        m = s[col].fillna(False).astype(bool)
        rows.append({
            "definition": label,
            "n": int(m.sum()),
            "share": float(m.mean()),
            "equal_country_share": _eq_country_mean(s.assign(_f=m.to_numpy()), "_f"),
            "med_farm": float(s.loc[m, "farm_size"].median()) if m.any() else np.nan,
            "med_cons": float(s.loc[m, "totcons_USD"].median()) if m.any() else np.nan,
            "med_days_ha": float(s.loc[m, "days_per_ha"].median()) if m.any() else np.nan,
            "med_family_days": float(s.loc[m, "family_days"].median()) if m.any() else np.nan,
        })
    # Conditional overlap: of raw high-days households, how many are small.
    high = s["high_days"].fillna(False).astype(bool)
    small = s["small_rel"].fillna(False).astype(bool)
    rows.append({
        "definition": "share_of_high_days_who_are_small",
        "n": int((high & small).sum()),
        "share": float((small[high]).mean()) if high.any() else np.nan,
        "equal_country_share": _eq_country_mean(s.loc[high].assign(_f=small[high].to_numpy()), "_f") if high.any() else np.nan,
        "med_farm": np.nan, "med_cons": np.nan, "med_days_ha": np.nan, "med_family_days": np.nan,
    })
    both = s["target"] | s["naive_target"]
    inter = s["target"] & s["naive_target"]
    rows.append({
        "definition": "jaccard_target_vs_naive",
        "n": int(inter.sum()),
        "share": float(inter.sum() / both.sum()) if both.sum() else np.nan,
        "equal_country_share": np.nan,
        "med_farm": np.nan, "med_cons": np.nan, "med_days_ha": np.nan, "med_family_days": np.nan,
    })
    return pd.DataFrame(rows)


def size_gradient(d: pd.DataFrame) -> pd.DataFrame:
    s = d[d["in_sample"]].copy()
    rows = []
    for country, g in s.groupby("country"):
        try:
            g = g.copy()
            g["q"] = pd.qcut(g["farm_size"], 5, labels=False, duplicates="drop")
        except ValueError:
            continue
        for q, sub in g.groupby("q"):
            rows.append({
                "country": country,
                "size_quintile": int(q) + 1,
                "n": int(len(sub)),
                "med_farm": float(sub["farm_size"].median()),
                "med_days_ha": float(sub["days_per_ha"].median()),
                "med_family_days": float(sub["family_days"].median()),
                "med_days_per_adult": float(sub["family_days_per_adult"].median()),
                "med_yield_usd_ha": float(sub["yield_usd_ha"].median()),
                "share_hired": float(sub["any_hired"].mean()),
            })
    return pd.DataFrame(rows)


def _prep_reg(d: pd.DataFrame) -> pd.DataFrame:
    r = d[d["in_sample"]].copy()
    crop = r["hh_main_crop"].astype("string").str.strip()
    r["crop"] = crop.mask(crop.isna() | (crop == ""), "missing")
    # Keep the harmonized crop groups. Anything unexpected is already a group label.
    r["log_farm"] = np.log(r["farm_size"].where(r["farm_size"] > 0))
    r["log_days_ha"] = np.log(r["days_per_ha"].where(r["days_per_ha"] > 0))
    r["log_cons"] = np.log(r["totcons_USD"].where(r["totcons_USD"] > 0))
    r["log_hh"] = np.log(r["hh_size"].where(r["hh_size"] > 0))
    r["asinh_family_days"] = np.arcsinh(r["family_days"])
    r["log_yield_usd"] = np.log(r["yield_usd_ha"].where(r["yield_usd_ha"] > 0))
    r["log_usd_day"] = np.log(r["usd_per_family_day"].where(r["usd_per_family_day"] > 0))
    r["low_q_num"] = r["low_q"].astype(float)
    r["target_num"] = r["target"].astype(float)
    r["naive_num"] = r["naive_target"].astype(float)
    r["ea_cluster"] = r["country"].astype(str) + ":" + r["ea_id_obs"].astype(str)
    r.loc[r["ea_id_obs"].isna(), "ea_cluster"] = (
        r.loc[r["ea_id_obs"].isna(), "country"].astype(str)
        + ":hh:"
        + r.loc[r["ea_id_obs"].isna(), "hh_id_obs"].astype(str)
    )
    # Within-country z-score of the asset index, so the unit is comparable.
    r["asset_z"] = r.groupby("country")["ag_asset_index"].transform(
        lambda s: (s - s.mean()) / s.std(ddof=0) if s.std(ddof=0) not in (0, np.nan) else np.nan
    )
    return r


def _fit(formula: str, data: pd.DataFrame, label: str) -> list[dict]:
    d = data.dropna(subset=["ea_cluster"]).copy()
    try:
        mod = smf.ols(formula, data=d)
        used = mod.fit()
        groups = d.loc[used.model.data.row_labels, "ea_cluster"]
        res = mod.fit(cov_type="cluster", cov_kwds={"groups": groups})
    except Exception as exc:  # noqa: BLE001 — recorded and skipped, not hidden as a result
        return [{"model": label, "term": "_error", "coef": np.nan, "se": np.nan, "pval": np.nan,
                 "n": int(len(d)), "r2": np.nan, "note": str(exc)}]
    rows = []
    for term in res.params.index:
        rows.append({
            "model": label,
            "term": term,
            "coef": float(res.params[term]),
            "se": float(res.bse[term]),
            "pval": float(res.pvalues[term]),
            "n": int(res.nobs),
            "r2": float(res.rsquared),
            "note": "",
        })
    return rows


def run_models(d: pd.DataFrame) -> pd.DataFrame:
    r = _prep_reg(d)
    specs = [
        ("elasticity_days", "log_days_ha ~ log_farm + C(country)", r),
        ("days_ha_full", "log_days_ha ~ log_farm + low_q_num + log_hh + hh_dependency_ratio + urban + C(crop) + C(country)", r),
        ("total_days_full", "asinh_family_days ~ log_farm + low_q_num + log_hh + hh_dependency_ratio + urban + C(crop) + C(country)", r),
        ("days_ha_assets_sales", "log_days_ha ~ log_farm + asset_z + any_hired + share_kg_sold + low_q_num + C(crop) + C(country)", r),
        ("hired_on_target", "any_hired ~ target_num + C(country)", r),
        ("hired_on_target_ctrl", "any_hired ~ target_num + log_farm + log_cons + log_hh + urban + C(crop) + C(country)", r),
        ("tractor_on_target", "tractor_any ~ target_num + C(country)", r),
        ("tractor_on_target_ctrl", "tractor_any ~ target_num + log_farm + log_cons + log_hh + urban + C(crop) + C(country)", r),
        ("fert_on_target", "any_inorg ~ target_num + C(country)", r),
        ("fert_on_target_ctrl", "any_inorg ~ target_num + log_farm + log_cons + log_hh + urban + C(crop) + C(country)", r),
        ("yield_on_target", "log_yield_usd ~ target_num + C(country)", r),
        ("yield_on_target_ctrl", "log_yield_usd ~ target_num + log_farm + log_cons + log_hh + urban + C(crop) + C(country)", r),
        ("prod_on_target", "log_usd_day ~ target_num + C(country)", r),
        ("prod_on_target_ctrl", "log_usd_day ~ target_num + log_farm + log_cons + log_hh + urban + C(crop) + C(country)", r),
        ("sold_on_target", "share_kg_sold ~ target_num + C(country)", r),
        ("sold_on_target_ctrl", "share_kg_sold ~ target_num + log_farm + log_cons + log_hh + urban + C(crop) + C(country)", r),
        ("hired_on_naive", "any_hired ~ naive_num + C(country)", r),
        ("yield_on_naive", "log_yield_usd ~ naive_num + C(country)", r),
    ]
    rows = []
    for label, formula, data in specs:
        rows.extend(_fit(formula, data, label))
    # Country-by-country elasticity, to see whether Nigeria's scale drives the pool.
    for country, g in r.groupby("country"):
        rows.extend(_fit("log_days_ha ~ log_farm", g, f"elasticity_{country}"))
    return pd.DataFrame(rows)


def country_gaps(d: pd.DataFrame) -> pd.DataFrame:
    """Target minus the small-and-poor low-labor group, by country.

    Land and consumption are held in the same bands, so a labor gap is
    definitional. Hired labor, assets, yield, and labor productivity are not.
    """
    rows = []
    metrics = {
        "days_per_ha": "median",
        "family_days": "median",
        "yield_usd_ha": "median",
        "yield_kg_ha": "median",
        "usd_per_family_day": "median",
        "ag_asset_index": "median",
        "share_kg_sold": "median",
        "any_hired": "mean",
        "tractor_any": "mean",
        "any_inorg": "mean",
        "any_pest": "mean",
        "any_female_mgr": "mean",
        "farm_size": "median",
        "totcons_USD": "median",
    }
    for country, g in d[d["in_sample"]].groupby("country"):
        a = g[g["target"]]
        b = g[g["small_poor_low_labor"]]
        c = g[g["rest"]]
        e = g[g["larger_hired_asset"]]
        rec = {"country": country, "n_target": int(len(a)), "n_low_labor": int(len(b)),
               "n_rest": int(len(c)), "n_larger": int(len(e))}
        for col, how in metrics.items():
            fn = "median" if how == "median" else "mean"
            rec[f"target_{col}"] = getattr(a[col], fn)() if a[col].notna().any() else np.nan
            rec[f"low_{col}"] = getattr(b[col], fn)() if len(b) and b[col].notna().any() else np.nan
            rec[f"rest_{col}"] = getattr(c[col], fn)() if c[col].notna().any() else np.nan
            rec[f"larger_{col}"] = getattr(e[col], fn)() if len(e) and e[col].notna().any() else np.nan
            rec[f"gap_vs_low_{col}"] = rec[f"target_{col}"] - rec[f"low_{col}"]
        day_gap = rec["gap_vs_low_days_per_ha"]
        rec["usd_per_extra_day"] = (
            rec["gap_vs_low_yield_usd_ha"] / day_gap if pd.notna(day_gap) and day_gap > 0 else np.nan
        )
        rows.append(rec)
    return pd.DataFrame(rows)


def crop_contrast(d: pd.DataFrame) -> pd.DataFrame:
    s = d[d["in_sample"] & (d["target"] | d["small_poor_low_labor"])].copy()
    s["arm"] = np.where(s["target"], "target", "small_poor_low_labor")
    rows = []
    for crop, g in s.groupby(s["hh_main_crop"].astype("string").fillna("missing")):
        for arm, sub in g.groupby("arm"):
            rows.append({
                "crop": str(crop),
                "arm": arm,
                "n": int(len(sub)),
                "med_days_ha": float(sub["days_per_ha"].median()),
                "med_yield_kg_ha": float(sub["yield_kg_ha"].median()),
                "med_yield_usd_ha": float(sub["yield_usd_ha"].median()),
                "med_usd_day": float(sub["usd_per_family_day"].median()),
                "share_hired": float(sub["any_hired"].mean()) if sub["any_hired"].notna().any() else np.nan,
                "share_tractor": float(sub["tractor_any"].mean()) if sub["tractor_any"].notna().any() else np.nan,
            })
    return pd.DataFrame(rows)


def alkire_foster(d: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Equal-weight five-indicator index. Cutoffs are normative and stated
    in the report. k = 3/5 is the primary poverty line, with k = 2 and 4."""
    s = d[d["in_sample"]].copy()
    asset_cut = s.groupby("country")["ag_asset_index"].transform(lambda x: x.quantile(0.40))
    s["d_land"] = (s["farm_size"] < 1).astype(float)
    s["d_cons"] = s["low_q"].astype(float)
    s["d_labor"] = s["high_resid"].astype(float)
    s["d_asset"] = np.where(s["ag_asset_index"].notna(), (s["ag_asset_index"] <= asset_cut).astype(float), np.nan)
    s["d_subst"] = np.where(
        s["any_hired"].notna() & s["tractor_any"].notna(),
        ((s["any_hired"] == 0) & (s["tractor_any"] == 0)).astype(float),
        np.nan,
    )
    dims = ["d_land", "d_cons", "d_labor", "d_asset", "d_subst"]
    raw_rows = []
    for country, g in s.groupby("country"):
        rec = {"country": country, "n": int(len(g))}
        for dim in dims:
            rec[f"raw_{dim}"] = float(g[dim].mean())
            rec[f"n_{dim}"] = int(g[dim].notna().sum())
        raw_rows.append(rec)
    raw = pd.DataFrame(raw_rows)

    m0_rows = []
    use = s.dropna(subset=dims).copy()
    for k_count in (2, 3, 4):
        k = k_count / len(dims)
        for country, g in list(use.groupby("country")) + [("_pooled", use)]:
            share = g[dims].mean(axis=1)  # equal weights
            poor = share >= k
            h = float(poor.mean())
            a = float(share[poor].mean()) if poor.any() else np.nan
            rec = {
                "k_indicators": k_count,
                "country": country if isinstance(country, str) else country,
                "n": int(len(g)),
                "H": h,
                "A": a,
                "M0": h * a if pd.notna(a) else np.nan,
            }
            for dim in dims:
                rec[f"cens_{dim}"] = float(((g[dim] == 1) & poor).mean())
            m0_rows.append(rec)
    # Version without the labor indicator, so the index is not the target definition.
    dims2 = ["d_land", "d_cons", "d_asset", "d_subst"]
    use2 = s.dropna(subset=dims2).copy()
    for k_count in (2, 3):
        k = k_count / len(dims2)
        for country, g in list(use2.groupby("country")) + [("_pooled", use2)]:
            share = g[dims2].mean(axis=1)
            poor = share >= k
            h = float(poor.mean())
            a = float(share[poor].mean()) if poor.any() else np.nan
            m0_rows.append({
                "k_indicators": k_count,
                "country": country,
                "n": int(len(g)),
                "H": h,
                "A": a,
                "M0": h * a if pd.notna(a) else np.nan,
                "index": "no_labor_dimension",
            })
    m0 = pd.DataFrame(m0_rows)
    m0["index"] = m0["index"].fillna("five_dimension") if "index" in m0.columns else "five_dimension"
    return raw, m0


def sample_flow(season_n: int, d: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for country, g in d.groupby("country"):
        rows.append({
            "country": country,
            "wave": LATEST_WAVE[country],
            "n_households": int(len(g)),
            "n_sample": int(g["in_sample"].sum()),
            "share_two_seasons": float((g["n_seasons"] > 1).mean()),
            "n_target": int(g["target"].sum()),
            "n_naive": int(g["naive_target"].sum()),
            "n_low_labor": int(g["small_poor_low_labor"].sum()),
            "n_larger": int(g["larger_hired_asset"].sum()),
            "share_target": float(g.loc[g["in_sample"], "target"].mean()),
            "pw_share_target": _pw_share(g.loc[g["in_sample"]]),
            "miss_tractor": float(g["tractor_any"].isna().mean()),
            "miss_asset": float(g["ag_asset_index"].isna().mean()),
            "miss_sold": float(g["share_kg_sold"].isna().mean()),
            "miss_hired": float(g["any_hired"].isna().mean()),
        })
    return pd.DataFrame(rows)


def _pw_share(g: pd.DataFrame) -> float:
    m = g["pw"].notna() & g["target"].notna()
    if m.sum() == 0 or g.loc[m, "pw"].sum() == 0:
        return np.nan
    return float(g.loc[m & g["target"], "pw"].sum() / g.loc[m, "pw"].sum())


def make_figures(d: pd.DataFrame, gaps: pd.DataFrame) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    s = d[d["in_sample"] & (d["days_per_ha"] > 0) & (d["farm_size"] > 0)].copy()
    fig, ax = plt.subplots(figsize=(8.2, 5.2))
    for country, g in s.groupby("country"):
        try:
            g = g.copy()
            g["bin"] = pd.qcut(g["farm_size"], 8, duplicates="drop")
        except ValueError:
            continue
        med = g.groupby("bin", observed=True).agg(farm=("farm_size", "median"), days=("days_per_ha", "median"))
        ax.plot(med["farm"], med["days"], marker="o", lw=1.2, ms=3.5, label=country)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Farm size (ha), bin median")
    ax.set_ylabel("Family labor days per ha, bin median")
    ax.set_title("Family labor intensity falls as farm size rises")
    ax.legend(frameon=False, fontsize=8, ncol=2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "days_per_ha_by_farm_size.png", dpi=160)
    plt.close(fig)

    # Gaps versus the small, poor, low-labor group. Labor days are definitional.
    plot_cols = [
        ("gap_vs_low_any_hired", "Hired labor (share)"),
        ("gap_vs_low_tractor_any", "Tractor (share)"),
        ("gap_vs_low_any_inorg", "Inorganic fertilizer (share)"),
        ("gap_vs_low_any_female_mgr", "Female plot manager (share)"),
    ]
    fig, ax = plt.subplots(figsize=(8.2, 5.0))
    countries = gaps["country"].tolist()
    y = np.arange(len(plot_cols))
    for _, row in gaps.iterrows():
        vals = [row[c] * 100 for c, _ in plot_cols]
        ax.plot(vals, y, "o", ms=5, color="#9aa0a6", zorder=2)
    means = [gaps[c].mean() * 100 for c, _ in plot_cols]
    ax.plot(means, y, "D", ms=7, color="#1a365d", label="Equal-country mean", zorder=3)
    ax.axvline(0, color="#444", lw=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels([lab for _, lab in plot_cols])
    ax.set_xlabel("Target minus small-poor low-labor group (percentage points)")
    ax.set_title("Among small, low-consumption farms, what else differs")
    ax.legend(frameon=False, loc="lower right")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "gaps_among_small_poor.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    order = gaps.sort_values("gap_vs_low_any_hired")
    ax.barh(order["country"], order["gap_vs_low_any_hired"] * 100, color="#1a365d")
    ax.axvline(0, color="#444", lw=0.8)
    ax.set_xlabel("Hired-labor share, target minus small-poor low-labor (pp)")
    ax.set_title("Hired labor gap by country")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "hired_gap_by_country.png", dpi=160)
    plt.close(fig)


def _coef(models: pd.DataFrame, model: str, term: str) -> dict:
    hit = models[(models["model"] == model) & (models["term"] == term)]
    if hit.empty:
        return {}
    row = hit.iloc[0]
    return {"coef": round(float(row["coef"]), 4), "se": round(float(row["se"]), 4),
            "pval": float(row["pval"]), "n": int(row["n"]), "r2": round(float(row["r2"]), 3)}


def digest(d: pd.DataFrame, models: pd.DataFrame, gaps: pd.DataFrame, flow: pd.DataFrame) -> dict:
    s = d[d["in_sample"]]
    out = {
        "n_sample": int(len(s)),
        "n_target": int(s["target"].sum()),
        "n_naive": int(s["naive_target"].sum()),
        "n_low": int(s["small_poor_low_labor"].sum()),
        "n_larger": int(s["larger_hired_asset"].sum()),
        "share_target_unweighted": float(s["target"].mean()),
        "share_target_equal_country": _eq_country_mean(s, "target"),
        "pw_share_by_country": {r.country: r.pw_share_target for r in flow.itertuples()},
        "elasticity_pooled": _coef(models, "elasticity_days", "log_farm"),
        "elasticity_by_country": {
            c: _coef(models, f"elasticity_{c}", "log_farm") for c in LATEST_WAVE
        },
        "days_full_log_farm": _coef(models, "days_ha_full", "log_farm"),
        "days_full_low_q": _coef(models, "days_ha_full", "low_q_num"),
        "total_days_log_farm": _coef(models, "total_days_full", "log_farm"),
        "days_asset": _coef(models, "days_ha_assets_sales", "asset_z"),
        "days_hired": _coef(models, "days_ha_assets_sales", "any_hired"),
        "days_sold": _coef(models, "days_ha_assets_sales", "share_kg_sold"),
        "hired_target": _coef(models, "hired_on_target", "target_num"),
        "hired_target_ctrl": _coef(models, "hired_on_target_ctrl", "target_num"),
        "tractor_target": _coef(models, "tractor_on_target", "target_num"),
        "tractor_target_ctrl": _coef(models, "tractor_on_target_ctrl", "target_num"),
        "fert_target": _coef(models, "fert_on_target", "target_num"),
        "fert_target_ctrl": _coef(models, "fert_on_target_ctrl", "target_num"),
        "yield_target": _coef(models, "yield_on_target", "target_num"),
        "yield_target_ctrl": _coef(models, "yield_on_target_ctrl", "target_num"),
        "prod_target": _coef(models, "prod_on_target", "target_num"),
        "prod_target_ctrl": _coef(models, "prod_on_target_ctrl", "target_num"),
        "sold_target": _coef(models, "sold_on_target", "target_num"),
        "sold_target_ctrl": _coef(models, "sold_on_target_ctrl", "target_num"),
        "equal_country_medians": {},
        "gap_signs": {},
    }
    for group in ("target", "small_poor_low_labor", "rest", "larger_hired_asset"):
        g = s[s[group]] if group != "rest" else s[s["rest"]]
        out["equal_country_medians"][group] = {
            "days_per_ha": _eq_country_median(g, "days_per_ha"),
            "family_days": _eq_country_median(g, "family_days"),
            "farm_size": _eq_country_median(g, "farm_size"),
            "cons": _eq_country_median(g, "totcons_USD"),
            "yield_usd_ha": _eq_country_median(g, "yield_usd_ha"),
            "yield_kg_ha": _eq_country_median(g, "yield_kg_ha"),
            "usd_per_day": _eq_country_median(g, "usd_per_family_day"),
            "share_hired": _eq_country_mean(g, "any_hired"),
            "share_tractor": _eq_country_mean(g, "tractor_any"),
            "share_fert": _eq_country_mean(g, "any_inorg"),
            "share_sold": _eq_country_mean(g, "sold_any"),
            "asset": _eq_country_median(g, "ag_asset_index"),
        }
    for col in ["any_hired", "tractor_any", "any_inorg", "yield_usd_ha", "usd_per_family_day", "days_per_ha"]:
        gap = gaps[f"gap_vs_low_{col}"]
        out["gap_signs"][col] = {
            "n_neg": int((gap < 0).sum()),
            "n_pos": int((gap > 0).sum()),
            "n_countries": int(gap.notna().sum()),
            "equal_country_mean_gap": float(gap.mean()),
        }
    return out


def main() -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    frame = pd.read_pickle(FRAME_PATH)
    # Fail loudly if the yes/no recode did not land.
    if frame["tractor_any"].notna().sum() < 1000:
        raise RuntimeError("tractor_any is empty; rerun audit_build.py after the yes/no fix")
    hh = select_latest(frame)
    d = add_definitions(hh)
    d.to_pickle(OUT_DIR / "analysis_sample.pkl")

    flow = sample_flow(0, d)
    overlap = definition_overlap(d)
    profiles = profile_table(d)
    gradient = size_gradient(d)
    models = run_models(d)
    gaps = country_gaps(d)
    crops = crop_contrast(d)
    raw, m0 = alkire_foster(d)

    flow.to_csv(TABLE_DIR / "sample_by_country.csv", index=False)
    overlap.to_csv(TABLE_DIR / "definition_overlap.csv", index=False)
    profiles.to_csv(TABLE_DIR / "group_profiles.csv", index=False)
    gradient.to_csv(TABLE_DIR / "days_by_size_quintile.csv", index=False)
    models.to_csv(TABLE_DIR / "regression_coefficients.csv", index=False)
    gaps.to_csv(TABLE_DIR / "country_gaps.csv", index=False)
    crops.to_csv(TABLE_DIR / "crop_contrast.csv", index=False)
    raw.to_csv(TABLE_DIR / "af_raw_deprivation.csv", index=False)
    m0.to_csv(TABLE_DIR / "af_m0.csv", index=False)

    summary = digest(d, models, gaps, flow)
    (OUT_DIR / "results_digest.json").write_text(json.dumps(summary, indent=2, default=str))
    make_figures(d, gaps)
    print(json.dumps({k: summary[k] for k in [
        "n_sample", "n_target", "n_naive", "n_low", "n_larger",
        "share_target_equal_country", "elasticity_pooled", "gap_signs",
        "equal_country_medians",
    ]}, indent=2, default=str))


if __name__ == "__main__":
    main()
