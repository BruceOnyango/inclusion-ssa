"""One-shot diagnostic: does any driver have outlier-scale year-to-year jumps
within a country? If drivers are smooth stock variables, plain mean is safe.
If something jumps wildly, that's usually a data revision/definition change
worth catching — and a signal to use median or a trend for that variable.
"""

import pandas as pd
from inclusion import load_panel, config

df = load_panel().sort_values(["country", "year"])

# The near-complete drivers we intend to average with a plain mean.
drivers = [
    "electricity_access",
    "internet_users",
    "basic_water_access",
    "labor_force_part",
    "labor_part_ratio_fm",
    "lower_sec_completion",
]

print("=== Year-to-year jump per driver (within country) ===")
print("If max |jump| is modest, these are smooth -> mean is fine.\n")

rows = []
for col in drivers:
    # absolute change from one year to the next, within each country
    diffs = df.groupby("country")[col].diff().abs()
    rows.append(
        {
            "driver": col,
            "median_jump": round(diffs.median(), 2),
            "p95_jump": round(diffs.quantile(0.95), 2),
            "max_jump": round(diffs.max(), 2),
        }
    )
summary = pd.DataFrame(rows).sort_values("max_jump", ascending=False)
print(summary.to_string(index=False))

# Show the actual worst offenders so we can eyeball whether they're real.
print("\n=== 8 largest single jumps (country, driver, from->to) ===")
records = []
for col in drivers:
    d = df.copy()
    d["jump"] = d.groupby("country")[col].diff().abs()
    d["prev"] = d.groupby("country")[col].shift(1)
    top = d.dropna(subset=["jump"]).nlargest(3, "jump")[
        ["country", "year", "prev", col, "jump"]
    ]
    for _, r in top.iterrows():
        records.append(
            {
                "country": r["country"],
                "driver": col,
                "year": int(r["year"]),
                "from": round(r["prev"], 1),
                "to": round(r[col], 1),
                "jump": round(r["jump"], 1),
            }
        )
worst = pd.DataFrame(records).sort_values("jump", ascending=False).head(8)
print(worst.to_string(index=False))
