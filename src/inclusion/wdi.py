"""Client for the World Bank Indicators (WDI) API.

One reason to change: the World Bank's HTTP contract. Knows how to ask that API
for an indicator and hand back clean rows. It does not know about parquet,
panels, which indicators matter, or how progress is shown to a human — callers
pass in what they want, including how (or whether) to report progress.
"""

from __future__ import annotations

import time
import requests
from typing import Callable

BASE = "https://api.worldbank.org/v2"
PER_PAGE = 20000
MAX_RETRIES = 4
BACKOFF_SECONDS = 2.0
TIMEOUT = 60


# --- Pure parsing, no network. This is what the tests target. ---
def parse_records(records: list | None) -> list[dict]:
    """Turn the API's row-dicts into clean rows; drop null-value observations."""
    rows = []
    for rec in records or []:
        if rec.get("value") is None:
            continue
        rows.append(
            {
                "iso3": rec.get("countryiso3code") or rec.get("country", {}).get("id"),
                "country": rec.get("country", {}).get("value"),
                "year": int(rec["date"]) if rec.get("date") else None,
                "value": rec.get("value"),
            }
        )
    return rows


def parse_countries(records: list | None) -> list[dict]:
    """Extract real countries from a /country response; drop aggregate rows (region id 'NA')."""
    rows = []
    for rec in records or []:
        if rec.get("region", {}).get("id") == "NA":
            continue
        rows.append(
            {
                "iso3": rec.get("id"),
                "country": rec.get("name"),
                "region": rec.get("region", {}).get("value"),
            }
        )
    return rows


# --- Network edge: fetch + paginate + retry. Thin, delegates parsing. ---
def _get(session: requests.Session, url: str, params: dict) -> list:
    """GET with retries and backoff; return parsed JSON (a 2-element list)."""
    params = {**params, "format": "json"}
    last_err: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = session.get(url, params=params, timeout=TIMEOUT)
            r.raise_for_status()
            return r.json()
        except (requests.RequestException, ValueError) as e:
            last_err = e
            if attempt < MAX_RETRIES:
                time.sleep(BACKOFF_SECONDS * attempt)
    raise RuntimeError(
        f"WDI request failed after {MAX_RETRIES} tries: {url}"
    ) from last_err


def get_region_countries(
    region_code: str, session: requests.Session | None = None
) -> list[dict]:
    """Return the real countries in a region (aggregates removed)."""
    session = session or requests.Session()
    payload = _get(session, f"{BASE}/country", {"region": region_code, "per_page": 500})
    records = payload[1] if len(payload) > 1 else []
    return parse_countries(records)


def fetch_indicator(
    indicator_code: str,
    iso3_list: list[str],
    year_start: int,
    year_end: int,
    session: requests.Session | None = None,
    on_page: Callable[[int, int], None] | None = None,
) -> list[dict]:
    """Fetch one indicator for a set of countries across a year range.

    Handles pagination. If ``on_page`` is given, it's called after each page as
    ``on_page(page, total_pages)`` — the module reports progress, the caller
    decides what that looks like (bar, log, nothing). Returns clean rows.
    """
    session = session or requests.Session()
    country_str = ";".join(iso3_list) if iso3_list else "all"
    url = f"{BASE}/country/{country_str}/indicator/{indicator_code}"
    base_params = {"date": f"{year_start}:{year_end}", "per_page": PER_PAGE}

    payload = _get(session, url, {**base_params, "page": 1})
    meta = payload[0] if payload else {}
    total_pages = int(meta.get("pages", 1) or 1)

    rows = parse_records(payload[1] if len(payload) > 1 else [])
    if on_page:
        on_page(1, total_pages)

    for page in range(2, total_pages + 1):
        payload = _get(session, url, {**base_params, "page": page})
        rows.extend(parse_records(payload[1] if len(payload) > 1 else []))
        if on_page:
            on_page(page, total_pages)

    for row in rows:
        row["indicator_code"] = indicator_code
    return rows
