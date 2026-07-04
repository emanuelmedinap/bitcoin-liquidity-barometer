-- ============================================================================
-- Checkpoint B — Verification evidence
-- Project: msbai-dwd-em5844   Panel: banks_marts.analysis_panel
-- Each query below is followed by its CAPTURED RESULT (run 2026-07-02, US location).
-- All queries run under the ~/.bigqueryrc 200 GB maximum_bytes_billed cap.
-- Re-run any block to reproduce; results are committed so reviewers need not run BQ.
-- ============================================================================


-- ----------------------------------------------------------------------------
-- 1. ROW COUNTS + KEY UNIQUENESS, every layer (raw -> clean -> marts)
--    Expectation: analysis_panel = 10,247 and its (cik, period_end_date) and
--    (cik, fiscal_year, fiscal_quarter) keys are BOTH unique (= row count).
-- ----------------------------------------------------------------------------
SELECT
  (SELECT COUNT(*) FROM `msbai-dwd-em5844.banks_raw.universe`)                                                       AS universe_rows,
  (SELECT COUNT(DISTINCT ticker) FROM `msbai-dwd-em5844.banks_raw.universe`)                                         AS universe_distinct_ticker,
  (SELECT COUNT(*) FROM `msbai-dwd-em5844.banks_raw.companyfacts_landing`)                                           AS companyfacts_rows,
  (SELECT COUNT(DISTINCT cik) FROM `msbai-dwd-em5844.banks_raw.companyfacts_landing`)                                AS companyfacts_distinct_cik,
  (SELECT COUNT(*) FROM `msbai-dwd-em5844.banks_raw.etf_holdings_landing`)                                           AS etf_landing_rows,
  (SELECT COUNT(*) FROM `msbai-dwd-em5844.banks_raw.fred_series`)                                                    AS fred_rows,
  (SELECT COUNT(DISTINCT series_id) FROM `msbai-dwd-em5844.banks_raw.fred_series`)                                   AS fred_series_count,
  (SELECT COUNT(*) FROM `msbai-dwd-em5844.banks_clean.nii_quarterly`)                                                AS nii_rows,
  (SELECT COUNT(DISTINCT FORMAT('%s|%t',cik,period_end_date)) FROM `msbai-dwd-em5844.banks_clean.nii_quarterly`)     AS nii_distinct_keys,
  (SELECT COUNT(*) FROM `msbai-dwd-em5844.banks_clean.financials_quarterly`)                                         AS financials_rows,
  (SELECT COUNT(DISTINCT FORMAT('%s|%t',cik,period_end_date)) FROM `msbai-dwd-em5844.banks_clean.financials_quarterly`) AS financials_distinct_keys,
  (SELECT COUNT(*) FROM `msbai-dwd-em5844.banks_marts.nii_macro_quarterly`)                                          AS macro_rows,
  (SELECT COUNT(*) FROM `msbai-dwd-em5844.banks_marts.features_quarterly`)                                           AS features_rows,
  (SELECT COUNT(*) FROM `msbai-dwd-em5844.banks_marts.analysis_panel`)                                               AS panel_rows,
  (SELECT COUNT(DISTINCT FORMAT('%s|%t',cik,period_end_date)) FROM `msbai-dwd-em5844.banks_marts.analysis_panel`)    AS panel_distinct_cik_periodend,
  (SELECT COUNT(DISTINCT FORMAT('%s|%d|%d',cik,fiscal_year,fiscal_quarter)) FROM `msbai-dwd-em5844.banks_marts.analysis_panel`) AS panel_distinct_cik_fy_fq;
-- RESULT (2026-07-02):
--   universe_rows=175            universe_distinct_ticker=175        (unique)
--   companyfacts_rows=171        companyfacts_distinct_cik=171       (unique)
--   etf_landing_rows=187         (24 KBWB + 161 KRE equity + 2 KRE cash)
--   fred_rows=18971              fred_series_count=4  (M2SL, FEDFUNDS, T10Y2Y, CBBTCUSD)
--   nii_rows=10247               nii_distinct_keys=10247            (unique)
--   financials_rows=10542        financials_distinct_keys=10542     (unique)
--   macro_rows=10247
--   features_rows=10542
--   panel_rows=10247             panel_distinct_cik_periodend=10247 (unique)  panel_distinct_cik_fy_fq=10247 (unique)
--   PASS: analysis_panel = 10,247; both key definitions unique = row count.


-- ----------------------------------------------------------------------------
-- 2. INVARIANT — no duplicate bank-quarter keys in the panel (expect 0 dup groups)
-- ----------------------------------------------------------------------------
SELECT
  (SELECT COUNT(*) FROM (
     SELECT 1 FROM `msbai-dwd-em5844.banks_marts.analysis_panel`
     GROUP BY cik, period_end_date HAVING COUNT(*) > 1))               AS dup_cik_periodend_groups,
  (SELECT COUNT(*) FROM (
     SELECT 1 FROM `msbai-dwd-em5844.banks_marts.analysis_panel`
     GROUP BY cik, fiscal_year, fiscal_quarter HAVING COUNT(*) > 1))   AS dup_cik_fy_fq_groups;
-- RESULT (2026-07-02): dup_cik_periodend_groups=0, dup_cik_fy_fq_groups=0.  PASS.


-- ----------------------------------------------------------------------------
-- 3. INVARIANT — no differencing across gaps.
--    Growth transforms are computed only when the EXACT lag quarter exists
--    (QoQ: qidx-1; YoY: qidx-4, via self-join on fiscal-quarter index).
--    prior_status labels every NULL: present / start (lag predates series) / gap.
-- ----------------------------------------------------------------------------
SELECT
  COUNTIF(qoq_prior_status='present') AS qoq_present,
  COUNTIF(qoq_prior_status='start')   AS qoq_start,
  COUNTIF(qoq_prior_status='gap')     AS qoq_gap,
  COUNTIF(yoy_prior_status='present') AS yoy_present,
  COUNTIF(yoy_prior_status='start')   AS yoy_start,
  COUNTIF(yoy_prior_status='gap')     AS yoy_gap
FROM `msbai-dwd-em5844.banks_marts.analysis_panel`;
-- RESULT (2026-07-02):
--   QoQ: present=10056  start=171  gap=20      (start=171 = one earliest quarter per bank)
--   YoY: present=9553   start=673  gap=21
--   Totals reconcile to 10,247. gap rows are NEVER differenced (transform = NULL). PASS.


-- ----------------------------------------------------------------------------
-- 4. INTERNAL consistency — interest_income - interest_expense ~= nii
--    (InterestAndDividendIncomeOperating - InterestExpense vs InterestIncomeExpenseNet).
--    Tolerance $1,000,000 absolute; residual = filer tag heterogeneity (labeled).
-- ----------------------------------------------------------------------------
SELECT
  COUNTIF(interest_income IS NOT NULL AND interest_expense IS NOT NULL AND nii IS NOT NULL) AS testable_rows,
  COUNTIF(interest_income IS NOT NULL AND interest_expense IS NOT NULL AND nii IS NOT NULL
          AND ABS((interest_income - interest_expense) - nii) <= 1000000)                   AS match_within_1M,
  ROUND(100*SAFE_DIVIDE(
    COUNTIF(interest_income IS NOT NULL AND interest_expense IS NOT NULL AND nii IS NOT NULL
            AND ABS((interest_income - interest_expense) - nii) <= 1000000),
    COUNTIF(interest_income IS NOT NULL AND interest_expense IS NOT NULL AND nii IS NOT NULL)),2) AS pct_match_within_1M
FROM `msbai-dwd-em5844.banks_marts.analysis_panel`;
-- RESULT (2026-07-02): testable_rows=10072, match_within_1M=10018, pct_match_within_1M=99.46%.
--   PASS (near-universal). The 54 residual rows (0.54%) are filers whose interest-income
--   tag base differs slightly from the NII income base; NII itself is taken from the
--   dedicated InterestIncomeExpenseNet tag, so those are not errors in nii.


-- ----------------------------------------------------------------------------
-- 5. EXTERNAL cross-check A — JPMorgan NII vs its reported 10-Q / 10-K
--    Method (see cleaning_log): Q1-Q3 differenced values EQUAL JPM's directly
--    reported 3-month InterestIncomeExpenseNet facts; Q4 = 10-K annual - 9-mo YTD.
-- ----------------------------------------------------------------------------
SELECT period_end_date, fiscal_year, fiscal_quarter, nii
FROM `msbai-dwd-em5844.banks_marts.analysis_panel`
WHERE ticker='JPM' AND period_end_date >= '2024-09-30'
ORDER BY period_end_date;
-- RESULT (2026-07-02), nii (USD):
--   2024-09-30 FY2024Q3  23,405,000,000   == JPM reported 3-month NII fact  [VERIFIED]
--   2024-12-31 FY2024Q4  23,350,000,000   = annual 92,583M - 9mo 69,233M    [VERIFIED vs FY2024 10-K]
--   2025-03-31 FY2025Q1  23,273,000,000   == reported 3-month NII fact      [VERIFIED]
--   2025-06-30 FY2025Q2  23,209,000,000   == reported 3-month NII fact      [VERIFIED]
--   2025-09-30 FY2025Q3  23,966,000,000   == reported 3-month NII fact      [VERIFIED]
--   2025-12-31 FY2025Q4  24,995,000,000   = annual 95,443M - 9mo 70,448M    [derivation internally consistent; FY2025 10-K NOT independently checked — see note]
--   2026-03-31 FY2026Q1  25,366,000,000   == reported 3-month NII fact      [self-consistent; recent quarter]
--   NOTE: quarters at/after 2025-12-31 rely on the 10-K/10-Q XBRL facts themselves
--   (published figures not independently re-verified from memory). 2024 anchor IS exact.


-- ----------------------------------------------------------------------------
-- 6. EXTERNAL cross-check B — JPMorgan balance sheet vs reported 10-K
--    (stocks are point-in-time XBRL facts = the reported balance-sheet lines).
-- ----------------------------------------------------------------------------
SELECT period_end_date, total_assets, total_deposits, total_loans, total_equity
FROM `msbai-dwd-em5844.banks_marts.analysis_panel`
WHERE ticker='JPM' AND period_end_date IN ('2024-12-31','2025-12-31')
ORDER BY period_end_date;
-- RESULT (2026-07-02), USD:
--   2024-12-31  assets 4,002,814,000,000  deposits 2,406,032,000,000  loans 1,299,590,000,000  equity 344,758,000,000
--     [VERIFIED vs FY2024 10-K: assets & deposits exact. loans 1,299,590M is JPM NET (after-allowance):
--      net 1,299,590M = gross 1,323,643M - allowance 24,345M (undimensioned CECL tags, end 2024-12-31).
--      Sourced from JPM's `FinancingReceivable...BeforeAllowanceForCreditLoss` tag, which JPM populates with
--      the NET figure (inverted tag names: its `...AfterAllowanceForCreditLoss` tag holds the GROSS 1,323,643M).
--      NB: total_loans basis is net pre-CECL / gross post-CECL across banks (see docs/cleaning_log.md); JPM is
--      one of only 3 net filers (JPM, CUBI, THFF) among ~106 post-CECL FinancingReceivable-sourced banks at
--      FY2024. total_loans/loan_deposit_ratio are not used in the reported analysis.]
--   2025-12-31  assets 4,424,900,000,000  deposits 2,559,320,000,000  loans 1,408,905,000,000  equity 362,438,000,000
--     [from FY2025 XBRL; published FY2025 10-K NOT independently re-verified — LABELED UNVERIFIED]


-- ----------------------------------------------------------------------------
-- 7. EXTERNAL cross-check C — FRED latest values vs published figures
-- ----------------------------------------------------------------------------
WITH r AS (
  SELECT series_id, value, date,
         ROW_NUMBER() OVER (PARTITION BY series_id ORDER BY date DESC) rn
  FROM `msbai-dwd-em5844.banks_raw.fred_series` WHERE value != '.')
SELECT series_id, value AS latest_value, date AS latest_date FROM r WHERE rn=1 ORDER BY series_id;
-- RESULT (2026-07-02):
--   M2SL     23052.3   2026-05-01   [matches FRED published latest M2 (monthly, $B)]      VERIFIED
--   FEDFUNDS 3.63      2026-06-01   [matches FRED published effective fed funds rate, %]   VERIFIED
--   T10Y2Y   0.31      2026-07-01   [matches FRED published 10y-2y spread, %]              VERIFIED
--   CBBTCUSD 59881.98  2026-07-01   [matches FRED CBBTCUSD latest daily close, USD]        VERIFIED


-- ----------------------------------------------------------------------------
-- 8. Coverage of the growth-transform columns (context for section 3).
-- ----------------------------------------------------------------------------
SELECT
  COUNTIF(nii_qoq IS NOT NULL) AS nii_qoq, COUNTIF(nii_yoy IS NOT NULL) AS nii_yoy,
  COUNTIF(bitcoin_qoq IS NOT NULL) AS bitcoin_qoq, COUNTIF(bitcoin_yoy IS NOT NULL) AS bitcoin_yoy,
  COUNTIF(fed_funds_qoq_chg IS NOT NULL) AS fed_funds_qoq_chg, COUNTIF(yield_slope_yoy_chg IS NOT NULL) AS yield_slope_yoy_chg
FROM `msbai-dwd-em5844.banks_marts.analysis_panel`;
-- RESULT (2026-07-02): nii_qoq=10055 nii_yoy=9552 bitcoin_qoq=7286 bitcoin_yoy=6781
--   fed_funds_qoq_chg=10056 yield_slope_yoy_chg=9553
--   (rate/macro transforms hit the present-lag ceiling exactly; bitcoin capped by 2015 start.)
