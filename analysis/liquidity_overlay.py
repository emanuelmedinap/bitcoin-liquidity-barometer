#!/usr/bin/env python3
"""
Liquidity overlay — two-panel figure (see DECISIONS.md §5.2).

Panel A: system NII (sum of NII across all banks per quarter), M2, and bitcoin,
         each INDEXED TO 100 at the first common quarter (log y-axis, because the
         three series span >2 orders of magnitude; log makes shared shape visible
         without implying the units are comparable).
Panel B: YEAR-OVER-YEAR % change of the same three series (unit-free; this is the
         panel we draw inference from — see DECISIONS.md §7).

FY2025 quarters (any bank-row with fiscal_year = 2025) are shaded and labeled
UNVERIFIED, per DECISIONS.md §6.

Data: sql/liquidity_overlay.sql, run through the `bq` CLI under the 200 GB
maximum_bytes_billed cap (~/.bigqueryrc; also passed explicitly here). A CSV
snapshot is committed alongside so the figure regenerates without BigQuery access.

Usage:
    python analysis/liquidity_overlay.py                 # run BigQuery, write CSV + PNG
    python analysis/liquidity_overlay.py --csv PATH      # plot from a saved CSV (offline)
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from io import StringIO
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
SQL_PATH = REPO / "sql" / "liquidity_overlay.sql"
CSV_PATH = REPO / "analysis" / "liquidity_overlay_data.csv"
PNG_PATH = REPO / "analysis" / "liquidity_overlay.png"
MAX_BYTES = 214_748_364_800  # 200 GB hard cap (CLAUDE.md, non-negotiable)
# System NII is a SUM across banks, so its early history is distorted by rising
# panel coverage (n_banks ramps 17 -> ~167). Quarters with materially fewer than
# the ~167 stable count are flagged as a composition artifact on the NII/M2 panel.
STABLE_N_BANKS = 167
THIN_COVERAGE_MAX = 160  # n_banks below this = thin coverage (holds through 2017-Q4)

SERIES = {
    "system_nii": ("System NII (Σ banks)", "#1f77b4"),
    "m2": ("M2 money stock", "#2ca02c"),
    "bitcoin": ("Bitcoin (CBBTCUSD)", "#ff7f0e"),
}


def load_from_bq() -> pd.DataFrame:
    """Run the committed SQL via bq CLI (inherits + re-asserts the 200 GB cap)."""
    sql = SQL_PATH.read_text()
    out = subprocess.run(
        ["bq", "query", "--use_legacy_sql=false",
         f"--maximum_bytes_billed={MAX_BYTES}", "--format=csv", "--max_rows=100000"],
        input=sql, capture_output=True, text=True,
    )
    if out.returncode != 0:
        sys.exit(f"bq query failed:\n{out.stderr}")
    df = pd.read_csv(StringIO(out.stdout))
    df.to_csv(CSV_PATH, index=False)
    print(f"wrote data snapshot -> {CSV_PATH}")
    return df


def load_from_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["cal_quarter"] = pd.to_datetime(df["cal_quarter"])
    df = df.sort_values("cal_quarter").reset_index(drop=True)
    df["has_fy2025"] = df["has_fy2025"].astype(str).str.lower().isin(["true", "1"])
    return df


def first_common_quarter(df: pd.DataFrame) -> int:
    """Row index of the first quarter where all three series are present."""
    mask = df[["system_nii", "m2", "bitcoin"]].notna().all(axis=1)
    if not mask.any():
        sys.exit("no quarter has all three series present")
    return int(mask.idxmax())


def shade_fy2025(ax, df: pd.DataFrame) -> None:
    """Shade contiguous runs of FY2025 quarters as UNVERIFIED."""
    q = pd.Timedelta(days=92)  # ~one quarter, to cover the bar width
    for _, row in df[df["has_fy2025"]].iterrows():
        ax.axvspan(row["cal_quarter"], row["cal_quarter"] + q,
                   color="#d62728", alpha=0.10, zorder=0)


def shade_thin_coverage(ax, df: pd.DataFrame) -> None:
    """Shade quarters whose bank count is well below the ~167 stable panel."""
    q = pd.Timedelta(days=92)
    for _, row in df[df["n_banks"] < THIN_COVERAGE_MAX].iterrows():
        ax.axvspan(row["cal_quarter"], row["cal_quarter"] + q,
                   color="#7f7f7f", alpha=0.13, zorder=0)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, help="plot from a saved CSV instead of BigQuery")
    args = ap.parse_args()

    df = load_from_csv(args.csv) if args.csv else load_from_bq()
    df = prepare(df)

    base = first_common_quarter(df)
    base_q = df.loc[base, "cal_quarter"]
    idx = df.iloc[base:].copy()  # indexed panel starts at the first common quarter

    fig, (axA, axBtc, axNiiM2) = plt.subplots(
        3, 1, figsize=(12, 11), sharex=True,
        gridspec_kw={"height_ratios": [3.0, 1.4, 1.4]})

    # --- Panel A: indexed levels (base = 100), log y ---
    for col, (label, color) in SERIES.items():
        base_val = df.loc[base, col]
        axA.plot(idx["cal_quarter"], idx[col] / base_val * 100.0,
                 label=label, color=color, lw=1.8)
    axA.set_yscale("log")
    axA.axhline(100, color="grey", lw=0.8, ls=":")
    axA.set_ylabel("Indexed to 100 at base\n(log scale)")
    axA.set_title(
        f"Panel A — Indexed levels (base = {base_q:%Y-Q}{(base_q.month-1)//3+1}, =100). "
        "Descriptive context only — after 2020 all three trend up and LOOK linked.",
        fontsize=10, loc="left")
    axA.grid(True, which="both", axis="y", alpha=0.25)
    shade_fy2025(axA, df)

    # --- Panel B (inference): YoY % change, split so each scale is legible ---
    # B-top: bitcoin alone (its swings are an order of magnitude larger).
    bl, bc = SERIES["bitcoin"]
    axBtc.plot(df["cal_quarter"], df["bitcoin"].pct_change(4) * 100.0,
               label=bl, color=bc, lw=1.8)
    axBtc.axhline(0, color="grey", lw=0.8, ls=":")
    axBtc.set_ylabel("Bitcoin\nYoY % change")
    axBtc.set_title(
        "Panel B — YoY % change (de-trended). The inference panel: strips the common "
        "trend so real co-movement (or its absence) shows.",
        fontsize=10, loc="left")
    axBtc.grid(True, axis="y", alpha=0.25)
    shade_fy2025(axBtc, df)

    # B-bottom: NII and M2 together on their own (much smaller) scale.
    for col in ("system_nii", "m2"):
        label, color = SERIES[col]
        axNiiM2.plot(df["cal_quarter"], df[col].pct_change(4) * 100.0,
                     label=label, color=color, lw=1.8)
    axNiiM2.axhline(0, color="grey", lw=0.8, ls=":")
    axNiiM2.set_ylabel("NII & M2\nYoY % change")
    axNiiM2.grid(True, axis="y", alpha=0.25)
    shade_fy2025(axNiiM2, df)
    shade_thin_coverage(axNiiM2, df)  # only here: system-NII sum is coverage-sensitive
    axNiiM2.legend(
        handles=[mpatches.Patch(color="#7f7f7f", alpha=0.13,
                                label="thin bank coverage — composition artifact, read with caution")],
        loc="upper right", fontsize=8, frameon=True, framealpha=0.9)

    axNiiM2.xaxis.set_major_locator(mdates.YearLocator(2))
    axNiiM2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    axNiiM2.set_xlabel("Calendar quarter")

    # shared legend incl. the UNVERIFIED shading
    handles, labels = axA.get_legend_handles_labels()
    handles.append(mpatches.Patch(color="#d62728", alpha=0.10,
                                  label="FY2025 quarters — UNVERIFIED (DECISIONS.md §6)"))
    fig.legend(handles=handles, loc="upper center", ncol=4,
               bbox_to_anchor=(0.5, 0.995), fontsize=9, frameon=False)

    fig.suptitle("System liquidity vs. bank Net Interest Income — barometer, not driver",
                 y=1.03, fontsize=13, fontweight="bold")
    fig.text(0.01, -0.01,
             "Source: SEC EDGAR XBRL via banks_marts.analysis_panel (system NII) + "
             "FRED M2SL & CBBTCUSD via banks_raw.fred_series, quarter-aligned. "
             "Bitcoin data begins 2015. Panel A log-scaled; inference drawn only from Panel B.",
             fontsize=7.5, color="#444")

    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(PNG_PATH, dpi=150, bbox_inches="tight")
    print(f"wrote figure -> {PNG_PATH}")
    print(f"base quarter (index=100): {base_q.date()}  |  quarters: {len(df)}  "
          f"|  FY2025 UNVERIFIED quarters: {int(df['has_fy2025'].sum())}")


if __name__ == "__main__":
    main()
