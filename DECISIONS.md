# DECISIONS — Why This Study Holds Up

An executive defense of the choices behind this data product, in plain business terms. It explains *why* I built it this way and *where a careful reader should stay skeptical* — it does not repeat the mechanics (see `docs/cleaning_log.md`, `docs/data_dictionary.md`, and `sql/verification.sql` for the evidence and column-level detail).

**The question:** Does system-wide liquidity — the money supply, policy interest rates, and the shape of the yield curve — drive the interest earnings of US banks, with bitcoin acting as a *barometer* of that liquidity rather than a cause of bank revenue?

---

## 1. Motivation

I chose this topic because, in the emerging markets I know best, volatility in local currencies is a constant — and digital assets have become a growing instrument for transacting and doing business there. At the same time, US monetary policy and gold have re-entered that conversation as live topics. This assignment gave me the opening to work with open, public data on both and to test them against **Net Interest Income (NII)** — a core bank-revenue line that, in my reading, moves with the flow of money and system liquidity.

*A caveat on where I stand: I come to this as an enthusiast of these topics, not a finance professional. My conclusions should be read as an analyst's exploration, not an expert's verdict.*

## 2. Guardrails — the anchor papers

Two papers keep this study honest: one tells me what to expect, the other tells me how not to fool myself.

- **Borio, Gambacorta & Hofmann (2017), *The influence of monetary policy on bank profitability*.** A panel of 109 large international banks across 14 advanced economies, 1995–2012. Their core finding: both the *level* of short-term rates and the *slope* of the yield curve have a positive effect on bank profitability, operating primarily through net interest income. Note that **M2 is not one of their variables** — bringing in the money supply is my own extension, and I flag it as such.
- **Granger & Newbold (1974), *Spurious regressions in econometrics*.** A methodological warning shown by simulation: regressing one independent random walk on another unrelated one routinely produces "significant" results — high R², large t-statistics — that are entirely spurious. This is exactly why I model in changes, not levels (§7).

A note on language: calling bitcoin a *barometer* is a claim about **co-movement, not causation**. My intent with this dataset is to watch how the series behave — to put the NII, bitcoin, and M2 curves side by side and read what the data shows — not to assert that one drives another.

## 3. Why this data

I wanted the cleanest available reading of two things: **what banks actually earn from lending and borrowing**, and **how much money is sloshing through the system**.

- **US public banks via SEC EDGAR.** Public banks file audited quarterly financials with the SEC in a machine-readable form (XBRL). This is primary-source, regulator-filed data — not a vendor's estimate — and it is free, reproducible, and independently checkable against each bank's own 10-Q/10-K. That auditability is the whole point.
- **FRED for liquidity.** The Federal Reserve's data service publishes the money-supply, policy-rate, and yield-curve series that define "system liquidity." It is the authoritative, free, revision-tracked source for exactly the macro variables my question is about.
- **Bitcoin as a barometer.** Bitcoin has no earnings and pays no interest, so it cannot *cause* bank revenue — but its price is widely read as a live gauge of risk appetite and easy money. That makes it a useful *thermometer* for liquidity, which is precisely how I use it (never as a driver).

I deliberately chose sources that a reviewer can pull themselves and reconcile line-by-line. Nothing here depends on a paid feed or a black box.

## 4. Why this question

Interest income is the revenue line **most directly exposed to rates and liquidity**, so if liquidity drives bank fortunes anywhere, it shows up here first and most cleanly. I identify the effect across a **cross-section of ~171 banks each quarter** rather than from a single national aggregate — many banks reacting to the same macro backdrop is far stronger evidence than one economy-wide number. Bitcoin enters only as a barometer: the interesting scientific claim is that it *co-moves* with liquidity, not that it moves bank revenue.

## 5. What the headline metric really measures — and where it falls short

The headline is **Net Interest Income (NII)**: what a bank earns on its assets minus what it pays on its funding, per quarter. I take it **straight from the dedicated regulator-defined tag** (`InterestIncomeExpenseNet`), which every bank in scope reports — so NII itself is a reported number, not something I reverse-engineered. That is its strength. The honest caveats:

- **It is a single net line.** NII nets earnings against funding cost into one figure. Two banks with identical NII can have very different underlying spreads; the net tag hides that.
- **My margin ratio is approximate.** `nim_approx` divides NII by **total** assets, because average **earning** assets (the textbook denominator) are not filed consistently. It is a size-normalized proxy, not a true net interest margin, and it is not annualized.
- **The loan figure mixes two bases.** There is no universal "total loans" tag. Most banks report loans **net of loss reserves**; six (including JPMorgan) report on a **gross** CECL basis. So `total_loans` — and any ratio built on it — is approximate and should not be read to the last dollar across banks.
- **Four banks are excluded.** HIFS, TOWN, OZK, and PFBC report to their banking regulator (FDIC/Fed), not the SEC, so no comparable XBRL exists. They are documented exclusions, not gaps I ignored — the working universe is **171 banks**, not 175.

### 5.1 Why gold was dropped

I intended gold as a second barometer alongside bitcoin. No free, reachable daily USD gold series survived, so after four dead ends I dropped it rather than force in a substitute (CLAUDE.md decision #18):

- **FRED discontinued the LBMA gold family** (`GOLDAMGBD228NLBM` and related) after ICE ended the license — the authoritative free source was gone.
- **stooq's CSV endpoint** serves a JavaScript bot-challenge, so the download never returns actual prices.
- **The Nasdaq Data Link API is Incapsula-WAF-blocked** from this build environment — the direct connection can't get through.
- **The free Quandl `LBMA/GOLD` dataset is retired** and now sits behind a paid subscription.

Because this project's whole premise is data a reviewer can pull and reconcile themselves, I dropped gold and said so here rather than substitute or invent a series. **Bitcoin (`CBBTCUSD`) stands as the sole liquidity barometer.** This is a source-availability limitation, honestly labeled — not a data error.

### 5.2 Strengthening the inference — M2 as a plotted barometer

Losing gold (§5.1) left me with one barometer. Rather than accept a thinner read, I bring **M2 forward as a plotted series** alongside NII and bitcoin. This is a deliberate improvement, not a patch: M2 is the money-supply variable at the center of my question, so surfacing it visually replaces the barometer I lost with a higher-quality one and strengthens the liquidity story rather than merely filling a hole.

I show it as **two panels, by design:**

- **Panel A — indexed levels (base quarter = 100).** System NII (summed across the 171 banks per quarter), M2, and bitcoin on one comparable scale. This is the naive view: after 2020 all three trend up together and *look* tightly linked.
- **Panel B — year-over-year % change** of the same three series. Stripping the common trend shows whether they actually move together or merely drifted up in parallel.

The point is the **contrast**. Panel A looks convincing; Panel B lets the de-trended data speak. That visually demonstrates the guard in §7 — co-movement in levels is the Granger–Newbold trap — instead of just asserting it. As a bonus, Panel B surfaces the late-2025 **BTC–M2 divergence** (M2 up, bitcoin down): direct visual support for "barometer, not predictor."

**Disclaimer — different scales, and how I handle them.** NII, M2, and bitcoin live on wildly different units (billions of dollars, tens of trillions, and a per-coin price). A raw shared-axis overlay would flatten two of the three lines into the floor and invite a false read, so I never plot them that way. Panel A **indexes every series to 100 at a common base quarter** (equivalently, z-scores them) so shape is comparable without implying the units are; Panel B works in **percentage change**, which is unit-free by construction. And I draw inference only from Panel B — the levels panel is descriptive context, never evidence.

## 6. Why the answer is trustworthy — and where it is not

**Why you can trust it:**

- **External reconciliation.** I tie my numbers back to JPMorgan's actual 10-Q/10-K filings. My derived quarterly NII **equals** JPMorgan's reported three-month figures, and its balance sheet matches to the dollar for FY2024. The macro series match FRED's published latest values.
- **Internal consistency.** Independently, `interest income − interest expense ≈ NII` holds for **99.46%** of testable rows. I do not bury the remaining 0.54% — it is a known effect of filers using slightly different income-tag bases, and it is labeled, not smoothed away.
- **Every check is reproducible.** All of the above lives in `sql/verification.sql` with its captured results committed, so a reviewer can confirm without re-running anything.

**Where you should stay skeptical:**

- **FY2025 figures are unverified.** The most recent quarters rely on the filed XBRL facts themselves; I have **not** independently re-confirmed the published FY2025 10-K. Those rows are explicitly labeled UNVERIFIED.
- **The macro story is low-N.** There are only ~48 quarters of history. Cross-bank breadth is large, but the *time-series* evidence on liquidity is thin — treat macro conclusions as suggestive, not settled.
- **Correlation is not causation.** I reserve causal language for the one channel with a clear mechanism — **interest rates → NII**. For bitcoin I claim **co-movement only**. It is a barometer of the same weather, not the cause of it.
- **The system-NII aggregate is thin-coverage before ~2018.** The system series is a *sum* of NII across banks, and panel coverage ramps over time — the early quarters run over as few as 16 banks in 2008, ramping to ~167 from 2020 on. So its early year-over-year swings are **composition artifacts** (banks entering the sum), not economics. Inference is reserved for the stable-coverage period, and the thin window is shaded in `analysis/liquidity_overlay.png`.

## 7. The guards against fooling myself

- **I model growth and changes, not raw levels.** Two trending series can look related by accident (the Granger–Newbold spurious-regression trap). Differencing to quarter-over-quarter and year-over-year changes removes that illusion.
- **Time-ordered train/test split, no look-ahead.** I train on the past and test on the future; the macro alignment uses only within-quarter information, so no future data leaks backward.
- **No imputation.** Missing values stay missing and flagged — I never fill a gap with a guess, and I never difference across a gap (those transforms are set to null and marked).

## 8. Reproducibility

- **`sql/verification.sql`** — every integrity, reconciliation, and coverage check, each with its committed result. A reviewer can re-run any block or simply read the captured output.
- **Committed cost and build config.** A hard **200 GB per-query cost cap** governs every query (documented in `CLAUDE.md`), the pipeline runs raw → clean → marts off immutable landed data, and every design decision is recorded in `CLAUDE.md` and `docs/cleaning_log.md`. Same inputs, same code, same numbers.

---

*Companion documents: `CLAUDE.md` (decision log) · `docs/cleaning_log.md` (every exclusion and derivation) · `docs/data_dictionary.md` (column-level spec) · `sql/verification.sql` (evidence).*
