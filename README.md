# msbai-dwd-a2-em5844

**Bank Revenue & the Flood of Money** — an end-to-end data product on US public banks and the monetary/liquidity cycle (NYU Stern MSBAi, Assignment 2).

## Overview

This project assembles an analysis-ready panel of US public banks' quarterly financials (SEC EDGAR XBRL) joined to Federal Reserve liquidity series and bitcoin, to examine one question: **does system liquidity — the money supply (M2), policy rates, and the yield-curve slope — drive US bank net interest income (NII), with bitcoin acting as a *barometer* of that liquidity rather than a cause of bank revenue?** The pipeline lands raw filings and macro series, types and cleans them into discrete quarterly facts, and materializes a bank × fiscal-quarter panel for analysis. For the reading of the evidence — what the figure shows and where it should not be trusted — see [`DECISIONS.md`](DECISIONS.md); this README describes the data product, not its conclusion.

## Scope

**Effective universe: 171 US public banks.** Built from two ETFs and deduped:

- **KBWB** (Invesco KBW Bank ETF) — 24 constituents
- **KRE** (SPDR S&P Regional Banking ETF) — 161 regional equity constituents
- 10 overlap → **175 distinct banks**
- **4 excluded** as FDIC-reporting filers with no SEC XBRL (HIFS, TOWN, OZK, PFBC) → **171** in the financials/NII layers.

The panel is **bank × fiscal quarter**: `banks_marts.analysis_panel` holds **10,247 rows** across the 171 banks, 2008-Q2 → 2026-Q1.

## Data sources & APIs

- **SEC EDGAR — companyfacts (XBRL).** Quarterly and annual financials from 10-Q/10-K filings, pulled per-CIK from the companyfacts API. Requests require a **descriptive `User-Agent`** header per SEC fair-access policy.
- **FRED API.** Four series: **`M2SL`** (M2 money stock), **`FEDFUNDS`** (effective federal funds rate), **`T10Y2Y`** (10y−2y Treasury spread), and **`CBBTCUSD`** (Coinbase BTC/USD — bitcoin, the liquidity barometer).
- **Gold — dropped.** No reachable free daily USD gold series survived; bitcoin stands as the sole barometer. See [`DECISIONS.md` §5.1](DECISIONS.md) for the four dead-end sources and rationale.

## Storage & architecture

- **GCP project:** `msbai-dwd-em5844`.
- **BigQuery pipeline:** `banks_raw` (verbatim landing, all-STRING) → `banks_clean` (typed, cleaned, discrete quarterly facts) → `banks_marts` (analysis-ready). The analysis-ready table is **`banks_marts.analysis_panel`**.
- **Cost guard:** a hard **200 GB per-query cap** (`maximum_bytes_billed = 214748364800`) enforced on every query, via `~/.bigqueryrc` for the `bq` CLI and set explicitly on each Python/programmatic job.

## Reproducibility

| Path | What it is |
|---|---|
| [`DECISIONS.md`](DECISIONS.md) | Executive defense of the data, method, and caveats; the reading of the evidence. |
| [`docs/cleaning_log.md`](docs/cleaning_log.md) | Every exclusion, derivation, and alignment decision with its reason. |
| [`docs/data_dictionary.md`](docs/data_dictionary.md) | Column-level spec for `banks_marts.analysis_panel` (55 columns). |
| [`sql/verification.sql`](sql/verification.sql) | Integrity, reconciliation, and coverage checks — each with its committed result. |
| [`sql/liquidity_overlay.sql`](sql/liquidity_overlay.sql) | Query behind the liquidity-overlay figure (quarter-aligned system NII + M2 + bitcoin). |
| [`analysis/liquidity_overlay.py`](analysis/liquidity_overlay.py) | Figure generator (runs the SQL under the cap, or replots offline from the CSV snapshot). |
| [`analysis/liquidity_overlay_data.csv`](analysis/liquidity_overlay_data.csv) | Committed 72-quarter data snapshot — regenerates the figure without BigQuery. |
| [`analysis/liquidity_overlay.png`](analysis/liquidity_overlay.png) | The two-panel figure. |
| [`index.html`](index.html) | Self-contained one-page report (GitHub Pages), reconciled to the CSV snapshot. |
| [`CLAUDE.md`](CLAUDE.md) | Working brief and decision log. |
