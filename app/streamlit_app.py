"""
Streamlit report — System liquidity vs. bank Net Interest Income.

Reproduces the static report (index.html) for Cloud Run, reading ONLY the
committed static bundle. It NEVER queries BigQuery at serve time:
  - analysis/liquidity_overlay.png          the two-panel figure
  - analysis/liquidity_overlay_data.csv     source for the reconciled-figures numbers
  - index.html                              source for the figure caption, Findings,
                                            caveats, and references — reused VERBATIM
                                            (extracted, never re-typed), plus its <style>.

Section order matches index.html: header → figure → reconciled figures →
Findings → caveats & disclaimer → references → footer.

Run locally:  streamlit run app/streamlit_app.py
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st
from bs4 import BeautifulSoup

BASE = Path(__file__).resolve().parents[1]           # repo root
PNG = BASE / "analysis" / "liquidity_overlay.png"
CSV = BASE / "analysis" / "liquidity_overlay_data.csv"
HTML = BASE / "index.html"


# --------------------------------------------------------------------------- #
# Static-bundle loaders (cached; no network, no BigQuery)                      #
# --------------------------------------------------------------------------- #
@st.cache_data
def load_soup() -> BeautifulSoup:
    return BeautifulSoup(HTML.read_text(encoding="utf-8"), "html.parser")


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV)
    df["cal_quarter"] = pd.to_datetime(df["cal_quarter"])
    df["has_fy2025"] = df["has_fy2025"].astype(str).str.lower().isin(["true", "1"])
    return df.sort_values("cal_quarter").reset_index(drop=True)


def qlabel(ts: pd.Timestamp) -> str:
    return f"{ts.year}-Q{(ts.month - 1) // 3 + 1}"


def reconciled_rows(df: pd.DataFrame) -> list[tuple[str, str]]:
    """Compute the reconciled-figures table straight from the CSV snapshot."""
    q = df["cal_quarter"]
    btc_first = df.loc[df["bitcoin"].notna(), "cal_quarter"].min()
    lo = int(df["n_banks"].min())
    lo_year = int(df.loc[df["n_banks"].idxmin(), "cal_quarter"].year)
    r20 = df.loc[df["cal_quarter"].dt.year >= 2020, "n_banks"]
    thin = df.loc[df["n_banks"] < 160, "cal_quarter"]
    stable_first = df.loc[df["n_banks"] >= 160, "cal_quarter"].min()
    fy = df.loc[df["has_fy2025"], "cal_quarter"]
    return [
        ("Coverage span", f"{len(df)} quarters, {qlabel(q.min())} → {qlabel(q.max())}"),
        ("Bitcoin data begins", f"{qlabel(btc_first)} (first observation) = index base quarter"),
        ("Bank coverage",
         f"ramps from {lo} ({lo_year}) to a stable {int(r20.min())}–{int(r20.max())} (~167) from 2020 on"),
        ("Thin-coverage window",
         f"n_banks &lt; 160 → {qlabel(thin.min())} – {qlabel(thin.max())}; "
         f"stable from {qlabel(stable_first)}"),
        ("FY2025 (UNVERIFIED)", f"{len(fy)} quarters, {qlabel(fy.min())} – {qlabel(fy.max())}"),
    ]


def section_by_h2(soup: BeautifulSoup, title: str):
    for sec in soup.find_all("section"):
        h2 = sec.find("h2")
        if h2 and h2.get_text(strip=True) == title:
            return sec
    raise KeyError(f"<section> with <h2>{title}</h2> not found in index.html")


# --------------------------------------------------------------------------- #
# Render — same section order as index.html                                   #
# --------------------------------------------------------------------------- #
st.set_page_config(page_title="System liquidity vs. bank Net Interest Income",
                   page_icon="📊", layout="centered")

soup = load_soup()
df = load_data()

# Reuse the page's own stylesheet verbatim so extracted fragments render as designed,
# plus a little scoping so it sits well inside Streamlit's container.
style = soup.find("style")
if style:
    st.html(f"<style>{style.decode_contents()}</style>"
            "<style>.block-container .wrap{max-width:100%;padding:0}"
            "section[data-testid='stMain'] img{border-radius:4px}</style>")

# 1) Header — title, north-star question, method note (verbatim, no assets)
st.html(str(soup.find("header")))

# 2) The figure — local PNG from the bundle + its verbatim caption
fig_sec = section_by_h2(soup, "The figure")
st.html(str(fig_sec.find("h2")))
st.image(str(PNG), width="stretch")
st.html(str(fig_sec.find("figcaption")))

# 3) Reconciled figures — numbers computed from the CSV snapshot
st.html("<h2>Reconciled figures</h2>")
rows = "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in reconciled_rows(df))
st.html(f'<div class="facts"><dl>{rows}</dl></div>')

# 4) Findings — the author's text, reused VERBATIM from index.html
st.html(str(section_by_h2(soup, "Findings")))

# 5) Caveats & disclaimer — verbatim
st.html(str(section_by_h2(soup, "Caveats & disclaimer")))

# 6) References — anchor papers + links, verbatim
st.html(str(section_by_h2(soup, "References")))

# 7) Footer — verbatim
footer = soup.find("footer")
if footer:
    st.html(str(footer))

st.caption("Static bundle only — no BigQuery at serve time. "
           "Figure and numbers reconcile to analysis/liquidity_overlay_data.csv.")
