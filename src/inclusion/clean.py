"""Collapse the sparse country-year panel into a solid country-level table.

Why this exists: NEET is measured irregularly (only ~29% of country-years), but
well across countries (43 of 48 have >=1 observation). So we summarise each
country over the 2010-2024 window rather than pretending we have annual data.

Every decision here is evidence-based, not assumed:
  * neet_total  -> mean over the window; countries with 0 observations dropped.
  * neet_n_obs  -> how many NEET observations back each country's value (a
                   reliability flag, since a value built on 1 survey is shakier
                   than one built on 4).
  * drivers     -> plain mean over the window. Justified by the jump diagnostic:
                   these are smooth stock variables with no outlier problem.
  * validation  -> structurally-impossible percentages (>100) are clipped BEFORE
                   averaging, so a future dirty indicator can't silently poison
                   the means (the 'Seychelles >100% completion' guard).

Pure: DataFrame in, DataFrame out.
"""

from __future__ import annotations

import pandas as pd

from . import config

# Indicators that are percentages of people and therefore cannot exceed 100.
# Clipped before averaging. (Ratios like labor_part_ratio_fm are NOT here — a
# female/male participation ratio can legitimately exceed 100.)
_PERCENT_CAPPED = {
    "neet_total",
    "neet_female",
    "neet_male",
    "electricity_access",
    "internet_users",
    "basic_water_access",
    "adult_literacy",
    "poverty_headcount_215",
    "labor_force_part",
}

# The reliability column name, referenced downstream so it's never hard-coded.
N_OBS_COL = "neet_n_obs"


def _clip_impossible_percentages(df: pd.DataFrame) -> pd.DataFrame:
    """Clip percentage indicators to [0, 100] before any aggregation."""
    df = df.copy()
    for col in _PERCENT_CAPPED:
        if col in df.columns:
            df[col] = df[col].clip(lower=0, upper=100)
    return df


def build_country_table(
    panel: pd.DataFrame, target: str = config.TARGET
) -> pd.DataFrame:
    """Country-year panel -> one row per country, summarised over the window.

    Drops countries with zero observations of ``target`` (no ground truth to
    train on). Adds ``neet_n_obs`` recording the target's observation count.
    """
    panel = _clip_impossible_percentages(panel)

    # Every indicator column = everything except the identifier columns.
    id_cols = {"iso3", "country", "year"}
    value_cols = [c for c in panel.columns if c not in id_cols]

    # Reliability flag: how many real target observations each country has.
    n_obs = panel.groupby("iso3")[target].count().rename(N_OBS_COL)

    # Mean over the window, skipping NaNs (so a country isn't penalised for a
    # single missing driver-year). iso3 -> country is 1:1, so we keep the name.
    agg = (
        panel.groupby(["iso3", "country"])[value_cols]
        .mean()  # pandas mean skips NaN by default
        .reset_index()
    )

    out = agg.merge(n_obs, on="iso3", how="left")

    # Drop countries with no target observations — nothing to train on.
    out = out[out[N_OBS_COL] > 0].reset_index(drop=True)
    out[N_OBS_COL] = out[N_OBS_COL].astype(int)

    return out.sort_values("country").reset_index(drop=True)
