-- ============================================================================
-- Liquidity overlay — quarterly source series for the two-panel figure
-- Project: YOUR_GCP_PROJECT
-- Produces ONE row per CALENDAR quarter with the three series the figure plots:
--   system_nii = SUM(nii) across all banks whose accrual-quarter ends in that
--                calendar quarter (analysis_panel; calendar quarter of period_end_date)
--   m2         = FRED M2SL   quarterly average (monthly obs)   [banks_raw.fred_series]
--   bitcoin    = FRED CBBTCUSD quarterly average (daily obs)   [banks_raw.fred_series]
-- has_fy2025   = TRUE if any bank-row in the quarter is fiscal_year 2025
--                (drives the UNVERIFIED shading on the chart; see DECISIONS.md §6).
-- Alignment: calendar quarter of period_end_date = the 3-month accrual window,
--   the same within-quarter, no-look-ahead basis used to join FRED elsewhere
--   (docs/cleaning_log.md, decision #9).
-- Cost: runs under the 200 GB maximum_bytes_billed cap (~/.bigqueryrc; the
--   generator also passes --maximum_bytes_billed explicitly).
-- ============================================================================
WITH nii_q AS (
  SELECT
    DATE_TRUNC(period_end_date, QUARTER) AS cal_quarter,
    SUM(nii)                             AS system_nii,
    LOGICAL_OR(fiscal_year = 2025)       AS has_fy2025,
    COUNT(DISTINCT cik)                  AS n_banks
  FROM `YOUR_GCP_PROJECT.banks_marts.analysis_panel`
  WHERE nii IS NOT NULL
  GROUP BY cal_quarter
),
fred_q AS (
  SELECT
    DATE_TRUNC(date, QUARTER) AS cal_quarter,
    AVG(IF(series_id = 'M2SL'     AND value != '.', SAFE_CAST(value AS FLOAT64), NULL)) AS m2,
    AVG(IF(series_id = 'CBBTCUSD' AND value != '.', SAFE_CAST(value AS FLOAT64), NULL)) AS bitcoin
  FROM `YOUR_GCP_PROJECT.banks_raw.fred_series`
  WHERE series_id IN ('M2SL', 'CBBTCUSD')
  GROUP BY cal_quarter
)
SELECT
  n.cal_quarter,
  n.system_nii,
  f.m2,
  f.bitcoin,
  n.has_fy2025,
  n.n_banks
FROM nii_q n
LEFT JOIN fred_q f USING (cal_quarter)
ORDER BY n.cal_quarter;
