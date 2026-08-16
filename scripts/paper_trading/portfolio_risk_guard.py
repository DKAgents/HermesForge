#!/usr/bin/env python3
"""
portfolio_risk_guard.py — US-111: Portfolio Risk Guard

Pre-entry risk controls that protect the portfolio from:
1. Over-concentration in correlated assets (sector/asset class)
2. Daily drawdown cascades (circuit breaker after consecutive stops)
3. Excessive concurrent positions
4. Aggregate portfolio heat exceeding safe limits

Called BEFORE opening any new trade. If any check fails, the trade is blocked.

Usage:
    from portfolio_risk_guard import check_trade_allowed
    allowed, reason = check_trade_allowed(strategy_id, ticker, asset_class, risk_pct)
    if not allowed:
        skip_signal(reason)
"""

import sys
import pathlib
import json
from datetime import datetime, timezone, timedelta
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import trade_log

# ── Configuration ────────────────────────────────────────────────────────────

# ── Configuration (Testing Phase — loosened for data collection) ─────────────
# These limits are deliberately loose during the strategy validation phase.
# Once we have 50+ closed trades and know which strategies work, tighten to:
#   MAX_CONCURRENT_POSITIONS=8, MAX_PORTFOLIO_HEAT_PCT=7.0,
#   MAX_SAME_SECTOR=3, MAX_SAME_ASSET_CLASS=5, DAILY_MAX_STOPS=3

# Max concurrent open positions across all strategies
MAX_CONCURRENT_POSITIONS = 15

# Max aggregate portfolio heat (% of account at risk across all open trades)
MAX_PORTFOLIO_HEAT_PCT = 15.0

# Max trades in the same sector (disabled during testing — set high)
MAX_SAME_SECTOR = 999

# Max trades in the same asset class (disabled during testing)
MAX_SAME_ASSET_CLASS = 999

# Circuit breaker: disabled during testing (set high so it never trips)
DAILY_MAX_STOPS = 999
CIRCUIT_BREAKER_HOURS = 0  # No cool-down

# ── Sector classification ────────────────────────────────────────────────────

# Simple sector mapping for common tickers (no external API needed)
SECTOR_MAP = {
    # Tech
    "AAPL": "Technology", "MSFT": "Technology", "GOOGL": "Technology", "META": "Technology",
    "NVDA": "Technology", "AMZN": "Consumer Discretionary", "NFLX": "Communication",
    "TSLA": "Consumer Discretionary", "AMD": "Technology", "INTC": "Technology",
    "CSCO": "Technology", "ORCL": "Technology", "ADBE": "Technology", "CRM": "Technology",
    "AVGO": "Technology", "QCOM": "Technology", "TXN": "Technology", "AMAT": "Technology",
    "ANET": "Technology", "MU": "Technology", "NXPI": "Technology",
    # ETFs
    "SPY": "Index", "QQQ": "Index", "IWM": "Index", "DIA": "Index",
    "XLK": "Sector-Tech", "XLF": "Sector-Finance", "XLE": "Sector-Energy",
    "XLV": "Sector-Health", "XLI": "Sector-Industrial", "XLY": "Sector-Consumer",
    "XLP": "Sector-Staples", "XLU": "Sector-Utility", "XLB": "Sector-Materials",
    "XLC": "Sector-Comm", "XLRE": "Sector-REIT",
    # Finance
    "JPM": "Finance", "BAC": "Finance", "WFC": "Finance", "GS": "Finance",
    "MS": "Finance", "C": "Finance", "BLK": "Finance", "SCHW": "Finance",
    # Energy
    "XOM": "Energy", "CVX": "Energy", "COP": "Energy", "SLB": "Energy",
    # Healthcare
    "PFE": "Healthcare", "JNJ": "Healthcare", "UNH": "Healthcare", "ABT": "Healthcare",
    "LLY": "Healthcare", "MRK": "Healthcare",
    # Consumer
    "WMT": "Consumer Staples", "PG": "Consumer Staples", "KO": "Consumer Staples",
    "PEP": "Consumer Staples", "COST": "Consumer Staples", "MCD": "Consumer Discretionary",
    "NKE": "Consumer Discretionary", "SBUX": "Consumer Discretionary",
    # Industrial
    "BA": "Industrial", "CAT": "Industrial", "GE": "Industrial", "HON": "Industrial",
    "UPS": "Industrial", "FDX": "Industrial",
}

# Crypto sectors (all crypto is "Crypto" but we can sub-classify)
CRYPTO_SECTORS = {
    "BTC": "Crypto-Major", "ETH": "Crypto-Major",
    "SOL": "Crypto-L1", "AVAX": "Crypto-L1", "ATOM": "Crypto-L1",
    "ARB": "Crypto-L2", "OP": "Crypto-L2", "SUI": "Crypto-L1", "APT": "Crypto-L1",
    "TIA": "Crypto-L1", "SEI": "Crypto-L1", "INJ": "Crypto-DeFi",
    "LINK": "Crypto-Oracle", "DOGE": "Crypto-Meme", "RNDR": "Crypto-AI",
}

DAILY_STOPS_FILE = pathlib.Path.home() / ".hermes" / "market_data" / "daily_stops.json"


def _get_sector(ticker: str, asset_class: str) -> str:
    """Get sector classification for a ticker."""
    ticker_upper = ticker.upper()
    if asset_class == "crypto":
        return CRYPTO_SECTORS.get(ticker_upper, "Crypto-Other")
    return SECTOR_MAP.get(ticker_upper, "Unknown")


# ── Circuit breaker state ──────────────────────────────────────────────────

def _load_daily_stops() -> dict:
    """Load today's stop count from state file."""
    if not DAILY_STOPS_FILE.exists():
        return {"date": "", "stops": 0, "last_stop_time": ""}
    
    try:
        with open(DAILY_STOPS_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"date": "", "stops": 0, "last_stop_time": ""}


def _save_daily_stops(state: dict):
    """Save daily stop count to state file."""
    DAILY_STOPS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DAILY_STOPS_FILE, "w") as f:
        json.dump(state, f, indent=2)


def _get_today_str() -> str:
    """Get today's date string in UTC."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def record_stop_loss():
    """Call this when a trade hits its stop. Increments the daily stop counter.
    If DAILY_MAX_STOPS is reached, circuit breaker trips."""
    state = _load_daily_stops()
    today = _get_today_str()
    
    # Reset counter if it's a new day
    if state.get("date") != today:
        state = {"date": today, "stops": 0, "last_stop_time": ""}
    
    state["stops"] += 1
    state["last_stop_time"] = datetime.now(timezone.utc).isoformat()
    _save_daily_stops(state)
    
    if state["stops"] >= DAILY_MAX_STOPS:
        return True, f"⚠️ Circuit breaker tripped: {state['stops']} stops today"
    return False, ""


def _check_circuit_breaker() -> tuple:
    """Check if circuit breaker is currently active (within cool-down period)."""
    state = _load_daily_stops()
    today = _get_today_str()
    
    # Different day — reset
    if state.get("date") != today:
        return False, ""
    
    # Check if we've hit the limit
    if state.get("stops", 0) >= DAILY_MAX_STOPS:
        last_stop = state.get("last_stop_time", "")
        if last_stop:
            try:
                last_dt = datetime.fromisoformat(last_stop.replace("Z", ""))
                now = datetime.now(timezone.utc)
                elapsed = (now - last_dt).total_seconds() / 3600
                
                if elapsed < CIRCUIT_BREAKER_HOURS:
                    remaining = CIRCUIT_BREAKER_HOURS - elapsed
                    return True, (
                        f"🔴 Circuit breaker active: {state['stops']} stops today, "
                        f"{remaining:.1f}h cool-down remaining"
                    )
                else:
                    # Cool-down passed — allow trades again
                    return False, ""
            except (ValueError, TypeError):
                pass
    
    return False, ""


# ── Main risk check ────────────────────────────────────────────────────────

def check_trade_allowed(
    strategy_id: str,
    ticker: str,
    asset_class: str,
    risk_pct: float,
) -> tuple:
    """
    Check if a new trade is allowed under portfolio risk rules.
    
    Returns:
        (allowed: bool, reason: str)
        If not allowed, reason explains which check failed.
    """
    open_trades = trade_log.get_open_trades()
    
    # 1. Circuit breaker check
    cb_active, cb_reason = _check_circuit_breaker()
    if cb_active:
        return False, cb_reason
    
    # 2. Max concurrent positions
    if len(open_trades) >= MAX_CONCURRENT_POSITIONS:
        return False, (
            f"Max concurrent positions ({len(open_trades)}/{MAX_CONCURRENT_POSITIONS})"
        )
    
    # 3. Max portfolio heat
    current_heat = sum(float(t.get("position_size_pct", 0) or 0) for t in open_trades)
    if current_heat + risk_pct > MAX_PORTFOLIO_HEAT_PCT:
        return False, (
            f"Portfolio heat would exceed limit "
            f"({current_heat:.1f}% + {risk_pct:.1f}% > {MAX_PORTFOLIO_HEAT_PCT}%)"
        )
    
    # 4. Sector concentration
    new_sector = _get_sector(ticker, asset_class)
    sector_counts = defaultdict(int)
    asset_class_counts = defaultdict(int)
    
    for t in open_trades:
        t_ticker = t.get("ticker", "")
        t_asset = t.get("asset_class", "stock")
        t_sector = _get_sector(t_ticker, t_asset)
        sector_counts[t_sector] += 1
        asset_class_counts[t_asset] += 1
    
    if sector_counts[new_sector] >= MAX_SAME_SECTOR:
        return False, (
            f"Sector concentration limit: {new_sector} already has "
            f"{sector_counts[new_sector]}/{MAX_SAME_SECTOR} open trades"
        )
    
    # 5. Asset class concentration
    if asset_class_counts[asset_class] >= MAX_SAME_ASSET_CLASS:
        return False, (
            f"Asset class limit: {asset_class} already has "
            f"{asset_class_counts[asset_class]}/{MAX_SAME_ASSET_CLASS} open trades"
        )
    
    return True, "All risk checks passed"


def get_portfolio_status() -> dict:
    """Get current portfolio risk status for reporting."""
    open_trades = trade_log.get_open_trades()
    current_heat = sum(float(t.get("position_size_pct", 0) or 0) for t in open_trades)
    
    sector_counts = defaultdict(int)
    asset_class_counts = defaultdict(int)
    for t in open_trades:
        t_sector = _get_sector(t.get("ticker", ""), t.get("asset_class", "stock"))
        sector_counts[t_sector] += 1
        asset_class_counts[t.get("asset_class", "stock")] += 1
    
    cb_active, cb_reason = _check_circuit_breaker()
    daily_stops = _load_daily_stops()
    
    return {
        "open_positions": len(open_trades),
        "max_positions": MAX_CONCURRENT_POSITIONS,
        "current_heat_pct": round(current_heat, 2),
        "max_heat_pct": MAX_PORTFOLIO_HEAT_PCT,
        "sector_concentration": dict(sector_counts),
        "max_same_sector": MAX_SAME_SECTOR,
        "asset_class_concentration": dict(asset_class_counts),
        "max_same_asset_class": MAX_SAME_ASSET_CLASS,
        "circuit_breaker_active": cb_active,
        "circuit_breaker_reason": cb_reason,
        "daily_stops": daily_stops.get("stops", 0),
        "daily_max_stops": DAILY_MAX_STOPS,
    }


if __name__ == "__main__":
    print("=== US-111: Portfolio Risk Guard Test ===\n")
    status = get_portfolio_status()
    print(json.dumps(status, indent=2, default=str))
