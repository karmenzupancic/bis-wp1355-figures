"""Figure 2: what backs USDC. Month-end holdings of the Circle Reserve Fund (USDXX) by investment
category, from its N-MFP filings with the SEC, against USDC outstanding."""
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

import style

ROOT = Path(__file__).resolve().parents[1]
FUND = ROOT / "data" / "circle_reserve_fund.csv"
COINS = ROOT / "data" / "stablecoins_weekly.csv"
OUT = ROOT / "figures"


def main():
    style.apply()
    f = pd.read_csv(FUND, parse_dates=["report_date"], index_col="report_date").drop(columns="accession") / 1e9
    usdc = pd.read_csv(COINS, parse_dates=["week"], index_col="week")["USDC"] / 1e9
    usdc_m = usdc.reindex(f.index, method="nearest")          # weekly average nearest month-end

    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.set_axisbelow(True)
    w = 20
    ax.bar(f.index, f["treasury_repo"], width=w, color=style.BLUE, label="Treasury repo")
    ax.bar(f.index, f["treasury_bills"], width=w, bottom=f["treasury_repo"], color=style.ORANGE,
           label="Treasury bills")
    ax.plot(usdc_m.index, usdc_m, color=style.INK, lw=1.6, label="USDC outstanding")
    ax.annotate("31 May 2023: no Treasury bills\nduring the US debt-ceiling standoff",
                (pd.Timestamp("2023-05-31"), f.loc[pd.Timestamp("2023-05-31"), "treasury_repo"]),
                xytext=(pd.Timestamp("2023-08-01"), 48), fontsize=8, color=style.INK_2,
                arrowprops=dict(arrowstyle="-", color=style.INK_2, lw=0.8))
    out25 = (1 - f["net_assets"] / usdc_m).loc["2025"].mean()
    ax.annotate(f"gap = reserves held outside the fund:\n{out25:.1%} of USDC on average in 2025",
                (pd.Timestamp("2025-06-30"), (usdc_m.loc["2025-06-30"] + f.loc[pd.Timestamp("2025-06-30"), "net_assets"]) / 2),
                xytext=(pd.Timestamp("2023-10-01"), 70), fontsize=8, color=style.INK_2,
                arrowprops=dict(arrowstyle="-", color=style.INK_2, lw=0.8))
    last = f.index[-1]
    ax.text(last, usdc_m.iloc[-1] + 2, f" USDC {usdc_m.iloc[-1]:.0f}", fontsize=9, color=style.INK,
            va="bottom", fontweight="bold")
    ax.text(last, f.loc[last].sum() / 2, f" fund {f.loc[last, 'net_assets']:.0f}", fontsize=9,
            color=style.INK, va="center")
    ax.set_ylabel("USD bn")
    ax.set_ylim(0, max(usdc_m.max(), f[["treasury_bills", "treasury_repo"]].sum(axis=1).max()) * 1.15)
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.legend(loc="upper left", fontsize=8)
    ax.set_title("What backs USDC: Treasury bills and repo in the Circle Reserve Fund")
    style.source_note(fig, "Month-end portfolio holdings of the Circle Reserve Fund (USDXX), November 2022 to "
                      f"{last:%B %Y}; USDC outstanding is the weekly average nearest each month-end.\n"
                      "Reserves not held in the fund are not shown. Sources: SEC, Form N-MFP; DefiLlama; "
                      "author's calculations.")
    style.save(fig, OUT / "fig02_reserves.png")
    plt.close(fig)
    print("saved figure 2")


if __name__ == "__main__":
    main()
