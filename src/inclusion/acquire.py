"""Orchestrate the pull: fetch every configured indicator once, cache each as a
parquet, then merge into the single wide panel the dashboard/model read.

The merge logic (records -> wide panel) is a PURE function, separate from the
network/IO plumbing, so it can be tested offline against mock rows.

    python -m inclusion.acquire            # uses the cache
    python -m inclusion.acquire --force    # re-pull everything
"""

from __future__ import annotations

import argparse
import requests
import pandas as pd
from tqdm import tqdm

from . import config, wdi


def _raw_path(column_name: str):
    return config.RAW_DIR / f"{column_name}.parquet"


def records_to_panel(long_rows: list[dict]) -> pd.DataFrame:
    """Pivot tidy long rows into a wide country-year panel. Pure: data in, data out.

    Each input row is expected to have: iso3, country, year, value, column.
    Output: one row per (iso3, country, year), one column per indicator name.
    """
    long = pd.DataFrame(
        long_rows, columns=["iso3", "country", "year", "value", "column"]
    )
    panel = (
        long.pivot_table(
            index=["iso3", "country", "year"],
            columns="column",
            values="value",
            aggfunc="first",
        )
        .reset_index()
        .sort_values(["country", "year"])
        .reset_index(drop=True)
    )
    panel.columns.name = None
    return panel


def acquire_indicator(
    code: str,
    name: str,
    iso3_list: list[str],
    session: requests.Session,
    force: bool = False,
) -> pd.DataFrame:
    """Fetch one indicator, or load it from the raw cache if present."""
    path = _raw_path(name)
    if path.exists() and not force:
        return pd.read_parquet(path)

    rows = wdi.fetch_indicator(
        code, iso3_list, config.YEAR_START, config.YEAR_END, session=session
    )
    df = pd.DataFrame(
        rows, columns=["iso3", "country", "year", "value", "indicator_code"]
    )
    df.to_parquet(path, index=False)
    return df


def build_panel(force: bool = False) -> pd.DataFrame:
    """Acquire all indicators (with a progress bar) and merge into the wide panel."""
    session = requests.Session()  # one shared session, reused across all pulls

    countries = wdi.get_region_countries(config.REGION_CODE, session=session)
    iso3_list = [c["iso3"] for c in countries]
    tqdm.write(f"Sub-Saharan Africa: {len(iso3_list)} countries")

    long_rows = []
    for code, name in tqdm(
        config.INDICATORS.items(), desc="Pulling indicators", unit="ind"
    ):
        df = acquire_indicator(code, name, iso3_list, session=session, force=force)
        for r in df.assign(column=name)[
            ["iso3", "country", "year", "value", "column"]
        ].to_dict("records"):
            long_rows.append(r)

    panel = records_to_panel(long_rows)  # the pure transform, now testable
    panel.to_parquet(config.PANEL_PATH, index=False)
    tqdm.write(
        f"Panel written: {config.PANEL_PATH}  ({panel.shape[0]} rows x {panel.shape[1]} cols)"
    )
    return panel


def main():
    ap = argparse.ArgumentParser(
        description="Pull SSA inclusion indicators and build the panel."
    )
    ap.add_argument(
        "--force", action="store_true", help="Ignore the raw cache and re-pull."
    )
    args = ap.parse_args()
    build_panel(force=args.force)


if __name__ == "__main__":
    main()
