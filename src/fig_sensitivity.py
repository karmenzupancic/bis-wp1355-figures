"""
Sensitivity of the cash policy to the model parameters.

Figure 6: the shark-fin cash policy drawn as a band across parameter uncertainty.
          Persistence (gamma) and volatility (sigma) are drawn from the paper's estimates
          and standard errors (Table 2, column 3); the constant liquidation cost of the
          closed-form model, which the paper leaves free, is drawn from a plausible range.
"""
from dataclasses import replace
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import style
from model import Params, closed_form_policy

OUT = Path(__file__).resolve().parents[1] / "figures"
OUT.mkdir(exist_ok=True)
style.apply()
p0 = Params()
rng = np.random.default_rng(1355)

# Estimated parameters: point estimate and standard error from the paper
GAMMA = (0.361, 0.065)       # Table 2 (3)
SIGMA = (0.063, 0.009)       # Table 2 (3), SD of residuals
# Plausible ranges for parameters that are calibrated rather than estimated
KAPPA = (20e-4, 80e-4)       # closed-form liquidation cost, bps per unit sold

# ------------------------------------------------------------------ Figure 6
r = np.linspace(-0.25, 0.25, 801)
N = 2000
draws = np.empty((N, r.size))
for i in range(N):
    p = replace(
        p0,
        gamma=float(np.clip(rng.normal(*GAMMA), 0.05, 0.95)),
        sigma=float(np.clip(rng.normal(*SIGMA), 0.02, 0.15)),
        kappa=float(rng.uniform(*KAPPA)),
    )
    draws[i] = closed_form_policy(r, p)["cash"]

lo, mid_lo, med, mid_hi, hi = np.percentile(draws, [5, 25, 50, 75, 95], axis=0)
base = closed_form_policy(r, p0)["cash"]

fig, ax = plt.subplots(figsize=(8.5, 4.6))
ax.fill_between(r, lo, hi, color=style.BLUE, alpha=0.15, lw=0, label="90% of draws")
ax.fill_between(r, mid_lo, mid_hi, color=style.BLUE, alpha=0.30, lw=0, label="50% of draws")
ax.plot(r, base, color=style.BLUE, lw=2, label="paper's calibration")
ax.axvline(0, color=style.INK_2, lw=0.8, ls=":")
ax.set_xlabel("Weekly stablecoin flow at date 1 (share of coins outstanding)")
ax.set_ylabel("Cash held at date 1, USD bn")
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:+.0%}"))
ax.set_ylim(bottom=0)
ax.legend(loc="upper right", fontsize=8)
ax.set_title("The shape is robust, the size of the buffer is not")
style.source_note(fig, "2,000 draws: persistence and volatility from the estimates and standard errors in Table 2, "
                  "liquidation cost uniform on 20-80 bps.\nSources: Goel, Lewrick and Agarwal (2026); "
                  "author's calculations.")
style.save(fig, OUT / "fig06_sensitivity_band.png")
plt.close(fig)

print("saved figure 6")
