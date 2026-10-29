"""
Closed-form date-1 policy of a fiat-backed stablecoin issuer.

Independent replication of Section 2.1 of
Goel, Lewrick and Agarwal (2026), "Making stablecoins stable(r): can regulation help?",
BIS Working Paper No 1355.

Notation follows the paper:
    s0      stablecoins outstanding at date 0
    c0, b0  cash and bonds at date 0, k0 capital at date 0  (c0 + b0 = s0 + k0)
    r1      stablecoin flow shock at date 1 (negative = redemptions)
    mu      weekly bond return
    kappa   constant liquidation cost per unit of bonds sold (kappa > mu)
    gamma   AR(1) persistence of flows, sigma their standard deviation
"""
from dataclasses import dataclass

import numpy as np
from scipy.optimize import brentq
from scipy.stats import norm


@dataclass
class Params:
    # Calibrated values, Table 1 of the paper
    s0: float = 100.0          # coins outstanding at date 0, USD bn
    mu: float = 7.67e-4        # weekly bond return (7.67 bps)
    gamma: float = 0.361       # weekly AR(1) persistence of flows
    sigma: float = 0.063       # standard deviation of flow shocks
    alpha: float = 0.037       # curvature of the price impact function
    m: float = 41e-4           # maximum price impact (41 bps)
    # Date-0 balance sheet set to the calibrated moments (liquidity ratio 11.7%,
    # capital ratio 0.108%), rather than re-solving the date-0 problem.
    liquidity_ratio: float = 0.117
    capital_ratio: float = 0.00108
    # Closed-form model only: constant per-unit liquidation cost. The paper leaves
    # it free (kappa > mu); we set it to the calibrated maximum price impact m.
    kappa: float = 41e-4

    @property
    def c0(self):
        return self.liquidity_ratio * self.s0

    @property
    def k0(self):
        return self.capital_ratio * self.s0

    @property
    def b0(self):
        return self.s0 + self.k0 - self.c0


def z_star(p: Params) -> float:
    """Target distance-to-shortfall: mu = kappa * (1 - Phi(z*)), eq. (8)."""
    return norm.ppf(1.0 - p.mu / p.kappa)


def interior_cash(r1, p: Params):
    """Interior cash target c1*(r1) = s0 (1 + r1)(sigma z* - gamma r1), eq. (9)."""
    return p.s0 * (1.0 + r1) * (p.sigma * z_star(p) - p.gamma * r1)


def cash_cap(r1, p: Params):
    """Cash available without selling bonds, eq. (10)."""
    return p.s0 * (1.0 + r1) + p.k0 - (1.0 - p.mu) * p.b0


def forced_sale_threshold(p: Params) -> float:
    """Flow below which bonds must be sold, eq. (11)."""
    return ((1.0 - p.mu) * p.b0 - p.k0) / p.s0 - 1.0


def phase_boundaries(p: Params) -> dict:
    """Flow levels separating the four phases of the shark-fin policy, eq. (13)."""
    r = np.linspace(-0.6, 0.6, 240_001)
    above_cap = interior_cash(r, p) > cash_cap(r, p)
    r_fs = forced_sale_threshold(p)
    # Phase III is the part of (r_cap-, r_cap+) above the forced-selling threshold
    in_cap = r[above_cap & (r >= r_fs)]
    return {
        "forced_selling": r_fs,                       # IV | III
        "cap_binds_upper": in_cap.max() if in_cap.size else np.nan,  # III | II
        "cash_zero": p.sigma * z_star(p) / p.gamma,   # II | I
    }


def closed_form_policy(r1, p: Params) -> dict:
    """Date-1 cash, bonds and capital in the closed-form model (constant kappa)."""
    r1 = np.asarray(r1, dtype=float)
    s1 = p.s0 * (1.0 + r1)
    k_hold = p.k0 + p.mu * p.b0                        # capital if no bonds are sold

    c = np.clip(interior_cash(r1, p), 0.0, None)       # Phase I truncation at zero
    c = np.minimum(c, cash_cap(r1, p))                 # Phase III: no discretionary sales
    forced = r1 < forced_sale_threshold(p)             # Phase IV: forced sales
    c = np.where(forced, 0.0, c)

    # Phase IV: c1 = 0 and k1 = k_hold - kappa (b0 - b1)  =>  solve for b1
    b_forced = (s1 + p.k0 + (p.mu - p.kappa) * p.b0) / (1.0 - p.kappa)
    b = np.where(forced, b_forced, s1 + k_hold - c)
    k = np.where(forced, k_hold - p.kappa * (p.b0 - b_forced), k_hold)
    return {"r1": r1, "cash": c, "bonds": b, "capital": k}


def price_impact(x, p: Params):
    """Concave price impact of selling x (USD bn) of bonds, eq. (16): m (1 - e^{-alpha x})."""
    return p.m * (1.0 - np.exp(-p.alpha * np.asarray(x, dtype=float)))


def forced_sale_capital(r1, p: Params) -> dict:
    """
    Capital after forced sales under the paper's workhorse loss function, where a
    sale of x marks down the whole bond book: k1 = k0 + mu b0 - b0 g(x).
    Used only beyond the forced-selling threshold, where cash is exhausted (c1 = 0).
    """
    r1 = np.atleast_1d(np.asarray(r1, dtype=float))
    k_out, x_out = np.empty_like(r1), np.empty_like(r1)
    for i, r in enumerate(r1):
        s1 = p.s0 * (1.0 + r)

        # c1 = s1 + k1 - b1 = 0 with b1 = b0 - x
        def f(x):
            k1 = p.k0 + p.mu * p.b0 - p.b0 * price_impact(x, p)
            return s1 + k1 - (p.b0 - x)

        if f(0.0) >= 0:                 # no forced sale needed
            x = 0.0
        else:
            x = brentq(f, 0.0, p.b0)
        k_out[i] = p.k0 + p.mu * p.b0 - p.b0 * price_impact(x, p)
        x_out[i] = x
    return {"r1": r1, "capital": k_out, "bonds_sold": x_out}


def default_flow(p: Params) -> float:
    """Redemption size at which forced-sale losses exhaust capital."""
    g = lambda r: forced_sale_capital(r, p)["capital"][0]
    lo, hi = -0.99, forced_sale_threshold(p)
    if g(lo) > 0:
        return np.nan
    return brentq(g, lo, hi)
