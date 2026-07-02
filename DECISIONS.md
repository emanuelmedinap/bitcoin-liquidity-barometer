# DECISIONS — Why This Study Holds Up

An executive defense of the choices behind this data product, in plain business terms.
It explains *why* we built it this way and *where a careful reader should stay skeptical* —
it does not repeat the mechanics (see `docs/cleaning_log.md`, `docs/data_dictionary.md`,
and `sql/verification.sql` for the evidence and column-level detail).

**The question:** Does system-wide liquidity — the money supply, policy interest rates,
and the shape of the yield curve — drive the interest earnings of US banks, with gold and
bitcoin acting as *barometers* of that liquidity rather than causes of bank revenue?

---

## 1. Why this data

We wanted the cleanest available reading of two things: **what banks actually earn from
lending and borrowing**, and **how much money is sloshing through the system**.

- **US public banks via SEC EDGAR.** Public banks file audited quarterly financials with
  the SEC in a machine-readable form (XBRL). This is primary-source, regulator-filed data —
  not a vendor's estimate — and it is free, reproducible, and independently checkable against
  each bank's own 10-Q/10-K. That auditability is the whole point.
- **FRED for liquidity.** The Federal Reserve's data service publishes the money-supply,
  policy-rate, and yield-curve series that define "system liquidity." It is the authoritative,
  free, revision-tracked source for exactly the macro variables our question is about.
- **Bitcoin as a barometer.** Bitcoin has no earnings and pays no interest, so it cannot
  *cause* bank revenue — but its price is widely read as a live gauge of risk appetite and
  easy money. That makes it a useful *thermometer* for liquidity, which is precisely how we
  use it (never as a driver).

We deliberately chose sources that a reviewer can pull themselves and reconcile line-by-line.
Nothing here depends on a paid feed or a black box.

## 2. Why this question

Interest income is the revenue line **most directly exposed to rates and liquidity**, so if
liquidity drives bank fortunes anywhere, it shows up here first and most cleanly. We identify
the effect across a **cross-section of ~171 banks each quarter** rather than from a single
national aggregate — many banks reacting to the same macro backdrop is far stronger evidence
than one economy-wide number. Gold and bitcoin enter only as barometers: the interesting
scientific claim is that they *co-move* with liquidity, not that they move bank revenue.

## 3. What the headline metric really measures — and where it falls short

The headline is **Net Interest Income (NII)**: what a bank earns on its assets minus what it
pays on its funding, per quarter. We take it **straight from the dedicated regulator-defined
tag** (`InterestIncomeExpenseNet`), which every bank in scope reports — so NII itself is a
reported number, not something we reverse-engineered. That is its strength. The honest caveats:

- **It is a single net line.** NII nets earnings against funding cost into one figure. Two
  banks with identical NII can have very different underlying spreads; the net tag hides that.
- **Our margin ratio is approximate.** `nim_approx` divides NII by **total** assets, because
  average **earning** assets (the textbook denominator) are not filed consistently. It is a
  size-normalized proxy, not a true net interest margin, and it is not annualized.
- **The loan figure mixes two bases.** There is no universal "total loans" tag. Most banks
  report loans **net of loss reserves**; six (including JPMorgan) report on a **gross** CECL
  basis. So `total_loans` — and any ratio built on it — is approximate and should not be read
  to the last dollar across banks.
- **Four banks are excluded.** HIFS, TOWN, OZK, and PFBC report to their banking regulator
  (FDIC/Fed), not the SEC, so no comparable XBRL exists. They are documented exclusions, not
  gaps we ignored — the working universe is **171 banks**, not 175.
- **Gold was dropped.** We wanted gold as a second barometer, but no free, reachable daily
  USD gold series survived (the licensed feeds were discontinued or paywalled). Rather than
  substitute a lower-quality or invented series, we **dropped it and said so**. Bitcoin stands
  as the sole barometer. This is a source-availability limitation, honestly labeled — not a
  data error.

## 4. Why the answer is trustworthy — and where it is not

**Why you can trust it:**

- **External reconciliation.** We tie our numbers back to JPMorgan's actual 10-Q/10-K filings.
  Our derived quarterly NII **equals** JPMorgan's reported three-month figures, and its balance
  sheet matches to the dollar for FY2024. The macro series match FRED's published latest values.
- **Internal consistency.** Independently, `interest income − interest expense ≈ NII` holds for
  **99.46%** of testable rows. We do not bury the remaining 0.54% — it is a known effect of
  filers using slightly different income-tag bases, and it is labeled, not smoothed away.
- **Every check is reproducible.** All of the above lives in `sql/verification.sql` with its
  captured results committed, so a reviewer can confirm without re-running anything.

**Where you should stay skeptical:**

- **FY2025 figures are unverified.** The most recent quarters rely on the filed XBRL facts
  themselves; we have **not** independently re-confirmed the published FY2025 10-K. Those rows
  are explicitly labeled UNVERIFIED.
- **The macro story is low-N.** There are only ~48 quarters of history. Cross-bank breadth is
  large, but the *time-series* evidence on liquidity is thin — treat macro conclusions as
  suggestive, not settled.
- **Correlation is not causation.** We reserve causal language for the one channel with a clear
  mechanism — **interest rates → NII**. For gold and bitcoin we claim **co-movement only**.
  They are barometers of the same weather, not the cause of it.

## 5. The guards against fooling ourselves

- **We model growth and changes, not raw levels.** Two trending series can look related by
  accident (the Granger–Newbold spurious-regression trap). Differencing to quarter-over-quarter
  and year-over-year changes removes that illusion.
- **Time-ordered train/test split, no look-ahead.** We train on the past and test on the future;
  the macro alignment uses only within-quarter information, so no future data leaks backward.
- **No imputation.** Missing values stay missing and flagged — we never fill a gap with a guess,
  and we never difference across a gap (those transforms are set to null and marked).

## 6. Reproducibility

- **`sql/verification.sql`** — every integrity, reconciliation, and coverage check, each with
  its committed result. A reviewer can re-run any block or simply read the captured output.
- **Committed cost and build config.** A hard **200 GB per-query cost cap** governs every query
  (documented in `CLAUDE.md`), the pipeline runs raw → clean → marts off immutable landed data,
  and every design decision is recorded in `CLAUDE.md` and `docs/cleaning_log.md`. Same inputs,
  same code, same numbers.

---

*Companion documents: `CLAUDE.md` (decision log) · `docs/cleaning_log.md` (every exclusion and
derivation) · `docs/data_dictionary.md` (column-level spec) · `sql/verification.sql` (evidence).*
