"""Paths for the LSMS smallholder social-needs analysis.

Raw survey files stay in 05_data and are never modified.
Derived tables and the household analysis frame are written under this
package's out/ directory (gitignored). Report tables and figures that
belong in the paper note are copied to 01_paper.
"""

from pathlib import Path

ROOT = Path("/mnt/e/patent-tod")
DATA_DIR = ROOT / "05_data" / "agri" / "lsms-worldbank"
HH_PATH = DATA_DIR / "Household_dataset.dta"
PLOT_PATH = DATA_DIR / "Plot_dataset.dta"
PLOTCROP_PATH = DATA_DIR / "Plotcrop_dataset.dta"
INDIV_PATH = DATA_DIR / "Individual_dataset.dta"

SRC_DIR = ROOT / "04_src" / "social_needs"
OUT_DIR = SRC_DIR / "out"
FRAME_PATH = OUT_DIR / "hh_season.pkl"

REPORT_DIR = ROOT / "01_paper" / "2026-winter" / "social-needs"
TABLE_DIR = REPORT_DIR / "results" / "tables"
FIG_DIR = REPORT_DIR / "results" / "figures"

# Plot area and labor screens used to build household labor intensity.
# 0.05 ha drops GPS slivers that inflate days/ha; 10 ha drops the long
# right tail of area when summing the intensity denominator.
AREA_MIN_HA = 0.05
AREA_MAX_HA = 10.0
# Per-plot family-labor cap. Values above this are treated as entry errors
# and the plot is left out of the intensity sum, not winsorized into it.
FAMILY_DAYS_MAX = 1500.0
# Farm-size window for a usable household land measure.
FARM_MIN_HA = 0.01
FARM_MAX_HA = 100.0

HH_KEYS = ["country", "wave", "season", "hh_id_obs"]
PLOT_KEYS = ["country", "wave", "season", "hh_id_obs", "plot_id_obs"]
