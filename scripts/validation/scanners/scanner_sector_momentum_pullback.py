#!/usr/bin/env python3
"""
scanner_sector_momentum_pullback.py
====================================
HermesForge Phase 1A — Sector-Momentum-Continuation Pullback (equity long).

Edge candidate: CAND-20260814-sector-momentum-continuation
Source hypothesis: "Strong sector with continued RS improvement. Momentum
persistence suggests more upside. Buy top stocks in the leading sector on
pullbacks to 10MA with volume contraction. Stop below 20MA. Exit when sector
RS turns negative on 5d, or target 3R."

Signal Rules:
  Sector leadership (computed once from cached sector-ETF daily series):
    - For each trading day, the "leading sector" = the sector ETF with the
      highest 20-day relative strength vs SPY: RS = ETF_20d_return - SPY_20d_return.
    - A day is "leader-active" if the leading ETF's 20d RS > 0 (sector is
      actually outperforming SPY, not just least-bad).
    - Persistence filter (optional): require the SAME sector to have led for
      >= SECTOR_PERSIST_DAYS consecutive days (momentum continuation).

  Per-ticker entry (all required, signal day i):
    - The stock's GICS sector == that day's leading sector (static sector map)
    - 10-SMA pullback: low[i] <= MA10[i] (price has pulled back to/touched the 10MA)
    - Close recovers: close[i] > MA10[i] (closed back above the 10MA)
    - Volume contraction: volume[i] < 0.9 * 20-day avg volume (contraction on pullback)
    - Trend agreement: close[i] > 50-SMA AND 50-SMA > 200-SMA
    - ATR% of price <= MAX_ATR_PCT

  Risk/reward & exit (forward-scan, max MAX_BARS_HELD bars):
    - entry  = close[i]
    - stop   = min(MA20[i], low[i]) - STOP_BUFFER_ATR * ATR(i)   (below 20MA)
    - target = entry + MIN_RR * risk
    - exit 'target' / 'stop' / 'time'

Dependencies: pandas, numpy. Sector ETFs + SPY loaded from local parquet cache.
The static GICS sector map covers ~170 well-known S&P constituents; tickers
not in the map are skipped (they can't be assigned a sector here without an
external reference). Survivorship-bias caveat applies (ADR-004): the map
reflects current constituents; historic members that later dropped out are
not represented, which can flatter the sector-continuation edge.
"""

import numpy as np
import pandas as pd
from pathlib import Path

STRATEGY_ID = "STR-20260814-SECTOR-MOMENTUM-PULLBACK"

# ── Parameters (module-level; walk-forward monkey-patches these) ─────────────
RS_LOOKBACK = 20
SECTOR_PERSIST_DAYS = 5
MA_PULLBACK = 10
MA_STOP = 20
MA_TREND_FAST = 50
MA_TREND_SLOW = 200
VOL_AVG_PERIOD = 20
VOL_CONTRACTION = 0.9
MIN_RR = 3.0
STOP_BUFFER_ATR = 0.3
MAX_ATR_PCT = 0.07
ATR_PERIOD = 14
MAX_BARS_HELD = 15

_CACHE_DIR = Path.home() / ".hermes" / "market_data"

# Sector ETF -> GICS sector key. Only ETFs present in the cache are used.
SECTOR_ETFS = {
    "XLK": "technology",
    "XLC": "communications",
    "XLY": "consumer_discretionary",
    "XLP": "consumer_staples",
    "XLE": "energy",
    "XLF": "financials",
    "XLV": "healthcare",
    "XLI": "industrials",
    "XLB": "materials",
    "XLU": "utilities",
    "XLRE": "real_estate",
}

# Static GICS sector map for well-known S&P constituents. Tickes not listed
# here are skipped by the scanner (no sector assignment available).
SECTOR_MAP = {
    # Technology
    "AAPL": "technology", "MSFT": "technology", "NVDA": "technology", "AVGO": "technology",
    "ORCL": "technology", "AMD": "technology", "ADBE": "technology", "CRM": "technology",
    "NOW": "technology", "SNOW": "technology", "PANW": "technology", "CRWD": "technology",
    "ZS": "technology", "TEAM": "technology", "WDAY": "technology", "DDOG": "technology",
    "CSCO": "technology", "IBM": "technology", "SNPS": "technology", "CDNS": "technology",
    "INTU": "technology", "FICO": "technology", "FTNT": "technology", "APP": "technology",
    "KLAC": "technology", "AMAT": "technology", "LRCX": "technology", "ADI": "technology",
    "MRVL": "technology", "ON": "technology", "QCOM": "technology", "TXN": "technology",
    "MU": "technology", "INTC": "technology", "NXPI": "technology", "MCHP": "technology",
    "STX": "technology", "WDC": "technology", "ASML": "technology", "TSM": "technology",
    "ARM": "technology", "SMCI": "technology", "HPE": "technology", "DELL": "technology",
    "HPQ": "technology", "GLW": "technology", "JN": "technology", "KEYS": "technology",
    "FFIV": "technology", "ANET": "technology", "CTSH": "technology", "GDDY": "technology",
    "AKAM": "technology", "FISV": "technology", "CPAY": "technology", "GEN": "technology",
    # Communications
    "META": "communications", "GOOGL": "communications", "GOOG": "communications",
    "NFLX": "communications", "CMCSA": "communications", "TMUS": "communications",
    "VZ": "communications", "T": "communications", "DIS": "communications", "WBD": "communications",
    "EA": "communications", "TTWO": "communications", "CHTR": "communications", "SPOT": "communications",
    "XYZ": "communications", "SIRI": "communications",
    # Consumer Discretionary
    "AMZN": "consumer_discretionary", "HD": "consumer_discretionary", "MCD": "consumer_discretionary",
    "NKE": "consumer_discretionary", "SBUX": "consumer_discretionary", "TGT": "consumer_discretionary",
    "LOW": "consumer_discretionary", "TJX": "consumer_discretionary", "ROST": "consumer_discretionary",
    "YUM": "consumer_discretionary", "CMG": "consumer_discretionary", "DPZ": "consumer_discretionary",
    "MAR": "consumer_discretionary", "HLT": "consumer_discretionary", "LULU": "consumer_discretionary",
    "DECK": "consumer_discretionary", "BKNG": "consumer_discretionary", "ABNB": "consumer_discretionary",
    "CCL": "consumer_discretionary", "EBAY": "consumer_discretionary", "EXPE": "consumer_discretionary",
    "F": "consumer_discretionary", "GM": "consumer_discretionary", "DLTR": "consumer_discretionary",
    "DG": "consumer_discretionary", "GRMN": "consumer_discretionary", "HAS": "consumer_discretionary",
    "APTV": "consumer_discretionary", "LEN": "consumer_discretionary", "DHI": "consumer_discretionary",
    "PHM": "consumer_discretionary", "TPR": "consumer_discretionary", "RL": "consumer_discretionary",
    "BBY": "consumer_discretionary", "DASH": "consumer_discretionary", "HOOD": "consumer_discretionary",
    "UBER": "consumer_discretionary", "SHOP": "consumer_discretionary", "PYPL": "consumer_discretionary",
    "COIN": "consumer_discretionary", "NVR": "consumer_discretionary",
    # Consumer Staples
    "WMT": "consumer_staples", "PG": "consumer_staples", "KO": "consumer_staples", "PEP": "consumer_staples",
    "MDLZ": "consumer_staples", "CL": "consumer_staples", "KMB": "consumer_staples", "GIS": "consumer_staples",
    "STZ": "consumer_staples", "MNST": "consumer_staples", "KDP": "consumer_staples", "HSY": "consumer_staples",
    "SYY": "consumer_staples", "TAP": "consumer_staples", "COST": "consumer_staples", "MO": "consumer_staples",
    "PM": "consumer_staples", "CLX": "consumer_staples", "CHD": "consumer_staples", "KR": "consumer_staples",
    "KVUE": "consumer_staples", "BG": "consumer_staples", "TSN": "consumer_staples", "ADM": "consumer_staples",
    "FMC": "consumer_staples", "MKC": "consumer_staples", "SJM": "consumer_staples", "CAG": "consumer_staples",
    "CPB": "consumer_staples",
    # Energy
    "XOM": "energy", "CVX": "energy", "COP": "energy", "SLB": "energy", "EOG": "energy",
    "MPC": "energy", "PSX": "energy", "VLO": "energy", "OXY": "energy", "HAL": "energy",
    "KMI": "energy", "WMB": "energy", "OKE": "energy", "BKR": "energy", "DVN": "energy",
    "FANG": "energy", "CTR": "energy", "TRGP": "energy", "WMB": "energy", "EQT": "energy",
    "HES": "energy", "MRO": "energy", "PXD": "energy", "COG": "energy", "APA": "energy",
    # Financials
    "JPM": "financials", "BAC": "financials", "GS": "financials", "MS": "financials",
    "WFC": "financials", "BLK": "financials", "SCHW": "financials", "AXP": "financials",
    "USB": "financials", "PNC": "financials", "V": "financials", "MA": "financials", "C": "financials",
    "COF": "financials", "TFC": "financials", "STT": "financials", "MET": "financials",
    "PRU": "financials", "AIG": "financials", "TRV": "financials", "ALL": "financials",
    "PGR": "financials", "CB": "financials", "ICE": "financials", "CME": "financials",
    "SPGI": "financials", "MCO": "financials", "AON": "financials", "BK": "financials",
    "BEN": "financials", "IVZ": "financials", "FITB": "financials", "KEY": "financials",
    "CFG": "financials", "CBOE": "financials", "KKR": "financials", "APO": "financials",
    "BX": "financials", "BRK-B": "financials", "NDAQ": "financials", "L": "financials",
    "PRU": "financials", "J": "financials", "MKTX": "financials", "NAVI": "financials",
    # Healthcare
    "LLY": "healthcare", "UNH": "healthcare", "JNJ": "healthcare", "ABBV": "healthcare",
    "MRK": "healthcare", "TMO": "healthcare", "ABT": "healthcare", "BMY": "healthcare",
    "AMGN": "healthcare", "GILD": "healthcare", "PFE": "healthcare", "CVS": "healthcare",
    "CI": "healthcare", "HUM": "healthcare", "ELV": "healthcare", "MDT": "healthcare",
    "SYK": "healthcare", "BSX": "healthcare", "ISRG": "healthcare", "VRTX": "healthcare",
    "REGN": "healthcare", "ZTS": "healthcare", "DHR": "healthcare", "BDX": "healthcare",
    "IDXX": "healthcare", "IQV": "healthcare", "MRNA": "healthcare", "BIIB": "healthcare",
    "DVA": "healthcare", "DXCM": "healthcare", "GEHC": "healthcare", "BAX": "healthcare",
    "ALGN": "healthcare", "A": "healthcare", "MCK": "healthcare", "COR": "healthcare",
    "CAH": "healthcare", "HSIC": "healthcare", "WST": "healthcare", "RMD": "healthcare",
    "STE": "healthcare", "ILMN": "healthcare", "CRL": "healthcare", "CNC": "healthcare",
    # Industrials
    "CAT": "industrials", "DE": "industrials", "BA": "industrials", "GE": "industrials",
    "HON": "industrials", "RTX": "industrials", "LMT": "industrials", "UPS": "industrials",
    "FDX": "industrials", "MMM": "industrials", "UNP": "industrials", "CSX": "industrials",
    "NSC": "industrials", "WM": "industrials", "EMR": "industrials", "ETN": "industrials",
    "PH": "industrials", "ITW": "industrials", "ROK": "industrials", "CMI": "industrials",
    "DAL": "industrials", "LUV": "industrials", "AAL": "industrials", "UAL": "industrials",
    "CARR": "industrials", "GD": "industrials", "HWM": "industrials", "JCI": "industrials",
    "FAST": "industrials", "FTV": "industrials", "PNR": "industrials", "DOV": "industrials",
    "R": "industrials", "GWW": "industrials", "ROL": "industrials", "AME": "industrials",
    "XYL": "industrials", "BR": "industrials", "HII": "industrials", "OC": "industrials",
    "PPG": "industrials", "LHX": "industrials", "GNRC": "industrials", "TEX": "industrials",
    # Materials
    "LIN": "materials", "APD": "materials", "SHW": "materials", "ECL": "materials",
    "NUE": "materials", "FCX": "materials", "NEM": "materials", "DOW": "materials",
    "DD": "materials", "ALB": "materials", "MLM": "materials", "BALL": "materials",
    "AVY": "materials", "IP": "materials", "CF": "materials", "CE": "materials",
    "EMN": "materials", "FSLR": "materials", "VMC": "materials", "MOS": "materials",
    "STLD": "materials", "AA": "materials", "PKG": "materials", "WRK": "materials",
    # Utilities
    "NEE": "utilities", "DUK": "utilities", "SO": "utilities", "D": "utilities",
    "AEP": "utilities", "AEE": "utilities", "AES": "utilities", "AWK": "utilities",
    "ATO": "utilities", "CMS": "utilities", "CNP": "utilities", "DTE": "utilities",
    "ED": "utilities", "EIX": "utilities", "ETR": "utilities", "EVRG": "utilities",
    "EXC": "utilities", "FE": "utilities", "NRG": "utilities", "PEG": "utilities",
    "SRE": "utilities", "WEC": "utilities", "XEL": "utilities", "ES": "utilities",
    # Real Estate
    "AMT": "real_estate", "ARE": "real_estate", "BXP": "real_estate", "DLR": "real_estate",
    "EQIX": "real_estate", "EQR": "real_estate", "EXR": "real_estate", "INVH": "real_estate",
    "AVB": "real_estate", "CCI": "real_estate", "DOC": "real_estate", "KIM": "real_estate",
    "PSA": "real_estate", "SPG": "real_estate", "O": "real_estate", "WELL": "real_estate",
    "PLD": "real_estate", "VTR": "real_estate", "ESS": "real_estate", "FRT": "real_estate",
}

# Reverse map: sector -> set of tickers
SECTOR_TICKERS = {}
for _t, _s in SECTOR_MAP.items():
    SECTOR_TICKERS.setdefault(_s, set()).add(_t)

_LEADER_SERIES: "pd.Series | None" = None  # date -> leading sector string


def _subperiod(date) -> str:
    if pd.isna(date):
        return "unknown"
    d = date.date() if hasattr(date, "date") else date
    if d < pd.Timestamp("2019-04-01").date():
        return "pre_warmup"
    if d <= pd.Timestamp("2021-12-31").date():
        return "period1_bull"
    if d <= pd.Timestamp("2023-12-31").date():
        return "period2_bear"
    return "period3_current"


def _compute_atr(high, low, close, period=ATR_PERIOD):
    prior_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prior_close).abs(),
        (low - prior_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False).mean()


def _load_leaders() -> pd.Series:
    """date -> leading sector (the ETF with best 20d RS vs SPY, if RS>0)."""
    global _LEADER_SERIES
    if _LEADER_SERIES is not None:
        return _LEADER_SERIES

    spy_path = _CACHE_DIR / "SPY.parquet"
    spy = pd.read_parquet(spy_path)
    spy.columns = [c.lower() for c in spy.columns]
    spy = spy.sort_index()
    spy_ret = spy["close"].pct_change(RS_LOOKBACK)

    etf_returns = {}
    for etf, sector in SECTOR_ETFS.items():
        p = _CACHE_DIR / f"{etf}.parquet"
        if not p.exists():
            continue
        d = pd.read_parquet(p)
        d.columns = [c.lower() for c in d.columns]
        d = d.sort_index()
        etf_returns[sector] = d["close"].pct_change(RS_LOOKBACK).reindex(spy.index)

    if not etf_returns:
        _LEADER_SERIES = pd.Series(dtype=object)
        return _LEADER_SERIES

    ret_df = pd.DataFrame(etf_returns)
    rs_df = ret_df.sub(spy_ret.reindex(ret_df.index), axis=0)
    # Leading sector each day = argmax RS; require RS > 0 (outperforming SPY)
    # Guard against all-NaN rows (idxmax raises on fully-NaN rows).
    valid_row = rs_df.notna().any(axis=1)
    best_rs = rs_df.max(axis=1, skipna=True)
    leader = pd.Series(index=rs_df.index, dtype=object)
    if valid_row.any():
        leader.loc[valid_row] = rs_df.loc[valid_row].idxmax(axis=1)
    leader = leader.where(best_rs > 0, other=None)

    # Persistence: require same leader for >= SECTOR_PERSIST_DAYS consecutive days
    s = leader.copy()
    streak = 1
    prev = None
    keep = []
    for idx in s.index:
        cur = s.loc[idx]
        if cur is None or (isinstance(cur, float) and pd.isna(cur)):
            streak = 0
            prev = None
            keep.append(False)
            continue
        if cur == prev:
            streak += 1
        else:
            streak = 1
            prev = cur
        keep.append(streak >= SECTOR_PERSIST_DAYS)
    s = s.where(pd.Series(keep, index=s.index))

    _LEADER_SERIES = s
    return _LEADER_SERIES


def _simulate_exit(df, entry_idx, entry_price, stop_price, target_price):
    closes = df["close"].values
    n = len(closes)
    for offset in range(1, MAX_BARS_HELD + 1):
        idx = entry_idx + offset
        if idx >= n:
            last_idx = min(entry_idx + offset - 1, n - 1)
            return closes[last_idx], "time", offset
        c = closes[idx]
        if c >= target_price:
            return c, "target", offset
        if c <= stop_price:
            return c, "stop", offset
    exit_idx = min(entry_idx + MAX_BARS_HELD, n - 1)
    return closes[exit_idx], "time", MAX_BARS_HELD


def scan(df: pd.DataFrame, ticker: str) -> list:
    """Per-ticker scan for sector-momentum-continuation 10MA pullbacks."""
    sector = SECTOR_MAP.get(ticker)
    if sector is None:
        return []
    if ticker in ("SPY", "VIXINDEX", "VIX3M", "^VIX"):
        return []

    df = df.copy()
    df.sort_index(inplace=True)
    if len(df) < max(MA_TREND_SLOW, VOL_AVG_PERIOD, ATR_PERIOD, MA_PULLBACK) + 10:
        return []

    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"] if "volume" in df.columns else None

    ma10 = close.rolling(MA_PULLBACK, min_periods=MA_PULLBACK).mean()
    ma20 = close.rolling(MA_STOP, min_periods=MA_STOP).mean()
    ma50 = close.rolling(MA_TREND_FAST, min_periods=MA_TREND_FAST).mean()
    ma200 = close.rolling(MA_TREND_SLOW, min_periods=MA_TREND_SLOW).mean()
    atr = _compute_atr(high, low, close)
    vol_avg = volume.rolling(VOL_AVG_PERIOD, min_periods=VOL_AVG_PERIOD).mean() if volume is not None else None

    leaders = _load_leaders()
    leader_aligned = leaders.reindex(df.index).ffill()

    min_start = max(MA_TREND_SLOW, ATR_PERIOD, VOL_AVG_PERIOD, MA_PULLBACK) + 1
    close_arr = close.values
    low_arr = low.values
    ma10_arr = ma10.values
    ma20_arr = ma20.values
    ma50_arr = ma50.values
    ma200_arr = ma200.values
    atr_arr = atr.values
    vol_arr = volume.values if volume is not None else None
    vol_avg_arr = vol_avg.values if vol_avg is not None else None
    lead_arr = leader_aligned.values
    dates = df.index

    signals = []
    n = len(df)
    for i in range(min_start, n):
        lead = lead_arr[i]
        if lead is None or (isinstance(lead, float) and pd.isna(lead)) or lead != sector:
            continue
        if np.isnan(ma10_arr[i]) or np.isnan(ma20_arr[i]) or np.isnan(ma50_arr[i]) or np.isnan(ma200_arr[i]):
            continue
        # Trend agreement
        if not (close_arr[i] > ma50_arr[i] and ma50_arr[i] > ma200_arr[i]):
            continue
        # 10MA pullback: low touched MA10, close recovered above MA10
        if low_arr[i] > ma10_arr[i] or close_arr[i] <= ma10_arr[i]:
            continue
        if np.isnan(atr_arr[i]) or atr_arr[i] <= 0:
            continue
        if atr_arr[i] / close_arr[i] > MAX_ATR_PCT:
            continue
        if vol_arr is None or vol_avg_arr is None:
            continue
        if np.isnan(vol_avg_arr[i]) or vol_avg_arr[i] <= 0:
            continue
        if vol_arr[i] >= VOL_CONTRACTION * vol_avg_arr[i]:
            continue

        entry_price = close_arr[i]
        stop_price = min(ma20_arr[i], low_arr[i]) - STOP_BUFFER_ATR * atr_arr[i]
        risk = entry_price - stop_price
        if risk <= 0 or risk / entry_price < 0.003:
            continue
        target_price = entry_price + MIN_RR * risk

        exit_price, exit_reason, bars_held = _simulate_exit(
            df, i, entry_price, stop_price, target_price)
        realised_r = (exit_price - entry_price) / risk

        signals.append({
            "ticker": ticker,
            "date": dates[i],
            "direction": "long",
            "entry_price": round(float(entry_price), 4),
            "stop_price": round(float(stop_price), 4),
            "target_price": round(float(target_price), 4),
            "exit_price": round(float(exit_price), 4),
            "exit_reason": exit_reason,
            "r_multiple": round(float(realised_r), 4),
            "bars_held": bars_held,
            "subperiod": _subperiod(dates[i]),
            "strategy_id": STRATEGY_ID,
            "sector": sector,
            "leader_sector": str(lead),
        })
    return signals


if __name__ == "__main__":
    import sys
    data_path = Path.home() / ".hermes" / "market_data" / "AAPL.parquet"
    if not data_path.exists():
        print(f"[ERROR] {data_path} not found")
        sys.exit(1)
    d = pd.read_parquet(data_path)
    d.columns = [c.lower() for c in d.columns]
    sigs = scan(d, "AAPL")
    print(f"AAPL signals: {len(sigs)}  (sector={SECTOR_MAP.get('AAPL')})")
