"""Figures 4 and 5: the shark-fin cash policy and capital under forced sales."""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import style
from model import (Params, closed_form_policy, default_flow, forced_sale_capital,
                   forced_sale_threshold, phase_boundaries)

OUT = Path(__file__).resolve().parents[1] / "figures"
OUT.mkdir(exist_ok=True)
style.apply()
p = Params()
r = np.linspace(-0.25, 0.25, 2001)
pol = closed_form_policy(r, p)
pb = phase_boundaries(p)

# ---------------------------------------------------------------- Figure 3
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))
edges = [r.min(), pb["forced_selling"], pb["cap_binds_upper"], pb["cash_zero"], r.max()]
labels = ["IV\nforced\nbond sales", "III\nspend\ncash first", "II\nprecautionary\nbuffer",
          "I\nall in\nbonds"]

for ax in (ax1, ax2):
    for i, (a, b) in enumerate(zip(edges[:-1], edges[1:])):
        if i % 2 == 0:
            ax.axvspan(a, b, color=style.SHADE, lw=0, zorder=0)
    ax.axvline(0, color=style.INK_2, lw=0.8, ls=":")
    ax.set_xlabel("Weekly stablecoin flow at date 1 (share of coins outstanding)")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:+.0%}"))

ax1.plot(r, pol["cash"], color=style.BLUE)
ax1.set_title("Cash: the shark fin")
ax1.set_ylabel("USD bn")
ytop = pol["cash"].max() * 1.45
ax1.set_ylim(0, ytop)
for (a, b), lab in zip(zip(edges[:-1], edges[1:]), labels):
    ax1.text((a + b) / 2, ytop * 0.97, lab, ha="center", va="top", fontsize=8,
             color=style.INK_2)

ax2.plot(r, pol["bonds"], color=style.ORANGE)
ax2.axhline(p.b0, color=style.INK_2, lw=1, ls="--")
ax2.text(r.max(), p.b0, " date-0\n bonds", va="center", fontsize=8, color=style.INK_2)
ax2.set_title("Bonds: held until cash runs out")
ax2.set_ylabel("USD bn")

fig.suptitle("A stablecoin issuer spends cash before it sells bonds", x=0.01, ha="left",
             fontsize=14, fontweight="bold", color=style.INK, y=1.04)
style.source_note(fig, "Closed-form model of Section 2.1 with the calibration of Table 1; constant liquidation cost "
                  "set to the calibrated maximum price impact (41 bps).\nSources: Goel, Lewrick and Agarwal "
                  "(2026); author's calculations.")
style.save(fig, OUT / "fig04_shark_fin.png")
plt.close(fig)

# ---------------------------------------------------------------- Figure 4
r2 = np.linspace(-0.40, 0.0, 801)
cap = forced_sale_capital(r2, p)
r_def = default_flow(p)

fig, ax = plt.subplots(figsize=(7.5, 4.2))
ax.axvspan(r2.min(), r_def, color=style.SHADE, lw=0, zorder=0)
ax.plot(r2, np.maximum(cap["capital"], 0) * 1000, color=style.AQUA)
ax.axvline(forced_sale_threshold(p), color=style.INK_2, lw=0.8, ls=":")
ax.text(forced_sale_threshold(p), 160, " cash exhausted,\n bond sales begin",
        fontsize=8, color=style.INK_2, va="top")
ax.text((r2.min() + r_def) / 2, 100, f"default beyond a\n{abs(r_def):.1%} weekly\nredemption", ha="center", fontsize=9,
        color=style.INK_2)
ax.axvline(r_def, color=style.INK_2, lw=0.8, ls=":")
ax.set_ylim(0, 200)
ax.set_title("Capital absorbs forced-sale losses up to about a 30% weekly run")
ax.set_ylabel("Capital, USD mn")
ax.set_xlabel("Weekly stablecoin flow at date 1 (share of coins outstanding)")
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:+.0%}"))
style.source_note(fig, "Capital after forced sales with the concave price impact m(1 - exp(-alpha x)), marking down "
                  "the whole bond book;\ncash 11.7% and capital 0.108% of coins at the start. Sources: Goel, "
                  "Lewrick and Agarwal (2026); author's calculations.")
style.save(fig, OUT / "fig05_forced_sales.png")
plt.close(fig)
print("saved figures 4 and 5; default flow", round(r_def, 4))
