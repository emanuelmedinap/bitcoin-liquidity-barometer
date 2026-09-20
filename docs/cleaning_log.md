# Cleaning Log — Checkpoint B

Every removal, alignment, and derivation decision with its reason. Companion to `sql/verification.sql` (evidence) and `docs/data_dictionary.md` (column spec). Nothing was fabricated; all exclusions are documented, not silent.

## Universe & exclusions

- **Universe = 175 banks** — KBWB (Invesco KBW Bank ETF, 24) + KRE (SPDR S&P Regional Banking ETF, 161 equity), 10 overlapping, deduped to 175. Holdings effectiveDate 2026-06-30.
  - *Note:* the former KBW Regional Banking ETF (KBWR) was reindexed to Invesco **FDIQ** (financial-data providers, not banks); **KRE substitutes** for the regional cross-section. KRE's 2 cash/non-equity lines (`US DOLLAR`, `SSI US GOV MONEY MARKET CLASS`) were excluded from the equity ticker set (flagged, not dropped silently).

- **4 banks excluded from the NII/financials layers (FDIC-reporting, no SEC XBRL).** Effective modeling universe = **171**. These are documented, not data errors:
  | ticker | reason |
  |---|---|
  | HIFS (Hingham Institution for Savings) | no SEC CIK usable for 10-Q XBRL — files with FDIC; SEC CIK 0002044671 files only 13F/13G |
  | TOWN (TowneBank) | no SEC registrant — files with FDIC/Fed |
  | OZK (Bank OZK) | has SEC CIK 0001569650 but 0 ten-Qs / no companyfacts XBRL (bank, not holding co) |
  | PFBC (Preferred Bank) | has SEC CIK 0001492165 but 0 ten-Qs / no companyfacts XBRL |
  - *Reason:* these report to their banking regulator (FDIC/Fed) under Exchange Act §12(i), not the SEC, so no 10-Q XBRL exists. CIK resolution (`company_tickers.json` → EDGAR company/full-text search) confirmed this rather than assumed it.

- **5 banks missing a specific field** (kept in the panel; that field is NULL + reported, never imputed):
  - `interest_income` missing: **AROW**
  - `noninterest_income` missing: **BANR**
  - `provision_credit_losses` missing: **BCAL, CBC**
  - *(all 171 have `nii`, `interest_expense`, `net_income`, and every stock field.)*

## Derivation & alignment decisions

- **Restatement dedup** — for each concept, one fact per `(start, end)` period, keeping the latest `filed` (tie-break: highest accession). Restatements resolve to the most recent filing.

- **Discrete quarters via YTD-differencing** — XBRL income-statement facts are cumulative fiscal-year-to-date, so discrete quarters are derived by differencing consecutive YTD facts within each fiscal-year start-group: Q1 = 3-month fact; Q2/Q3 = successive YTD differences; **Q4 = 10-K annual − 9-month YTD**. Only ~3-month (80–100 day) segments accepted; a directly-reported 3-month fact is preferred when present. (Decision #13.)

- **Per-bank fiscal-year-end** — `fiscal_year`/`fiscal_quarter` labeled by each bank's detected FYE month, not calendar month. 9 non-December filers handled: **AX, HTB, KRNY, NBN, SMBC = June**; **CASH, CFFN, TFSL, WAFD = September**. (Decision #15.)

- **NII primary tag verified** — `InterestIncomeExpenseNet` present for 171/171 (100%), taken directly; no per-filer `income − expense` derivation needed. `InterestExpense`, `InterestAndDividendIncomeOperating`, and ~110 component tags are secondary. Internal check `interest_income − interest_expense ≈ nii` holds for 99.46% of testable rows (residual = filer tag heterogeneity, labeled).

- **Balance-sheet tag basis — `total_loans` shifts at CECL (~2020).** No universal loans tag; the tag the panel lands on changes with CECL adoption, so the basis flips **within** each bank's own series. Verified at two year-ends: at **FY2016 (pre-CECL)** 135 of 138 banks source `LoansAndLeasesReceivableNetReportedAmount` = **net**; at **FY2024 (post-CECL)** ~106 banks source `FinancingReceivable…BeforeAllowance` — of which **103 are gross** and **3 net** — plus `NotesReceivableNet` (42, net) and `LoansAndLeasesReceivableNetReportedAmount` (4, net). So `total_loans` is **predominantly net before ~2020 and predominantly gross after**, a within-series net→gross break that makes `total_loans` (and derived `loan_deposit_ratio`) **NOT comparable across the CECL boundary**. Three filers — **JPM, CUBI, THFF** — read as net despite sitting on the before-allowance tag because they populate the before/after-allowance concepts with inverted values (JPM: `total_loans` net 1,299,590M = gross 1,323,643M − allowance 24,345M). **These are balance-sheet features not used in the reported analysis (the NII–M2–rate–bitcoin result), so the break does not affect the findings.**

- **Quarterly-average macro alignment** — each FRED series (M2SL, FEDFUNDS, T10Y2Y, CBBTCUSD) averaged over its available (non-`.`) observations within a **calendar quarter**, matched to each bank-quarter by the **calendar quarter of `period_end_date`** (= the 3-month accrual window; correct for non-December filers; within-quarter only, no look-ahead). Chosen because NII is a flow accrued over the quarter. (Aligns with decision #9, no look-ahead.)

- **Gap-aware growth transforms** — QoQ needs the exact t−1 fiscal quarter; YoY needs the exact t−4 (self-joined on the per-bank fiscal-quarter index). If the lag quarter is absent the transform is **NULL and flagged** via `qoq_prior_status`/`yoy_prior_status` (`start` vs `gap`) — never differenced across a gap, never fabricated. (Decision #8, model in changes; decision #10, no imputation.) Counts: QoQ present 10,056 / start 171 / gap 20; YoY present 9,553 / start 673 / gap 21.

## Sources dropped / caveats

- **Gold dropped as a barometer** (docs/cleaning_log.md, "Gold dropped"). No reachable free daily USD gold series: FRED discontinued the LBMA gold family (`GOLDAMGBD228NLBM` etc.) after ICE ended the license; stooq's CSV endpoint serves a JS bot-challenge; the Nasdaq Data Link API is Incapsula-WAF-blocked from this environment; the free Quandl `LBMA/GOLD` dataset is retired (now paid). **Bitcoin (`CBBTCUSD`) stands as the sole liquidity barometer.** Documented and honest — a source-availability limitation, not a data error; nothing substituted or invented.

- **≤0-base %-change caveat** — `net_income_*` and `provision_credit_losses_*` percent-changes are sign-ambiguous/unstable when the base quarter is ≤ 0 (zero base → NULL via `SAFE_DIVIDE`; negative base makes % change hard to interpret). Applied as specified (they are money levels) but flagged for downstream modeling.

- **No forward-fill / no imputation** — missing values stay NULL and are flagged (`flags` column, `*_prior_status`), never filled. (Decision #10.)
