"""Energy-balance ceiling: how much surface warming a data center's own heat could cause at most.

All electricity a facility draws ends up as heat. Spread over an area it is a heat flux Q (W/m^2). If
all of it entered the surface the satellite sees, the surface would warm by about Q / lambda, where
lambda (W m^-2 K^-1) combines extra longwave emission (4*eps*sigma*T^3, ~6) and convective loss
(~10-25). Turned around, an upper bound on the observed extra warming caps the fraction of the heat
that can be reaching the surface.
"""

import numpy as np
import pandas as pd


def heat_flux(power_mw: float, radius_m: float) -> float:
    """Facility power spread evenly over a disk of ``radius_m``, in W/m^2."""
    return power_mw * 1e6 / (np.pi * radius_m ** 2)


def full_coupling_warming(flux: float, coupling: float = 25.0) -> float:
    """Surface warming (K) if the whole flux entered the surface energy balance."""
    return flux / coupling


def max_coupled_fraction(delta_t_upper: float, flux: float, coupling: float = 25.0) -> float:
    """Largest fraction of the heat flux consistent with at most ``delta_t_upper`` K of extra warming."""
    return max(0.0, delta_t_upper) * coupling / flux


def after_window_power(timeline: pd.DataFrame, start: str, end: str) -> float:
    """Mean facility power (MW) over records in [start, end]; else the latest record before ``start``."""
    dates = timeline["Date"]
    inside = timeline.loc[(dates >= start) & (dates <= end), "Power (MW)"].dropna()
    if len(inside):
        return float(inside.mean())
    before = timeline.loc[dates < start].sort_values("Date")["Power (MW)"].dropna()
    return float(before.iloc[-1]) if len(before) else np.nan
