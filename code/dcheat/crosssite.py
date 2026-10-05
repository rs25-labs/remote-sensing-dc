"""Cross-site analysis: pre-construction setting, cluster collapsing, sign test, and regression."""

import numpy as np
import pandas as pd
from scipy import stats as sps

COVER_GROUPS = {
    "forest": [41, 42, 43], "crop": [82], "pasture": [81], "grass_shrub": [52, 71],
    "barren": [31], "developed": [21, 22, 23, 24], "wetland": [90, 95], "water": [11],
}
DRY_ARIDITY = 0.5   # precipitation / potential evapotranspiration below this is semi-arid or drier


def precon_cover(labels: pd.DataFrame, construction_years: dict) -> pd.DataFrame:
    """Cover fractions from the latest NLCD year before construction (earliest year if none is),
    the dominant cover group, aridity, and a moisture setting: humid, dry natural, dry irrigated."""
    rows = []
    for site_id, site in labels.groupby("site_id"):
        year = construction_years.get(site_id)
        before = site[site["nlcd_year"] < year] if year is not None and not pd.isna(year) else site.iloc[0:0]
        chosen = before.loc[before["nlcd_year"].idxmax()] if len(before) else site.loc[site["nlcd_year"].idxmin()]
        fractions = {
            f"frac_{group}": float(sum(chosen.get(f"nlcd_{code}", 0.0) for code in codes))
            for group, codes in COVER_GROUPS.items()
        }
        dominant = max(fractions, key=fractions.get).removeprefix("frac_")
        aridity = float(chosen["aridity"])
        if aridity >= DRY_ARIDITY:
            setting = "humid"
        elif fractions["frac_crop"] + fractions["frac_pasture"] >= 0.5:
            setting = "dry irrigated"
        else:
            setting = "dry natural"
        rows.append({"site_id": site_id, "nlcd_year_used": int(chosen["nlcd_year"]), **fractions,
                     "dominant_cover": dominant, "aridity": aridity, "setting": setting})
    return pd.DataFrame(rows)


def collapse_clusters(df: pd.DataFrame, value_cols: list[str]) -> pd.DataFrame:
    """One row per cluster: mean of ``value_cols``; ``unit`` joins the member site ids."""
    grouped = df.groupby("cluster_id")
    out = grouped[value_cols].mean()
    out["unit"] = grouped["site_id"].agg(lambda ids: "+".join(ids))
    out["n_sites"] = grouped.size()
    for col in df.columns.difference(value_cols + ["site_id", "cluster_id"]):
        out[col] = grouped[col].first()
    return out.reset_index(drop=True)


def sign_test(df: pd.DataFrame, flag_col: str, value_col: str = "dlst") -> dict:
    """2x2 table of cooling vs warming by ``flag_col``, with a two-sided Fisher exact p-value."""
    cool = df[value_col] < 0
    flag = df[flag_col].astype(bool)
    table = {"dry_cool": int((flag & cool).sum()), "dry_warm": int((flag & ~cool).sum()),
             "other_cool": int((~flag & cool).sum()), "other_warm": int((~flag & ~cool).sum())}
    p = sps.fisher_exact([[table["dry_cool"], table["dry_warm"]],
                          [table["other_cool"], table["other_warm"]]]).pvalue
    return {"table": table, "p": float(p)}


def _fit(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    design = np.column_stack([np.ones(len(x)), x])
    return np.linalg.lstsq(design, y, rcond=None)[0]


def ols_bootstrap(df: pd.DataFrame, y: str, xs: list[str], n: int = 5000, seed: int = 0) -> pd.DataFrame:
    """OLS coefficients with 95% CIs from resampling whole units (rows) with replacement."""
    data = df[[y] + xs].dropna()
    x, target = data[xs].to_numpy(dtype=float), data[y].to_numpy(dtype=float)
    coefs = _fit(x, target)
    residual = target - np.column_stack([np.ones(len(x)), x]) @ coefs
    r2 = 1 - residual.var() / target.var()
    rng = np.random.default_rng(seed)
    draws = []
    for _ in range(n):
        idx = rng.integers(0, len(data), len(data))
        draws.append(_fit(x[idx], target[idx]))
    lo, hi = np.percentile(np.array(draws), [2.5, 97.5], axis=0)
    out = pd.DataFrame({"coef": coefs, "ci_lo": lo, "ci_hi": hi}, index=["intercept"] + xs)
    out.attrs.update({"r2": float(r2), "n": len(data)})
    return out


def permutation_test(values: np.ndarray, flags: np.ndarray, n: int = 10000, seed: int = 0) -> dict:
    """Difference in means (flagged minus unflagged) with a two-sided p from shuffling the flags."""
    values, flags = np.asarray(values, dtype=float), np.asarray(flags, dtype=bool)
    diff = values[flags].mean() - values[~flags].mean()
    rng = np.random.default_rng(seed)
    shuffled = np.array([
        values[perm].mean() - values[~perm].mean()
        for perm in (rng.permutation(flags) for _ in range(n))
    ])
    p = (np.sum(np.abs(shuffled) >= abs(diff) - 1e-12) + 1) / (n + 1)
    return {"diff": float(diff), "p": float(p)}
