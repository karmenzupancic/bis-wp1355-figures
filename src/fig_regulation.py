"""
Figure 7: what regulation can do. Contours of equal default probability (PD) and equal expected
price impact (EPI) over pairs of liquidity and capital thresholds, the chart type of the paper's
two-way mapping between regulatory thresholds and prudential targets.

Closed-form approximation, not the paper's full numerical model: the issuer enters a week with
cash and capital at the thresholds, after a week of redemptions of two standard deviations, so
that next week's flow is drawn from N(gamma * (-2 sigma), sigma^2). PD is the probability that
forced-sale losses exhaust capital; EPI is the expected price impact of the bonds sold.
"""
from dataclasses import replace
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import brentq
from scipy.stats import norm

import style
from model import Params, default_flow, forced_sale_capital, forced_sale_threshold, price_impact

OUT = Path(__file__).resolve().parents[1] / "figures"
SHOCK = -2.0                 # previous week's flow, in standard deviations
TARGET_EPI, TARGET_PD = 0.25, 0.1    # bps, illustrative prudential targets
USDC_LR, USDC_CR = 0.118, 0.00101     # USDC, 2025 averages (paper, Annex D)


def pd_epi(p: Params, shock=SHOCK):
    """Weekly default probability and expected price impact, both in bps."""
    mean = p.gamma * shock * p.sigma
    r_def, r_fs = default_flow(p), forced_sale_threshold(p)
    pd_ = 0.0 if np.isnan(r_def) else norm.cdf((r_def - mean) / p.sigma)
    r = np.linspace(max(mean - 6 * p.sigma, -0.99), r_fs, 120)
    g = price_impact(forced_sale_capital(r, p)["bonds_sold"], p)
    epi = np.trapezoid(g * norm.pdf((r - mean) / p.sigma) / p.sigma, r)
    return pd_ * 1e4, epi * 1e4


def implied_thresholds(p0, target_epi=TARGET_EPI, target_pd=TARGET_PD):
    """Read the map backwards: the liquidity threshold that meets the EPI target, then the
    capital threshold that meets the PD target at that liquidity threshold."""
    lr = brentq(lambda l: pd_epi(replace(p0, liquidity_ratio=l))[1] - target_epi, 0.02, 0.4)
    cr = brentq(lambda c: pd_epi(replace(p0, liquidity_ratio=lr, capital_ratio=c))[0] - target_pd,
                1e-5, 0.01)
    return lr, cr


def grid(p0, n=41):
    lr = np.linspace(0.02, 0.25, n)
    cr = np.linspace(0.0002, 0.0025, n)
    PD, EPI = np.empty((n, n)), np.empty((n, n))
    for i, c in enumerate(cr):
        for j, l in enumerate(lr):
            PD[i, j], EPI[i, j] = pd_epi(replace(p0, liquidity_ratio=l, capital_ratio=c))
    return lr, cr, PD, EPI


def main():
    style.apply()
    p0 = Params()
    lr, cr, PD, EPI = grid(p0)
    lr_t, cr_t = implied_thresholds(p0)
    pd_u, epi_u = pd_epi(replace(p0, liquidity_ratio=USDC_LR, capital_ratio=USDC_CR))

    fig, ax = plt.subplots(figsize=(9, 5.6), layout="constrained")
    X, Y = lr * 100, cr * 100
    logpd = np.log10(np.clip(PD, 1e-3, None))
    im = ax.contourf(X, Y, logpd, levels=np.arange(-3, 3.01, 0.25), cmap="Blues", extend="both")
    cl = ax.contour(X, Y, logpd, levels=[-1, 0, 1, 2], colors=style.INK, linewidths=0.9, linestyles="solid")
    ax.clabel(cl, fmt=lambda v: f"PD {10 ** v:g} bp", fontsize=8)
    ce = ax.contour(X, Y, EPI, levels=[0.25, 0.5, 1, 2], colors=style.ORANGE, linewidths=1.4,
                    linestyles="--")
    xs = [X[np.argmin(np.abs(EPI[0] - v))] for v in [0.25, 0.5, 1, 2]]
    ax.clabel(ce, fmt=lambda v: f"EPI {v:g} bp", fontsize=8, colors=style.ORANGE,
              manual=[(x, 0.225) for x in xs])

    ax.plot(USDC_LR * 100, USDC_CR * 100, "o", color=style.INK, ms=8, mec="white", mew=1.5, zorder=5)
    ax.annotate(f"from thresholds to risks: USDC's 2025 balance sheet\n-> PD {pd_u:.1f} bp, EPI {epi_u:.1f} bp",
                (USDC_LR * 100, USDC_CR * 100), xytext=(30, -70), textcoords="offset points",
                fontsize=8.5, color=style.INK, fontweight="bold", ha="left",
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="none", alpha=0.85),
                arrowprops=dict(arrowstyle="-", color=style.INK_2, lw=0.8, ls=":"))
    ax.plot(lr_t * 100, cr_t * 100, "o", color="#e5559b", ms=9, mec="white", mew=1.5, zorder=5)
    ax.annotate(f"from targets to thresholds: EPI {TARGET_EPI:g} bp, PD {TARGET_PD:g} bp\n-> liquidity {lr_t:.1%}, "
                f"capital {cr_t:.3%}", (lr_t * 100, cr_t * 100), xytext=(12, 8),
                textcoords="offset points", fontsize=8.5, color="#b8326f", fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="none", alpha=0.85))

    cb = fig.colorbar(im, ax=ax, ticks=[-3, -2, -1, 0, 1, 2, 3])
    cb.ax.set_yticklabels(["0.001", "0.01", "0.1", "1", "10", "100", "1,000"])
    cb.set_label("Weekly default probability (PD), bps")
    ax.set_xlabel("Liquidity threshold: cash, % of coins outstanding")
    ax.set_ylabel("Capital threshold, % of coins outstanding")
    ax.grid(False)
    ax.set_title("Reading regulation in both directions")
    style.source_note(fig, "Illustrative: computed with the closed-form model, not the paper's full numerical model.\n"
                      "Issuer entering a week with cash and capital at the thresholds, after a two-standard-deviation "
                      "week of redemptions. Orange: expected price\nimpact of forced sales (EPI). Blue: weekly default "
                      "probability (PD). Sources: Goel, Lewrick and Agarwal (2026); author's calculations.")
    style.save(fig, OUT / "fig07_regulation_map.png")
    plt.close(fig)
    print(f"saved figure 7; target-implied thresholds LR {lr_t:.4f}, CR {cr_t:.5f}; "
          f"USDC PD {pd_u:.2f} bp, EPI {epi_u:.2f} bp")


if __name__ == "__main__":
    main()
