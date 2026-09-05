"""Single source of truth for the SSA social & economic inclusion project.

Only declared facts live here — paths, the year window, the region, and the
indicators. No logic. Every other module imports from this file so they can
never disagree about what we're pulling or where it goes.
"""

from pathlib import Path

# --- Paths (computed from THIS file's location, so it works from anywhere) ---
# config.py is at: <root>/src/inclusion/config.py  ->  parents[2] is <root>
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"  # one parquet per indicator (a cache)
PROCESSED_DIR = DATA_DIR / "processed"  # the merged panel the dashboard reads
PANEL_PATH = PROCESSED_DIR / "inclusion_panel.parquet"

# --- Date knob (Option A: one window, model AND dashboard obey it) ---
YEAR_START = 2010
YEAR_END = 2024

# --- Geography: Sub-Saharan Africa, fetched live from this region code ---
REGION_CODE = "SSF"

# --- Indicators: World Bank code -> our friendly name. TARGET is first. ---
INDICATORS = {
    # Target: youth exclusion (Not in Employment, Education or Training)
    "SL.UEM.NEET.ZS": "neet_total",
    "SL.UEM.NEET.FE.ZS": "neet_female",
    "SL.UEM.NEET.MA.ZS": "neet_male",
    # Labour market
    "SL.TLF.CACT.ZS": "labor_force_part",
    "SL.TLF.CACT.FM.ZS": "labor_part_ratio_fm",
    # Education
    "SE.ADT.LITR.ZS": "adult_literacy",
    # Access to basic services
    "EG.ELC.ACCS.ZS": "electricity_access",
    "IT.NET.USER.ZS": "internet_users",
    "SH.H2O.BASW.ZS": "basic_water_access",
    # Poverty & inequality (context, not modelled as a target)
    "SI.POV.DDAY": "poverty_headcount_215",
    "SI.POV.GINI": "gini",
}

TARGET = "neet_total"
