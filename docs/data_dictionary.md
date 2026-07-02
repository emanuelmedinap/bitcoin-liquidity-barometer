# Data Dictionary — `banks_marts.analysis_panel`

Analysis-ready bank × fiscal-quarter panel. **10,247 rows**, one per (bank, fiscal quarter), anchored on `banks_clean.nii_quarterly`. 55 columns.

Conventions: **money** amounts are in **USD** (as reported in XBRL, whole dollars). **Rates** are in **percent (%)**. `*_qoq`/`*_yoy` = percent change (fraction, e.g. 0.043 = +4.3%). `*_qoq_chg`/`*_yoy_chg` = first difference in **percentage points**. Lags are per-bank on the fiscal-quarter index; a transform is NULL when the exact lag quarter is absent (never differenced across a gap — see `qoq_prior_status`/`yoy_prior_status`).

## Identity keys
| column | type | definition | source | transform | units |
|---|---|---|---|---|---|
| cik | STRING | SEC Central Index Key (zero-padded 10) | SEC `company_tickers.json` / EDGAR | none | id |
| ticker | STRING | Exchange ticker | KBWB/KRE holdings | none | id |
| bank_type | STRING | `money_center_large` (KBWB only) · `large_regional` (both) · `regional` (KRE only) | `banks_raw.universe` flags | derived from in_kbwb/in_kre | category |
| period_end_date | DATE | Fiscal-quarter end date (balance-sheet / accrual end) | SEC XBRL fact period end | none | date |
| fiscal_year | INT64 | Fiscal year (by each bank's detected FYE) | derived | per-bank FYE labeling | year |
| fiscal_quarter | INT64 | Fiscal quarter 1–4 (by each bank's FYE) | derived | per-bank FYE labeling | 1–4 |

## Target & levels
| column | type | definition | source | transform | units | approximation |
|---|---|---|---|---|---|---|
| nii | NUMERIC | Net interest income (discrete quarter) | SEC XBRL `InterestIncomeExpenseNet` | YTD-differenced; Q4 = annual − 9-mo | USD | — |
| m2 | FLOAT | M2 money stock, quarterly avg | FRED `M2SL` | avg of monthly obs in calendar quarter | USD billions | — |
| fed_funds | FLOAT | Effective federal funds rate, quarterly avg | FRED `FEDFUNDS` | avg of monthly obs in calendar quarter | % | — |
| yield_slope | FLOAT | 10y−2y Treasury spread, quarterly avg | FRED `T10Y2Y` | avg of available daily obs in calendar quarter | % (pp) | — |
| bitcoin | FLOAT | Coinbase BTC/USD, quarterly avg | FRED `CBBTCUSD` | avg of available daily obs in calendar quarter | USD | starts 2015 (Q4-2014 first obs); NULL before |
| loan_deposit_ratio | NUMERIC | total_loans / total_deposits | `features_quarterly` | level (kept) | ratio | inherits total_loans net/gross basis |
| size_log_assets | FLOAT | ln(total_assets) | `features_quarterly` | level (kept) | ln(USD) | — |
| equity_ratio | NUMERIC | total_equity / total_assets | `features_quarterly` | level (kept) | ratio | — |
| nim_approx | NUMERIC | nii / total_assets | `features_quarterly` | level (kept) | ratio (quarterly) | **APPROXIMATE — uses TOTAL assets, not average EARNING assets (not pulled); not annualized** |
| interest_income | NUMERIC | Total interest & dividend income (discrete quarter) | XBRL `InterestAndDividendIncomeOperating`→`InterestIncomeOperating` | YTD-differenced | USD | — |
| interest_expense | NUMERIC | Total interest expense (discrete quarter) | XBRL `InterestExpense`→`InterestExpenseOperating` | YTD-differenced | USD | — |
| noninterest_income | NUMERIC | Noninterest income (discrete quarter) | XBRL `NoninterestIncome` | YTD-differenced | USD | — |
| net_income | NUMERIC | Net income (discrete quarter) | XBRL `NetIncomeLoss`→`ProfitLoss` | YTD-differenced | USD | can be ≤0 → %-change unstable |
| provision_credit_losses | NUMERIC | Provision for credit/loan losses (discrete quarter) | XBRL `ProvisionForLoanAndLeaseLosses`→`…LoanLeaseAndOtherLosses`→`…LoanLossesExpensed` | YTD-differenced, per-quarter coalesced | USD | can be ≤0 → %-change unstable |
| total_assets | NUMERIC | Total assets (period end) | XBRL `Assets` | instant (point-in-time) | USD | — |
| total_loans | NUMERIC | Total loans (period end) | XBRL `LoansAndLeasesReceivableNetReportedAmount`→`…NetOfDeferredIncome`→`NotesReceivableNet`→`FinancingReceivable…BeforeAllowance` | instant | USD | **BASIS HETEROGENEOUS — mostly net-of-allowance; 6 banks (incl. JPM) use CECL FinancingReceivable tag; mixes net & gross** |
| total_deposits | NUMERIC | Total deposits (period end) | XBRL `Deposits` | instant | USD | — |
| total_equity | NUMERIC | Total stockholders' equity, parent (period end) | XBRL `StockholdersEquity` | instant | USD | parent-only (excludes NCI) |
| flags | STRING | Comma-list of feature-build data flags (carried from `features_quarterly`) | derived | none | text |

## Growth transforms — money levels → percent change (fraction)
`*_qoq` = (x_t − x_{t−1}) / x_{t−1};  `*_yoy` = (x_t − x_{t−4}) / x_{t−4}. NULL if the exact lag quarter is absent, or base is null/zero.
| columns | base | type |
|---|---|---|
| nii_qoq, nii_yoy | nii | FLOAT |
| m2_qoq, m2_yoy | m2 | FLOAT |
| bitcoin_qoq, bitcoin_yoy | bitcoin | FLOAT |
| interest_income_qoq, interest_income_yoy | interest_income | FLOAT |
| interest_expense_qoq, interest_expense_yoy | interest_expense | FLOAT |
| noninterest_income_qoq, noninterest_income_yoy | noninterest_income | FLOAT |
| net_income_qoq, net_income_yoy | net_income | FLOAT (⚠ ≤0-base unstable) |
| provision_credit_losses_qoq, provision_credit_losses_yoy | provision_credit_losses | FLOAT (⚠ ≤0-base unstable) |
| total_assets_qoq, total_assets_yoy | total_assets | FLOAT |
| total_loans_qoq, total_loans_yoy | total_loans | FLOAT |
| total_deposits_qoq, total_deposits_yoy | total_deposits | FLOAT |
| total_equity_qoq, total_equity_yoy | total_equity | FLOAT |

## Growth transforms — rates → first difference (percentage points)
`*_qoq_chg` = x_t − x_{t−1};  `*_yoy_chg` = x_t − x_{t−4}. **NOT** percent change. NULL if exact lag quarter absent.
| column | base | type | units |
|---|---|---|---|
| fed_funds_qoq_chg, fed_funds_yoy_chg | fed_funds | FLOAT | pp |
| yield_slope_qoq_chg, yield_slope_yoy_chg | yield_slope | FLOAT | pp |

## Lag-availability status (explains every transform NULL)
| column | type | values |
|---|---|---|
| qoq_prior_status | STRING | `present` (t−1 exists) · `start` (t−1 predates the bank's series) · `gap` (t−1 missing mid-series → not differenced) |
| yoy_prior_status | STRING | `present` (t−4 exists) · `start` (t−4 predates series) · `gap` (t−4 missing → not differenced) |
