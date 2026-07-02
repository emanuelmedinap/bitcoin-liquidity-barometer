# CLAUDE.md — Bank Revenue & the Flood of Money (Assignment 2)

**Purpose:** working brief and repo-as-memory for an end-to-end data product on US public banks and the monetary/liquidity cycle. Claude Code re-reads this at the start of every session. Decisions live here, not in chat.

**Sources:** SEC EDGAR 10-Q financials (XBRL) · FRED (`M2SL`, `FEDFUNDS`, `T10Y2Y`) · gold (USD spot) · bitcoin (USD, public API). Joined on the fiscal quarter.

> Anything not confirmed from source is marked **TO VERIFY** and checked at pull time. Do not invent tickers or XBRL tags — unknowns stay labeled.

---

## ⛔ Hard cost rule — 200 GB query cap (non-negotiable)

**EVERY BigQuery query MUST enforce `maximum_bytes_billed = 214748364800` (200 GB). No query runs without it.**

- **`bq` CLI:** inherits the cap from `~/.bigqueryrc`:
  ```ini
  [query]
  maximum_bytes_billed = 214748364800
  ```
- **Python:** set it explicitly on every job — `job_config.maximum_bytes_billed = 214748364800`. A query without this bound does not run.

---

## North star

Does **system liquidity** — M2, policy rates, and the yield-curve slope — drive **US bank net interest income (NII)**, and do **gold and bitcoin co-move as barometers** of that liquidity rather than as causes of bank revenue?

---

## Objects

- **GCP project:** `msbai-dwd-em5844` (shared; A2 lives in its own datasets).
- **Datasets:** `banks_raw` (landing) → `banks_clean` (typed views) → `banks_marts` (analysis-ready).
- **Repo:** `msbai-dwd-a2-em5844`.
- **App:** Streamlit on Cloud Run, reading a static data bundle (no live query at serve time).

---

## Facts (source-anchored; verify before trusting)

- **Universe:** 175 banks — KBWB (Invesco KBW Bank ETF, 24 constituents, verified) + KRE (SPDR S&P Regional Banking ETF, 161 regional constituents), 10 overlapping, deduped to 175. Holdings effectiveDate 2026-06-30. Note: the former KBW Regional Banking ETF (KBWR) has been reindexed to **Invesco FDIQ** (financial-data providers, not banks), so **KRE substitutes for the regional cross-section**. Exact ticker → CIK list **TO VERIFY** at pull.
- **NII XBRL tags (VERIFIED at pull):** `InterestIncomeExpenseNet` is the **primary** target — 171/171 banks report it (100% coverage), so NII is taken directly and **no per-filer `income − expense` derivation is needed**. `InterestExpense` (169/171) and `InterestAndDividendIncomeOperating` (166/171) plus the ~110 finer component tags are **secondary** (cross-checks / decomposition only).
- **Frequency:** period-end vs quarterly-average — **decide and document** before joining to FRED.
- **Bitcoin history:** usable from ~2014 onward.
- **Grain:** bank × quarter. Clean NII table `banks_clean.nii_quarterly` (`cik, ticker, period_end_date, fiscal_year, fiscal_quarter, nii`) landed with **10,247 rows across 171 banks, 2008-Q2 → 2026-Q1**. Effective universe is **171** — 4 of the 175 are excluded as FDIC-reporting (no SEC XBRL): HIFS, TOWN (no SEC CIK), OZK, PFBC (CIK but no companyfacts).

---

## Decisions (each with a one-line reason)

1. **NII is the target** — it is the revenue line most directly exposed to rates and liquidity.
2. **175-bank scope** — KBWB (24) + KRE (161) deduped to 175; enough cross-section for identification while keeping the panel tractable over time.
3. **Isolated `banks_*` datasets** — A2 stays separate from other work in the shared project.
4. **Raw all-STRING, load-first** — land data verbatim, then type and clean in a view (no lossy parsing at ingest).
5. **Clean in a view** — typing/cleaning is reproducible and re-runnable off immutable raw.
6. **Identification via the bank cross-section**, not the single macro scalar — many banks per quarter beat one aggregate series.
7. **Gold / bitcoin = correlation only** — treated as barometers, never as causal drivers of NII.
8. **Model in growth/changes** — differenced series to avoid spurious regression (Granger–Newbold).
9. **Temporal split, no look-ahead** — train on past, test on future; no leakage across the time boundary.
10. **No forward-fill** — flag missing values, do not impute them.
11. **NOT a Um et al. replication** — this is an independent design, not a reproduction.
12. **External verification** — check NII against each 10-Q and M2 against FRED directly.
13. **Discrete quarters via YTD-differencing** — XBRL income facts are cumulative, so derive each quarter from consecutive fiscal-year-to-date facts (Q1 = 3-month; Q2/Q3 = successive YTD diffs; **Q4 = 10-K annual − 9-month YTD**), accepting only ~3-month (80–100 day) segments and preferring a directly-reported 3-month fact when present.
14. **Restatement dedup** — one fact per `(start, end)`, keeping the latest `filed` (then highest accession), so restatements resolve to the most recent filing.
15. **Per-bank fiscal-year-end** — label `fiscal_year`/`fiscal_quarter` by each bank's detected FYE month, not the calendar month (9 non-December filers: AX/HTB/KRNY/NBN/SMBC = June; CASH/CFFN/TFSL/WAFD = Sept).
16. **NII layer is a materialized table** (not a view) — the differencing logic can't be a simple view; `banks_clean.nii_quarterly` is rebuilt deterministically from immutable `banks_raw`. (Refines decision #5 for this layer.)
17. **JPMorgan verified against 10-Q** — derived Q1–Q3 equal JPM's reported 3-month `InterestIncomeExpenseNet` facts exactly; Q4 reconstructed as annual − 9-month YTD, magnitudes consistent with reported NII.

---

## Working rule

Mark anything not source-confirmed as **TO VERIFY**. Do not invent tickers or XBRL tags.
