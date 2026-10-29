"""
Download daily circulating supply for the five US dollar stablecoins used in the paper
(USDT, USDC, BUSD, USDP, TUSD) from the public DefiLlama stablecoins API and save
weekly averages of coins outstanding to data/stablecoins_weekly.csv, from 2020 to the
latest complete week (the flow estimates use 2020-2025).

The paper uses CoinGecko market capitalisation; DefiLlama circulating supply tracks the
same quantity for fiat-backed coins and needs no API key.
"""
from pathlib import Path

import pandas as pd
import requests

BASE = "https://stablecoins.llama.fi"
SYMBOLS = ["USDT", "USDC", "BUSD", "USDP", "TUSD"]
OUT = Path(__file__).resolve().parents[1] / "data" / "stablecoins_weekly.csv"


def candidates() -> dict:
    """All US dollar pegged assets on DefiLlama listed under each of the five symbols."""
    assets = requests.get(f"{BASE}/stablecoins", timeout=60).json()["peggedAssets"]
    out = {}
    for a in assets:
        sym = a["symbol"].upper()
        if sym in SYMBOLS and a.get("pegType") == "peggedUSD":
            out.setdefault(sym, []).append(a["id"])
    return out


def daily_supply(asset_id) -> pd.Series:
    rows = requests.get(f"{BASE}/stablecoincharts/all", params={"stablecoin": asset_id},
                        timeout=60).json()
    s = pd.Series(
        {pd.to_datetime(int(r["date"]), unit="s"): r["totalCirculating"]["peggedUSD"]
         for r in rows if r.get("totalCirculating", {}).get("peggedUSD")}
    )
    return s.sort_index()


def main():
    cands = candidates()
    missing = set(SYMBOLS) - set(cands)
    if missing:
        print("Not found on DefiLlama:", ", ".join(sorted(missing)))
    frames = {}
    for sym, ids in cands.items():
        # Several assets can share a symbol (BUSD in particular). Keep the one with the
        # longest history, which is the original coin, rather than the largest today.
        series = [daily_supply(i) for i in ids]
        frames[sym] = max(series, key=len)
        print(f"{sym}: {len(frames[sym])} daily observations from {frames[sym].index[0]:%Y-%m-%d}"
              f" ({len(ids)} candidate asset(s))")
    daily = pd.DataFrame(frames)
    weekly = daily.resample("W-SUN").mean().loc["2020-01-01":]
    weekly = weekly.iloc[:-1]   # drop the current, incomplete week
    OUT.parent.mkdir(exist_ok=True)
    weekly.to_csv(OUT, index_label="week")
    print("saved", OUT)


if __name__ == "__main__":
    main()
