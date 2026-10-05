"""Baseline and after-window rules for the census, and construction-year detection from Landsat."""

import pandas as pd

from dc_heat import stats

FIRST_LANDSAT_YEAR = 2013


def detect_construction_year(scenes: pd.DataFrame, ndvi_threshold: float = 0.08,
                             albedo_threshold: float = 0.02,
                             reference_years=(2013, 2014, 2015)) -> int | None:
    """First year the core's NDVI or albedo, relative to the far ring, departs from its reference
    level by at least the threshold and is still departed the following year.

    Uses the within-scene core-minus-far contrast, so regional greening or drought cancels.
    """
    flagged = None
    for column, threshold in (("ndvi", ndvi_threshold), ("albedo", albedo_threshold)):
        if column not in scenes.columns:
            continue
        core = stats.within_scene_contrast(scenes, value=column)
        core = core[core["ring"] == 0]
        annual = core.groupby(core["date"].dt.year)["c"].median()
        reference = annual[annual.index.isin(reference_years)].median()
        departed = (annual - reference).abs() >= threshold
        flagged = departed if flagged is None else (flagged | departed.reindex(flagged.index, fill_value=False))
    if flagged is None:
        return None
    candidates = flagged[flagged.index > max(reference_years)]
    years = list(candidates.index)
    for i, year in enumerate(years):
        is_last = i == len(years) - 1
        if candidates[year] and (is_last or candidates[years[i + 1]]):
            return int(year)
    return None


def resolve_construction_year(registry_year, detected=None, announced=None) -> tuple[int | None, str]:
    """Construction year to use, and where it came from.

    A dated year from the registry (Epoch, the paper, or a manual decision) always wins. Otherwise
    take the earlier of the Landsat-detected year and the public announcement year: a baseline that
    ends too early only loses years, while one that ends too late mixes construction into it.
    """
    if registry_year is not None and not pd.isna(registry_year):
        return int(registry_year), "registry"
    options = {"announced": announced, "detected": detected}
    known = {source: int(year) for source, year in options.items() if year is not None and not pd.isna(year)}
    if not known:
        return None, "none"
    source = min(known, key=lambda s: (known[s], s != "announced"))
    return known[source], source


def census_windows(group: str, construction_year: int | None = None,
                   operation_start: pd.Timestamp | None = None, after_years=(2025, 2026),
                   max_base_years: int = 5, min_base_years: int = 2) -> dict:
    """Baseline = up to five years before construction; after = latest years (greenfield) or
    years from operation onward (conversion). ``reason`` is empty when the windows are usable."""
    if construction_year is None or pd.isna(construction_year):
        return {"base_years": [], "op_years": [], "reason": "no construction year"}
    construction_year = int(construction_year)
    base = list(range(max(FIRST_LANDSAT_YEAR, construction_year - max_base_years), construction_year))
    reason = "" if len(base) >= min_base_years else f"baseline shorter than {min_base_years} years"

    if group == "conversion":
        if operation_start is None or pd.isna(operation_start):
            return {"base_years": base, "op_years": [], "reason": "no operation date"}
        first = operation_start.year if operation_start.month <= 3 else operation_start.year + 1
        op = list(range(first, after_years[-1] + 1))
    else:
        op = list(after_years)
        if construction_year >= after_years[0] and not reason:
            reason = "construction began in the after window"
    return {"base_years": base, "op_years": op, "reason": reason}
