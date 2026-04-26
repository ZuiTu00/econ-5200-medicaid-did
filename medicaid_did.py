"""
medicaid_did.py

Reusable analysis module for the ECON 5200 final project:
"The Causal Effect of ACA Medicaid Expansion on County-Level Uninsured Rates."

This module exposes the core data-cleaning, estimation, and visualization
functions used in the main notebook. Importing from this module ensures
that the notebook, the Streamlit dashboard, and any future replications
share the exact same code paths.

Author: ZuiTu00
Date: April 2026
"""

from __future__ import annotations

import os
from typing import Iterable, Optional, Tuple

import numpy as np
import pandas as pd

# ============================================================================
# Constants: state expansion classification
# ============================================================================

# 26 states + DC that expanded Medicaid by January 1, 2014
EXPANSION_2014: list[str] = [
    "Arizona", "Arkansas", "California", "Colorado", "Connecticut",
    "Delaware", "District of Columbia", "Hawaii", "Illinois", "Iowa",
    "Kentucky", "Maryland", "Massachusetts", "Michigan", "Minnesota",
    "Nevada", "New Jersey", "New Mexico", "New York", "North Dakota",
    "Ohio", "Oregon", "Rhode Island", "Vermont", "Washington",
    "West Virginia",
]

# 10 states that have not expanded as of 2023
NEVER_EXPANDED: list[str] = [
    "Alabama", "Florida", "Georgia", "Kansas", "Mississippi",
    "South Carolina", "Tennessee", "Texas", "Wisconsin", "Wyoming",
]


# ============================================================================
# Data cleaning
# ============================================================================

def find_header_line(filepath: str) -> int:
    """Find the row index where SAHIE CSV column headers begin.

    SAHIE files contain a metadata preamble; the actual data starts after
    a row beginning with 'year,'.
    """
    with open(filepath, "r") as f:
        for i, line in enumerate(f):
            if line.strip().startswith("year,"):
                return i
    raise ValueError(f"No header row found in {filepath}")


def load_sahie_year(filepath: str) -> pd.DataFrame:
    """Load a single SAHIE CSV file, skipping its metadata preamble."""
    header_line = find_header_line(filepath)
    df = pd.read_csv(filepath, skiprows=header_line, low_memory=False)
    df.columns = [c.strip() for c in df.columns]
    return df


def load_sahie_panel(
    data_dir: str,
    years: Iterable[int] = range(2009, 2024),
) -> pd.DataFrame:
    """Concatenate SAHIE files across years into a single DataFrame."""
    dfs = []
    for year in years:
        fpath = os.path.join(data_dir, f"sahie_{year}.csv")
        df = load_sahie_year(fpath)
        dfs.append(df)
    out = pd.concat(dfs, ignore_index=True)
    out = out.drop(columns=["Unnamed: 25"], errors="ignore")
    out["state_name"] = out["state_name"].str.strip()
    if out["county_name"].dtype == object:
        out["county_name"] = out["county_name"].str.strip()
    if out["version"].dtype == object:
        out["version"] = out["version"].str.strip()
    return out


def filter_to_county_panel(raw: pd.DataFrame) -> pd.DataFrame:
    """Filter raw SAHIE data to county-level under-65 all-races both-sexes
    all-income observations.
    """
    mask = (
        (raw["geocat"] == 50) &
        (raw["agecat"] == 0) &
        (raw["racecat"] == 0) &
        (raw["sexcat"] == 0) &
        (raw["iprcat"] == 0)
    )
    out = raw.loc[mask].copy()
    # 2013 has both Original and Updated; keep Updated only
    drop_2013_orig = (out["year"] == 2013) & (out["version"] == "Original")
    out = out.loc[~drop_2013_orig].copy()
    return out


def add_treatment_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add treatment, post, and treat_post indicators to a county-level frame.

    Excludes late-adopting states (those that expanded after 2014).
    Returns a clean 2x2 panel of 2014-expansion versus never-expansion counties.
    """
    df = df.copy()
    df["group"] = np.where(
        df["state_name"].isin(EXPANSION_2014), "expansion",
        np.where(df["state_name"].isin(NEVER_EXPANDED), "control", "late_expander")
    )
    out = df[df["group"].isin(["expansion", "control"])].copy()
    out["treated"] = out["state_name"].isin(EXPANSION_2014).astype(int)
    out["post"] = (out["year"] >= 2014).astype(int)
    out["treat_post"] = out["treated"] * out["post"]

    # Construct globally-unique county identifier
    out["county_id"] = (
        out["statefips"].astype(int) * 1000 + out["countyfips"].astype(int)
    )

    # Numeric type coercion
    for col in ["PCTUI", "pctui_moe", "NIPR", "NUI", "NIC"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")

    return out


def balance_panel(df: pd.DataFrame, expected_years: int = 15) -> pd.DataFrame:
    """Drop counties without complete year coverage. Drop missing PCTUI."""
    df = df.dropna(subset=["PCTUI"]).copy()
    n_years = df.groupby("county_id")["year"].count()
    full_panel = n_years[n_years == expected_years].index
    return df[df["county_id"].isin(full_panel)].copy()


def build_clean_panel(data_dir: str) -> pd.DataFrame:
    """Full pipeline: raw SAHIE files -> cleaned balanced panel.

    Convenience wrapper around the four functions above.
    """
    raw = load_sahie_panel(data_dir)
    counties = filter_to_county_panel(raw)
    with_treat = add_treatment_indicators(counties)
    return balance_panel(with_treat)


# ============================================================================
# Estimation: TWFE DiD via within transformation + state-clustered SEs
# ============================================================================

def two_way_within_transform(
    df: pd.DataFrame, y_col: str, x_col: str,
    entity_col: str = "county_id", time_col: str = "year",
) -> Tuple[pd.Series, pd.Series]:
    """Two-way within (demean by entity and time, add grand mean)."""
    y = df[y_col]
    x = df[x_col]
    y_dm = (y
            - df.groupby(entity_col)[y_col].transform("mean")
            - df.groupby(time_col)[y_col].transform("mean")
            + y.mean())
    x_dm = (x
            - df.groupby(entity_col)[x_col].transform("mean")
            - df.groupby(time_col)[x_col].transform("mean")
            + x.mean())
    return y_dm, x_dm


def twfe_did(
    df: pd.DataFrame, y_col: str = "PCTUI", x_col: str = "treat_post",
    cluster_col: str = "statefips",
    entity_col: str = "county_id", time_col: str = "year",
) -> dict:
    """TWFE DiD with cluster-robust standard errors.

    Returns dict with point estimate, SE, 95% CI, and number of clusters.
    """
    y_dm, x_dm = two_way_within_transform(df, y_col, x_col, entity_col, time_col)

    # Coefficient
    beta = (x_dm * y_dm).sum() / (x_dm * x_dm).sum()

    # Residuals
    u = y_dm - beta * x_dm

    # Cluster-robust variance (CR1S, matches linearmodels default)
    G = df[cluster_col].nunique()
    N = len(df)
    K = 1 + df[entity_col].nunique() + df[time_col].nunique() - 1

    XX_inv = 1.0 / (x_dm * x_dm).sum()
    meat = 0.0
    for cluster_value in df[cluster_col].unique():
        mask = df[cluster_col] == cluster_value
        score = (x_dm[mask] * u[mask]).sum()
        meat += score ** 2

    dof_adj = (G / (G - 1)) * ((N - 1) / (N - K))
    var = XX_inv * meat * XX_inv * dof_adj
    se = np.sqrt(var)

    return {
        "beta": beta,
        "se": se,
        "ci_lower": beta - 1.96 * se,
        "ci_upper": beta + 1.96 * se,
        "n_clusters": G,
        "n_obs": N,
    }


def naive_ols(df: pd.DataFrame, y_col: str = "PCTUI",
              x_col: str = "treated") -> dict:
    """Simple OLS of y on x with intercept; iid SEs."""
    X = np.column_stack([np.ones(len(df)), df[x_col].values])
    y = df[y_col].values
    beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    n, k = X.shape
    sigma2 = (resid ** 2).sum() / (n - k)
    var = sigma2 * np.linalg.inv(X.T @ X)
    se = np.sqrt(np.diag(var))
    return {
        "beta": beta[1], "se": se[1],
        "ci_lower": beta[1] - 1.96 * se[1],
        "ci_upper": beta[1] + 1.96 * se[1],
    }


# ============================================================================
# Helpers
# ============================================================================

def weighted_mean(x: pd.Series, w: pd.Series) -> float:
    return (x * w).sum() / w.sum()


def parallel_trends_table(df: pd.DataFrame) -> pd.DataFrame:
    """Annual weighted means by group for parallel-trends visualization."""
    rows = []
    for yr in sorted(df["year"].unique()):
        for grp in [0, 1]:
            d = df[(df["year"] == yr) & (df["treated"] == grp)]
            rows.append({
                "year": yr,
                "treated": grp,
                "weighted_mean": weighted_mean(d["PCTUI"], d["NIPR"]),
                "unweighted_mean": d["PCTUI"].mean(),
            })
    return pd.DataFrame(rows)
