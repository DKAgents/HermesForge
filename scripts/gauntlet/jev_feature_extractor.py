#!/usr/bin/env python3
"""
jev_feature_extractor.py — Feature engineering for Jev ML feedback loop

Extracts signal-time features from trades.csv for model training.
All features must be computable at signal entry time — no lookahead.

Features extracted:
  - strategy_id (one-hot encoded)
  - asset_class (stock/crypto)
  - direction (long/short)
  - R:R ratio (target distance / stop distance)
  - position_size_pct
  - quality_tier (low/medium/high → 1/2/3)
  - day_of_week (0=Mon..6=Sun)
  - hour_of_day (0-23)
  - regime (numerical: bear=-1, neutral=0, bull=1)
  - vix (float at entry)
  - dxy (float at entry)
  - fear_greed (float 0-100)
  - confirmation_level
  - weekly_gate_scaling
  - ticker_encoded (frequency-based hash for dimensionality control)

Target: gauntlet_r (cost-adjusted R multiple), or binary win/loss.

Usage:
    from jev_feature_extractor import extract_features, extract_signal_features
"""

from __future__ import annotations

import csv
import os
import hashlib
from collections import Counter
from datetime import datetime
from typing import Optional

import numpy as np

TRADES_CSV = os.path.join(os.path.dirname(__file__), "..", "paper_trading", "trades.csv")


def _load_rows() -> list[dict]:
    """Load all closed trades with parsable fields."""
    path = os.path.normpath(TRADES_CSV)
    if not os.path.exists(path):
        return []
    
    rows = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            if row.get("status") != "closed":
                continue
            # Must have gauntlet_r or r_multiple
            gr = row.get("gauntlet_r", "").strip()
            try:
                r = float(gr) if gr else float(row.get("r_multiple", 0))
            except (ValueError, TypeError):
                continue
            row["_r"] = r
            rows.append(row)
    
    return rows


def _parse_regime(regime_str: str) -> float:
    """Convert regime string to numerical score."""
    if not regime_str:
        return 0.0
    r = regime_str.lower()
    if "bull" in r:
        return 1.0
    elif "bear" in r:
        return -1.0
    elif "neutral" in r or "sideways" in r or "choppy" in r:
        return 0.0
    return 0.0


def _safe_float(val: str, default: float = 0.0) -> float:
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _encode_ticker(ticker: str, ticker_freq: Counter) -> int:
    """Encode ticker as a frequency-based hash (0-99)."""
    if not ticker:
        return 0
    h = int(hashlib.md5(ticker.encode()).hexdigest()[:4], 16)
    return h % 100


def extract_features(rows: list[dict] = None) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """
    Extract feature matrix X and target vector y from closed trades.
    
    Returns:
        X: (n_trades, n_features) numpy array
        y: (n_trades,) numpy array of gauntlet_r values
        feature_names: list of feature column names
    """
    if rows is None:
        rows = _load_rows()
    
    if not rows:
        return np.array([]).reshape(0, 0), np.array([]), []
    
    # Count ticker frequencies for encoding
    ticker_freq: Counter = Counter()
    for row in rows:
        ticker_freq[row.get("ticker", "")] += 1
    
    # Strategy one-hot encoding
    strategies = sorted(set(row.get("strategy_id", "unknown") for row in rows))
    strategy_idx = {s: i for i, s in enumerate(strategies)}
    
    X_list = []
    y_list = []
    
    for row in rows:
        features = {}
        
        # Strategy (one-hot)
        sid = row.get("strategy_id", "unknown")
        for s in strategies:
            features[f"strat_{s}"] = 1.0 if s == sid else 0.0
        
        # Asset class
        ac = row.get("asset_class", "stock")
        features["asset_crypto"] = 1.0 if ac == "crypto" else 0.0
        features["asset_stock"] = 1.0 if ac == "stock" else 0.0
        
        # Direction
        d = row.get("direction", "long")
        features["dir_long"] = 1.0 if d == "long" else 0.0
        features["dir_short"] = 1.0 if d == "short" else 0.0
        
        # R:R ratio
        entry = _safe_float(row.get("entry_price", "0"))
        stop = _safe_float(row.get("stop_price", "0"))
        target = _safe_float(row.get("target_price", "0"))
        if stop != entry and stop != 0:
            rr = abs((target - entry) / (entry - stop)) if d == "long" else abs((target - entry) / (stop - entry))
            rr = min(rr, 10.0)  # cap extreme ratios
        else:
            rr = 2.0  # default assumption
        features["rr_ratio"] = rr
        
        # Position size
        features["pos_size_pct"] = _safe_float(row.get("position_size_pct", "1"), 1.0)
        
        # Quality tier
        qt = row.get("quality_tier", "medium").lower()
        tier_map = {"low": 1.0, "medium": 2.0, "high": 3.0}
        features["quality_tier"] = tier_map.get(qt, 2.0)
        
        # Time features
        try:
            entry_str = row["entry_date"].replace(" ", "T").replace("Z", "+00:00")
            entry_dt = datetime.fromisoformat(entry_str)
            features["day_of_week"] = float(entry_dt.weekday())  # 0=Mon..6=Sun
            features["hour_of_day"] = float(entry_dt.hour)
        except (ValueError, KeyError):
            features["day_of_week"] = 3.0  # Wednesday default
            features["hour_of_day"] = 12.0
        
        # Regime
        features["regime_stock"] = _parse_regime(row.get("regime_stock", ""))
        features["regime_crypto"] = _parse_regime(row.get("regime_crypto", ""))
        features["regime_overall"] = _parse_regime(row.get("regime_overall", ""))
        
        # Market indicators
        features["vix"] = _safe_float(row.get("vix", "20"), 20.0)
        features["dxy"] = _safe_float(row.get("dxy", "100"), 100.0)
        features["fear_greed"] = _safe_float(row.get("fear_greed", "50"), 50.0)
        
        # Signal quality
        features["confirmation_level"] = _safe_float(row.get("confirmation_level", "0"), 0.0)
        features["weekly_gate_scaling"] = _safe_float(row.get("weekly_gate_scaling", "1"), 1.0)
        
        # Ticker encoding
        features["ticker_id"] = float(_encode_ticker(row.get("ticker", ""), ticker_freq))
        
        X_list.append(list(features.values()))
        y_list.append(row["_r"])
    
    feature_names = list(features.keys())
    return np.array(X_list, dtype=np.float32), np.array(y_list, dtype=np.float32), feature_names


def extract_signal_features(signal: dict) -> np.ndarray:
    """
    Extract the same feature vector for a live signal (single row).
    Must match the column order from extract_features().
    """
    # This mirrors the feature extraction above for a single signal
    # We use the same keys and order
    rows = _load_rows()
    strategies = sorted(set(row.get("strategy_id", "unknown") for row in rows))
    ticker_freq = Counter(row.get("ticker", "") for row in rows)
    
    features = {}
    sid = signal.get("strategy_id", "unknown")
    for s in strategies:
        features[f"strat_{s}"] = 1.0 if s == sid else 0.0
    
    ac = signal.get("asset_class", "stock")
    features["asset_crypto"] = 1.0 if ac == "crypto" else 0.0
    features["asset_stock"] = 1.0 if ac == "stock" else 0.0
    
    d = signal.get("direction", "long")
    features["dir_long"] = 1.0 if d == "long" else 0.0
    features["dir_short"] = 1.0 if d == "short" else 0.0
    
    entry = _safe_float(str(signal.get("entry_price", "0")))
    stop = _safe_float(str(signal.get("stop_price", "0")))
    target = _safe_float(str(signal.get("target_price", "0")))
    if stop != entry and stop != 0:
        rr = abs((target - entry) / (entry - stop)) if d == "long" else abs((target - entry) / (stop - entry))
        rr = min(rr, 10.0)
    else:
        rr = 2.0
    features["rr_ratio"] = rr
    
    features["pos_size_pct"] = _safe_float(str(signal.get("position_size_pct", "1")), 1.0)
    
    qt = signal.get("quality_tier", "medium").lower() if isinstance(signal.get("quality_tier"), str) else "medium"
    tier_map = {"low": 1.0, "medium": 2.0, "high": 3.0}
    features["quality_tier"] = tier_map.get(qt, 2.0)
    
    # Time — use current time for live signals
    now = datetime.now()
    features["day_of_week"] = float(now.weekday())
    features["hour_of_day"] = float(now.hour)
    
    # Regime — from signal or defaults
    features["regime_stock"] = _parse_regime(signal.get("regime_stock", "") if isinstance(signal.get("regime_stock"), str) else "")
    features["regime_crypto"] = _parse_regime(signal.get("regime_crypto", "") if isinstance(signal.get("regime_crypto"), str) else "")
    features["regime_overall"] = _parse_regime(signal.get("regime_overall", "") if isinstance(signal.get("regime_overall"), str) else "")
    
    features["vix"] = _safe_float(str(signal.get("vix", "20")), 20.0)
    features["dxy"] = _safe_float(str(signal.get("dxy", "100")), 100.0)
    features["fear_greed"] = _safe_float(str(signal.get("fear_greed", "50")), 50.0)
    features["confirmation_level"] = _safe_float(str(signal.get("confirmation_level", "0")), 0.0)
    features["weekly_gate_scaling"] = _safe_float(str(signal.get("weekly_gate_scaling", "1")), 1.0)
    features["ticker_id"] = float(_encode_ticker(signal.get("ticker", ""), ticker_freq))
    
    return np.array(list(features.values()), dtype=np.float32)


# ── Quick test ──

if __name__ == "__main__":
    X, y, names = extract_features()
    print(f"Features: {len(names)}")
    print(f"Samples: {len(y)}")
    print(f"Target mean: {y.mean():.4f}, std: {y.std():.4f}")
    print(f"Target range: [{y.min():.2f}, {y.max():.2f}]")
    print(f"\nTop 5 features by name:")
    for n in names[:5]:
        print(f"  {n}")
    print(f"  ... ({len(names)} total)")
    
    # Test live signal extraction
    sig = {
        "strategy_id": "STR-Q-liquidity-sweep",
        "ticker": "BTC",
        "direction": "long",
        "entry_price": "87200",
        "stop_price": "86900",
        "target_price": "88100",
        "asset_class": "crypto",
    }
    x_live = extract_signal_features(sig)
    print(f"\nLive signal vector: {len(x_live)} features, shape={x_live.shape}")