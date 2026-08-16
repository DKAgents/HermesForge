#!/usr/bin/env python3
"""
regime_detector.py — HermesForge Market Regime Detector

Classifies the current market regime using SPY daily OHLCV data.
Determines which strategies should be activated based on the detected regime.

Regime classification logic:
  - ATR(14)/Close ratio vs its 50-day average → volatility level
  - ADX(14) → trend strength
  - Bollinger Band width percentile → contraction/expansion
  - Price vs 200-day SMA → bull/bear structural context

Regime outputs:
  - "trending"        — ADX > 25, price in sustained direction
  - "ranging"         — ADX < 20, price oscillating near SMA
  - "transitional"    — ADX falling from >25 toward <20, volatility expanding
  - "high-volatility" — ATR/Close > 2.0x its 50-day average
  - "low-volatility"  — ATR/Close < 0.5x its 50-day average

Usage:
    from regime_detector import detect_regime, get_active_strategies
    regime = detect_regime(spy_df)
    strategies = get_active_strategies(regime)
"""

import pandas as pd
import numpy as np
from typing import Optional

# ── Strategy-to-Regime Mapping ────────────────────────────────────────────────
# Each strategy maps to one or more regimes where it has demonstrated edge.
# Strategies NOT mapped to the current regime are skipped for that day.

STRATEGY_REGIME_MAP = {
    # Live strategies (publish_enabled: true)
    "STR-B-macd-histogram-divergence": ["trending", "ranging"],
    "STR-I-adaptive-trend":            ["trending"],
    
    # WATCH strategies (publish_enabled: false, but active in portfolio pipeline)
    "STR-L-atr-contraction":           ["low-volatility"],
    "STR-P-crosssectional":            ["ranging", "trending"],
    
    # Fallback scanner (runs in all regimes — informational only)
    "STR-D-sr-role-reversal":          ["trending", "ranging", "transitional", "high-volatility", "low-volatility"],
}

# Regime descriptions for logging
REGIME_DESCRIPTIONS = {
    "trending":        "ADX > 25, sustained directional move",
    "ranging":         "ADX < 20, price oscillating near SMA",
    "transitional":    "ADX falling, volatility expanding, regime shift",
    "high-volatility": "ATR/Close > 2.0x 50-day average",
    "low-volatility":  "ATR/Close < 0.5x 50-day average",
}


def _compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Compute Average True Range."""
    high, low, close = df['high'], df['low'], df['close']
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(window=period, min_periods=1).mean()


def _compute_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Compute ADX (Average Directional Index)."""
    high, low, close = df['high'], df['low'], df['close']
    up_move = high.diff()
    down_move = -low.diff()
    
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
    plus_dm = pd.Series(plus_dm, index=df.index)
    minus_dm = pd.Series(minus_dm, index=df.index)
    
    atr = _compute_atr(df, period)
    plus_di = 100 * (plus_dm.rolling(window=period, min_periods=1).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=period, min_periods=1).mean() / atr)
    
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.rolling(window=period, min_periods=1).mean()
    return adx


def _compute_bollinger_width(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """Compute normalized Bollinger Band width."""
    sma = df['close'].rolling(window=period).mean()
    std = df['close'].rolling(window=period).std(ddof=0)
    upper = sma + 2 * std
    lower = sma - 2 * std
    width = (upper - lower) / sma
    return width


def detect_regime(df: pd.DataFrame) -> dict:
    """
    Detect the current market regime from OHLCV data (typically SPY).
    
    Returns:
        {
            "regime": str,           # primary regime label
            "secondary": str | None, # secondary regime if mixed signals
            "adx": float,            # current ADX(14)
            "atr_ratio": float,      # ATR/Close / its 50-day average
            "bb_width_pct": float,   # Bollinger width percentile (0-1)
            "above_sma200": bool,    # price above 200-day SMA
            "adx_trend": str,        # "rising", "falling", "flat"
            "description": str,      # human-readable summary
            "active_strategies": list,  # strategy IDs to run
        }
    """
    if len(df) < 250:
        return {
            "regime": "unknown",
            "secondary": None,
            "adx": 0,
            "atr_ratio": 0,
            "bb_width_pct": 0.5,
            "above_sma200": True,
            "adx_trend": "flat",
            "description": "Insufficient data for regime detection",
            "active_strategies": list(STRATEGY_REGIME_MAP.keys()),
        }
    
    atr = _compute_atr(df)
    adx = _compute_adx(df)
    bb_width = _compute_bollinger_width(df)
    sma200 = df['close'].rolling(200).mean()
    
    # Current values (last bar)
    idx = len(df) - 1
    current_atr = atr.iloc[idx]
    current_close = df['close'].iloc[idx]
    current_adx = adx.iloc[idx]
    current_sma200 = sma200.iloc[idx]
    
    # Normalized ATR ratio (volatility level relative to its own average)
    atr_normalized = atr / df['close']
    atr_norm_avg = atr_normalized.rolling(50).mean()
    atr_ratio = atr_normalized.iloc[idx] / atr_norm_avg.iloc[idx] if atr_norm_avg.iloc[idx] > 0 else 1.0
    
    # Bollinger width percentile (where does current width sit in last 120 bars?)
    bb_lookback = 120
    if len(bb_width) > bb_lookback:
        bb_window = bb_width.iloc[idx - bb_lookback:idx]
        bb_width_pct = (bb_window < bb_width.iloc[idx]).sum() / len(bb_window)
    else:
        bb_width_pct = 0.5
    
    # ADX trend (rising or falling over last 10 bars?)
    adx_10_ago = adx.iloc[idx - 10] if idx >= 10 else adx.iloc[0]
    adx_delta = current_adx - adx_10_ago
    if adx_delta > 2:
        adx_trend = "rising"
    elif adx_delta < -2:
        adx_trend = "falling"
    else:
        adx_trend = "flat"
    
    above_sma200 = current_close > current_sma200 if not pd.isna(current_sma200) else True
    
    # ── Regime Classification ────────────────────────────────────────────────
    # Priority: high-volatility > low-volatility > transitional > trending > ranging
    # Volatility extremes take priority because they affect all strategies.
    
    regime = None
    secondary = None
    
    if atr_ratio >= 2.0:
        regime = "high-volatility"
        # Secondary: still classify trend/range context
        if current_adx > 25:
            secondary = "trending"
        elif current_adx < 20:
            secondary = "ranging"
    elif atr_ratio <= 0.5:
        regime = "low-volatility"
        if current_adx < 20:
            secondary = "ranging"
    elif adx_trend == "falling" and current_adx < 25 and atr_ratio > 1.2:
        # ADX was high, now falling, volatility expanding → transition
        regime = "transitional"
    elif current_adx > 25:
        regime = "trending"
    elif current_adx < 20:
        regime = "ranging"
    else:
        # ADX between 20-25 — ambiguous, default to trending with note
        regime = "trending"
        secondary = "ranging"
    
    # Get active strategies for this regime
    active = get_active_strategies(regime, secondary)
    
    description = (
        f"Regime: {regime}"
        f"{' / ' + secondary if secondary else ''} | "
        f"ADX: {current_adx:.1f} ({adx_trend}) | "
        f"ATR ratio: {atr_ratio:.2f}x | "
        f"BB width pct: {bb_width_pct:.0%} | "
        f"{'Above' if above_sma200 else 'Below'} SMA200"
    )
    
    return {
        "regime": regime,
        "secondary": secondary,
        "adx": round(current_adx, 1),
        "atr_ratio": round(atr_ratio, 2),
        "bb_width_pct": round(bb_width_pct, 3),
        "above_sma200": above_sma200,
        "adx_trend": adx_trend,
        "description": description,
        "active_strategies": active,
    }


def get_active_strategies(primary_regime: str, secondary_regime: str = None) -> list:
    """
    Return list of strategy IDs that should be active given the current regime.
    A strategy is active if its regime map includes either the primary or secondary regime.
    """
    active = set()
    for strategy_id, regimes in STRATEGY_REGIME_MAP.items():
        if primary_regime in regimes:
            active.add(strategy_id)
        if secondary_regime and secondary_regime in regimes:
            active.add(strategy_id)
    return sorted(active)


def detect_regime_for_asset_class(
    stock_data: dict, crypto_data: dict = None, asset_class: str = "stock"
) -> dict:
    """
    Detect regime using the appropriate benchmark for each asset class.
    
    Stocks → SPY (S&P 500 ETF)
    Crypto → BTC (Bitcoin, dominant market proxy)
    
    Returns same dict format as detect_regime().
    """
    if asset_class == "crypto":
        # Use BTC as the crypto regime benchmark
        benchmark_df = None
        if crypto_data:
            for key in ["BTC", "BTCUSDT", "BTC-PERP"]:
                if key in crypto_data:
                    benchmark_df = crypto_data[key]
                    break
            if benchmark_df is None and crypto_data:
                # Fallback: use first available crypto
                benchmark_df = list(crypto_data.values())[0]
        
        if benchmark_df is None:
            return {
                "regime": "unknown",
                "secondary": None,
                "adx": 0, "atr_ratio": 0, "bb_width_pct": 0.5,
                "above_sma200": True, "adx_trend": "flat",
                "description": "No crypto benchmark data available",
                "active_strategies": list(STRATEGY_REGIME_MAP.keys()),
                "benchmark": "none",
            }
        
        result = detect_regime(benchmark_df)
        result["benchmark"] = "BTC"
        return result
    else:
        # Use SPY as the stock regime benchmark
        benchmark_df = stock_data.get("SPY")
        if benchmark_df is None and stock_data:
            benchmark_df = list(stock_data.values())[0]
        
        if benchmark_df is None:
            return {
                "regime": "unknown",
                "secondary": None,
                "adx": 0, "atr_ratio": 0, "bb_width_pct": 0.5,
                "above_sma200": True, "adx_trend": "flat",
                "description": "No stock benchmark data available",
                "active_strategies": list(STRATEGY_REGIME_MAP.keys()),
                "benchmark": "none",
            }
        
        result = detect_regime(benchmark_df)
        result["benchmark"] = "SPY"
        return result


if __name__ == "__main__":
    import pathlib
    import sys
    
    CACHE_DIR = pathlib.Path.home() / ".hermes" / "market_data"
    
    # Detect stock regime from SPY
    spy_path = CACHE_DIR / "SPY.parquet"
    if spy_path.exists():
        spy_df = pd.read_parquet(spy_path)
        stock_regime = detect_regime(spy_df)
        stock_regime["benchmark"] = "SPY"
        
        print(f"\n{'='*60}")
        print("HermesForge Market Regime Detector — STOCKS (SPY)")
        print(f"{'='*60}")
        print(stock_regime["description"])
        print(f"\nActive strategies: {stock_regime['active_strategies']}")
    else:
        print("SPY data not found.")
    
    # Detect crypto regime from BTC
    btc_path = CACHE_DIR / "crypto" / "BTC.parquet"
    if btc_path.exists():
        btc_df = pd.read_parquet(btc_path)
        crypto_regime = detect_regime(btc_df)
        crypto_regime["benchmark"] = "BTC"
        
        print(f"\n{'='*60}")
        print("HermesForge Market Regime Detector — CRYPTO (BTC)")
        print(f"{'='*60}")
        print(crypto_regime["description"])
        print(f"\nActive strategies: {crypto_regime['active_strategies']}")
    else:
        print("\nBTC data not found.")
    
    # Summary comparison
    if spy_path.exists() and btc_path.exists():
        print(f"\n{'='*60}")
        print("Regime Comparison")
        print(f"{'='*60}")
        print(f"Stocks (SPY):  {stock_regime['regime']:15s} ADX={stock_regime['adx']:.1f}  ATR ratio={stock_regime['atr_ratio']:.2f}x")
        print(f"Crypto (BTC):  {crypto_regime['regime']:15s} ADX={crypto_regime['adx']:.1f}  ATR ratio={crypto_regime['atr_ratio']:.2f}x")
        
        stock_only = set(stock_regime['active_strategies']) - set(crypto_regime['active_strategies'])
        crypto_only = set(crypto_regime['active_strategies']) - set(stock_regime['active_strategies'])
        both = set(stock_regime['active_strategies']) & set(crypto_regime['active_strategies'])
        
        print(f"\nBoth asset classes:   {sorted(both)}")
        print(f"Stocks only:          {sorted(stock_only)}")
        print(f"Crypto only:          {sorted(crypto_only)}")
