# STR-Q-liquidity-sweep: Hostile Fill Variant Specs

**Date:** 2026-09-13
**Reference:** `scripts/paper_trading/hostile_fills_strq.py` (FROZEN baseline)
**Current baseline:** paper +1,305R / 52% WR → hostile -104R / 42% WR

All variants defined as diffs against the frozen baseline. Each expects to be
implemented as a separate `check_exit_hostile_vN()` function in a new script
(e.g., `hostile_fills_strq_variants.py`) that imports the frozen helpers
(`_apply_taker_fee`, `_worst_print`, `_trades_through`, `_bar_touches`,
`_compute_r`, `_load_bars`, `_find_signal_bar`) and varies only the named
modules below. Entry logic (`check_entry_hostile`) is shared across all
variants except Variant 2.

---

## Variant 1: Tight Stop (0.5× Risk Multiplier)

### What changes vs baseline

The stop distance from entry is halved. Instead of using the raw `stop_price`
from the trade record, the hostile model tightens it to midpoint between
entry and the original stop:

```
tight_stop = entry_price + 0.5 × (stop_price - entry_price)   # long
tight_stop = entry_price - 0.5 × (entry_price - stop_price)   # short
```

The 0.5 multiplier is the configuration knob; 0.33 and 0.67 are obvious
alternatives. The target price is unchanged. All other rules (worst-print
stop fill, limit target, time stop at 75 min, taker fee) stay identical.

### Expected impact on hostile R

| Mechanism | Direction | Magnitude |
|-----------|-----------|-----------|
| Stop triggered earlier on adverse moves | ↓ R per losing trade | Stop loss is ~50% smaller in price terms → losses shrink proportionally |
| Stop triggered on noise that would have recovered | ↓ WR | Tighter stops get hunted by intra-bar wicks; more trades stop out before reaching target |
| Risk denominator (used in R calculation) shrinks | Mixed | R-multiple = P&L / risk. Same dollar loss = larger negative R. But dollar loss is also smaller. Net: R per losing trade stays similar magnitude, win rate drops |

Net expectation: **hostile R becomes less negative** because the absolute
dollar losses shrink, but win rate will also drop. The trade-off is between
fewer catastrophic -2R stops vs more frequent -0.5R noise stops. In a
hostile-fill environment where stops fill at worst print (slippage), the
tight stop may paradoxically *increase* slippage impact because worst-print
fills are a larger fraction of a smaller stop distance.

Best case: hostile R moves from -104R toward -50R to -70R range.
Worst case: noise stops dominate, hostile R worsens to -150R+.

### Implementation notes

- **Where:** `check_exit_hostile()` — intercept `stop_price` before the bar
  scan loop.
- **New config:** `STOP_MULTIPLIER = 0.5` at top of variant file.
- **Code change:** One line before the `for _, row in bars.iterrows()` loop:
  ```python
  stop_price = entry_price + STOP_MULTIPLIER * (stop_price - entry_price)
  ```
- **No change to:** entry logic, target logic, time stop, fee application,
  R computation (risk denominator stays at *original* paper stop so R is
  comparable across variants — this is already how `_compute_r` works,
  using `paper_entry` and `paper_stop`).
- **Test surface:** Only stop-hit trades change. Verify that target-hit and
  time-stop trades produce identical R to baseline.

---

## Variant 2: True Limit Entry (Entry at Signal Price, Not t+1 Open)

### What changes vs baseline

Baseline entry fills at the *open* of the first bar that trades through the
entry level (`row["open"]` in `check_entry_hostile` line 186). This means
entry price can be substantially worse than the signal price when the bar
gaps through the level.

Variant 2 changes entry to fill at the **signal's entry price** (the price
the strategy intended), but *only* if a bar's range fully spans it (bar
trades through using `_trades_through`). This is a true limit order: you get
the exact price you asked for, or no fill at all.

Concretely, line 186 changes from:
```python
fill_price = float(row["open"])
```
to:
```python
fill_price = entry_price  # use the signal's intended price, not bar open
```

The taker fee is still applied on top (the limit order pays taker fee since
it removes liquidity from the book in the hostile model — the fill happens
when the market sweeps through the resting limit order).

### Expected impact on hostile R

| Mechanism | Direction | Magnitude |
|-----------|-----------|-----------|
| Entry price never worse than signal | ↑ R per trade | Eliminates entry slippage entirely — every fill is at the exact intended price |
| Fewer fills overall | ↓ trade count | A bar that gaps through the level but opens beyond it no longer fills at a worse price; it simply doesn't fill. Fewer entries → total R denominator shrinks |
| No "bad entry" trades | ↑ WR | Trades that would have entered at a poor price and immediately stopped out are now filtered out |

Net expectation: **hostile R improves significantly** because the single
largest source of hostile degradation — entry slippage — is eliminated.
Estimate: hostile R moves from -104R toward -20R to +50R range. The win
rate should improve because bad-entry trades are filtered. The trade count
drops, so total R sum may not reach paper's +1,305R, but R-per-trade
should converge toward paper.

### Implementation notes

- **Where:** `check_entry_hostile()` — line 186.
- **New config:** `ENTRY_MODE = "limit"` (baseline is effectively `"market"`).
- **Code change:** Replace `fill_price = float(row["open"])` with
  `fill_price = entry_price`. Rest of the function unchanged.
- **Critical:** Entry fills become rarer because bars that gap through the
  level without opening near it will no longer fill. The "no fill" skip
  rate will increase. This is measurable and intentional.
- **Exit logic:** No changes. `entry_bar_idx` is still the bar where the
  fill occurred.
- **R computation:** No changes (already uses `paper_entry` for risk
  denominator).
- **Test surface:** Compare skip rate (stage="skip" records) between
  baseline and Variant 2. Expect 10-30% more skips.

---

## Variant 3: Short Time Stop (30-Minute / 6-Bar Cap)

### What changes vs baseline

`MAX_BARS_HELD` drops from 15 (75 minutes) to 6 (30 minutes). All other
exit rules are unchanged. Time stop still fills at worst print + taker fee.

### Expected impact on hostile R

| Mechanism | Direction | Magnitude |
|-----------|-----------|-----------|
| Cuts tail risk on trades that drift sideways | ↑ R | Trades that neither hit stop nor target get closed sooner, reducing exposure to adverse drift |
| Fewer trades reach target | ↓ WR | Target needs time to be reached; halving the time window means more trades exit via time stop at a loss instead of reaching target |
| Time stops are always at worst print | ↓ R per time-stop trade | Time-stop exits pay slippage + taker fee, which is worse than a target fill |

Net expectation: **ambiguous — depends on STR-Q's time-to-target
distribution.** If STR-Q winners typically reach target within 6 bars,
Variant 3 is strictly better (cuts tail risk without sacrificing winners).
If winners typically take 10-12 bars, Variant 3 will destroy win rate.

From the baseline hostile report, the distribution of `hostile_bars_held`
for target-hit trades is the key diagnostic. Without that data, estimate:

- If median bars-to-target < 6: hostile R improves to -30R to +20R.
- If median bars-to-target > 6: hostile R worsens to -150R to -200R
  (winners become time-stop losers).

### Implementation notes

- **Where:** `check_exit_hostile()` — the `MAX_BARS_HELD` constant and the
  time-stop branch (line 258).
- **New config:** `MAX_BARS_HELD = 6` (baseline = 15).
- **Code change:** One constant. No logic changes.
- **Diagnostic prerequisite:** Before implementing, query
  `hostile_fill_report_strq.jsonl` for the distribution of `hostile_bars_held`
  grouped by `hostile_exit_reason == "target"`. If 80%+ of targets hit
  within 6 bars, this variant has high upside and low risk.
- **Test surface:** Compare `hostile_exit_reason` distribution. Expect
  time-stop share to rise from baseline X% to Y%. Compare hostile R on
  the same set of trades that *did* fill under both models.

---

## Variant 4: Crypto-Only + Fee Asymmetry (Filter + 5 bps Taker)

### What changes vs baseline

This is a compound variant with two independent levers:

**4a. Asset filter (crypto-only):** Process only trades where
`asset_class == "crypto"`. This mirrors the existing `--crypto-only` CLI
flag but bakes it into the variant as a permanent filter. Rationale: crypto
markets have 24/7 5m bar data; stocks may have gaps, thinner intraday data,
or different microstructure that degrades fill quality. Running crypto-only
tests whether the hostile degradation is asset-class-specific.

**4b. Reduced taker fee (5 bps per side):** `TAKER_FEE_BPS` drops from
10 to 5. This reflects the reality that high-volume traders and certain
venue tiers (Binance VIP, Coinbase Advanced) pay 5 bps or less. The 10 bps
baseline is conservative; 5 bps tests whether fee drag alone explains the
hostile R gap.

These can be tested independently (4a-only, 4b-only) or combined, but the
spec groups them as one variant file with both knobs togglable.

### Expected impact on hostile R

**4a (crypto-only):**

| Mechanism | Direction | Magnitude |
|-----------|-----------|-----------|
| Eliminates stocks with potentially worse 5m data | ↑ R | Stock bar data may have gaps, wider spreads, or fewer liquidity sweeps |
| Smaller universe → fewer trades | Neutral | Total R sum shrinks but R-per-trade should improve |

**4b (5 bps taker):**

| Mechanism | Direction | Magnitude |
|-----------|-----------|-----------|
| Round-trip cost drops from 20 bps → 10 bps | ↑ R | Saves 10 bps per closed trade. With average trade P&L of ~0.5R and R typically 1-2% of price, this is ~0.05-0.10R per trade |
| Cumulative effect over 100+ trades | Meaningful | 100 trades × 0.07R average = ~7R improvement |

Net expectation (combined): **hostile R improves modestly.** The fee
reduction alone contributes ~5-10R per 100 closed trades. The crypto-only
filter may improve R-per-trade but won't close the -104R gap alone.

Estimate: hostile R moves from -104R toward -70R to -85R (crypto-only),
and toward -90R to -97R (5 bps only). Combined: -55R to -80R.

### Implementation notes

- **Where:** `run()` function — asset class filter, and `TAKER_FEE_BPS`
  constant.
- **New config:**
  ```python
  TAKER_FEE_BPS = 5               # baseline: 10
  ASSET_CLASS_FILTER = "crypto"   # baseline: None (all)
  ```
- **Code change (4a):** In the trade loop, add:
  ```python
  if ASSET_CLASS_FILTER and trade.get("asset_class") != ASSET_CLASS_FILTER:
      continue
  ```
- **Code change (4b):** Change the constant. No logic changes — `_apply_taker_fee`
  reads `TAKER_FEE_BPS` directly.
- **Test surface:** Run baseline with `--crypto-only` and compare to
  full-universe baseline to isolate 4a. Then run Variant 4 with 5 bps to
  isolate 4b. The two effects are additive and independently measurable.

---

## Variant Comparison Matrix

| Variant | Changes | Expected hostile R delta | Risk to WR | Implementation effort |
|---------|---------|--------------------------|------------|----------------------|
| V1: Tight stop | Stop = entry + 0.5×(orig_stop − entry) | -104R → -50R to -150R | ↓ WR (more noise stops) | 1 line |
| V2: Limit entry | Fill at signal price, not bar open | -104R → -20R to +50R | ↑ WR (filters bad entries) | 1 line |
| V3: 30min stop | MAX_BARS_HELD = 6 | -104R → -30R to -200R | Data-dependent | 1 constant |
| V4a: Crypto-only | asset_class == "crypto" | -104R → -70R to -85R | Neutral | 3 lines |
| V4b: 5 bps fee | TAKER_FEE_BPS = 5 | -104R → -90R to -97R | Neutral | 1 constant |

## Recommended Testing Order

1. **Variant 2 first** — highest expected upside, lowest downside risk,
   only changes entry behavior.
2. **Variant 4** — safe, incremental, independently measurable levers.
3. **Variant 1** — requires tuning the multiplier; 0.5 is a starting point.
4. **Variant 3** — requires diagnostic data first (bars-to-target
   distribution); highest variance in outcome.

## Shared Infrastructure Note

All variants share entry logic (except V2) and R computation. They can
coexist in one script with a `--variant` flag:
```
python3 hostile_fills_strq_variants.py --variant tight-stop
python3 hostile_fills_strq_variants.py --variant limit-entry
python3 hostile_fills_strq_variants.py --variant short-time
python3 hostile_fills_strq_variants.py --variant crypto-5bps
```

Each variant writes to its own report file (e.g.,
`hostile_fill_report_strq_v1_tight_stop.jsonl`) so results are
independently comparable and the baseline report is never overwritten.