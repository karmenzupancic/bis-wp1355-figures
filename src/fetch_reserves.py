"""
Download the monthly portfolio holdings of the Circle Reserve Fund (USDXX), the money market fund
that holds most of USDC's reserves, from its N-MFP filings with the SEC, and save the totals by
investment category to data/circle_reserve_fund.csv.

N-MFP2 (to May 2024) and N-MFP3 (from June 2024) filings share the fields used here. Where a month
was refiled, the amendment replaces the original.
"""
import re
import time
from pathlib import Path

import pandas as pd
import requests

SERIES = "S000077205"            # Circle Reserve Fund
CIK = "0000844779"               # BlackRock Funds, the registrant
HEADERS = {"User-Agent": "bis-wp1355-figures research (github.com/karmenzupancic/bis-wp1355-figures)"}
OUT = Path(__file__).resolve().parents[1] / "data" / "circle_reserve_fund.csv"


def accessions():
    accs = []
    for form in ["N-MFP3", "N-MFP2"]:
        for start in (0, 100):
            html = requests.get("https://www.sec.gov/cgi-bin/browse-edgar",
                                params={"action": "getcompany", "CIK": SERIES, "type": form,
                                        "count": 100, "start": start}, headers=HEADERS, timeout=60).text
            accs += re.findall(r"Acc-no: (\d{10}-\d{2}-\d{6})", html)
            time.sleep(0.2)
    return list(dict.fromkeys(accs))


def holdings(acc):
    url = f"https://www.sec.gov/Archives/edgar/data/{int(CIK)}/{acc.replace('-', '')}/primary_doc.xml"
    x = requests.get(url, headers=HEADERS, timeout=60).text
    if f"<seriesId>{SERIES}</seriesId>" not in x:
        return None
    get = lambda tag: (re.search(f"<{tag}>([^<]+)</{tag}>", x) or [None, None])[1]
    totals = {"treasury_bills": 0.0, "treasury_repo": 0.0, "other": 0.0}
    for block in re.findall(r"<scheduleOfPortfolioSecuritiesInfo>(.*?)</scheduleOfPortfolioSecuritiesInfo>", x, re.S):
        cat = (re.search(r"<investmentCategory>([^<]+)<", block) or [None, ""])[1]
        val = float((re.search(r"<includingValueOfAnySponsorSupport>([^<]+)<", block) or [None, 0])[1])
        key = ("treasury_bills" if cat.startswith("U.S. Treasury Debt")
               else "treasury_repo" if "Repurchase" in cat else "other")
        totals[key] += val
    return {"report_date": get("reportDate"), "net_assets": float(get("netAssetOfSeries")),
            **totals, "accession": acc, "amendment": "/A" in (get("submissionType") or "")}


def main():
    rows = []
    for acc in accessions():
        r = holdings(acc)
        if r:
            rows.append(r)
        time.sleep(0.2)
    df = (pd.DataFrame(rows).sort_values(["report_date", "amendment"])
          .drop_duplicates("report_date", keep="last").drop(columns="amendment"))
    df.to_csv(OUT, index=False, float_format="%.2f")
    print(f"saved {len(df)} months to {OUT}")


if __name__ == "__main__":
    main()
