"""Rebuild every figure and the validation table. Figures 1 to 3 need the data in data/, which
`python src/fetch_flows.py` and `python src/fetch_reserves.py` download; the model figures need no data."""
import runpy
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(SRC))
data = Path(__file__).resolve().parent / "data" / "stablecoins_weekly.csv"
if data.exists():
    for script in ["fig_supply.py", "fig_reserves.py", "estimate_ar1.py"]:
        runpy.run_path(str(SRC / script), run_name="__main__")
else:
    print("No data yet: run `python src/fetch_flows.py` for figures 1 to 3.")
for script in ["fig_shark_fin.py", "fig_sensitivity.py", "fig_regulation.py", "validate.py"]:
    runpy.run_path(str(SRC / script), run_name="__main__")
