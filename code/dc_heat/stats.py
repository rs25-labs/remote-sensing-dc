"""Before/after estimators and uncertainty for ring and point-control LST series.

All functions take tidy DataFrames with a ``date`` column (datetime64) so the same code runs
locally under pytest and in Colab on Earth Engine exports.
"""

import numpy as np
import pandas as pd
from scipy import stats as sps


def within_scene_contrast(scenes: pd.DataFrame, value: str = "lst_c", far_ring: int = 4) -> pd.DataFrame:
    """Return c = value(ring) - value(far_ring) for every inner ring, formed within each scene.

    Scenes where the far ring is missing are dropped rather than filled, because a background
    from another day would not describe the same atmosphere.
    """
    wide = scenes.pivot_table(index="date", columns="ring", values=value, aggfunc="mean")
    if far_ring not in wide.columns:
        raise ValueError(f"far ring {far_ring} is not present in the scenes")
    wide = wide.dropna(subset=[far_ring])
    inner = [ring for ring in wide.columns if ring != far_ring]
    contrast = wide[inner].sub(wide[far_ring], axis=0)
    out = contrast.reset_index().melt(id_vars="date", var_name="ring", value_name="c")
    return out.dropna(subset=["c"]).sort_values(["date", "ring"]).reset_index(drop=True)


def month_demean(df: pd.DataFrame, col: str = "c") -> pd.DataFrame:
    """Subtract the calendar-month mean of ``col`` (per ring when a ring column exists)."""
    out = df.copy()
    keys = [out["date"].dt.month]
    if "ring" in out.columns:
        keys.insert(0, out["ring"])
    out[col + "_prime"] = out[col] - out.groupby(keys)[col].transform("mean")
    return out


def hour_demean(df: pd.DataFrame, col: str = "d", bins=(21, 24, 2, 5)) -> pd.DataFrame:
    """Subtract night hour-bin means of ``col``, using a ``local_hour`` column.

    ``bins`` are bin edges on the clock starting in the evening; the default gives evening
    (21-24 h), around midnight (0-2 h) and pre-dawn (2-5 h). Hours outside the bins are dropped.
    """
    night_edges = [(edge - bins[0]) % 24 for edge in bins]
    night_hour = (df["local_hour"] - bins[0]) % 24
    labels = pd.cut(night_hour, bins=night_edges, right=False, labels=False)
    out = df.assign(hour_bin=labels).dropna(subset=["hour_bin"]).copy()
    out[col + "_prime"] = out[col] - out.groupby("hour_bin")[col].transform("mean")
    return out


def _period_values(df: pd.DataFrame, years, col: str, name: str) -> pd.DataFrame:
    selected = df[df["date"].dt.year.isin(list(years))]
    if selected.empty:
        raise ValueError(f"no scenes in the {name} period {list(years)}")
    return selected


def before_after(df: pd.DataFrame, base_years, op_years, col: str = "c_prime") -> float:
    """Mean of ``col`` in operational years minus its mean in baseline years."""
    base = _period_values(df, base_years, col, "baseline")
    op = _period_values(df, op_years, col, "operational")
    return float(op[col].mean() - base[col].mean())


def bootstrap_ci(base: np.ndarray, op: np.ndarray, n: int = 10_000, seed: int = 0) -> tuple[float, float]:
    """95% percentile bootstrap CI of mean(op) - mean(base), resampling each group independently."""
    rng = np.random.default_rng(seed)
    base, op = np.asarray(base, dtype=float), np.asarray(op, dtype=float)
    base_means = base[rng.integers(0, base.size, (n, base.size))].mean(axis=1)
    op_means = op[rng.integers(0, op.size, (n, op.size))].mean(axis=1)
    lo, hi = np.percentile(op_means - base_means, [2.5, 97.5])
    return float(lo), float(hi)


def _resampled_period_means(values: pd.DataFrame, col: str, n: int, rng) -> np.ndarray:
    """Resample whole years when the period has two or more; otherwise resample scenes."""
    years = values["date"].dt.year
    if years.nunique() < 2:
        x = values[col].to_numpy(dtype=float)
        return x[rng.integers(0, x.size, (n, x.size))].mean(axis=1)
    per_year = values.groupby(years)[col].agg(["sum", "count"])
    sums, counts = per_year["sum"].to_numpy(), per_year["count"].to_numpy()
    picks = rng.integers(0, len(per_year), (n, len(per_year)))
    return sums[picks].sum(axis=1) / counts[picks].sum(axis=1)


def year_block_bootstrap_ci(df: pd.DataFrame, base_years, op_years, col: str = "c_prime",
                            n: int = 10_000, seed: int = 0) -> tuple[float, float]:
    """95% CI that resamples whole years, allowing for correlation between scenes in a year."""
    rng = np.random.default_rng(seed)
    base = _period_values(df, base_years, col, "baseline")
    op = _period_values(df, op_years, col, "operational")
    diffs = _resampled_period_means(op, col, n, rng) - _resampled_period_means(base, col, n, rng)
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return float(lo), float(hi)


def welch_p(base: np.ndarray, op: np.ndarray) -> float:
    """Two-sided Welch unequal-variance t-test p-value."""
    return float(sps.ttest_ind(op, base, equal_var=False).pvalue)


def mde(ci_lo: float, ci_hi: float, power: float = 0.80, alpha: float = 0.05) -> float:
    """Minimum detectable effect implied by a 95% CI, assuming a near-normal sampling distribution."""
    z_alpha = sps.norm.ppf(1 - alpha / 2)
    standard_error = (ci_hi - ci_lo) / (2 * sps.norm.ppf(0.975))
    return float((z_alpha + sps.norm.ppf(power)) * standard_error)
