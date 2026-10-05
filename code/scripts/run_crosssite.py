"""Phase 8 cross-site analysis on the census outputs (local copies in outputs/census/)."""

from pathlib import Path

import pandas as pd
from scipy import stats as sps

from dcheat import crosssite

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "census"

if __name__ == "__main__":
    rings = pd.read_csv(OUT / "rings_summary.csv")
    windows_used = pd.read_csv(OUT / "census_windows.csv")
    labels = pd.read_csv(OUT / "site_labels.csv").fillna(0.0)
    sites = pd.read_csv(ROOT / "data" / "census" / "census_sites.csv")

    years = dict(zip(windows_used.site_id, windows_used.construction_year))
    cover = crosssite.precon_cover(labels[labels.site_id.isin(years)], years)
    core = (rings[rings.ring == 0]
            .merge(sites[["site_id", "name", "group", "cluster_id"]], on="site_id")
            .merge(cover, on="site_id"))
    core["significant"] = (core.ci_lo > 0) | (core.ci_hi < 0)
    core.to_csv(OUT / "crosssite_core.csv", index=False)

    cols = ["name", "group", "setting", "dominant_cover", "aridity", "dlst", "ci_lo", "ci_hi", "dndvi", "dalbedo"]
    with pd.option_context("display.width", 200):
        print(core.sort_values("dlst")[cols].to_string(index=False, float_format=lambda v: f"{v:.2f}"))

    green = core[core.group == "greenfield"]
    values = ["dlst", "ci_lo", "ci_hi", "dndvi", "dalbedo", "aridity"]
    units = crosssite.collapse_clusters(green[["site_id", "cluster_id", "setting"] + values], values)
    print(f"\ngreenfield: {len(green)} sites -> {len(units)} independent units")

    print("\nCore change by setting (independent units):")
    print(units.groupby("setting").dlst.agg(["count", "mean", "median", "min", "max"]).round(2).to_string())

    for label, flag in [("dry natural vs everything else", units.setting == "dry natural"),
                        ("any dry (aridity < 0.5) vs humid", units.setting != "humid")]:
        result = crosssite.sign_test(units.assign(flag=flag), "flag")
        print(f"\nSign test, {label}: {result['table']}  Fisher p = {result['p']:.2g}")

    rho, p = sps.spearmanr(units.aridity, units.dlst)
    print(f"\nSpearman, core change vs aridity: rho = {rho:.2f}, p = {p:.2g}")

    for xs in (["dndvi", "dalbedo"], ["dndvi", "dalbedo", "aridity"]):
        fit = crosssite.ols_bootstrap(units, "dlst", xs)
        print(f"\nOLS dlst ~ {' + '.join(xs)}  (n = {fit.attrs['n']}, R^2 = {fit.attrs['r2']:.2f}, unit bootstrap CIs)")
        print(fit.round(2).to_string())
        fit.to_csv(OUT / f"crosssite_ols_{'_'.join(xs)}.csv")
