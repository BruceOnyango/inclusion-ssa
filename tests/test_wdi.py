"""Tests for the WDI client. We test the PURE parsers — that's where the API's
quirks live and where silent data corruption would hide. No network is touched.
"""

from inclusion import wdi


def test_parse_records_drops_null_values():
    raw = [
        {
            "countryiso3code": "KEN",
            "country": {"value": "Kenya"},
            "date": "2020",
            "value": 12.5,
        },
        {
            "countryiso3code": "KEN",
            "country": {"value": "Kenya"},
            "date": "2021",
            "value": None,
        },
        {
            "countryiso3code": "RWA",
            "country": {"value": "Rwanda"},
            "date": "2020",
            "value": 8.1,
        },
    ]
    rows = wdi.parse_records(raw)
    assert len(rows) == 2  # the null-value row is gone
    assert {r["iso3"] for r in rows} == {"KEN", "RWA"}
    assert rows[0]["year"] == 2020 and isinstance(rows[0]["year"], int)


def test_parse_records_handles_empty():
    assert wdi.parse_records([]) == []
    assert wdi.parse_records(None) == []


def test_parse_countries_drops_aggregates():
    raw = [
        {
            "id": "KEN",
            "name": "Kenya",
            "region": {"id": "SSF", "value": "Sub-Saharan Africa"},
        },
        {
            "id": "ZG",
            "name": "Sub-Saharan Africa",
            "region": {"id": "NA", "value": "Aggregates"},
        },
    ]
    countries = wdi.parse_countries(raw)
    assert len(countries) == 1  # the aggregate row is gone
    assert countries[0]["iso3"] == "KEN"
