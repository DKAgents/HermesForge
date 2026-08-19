#!/usr/bin/env python3
"""
options_recommender.py — Generate options trade recommendations from stock signals.

Given a stock signal (ticker, direction, entry, stop, target), produces:
  1. Single-leg: Long Call (bullish) or Long Put (bearish)
  2. Vertical spread: Bull Call Spread or Bear Put Spread (defined risk)
  3. Credit spread: Bull Put Spread or Bear Call Spread (income)

Selection logic:
  - Expiry: 30-45 DTE (sweet spot for swing trades — enough theta to not
    decay too fast, but short enough to keep cost reasonable)
  - Strike selection:
    - Long leg: ATM or slightly ITM (delta ~0.50)
    - Short leg for debit spread: at/near target price
    - Short leg for credit spread: at/beyond stop price
  - Liquidity filter: skip strikes with 0 volume AND 0 OI

Usage:
    from options_recommender import get_options_recommendations
    recs = get_options_recommendations('AMAT', 'long', 548.15, 476.42, 969.01)
"""

import datetime
import logging

import yfinance as yf

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────

MIN_DTE = 20
MAX_DTE = 75  # wider range to accommodate per-stock optimization
PREFERRED_DTE = 35  # default target ~35 DTE

MAX_EXPIRIES_TO_CHECK = 3
MIN_STRIKE_LIQUIDITY = 0  # skip strikes with 0 vol AND 0 OI


def _compute_optimal_dte(ticker: str, current_price: float) -> int:
    """
    Compute the optimal DTE for a given stock based on its volatility profile.
    
    Rationale: The optimal DTE for a swing trade option should be:
    - Base: expected hold time (10 trading days) * 1.5 buffer → ~21 calendar days
    - + IV adjustment: high-IV stocks need more time (theta is expensive)
    - + Volatility adjustment: high-ATR stocks need more time (stock needs room)
    
    This gives each stock a custom DTE rather than a one-size-fits-all 30-45.
    """
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

    # Base: 10 trading days hold * 1.5 buffer * 7/5 (trading→calendar)
    base_dte = int(10 * 1.5 * 7 / 5)  # = 21

    # IV adjustment (we don't have IV rank, but IV from ATM option is a proxy)
    # Low IV (<20%) = theta is cheap, can go shorter → +0
    # Mid IV (20-40%) = moderate → +5
    # High IV (>40%) = theta is expensive, go longer → +15
    # Note: yfinance IV can be unreliable, so this is a gentle adjustment
    iv_adj = 0  # We'll use ATR% as the primary signal since yfinance IV is often 0

    # Volatility adjustment using ATR%
    if atr_pct > 3.0:
        vol_adj = 10  # high vol = stock needs more room to work
    elif atr_pct > 1.5:
        vol_adj = 5
    else:
        vol_adj = 0  # low vol = shorter is fine

    optimal = base_dte + iv_adj + vol_adj
    return max(MIN_DTE, min(optimal, MAX_DTE))


def _pick_best_expiry(expirations: tuple, optimal_dte: int = None) -> list[str]:
    """Pick 1-3 expirations near the optimal DTE (per-stock if provided)."""
    target_dte = optimal_dte if optimal_dte else PREFERRED_DTE
    today = datetime.datetime.now()
    candidates = []

    for exp_str in expirations:
        try:
            exp_date = datetime.datetime.strptime(exp_str, "%Y-%m-%d")
        except ValueError:
            continue
        dte = (exp_date - today).days
        # Allow a window of ±15 days around the target DTE
        if MIN_DTE <= dte <= MAX_DTE:
            candidates.append((exp_str, dte))

    # Sort by distance from target DTE
    candidates.sort(key=lambda x: abs(x[1] - target_dte))
    return [exp_str for exp_str, _ in candidates[:MAX_EXPIRIES_TO_CHECK]]


def _find_atm_strike(chain_df, target_price: float):
    """Find the strike closest to target_price."""
    if len(chain_df) == 0:
        return None
    idx = (chain_df["strike"] - target_price).abs().argsort().iloc[0]
    return float(chain_df.iloc[idx]["strike"])


def _find_strike_at_price(chain_df, price: float, direction: str = "above"):
    """Find the strike closest to `price`, either above or below."""
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


def _get_contract(chain_df, strike: float):
    """Get the contract row for a given strike."""
    matches = chain_df[chain_df["strike"] == strike]
    if len(matches) == 0:
        return None
    return matches.iloc[0]


def _is_liquid(contract) -> bool:
    """Check if a contract has any liquidity (volume or OI)."""
    vol = float(contract.get("volume", 0) or 0)
    oi = float(contract.get("openInterest", 0) or 0)
    return (vol + oi) > MIN_STRIKE_LIQUIDITY


def _mid_price(contract) -> float:
    """Get mid price from bid/ask, fall back to lastPrice."""
    bid = float(contract.get("bid", 0) or 0)
    ask = float(contract.get("ask", 0) or 0)
    if bid > 0 and ask > 0:
        return (bid + ask) / 2
    return float(contract.get("lastPrice", 0) or 0)


def get_options_recommendations(
    ticker: str,
    direction: str,
    entry_price: float,
    stop_price: float,
    target_price: float,
) -> list[dict]:
    """
    Generate options recommendations for a stock signal.

    Parameters
    ----------
    ticker : str
        Stock ticker (e.g. 'AMAT')
    direction : str
        'long' (bullish) or 'short' (bearish)
    entry_price : float
        Entry price from the signal
    stop_price : float
        Stop loss price
    target_price : float
        Target price

    Returns
    -------
    list of dicts, one per expiry, each containing:
        {
            'expiry': '2026-09-18',
            'dte': 30,
            'single_leg': {type, strike, price, max_loss, breakeven, ...},
            'debit_spread': {type, long_strike, short_strike, net_debit, max_loss, max_profit, ...},
            'credit_spread': {type, short_strike, long_strike, net_credit, max_loss, max_profit, ...},
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

    # Compute per-stock optimal DTE based on volatility profile
    optimal_dte = _compute_optimal_dte(ticker, current_price)
    logger.debug(f"{ticker} optimal DTE: {optimal_dte}")

    expiries = _pick_best_expiry(expirations, optimal_dte)
    if not expiries:
        # Fallback: use 3rd expiry
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

        if direction == "long":
            rec = _build_bullish_recs(
                calls, puts, entry_price, stop_price, target_price, exp_str, dte
            )
        else:
            rec = _build_bearish_recs(
                calls, puts, entry_price, stop_price, target_price, exp_str, dte
            )

        if rec:
            results.append(rec)

    return results


def _build_bullish_recs(calls, puts, entry, stop, target, exp_str, dte):
    """Build bullish options recommendations (long call, bull call spread, bull put spread)."""
    # ── Single leg: ATM long call ─────────────────────────────────────────
    atm_strike = _find_atm_strike(calls, entry)
    atm_call = _get_contract(calls, atm_strike)
    if atm_call is None or not _is_liquid(atm_call):
        # Try near strikes
        for offset in [2.5, 5, 7.5, 10]:
            atm_strike = _find_strike_at_price(calls, entry + offset, "above")
            atm_call = _get_contract(calls, atm_strike)
            if atm_call and _is_liquid(atm_call):
                break

    single_leg = None
    if atm_call is not None:
        call_price = _mid_price(atm_call)
        single_leg = {
            "type": "Long Call",
            "strike": float(atm_strike),
            "price": round(call_price, 2),
            "max_loss": round(call_price * 100, 2),
            "max_profit": "Unlimited",
            "breakeven": round(entry + call_price, 2),
            "iv": round(float(atm_call.get("impliedVolatility", 0) or 0) * 100, 1),
        }

    # ── Debit spread: Bull Call Spread ────────────────────────────────────
    # Long ATM call, short call at target
    short_strike = _find_strike_at_price(calls, target, "above")
    short_call = _get_contract(calls, short_strike)

    debit_spread = None
    if atm_call is not None and short_call is not None:
        long_price = _mid_price(atm_call)
        short_price = _mid_price(short_call)
        net_debit = long_price - short_price
        width = short_strike - atm_strike
        max_profit = (width - net_debit) * 100
        max_loss = net_debit * 100

        if net_debit > 0:
            debit_spread = {
                "type": "Bull Call Spread",
                "long_strike": float(atm_strike),
                "short_strike": float(short_strike),
                "net_debit": round(net_debit, 2),
                "max_loss": round(max_loss, 2),
                "max_profit": round(max_profit, 2),
                "breakeven": round(atm_strike + net_debit, 2),
                "roi": round(max_profit / max_loss * 100, 1) if max_loss > 0 else 0,
            }

    # ── Credit spread: Bull Put Spread ───────────────────────────────────
    # Short put at/below stop, long put further below
    short_put_strike = _find_strike_at_price(puts, stop, "above")
    long_put_strike = _find_strike_at_price(puts, stop * 0.90, "below")  # 10% below stop

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

    if not any([single_leg, debit_spread, credit_spread]):
        return None

    return {
        "expiry": exp_str,
        "dte": dte,
        "single_leg": single_leg,
        "debit_spread": debit_spread,
        "credit_spread": credit_spread,
    }


def _build_bearish_recs(calls, puts, entry, stop, target, exp_str, dte):
    """Build bearish options recommendations (long put, bear put spread, bear call spread)."""
    # ── Single leg: ATM long put ──────────────────────────────────────────
    atm_strike = _find_atm_strike(puts, entry)
    atm_put = _get_contract(puts, atm_strike)
    if atm_put is None or not _is_liquid(atm_put):
        for offset in [2.5, 5, 7.5, 10]:
            atm_strike = _find_strike_at_price(puts, entry - offset, "below")
            atm_put = _get_contract(puts, atm_strike)
            if atm_put and _is_liquid(atm_put):
                break

    single_leg = None
    if atm_put is not None:
        put_price = _mid_price(atm_put)
        single_leg = {
            "type": "Long Put",
            "strike": float(atm_strike),
            "price": round(put_price, 2),
            "max_loss": round(put_price * 100, 2),
            "max_profit": round((atm_strike - put_price) * 100, 2),
            "breakeven": round(entry - put_price, 2),
            "iv": round(float(atm_put.get("impliedVolatility", 0) or 0) * 100, 1),
        }

    # ── Debit spread: Bear Put Spread ─────────────────────────────────────
    # Long ATM put, short put at target
    short_strike = _find_strike_at_price(puts, target, "below")
    short_put = _get_contract(puts, short_strike)

    debit_spread = None
    if atm_put is not None and short_put is not None:
        long_price = _mid_price(atm_put)
        short_price = _mid_price(short_put)
        net_debit = long_price - short_price
        width = atm_strike - short_strike
        max_profit = (width - net_debit) * 100
        max_loss = net_debit * 100

        if net_debit > 0:
            debit_spread = {
                "type": "Bear Put Spread",
                "long_strike": float(atm_strike),
                "short_strike": float(short_strike),
                "net_debit": round(net_debit, 2),
                "max_loss": round(max_loss, 2),
                "max_profit": round(max_profit, 2),
                "breakeven": round(atm_strike - net_debit, 2),
                "roi": round(max_profit / max_loss * 100, 1) if max_loss > 0 else 0,
            }

    # ── Credit spread: Bear Call Spread ──────────────────────────────────
    # Short call at/above stop, long call further above
    short_call_strike = _find_strike_at_price(calls, stop, "above")
    long_call_strike = _find_strike_at_price(calls, stop * 1.10, "above")  # 10% above stop

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

    if not any([single_leg, debit_spread, credit_spread]):
        return None

    return {
        "expiry": exp_str,
        "dte": dte,
        "single_leg": single_leg,
        "debit_spread": debit_spread,
        "credit_spread": credit_spread,
    }


def format_options_embed(recs: list[dict]) -> str:
    """Format recommendations as a compact text block for Discord embeds."""
    if not recs:
        return "No liquid options found for this signal."

    lines = []
    for rec in recs[:2]:  # Show up to 2 expiries
        lines.append(f"**{rec['expiry']} ({rec['dte']} DTE)**")

        if rec.get("single_leg"):
            s = rec["single_leg"]
            lines.append(
                f"  • {s['type']}: Strike {s['strike']} @ ${s['price']:.2f} "
                f"(Max Loss ${s['max_loss']:.0f}, IV {s.get('iv', '?')}%)"
            )

        if rec.get("debit_spread"):
            d = rec["debit_spread"]
            lines.append(
                f"  • {d['type']}: {d['long_strike']}/{d['short_strike']} "
                f"Net Debit ${d['net_debit']:.2f} "
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