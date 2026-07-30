#!/usr/bin/env python3
"""
run_phase1b2.py — HermesForge Phase 1B/2 Backtest for STR-I AdaptiveTrend
=========================================================================

Phase 1B: Monthly walk-forward parameter optimization + Sharpe-ratio asset selection
Phase 2:  Full portfolio backtest with market-cap filter, 70/30 allocation,
          monthly rebalancing, and transaction cost modeling.

Optimized approach: pre-compute indicators (momentum, ATR, SMA200) once per
asset, then do lightweight signal checks on each bar using the current
month's optimized parameters.

Usage:
    python3 scripts/validation/run_phase1b2.py [--asset-class stocks|crypto|both]
"""

import sys
import argparse
import pathlib
import datetime
import numpy as np
import pandas as pd
from collections import defaultdict

# ── Path setup ──────────────────────────────────────────────────────────────
REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validation"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "paper_trading"))

from fetch_data import load_all as load_stocks
from fetch_crypto_data import load_all as load_crypto
from scanners.scanner_i_adaptive_trend import _compute_atr, _compute_momentum, _simulate_trailing_exit

RESULTS_DIR = REPO_ROOT / "scripts" / "validation" / "results"

# ── Phase 1B/2 Parameters ────────────────────────────────────────────────────

OPTIMIZATION_WINDOW_MONTHS = 6
SHARPE_LOOKBACK_MONTHS = 12

PARAM_GRID_L = [10, 20]
PARAM_GRID_THETA = [0.10, 0.20]
PARAM_GRID_ALPHA = [2.0, 2.5]
PARAM_GRID_MAX_BARS = [90, 120]
OPTIMIZE_EVERY_N_REBALANCES = 3  # re-optimize quarterly, not monthly

K_LONG = 15
K_SHORT = 15
LAMBDA = 0.70
SHARPE_GATE_LONG = 0.3
SHARPE_GATE_SHORT = 0.5

COST_STOCKS = 0.0015
COST_CRYPTO = 0.0007

RISK_PER_TRADE = 0.01
MAX_PORTFOLIO_HEAT = 0.15    # 15% — allows up to 15 concurrent positions at 1% each
INITIAL_CAPITAL = 100_000


# ── Pre-computed indicators per asset ────────────────────────────────────────

class AssetData:
    """Pre-computed indicators for a single asset, avoiding repeated computation."""
    def __init__(self, ticker: str, df: pd.DataFrame):
        self.ticker = ticker
        self.df = df
        self.close = df["close"]
        self.high = df["high"]
        self.low = df["low"]
        self.volume = df["volume"]
        self.atr = _compute_atr(df, 14)
        self.sma200 = df["close"].rolling(200, min_periods=50).mean()
        self._momentum_cache = {}

    def momentum(self, L: int) -> pd.Series:
        if L not in self._momentum_cache:
            self._momentum_cache[L] = self.close.pct_change(periods=L)
        return self._momentum_cache[L]

    def dollar_volume(self, as_of: pd.Timestamp, lookback_days: int = 60) -> float:
        start = as_of - pd.Timedelta(days=lookback_days)
        mask = (self.df.index >= start) & (self.df.index <= as_of)
        window = self.df.loc[mask]
        if len(window) == 0:
            return 0.0
        return float((window["close"] * window["volume"]).mean())

    def trailing_sharpe(self, as_of: pd.Timestamp, lookback_months: int = SHARPE_LOOKBACK_MONTHS) -> float:
        start = as_of - pd.DateOffset(months=lookback_months)
        window = self.close.loc[start:as_of]
        if len(window) < 30:
            return 0.0
        returns = window.pct_change().dropna()
        if returns.std() == 0 or len(returns) < 20:
            return 0.0
        return float(returns.mean() / returns.std() * np.sqrt(252))


# ── Signal check (lightweight, per-bar) ─────────────────────────────────────

def check_signal(asset: AssetData, idx: int, L: int, theta: float,
                 alpha: float, long_only: bool) -> dict | None:
    """Check if a momentum entry signal fires at bar idx. Returns signal dict or None."""
    if idx < max(L, 200, 15):
        return None

    mom_val = asset.momentum(L).iloc[idx]
    if np.isnan(mom_val):
        return None

    atr_val = asset.atr.iloc[idx]
    if np.isnan(atr_val):
        return None

    sma_val = asset.sma200.iloc[idx]
    if np.isnan(sma_val):
        return None

    price = asset.close.iloc[idx]
    price_above_sma = price > sma_val

    if mom_val > theta:
        if not price_above_sma:
            return None
        direction = "long"
    elif mom_val < -theta:
        if long_only:
            return None
        if price_above_sma:
            return None
        direction = "short"
    else:
        return None

    if direction == "long":
        stop = price - alpha * atr_val
    else:
        stop = price + alpha * atr_val

    risk = abs(price - stop)
    if risk <= 0:
        return None

    return {
        "date": asset.df.index[idx],
        "ticker": asset.ticker,
        "direction": direction,
        "entry_price": float(price),
        "stop_price": float(stop),
        "momentum": float(mom_val),
        "atr": float(atr_val),
        "risk_per_share": float(risk),
    }


def simulate_exit(asset: AssetData, entry_idx: int, direction: str,
                   entry_price: float, initial_stop: float, alpha: float,
                   max_bars: int) -> tuple[float, str, int, float]:
    """Simulate trailing stop exit from entry_idx forward."""
    return _simulate_trailing_exit(
        asset.df, entry_idx, direction, entry_price, initial_stop, asset.atr
    )


# ── Parameter optimization ──────────────────────────────────────────────────

def optimize_params(asset: AssetData, as_of: pd.Timestamp, long_only: bool) -> tuple:
    """Grid search optimal params on trailing window."""
    start = as_of - pd.DateOffset(months=OPTIMIZATION_WINDOW_MONTHS)
    end_idx = asset.df.index.get_loc(as_of)
    start_idx = asset.df.index.get_loc(asset.df.index[asset.df.index >= start][0])

    if end_idx - start_idx < 100:
        return (10, 0.20, 2.0, 120)

    best_r = -999
    best_params = (10, 0.20, 2.0, 120)

    for L in PARAM_GRID_L:
        mom = asset.momentum(L)
        for theta in PARAM_GRID_THETA:
            for alpha in PARAM_GRID_ALPHA:
                for max_bars in PARAM_GRID_MAX_BARS:
                    rs = []
                    next_entry = start_idx
                    for i in range(start_idx, end_idx):
                        if i < next_entry:
                            continue
                        sig = check_signal(asset, i, L, theta, alpha, long_only)
                        if sig is None:
                            continue
                        try:
                            exit_price, reason, bars_held, _ = simulate_exit(
                                asset, i, sig["direction"], sig["entry_price"],
                                sig["stop_price"], alpha, max_bars
                            )
                            if sig["direction"] == "long":
                                r = (exit_price - sig["entry_price"]) / sig["risk_per_share"]
                            else:
                                r = (sig["entry_price"] - exit_price) / sig["risk_per_share"]
                            if not np.isnan(r):
                                rs.append(r)
                            next_entry = i + bars_held + 1
                        except Exception:
                            continue
                    if len(rs) >= 3:
                        avg_r = np.mean(rs)
                        if avg_r > best_r:
                            best_r = avg_r
                            best_params = (L, theta, alpha, max_bars)

    return best_params


# ── Portfolio Backtest ──────────────────────────────────────────────────────

class PortfolioBacktest:
    def __init__(self, asset_class: str = "both"):
        self.asset_class = asset_class
        self.equity = INITIAL_CAPITAL
        self.equity_curve = []
        self.positions = {}  # ticker -> position dict
        self.closed_trades = []
        self.rebalance_log = []
        self.cost_rate = COST_STOCKS if asset_class == "stocks" else COST_CRYPTO
        # Both stocks and crypto are long-only (shorts proven negative in Phase 1A)
        self.long_only = True

    def run(self, data: dict[str, pd.DataFrame]) -> dict:
        print(f"\n{'='*60}")
        print(f"Phase 1B/2 Backtest — STR-I AdaptiveTrend ({self.asset_class})")
        print(f"{'='*60}")

        long_only = self.long_only

        # Pre-compute indicators for all assets
        print("Pre-computing indicators...")
        assets = {}
        for ticker, df in data.items():
            if len(df) >= 250:
                assets[ticker] = AssetData(ticker, df)
        print(f"  {len(assets)} assets with sufficient history")

        # Build unified date index
        all_dates = sorted(set(d for a in assets.values() for d in a.df.index))
        all_dates = [d for d in all_dates if d >= pd.Timestamp("2020-01-01")]
        print(f"  Date range: {all_dates[0].date()} to {all_dates[-1].date()} ({len(all_dates)} bars)")

        # Monthly rebalance dates (1st trading day of each month)
        rebalance_set = set()
        seen = set()
        for d in all_dates:
            key = (d.year, d.month)
            if key not in seen:
                seen.add(key)
                rebalance_set.add(d)
        rebalance_dates = sorted(rebalance_set)
        print(f"  {len(rebalance_dates)} monthly rebalances")

        current_params = (10, 0.20, 2.0, 120)
        long_universe = []
        short_universe = []
        long_cap = 0
        short_cap = 0
        reb_idx = 0
        reb_count = 0

        for date in all_dates:

            # Monthly rebalance — DON'T close existing positions, just update universe + params
            if reb_idx < len(rebalance_dates) and date >= rebalance_dates[reb_idx]:
                current_params, long_universe, short_universe, long_cap, short_cap = \
                    self._rebalance(assets, date, long_only, reb_count)
                reb_idx += 1
                reb_count += 1

            # Update existing positions (check trailing stops)
            self._update_stops(assets, date, current_params[2])

            # Check for new entries
            self._check_entries(assets, date, long_universe, short_universe,
                                current_params, long_only, long_cap, short_cap)

            # Mark-to-market
            mtm = self._mark_to_market(assets, date)
            self.equity_curve.append({"date": date, "equity": mtm})

        # Close remaining
        self._close_all(assets, all_dates[-1])

        return self._metrics()

    def _rebalance(self, assets: dict, date: pd.Timestamp, long_only: bool,
                   reb_count: int = 0):
        """Monthly rebalance: optimize params, select universe."""
        # 1. Score all assets
        candidates = []
        for ticker, a in assets.items():
            if date not in a.df.index:
                continue
            sharpe = a.trailing_sharpe(date)
            dvol = a.dollar_volume(date)
            candidates.append({"ticker": ticker, "sharpe": sharpe, "dvol": dvol})

        # 2. Sharpe gate
        long_cands = [c for c in candidates if c["sharpe"] >= SHARPE_GATE_LONG]
        short_cands = [c for c in candidates if c["sharpe"] >= SHARPE_GATE_SHORT] if not long_only else []

        # 3. Rank by dollar volume, select top K
        long_cands.sort(key=lambda x: x["dvol"], reverse=True)
        long_selected = [c["ticker"] for c in long_cands[:K_LONG]]
        short_cands.sort(key=lambda x: x["dvol"], reverse=True)
        short_selected = [c["ticker"] for c in short_cands[:K_SHORT]] if not long_only else []

        # 4. Optimize params (quarterly, not monthly)
        if 'best_params' not in self.__dict__:
            self.best_params = (10, 0.20, 2.0, 120)
        if reb_count % OPTIMIZE_EVERY_N_REBALANCES == 0 and long_selected:
            opt_asset = assets[long_selected[0]]
            self.best_params = optimize_params(opt_asset, date, long_only)
        best_params = self.best_params

        # 5. Capital allocation
        n_long = len(long_selected)
        n_short = len(short_selected)
        if long_only:
            per_long = self.equity / max(n_long, 1) if n_long > 0 else 0
            per_short = 0
        else:
            per_long = (self.equity * LAMBDA) / max(n_long, 1) if n_long > 0 else 0
            per_short = (self.equity * (1 - LAMBDA)) / max(n_short, 1) if n_short > 0 else 0

        self.rebalance_log.append({
            "date": str(date.date()),
            "n_long": n_long,
            "n_short": n_short,
            "params_L": best_params[0],
            "params_theta": best_params[1],
            "params_alpha": best_params[2],
            "params_max_bars": best_params[3],
            "equity": round(self.equity, 2),
        })

        print(f"  Rebalance {date.date()}: L={best_params[0]} θ={best_params[1]} "
              f"α={best_params[2]} max_bars={best_params[3]} | "
              f"L:{n_long} S:{n_short} | ${self.equity:,.0f}")

        return best_params, long_selected, short_selected, per_long, per_short

    def _check_entries(self, assets: dict, date: pd.Timestamp,
                       long_univ: list, short_univ: list,
                       params: tuple, long_only: bool,
                       long_cap: float, short_cap: float):
        L, theta, alpha, max_bars = params

        # Portfolio heat check
        if len(self.positions) * RISK_PER_TRADE >= MAX_PORTFOLIO_HEAT:
            return

        for ticker in long_univ:
            if ticker in self.positions or ticker not in assets:
                continue
            a = assets[ticker]
            if date not in a.df.index:
                continue
            idx = a.df.index.get_loc(date)
            sig = check_signal(a, idx, L, theta, alpha, True)
            if sig:
                self._open(sig, long_cap, alpha, max_bars, a, idx)

        if not long_only:
            for ticker in short_univ:
                if ticker in self.positions or ticker not in assets:
                    continue
                a = assets[ticker]
                if date not in a.df.index:
                    continue
                idx = a.df.index.get_loc(date)
                sig = check_signal(a, idx, L, theta, alpha, False)
                if sig:
                    self._open(sig, short_cap, alpha, max_bars, a, idx)

    def _open(self, sig: dict, cap: float, alpha: float, max_bars: int,
              asset: AssetData, entry_idx: int):
        if cap <= 0:
            return
        risk_per_share = sig["risk_per_share"]
        max_risk = self.equity * RISK_PER_TRADE
        shares_risk = int(max_risk / risk_per_share)
        shares_cap = int(cap / sig["entry_price"])
        shares = min(shares_risk, shares_cap)
        if shares <= 0:
            return

        cost = shares * sig["entry_price"] * self.cost_rate
        self.equity -= cost

        self.positions[sig["ticker"]] = {
            "direction": sig["direction"],
            "entry_price": sig["entry_price"],
            "stop_price": sig["stop_price"],
            "entry_date": sig["date"],
            "entry_idx": entry_idx,
            "shares": shares,
            "capital": shares * sig["entry_price"],
            "alpha": alpha,
            "max_bars": max_bars,
        }

    def _update_stops(self, assets: dict, date: pd.Timestamp, alpha: float):
        to_close = []
        for ticker, pos in self.positions.items():
            if ticker not in assets:
                continue
            a = assets[ticker]
            if date not in a.df.index:
                continue

            high = a.high.loc[date]
            low = a.low.loc[date]
            close = a.close.loc[date]
            atr_val = a.atr.loc[date]

            if pos["direction"] == "long":
                # Check OLD stop first (before updating)
                if low <= pos["stop_price"]:
                    to_close.append((ticker, pos["stop_price"], "stop"))
                elif not np.isnan(atr_val):
                    # Then update trailing stop (monotonic up)
                    pos["stop_price"] = max(pos["stop_price"],
                                            float(close) - alpha * float(atr_val))
            else:
                # Check OLD stop first
                if high >= pos["stop_price"]:
                    to_close.append((ticker, pos["stop_price"], "stop"))
                elif not np.isnan(atr_val):
                    # Then update trailing stop (monotonic down)
                    pos["stop_price"] = min(pos["stop_price"],
                                            float(close) + alpha * float(atr_val))

        for ticker, exit_price, reason in to_close:
            self._close(ticker, exit_price, reason, date)

    def _close(self, ticker: str, exit_price: float, reason: str, date: pd.Timestamp):
        pos = self.positions.pop(ticker)
        if pos["direction"] == "long":
            pnl = (exit_price - pos["entry_price"]) * pos["shares"]
        else:
            pnl = (pos["entry_price"] - exit_price) * pos["shares"]
        cost = pos["shares"] * exit_price * self.cost_rate
        pnl -= cost
        self.equity += pnl

        self.closed_trades.append({
            "ticker": ticker,
            "direction": pos["direction"],
            "entry_date": str(pos["entry_date"].date()),
            "exit_date": str(date.date()),
            "entry_price": pos["entry_price"],
            "exit_price": exit_price,
            "shares": pos["shares"],
            "pnl": round(pnl, 2),
            "exit_reason": reason,
            "hold_days": (date - pos["entry_date"]).days,
        })

    def _close_all(self, assets: dict, date: pd.Timestamp):
        for ticker in list(self.positions.keys()):
            if ticker in assets and date in assets[ticker].df.index:
                close_price = assets[ticker].close.loc[date]
                self._close(ticker, float(close_price), "rebalance", date)

    def _mark_to_market(self, assets: dict, date: pd.Timestamp) -> float:
        mtm = self.equity
        for ticker, pos in self.positions.items():
            if ticker in assets and date in assets[ticker].df.index:
                price = assets[ticker].close.loc[date]
                if pos["direction"] == "long":
                    mtm += (float(price) - pos["entry_price"]) * pos["shares"]
                else:
                    mtm += (pos["entry_price"] - float(price)) * pos["shares"]
        return mtm

    def _metrics(self) -> dict:
        if not self.equity_curve:
            return {"error": "No equity curve data"}

        eq_df = pd.DataFrame(self.equity_curve).set_index("date")
        # Drop any NaN rows (edge case at end of backtest)
        eq_df = eq_df.dropna(subset=["equity"])
        if len(eq_df) < 2:
            return {"error": "Insufficient equity curve data"}
        eq_df["daily_return"] = eq_df["equity"].pct_change()

        total_ret = eq_df["equity"].iloc[-1] / INITIAL_CAPITAL - 1
        years = (eq_df.index[-1] - eq_df.index[0]).days / 365.25
        ann_ret = (1 + total_ret) ** (1 / years) - 1 if years > 0 else 0

        dr = eq_df["daily_return"].dropna()
        ann_vol = dr.std() * np.sqrt(252)
        sharpe = (dr.mean() / dr.std() * np.sqrt(252)) if dr.std() > 0 else 0

        downside = dr[dr < 0]
        sortino = (dr.mean() / downside.std() * np.sqrt(252)) if len(downside) > 0 and downside.std() > 0 else 0

        rolling_max = eq_df["equity"].cummax()
        dd = (eq_df["equity"] - rolling_max) / rolling_max
        max_dd = float(dd.min())
        calmar = ann_ret / abs(max_dd) if max_dd < 0 else 0

        trades = self.closed_trades
        n = len(trades)
        wins = sum(1 for t in trades if t["pnl"] > 0)
        win_rate = wins / n * 100 if n > 0 else 0
        avg_pnl = np.mean([t["pnl"] for t in trades]) if trades else 0
        avg_hold = np.mean([t["hold_days"] for t in trades]) if trades else 0

        return {
            "asset_class": self.asset_class,
            "start": str(eq_df.index[0].date()),
            "end": str(eq_df.index[-1].date()),
            "years": round(years, 2),
            "final_equity": round(eq_df["equity"].iloc[-1], 2),
            "total_return_pct": round(total_ret * 100, 2),
            "annual_return_pct": round(ann_ret * 100, 2),
            "annual_vol_pct": round(ann_vol * 100, 2),
            "sharpe": round(sharpe, 3),
            "sortino": round(sortino, 3),
            "max_drawdown_pct": round(max_dd * 100, 2),
            "calmar": round(calmar, 3),
            "n_trades": n,
            "win_rate_pct": round(win_rate, 1),
            "avg_pnl": round(avg_pnl, 2),
            "avg_hold_days": round(avg_hold, 1),
            "n_rebalances": len(self.rebalance_log),
        }


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Phase 1B/2 backtest for STR-I")
    parser.add_argument("--asset-class", choices=["stocks", "crypto", "both"],
                        default="both")
    args = parser.parse_args()

    results = {}

    if args.asset_class in ("stocks", "both"):
        print("Loading stock data...")
        stock_data = load_stocks()
        print(f"  {len(stock_data)} tickers loaded")

        bt = PortfolioBacktest(asset_class="stocks")
        results["stocks"] = bt.run(stock_data)

        if bt.equity_curve:
            pd.DataFrame(bt.equity_curve).to_csv(
                RESULTS_DIR / "STR-I-phase1b2-stocks-equity.csv", index=False)
        if bt.closed_trades:
            pd.DataFrame(bt.closed_trades).to_csv(
                RESULTS_DIR / "STR-I-phase1b2-stocks-trades.csv", index=False)
        if bt.rebalance_log:
            pd.DataFrame(bt.rebalance_log).to_csv(
                RESULTS_DIR / "STR-I-phase1b2-stocks-rebalances.csv", index=False)

    if args.asset_class in ("crypto", "both"):
        print("\nLoading crypto data...")
        crypto_data = load_crypto()
        for t, df in crypto_data.items():
            if "subperiod" not in df.columns:
                df["subperiod"] = "crypto"
        print(f"  {len(crypto_data)} tickers loaded")

        bt = PortfolioBacktest(asset_class="crypto")
        results["crypto"] = bt.run(crypto_data)

        if bt.equity_curve:
            pd.DataFrame(bt.equity_curve).to_csv(
                RESULTS_DIR / "STR-I-phase1b2-crypto-equity.csv", index=False)
        if bt.closed_trades:
            pd.DataFrame(bt.closed_trades).to_csv(
                RESULTS_DIR / "STR-I-phase1b2-crypto-trades.csv", index=False)
        if bt.rebalance_log:
            pd.DataFrame(bt.rebalance_log).to_csv(
                RESULTS_DIR / "STR-I-phase1b2-crypto-rebalances.csv", index=False)

    # Summary
    print(f"\n{'='*60}")
    print("PHASE 1B/2 RESULTS SUMMARY")
    print(f"{'='*60}")
    print(f"{'Asset':<10} {'AnnRet':>8} {'Sharpe':>8} {'Sortino':>8} {'MaxDD':>8} {'Calmar':>8} {'Trades':>7} {'Win%':>6}")
    print("-" * 70)
    for asset, m in results.items():
        if "error" in m:
            print(f"{asset:<10} ERROR: {m['error']}")
        else:
            print(f"{asset:<10} {m['annual_return_pct']:>7.1f}% {m['sharpe']:>8.3f} "
                  f"{m['sortino']:>8.3f} {m['max_drawdown_pct']:>7.1f}% {m['calmar']:>8.3f} "
                  f"{m['n_trades']:>7} {m['win_rate_pct']:>5.1f}%")

    print(f"\nInitial capital: ${INITIAL_CAPITAL:,}")
    for asset, m in results.items():
        if "error" not in m:
            print(f"  {asset}: ${m['final_equity']:,.2f} ({m['total_return_pct']:+.1f}% over {m['years']}y)")

    # Save summary
    summary_path = RESULTS_DIR / "STR-I-phase1b2-summary.txt"
    with open(summary_path, "w") as f:
        f.write("PHASE 1B/2 RESULTS — STR-I AdaptiveTrend\n")
        f.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        for asset, m in results.items():
            f.write(f"=== {asset.upper()} ===\n")
            for k, v in m.items():
                f.write(f"  {k}: {v}\n")
            f.write("\n")
    print(f"\nSummary saved → {summary_path}")


if __name__ == "__main__":
    main()
