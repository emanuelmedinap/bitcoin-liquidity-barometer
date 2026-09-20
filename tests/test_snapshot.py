"""
Tests that would be expensive to get wrong.

They run against the committed 72-quarter snapshot (analysis/liquidity_overlay_data.csv)
with no cloud, no credentials and no network. Every number is one the report states;
see DECISIONS.md section 6 for why each matters.

    pip install -r requirements.txt
    pytest
"""
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "analysis" / "liquidity_overlay_data.csv"
PNG = ROOT / "analysis" / "liquidity_overlay.png"


@pytest.fixture(scope="module")
def df() -> pd.DataFrame:
    d = pd.read_csv(CSV, parse_dates=["cal_quarter"])
    return d.sort_values("cal_quarter").reset_index(drop=True)


def test_seventy_two_quarters_2008q2_to_2026q1(df):
    assert len(df) == 72
    assert df["cal_quarter"].iloc[0].date().isoformat() == "2008-04-01"
    assert df["cal_quarter"].iloc[-1].date().isoformat() == "2026-01-01"


def test_no_gaps_in_the_quarterly_index(df):
    expected = pd.date_range("2008-04-01", "2026-01-01", freq="QS")
    assert list(df["cal_quarter"]) == list(expected)


def test_nii_and_m2_are_never_imputed(df):
    # DECISIONS.md section 7: no imputation. A filled gap would show up as a value here.
    assert df["system_nii"].notna().all()
    assert df["m2"].notna().all()


def test_bitcoin_starts_2014q4_and_is_null_before(df):
    first = df.loc[df["bitcoin"].notna(), "cal_quarter"].min()
    assert first.date().isoformat() == "2014-10-01"
    assert df.loc[df["cal_quarter"] < first, "bitcoin"].isna().all()


def test_thin_coverage_window_is_2008q2_to_2017q4(df):
    # Fewer than 160 banks reporting: the system-NII sum is a composition artifact there.
    thin = df[df["n_banks"] < 160]
    assert len(thin) == 39
    assert thin["cal_quarter"].max().date().isoformat() == "2017-10-01"
    assert df.loc[df["cal_quarter"].dt.year >= 2020, "n_banks"].between(164, 169).all()


def test_fy2025_is_flagged_unverified(df):
    flagged = df[df["has_fy2025"]]
    assert len(flagged) == 6
    assert flagged["cal_quarter"].min().date().isoformat() == "2024-07-01"
    assert flagged["cal_quarter"].max().date().isoformat() == "2025-10-01"


def test_figure_regenerates_offline_from_the_snapshot(tmp_path):
    # The committed PNG must be reproducible from the committed CSV with no BigQuery.
    import subprocess, sys
    out = tmp_path / "overlay.png"
    r = subprocess.run(
        [sys.executable, str(ROOT / "analysis" / "liquidity_overlay.py"),
         "--csv", str(CSV), "--out", str(out)],
        capture_output=True, text=True, timeout=120,
    )
    assert r.returncode == 0, r.stderr
    assert out.exists() and out.stat().st_size > 50_000
    assert PNG.exists()
