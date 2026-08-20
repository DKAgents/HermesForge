---
status: backtest_failed
source: web
edge_type: macro_policy_equity_complacency_divergence
composite_score: 62.0
confidence: medium
regime_fit: ['complacent', 'risk_on', 'caution']
created: 20260820
processed: 20260820
topic: research
has_quotes: false
tags: [macro, regime, rate-hike, divergence, vix, external]
---
# Edge Candidate: Rate-Hike-Reversal Equity Complacency Divergence

## Pipeline Result: BACKTEST FAILED (2026-08-20)

**Scanner:** `scanner_rate_hike_complacency.py` (STR-RHC-RATE-HIKE-COMPLACENCY)
**Phase 1A Results:**
- Total signals: 0
- Mean R: 0.0 (no signals generated)
- Classification: ❌ KILL (no signals)

**Analysis:**
The 4-condition regime gate (VIX ≤ 16, SPY within 2% of 60-day high, 2yr yield
risen ≥15bps over 20 days, 2s10s flattened by ≥1bp over same window) never
triggered simultaneously over the 2019-2026 stock history. The conjunction
of all 4 conditions is too strict. The signal is directionally sound but the
implementation needs parameter relaxation:

1. The 2yr yield proxy (^IRX = 13-week T-bill) may not capture rate-hike
   expectations as well as a true 2yr Treasury (^FVX). IRX measures the
   very short end which moves with Fed funds, not 2yr hike expectations.
2. The 15bps threshold over 20 days may be too high for the IRX proxy
   (which typically trades in a narrow range around the Fed funds rate).
3. The 2s10s flattening requirement compounds the strictness — requiring
   both short-end rise AND curve flattening in the same 20-day window
   eliminates most historical periods.

**What would change my view:** Relaxing to 3-condition gate (VIX ≤ 18,
SPY near ATH, short-rate rising) without the 2s10s flattening requirement.
Alternatively, using ^FVX (5yr) or ^TYX (30yr) for a cleaner term-structure
signal. The macro divergence hypothesis is still valid; the implementation
gate needs recalibration.
# Edge Candidate: Rate-Hike-Reversal Equity Complacency Divergence

## Source
Web / macro research (Aug 2026) —
- **BofA & Deutsche Bank reversed to forecast 3 Fed rate hikes in 2026** (CNBC Jun 22 2026; CU Today Jun 22; Yahoo Finance Jun 23). Inflation described as "unambiguously worse"; Chair Warsh hawkish turn. Earlier 2026 cut calls fully unwound.
- **IBTimes (Aug 18 2026):** "VIX hit its lowest level of 2026 just as stocks continue near record highs... expectations for an immediate Federal Reserve rate hike." Explicit divergence framing.
- **Elliott Wave / Benzinga (Aug 18 2026):** VIX closed at 2026 low; 45-yr veteran Tony Battista flags low vol as a black-swan-hedge opportunity.
- **Goldman Sachs US Market Pulse (Aug 5 2026):** core inflation ~3% by Dec 2026; tariffs + energy + AI-measurement issues.
- **VIX term structure:** VIX 15.19, VIX3M 19.04, IVTS 0.798 — day 91 of contango (thetrading.tools). Deep complacency.
- **Equities:** SPX ~7,790 record highs; SPY/QQQ/IWM all above 20/50-day MAs (Aug 13 briefing).

## Signal
A **macro/sentiment divergence**: equity volatility and positioning are at 2026 extremes of complacency (VIX at yearly low, term structure in 90+ day contango, F&G 62 Greed, SPX at ATH) while the policy path has *reversed hawkish* (3 hikes now priced by two major banks, inflation "unambiguously worse"). Historically, the combination of (a) VIX ≤ 16, (b) rising rate-hike-implied probability, and (c) equities within 1% of ATH marks a fragile risk-on regime where the asymmetry of a policy-driven repricing is skewed to the downside.

This is **not** the VIX-contango-persistence edge (that candidate trades contango as a breakout persistence signal). This edge trades the *cross-variable divergence* between the volatility complex and the policy-rate path — a regime-level tail-hedge / defensive-tilt trigger.

## Hypothesis
When the rate-hike-implied path steepens (proxy: 2yr Treasury yield rising + 2s10s curve shifting) while the VIX complex is simultaneously at multi-month lows and equities are at highs, the forward 1-3 month equity risk premium is negatively skewed. A defensive rotation (long low-beta/defensive sectors, short high-beta/momentum; or a vol-long / tail-hedge overlay) earns a positive expected return in this state because the market has under-priced the policy-tightening path.

## Entry Rules
- **Regime trigger (daily check):** FIRE when ALL hold:
  1. VIX ≤ 16 (complacency floor)
  2. SPX within 2% of its 60-day high (near-ATH)
  3. 2yr Treasury yield (^IRX or 2yr proxy from yfinance) has risen ≥ 15 bps over the prior 20 trading days (hike-odds steepening)
  4. 2s10s spread has flattened or inverted further over the same 20-day window
- **Defensive rotation (long/short equity):** Long XLP/XLV/XLU (consumer staples, healthcare, utilities), short XLK/XLY (tech, discretionary) — equal-dollar, beta-neutral. Rebalance weekly while trigger holds.
- **Tail-hedge variant:** Long VIX call spread or long far-OTM SPY puts funded by short near-ATM VIX futures (collared), sized to ≤0.5% capital risk per the 1% rule.

## Exit Rules
- Exit the defensive rotation when VIX spikes ≥ 22 OR the 2yr yield rolls over ≥ 10 bps from its trigger-window peak (policy path softens) OR SPX breaks ≥ 5% below its trigger-date close.
- Tail-hedge: time-stop 30 calendar days; roll if trigger still valid.

## Score Breakdown
- Composite: 62.0
- Signal Strength: 13 (explicit, current, multi-source divergence; directly observable in price/yield data)
- Confidence: medium (15) — strong consensus among major banks + contemporaneous VIX/ATH data; medium because "hike-priced-but-delayed" regimes can persist for weeks before repricing
- Data Quality: 15 (VIX, sector ETFs, Treasury yields all in yfinance daily; no external feed needed)
- Actionable: 12 (defensive rotation is a clean long/short; tail-hedge variant needs options which paper-trading can simulate)
- Precedent: 7 (some_evidence — 2018 Q4 and 2022 Q1 both saw policy-tightening-into-complacency repricings; not a deeply replicated academic anomaly)

## Regime Fit
['complacent', 'risk_on', 'caution'] — fires specifically in the complacent/risk-on state with a hawkish policy overlay. Suppress entirely in 'risk_off' (vol already elevated, edge consumed). In 'neutral' without the yield-trigger it does not fire.

## Testability
✅ **Fully testable with free data.** All inputs (VIX, SPY, sector ETFs, ^IRX/^FVX/^TNX Treasury yields) are daily yfinance series. The 2yr-hike-odds proxy is the one approximation — true hike-implied probabilities (Polymarket/Fed funds futures) aren't free, but the 2yr yield + 2s10s slope is the standard free proxy and moves with hike expectations. Backtest: identify all historical trigger windows over the 1806-day stock history, measure forward 5/20/60-day returns of the defensive rotation vs. SPY.

**Overlap with engine:** Engine VIX-contango candidate trades contango persistence as a breakout signal; this trades the *equity-VIX vs. policy-rate* divergence — different variables, different direction (defensive vs. breakout). No existing candidate covers the macro policy divergence. Genuinely new.

## Recommended Pipeline Action
**PROMISING →** Build scanner `scanner_rate_hike_complacency.py` that detects the 4-condition trigger on the daily yfinance series and backtests the defensive sector rotation (long XLP/XLV/XLU, short XLK/XLY) over forward 5/20/60-day windows, plus the standalone VIX-call-spread variant. Priority: medium-high — the trigger may be active *right now* (VIX at 2026 low, hikes priced, SPX at ATH), so a timely backtest could surface a live-deployable defensive tilt.
