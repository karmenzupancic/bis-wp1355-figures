"""Compare the numbers behind the figures with the paper and write figures/validation.csv."""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar

from model import Params, interior_cash

ROOT = Path(__file__).resolve().parents[1]
FIG, DATA = ROOT / "figures", ROOT / "data"
rows = []

# Flow persistence and volatility (figure 3) against the paper's Table 2
t = pd.read_csv(FIG / "table_ar1.csv", index_col=0)
for ours, paper, label in [("(3) coin + week FE", "paper, Table 2 (3)", "all five coins"),
                           ("(4) USDT and USDC only", "paper, Table 2 (4)", "USDT and USDC")]:
    g, se = t.loc[ours, "gamma"], t.loc[ours, "se"]
    rows.append([f"flow persistence, {label}", f"{g:.3f} (95% CI {g - 1.96 * se:.2f} to {g + 1.96 * se:.2f})",
                 f"{t.loc[paper, 'gamma']:.3f}", "paper, Table 2"])
    rows.append([f"flow volatility, {label}", f"{t.loc[ours, 'sigma']:.1%}", f"{t.loc[paper, 'sigma']:.1%}",
                 "paper, Table 2"])

# USDC reserves outside the Circle Reserve Fund (figure 2) against the paper's cash ratio for USDC
fund = pd.read_csv(DATA / "circle_reserve_fund.csv", parse_dates=["report_date"], index_col="report_date")
usdc = pd.read_csv(DATA / "stablecoins_weekly.csv", parse_dates=["week"], index_col="week")["USDC"]
outside = (1 - fund["net_assets"] / usdc.reindex(fund.index, method="nearest")).loc["2025"].mean()
rows.append(["USDC reserves outside the fund, 2025 average", f"{outside:.1%}", "11.8% cash ratio",
             "paper, Annex D"])

# The closed-form cash policy (figure 4) against a numerical solution of the issuer's problem
p, eps = Params(), np.random.default_rng(0).standard_normal(400_000)
gap = 0.0
for r1 in [-0.03, 0.0, 0.05, 0.10]:
    s1, r2 = p.s0 * (1 + r1), p.gamma * r1 + p.sigma * eps
    loss = lambda c: -(p.mu * (s1 - c) - p.kappa * np.mean(np.maximum(-r2 * s1 - c, 0)))
    gap = max(gap, abs(minimize_scalar(loss, bounds=(0, 40), method="bounded").x - float(interior_cash(r1, p))))
rows.append(["cash policy, formula against numerical optimum", f"largest gap USD {gap:.2f} bn", "0",
             "numerical optimisation"])

out = pd.DataFrame(rows, columns=["check", "this repository", "reference", "source"])
out.to_csv(FIG / "validation.csv", index=False)
print(out.to_string(index=False))
