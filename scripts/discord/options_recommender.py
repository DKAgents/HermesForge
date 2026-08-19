#!/usr/bin/env python3
"""
options_recommender.py — Generate options trade recommendations from stock signals.

Given a stock signal (ticker, direction, entry, stop, target), produces:
  1. Single-leg: Long Call (bullish) or Long Put (bearish) — 3 delta tiers
  2. Vertical spread: Bull Call Spread or Bear Put Spread (defined risk)
  3. Credit spread: Bull Put Spread or Bear Call Spread (income)

Optimizations:
  - Per-stock DTE based on ATR (volatility-adjusted)
  - Delta-based strike selection (Conservative ~0.70, Balanced ~0.50, Aggressive ~0.30)
  - Black-Scholes Greeks (delta, theta, gamma) for each recommendation
  - Earnings-aware expiry selection (warns if earnings falls within DTE window)
  - Liquidity filter (skip 0-volume/0-OI strikes)

Usage:
    from options_recommender import get_options_recommendations
    recs = get_options_recommendations('AMAT', 'long', 548.15, 476.42, 969.01)
"""

import datetime
import logging
import math
from typing import Optional

import yfinance as yf

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────

MIN_DTE = 20
MAX_DTE = 75
PREFERRED_DTE = 35

MAX_EXPIRIES_TO_CHECK = 3
MIN_STRIKE_LIQUIDITY = 0

# Delta targets for 3-tier strike selection
DELTA_CONSERVATIVE = 0.70  # ITM — higher probability, more expensive
DELTA_BALANCED = 0.50      # ATM — balanced
DELTA_AGGRESSIVE = 0.30    # OTM — cheaper, higher ROI, lower probability

# Risk-free rate for Black-Scholes (approximate, doesn't need to be precise
# for relative strike selection)
RISK_FREE_RATE = 0.045  # ~4.5%


# ── Black-Scholes ─────────────────────────────────────────────────────────────


def _norm_cdf(x: float) -> float:
    """Standard normal cumulative distribution function."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _norm_pdf(x: float) -> float:
    """Standard normal probability density function."""
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def _bs_d1(S: float, K: float, T: float, r: float, sigma: float) -> float:
    if T <= 0 or sigma <= 0:
        return 0.0
    return (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))


def _bs_delta(S: float, K: float, T: float, r: float, sigma: float,
              option_type: str = "call") -> float:
    """Black-Scholes delta. Returns positive for calls, negative for puts."""
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        # Fallback: moneyness-based estimate
        if option_type == "call":
            moneyness = S / K
            return max(0.01, min(0.99, moneyness - 0.15))
        else:
            moneyness = K / S
            return -max(0.01, min(0.99, moneyness - 0.15))
    d1 = _bs_d1(S, K, T, r, sigma)
    if option_type == "call":
        return _norm_cdf(d1)
    else:
        return _norm_cdf(d1) - 1.0


def _bs_theta(S: float, K: float, T: float, r: float, sigma: float,
              option_type: str = "call") -> float:
    """Black-Scholes theta (per day, not per year)."""
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return 0.0
    d1 = _bs_d1(S, K, T, r, sigma)
    d2 = d1 - sigma * math.sqrt(T)
    theta_annual = (
        -(S * _norm_pdf(d1) * sigma) / (2.0 * math.sqrt(T))
        - r * K * _norm_cdf(d2 if option_type == "call" else -d2)
    ) if option_type == "call" else (
        -(S * _norm_pdf(d1) * sigma) / (2.0 * math.sqrt(T))
        + r * K * _norm_cdf(-d2)
    )
    return theta_annual / 365.0


def _bs_gamma(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Black-Scholes gamma."""
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return 0.0
    d1 = _bs_d1(S, K, T, r, sigma)
    return _norm_pdf(d1) / (S * sigma * math.sqrt(T))


def _estimate_iv(price: float, S: float, K: float, T: float, r: float,
                 option_type: str = "call") -> float:
    """
    Simple IV estimation using bisection search on Black-Scholes.
    Falls back to a heuristic if search fails.
    """
    if price <= 0 or T <= 0 or S <= 0 or K <= 0:
        return 0.30  # default 30% IV

    lo, hi = 0.01, 5.0
    mid = 0.30  # default fallback
    for _ in range(50):
        mid = (lo + hi) / 2.0
        d1 = _bs_d1(S, K, T, r, mid)
        d2 = d1 - mid * math.sqrt(T)
        if option_type == "call":
            bs_price = S * _norm_cdf(d1) - K * math.exp(-r * T) * _norm_cdf(d2)
        else:
            bs_price = K * math.exp(-r * T) * _norm_cdf(-d2) - S * _norm_cdf(-d1)
        if abs(bs_price - price) < 0.01:
            return mid
        if bs_price < price:
            lo = mid
        else:
            hi = mid
    return mid  # return best estimate


# ── DTE Optimization ──────────────────────────────────────────────────────────


def _compute_optimal_dte(ticker: str, current_price: float) -> int:
    """Compute optimal DTE based on the stock's volatility profile."""
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="20d")
        if len(hist) > 0:
            high_low = (hist["High"] - hist["Low"]).mean()
            atr_pct = (high_low / current_price) * 100 if current_price else 2.0
        else:
            atr_pct = 2.0
    except Exception:
        atr_pct = 2.0

    base_dte = int(10 * 1.5 * 7 / 5)  # = 21 calendar days

    if atr_pct > 3.0:
        vol_adj = 10
    elif atr_pct > 1.5:
        vol_adj = 5
    else:
        vol_adj = 0

    optimal = base_dte + vol_adj
    return max(MIN_DTE, min(optimal, MAX_DTE))


# ── Earnings Awareness ────────────────────────────────────────────────────────


def _get_next_earnings_date(ticker: str) -> Optional[datetime.datetime]:
    """
    Get the next earnings date for a ticker.
    Returns None if no earnings upcoming or data unavailable.
    """
    try:
        t = yf.Ticker(ticker)
        cal = t.calendar
        if cal is None:
            return None
        # yfinance calendar is a dict with 'Earnings Date' key
        if isinstance(cal, dict):
            earnings_dates = cal.get("Earnings Date", [])
        elif hasattr(cal, "get"):
            earnings_dates = cal.get("Earnings Date", [])
        else:
            return None

        if earnings_dates and len(earnings_dates) > 0:
            ed = earnings_dates[0]
            if isinstance(ed, datetime.datetime):
                return ed
            elif isinstance(ed, datetime.date):
                return datetime.datetime(ed.year, ed.month, ed.day)
            # Try parsing string
            if isinstance(ed, str):
                return datetime.datetime.strptime(ed[:10], "%Y-%m-%d")
        return None
    except Exception:
        return None


def _check_earnings_in_window(ticker: str, exp_date: datetime.datetime) -> dict:
    """
    Check if earnings falls between now and expiry.
    Returns {has_earnings: bool, earnings_date: str|None, warning: str|None}
    """
    next_earnings = _get_next_earnings_date(ticker)
    if next_earnings is None:
        return {"has_earnings": False, "earnings_date": None, "warning": None}

    now = datetime.datetime.now()
    if now < next_earnings <= exp_date:
        ed_str = next_earnings.strftime("%Y-%m-%d")
        days_to_earnings = (next_earnings - now).days
        warning = f"⚠️ Earnings {ed_str} ({days_to_earnings}d) before expiry"
        return {
            "has_earnings": True,
            "earnings_date": ed_str,
            "warning": warning,
        }
    return {"has_earnings": False, "earnings_date": None, "warning": None}


# ── Expiry Selection ──────────────────────────────────────────────────────────


def _pick_best_expiry(expirations: tuple, optimal_dte: int = None,
                      ticker: str = None) -> list[str]:
    """
    Pick 1-3 expirations near the optimal DTE.
    If earnings falls within an expiry's window, deprioritize it (push further out).
    """
    target_dte = optimal_dte if optimal_dte else PREFERRED_DTE
    today = datetime.datetime.now()
    candidates = []

    for exp_str in expirations:
        try:
            exp_date = datetime.datetime.strptime(exp_str, "%Y-%m-%d")
        except ValueError:
            continue
        dte = (exp_date - today).days
        if MIN_DTE <= dte <= MAX_DTE:
            # Check for earnings — add penalty if earnings falls in window
            earnings_penalty = 0
            if ticker:
                earnings_info = _check_earnings_in_window(ticker, exp_date)
                if earnings_info["has_earnings"]:
                    # Deprioritize expiries that contain earnings (binary risk)
                    earnings_penalty = 10  # push ranking further away
            candidates.append((exp_str, dte, earnings_penalty))

    # Sort by (penalty + distance from target DTE)
    candidates.sort(key=lambda x: (x[2], abs(x[1] - target_dte)))
    return [exp_str for exp_str, _, _ in candidates[:MAX_EXPIRIES_TO_CHECK]]


# ── Strike Selection ──────────────────────────────────────────────────────────


def _find_atm_strike(chain_df, target_price: float):
    if len(chain_df) == 0:
        return None
    idx = (chain_df["strike"] - target_price).abs().argsort().iloc[0]
    return float(chain_df.iloc[idx]["strike"])


def _find_strike_at_price(chain_df, price: float, direction: str = "above"):
    if len(chain_df) == 0:
        return None
    if direction == "above":
        filtered = chain_df[chain_df["strike"] >= price]
        if len(filtered) == 0:
            filtered = chain_df
    else:
        filtered = chain_df[chain_df["strike"] <= price]
        if len(filtered) == 0:
            filtered = chain_df
    idx = (filtered["strike"] - price).abs().argsort().iloc[0]
    return float(filtered.iloc[idx]["strike"])


def _find_strike_by_delta(chain_df, target_delta: float, S: float, T: float,
                          r: float, option_type: str = "call"):
    """
    Find the strike with delta closest to target_delta.
    Uses IV from the chain when available, falls back to estimated IV.
    Returns (strike, contract_row, actual_delta, iv_used).
    """
    if len(chain_df) == 0:
        return None, None, None, None

    best = None
    best_delta_diff = float("inf")

    for _, contract in chain_df.iterrows():
        strike = float(contract["strike"])
        chain_iv = float(contract.get("impliedVolatility", 0) or 0)

        # Use chain IV if reasonable, otherwise estimate from price
        if 0.05 < chain_iv < 5.0:
            iv = chain_iv
        else:
            price = _mid_price(contract)
            if price > 0:
                iv = _estimate_iv(price, S, strike, T, r, option_type)
            else:
                iv = 0.30  # default

        delta = abs(_bs_delta(S, strike, T, r, iv, option_type))

        # Skip 0-delta (deep OTM/ITM with bad data)
        if delta < 0.01 or delta > 0.99:
            continue

        diff = abs(delta - target_delta)
        if diff < best_delta_diff:
            best_delta_diff = diff
            best = (strike, contract, delta, iv)

    return best if best else (None, None, None, None)


def _get_contract(chain_df, strike: float):
    matches = chain_df[chain_df["strike"] == strike]
    if len(matches) == 0:
        return None
    return matches.iloc[0]


def _is_liquid(contract) -> bool:
    vol = float(contract.get("volume", 0) or 0)
    oi = float(contract.get("openInterest", 0) or 0)
    return (vol + oi) > MIN_STRIKE_LIQUIDITY


def _mid_price(contract) -> float:
    bid = float(contract.get("bid", 0) or 0)
    ask = float(contract.get("ask", 0) or 0)
    if bid > 0 and ask > 0:
        return (bid + ask) / 2
    return float(contract.get("lastPrice", 0) or 0)


# ── Main Recommendation Engine ────────────────────────────────────────────────


def get_options_recommendations(
    ticker: str,
    direction: str,
    entry_price: float,
    stop_price: float,
    target_price: float,
) -> list[dict]:
    """
    Generate options recommendations for a stock signal.

    Returns list of dicts, one per expiry, each containing:
        {
            'expiry': str, 'dte': int,
            'earnings_warning': str|None,
            'single_leg': {type, strike, delta, price, theta, max_loss, ...},
            'debit_spread': {type, long_strike, short_strike, net_debit, ...},
            'credit_spread': {type, short_strike, long_strike, net_credit, ...},
        }
    """
    try:
        t = yf.Ticker(ticker)
        expirations = t.options
        info = t.fast_info
        current_price = info.get("lastPrice") or info.get("previousClose") or entry_price
    except Exception as e:
        logger.warning(f"Could not fetch options for {ticker}: {e}")
        return []

    if not expirations:
        return []

    optimal_dte = _compute_optimal_dte(ticker, current_price)
    logger.debug(f"{ticker} optimal DTE: {optimal_dte}")

    expiries = _pick_best_expiry(expirations, optimal_dte, ticker)
    if not expiries:
        if len(expirations) > 2:
            expiries = [expirations[2]]
        else:
            expiries = [expirations[0]]

    today = datetime.datetime.now()
    results = []

    for exp_str in expiries:
        try:
            chain = t.option_chain(exp_str)
            exp_date = datetime.datetime.strptime(exp_str, "%Y-%m-%d")
            dte = (exp_date - today).days
        except Exception as e:
            logger.warning(f"Could not fetch chain for {ticker} {exp_str}: {e}")
            continue

        calls = chain.calls
        puts = chain.puts

        # Time to expiry in years for Black-Scholes
        T = max(dte, 1) / 365.0

        # Check earnings
        earnings_info = _check_earnings_in_window(ticker, exp_date)

        if direction == "long":
            rec = _build_bullish_recs(
                calls, puts, entry_price, stop_price, target_price,
                exp_str, dte, current_price, T, earnings_info
            )
        else:
            rec = _build_bearish_recs(
                calls, puts, entry_price, stop_price, target_price,
                exp_str, dte, current_price, T, earnings_info
            )

        if rec:
            results.append(rec)

    return results


def _build_bullish_recs(calls, puts, entry, stop, target, exp_str, dte,
                        current_price, T, earnings_info):
    """Build bullish options recommendations with delta-based strike selection."""
    r = RISK_FREE_RATE

    # ── Single leg: 3 delta tiers ────────────────────────────────────────
    single_legs = []

    for label, target_delta in [
        ("Conservative", DELTA_CONSERVATIVE),
        ("Balanced", DELTA_BALANCED),
        ("Aggressive", DELTA_AGGRESSIVE),
    ]:
        strike, contract, actual_delta, iv = _find_strike_by_delta(
            calls, target_delta, current_price, T, r, "call"
        )
        if contract is None or not _is_liquid(contract):
            continue

        call_price = _mid_price(contract)
        theta = _bs_theta(current_price, strike, T, r, iv, "call")

        single_legs.append({
            "tier": label,
            "type": "Long Call",
            "strike": strike,
            "delta": round(actual_delta, 2),
            "price": round(call_price, 2),
            "theta": round(theta, 2),
            "max_loss": round(call_price * 100, 2),
            "max_profit": "Unlimited",
            "breakeven": round(strike + call_price, 2),
            "iv": round(iv * 100, 1),
        })

    # If delta-based selection found nothing, fall back to ATM
    if not single_legs:
        atm_strike = _find_atm_strike(calls, entry)
        atm_call = _get_contract(calls, atm_strike)
        if atm_call and _is_liquid(atm_call):
            call_price = _mid_price(atm_call)
            chain_iv = float(atm_call.get("impliedVolatility", 0) or 0)
            iv = chain_iv if 0.05 < chain_iv < 5.0 else _estimate_iv(
                call_price, current_price, atm_strike, T, r, "call")
            delta = _bs_delta(current_price, atm_strike, T, r, iv, "call")
            theta = _bs_theta(current_price, atm_strike, T, r, iv, "call")
            single_legs.append({
                "tier": "Balanced",
                "type": "Long Call",
                "strike": float(atm_strike),
                "delta": round(abs(delta), 2),
                "price": round(call_price, 2),
                "theta": round(theta, 2),
                "max_loss": round(call_price * 100, 2),
                "max_profit": "Unlimited",
                "breakeven": round(atm_strike + call_price, 2),
                "iv": round(iv * 100, 1),
            })

    # ── Debit spread: Bull Call Spread ────────────────────────────────────
    # Long at balanced delta (~0.50), short at target price (~0.20-0.30 delta)
    long_strike, long_call, _, long_iv = _find_strike_by_delta(
        calls, DELTA_BALANCED, current_price, T, r, "call"
    )
    short_strike = _find_strike_at_price(calls, target, "above")
    short_call = _get_contract(calls, short_strike) if short_strike else None

    debit_spread = None
    if long_call is not None and short_call is not None:
        long_price = _mid_price(long_call)
        short_price = _mid_price(short_call)
        net_debit = long_price - short_price
        width = short_strike - long_strike
        max_profit = (width - net_debit) * 100
        max_loss = net_debit * 100

        if net_debit > 0:
            # Compute net delta and theta
            short_iv = float(short_call.get("impliedVolatility", 0) or 0)
            if not (0.05 < short_iv < 5.0):
                short_iv = _estimate_iv(short_price, current_price, short_strike, T, r, "call")
            long_delta = _bs_delta(current_price, long_strike, T, r, long_iv, "call")
            short_delta = _bs_delta(current_price, short_strike, T, r, short_iv, "call")
            net_delta = abs(long_delta) - abs(short_delta)
            long_theta = _bs_theta(current_price, long_strike, T, r, long_iv, "call")
            short_theta = _bs_theta(current_price, short_strike, T, r, short_iv, "call")
            net_theta = long_theta + short_theta  # short call theta is positive

            debit_spread = {
                "type": "Bull Call Spread",
                "long_strike": float(long_strike),
                "short_strike": float(short_strike),
                "net_debit": round(net_debit, 2),
                "max_loss": round(max_loss, 2),
                "max_profit": round(max_profit, 2),
                "breakeven": round(long_strike + net_debit, 2),
                "roi": round(max_profit / max_loss * 100, 1) if max_loss > 0 else 0,
                "net_delta": round(net_delta, 2),
                "net_theta": round(net_theta, 2),
            }

    # ── Credit spread: Bull Put Spread ───────────────────────────────────
    short_put_strike = _find_strike_at_price(puts, stop, "above")
    long_put_strike = _find_strike_at_price(puts, stop * 0.90, "below")

    credit_spread = None
    short_put = _get_contract(puts, short_put_strike) if short_put_strike else None
    long_put = _get_contract(puts, long_put_strike) if long_put_strike else None

    if short_put is not None and long_put is not None:
        short_price = _mid_price(short_put)
        long_price = _mid_price(long_put)
        net_credit = short_price - long_price
        width = short_put_strike - long_put_strike
        max_loss = (width - net_credit) * 100
        max_profit = net_credit * 100

        if net_credit > 0:
            credit_spread = {
                "type": "Bull Put Spread",
                "short_strike": float(short_put_strike),
                "long_strike": float(long_put_strike),
                "net_credit": round(net_credit, 2),
                "max_loss": round(max_loss, 2),
                "max_profit": round(max_profit, 2),
                "breakeven": round(short_put_strike - net_credit, 2),
                "roi": round(max_profit / max_loss * 100, 1) if max_loss > 0 else 0,
            }

    if not any([single_legs, debit_spread, credit_spread]):
        return None

    return {
        "expiry": exp_str,
        "dte": dte,
        "earnings_warning": earnings_info.get("warning"),
        "single_legs": single_legs,
        "debit_spread": debit_spread,
        "credit_spread": credit_spread,
    }


def _build_bearish_recs(calls, puts, entry, stop, target, exp_str, dte,
                        current_price, T, earnings_info):
    """Build bearish options recommendations with delta-based strike selection."""
    r = RISK_FREE_RATE

    # ── Single leg: 3 delta tiers (puts have negative delta, use abs) ─────
    single_legs = []

    for label, target_delta in [
        ("Conservative", DELTA_CONSERVATIVE),
        ("Balanced", DELTA_BALANCED),
        ("Aggressive", DELTA_AGGRESSIVE),
    ]:
        strike, contract, actual_delta, iv = _find_strike_by_delta(
            puts, target_delta, current_price, T, r, "put"
        )
        if contract is None or not _is_liquid(contract):
            continue

        put_price = _mid_price(contract)
        theta = _bs_theta(current_price, strike, T, r, iv, "put")

        single_legs.append({
            "tier": label,
            "type": "Long Put",
            "strike": strike,
            "delta": round(actual_delta, 2),
            "price": round(put_price, 2),
            "theta": round(theta, 2),
            "max_loss": round(put_price * 100, 2),
            "max_profit": round((strike - put_price) * 100, 2),
            "breakeven": round(strike - put_price, 2),
            "iv": round(iv * 100, 1),
        })

    # Fallback to ATM
    if not single_legs:
        atm_strike = _find_atm_strike(puts, entry)
        atm_put = _get_contract(puts, atm_strike)
        if atm_put and _is_liquid(atm_put):
            put_price = _mid_price(atm_put)
            chain_iv = float(atm_put.get("impliedVolatility", 0) or 0)
            iv = chain_iv if 0.05 < chain_iv < 5.0 else _estimate_iv(
                put_price, current_price, atm_strike, T, r, "put")
            delta = _bs_delta(current_price, atm_strike, T, r, iv, "put")
            theta = _bs_theta(current_price, atm_strike, T, r, iv, "put")
            single_legs.append({
                "tier": "Balanced",
                "type": "Long Put",
                "strike": float(atm_strike),
                "delta": round(abs(delta), 2),
                "price": round(put_price, 2),
                "theta": round(theta, 2),
                "max_loss": round(put_price * 100, 2),
                "max_profit": round((atm_strike - put_price) * 100, 2),
                "breakeven": round(atm_strike - put_price, 2),
                "iv": round(iv * 100, 1),
            })

    # ── Debit spread: Bear Put Spread ─────────────────────────────────────
    long_strike, long_put, _, long_iv = _find_strike_by_delta(
        puts, DELTA_BALANCED, current_price, T, r, "put"
    )
    short_strike = _find_strike_at_price(puts, target, "below")
    short_put = _get_contract(puts, short_strike) if short_strike else None

    debit_spread = None
    if long_put is not None and short_put is not None:
        long_price = _mid_price(long_put)
        short_price = _mid_price(short_put)
        net_debit = long_price - short_price
        width = long_strike - short_strike
        max_profit = (width - net_debit) * 100
        max_loss = net_debit * 100

        if net_debit > 0:
            debit_spread = {
                "type": "Bear Put Spread",
                "long_strike": float(long_strike),
                "short_strike": float(short_strike),
                "net_debit": round(net_debit, 2),
                "max_loss": round(max_loss, 2),
                "max_profit": round(max_profit, 2),
                "breakeven": round(long_strike - net_debit, 2),
                "roi": round(max_profit / max_loss * 100, 1) if max_loss > 0 else 0,
            }

    # ── Credit spread: Bear Call Spread ──────────────────────────────────
    short_call_strike = _find_strike_at_price(calls, stop, "above")
    long_call_strike = _find_strike_at_price(calls, stop * 1.10, "above")

    credit_spread = None
    short_call = _get_contract(calls, short_call_strike) if short_call_strike else None
    long_call = _get_contract(calls, long_call_strike) if long_call_strike else None

    if short_call is not None and long_call is not None:
        short_price = _mid_price(short_call)
        long_price = _mid_price(long_call)
        net_credit = short_price - long_price
        width = long_call_strike - short_call_strike
        max_loss = (width - net_credit) * 100
        max_profit = net_credit * 100

        if net_credit > 0:
            credit_spread = {
                "type": "Bear Call Spread",
                "short_strike": float(short_call_strike),
                "long_strike": float(long_call_strike),
                "net_credit": round(net_credit, 2),
                "max_loss": round(max_loss, 2),
                "max_profit": round(max_profit, 2),
                "breakeven": round(short_call_strike + net_credit, 2),
                "roi": round(max_profit / max_loss * 100, 1) if max_loss > 0 else 0,
            }

    if not any([single_legs, debit_spread, credit_spread]):
        return None

    return {
        "expiry": exp_str,
        "dte": dte,
        "earnings_warning": earnings_info.get("warning"),
        "single_legs": single_legs,
        "debit_spread": debit_spread,
        "credit_spread": credit_spread,
    }


def format_options_embed(recs: list[dict]) -> str:
    """Format recommendations as a compact text block for Discord embeds."""
    if not recs:
        return "No liquid options found for this signal."

    lines = []
    for rec in recs[:2]:  # Show up to 2 expiries
        header = f"**{rec['expiry']} ({rec['dte']} DTE)**"
        if rec.get("earnings_warning"):
            header += f" {rec['earnings_warning']}"
        lines.append(header)

        # Single-leg: show best tier (Balanced) + Aggressive for comparison
        if rec.get("single_legs"):
            for leg in rec["single_legs"][:2]:  # Show top 2 tiers
                lines.append(
                    f"  • {leg['tier']} {leg['type']}: Strike {leg['strike']} "
                    f"Δ{leg['delta']:.2f} @ ${leg['price']:.2f} "
                    f"(θ${leg['theta']:.2f}/d, Max Loss ${leg['max_loss']:.0f}, "
                    f"IV {leg.get('iv', '?')}%)"
                )

        if rec.get("debit_spread"):
            d = rec["debit_spread"]
            greeks = ""
            if d.get("net_delta") is not None:
                greeks = f" Δ{d['net_delta']:.2f} θ${d.get('net_theta', 0):.2f}/d"
            lines.append(
                f"  • {d['type']}: {d['long_strike']}/{d['short_strike']} "
                f"Net Debit ${d['net_debit']:.2f}{greeks} "
                f"(Max Profit ${d['max_profit']:.0f}, Max Loss ${d['max_loss']:.0f}, "
                f"ROI {d['roi']}%)"
            )

        if rec.get("credit_spread"):
            c = rec["credit_spread"]
            lines.append(
                f"  • {c['type']}: {c['short_strike']}/{c['long_strike']} "
                f"Net Credit ${c['net_credit']:.2f} "
                f"(Max Profit ${c['max_profit']:.0f}, Max Loss ${c['max_loss']:.0f}, "
                f"ROI {c['roi']}%)"
            )
        lines.append("")

    return "\n".join(lines)