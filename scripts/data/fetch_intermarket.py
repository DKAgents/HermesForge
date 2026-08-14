#!/usr/bin/env python3
"""
fetch_intermarket.py — Intermarket data feed via yfinance

Fetches cross-asset intermarket data used to read the market's "true"
risk posture (which often diverges from headline equity indices):

  1. VIX Term Structure  — ^VIX, ^VIX3M, ^VIX6M
       Contango (VIX3M > VIX)  = normal / complacent
       Backwardation (VIX3M < VIX) = stress / risk-off
       Slope = VIX6M - VIX (overall term-structure steepness)

  2. Vol of Vol          — ^VVIX
       High VVIX + low VIX = early warning of a vol explosion.

  3. MOVE Index          — ^MOVE  (ICE BofA bond-volatility index)
       MOVE > 100 = bond-market stress = risk-off.

  4. Commodities        — GC=F (Gold), CL=F (Oil), HG=F (Copper),
                          SI=F (Silver), NG=F (NatGas),
                          ZW=F (Wheat), ZC=F (Corn)
       Per-commodity 1d / 7d / 30d returns, 20d-MA trend, plus
       intermarket reads:
         - Copper up   = economic growth (risk-on)
         - Gold up + stocks down = risk-off flight to safety
         - Oil up      = inflation pressure
         - Gold/Oil ratio > 25 = recession fear, < 15 = growth optimism

  5. FX                 — EURUSD, GBPUSD, USDJPY (yfinance =X form)
       JPY = safe haven, EUR = risk proxy. DXY trend lives in
       fetch_macro.py; this adds the crosses.

Caches to ~/.hermes/market_data/intermarket/ as dated JSON files.
Refreshes if the day's cache is > 6h old. All tickers are fetched
independently so a single failed ticker never breaks the feed.

Public API:
    get_intermarket_summary()    -> dict with all data
    get_vix_term_structure()     -> dict (VIX, VIX3M, VIX6M, contango, ...)
    get_commodity_summary()      -> dict (prices, returns, signals)
    get_intermarket_signals()    -> dict of actionable signals

Usage:
    python3 fetch_intermarket.py             # fetch + print summary
    python3 fetch_intermarket.py --force      # force refresh cache
    python3 fetch_intermarket.py --signals    # print signals only
"""

from __future__ import annotations

import sys
import json
import argparse
import pathlib
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import yfinance as yf

# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #

CACHE_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "intermarket"
CACHE_MAX_AGE_HOURS = 6  # re-fetch at most every 6h

# History length — "3mo" gives ~60 trading days, enough for 30d returns
# and a 20d moving average with comfortable headroom.
HISTORY_PERIOD = "3mo"

# VIX term structure
VIX_TICKERS = {
    "VIX": "^VIX",
    "VIX3M": "^VIX3M",
    "VIX6M": "^VIX6M",
}
VVIX_TICKER = "^VVIX"
MOVE_TICKER = "^MOVE"

# Commodities
COMMODITY_TICKERS = {
    "Gold": "GC=F",
    "Oil": "CL=F",
    "Copper": "HG=F",
    "Silver": "SI=F",
    "NatGas": "NG=F",
    "Wheat": "ZW=F",
    "Corn": "ZC=F",
}

# FX pairs (yfinance uses the =X convention)
FX_TICKERS = {
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "USDJPY=X",
}

# Equity proxy used to detect "stocks down" for the gold flight-to-safety
# signal. SPY is the most liquid US large-cap proxy.
EQUITY_PROXY_TICKER = "SPY"


# --------------------------------------------------------------------------- #
# Low-level fetching (graceful, one ticker at a time)
# --------------------------------------------------------------------------- #

def _fetch_series(ticker: str, period: str = HISTORY_PERIOD) -> pd.Series | None:
    """
    Download close prices for a single yfinance ticker.

    Returns a pandas Series indexed by date, or None if the ticker could
    not be fetched (delisted, 404, empty, etc.). Never raises.
    """
    try:
        hist = yf.Ticker(ticker).history(period=period, auto_adjust=False)  # type: ignore[union-attr]
    except Exception as exc:  # noqa: BLE001
        print(f"[intermarket] {ticker}: download failed ({exc})", file=sys.stderr)
        return None
    if hist is None or hist.empty or "Close" not in hist.columns:
        print(f"[intermarket] {ticker}: no data returned", file=sys.stderr)
        return None
    close = hist["Close"]
    # Coerce to a 1-D Series (single-column frames collapse cleanly).
    s = pd.Series(close).dropna() if not isinstance(close, pd.Series) else close.dropna()  # type: ignore[union-attr]
    if s.empty:
        print(f"[intermarket] {ticker}: empty close series", file=sys.stderr)
        return None
    return s


def _pct_return(series: pd.Series | None, lookback: int) -> float | None:
    """Return % change over `lookback` bars, or None if not enough history."""
    if series is None or len(series) <= lookback:
        return None
    try:
        prev = float(series.iloc[-1 - lookback])
        last = float(series.iloc[-1])
    except (IndexError, TypeError, ValueError):
        return None
    if prev == 0 or pd.isna(prev) or pd.isna(last):
        return None
    return round((last / prev - 1.0) * 100.0, 4)


def _ma_trend(series: pd.Series | None, window: int = 20) -> tuple[float | None, str]:
    """
    Compute the moving-average trend.

    Returns (ma_value, trend) where trend is "up" / "down" / "flat":
        up   — price above MA and MA is rising
        down — price below MA and MA is falling
        flat — otherwise
    """
    if series is None or len(series) < window + 5:
        return None, "unknown"
    ma = series.rolling(window=window).mean().dropna()
    if len(ma) < 5:
        return None, "unknown"
    ma_now = float(ma.iloc[-1])
    ma_prev = float(ma.iloc[-5])
    price = float(series.iloc[-1])
    rising = ma_now > ma_prev
    falling = ma_now < ma_prev
    if price > ma_now and rising:
        trend = "up"
    elif price < ma_now and falling:
        trend = "down"
    else:
        trend = "flat"
    return round(ma_now, 4), trend


def _scalar(series: "pd.Series | None") -> float | None:
    """Latest close as a rounded float, or None."""
    if series is None or series.empty:
        return None
    val = series.iloc[-1]
    if pd.isna(val):
        return None
    return round(float(val), 4)


def _last_date(series: pd.Series | None) -> str | None:
    if series is None or series.empty:
        return None
    ts = pd.Timestamp(series.index[-1])  # type: ignore[arg-type]
    if hasattr(ts, "date"):
        return str(ts.date())
    return str(ts)


# --------------------------------------------------------------------------- #
# VIX term structure
# --------------------------------------------------------------------------- #

def _fetch_vix_term_structure() -> dict:
    """Fetch and analyse the VIX term structure."""
    series = {name: _fetch_series(tk) for name, tk in VIX_TICKERS.items()}
    vix = _scalar(series["VIX"])
    vix3m = _scalar(series["VIX3M"])
    vix6m = _scalar(series["VIX6M"])

    contango = None
    backwardation = None
    slope = None
    state = "unknown"

    if vix is not None and vix3m is not None:
        spread_3m = round(vix3m - vix, 4)
        contango = spread_3m > 0
        backwardation = spread_3m < 0
        if contango:
            state = "contango"
        elif backwardation:
            state = "backwardation"
        else:
            state = "flat"
    if vix is not None and vix6m is not None:
        slope = round(vix6m - vix, 4)

    return {
        "VIX": vix,
        "VIX3M": vix3m,
        "VIX6M": vix6m,
        "spread_3m": (round(vix3m - vix, 4) if vix is not None and vix3m is not None else None),
        "spread_6m": (round(vix6m - vix, 4) if vix is not None and vix6m is not None else None),
        "contango": contango,
        "backwardation": backwardation,
        "slope": slope,
        "state": state,
        "dates": {
            name: _last_date(s) for name, s in series.items()
        },
    }


def get_vix_term_structure() -> dict:
    """
    Return the VIX term-structure snapshot.

        {
            "VIX":  float,
            "VIX3M": float,
            "VIX6M": float,
            "spread_3m": float,        # VIX3M - VIX   (positive = contango)
            "spread_6m": float,        # VIX6M - VIX
            "contango": bool,
            "backwardation": bool,
            "slope": float,
            "state": "contango" | "backwardation" | "flat" | "unknown",
        }
    """
    data = _load_or_fetch()
    return data.get("vix_term_structure", {})


# --------------------------------------------------------------------------- #
# VVIX & MOVE
# --------------------------------------------------------------------------- #

def _fetch_vol_of_vol() -> dict:
    s = _fetch_series(VVIX_TICKER)
    return {
        "VVIX": _scalar(s),
        "date": _last_date(s),
    }


def _fetch_move() -> dict:
    s = _fetch_series(MOVE_TICKER)
    current = _scalar(s)
    stress = current is not None and current > 100
    return {
        "MOVE": current,
        "stress": stress,
        "date": _last_date(s),
    }


# --------------------------------------------------------------------------- #
# Commodities
# --------------------------------------------------------------------------- #

def _fetch_commodity_block() -> dict:
    """
    Per-commodity: price, 1d/7d/30d returns, 20d-MA trend.
    Plus derived Gold/Oil ratio and aggregate signals.
    """
    series = {}
    for name, tk in COMMODITY_TICKERS.items():
        series[name] = _fetch_series(tk)

    commodities: dict[str, Any] = {}
    for name in COMMODITY_TICKERS:
        s = series[name]
        ma20, trend = _ma_trend(s, 20) if s is not None else (None, "unknown")
        commodities[name] = {
            "ticker": COMMODITY_TICKERS[name],
            "price": _scalar(s),
            "return_1d": _pct_return(s, 1),
            "return_7d": _pct_return(s, 7),
            "return_30d": _pct_return(s, 30),
            "ma_20": ma20,
            "trend": trend,
            "date": _last_date(s),
        }

    # Gold/Oil ratio — recession-fear / growth-optimism gauge
    gold = commodities["Gold"]["price"]
    oil = commodities["Oil"]["price"]
    gold_oil_ratio = None
    gold_oil_read = "unknown"
    if gold is not None and oil is not None and oil != 0:
        gold_oil_ratio = round(gold / oil, 4)
        if gold_oil_ratio > 25:
            gold_oil_read = "recession_fear"
        elif gold_oil_ratio < 15:
            gold_oil_read = "growth_optimism"
        else:
            gold_oil_read = "neutral"

    return {
        "commodities": commodities,
        "gold_oil_ratio": gold_oil_ratio,
        "gold_oil_read": gold_oil_read,
    }


def get_commodity_summary() -> dict:
    """
    Return all commodity prices, returns, trends, and the Gold/Oil ratio.

    {
        "commodities": { <name>: {price, return_1d, return_7d,
                                  return_30d, ma_20, trend, date}, ... },
        "gold_oil_ratio": float | None,
        "gold_oil_read":  "recession_fear" | "growth_optimism"
                          | "neutral" | "unknown",
    }
    """
    data = _load_or_fetch()
    block = data.get("commodities", {})
    return {
        "commodities": block.get("commodities", {}),
        "gold_oil_ratio": block.get("gold_oil_ratio"),
        "gold_oil_read": block.get("gold_oil_read"),
    }


# --------------------------------------------------------------------------- #
# FX
# --------------------------------------------------------------------------- #

def _fetch_fx_block() -> dict:
    fx: dict[str, Any] = {}
    for name, tk in FX_TICKERS.items():
        s = _fetch_series(tk)
        ma20, trend = _ma_trend(s, 20) if s is not None else (None, "unknown")
        fx[name] = {
            "ticker": tk,
            "price": _scalar(s),
            "return_1d": _pct_return(s, 1),
            "return_7d": _pct_return(s, 7),
            "return_30d": _pct_return(s, 30),
            "ma_20": ma20,
            "trend": trend,
            "date": _last_date(s),
        }
    return fx


def _fetch_equity_proxy() -> dict:
    """Fetch SPY as the 'stocks' reference for flight-to-safety logic."""
    s = _fetch_series(EQUITY_PROXY_TICKER)
    ma20, trend = _ma_trend(s, 20) if s is not None else (None, "unknown")
    return {
        "ticker": EQUITY_PROXY_TICKER,
        "price": _scalar(s),
        "return_1d": _pct_return(s, 1),
        "return_7d": _pct_return(s, 7),
        "return_30d": _pct_return(s, 30),
        "ma_20": ma20,
        "trend": trend,
        "date": _last_date(s),
    }


# --------------------------------------------------------------------------- #
# Intermarket signals (actionable)
# --------------------------------------------------------------------------- #

def _compute_signals(payload: dict) -> dict:
    """Derive the actionable intermarket signals from the full payload."""
    signals: dict[str, Any] = {}

    # --- VIX term structure ----------------------------------------------
    vts = payload.get("vix_term_structure", {})
    state = vts.get("state")
    if state == "backwardation":
        signals["vix_term_structure"] = {
            "signal": "risk_off",
            "detail": "VIX term structure in backwardation (VIX3M < VIX) — stress regime.",
            "spread_3m": vts.get("spread_3m"),
        }
    elif state == "contango":
        signals["vix_term_structure"] = {
            "signal": "normal",
            "detail": "VIX term structure in contango — normal/complacent regime.",
            "spread_3m": vts.get("spread_3m"),
        }

    # --- Vol of vol early warning ----------------------------------------
    vvix = payload.get("vvix", {})
    vix = vts.get("VIX")
    vvix_val = vvix.get("VVIX")
    if vvix_val is not None and vix is not None:
        # VVIX above its long-run ~90 area while spot VIX is low flags
        # positioning for a vol spike before spot VIX has reacted.
        if vvix_val > 95 and vix < 15:
            signals["vol_of_vol_warning"] = {
                "signal": "early_warning",
                "detail": (
                    "High VVIX with low spot VIX — early warning of a "
                    "volatility explosion."
                ),
                "VVIX": vvix_val,
                "VIX": vix,
            }

    # --- MOVE (bond vol) -------------------------------------------------
    move = payload.get("move", {})
    if move.get("stress"):
        signals["bond_volatility"] = {
            "signal": "risk_off",
            "detail": f"MOVE Index ({move.get('MOVE')}) > 100 — bond-market stress.",
            "MOVE": move.get("MOVE"),
        }

    # --- Commodities -----------------------------------------------------
    comm = payload.get("commodities", {}).get("commodities", {})
    copper = comm.get("Copper", {})
    gold = comm.get("Gold", {})
    oil = comm.get("Oil", {})

    # Copper up = economic growth (risk-on)
    copper_trend = copper.get("trend")
    if copper_trend == "up":
        signals["copper_growth"] = {
            "signal": "risk_on",
            "detail": "Copper trending up — economic growth signal.",
            "trend": copper_trend,
            "return_30d": copper.get("return_30d"),
        }
    elif copper_trend == "down":
        signals["copper_growth"] = {
            "signal": "risk_off",
            "detail": "Copper trending down — growth slowdown signal.",
            "trend": copper_trend,
            "return_30d": copper.get("return_30d"),
        }

    # Oil up = inflation pressure
    oil_trend = oil.get("trend")
    if oil_trend == "up":
        signals["oil_inflation"] = {
            "signal": "inflation_pressure",
            "detail": "Oil trending up — inflation pressure building.",
            "trend": oil_trend,
            "return_30d": oil.get("return_30d"),
        }

    # Gold up + stocks down = flight to safety
    gold_trend = gold.get("trend")
    equities = payload.get("equity_proxy", {})
    eq_trend = equities.get("trend")
    eq_ret_1d = equities.get("return_1d")
    stocks_down = eq_trend == "down" or (eq_ret_1d is not None and eq_ret_1d < 0)
    if gold_trend == "up" and stocks_down:
        signals["flight_to_safety"] = {
            "signal": "risk_off",
            "detail": "Gold up while equities down — flight to safety.",
            "gold_trend": gold_trend,
            "equity_trend": eq_trend,
            "equity_return_1d": eq_ret_1d,
        }

    # Gold/Oil ratio
    go_read = payload.get("commodities", {}).get("gold_oil_read")
    go_ratio = payload.get("commodities", {}).get("gold_oil_ratio")
    if go_read == "recession_fear":
        signals["gold_oil_ratio"] = {
            "signal": "risk_off",
            "detail": f"Gold/Oil ratio ({go_ratio}) > 25 — recession fear.",
            "ratio": go_ratio,
        }
    elif go_read == "growth_optimism":
        signals["gold_oil_ratio"] = {
            "signal": "risk_on",
            "detail": f"Gold/Oil ratio ({go_ratio}) < 15 — growth optimism.",
            "ratio": go_ratio,
        }

    # --- FX -------------------------------------------------------------
    fx = payload.get("fx", {})
    jpy = fx.get("USDJPY", {})
    eur = fx.get("EURUSD", {})
    jpy_trend = jpy.get("trend")
    # USDJPY down = JPY strengthening = safe-haven demand (risk-off).
    # Note: a falling USDJPY means fewer JPY per USD, i.e. JPY up.
    if jpy_trend == "down":
        signals["jpy_safe_haven"] = {
            "signal": "risk_off",
            "detail": "USDJPY trending down — JPY strengthening (safe-haven bid).",
            "trend": jpy_trend,
            "return_7d": jpy.get("return_7d"),
        }
    eur_trend = eur.get("trend")
    if eur_trend == "down":
        signals["eur_risk_proxy"] = {
            "signal": "risk_off",
            "detail": "EURUSD trending down — risk appetite fading (EUR weak).",
            "trend": eur_trend,
            "return_7d": eur.get("return_7d"),
        }

    # --- Aggregate risk posture -----------------------------------------
    risk_off_count = sum(
        1 for v in signals.values()
        if v.get("signal") in ("risk_off", "inflation_pressure", "early_warning")
    )
    risk_on_count = sum(
        1 for v in signals.values() if v.get("signal") == "risk_on"
    )
    if risk_off_count >= 3:
        posture = "risk_off"
    elif risk_off_count > 0 and risk_off_count >= risk_on_count:
        posture = "caution"
    elif risk_on_count >= 2 and risk_off_count == 0:
        posture = "risk_on"
    else:
        posture = "mixed"

    signals["_summary"] = {
        "posture": posture,
        "risk_off_signals": risk_off_count,
        "risk_on_signals": risk_on_count,
    }

    return signals


def get_intermarket_signals() -> dict:
    """Return a dict of actionable intermarket signals + aggregate posture."""
    data = _load_or_fetch()
    return data.get("signals", {})


# --------------------------------------------------------------------------- #
# Orchestration + cache
# --------------------------------------------------------------------------- #

def _build_payload() -> dict:
    """Fetch every intermarket block and assemble the full payload."""
    payload: dict[str, Any] = {
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    errors: list[str] = []

    # VIX term structure
    try:
        payload["vix_term_structure"] = _fetch_vix_term_structure()
    except Exception as exc:  # noqa: BLE001
        errors.append(f"vix_term_structure: {exc}")
        payload["vix_term_structure"] = {}

    # VVIX
    try:
        payload["vvix"] = _fetch_vol_of_vol()
    except Exception as exc:  # noqa: BLE001
        errors.append(f"vvix: {exc}")
        payload["vvix"] = {}

    # MOVE
    try:
        payload["move"] = _fetch_move()
    except Exception as exc:  # noqa: BLE001
        errors.append(f"move: {exc}")
        payload["move"] = {}

    # Commodities
    try:
        payload["commodities"] = _fetch_commodity_block()
    except Exception as exc:  # noqa: BLE001
        errors.append(f"commodities: {exc}")
        payload["commodities"] = {"commodities": {}, "gold_oil_ratio": None,
                                  "gold_oil_read": "unknown"}

    # FX
    try:
        payload["fx"] = _fetch_fx_block()
    except Exception as exc:  # noqa: BLE001
        errors.append(f"fx: {exc}")
        payload["fx"] = {}

    # Equity proxy (for flight-to-safety logic)
    try:
        payload["equity_proxy"] = _fetch_equity_proxy()
    except Exception as exc:  # noqa: BLE001
        errors.append(f"equity_proxy: {exc}")
        payload["equity_proxy"] = {}

    payload["errors"] = errors

    # Derive actionable signals from everything above
    payload["signals"] = _compute_signals(payload)
    return payload


def _cache_path(day: datetime | None = None) -> pathlib.Path:
    day = day or datetime.now(timezone.utc)
    return CACHE_DIR / f"intermarket_{day.strftime('%Y-%m-%d')}.json"


def _load_or_fetch(force: bool = False) -> dict:
    """
    Return today's intermarket payload, using a fresh cache when valid
    and fetching otherwise.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _cache_path()

    if not force and path.exists():
        try:
            cached = json.loads(path.read_text())
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            age_h = (datetime.now(timezone.utc) - mtime).total_seconds() / 3600.0
            if age_h < CACHE_MAX_AGE_HOURS:
                return cached
        except (json.JSONDecodeError, OSError):
            pass  # corrupt cache -> refetch

    payload = _build_payload()
    try:
        path.write_text(json.dumps(payload, indent=2, default=str))
        print(f"[intermarket] cached to {path}", file=sys.stderr)
    except OSError as exc:
        print(f"[intermarket] cache write failed: {exc}", file=sys.stderr)
    return payload


def get_intermarket_summary(force: bool = False) -> dict:
    """
    Return the complete intermarket data dict: VIX term structure, VVIX,
    MOVE, commodities (prices/returns/trends), FX, equity proxy, and
    actionable signals.
    """
    return _load_or_fetch(force=force)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def _print_summary(payload: dict) -> None:
    print(f"\nIntermarket Summary — fetched {payload.get('fetched_at')}")

    print("\n--- VIX Term Structure ---")
    vts = payload.get("vix_term_structure", {})
    print(f"  VIX   : {vts.get('VIX')}")
    print(f"  VIX3M : {vts.get('VIX3M')}")
    print(f"  VIX6M : {vts.get('VIX6M')}")
    print(f"  State : {vts.get('state')}  "
          f"(spread_3m={vts.get('spread_3m')}, slope={vts.get('slope')})")

    print("\n--- Vol of Vol / Bond Vol ---")
    print(f"  VVIX  : {payload.get('vvix', {}).get('VVIX')}")
    move = payload.get("move", {})
    print(f"  MOVE  : {move.get('MOVE')}  stress={move.get('stress')}")

    print("\n--- Commodities ---")
    comm = payload.get("commodities", {})
    for name, info in comm.get("commodities", {}).items():
        print(f"  {name:8s} price={info.get('price')}  "
              f"1d={info.get('return_1d')}%  7d={info.get('return_7d')}%  "
              f"30d={info.get('return_30d')}%  trend={info.get('trend')}")
    print(f"  Gold/Oil ratio: {comm.get('gold_oil_ratio')}  "
          f"({comm.get('gold_oil_read')})")

    print("\n--- FX ---")
    for name, info in payload.get("fx", {}).items():
        print(f"  {name:6s} price={info.get('price')}  "
              f"1d={info.get('return_1d')}%  trend={info.get('trend')}")

    eq = payload.get("equity_proxy", {})
    print(f"\n--- Equity Proxy ({eq.get('ticker')}) ---")
    print(f"  price={eq.get('price')}  1d={eq.get('return_1d')}%  "
          f"trend={eq.get('trend')}")

    print("\n--- Intermarket Signals ---")
    sig = payload.get("signals", {})
    for k, v in sig.items():
        if k == "_summary":
            continue
        if isinstance(v, dict):
            print(f"  [{k}] {v.get('signal')}: {v.get('detail')}")
    summ = sig.get("_summary", {})
    print(f"\n  Posture: {summ.get('posture')}  "
          f"(risk_off={summ.get('risk_off_signals')}, "
          f"risk_on={summ.get('risk_on_signals')})")

    errs = payload.get("errors", [])
    if errs:
        print(f"\n--- Errors ({len(errs)}) ---")
        for e in errs:
            print(f"  {e}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Fetch intermarket data (VIX term structure, VVIX, "
                    "MOVE, commodities, FX) via yfinance"
    )
    ap.add_argument("--force", action="store_true",
                    help="Force refresh cache")
    ap.add_argument("--signals", action="store_true",
                    help="Print actionable signals only (as JSON)")
    args = ap.parse_args()

    if args.signals:
        print(json.dumps(get_intermarket_signals(), indent=2, default=str))
    else:
        payload = get_intermarket_summary(force=args.force)
        _print_summary(payload)
