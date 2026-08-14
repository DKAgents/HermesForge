#!/usr/bin/env python3
"""
compute_volatility.py — Realized Volatility vs VIX (Volatility Risk Premium)

Computes 20-day realized volatility from SPY OHLCV data and compares
to VIX (implied volatility). The spread between implied and realized
vol is a known signal:
  - VIX >> realized = fear priced in but not materialized = bullish
  - VIX << realized = complacency = bearish

Also computes realized vol for individual assets and crypto.

Usage:
    python3 compute_volatility.py
    python3 compute_volatility.py --json
"""

import sys
import json
import pathlib
import argparse
import pandas as pd
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "paper_trading"))
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "validation"))

CACHE_DIR = pathlib.Path.home() / ".hermes" / "market_data"


def _realized_vol(close: pd.Series, window: int = 20) -> float:
    """Annualized realized volatility from log returns."""
    log_ret = np.log(close / close.shift(1)).dropna()
    if len(log_ret) < window:
        return 0.0
    return float(log_ret.tail(window).std() * np.sqrt(252) * 100)


def compute_vol_risk_premium() -> dict:
    """
    Compute volatility risk premium (VIX - realized SPY vol).
    
    Returns:
    {
        "vix": float,                # current VIX
        "realized_vol_20d": float,   # 20-day annualized realized vol (SPY)
        "realized_vol_10d": float,   # 10-day
        "vol_risk_premium": float,   # VIX - realized_20d (positive = fear overpriced)
        "signal": str,               # "fear_overpriced" / "complacent" / "neutral"
        "spy_20d_vol": float,
        "qqq_20d_vol": float,
    }
    """
    from fetch_macro import load_macro
    from fetch_data import load_all
    
    macro = load_macro()
    stock_data = load_all()
    
    vix = float(macro["VIX"].iloc[-1]) if "VIX" in macro.columns else 0
    
    # SPY realized vol
    spy_rv_20 = 0
    spy_rv_10 = 0
    qqq_rv_20 = 0
    if "SPY" in stock_data:
        spy_rv_20 = _realized_vol(stock_data["SPY"]["close"], 20)
        spy_rv_10 = _realized_vol(stock_data["SPY"]["close"], 10)
    if "QQQ" in stock_data:
        qqq_rv_20 = _realized_vol(stock_data["QQQ"]["close"], 20)
    
    # Vol risk premium
    vrp = vix - spy_rv_20
    
    if vrp > 5:
        signal = "fear_overpriced"  # VIX much higher than realized = bullish
    elif vrp < -2:
        signal = "complacent"       # VIX lower than realized = bearish
    else:
        signal = "neutral"
    
    return {
        "vix": round(vix, 2),
        "realized_vol_20d": round(spy_rv_20, 2),
        "realized_vol_10d": round(spy_rv_10, 2),
        "vol_risk_premium": round(vrp, 2),
        "signal": signal,
        "spy_20d_vol": round(spy_rv_20, 2),
        "qqq_20d_vol": round(qqq_rv_20, 2),
    }


def get_crypto_volatility(coins: list = None) -> dict:
    """Compute realized volatility for crypto assets."""
    from fetch_crypto_data import load_all as load_crypto
    crypto_data = load_crypto()
    
    if coins is None:
        coins = list(crypto_data.keys())[:10]
    
    vol_dict = {}
    for coin in coins:
        if coin in crypto_data:
            rv = _realized_vol(crypto_data[coin]["close"], 20)
            vol_dict[coin] = round(rv, 2)
    
    return vol_dict


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Volatility risk premium")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    
    vrp = compute_vol_risk_premium()
    crypto_vol = get_crypto_volatility()
    
    if args.json:
        print(json.dumps({"vol_risk_premium": vrp, "crypto_volatility": crypto_vol}, indent=2))
    else:
        print("\n📊 **Volatility Risk Premium**\n")
        print(f"VIX (implied): {vrp['vix']}")
        print(f"SPY 20d Realized Vol: {vrp['realized_vol_20d']}%")
        print(f"SPY 10d Realized Vol: {vrp['realized_vol_10d']}%")
        print(f"Vol Risk Premium: {vrp['vol_risk_premium']}%")
        print(f"Signal: {vrp['signal']}")
        print(f"\nCrypto 20d Realized Vol:")
        for coin, vol in sorted(crypto_vol.items(), key=lambda x: x[1], reverse=True):
            print(f"  {coin}: {vol}%")
