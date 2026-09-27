# LU-04: Jev — Call Map and Authority Boundary

**Status**: note-only (no code edits)
**Date**: 2026-09-25
**Campaign**: 2026-09-aegis-rebuild

---

## Jev Call Map

Every Jev API call in the codebase, what file it lives in, and what
consumes the answer:

### 1. `jev_client.py` — no calls

Thin wrapper: `JevClient.ask()` / `.noul()` / `.score()` / `.choice()`.
Imported by all consumers below. Reads `TYPESAFE_API_KEY` from env or
`~/.hermes/.env`. Posts to `api.typesafe.ai/v1/systemone`. Does not
initiate any calls on its own.

### 2. `jev_prefilter.py` — 3 noul calls per signal

**Called by**: `capture_signals.py` (lines 399, 559) and
`capture_sweep_signals.py` (line 392).

| # | Method | Question | Consumer action |
|---|---|---|---|
| Q1 | `jev.noul` | Signal validity — genuine setup? | Composite scoring |
| Q2 | `jev.noul` | Market alignment — regime favorable? | Composite scoring |
| Q3 | `jev.noul` | Risk/reward — R:R reasonable? | Composite scoring |

**Composite**: `min(Q1, Q2, Q3)` — weakest-link rule.
- `≥ 0.75` → tier `"approved"` → paper-trade, eligible for live (user must confirm)
- `0.30–0.74` → tier `"marginal"` → paper-trade ONLY, never live
- `< 0.30` → tier `"rejected"` → skip entirely

The consumer (`capture_signals.py` / `capture_sweep_signals.py`) uses the
tier to set `jev_action = "skip"` or `"allow"`. On `"allow"`, the trade
goes to `trade_log.open_trade()` (paper trading). On `"skip"`, the trade
is silently dropped from the pipeline.

**Supplemental data passed to Jev**: `get_performance_context(strategy_id)`
reads trades.csv for 30d + all-time stats (win rate, avg R, trade count,
trend, max DD). `ml_pred` from `MLPredictor.predict_signal()` gives
expected R and win probability. Both are read-only — they inform Jev's
noul calls but do not independently make API calls.

### 3. `jev_regime.py` — 3 calls per classification (2 score, 1 noul)

**Imported by**: `capture_signals.py` line 47 (`from jev_regime import classify_regime as _jev_regime`).

**Called by**: nowhere. `_jev_regime` is imported but never invoked in
the capture pipeline. The existing regime classifier used at capture time
is `crypto_regime.py` (heuristic, not Jev-powered).

If it were called, it would make:

| # | Method | Question |
|---|---|---|
| Q4 | `jev.score` | Regime classification (9-way: bull/bear/flat × high/normal/low vol) |
| Q5 | `jev.score` | Trend classification (5-way: strong/weak uptrend/downtrend, ranging) |
| Q6 | `jev.noul` | Risk environment (risk-on vs risk-off) |

**Consumer**: the returned `RegimeResult` would be passed as `market_context`
to `prefilter_signal()` in `jev_prefilter.py`, enriching Q2 (market alignment).

### 4. `jev_ml_predictor.py` — no Jev API calls

MLPredictor trains a local logistic regression model on historical trades
from `scripts/paper_trading/jev_features.csv`. It reads features, trains
scikit-learn, and caches the model to `.jev_ml_model.pkl`. No API calls.
Its output (`win_probability`, `expected_r`, `top_features`) is passed as
`state["ml_prediction"]` to Jev's noul questions in `jev_prefilter.py`.

### 5. `jev_performance_tracker.py` — no Jev API calls

Reads `trades.csv`, computes per-strategy stats (30d and all-time), returns
compact context dict. No API calls. Feeds `jev_prefilter.py` via
`get_performance_context()`.

---

## Total Call Count Per Signal

For **daily signals** (capture_signals.py):
- 3 noul calls via `prefilter_signal()` per signal that passes scanner gates
- Jev is WAIVED when `--jev-off` flag is set or `--jev-shadow` mode logs but doesn't block

For **intraday sweeps** (capture_sweep_signals.py):
- Same 3 noul calls per sweep signal
- Same `--jev-off` / `--jev-shadow` flags

Regime classification (jev_regime.py) is **imported but not called** — zero
additional API cost at runtime.

---

## Authority Boundary

### Jev MAY:
- Classify signals into `approved` / `marginal` / `rejected` tiers
- Return a `PrefilterResult` with confidence and reasons
- Read trades.csv (via `jev_performance_tracker`) to inform classification
- Classify market regime (if `jev_regime` is ever wired in)

### Jev MUST NOT:
- Place orders — no broker API access, no exchange credentials, no `curl` to
  Hyperliquid/Alpaca/OKX endpoints
- Write `trades.csv` — only `trade_log.py` writes to the trade ledger; Jev's
  callers use `trade_log.open_trade()` AFTER Jev approves
- Post to Discord — Jev has no webhook or bot-token access
- Modify position sizes, account limits, allowlists, kill switches, or session
  hours — these are in `position_manager.py` and `live_performance_tracker.py`

### A Jev "approved" or "marginal" is NOT a ship signal

The capture pipelines treat Jev's output as a GATE, not a COMMAND. A Jev
`"approved"` tier means the signal passes the gate and enters PAPER trading.
It never triggers a live order. The comment in `jev_prefilter.py` lines 40-44
shows the design intent:

```python
# ---- docstring ----
# if result.tier == "approved":
#     open_live_trade(signal)
# elif result.tier == "marginal":
#     open_paper_trade(signal)  # never live
```

But `open_live_trade` does not exist. The actual code paths in both capture
files go through `trade_log.open_trade()` only — which writes to the paper
journal. There is no live execution path from Jev's output.

### Fail-closed: a dead Jev blocks signals, not opens them

If `JevClient()` init fails (bad key, network error), `prefilter_signal()`
returns `tier="rejected", approved=False`. The consumer skips the signal.
A dead Jev cannot silently approve trades.

---

## What Jev is NOT

Jev is not T1 (guardrails/risk), T2 (code generation), or T3 (execution). It
is a classification sidecar. It has exactly one API endpoint
(`typesafe.ai/v1/systemone`) and returns structured answers. It has no access
to the agent's runtime, filesystem writes, or platform connectors.

---

## Invariants

- **Do NOT edit** any Jev file or capture file.
- **Do NOT train** `jev_ml_predictor` in this story.
- **Do NOT wire** `jev_regime.py` into the capture pipeline.
- **Do NOT create** an order path or live execution path from Jev output.
- **Do NOT read** `.env` or secrets files.
- **Do NOT post. Do NOT trade.**

---

## Verified

```bash
$ grep -n -E 'jev|order|trades\.csv' \
    scripts/paper_trading/capture_signals.py \
    scripts/paper_trading/capture_sweep_signals.py | head -60

capture_signals.py:27: # They must NOT write to the operational paper journal or trades.csv.
capture_signals.py:46:     from jev_prefilter import prefilter_signal as _jev_prefilter
capture_signals.py:47:     from jev_regime import classify_regime as _jev_regime
capture_signals.py:126: # These must NOT write to the operational paper journal or trades.csv
capture_signals.py:267:                        jev_off: bool = False, jev_shadow: bool = False)
capture_signals.py:396-416:  Jev tier → jev_action = "skip" or "allow" → continue or trade_log.open_trade()
capture_signals.py:556-576:  (duplicate pattern in second scan loop)
capture_signals.py:590:          jev_off: bool = False, jev_shadow: bool = False)
capture_signals.py:648:     ap.add_argument("--dry-run", ...)
capture_signals.py:653-655:  --jev-off / --jev-shadow flags

capture_sweep_signals.py:50:     from jev_prefilter import prefilter_signal as _jev_prefilter
capture_sweep_signals.py:268:                     jev_off: bool = False, jev_shadow: bool = False)
capture_sweep_signals.py:389-412:  Jev tier → jev_action = "skip" or "allow" → continue or trade_log.open_trade()
capture_sweep_signals.py:754:     ap.add_argument("--dry-run", ...)
capture_sweep_signals.py:758-760:  --jev-off / --jev-shadow flags
```

No Jev call path leads to an exchange order, a `trades.csv` write, or a
Discord post. All Jev output is consumed as a gate boolean by the capture
pipeline, before `trade_log.open_trade()` is called.

---

## Key Takeaway

Jev is a classification sidecar with exactly one job: return
`approved`/`marginal`/`rejected` for each signal. It makes 3 noul API calls
per signal. The capture pipelines gate on the result, but only to allow or
block paper-trade entry. No Jev output triggers a live order, writes to
trades.csv, or posts to any channel.