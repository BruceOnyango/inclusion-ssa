"""Sub-Saharan Africa social & economic inclusion — data, modelling, delivery."""

from . import config

__all__ = ["config", "load_panel"]


def load_panel():
    """Load the processed panel the dashboard/model read. Never touches the network.

    Fails with a clear pointer to the acquisition step if the panel isn't built yet,
    rather than a cryptic file error deep inside the dashboard.
    """
    import pandas as pd

    if not config.PANEL_PATH.exists():
        raise FileNotFoundError(
            f"No panel at {config.PANEL_PATH}. Build it first:  python -m inclusion.acquire"
        )
    return pd.read_parquet(config.PANEL_PATH)
