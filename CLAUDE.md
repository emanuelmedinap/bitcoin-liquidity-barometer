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

- **Universe:** ~75 banks — KBW Bank Index + KBW Regional Banking Index constituents, SIC `6020`–`6022`. Exact ticker → CIK list **TO VERIFY** at pull.
- **NII XBRL tags:** `InterestAndDividendIncomeOperating`, `InterestExpense`, `InterestIncomeExpenseNet` — presence **TO VERIFY** per filer; derive `NII = interest income − interest expense` when the net tag is absent.
- **Frequency:** period-end vs quarterly-average — **decide and document** before joining to FRED.
- **Bitcoin history:** usable from ~2014 onward.
- **Grain:** bank × quarter, ~48 quarters, ≈ 3,500–4,000 rows.

---

## Decisions (each with a one-line reason)

1. **NII is the target** — it is the revenue line most directly exposed to rates and liquidity.
2. **75-bank scope** — enough cross-section for identification while keeping the panel tractable over time.
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

---

## Working rule

Mark anything not source-confirmed as **TO VERIFY**. Do not invent tickers or XBRL tags.
