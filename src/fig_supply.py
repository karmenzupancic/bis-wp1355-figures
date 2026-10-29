"""Figure 1: how large the issuers in the paper have become. Weekly average circulating supply
of USDT, USDC and the three smaller coins, from DefiLlama."""
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

import style

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "stablecoins_weekly.csv"
OUT = ROOT / "figures"
PUBLISHED = pd.Timestamp("2026-06-02")


def main():
    style.apply()
    w = pd.read_csv(DATA, parse_dates=["week"], index_col="week") / 1e9
    parts = pd.DataFrame({"USDT": w["USDT"], "USDC": w["USDC"],
                          "BUSD, USDP and TUSD": w[["BUSD", "USDP", "TUSD"]].sum(axis=1, min_count=1)}).fillna(0)
    fig, ax = plt.subplots(figsize=(9, 4.6))
    ax.set_axisbelow(True)
    ax.stackplot(parts.index, parts.T.values, labels=parts.columns,
                 colors=[style.BLUE, style.ORANGE, style.INK_2], alpha=0.9, lw=0)
    total = parts.sum(axis=1)
    last = parts.index[-1]
    ax.axvline(PUBLISHED, color=style.INK, lw=0.8, ls=":")
    ax.text(PUBLISHED - pd.Timedelta(days=20), total.max() * 1.06, "paper published\n2 June 2026", ha="right", va="bottom",
            fontsize=8, color=style.INK_2)
    for name, y in [("USDT", parts["USDT"].iloc[-1] / 2),
                    ("USDC", parts["USDT"].iloc[-1] + parts["USDC"].iloc[-1] / 2)]:
        ax.text(last, y, f" {name} {parts[name].iloc[-1]:.0f}", va="center", fontsize=9,
                color=style.INK, fontweight="bold")
    ax.text(last, total.iloc[-1] + 6, f" total {total.iloc[-1]:.0f}", va="bottom", fontsize=9,
            color=style.INK)
    ax.set_ylim(0, total.max() * 1.22)
    ax.set_xlim(parts.index[0], last)
    ax.set_ylabel("Coins outstanding, USD bn")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.legend(loc="upper left", fontsize=8)
    ax.set_title(f"The five coins in the paper: USD {total.iloc[-1]:.0f} bn outstanding")
    style.source_note(fig, f"Weekly average circulating supply, January 2020 to {last:%B %Y}.\n"
                      "Sources: DefiLlama; author's calculations.")
    style.save(fig, OUT / "fig01_supply.png")
    plt.close(fig)
    print("saved figure 1")


if __name__ == "__main__":
    main()
