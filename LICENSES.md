# Licenses of what this repository uses

Every external source, the terms it comes under, and the date those terms were
read. This project is individual academic coursework for *Dealing With Data*,
NYU Stern MSBAi, July 2026. It is not a commercial product, the data is not
sold, and nothing here is presented as a dataset for redistribution.

| source | what is used | terms | read on |
|---|---|---|---|
| SEC EDGAR, companyfacts API (data.sec.gov) | quarterly XBRL facts for 171 banks, aggregated into the panel; only a 72-quarter system-level sum is committed | Work of the US federal government, public domain. SEC fair-access policy requires a descriptive User-Agent, which the build used | 2026-09-20 |
| FRED, Federal Reserve Bank of St. Louis: `M2SL`, `FEDFUNDS`, `T10Y2Y` | quarterly averages, committed in `analysis/liquidity_overlay_data.csv` | Federal Reserve series, public domain, citation requested. FRED terms allow use in research and reports with attribution and require noting that the data was accessed via FRED | 2026-09-20 |
| FRED: `CBBTCUSD` (Coinbase Bitcoin, USD) | 46 quarterly averages from 2014-Q4, committed in the same CSV | **Copyright Coinbase.** FRED's series page states that reproduction of Coinbase data in any form is prohibited without Coinbase's prior written permission, and FRED's terms ask users to contact third-party owners for anything beyond personal use. Written permission was not requested. What is committed is a small derived aggregate (quarterly means, not the series), used for non-commercial academic analysis, and it is disclosed here rather than hidden. If this repository ever stops being academic, this column is the first thing to replace or clear with Coinbase | 2026-09-20 |
| ETF constituent lists: Invesco KBWB, SPDR KRE | ticker lists as of 2026-06-30, used to define the bank universe; only the resulting count (175, 171 after exclusions) and four excluded tickers are stated | Published by the issuers on their public sites; used as a reference list, not redistributed | 2026-09-20 |
| Borio, Gambacorta and Hofmann (2017); Granger and Newbold (1974) | cited as anchor papers | Academic citation, no reproduction of content | 2026-09-20 |

Code in this repository: MIT, see `LICENSE`.

Attribution as FRED requests: M2SL, FEDFUNDS, T10Y2Y from the Board of Governors
of the Federal Reserve System, and CBBTCUSD from Coinbase, all retrieved from
FRED, Federal Reserve Bank of St. Louis.
