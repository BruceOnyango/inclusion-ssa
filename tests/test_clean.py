"""Tests for the country-level collapse. Pure transform, no network/files.
We feed a tiny mock panel that deliberately includes:
  * a country with an impossible >100 value (must be clipped),
  * a country with zero target observations (must be dropped),
  * a country whose target has a known number of observations (n_obs check).
"""

import pandas as pd
from inclusion import clean


def _mock_panel():
    return pd.DataFrame(
        [
            # Kenya: 2 NEET observations (one year missing), a clean driver.
            {
                "iso3": "KEN",
                "country": "Kenya",
                "year": 2015,
                "neet_total": 20.0,
                "electricity_access": 40.0,
            },
            {
                "iso3": "KEN",
                "country": "Kenya",
                "year": 2016,
                "neet_total": 30.0,
                "electricity_access": 50.0,
            },
            {
                "iso3": "KEN",
                "country": "Kenya",
                "year": 2017,
                "neet_total": None,
                "electricity_access": 60.0,
            },
            # Ghana: 1 NEET obs, and an IMPOSSIBLE 120% that must be clipped to 100.
            {
                "iso3": "GHA",
                "country": "Ghana",
                "year": 2015,
                "neet_total": 10.0,
                "electricity_access": 120.0,
            },
            # Chad: NO NEET observations at all -> must be dropped entirely.
            {
                "iso3": "TCD",
                "country": "Chad",
                "year": 2015,
                "neet_total": None,
                "electricity_access": 10.0,
            },
        ]
    )


def test_zero_target_country_is_dropped():
    out = clean.build_country_table(_mock_panel(), target="neet_total")
    assert "Chad" not in set(out["country"])  # no target -> gone
    assert set(out["country"]) == {"Kenya", "Ghana"}


def test_neet_mean_and_n_obs():
    out = clean.build_country_table(_mock_panel(), target="neet_total")
    kenya = out[out.country == "Kenya"].iloc[0]
    assert kenya["neet_total"] == 25.0  # mean of 20 and 30, NaN skipped
    assert kenya[clean.N_OBS_COL] == 2  # two real observations
    ghana = out[out.country == "Ghana"].iloc[0]
    assert ghana[clean.N_OBS_COL] == 1  # single survey -> flagged as 1


def test_impossible_percentage_is_clipped():
    out = clean.build_country_table(_mock_panel(), target="neet_total")
    ghana = out[out.country == "Ghana"].iloc[0]
    assert ghana["electricity_access"] == 100.0  # 120 clipped to 100 before mean


def test_driver_mean_skips_missing_years():
    out = clean.build_country_table(_mock_panel(), target="neet_total")
    kenya = out[out.country == "Kenya"].iloc[0]
    assert kenya["electricity_access"] == 50.0  # mean of 40, 50, 60
