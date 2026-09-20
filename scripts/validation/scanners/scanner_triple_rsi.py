#!/usr/bin/env python3
"""
scanner_triple_rsi.py — HermesForge Triple RSI Strategy (HYP-13)
=================================================================

QuantifiedStrat's Triple RSI mean-reversion strategy on SPY:

Conditions (all must be true):
  1. 5-day RSI < 30 (oversold)
  2. 5-day RSI fallen for 3 consecutive days
  3. 5-day RSI was < 60 three trading days ago
  4. Close above 200-day MA (bull trend filter)

Entry: buy at close
Exit:  sell at close when 5-day RSI crosses above 50

Timeframe: daily bars
Asset class: stocks (SPY)
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional

STRATEGY_ID = "STR-TRSI-triple-rsi-mean-reversion"
STRATEGY_NAME = "Triple RSI Mean Reversion"
VERSION = "1.0"
HYPOTHESIS_ID = "HYP-13"

# Parameters
RSI_PERIOD = 5
RSI_OVERSOLD = 30
RSI_EXIT = 50
RSI_PRIOR_MAX = 60
FALLING_DAYS = 3
MA_PERIOD = 200


def _rsi(series: pd.Series, period: int = RSI_PERIOD) -> pd.Series:
    """Compute Wilder's RSI."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def scan(symbol: str, df: pd.DataFrame) -> List[Dict]:
    """Scan for Triple RSI signals."""
    close = df['close']
    rsi = _rsi(close)
    ma200 = close.rolling(MA_PERIOD).mean()
    
    # Entry conditions
    c_oversold = rsi < RSI_OVERSOLD
    c_falling = (
        (rsi < rsi.shift(1)) &
        (rsi.shift(1) < rsi.shift(2)) &
        (rsi.shift(2) < rsi.shift(3))
    )
    c_prior_low = rsi.shift(3) < RSI_PRIOR_MAX
    c_trend = close > ma200
    
    entry = c_oversold & c_falling & c_prior_low & c_trend
    
    if not entry.iloc[-1]:
        return []
    
    latest_close = close.iloc[-1]
    latest_rsi = rsi.iloc[-1]
    latest_ma = ma200.iloc[-1]
    
    # Compute stop: 2× ATR(14) below entry
    atr14 = (df['high'] - df['low']).rolling(14).mean().iloc[-1]
    stop = latest_close - 2 * atr14
    target = latest_close + 4 * atr14  # 2:1 R:R
    
    signal = {
        "ticker": symbol,
        "strategy_id": STRATEGY_ID,
        "strategy_name": STRATEGY_NAME,
        "strategy_version": VERSION,
        "direction": "long",
        "entry_price": round(latest_close, 2),
        "stop_price": round(stop, 2),
        "target_price": round(target, 2),
        "asset_class": "stocks",
        "publish_channel": "stocks",
        "timeframe": "daily",
        "subperiod": "triple_rsi",
        "conditions": (
            f"• 5-day RSI: {latest_rsi:.1f} (oversold < 30)\n"
            f"• RSI falling for {FALLING_DAYS}+ days\n"
            f"• RSI 3 days ago < {RSI_PRIOR_MAX} (trend reset)\n"
            f"• SPY above 200-MA (${latest_ma:.0f}) — trend filter\n"
            f"• Exit: RSI crosses above {RSI_EXIT}"
        ),
        "date": str(df.index[-1])[:10],
        "rsi_value": round(latest_rsi, 1),
        "ma200_value": round(latest_ma, 0),
    }
    
    return [signal]


# ── CLI test ──
if __name__ == "__main__":
    import sys, os
    symbol = sys.argv[1] if len(sys.argv) > 1 else "SPY"
    path = f"/root/.hermes/market_data/{symbol}.parquet"
    
    if not os.path.exists(path):
        print(f"No data for {symbol}")
        sys.exit(1)
    
    df = pd.read_parquet(path)
    signals = scan(symbol, df)
    
    if signals:
        s = signals[0]
        print(f"✅ SIGNAL: {s['ticker']} {s['direction'].upper()}")
        print(f"   Entry:  ${s['entry_price']:,.2f}")
        print(f"   Stop:   ${s['stop_price']:,.2f}")
        print(f"   Target: ${s['target_price']:,.2f}")
        print(f"   RSI(5): {s['rsi_value']}")
        print(f"   200-MA: ${s['ma200_value']:,.0f}")
        print(f"   {s['conditions']}")
    else:
        rsi = _rsi(df['close'])
        print(f"No signal. Latest RSI(5): {rsi.iloc[-1]:.1f} (need < {RSI_OVERSOLD})")
        print(f"  RSI falling 3d: {(rsi.iloc[-1] < rsi.iloc[-2]) and (rsi.iloc[-2] < rsi.iloc[-3]) and (rsi.iloc[-3] < rsi.iloc[-4])}")