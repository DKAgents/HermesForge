---
topic: strategies
confidence: high
has_quotes: false
tags: []
source: HermesForge Strategies
created: 2026-08-16
---
# STR-Q MAE/MFE Analysis (Deep Backtest, Phase 1A)

**Source:** `scripts/validation/results/STR-Q-stocks-deep-phase1a.csv`  
**Total trades:** 826  
**Generated:** 2026-08-15

---

## Methodology Note

This backtest CSV records the **final outcome** of each trade (stop / target / time exit) 
rather than bar-by-bar intraday MAE/MFE. Therefore this analysis is a **simplified excursion study**:

- **MAE proxy:** `-1R` if `exit_type=stop` (price reached the stop), `0R` if `exit_type=time` (no stop touched), and a small positive value if `exit_type=target`.
- **MFE proxy:** `+3R` if `exit_type=target` (target reached). For `time` exits the trade closed at `exit_price` so only the final R is known, not the intraday peak favorable excursion.

The key diagnostic this report targets is the **stop-hit rate** — the proportion of trades that 
reached their stop before their target or the time limit. This is the cleanest signal of whether 
STR-Q's sweep-entry timing is actually improving entry quality over the original daily-bar strategies.

---

## 1. Exit Type Distribution

| Exit Type | Count | % of Trades |
|-----------|-------|-------------|
| stop | 396 | 47.9% |
| target | 254 | 30.8% |
| time | 176 | 21.3% |
| **Total** | **826** | **100.0%** |

**Stop-hit rate: 47.9%**  
Target-hit rate: 30.8%  
Time-exit rate: 21.3%

---

## 2. Comparison vs Original Daily-Bar Strategies (73.7% stop-hit)

| Strategy | Stop-hit rate | Target-hit rate | Time-exit rate |
|----------|--------------|----------------|----------------|
| Original daily-bar (baseline) | 73.7% | ~? | ~? |
| **STR-Q (deep phase 1A)** | **47.9%** | **30.8%** | **21.3%** |

**Delta: 25.8 pts lower (better) than the 73.7% original baseline.**

The sweep-entry timing in STR-Q reduces the stop-hit rate by **25.8 percentage points**, 
indicating the entry timing is filtering out a meaningful share of the trades that would have 
stopped out under the original daily-bar strategy. The remainder that *do* stop out represent 
genuine sweep failures rather than poor-timing noise.

---

## 3. Average R by Exit Type

| Exit Type | Avg R | Count |
|-----------|-------|-------|
| stop | -1.000 | 396 |
| target | +3.000 | 254 |
| time | +0.678 | 176 |

**Overall avg R per trade: +0.5875**  
**Expectancy (weighted): +0.5875R per trade**  
**Win rate (R>0): 46.2%** (382/826)

Observations:

- Stop exits are realized at exactly -1R (full stop), as expected.
- Target exits are realized at exactly +3R (full target), as expected.

---

## 4. Stop-Hit Rate by Level Type

| Level Type | Total | Stop | Target | Time | Stop % | Avg R |
|------------|-------|------|--------|------|--------|-------|
| equal_lows | 107 | 63 | 25 | 19 | 58.9% | +0.224 |
| swing_high | 224 | 117 | 70 | 37 | 52.2% | +0.530 |
| swing_low | 218 | 110 | 68 | 40 | 50.5% | +0.515 |
| equal_highs | 124 | 58 | 36 | 30 | 46.8% | +0.614 |
| round_number | 86 | 29 | 30 | 27 | 33.7% | +0.907 |
| PDL | 27 | 8 | 10 | 9 | 29.6% | +1.176 |
| PDH | 40 | 11 | 15 | 14 | 27.5% | +1.110 |

**Worst stop-hit rates:**
- `equal_lows`: 58.9% stop-hit (63/107), avg R +0.224
- `swing_high`: 52.2% stop-hit (117/224), avg R +0.530
- `swing_low`: 50.5% stop-hit (110/218), avg R +0.515

**Best stop-hit rates:**
- `PDH`: 27.5% stop-hit (11/40), avg R +1.110
- `PDL`: 29.6% stop-hit (8/27), avg R +1.176
- `round_number`: 33.7% stop-hit (29/86), avg R +0.907

---

## 5. Stop-Hit Rate by Direction

| Direction | Total | Stop | Target | Time | Stop % |
|-----------|-------|------|--------|------|--------|
| bearish | 401 | 182 | 133 | 86 | 45.4% |
| bullish | 425 | 214 | 121 | 90 | 50.4% |

---

## 6. Stop-Hit Rate by Quality Score Bucket

| Quality Bucket | Total | Stop-hit % |
|----------------|-------|------------|
| low (<=40) | 8 | 0.0% |
| mid (41-60) | 418 | 48.3% |
| high (>60) | 400 | 48.5% |

---

## Key Findings

1. **Stop-hit rate is 47.9%** across 826 STR-Q trades, vs 73.7% for the original daily-bar baseline — a 25.8-pt lower difference.
2. **Target-hit rate 30.8%**, **time-exit rate 21.3%**.
3. **Expectancy: +0.5875R/trade**, win rate 46.2%.
4. **Worst level type:** `equal_lows` at 58.9% stop-hit — candidate for filtering or criteria tightening.

---
*End of report.*
