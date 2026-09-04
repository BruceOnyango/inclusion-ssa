"""Tests for the pure panel-building logic. No network, no files — just the
transform that can silently mangle data if it's wrong.
"""

from inclusion import acquire


def test_records_to_panel_pivots_to_wide():
    long_rows = [
        {
            "iso3": "KEN",
            "country": "Kenya",
            "year": 2020,
            "value": 12.5,
            "column": "neet_total",
        },
        {
            "iso3": "KEN",
            "country": "Kenya",
            "year": 2020,
            "value": 47.0,
            "column": "gini",
        },
        {
            "iso3": "KEN",
            "country": "Kenya",
            "year": 2021,
            "value": 13.1,
            "column": "neet_total",
        },
        {
            "iso3": "RWA",
            "country": "Rwanda",
            "year": 2020,
            "value": 8.1,
            "column": "neet_total",
        },
    ]
    panel = acquire.records_to_panel(long_rows)

    # 3 distinct country-years -> 3 rows; index cols + 2 indicators -> 5 cols
    assert panel.shape == (3, 5)
    assert {"iso3", "country", "year", "neet_total", "gini"} == set(panel.columns)

    # Values land in the right cell
    ken_2020 = panel[(panel.iso3 == "KEN") & (panel.year == 2020)].iloc[0]
    assert ken_2020["neet_total"] == 12.5
    assert ken_2020["gini"] == 47.0

    # A country-year missing an indicator is NaN, not an error
    ken_2021 = panel[(panel.iso3 == "KEN") & (panel.year == 2021)].iloc[0]
    assert pd.isna(ken_2021["gini"])


def test_records_to_panel_empty_is_safe():
    panel = acquire.records_to_panel([])
    assert list(panel.columns) == ["iso3", "country", "year"]
    assert len(panel) == 0


import pandas as pd  # imported at bottom only to keep the test body readable
