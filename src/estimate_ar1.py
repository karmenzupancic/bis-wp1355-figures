"""
Figure 3 and the flow estimate behind the calibration.

Table:    re-estimation of equation (14) of the paper on 2020-2025,
              r_{i,t} = gamma r_{i,t-1} + eta_i + eta_t + e_{i,t},
          with coin and week fixed effects and standard errors clustered by week, next to the
          paper's estimates (Table 2).
Figure 3: weekly flows conditional on the previous week (as in the paper's Figure 3).

Flows are weekly net changes in coins outstanding, r_t = s_t / s_{t-1} - 1, as in the paper.
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

import style

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "stablecoins_weekly.csv"
FIG = ROOT / "figures"
EST_START, EST_END = "2020-01-01", "2025-12-31"

PAPER = {"all": (0.361, 0.063), "top2": (0.462, 0.028)}   # Table 2, columns (3) and (4)


def load_flows(path=DATA) -> pd.DataFrame:
    w = pd.read_csv(path, parse_dates=["week"], index_col="week")
    flows = w / w.shift(1) - 1.0
    long = flows.stack().rename("r").reset_index()
    long.columns = ["week", "coin", "r"]
    long = long.replace([np.inf, -np.inf], np.nan).dropna().sort_values(["coin", "week"])
    long["r_lag"] = long.groupby("coin")["r"].shift(1)
    return long.dropna()


def fit(df, fe="coin + week"):
    rhs = "r_lag" + "".join(f" + C({x.strip()})" for x in fe.split("+") if x.strip())
    res = smf.ols(f"r ~ {rhs}", data=df).fit(
        cov_type="cluster", cov_kwds={"groups": pd.factorize(df["week"])[0]})
    return res


def summary(res):
    return {"gamma": res.params["r_lag"], "se": res.bse["r_lag"],
            "sigma": np.sqrt(res.mse_resid), "n": int(res.nobs), "adj_r2": res.rsquared_adj}


def table(est) -> pd.DataFrame:
    rows = {
        "(1) pooled": summary(fit(est, fe="")),
        "(2) coin FE": summary(fit(est, fe="coin")),
        "(3) coin + week FE": summary(fit(est, fe="coin + week")),
        "(4) USDT and USDC only": summary(fit(est[est["coin"].isin(["USDT", "USDC"])])),
    }
    t = pd.DataFrame(rows).T
    t.loc["paper, Table 2 (3)"] = [0.361, 0.065, 0.063, 1455, 0.250]
    t.loc["paper, Table 2 (4)"] = [0.462, 0.078, 0.028, 588, 0.353]
    return t


def fig_conditional(est, out):
    d = est[est["r"].abs() <= 0.3]
    groups = [
        ("Previous week stable (|flow| ≤ 3%)", d[d["r_lag"].abs() <= 0.03], style.INK_2),
        ("Previous week: redemptions > 3%", d[d["r_lag"] < -0.03], style.ORANGE),
        ("Previous week: subscriptions > 3%", d[d["r_lag"] > 0.03], style.AQUA),
    ]
    bins = np.linspace(-0.3, 0.3, 41)
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.6), sharey=True)
    for ax, (title, g, col) in zip(axes, groups):
        ax.hist(g["r"], bins=bins, color=col, density=True, rwidth=0.85)
        ax.axvline(g["r"].mean(), color=style.INK, lw=1, ls="--")
        ax.set_title(title, fontsize=10)
        ax.text(0.97, 0.95, f"mean {g['r'].mean():+.1%}\nn = {len(g)}", transform=ax.transAxes,
                ha="right", va="top", fontsize=8, color=style.INK_2)
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:+.0%}"))
        ax.set_xlabel("Weekly net flow")
    axes[0].set_ylabel("Density")
    fig.suptitle("Last week's flows predict this week's", x=0.01, ha="left", fontsize=14,
                 fontweight="bold", color=style.INK, y=1.05)
    style.source_note(fig, "Weekly net flows of USDT, USDC, BUSD, USDP and TUSD, 2020-2025; flows beyond ±30% omitted "
                      "for display, as in the paper's Figure 3.\nSources: DefiLlama; author's calculations.")
    style.save(fig, out)
    plt.close(fig)


def main(path=DATA, figdir=FIG):
    style.apply()
    long = load_flows(path)
    est = long[(long["week"] >= EST_START) & (long["week"] <= EST_END)]
    t = table(est)
    pd.set_option("display.float_format", lambda v: f"{v:.3f}")
    print(t)
    t.to_csv(figdir / "table_ar1.csv", float_format="%.4f")
    fig_conditional(est, figdir / "fig03_flow_persistence.png")


if __name__ == "__main__":
    main(*(Path(a) for a in sys.argv[1:]))
