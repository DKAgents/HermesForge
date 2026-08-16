# DESIGN: US-116 — Real regime_filter Module

**Architect:** HermesForge Architect Agent  
**Date:** 2026-08-16  
**Status:** DESIGN ONLY (no implementation)  
**Ticket:** US-116

---

## 0. Problem Summary

`scripts/data/regime_filter.py` is a 74-line hardcoded JSON dump — no functions, no imports, no module-level API. Three callers try `from regime_filter import get_regime, tag_signal` and all fail with ImportError. This silently disables regime-aware strategy selection: every signal scan runs ALL strategies at default risk regardless of market conditions.

The fix is to replace the stub with a real module that computes regime from cached data and exposes `get_regime()` + `tag_signal()`.

---

## 1. Module API

### File location
`~/HermesForge/scripts/data/regime_filter.py` (same path — no caller path changes needed)

### Function signatures

```python
def get_regime(as_of: str | None = None, force_refresh: bool = False) -> dict:
    """
    Determine the current market regime from cached parquet data.

    Parameters:
        as_of: ISO date string (e.g. "2026-08-14"). If provided, uses only
               data up to and including this date (look-ahead-free backtesting).
               If None, uses the most recent available bar in each cache.
        force_refresh: If True, attempt live API fetch for stale sources
                       before falling back to cache. Default False (offline mode).

    Returns:
        dict with the structure specified in Section 2 below.
        Never raises — on total failure, returns a degenerate neutral regime
        with confidence=0 and a "data_unavailable" reason.
    """

def tag_signal(signal: dict, regime: dict | None = None) -> dict:
    """
    Annotate a signal dict with regime context.

    MUTATES the signal dict in place AND returns it.
    (Caller in capture_signals.py does: tag_signal(trade_dict, regime)
    without capturing the return — so in-place mutation is required.)

    Parameters:
        signal: dict with at least 'strategy_id' key (e.g. "STR-I-AAPL-20260814").
                May also contain 'asset_class' ('stock' or 'crypto').
        regime: dict from get_regime(). If None, calls get_regime() internally.
                If regime is None/unavailable, tags with regime="unknown".

    Returns:
        The same signal dict, with these keys added:
        - regime: str (overall regime name)
        - regime_confidence: float 0-1
        - regime_compatible: bool (strategy's regime_best contains current regime)
        - regime_action: str ("boost"|"run"|"reduce"|"suppress") from directives
        - regime_risk_multiplier: float (0.0-2.0)
        - regime_tagged_at: ISO timestamp
    """
```

### Module-level constants

```python
MARKET_DATA_DIR = pathlib.Path.home() / ".hermes" / "market_data"
CRYPTO_DATA_DIR = MARKET_DATA_DIR / "6h"
STALE_THRESHOLD_HOURS = 24  # data older than this gets confidence penalty
BREADTH_SAMPLE_SIZE = 100   # sample N stocks for breadth (perf, see Section 6)
```

---

## 2. get_regime() Return Structure

The return dict must satisfy ALL three callers simultaneously. Below is the full schema with field-by-field source mapping. Fields marked [LEGACY] are already expected by `regime_strategy_selector.py`'s `get_regime_state()`. Fields marked [NEW] are added by this design for the US-116 requirements.

```python
{
    # ---- Top-level metadata ----
    "timestamp": "2026-08-16T14:30:00Z",         # [NEW] ISO UTC timestamp of this call
    "as_of": "2026-08-14",                        # [NEW] date used for look-ahead-free cutoff
    "confidence": 0.82,                           # [NEW] 0-1 overall confidence score
    "data_freshness": "fresh",                    # [NEW] "fresh"|"stale"|"very_stale"|"unavailable"
    
    # ---- Regime classification ----
    "overall": "risk_on",                         # [LEGACY+NEW] primary regime label
    "stock_regime": "risk_on",                    # [LEGACY] regime for stock strategies
    "crypto_regime": "neutral",                   # [LEGACY] regime for crypto strategies
    
    # ---- Component: VIX ----
    "vix": {                                      # [LEGACY]
        "current": 14.25,                         #   latest VIX close
        "regime": "low",                          #   "low"(<18)|"normal"(18-25)|"high"(>25)
        "change_5d": -0.32,                       # [NEW] 5-day VIX delta
        "change_pct_5d": -2.2,                    # [NEW] 5-day VIX % change
        "term_structure": "contango",             # [NEW] "contango"|"backwardation"|"flat"
        "vix_3m": 20.54,                          # [NEW] VIX3M close (if available)
    },
    
    # ---- Component: DXY ----
    "dxy": {                                      # [LEGACY]
        "current": 99.67,
        "trend": "falling",                       #   "rising"|"falling"|"flat"
        "change_5d": -0.45,                       # [NEW]
        "regime": "dollar_weak",                  # [NEW] "dollar_weak"|"dollar_strong"|"neutral"
    },
    
    # ---- Component: Yields ----
    "yields": {                                   # [NEW]
        "t10y": 4.696,                            #   TNX close
        "t10y_trend": "rising",                   #   5-day slope
        "yield_curve_status": "normal",           #   "normal"|"inverted"|"flat"
        # Note: 2y not available in free sources. If TNX > 4.5 and trend rising,
        # flag "caution". Full curve inversion requires 2y/10y which needs FRED.
    },
    
    # ---- Component: Crypto Fear & Greed ----
    "fear_greed": {                               # [LEGACY]
        "value": 34,
        "classification": "Fear",
        "regime": "fear",                         #   "extreme_fear"(<25)|"fear"(25-45)
                                                   #   |"neutral"(45-55)|"greed"(55-75)
                                                   #   |"extreme_greed"(>75)
    },
    
    # ---- Component: Market Breadth ----
    "breadth": {                                  # [LEGACY]
        "pct_above_50ma": 68.0,                   #   % of stocks above their 50-day MA
        "advancing_pct": 62.0,                    # [NEW] % of stocks up on the day
        "divergence": "none",                     #   "none"|"bullish"|"bearish"
                                                   #   (price up but breadth down = bearish div)
        "sample_size": 100,                       # [NEW] how many stocks were sampled
    },
    
    # ---- Component: SPY Trend ----
    "spy_trend": {                                # [NEW]
        "close": 777.28,
        "above_50ma": True,
        "above_200ma": True,
        "ma_50": 765.2,                           #   50-day MA value
        "ma_200": 740.5,                          #   200-day MA value
        "trend": "uptrend",                       #   "uptrend"|"downtrend"|"sideways"
    },
    
    # ---- Component: Cross-Asset Correlation ----
    "correlation": {                              # [LEGACY]
        "correlation_regime": "normal",           #   "unified"|"diversified"|"normal"
        "stock_crypto_corr_30d": 0.42,            # [NEW] rolling 30-day corr SPY vs BTC
        "stock_internal_corr_30d": 0.55,          # [NEW] avg pairwise corr of top 20 stocks
        "description": "Moderate cross-asset correlation",
    },
    
    # ---- Component: Volatility Risk Premium ----
    "vol_risk_premium": {                         # [LEGACY]
        "vol_risk_premium": 2.1,                  #   VIX - realized_20d_vol (percentage points)
        "realized_vol_20d": 12.1,                 # [NEW] SPY 20-day realized vol
        "interpretation": "VIX slightly above realized — normal",
    },
    
    # ---- Components with no free data source (graceful defaults) ----
    "put_call": {                                 # [LEGACY] — no free source
        "total_ratio": 1.0,                       #   neutral default
        "available": False,
    },
    "tvl": {                                      # [LEGACY] — no free source
        "trend": "",
        "available": False,
    },
    "stablecoin": {                               # [LEGACY] — no free source
        "trend": "",
        "available": False,
    },
    "rotation": {                                 # [LEGACY] — computable from stock data
        "leading_sector": "Technology",           #   best-performing sector 20d
        "lagging_sector": "Energy",
        "available": True,
    },
    "funding": {},                                # [LEGACY] — Hyperliquid data exists but
                                                   #   not in this module's scope; empty dict
    "economic_events": [],                        # [LEGACY] — no free calendar source
    
    # ---- [NEW] components breakdown for transparency ----
    "components": {
        "vix": {"regime": "low", "score": 1.0, "weight": 0.20},
        "dxy": {"regime": "dollar_weak", "score": 0.8, "weight": 0.15},
        "breadth": {"regime": "strong", "score": 0.7, "weight": 0.20},
        "spy_trend": {"regime": "uptrend", "score": 1.0, "weight": 0.20},
        "fear_greed": {"regime": "fear", "score": 0.5, "weight": 0.10},
        "correlation": {"regime": "normal", "score": 0.5, "weight": 0.10},
        "yields": {"regime": "caution", "score": 0.3, "weight": 0.05},
    },
}
```

---

## 3. Regime Classification Algorithm

### 3.1 Overview

The classification is a weighted scoring system. Each component produces a sub-regime label and a 0-1 score. The overall regime is determined by:

1. Compute each component's sub-regime and score (see 3.2-3.8).
2. Apply hard override rules (see 3.9) — these can force a regime regardless of scores.
3. If no override, compute weighted average score and map to regime (see 3.10).
4. Compute separate stock_regime and crypto_regime (see 3.11).

### 3.2 VIX Component

```
INPUT: VIXINDEX.parquet (daily, cols: open/high/low/close/volume)
       VIX3M.parquet (daily, for term structure) — may be stale/missing

vix_current = last close
vix_change_5d = current - close[5 bars ago]
vix_change_pct_5d = (current / close[5 bars ago] - 1) * 100

SUB-REGIME:
  if vix_current < 18:
    regime = "low"
    score = 1.0  (risk-on supportive)
  elif vix_current < 25:
    regime = "normal"
    score = 0.5
  else:
    regime = "high"
    score = 0.0  (risk-off)

SHARP RISE DETECTION (for caution override):
  if vix_change_pct_5d > 25%:
    flag vix_sharp_rise = True

TERM STRUCTURE:
  if VIX3M available and VIX3M > VIX * 1.05:
    term_structure = "contango"  (normal, risk-on)
  elif VIX3M < VIX * 0.95:
    term_structure = "backwardation"  (risk-off signal)
  else:
    term_structure = "flat"
```

### 3.3 DXY Component

```
INPUT: DXY.parquet (daily)

dxy_current = last close
dxy_change_5d = current - close[5 bars ago]
dxy_slope_20d = linear regression slope of last 20 closes

SUB-REGIME:
  if dxy_slope_20d < -0.02:
    trend = "falling"
    regime = "dollar_weak"
    score = 0.8  (risk-on tailwind)
  elif dxy_slope_20d > 0.02:
    trend = "rising"
    regime = "dollar_strong"
    score = 0.2  (risk-off headwind)
  else:
    trend = "flat"
    regime = "neutral"
    score = 0.5
```

### 3.4 Yields Component

```
INPUT: TNX.parquet (10y yield, daily)

t10y = last close
t10y_slope_20d = linear regression slope of last 20 closes

YIELD CURVE STATUS:
  Note: We only have 10y (TNX). We do NOT have 2y in free sources.
  Proxy: If TNX > 4.5% and rising → "caution" (high yields pressure equities).
  If TNX < 3.5% → accommodative (risk-on).
  Full inversion detection requires 2y — mark as "partial_data".

  if t10y > 4.5 and t10y_slope_20d > 0:
    status = "caution"
    score = 0.3
  elif t10y < 3.5:
    status = "accommodative"
    score = 0.8
  else:
    status = "normal"
    score = 0.5
```

### 3.5 Crypto Fear & Greed Component

```
INPUT: fear_greed.parquet (daily, cols: date/value/classification)

fg_value = last value
fg_class = last classification

SUB-REGIME:
  if fg_value < 25:   regime = "extreme_fear", score = 0.3  (contrarian bullish but risky)
  elif fg_value < 45: regime = "fear",        score = 0.5
  elif fg_value < 55: regime = "neutral",     score = 0.5
  elif fg_value < 75: regime = "greed",       score = 0.7
  else:               regime = "extreme_greed", score = 0.2  (contrarian bearish)
```

### 3.6 Market Breadth Component

```
INPUT: 529 stock parquets (daily, cols: close/high/low/open/volume/ticker/subperiod)
       To keep <1s, SAMPLE up to 100 random stocks (see Section 6.2).

For each sampled stock:
  close = last close
  ma_50 = 50-day SMA of close
  is_above_50ma = close > ma_50
  is_advancing = close > close[1 bar ago]

pct_above_50ma = count(is_above_50ma) / sample_size * 100
advancing_pct = count(is_advancing) / sample_size * 100

DIVERGENCE DETECTION:
  spy_up = SPY close > SPY close[1 bar ago]
  if spy_up and advancing_pct < 45:
    divergence = "bearish"  (price up, breadth weak)
  elif not spy_up and advancing_pct > 55:
    divergence = "bullish"  (price down, breadth strong)
  else:
    divergence = "none"

SUB-REGIME:
  if pct_above_50ma > 70 and advancing_pct > 60:
    regime = "strong", score = 0.9
  elif pct_above_50ma < 30 and advancing_pct < 40:
    regime = "weak", score = 0.1
  else:
    regime = "mixed", score = 0.5
```

### 3.7 SPY Trend Component

```
INPUT: SPY.parquet (daily)

spy_close = last close
ma_50 = SMA(close, 50)
ma_200 = SMA(close, 200)
above_50ma = spy_close > ma_50
above_200ma = spy_close > ma_200

SUB-REGIME:
  if above_50ma and above_200ma:
    trend = "uptrend", score = 1.0
  elif not above_50ma and not above_200ma:
    trend = "downtrend", score = 0.0
  elif above_50ma and not above_200ma:
    trend = "recovering", score = 0.6
  else:  # below 50ma, above 200ma
    trend = "pullback", score = 0.4
```

### 3.8 Cross-Asset Correlation Component

```
INPUT: SPY.parquet (daily close)
       CRYPTO_DATA_DIR/BTC.parquet (6h close → resample to daily)
       20 largest-cap stock parquets (for internal correlation)

stock_crypto_corr_30d = pearson_corr(
    SPY_daily_returns[-30:],
    BTC_daily_returns[-30:]
)

stock_internal_corr_30d = avg pairwise corr of top-20 stock daily returns[-30:]

CORRELATION REGIME:
  if stock_crypto_corr_30d > 0.7:
    correlation_regime = "unified"     (everything moving together)
    score = 0.3  (stock-picking adds little value)
  elif stock_crypto_corr_30d < 0.3:
    correlation_regime = "diversified" (sector rotation environment)
    score = 0.8  (stock-picking environment)
  else:
    correlation_regime = "normal"
    score = 0.5

NOTE: If BTC data is stale (>30 days), skip this component and set
      correlation_regime = "normal", score = 0.5, available = False.
```

### 3.9 Hard Override Rules

These are evaluated AFTER all components are computed. If any triggers, it overrides the weighted-average result.

```
OVERRIDE 1 — Risk-Off Crisis:
  IF vix_current > 30 OR (vix_current > 25 AND vix_change_pct_5d > 30%)
  THEN overall = "risk_off", confidence = 0.9

OVERRIDE 2 — Sharp Volatility Spike (Caution):
  IF vix_change_pct_5d > 25% AND vix_current < 25
  THEN overall = "caution", confidence = 0.7

OVERRIDE 3 — Unified Market (everything correlated):
  IF stock_crypto_corr_30d > 0.8 AND correlation_regime == "unified"
  THEN overall = "unified", confidence = 0.8
  (This means risk-on or risk-off is being applied uniformly across all assets.
   The direction is determined by VIX/SPY: if VIX < 20, it's risk-on unified;
   if VIX > 25, it's risk-off unified.)

OVERRIDE 4 — Diversified Market:
  IF stock_crypto_corr_30d < 0.2 AND stock_internal_corr_30d < 0.3
  THEN overall = "diversified", confidence = 0.7
```

### 3.10 Weighted Average (Default Path)

If no override triggers:

```
weighted_score = sum(component_score * component_weight for each component)

Weights (sum = 1.0):
  VIX:         0.20
  Breadth:     0.20
  SPY Trend:   0.20
  DXY:         0.15
  Fear&Greed:  0.10
  Correlation: 0.10
  Yields:      0.05

REGIME MAPPING:
  if weighted_score >= 0.70: overall = "risk_on"
  elif weighted_score >= 0.45: overall = "neutral"
  else: overall = "risk_off"

CONFIDENCE:
  confidence = weighted_score
  Adjusted by data freshness (Section 5).
```

### 3.11 Stock vs Crypto Regime

```
stock_regime:
  Start from overall.
  If overall is "unified" or "diversified", inherit the VIX/SPY direction:
    if VIX < 18 and SPY uptrend: stock_regime = "risk_on"
    elif VIX > 25: stock_regime = "risk_off"
    else: stock_regime = "neutral"

crypto_regime:
  Driven by fear_greed + crypto correlation:
    if fg_value < 25: crypto_regime = "caution"  (extreme fear, contrarian)
    elif fg_value > 75: crypto_regime = "caution" (extreme greed, contrarian)
    elif overall == "risk_on": crypto_regime = "risk_on"
    elif overall == "risk_off": crypto_regime = "risk_off"
    else: crypto_regime = "neutral"
```

---

## 4. Data Source Integration

### 4.1 Source Map

| Component     | Parquet file                         | Columns (lowercase)     | Last data (as of audit) | Fresh? |
|---------------|--------------------------------------|-------------------------|-------------------------|--------|
| VIX           | `~/.hermes/market_data/VIXINDEX.parquet` | open/high/low/close/volume | 2026-08-14          | Yes    |
| VIX3M         | `~/.hermes/market_data/VIX3M.parquet`    | open/high/low/close/volume | 2026-07-17          | STALE  |
| DXY           | `~/.hermes/market_data/DXY.parquet`      | open/high/low/close/volume | 2026-08-14          | Yes    |
| TNX (10y)     | `~/.hermes/market_data/TNX.parquet`      | open/high/low/close/volume | 2026-08-14          | Yes    |
| SPY           | `~/.hermes/market_data/SPY.parquet`      | open/high/low/close/volume/ticker/subperiod | 2026-08-14 | Yes |
| Fear & Greed  | `~/.hermes/market_data/fear_greed.parquet` | date/value/classification | 2026-08-16          | Yes    |
| Stocks (529)  | `~/.hermes/market_data/<TICKER>.parquet`  | open/high/low/close/volume/ticker/subperiod | 2026-08-14 | Yes |
| Crypto (35)   | `~/.hermes/market_data/6h/<TICKER>.parquet` | open/high/low/close/volume/ticker/subperiod | 2026-07-29 | STALE |

### 4.2 Caching Strategy

The module reads ONLY from parquet caches — no live API calls in the default path (`force_refresh=False`). This ensures:
- Sub-second performance (no network I/O)
- Offline operation
- Look-ahead-free (historical data only)

**Refresh responsibility is OUTSIDE this module.** The existing `fetch_fear_greed.py`, `fetch_intraday_stocks.py`, and `fetch_intraday_crypto.py` scripts populate the caches. A cron job or pre-scan hook should call them before signal scans.

When `force_refresh=True`:
- Attempt to call `fetch_fear_greed.py` (only source with a simple free API)
- All other sources require yfinance/Hyperliquid fetch scripts — delegate to those scripts via subprocess, with 5-second timeout, fall back to cache on failure.

### 4.3 Data Freshness Check

```python
def _check_freshness(parquet_path: Path, as_of: str | None = None) -> tuple[str, float]:
    """
    Returns (freshness_label, confidence_penalty).
    - "fresh":       last bar within 24h of as_of/now → penalty = 1.0
    - "stale":       24h-72h → penalty = 0.8
    - "very_stale":  72h-7d → penalty = 0.5
    - "unavailable": file missing or >7d → penalty = 0.3
    """
```

The overall confidence is multiplied by the minimum freshness penalty across all available components. This ensures stale data degrades confidence without blocking the regime determination.

---

## 5. Graceful Degradation (Missing Data Handling)

### 5.1 Principle

`get_regime()` NEVER raises. It always returns a dict with all keys present. Missing components get default values and `available: False`.

### 5.2 Per-Component Fallbacks

| Component      | If Missing                          | Fallback                                    |
|----------------|-------------------------------------|---------------------------------------------|
| VIX            | VIXINDEX.parquet missing            | score=0.5 (neutral), regime="unknown"       |
| VIX3M          | VIX3M.parquet missing or stale      | Skip term structure, note in components     |
| DXY            | DXY.parquet missing                 | score=0.5, trend="unknown"                  |
| TNX            | TNX.parquet missing                 | score=0.5, status="partial_data"            |
| SPY            | SPY.parquet missing                 | score=0.5, trend="unknown" (critical gap)   |
| Fear & Greed   | fear_greed.parquet missing          | score=0.5, value=50, classification="Neutral"|
| Breadth        | Stock parquets missing              | score=0.5, pct_above_50ma=50, sample_size=0 |
| Correlation    | BTC.parquet missing/stale           | regime="normal", score=0.5, available=False  |

### 5.3 Confidence Adjustment

```
base_confidence = weighted_score  (or override confidence)

# Count available components
available_count = count of components with available=True
total_count = 7

# Penalize for missing components
completeness_ratio = available_count / total_count
adjusted_confidence = base_confidence * completeness_ratio

# Apply freshness penalty (minimum across all available components)
freshness_penalty = min(freshness_penalties)
final_confidence = adjusted_confidence * freshness_penalty

# Floor: if <3 components available, confidence cannot exceed 0.3
if available_count < 3:
    final_confidence = min(final_confidence, 0.3)
```

### 5.4 Total Failure Mode

If even VIX and SPY are unavailable (the two most critical sources):

```python
return {
    "overall": "neutral",
    "stock_regime": "neutral",
    "crypto_regime": "neutral",
    "confidence": 0.0,
    "data_freshness": "unavailable",
    "components": {},
    # ... all other fields with defaults ...
    "error": "Critical data sources unavailable — VIX and SPY missing",
}
```

The callers already handle this: `regime_strategy_selector.py` checks `state.get("available")` and falls back to "run all at default risk". `capture_signals.py` wraps the import in try/except and continues without tagging.

---

## 6. Performance Considerations

### 6.1 Budget: <1 second per call

Called on every signal scan. Must be fast.

### 6.2 Breadth Sampling

The biggest risk is reading 529 parquet files for breadth computation. At ~5ms per parquet read, 529 files = ~2.6 seconds — TOO SLOW.

**Solution: Random sample of 100 stocks.**

```python
import random
STOCK_FILES = sorted(MARKET_DATA_DIR.glob("*.parquet"))
# Exclude macro files
STOCK_FILES = [f for f in STOCK_FILES if f.stem not in 
               ("VIXINDEX","VIX3M","DXY","TNX","SPY","fear_greed")]
sample = random.Random(42).sample(STOCK_FILES, min(100, len(STOCK_FILES)))
# Fixed seed for reproducibility within a session
```

100 files * 5ms = 500ms. Acceptable.

For each sampled stock, we only need the last 51 rows (for 50-day MA + 1-day return):

```python
df = pd.read_parquet(path).tail(51)  # tail read is fast in parquet
```

Actually, parquet doesn't support efficient tail reads by default. Alternative: read only the 'close' column:

```python
df = pd.read_parquet(path, columns=['close']).tail(51)
```

Column projection in parquet IS efficient — reads only the close column row group, skipping OHLCV. This should be ~1-2ms per file. 100 files = ~200ms.

### 6.3 Caching Breadth Within Session

If `get_regime()` is called multiple times in the same scan (e.g. once for stocks, once for crypto), cache the breadth result with a 5-minute TTL:

```python
_breadth_cache = {"value": None, "timestamp": 0}

def _compute_breadth(as_of):
    if time.time() - _breadth_cache["timestamp"] < 300:
        return _breadth_cache["value"]
    # ... compute ...
    _breadth_cache["value"] = result
    _breadth_cache["timestamp"] = time.time()
    return result
```

### 6.4 Correlation Computation

Reading 20 stock files + BTC + SPY for correlation: ~22 files * 2ms = 44ms. Acceptable. Only compute 30-day returns (tail 31 rows per file).

### 6.5 Sector Rotation

Computable from the same 100-stock breadth sample. Map ticker to sector via a hardcoded dict (or yfinance sector info cached separately). Group by sector, compute 20-day return, identify leading/lagging.

### 6.6 Performance Budget Breakdown

| Operation                | Files | Time (est) |
|--------------------------|-------|------------|
| Read VIX                 | 1     | 2ms        |
| Read VIX3M               | 1     | 2ms        |
| Read DXY                 | 1     | 2ms        |
| Read TNX                 | 1     | 2ms        |
| Read SPY                 | 1     | 2ms        |
| Read fear_greed          | 1     | 2ms        |
| Read breadth sample      | 100   | 200ms      |
| Read correlation sample  | 22    | 44ms       |
| Compute (SMA, corr, etc) | —     | ~50ms      |
| **Total**                | **128** | **~306ms** |

Well within the 1-second budget. Even with 2x overhead for I/O variance, we're at ~600ms.

---

## 7. tag_signal() Implementation Design

### 7.1 Compatibility Logic

```python
def tag_signal(signal: dict, regime: dict | None = None) -> dict:
    if regime is None:
        regime = get_regime()
    
    if not regime or regime.get("confidence", 0) == 0:
        signal["regime"] = "unknown"
        signal["regime_confidence"] = 0.0
        signal["regime_compatible"] = True  # don't block when unknown
        signal["regime_action"] = "run"
        signal["regime_risk_multiplier"] = 1.0
        signal["regime_tagged_at"] = datetime.now(timezone.utc).isoformat()
        return signal
    
    overall = regime.get("overall", "neutral")
    confidence = regime.get("confidence", 0.5)
    
    # Extract strategy ID from signal
    strategy_id = signal.get("strategy_id", "")
    # Parse prefix: "STR-I-AAPL-20260814" → "STR-I"
    strat_prefix = "-".join(strategy_id.split("-")[:2]) if strategy_id else ""
    
    # Look up strategy in registry to check regime compatibility
    # Import locally to avoid circular dependency
    try:
        from regime_strategy_selector import STRATEGY_REGISTRY
        strat_info = STRATEGY_REGISTRY.get(strat_prefix, {})
        regime_best = strat_info.get("regime_best", [])
        regime_avoid = strat_info.get("regime_avoid", [])
    except ImportError:
        regime_best = []
        regime_avoid = []
    
    # Determine compatibility
    # Map overall regime to tags for matching
    regime_tags = [overall]
    corr = regime.get("correlation", {}).get("correlation_regime", "normal")
    if corr == "diversified":
        regime_tags.append("diversified")
    elif corr == "unified":
        regime_tags.append("unified")
    
    is_compatible = (
        not any(r in regime_avoid for r in regime_tags) and
        (not regime_best or any(r in regime_best for r in regime_tags) or 
         overall not in regime_avoid)
    )
    # Simpler: compatible = overall not in regime_avoid
    is_compatible = overall not in regime_avoid
    
    # Determine action
    if overall in regime_avoid:
        action = "suppress"
        risk_mult = 0.0
    elif overall in regime_best:
        action = "boost"
        risk_mult = 1.5
    else:
        action = "run"
        risk_mult = 1.0
    
    # Apply to signal dict (IN-PLACE mutation)
    signal["regime"] = overall
    signal["regime_confidence"] = confidence
    signal["regime_compatible"] = is_compatible
    signal["regime_action"] = action
    signal["regime_risk_multiplier"] = risk_mult
    signal["regime_tagged_at"] = datetime.now(timezone.utc).isoformat()
    
    return signal
```

### 7.2 Why In-Place Mutation

The caller in `capture_signals.py` line 220 does:
```python
tag_signal(trade_dict, regime)
```
No assignment. The return value is discarded. Therefore tag_signal MUST mutate `trade_dict` in place. Returning the dict as well is a courtesy for callers that do capture the return.

### 7.3 Strategy ID Parsing

Signals in capture_signals use IDs like `"STR-I-AAPL-20260814"`. The registry uses `"STR-I"`. The parsing logic:

```python
parts = strategy_id.split("-")
strat_prefix = "-".join(parts[:2]) if len(parts) >= 2 else strategy_id
# "STR-I-AAPL-20260814" → "STR-I"
# "STR-VIXC-SPY-20260814" → "STR-VIXC"
```

---

## 8. Python Path / venv Issue

### 8.1 The Problem

`edge_discovery_engine.py` and other research scripts fail with `No module named numpy` when run with the system default `python3`. This is because:

- The Hermes agent venv at `/usr/local/lib/hermes-agent/venv/bin/python` has numpy 2.4.6 installed.
- The system `python3` (3.11.15) also has numpy 2.4.6 (verified during audit).
- However, some execution contexts (cron, subprocess from capture_signals) may use a different venv or the bare `python3` without the right site-packages path.

### 8.2 The Fix (Design Recommendation)

Two-layer fix:

**Layer 1 — Module-level (regime_filter.py):**
Add a numpy import guard at the top of regime_filter.py:

```python
try:
    import numpy as np
    import pandas as pd
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    # Fall back to pure-Python calculations (slower, but functional)
```

For the correlation computation, if numpy is unavailable, use `statistics.correlation()` from the stdlib (Python 3.10+). For SMA, use pure Python. This makes the module resilient to venv issues.

**Layer 2 — Execution context:**
All research scripts should use the Hermes agent venv explicitly:
```bash
#!/usr/bin/env python3
# OR explicitly:
/usr/local/lib/hermes-agent/venv/bin/python script.py
```

The recommendation for the Coder agent: update the shebang or execution wrapper in:
- `scripts/research/edge_discovery_engine.py`
- `scripts/research/regime_strategy_selector.py`
- `scripts/research/compute_confluence.py`

to use `/usr/local/lib/hermes-agent/venv/bin/python` instead of bare `python3`.

Alternatively, install numpy in whatever venv the scripts are being run from:
```bash
pip install numpy pandas
```

**However**, since this is a DESIGN document, the Coder agent should implement Layer 1 (the import guard) as part of the regime_filter.py rewrite, and note Layer 2 as a separate fix task.

---

## 9. Look-Ahead-Free Guarantee

### 9.1 The Rule

For backtesting (when `as_of` is specified), the regime on date D must be computed using ONLY data from bars on or before date D. No future data.

### 9.2 Implementation

```python
def _load_parquet_as_of(path, as_of=None, n_tail=None):
    """Load parquet, optionally truncating to as_of date."""
    df = pd.read_parquet(path, columns=['close'])  # column projection for speed
    if as_of is not None:
        as_of_ts = pd.Timestamp(as_of)
        df = df[df.index <= as_of_ts]
    if n_tail is not None:
        df = df.tail(n_tail)
    return df
```

Every component function receives `as_of` and passes it to `_load_parquet_as_of()`. This ensures:
- VIX close on date D uses only VIX data up to D
- SPY 50-day MA on date D uses only SPY closes up to D
- Breadth on date D uses only stock closes up to D
- Correlation window ends at D, not after

### 9.3 No Future Data in Cached Files

The cached parquet files contain historical data only (last bar = 2026-08-14 or 2026-08-16). There is no future data in the caches. The `as_of` parameter is for backtesting scenarios where you want to simulate "what would the regime have been on date X?"

### 9.4 Audit Note

The HermesForge US-114 swarm audit found 7 look-ahead bias bugs in scanner code. The regime_filter module must NOT repeat those mistakes. Specifically:
- `find_peaks(distance=N)` looks N bars into the future — DO NOT use for regime detection
- Entry conditions must use `df.iloc[-1]` (current bar) or `df.loc[:as_of].iloc[-1]`, never `df.shift(-N)`
- All SMA/rolling computations naturally exclude future data (pandas rolling is backward-looking by default)

---

## 10. Testing Plan

### 10.1 Unit Tests (pytest)

Test file: `~/HermesForge/scripts/data/test_regime_filter.py`

```
Test Group 1: Component Functions
  test_vix_component_low()      — VIX=15 → regime="low", score=1.0
  test_vix_component_normal()   — VIX=20 → regime="normal", score=0.5
  test_vix_component_high()     — VIX=30 → regime="high", score=0.0
  test_vix_sharp_rise()         — 5d change >25% → caution flag
  test_vix_term_structure()     — VIX3M > VIX*1.05 → contango
  test_dxy_falling()            — slope < -0.02 → dollar_weak
  test_dxy_rising()             — slope > 0.02 → dollar_strong
  test_breadth_strong()         — 70%+ above 50ma → strong
  test_breadth_weak()           — <30% above 50ma → weak
  test_breadth_bearish_div()    — SPY up, <45% advancing → bearish divergence
  test_spy_uptrend()            — above 50+200ma → uptrend
  test_spy_downtrend()          — below both → downtrend
  test_correlation_unified()    — corr >0.7 → unified
  test_correlation_diversified() — corr <0.3 → diversified
  test_fear_greed_extreme_fear() — value=20 → extreme_fear
  test_fear_greed_extreme_greed() — value=80 → extreme_greed

Test Group 2: Regime Classification
  test_risk_on_regime()         — VIX<18, DXY falling, breadth strong, SPY uptrend → risk_on
  test_risk_off_regime()        — VIX>25, DXY rising, breadth weak, SPY downtrend → risk_off
  test_neutral_regime()         — VIX 18-25, mixed → neutral
  test_caution_override()       — VIX sharp rise → caution (even if VIX<25)
  test_unified_override()       — corr >0.8 → unified
  test_diversified_override()   — corr <0.2 + low internal corr → diversified

Test Group 3: Graceful Degradation
  test_missing_vix()            — VIXINDEX.parquet absent → neutral fallback, confidence<0.5
  test_missing_spy()            — SPY.parquet absent → neutral fallback
  test_missing_fear_greed()     — fear_greed.parquet absent → value=50 default
  test_missing_breadth()        — no stock files → sample_size=0, neutral
  test_total_failure()          — all missing → confidence=0, overall=neutral
  test_stale_data()             — VIX3M 30+ days old → freshness penalty applied

Test Group 4: tag_signal
  test_tag_signal_compatible()  — STR-I in risk_on → compatible=True, action=boost
  test_tag_signal_incompatible() — STR-I in risk_off → compatible=False, action=suppress
  test_tag_signal_neutral()     — STR-B in neutral → action=run, risk_mult=1.0
  test_tag_signal_mutates()     — verify dict is mutated in place
  test_tag_signal_no_regime()   — regime=None → calls get_regime() internally
  test_tag_signal_unknown_strat() — strategy_id not in registry → action=run (no block)

Test Group 5: Look-Ahead-Free
  test_as_of_truncation()       — as_of="2026-06-01" → only uses data up to June 1
  test_as_of_vs_now()           — regime as_of Jan 1 vs as_of Aug 14 differ

Test Group 6: Performance
  test_get_regime_under_1s()    — time get_regime() < 1.0 second
  test_breadth_sample_size()    — verify exactly 100 stocks sampled
  test_session_cache()          — second call within 5min uses cached breadth

Test Group 7: Integration (with real cached data)
  test_get_regime_real_data()   — call with actual parquet files, verify sane output
  test_strategy_selector_integration() — get_regime() output feeds into get_strategy_directives()
  test_capture_signals_integration() — tag_signal() output has all expected keys
```

### 10.2 Integration Test Script

A standalone script `scripts/data/test_regime_live.py` that:
1. Calls `get_regime()` with real cached data
2. Prints the full regime dict
3. Calls `get_strategy_directives()` to verify the chain works end-to-end
4. Creates a dummy signal and calls `tag_signal()` to verify annotation
5. Times the full call

### 10.3 Validation Checklist (for Coder agent)

- [ ] `from regime_filter import get_regime, tag_signal` works from all three caller directories
- [ ] `get_regime()` returns dict with ALL keys expected by `regime_strategy_selector.py` `get_regime_state()`
- [ ] `get_regime()` returns dict with ALL keys expected by `capture_signals.py` (stock_regime, crypto_regime, overall, vix.current, dxy.trend, fear_greed.value)
- [ ] `tag_signal()` mutates the signal dict in place (not just returns)
- [ ] `get_regime()` completes in <1 second with real data
- [ ] `get_regime()` never raises (even with missing files)
- [ ] `as_of` parameter correctly truncates data (no look-ahead)
- [ ] numpy import guard present and functional
- [ ] All code committed to git after implementation

---

## 11. Implementation Notes for Coder Agent

### 11.1 Module Structure

```python
#!/usr/bin/env python3
"""
regime_filter.py — Market regime detection from cached data sources.

Replaces the former hardcoded JSON stub with a real module that:
  - Reads VIX, DXY, TNX, SPY, Fear&Greed, stock breadth, crypto correlation
    from cached parquet files
  - Computes a weighted regime classification with hard overrides
  - Exposes get_regime() and tag_signal() for strategy selection
  - Handles missing/stale data gracefully (never raises)
  - Is look-ahead-free (supports as_of parameter for backtesting)

Usage:
    from regime_filter import get_regime, tag_signal
    regime = get_regime()
    tag_signal(signal_dict, regime)
    
    python3 regime_filter.py              # print regime as JSON
    python3 regime_filter.py --as-of 2026-06-01  # historical regime
"""

# Imports with guard
# Constants
# Helper: _load_parquet_as_of()
# Helper: _check_freshness()
# Component functions: _compute_vix(), _compute_dxy(), etc.
# Main: get_regime()
# Annotation: tag_signal()
# CLI: main() with argparse
```

### 11.2 Import Path Fix

The callers add `scripts/data` to `sys.path` before importing. This already works in `regime_strategy_selector.py` (line 28). `capture_signals.py` needs the same path insertion — verify it's present or add it.

### 11.3 Column Name Convention

All parquet files use LOWERCASE column names: `open, high, low, close, volume`. The module must use lowercase, not the yfinance default `Open, High, Low, Close`. The stock parquets also have `ticker` and `subperiod` columns.

### 11.4 CLI Interface

Keep the `if __name__ == "__main__"` block for standalone testing:

```python
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--as-of", help="Historical date (YYYY-MM-DD)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    
    regime = get_regime(as_of=args.as_of)
    if args.json:
        print(json.dumps(regime, indent=2, default=str))
    else:
        _print_regime_human(regime)
```

### 11.5 Git Commit

Per user hard rule: commit immediately after implementation.

```bash
git add scripts/data/regime_filter.py scripts/data/test_regime_filter.py
git commit -m "US-116: Replace regime_filter stub with real module

- get_regime() computes weighted regime from 7 cached data sources
- tag_signal() annotates signals with regime compatibility
- Graceful degradation for missing/stale data
- Look-ahead-free via as_of parameter
- <1s performance via breadth sampling + column projection"
```

---

## 12. Risk Assessment

| Risk                              | Likelihood | Impact | Mitigation                              |
|-----------------------------------|------------|--------|-----------------------------------------|
| Breadth sample not representative | Medium     | Low    | Fixed seed + 100 stocks is statistically sufficient for regime detection |
| VIX3M data stale (last 2026-07-17)| Certain    | Low    | Term structure flagged as unavailable, no impact on primary regime |
| Crypto data stale (last 2026-07-29)| Certain   | Medium | Correlation component skipped, crypto_regime uses fear_greed only |
| Missing put_call/TVL/funding data | Certain    | Low    | Callers already handle defaults; these are enhancement signals |
| Performance regression with 529 stocks | Low    | Medium | Column projection + sampling keeps it under 300ms |
| Circular import with regime_strategy_selector | Medium | High | tag_signal imports STRATEGY_REGISTRY locally inside function, not at module level |
| numpy unavailable in some venv    | Low        | Medium | Import guard + pure-Python fallback for correlation/SMA |

---

## 13. Out of Scope

- Live API calls inside get_regime() (delegate to fetch scripts)
- Computing put_call ratio (no free source identified)
- Computing TVL/stablecoin trends (no free source identified)
- Economic event calendar (no free source identified)
- Funding rate integration (exists in Hyperliquid fetch scripts but separate concern)
- Fixing the venv/numpy issue in edge_discovery_engine.py (noted in Section 8, separate task)
- Modifying the callers (they already expect the right interface — this module just needs to provide it)

---

**End of Design Document**  
Ready for Coder agent implementation per ADR-001 T2 hard floor.
