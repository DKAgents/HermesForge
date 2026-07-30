#!/usr/bin/env python3
"""
run_phase1b2_j.py — HermesForge Phase 1B/2 Backtest for STR-J EUFEARIA CCI Reversal
==================================================================================

Phase 1B: Sharpe-ratio asset selection + portfolio-level risk management
Phase 2:  Full portfolio backtest with monthly rebalancing, transaction costs,
          and mean-reversion exit logic (stop/target/time)

Architecture:
  1. Pre-compute EUFEARIA oscillator (modified CCI + EMA + SMA signal line) per asset
  2. Walk forward month-by-month from 2020-01 through present
  3. At each monthly rebalance:
     a. Compute trailing Sharpe ratio for each asset (12-month lookback)
     b. Filter by Sharpe gate (>= 0.3 for longs)
     c. Rank by avg dollar volume, select top 15
     d. Allocate capital equally across selected assets
  4. Between rebalances: check for CCI crossover signals at oversold extremes
  5. Track positions with stop (1 ATR), target (mean reversion), time stop (10 bars)
  6. Apply transaction costs (stocks: 0.15% per side)

Usage:
    python3 scripts/validation/run_phase1b2_j.py
"""

import sys
import pathlib
import datetime
import numpy as np
import pandas as pd

# ── Path setup ──────────────────────────────────────────────────────────────
REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validation"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "paper_trading"))

from fetch_data import load_all as load_stocks
from scanners.scanner_j_eufearia_cci import _compute_eufearia_oscillator, _compute_atr, _compute_hlc3

RESULTS_DIR = REPO_ROOT / "scripts" / "validation" / "results"

# ── Parameters ───────────────────────────────────────────────────────────────
SHARPE_LOOKBACK_MONTHS = 12
SHARPE_GATE_LONG = 0.3
K_LONG = 15
COST_STOCKS = 0.0015  # 0.15% per side
RISK_PER_TRADE = 0.01
MAX_PORTFOLIO_HEAT = 0.15
INITIAL_CAPITAL = 100_000

# EUFEARIA parameters (from Phase 1A validated config)
CHANNEL_LENGTH = 10
SIGNAL_LENGTH = 21
SIGNAL_LINE_PERIOD = 4
OB_LEVEL = 50
OS_LEVEL = -50
STRICT_EXTREME = True
ATR_PERIOD = 14
ATR_STOP_MULTIPLIER = 1.0
MAX_BARS_HELD = 10
MIN_RR = 2.0
CCI_CONSTANT = 0.015


# ── Pre-computed asset data ──────────────────────────────────────────────────

class EufeariaAsset:
    """Pre-computed EUFEARIA indicators for a single asset."""
    def __init__(self, ticker: str, df: pd.DataFrame):
        self.ticker = ticker
        self.df = df
        self.close = df["close"]
        self.high = df["high"]
        self.low = df["low"]
        self.volume = df["volume"]
        self.atr = _compute_atr(df, ATR_PERIOD)
        self.osc, self.sig = _compute_eufearia_oscillator(
            df, CHANNEL_LENGTH, SIGNAL_LENGTH, SIGNAL_LINE_PERIOD
        )
        # Pre-compute crossover signals
        above = self.osc > self.sig
        below = self.osc < self.sig
        prev_above = above.shift(1).fillna(False)
        prev_below = below.shift(1).fillna(False)
        self.cross_up = above & prev_below    # bullish crossover
        self.cross_down = below & prev_above  # bearish crossunder

    def dollar_volume(self, as_of: pd.Timestamp, lookback_days: int = 60) -> float:
        start = as_of - pd.Timedelta(days=lookback_days)
        mask = (self.df.index >= start) & (self.df.index <= as_of)
        window = self.df.loc[mask]
        if len(window) == 0:
            return 0.0
        return float((window["close"] * window["volume"]).mean())

    def trailing_sharpe(self, as_of: pd.Timestamp,
                        lookback_months: int = SHARPE_LOOKBACK_MONTHS) -> float:
        start = as_of - pd.DateOffset(months=lookback_months)
        window = self.close.loc[start:as_of]
        if len(window) < 30:
            return 0.0
        returns = window.pct_change().dropna()
        if returns.std() == 0 or len(returns) < 20:
            return 0.0
        return float(returns.mean() / returns.std() * np.sqrt(252))


# ── Portfolio Backtest ──────────────────────────────────────────────────────

class EufeariaBacktest:
    def __init__(self):
        self.equity = INITIAL_CAPITAL
        self.equity_curve = []
        self.positions = {}  # ticker -> position dict
        self.closed_trades = []
        self.rebalance_log = []
        self.cost_rate = COST_STOCKS

    def run(self, data: dict[str, pd.DataFrame]) -> dict:
        print(f"\n{'='*60}")
        print(f"Phase 1B/2 Backtest — STR-J EUFEARIA CCI Reversal (stocks, long-only)")
        print(f"{'='*60}")

        # Pre-compute indicators
        print("Pre-computing EUFEARIA indicators...")
        assets = {}
        for ticker, df in data.items():
            if len(df) >= 250:
                assets[ticker] = EufeariaAsset(ticker, df)
        print(f"  {len(assets)} assets with sufficient history")

        # Build unified date index
        all_dates = sorted(set(d for a in assets.values() for d in a.df.index))
        all_dates = [d for d in all_dates if d >= pd.Timestamp("2020-01-01")]
        print(f"  Date range: {all_dates[0].date()} to {all_dates[-1].date()} ({len(all_dates)} bars)")

        # Monthly rebalance dates
        rebalance_set = set()
        seen = set()
        for d in all_dates:
            key = (d.year, d.month)
            if key not in seen:
                seen.add(key)
                rebalance_set.add(d)
        rebalance_dates = sorted(rebalance_set)
        print(f"  {len(rebalance_dates)} monthly rebalances")

        universe = []
        per_asset_cap = 0
        reb_idx = 0

        for date in all_dates:
            # Monthly rebalance
            if reb_idx < len(rebalance_dates) and date >= rebalance_dates[reb_idx]:
                universe, per_asset_cap = self._rebalance(assets, date)
                reb_idx += 1

            # Update existing positions (check stops/targets/time)
            self._update_positions(assets, date)

            # Check for new entries
            self._check_entries(assets, date, universe, per_asset_cap)

            # Mark-to-market
            mtm = self._mark_to_market(assets, date)
            self.equity_curve.append({"date": date, "equity": mtm})

        # Close remaining positions
        self._close_all(assets, all_dates[-1])

        return self._metrics()

    def _rebalance(self, assets: dict, date: pd.Timestamp) -> tuple[list[str], float]:
        """Monthly rebalance: select universe by Sharpe + dollar volume."""
        candidates = []
        for ticker, a in assets.items():
            if date not in a.df.index:
                continue
            sharpe = a.trailing_sharpe(date)
            dvol = a.dollar_volume(date)
            candidates.append({"ticker": ticker, "sharpe": sharpe, "dvol": dvol})

        # Sharpe gate
        long_cands = [c for c in candidates if c["sharpe"] >= SHARPE_GATE_LONG]
        long_cands.sort(key=lambda x: x["dvol"], reverse=True)
        selected = [c["ticker"] for c in long_cands[:K_LONG]]

        # Capital allocation
        n = len(selected)
        per_cap = self.equity / max(n, 1) if n > 0 else 0

        self.rebalance_log.append({
            "date": str(date.date()),
            "n_selected": n,
            "equity": round(self.equity, 2),
        })

        print(f"  Rebalance {date.date()}: {n} selected | ${self.equity:,.0f}")
        return selected, per_cap

    def _check_entries(self, assets: dict, date: pd.Timestamp,
                       universe: list[str], per_cap: float):
        """Check for new CCI crossover signals at oversold extremes."""
        if len(self.positions) * RISK_PER_TRADE >= MAX_PORTFOLIO_HEAT:
            return

        for ticker in universe:
            if ticker in self.positions or ticker not in assets:
                continue
            a = assets[ticker]
            if date not in a.df.index:
                continue

            idx = a.df.index.get_loc(date)
            if idx < max(CHANNEL_LENGTH, SIGNAL_LENGTH, ATR_PERIOD) + SIGNAL_LINE_PERIOD + 5:
                continue

            # Check for bullish crossover at oversold
            if not a.cross_up.iloc[idx]:
                continue

            osc_val = a.osc.iloc[idx]
            sig_val = a.sig.iloc[idx]
            atr_val = a.atr.iloc[idx]

            if np.isnan(osc_val) or np.isnan(sig_val) or np.isnan(atr_val):
                continue

            # Must be at oversold extreme
            if osc_val > OS_LEVEL:
                continue

            # Strict extreme: signal line also at oversold
            if STRICT_EXTREME and sig_val > OS_LEVEL:
                continue

            entry_price = float(a.close.iloc[idx])
            stop_price = entry_price - ATR_STOP_MULTIPLIER * float(atr_val)

            # Target: mean reversion toward zero line
            reversion_pct = abs(osc_val) / 100.0
            target_price = entry_price * (1 + min(reversion_pct, 0.15))

            risk = abs(entry_price - stop_price)
            reward = abs(target_price - entry_price)
            if risk <= 0 or reward / risk < MIN_RR:
                continue

            self._open_position(ticker, entry_price, stop_price, target_price,
                                per_cap, atr_val, date)

    def _open_position(self, ticker: str, entry_price: float, stop_price: float,
                       target_price: float, cap: float, atr_val: float,
                       date: pd.Timestamp):
        """Open a long position."""
        risk_per_share = abs(entry_price - stop_price)
        max_risk = self.equity * RISK_PER_TRADE
        shares_risk = int(max_risk / risk_per_share)
        shares_cap = int(cap / entry_price)
        shares = min(shares_risk, shares_cap)
        if shares <= 0:
            return

        cost = shares * entry_price * self.cost_rate
        self.equity -= cost

        self.positions[ticker] = {
            "direction": "long",
            "entry_price": entry_price,
            "stop_price": stop_price,
            "target_price": target_price,
            "entry_date": date,
            "shares": shares,
            "capital": shares * entry_price,
            "bars_held": 0,
        }

    def _update_positions(self, assets: dict, date: pd.Timestamp):
        """Check stop, target, and time exits for open positions."""
        to_close = []

        for ticker, pos in self.positions.items():
            if ticker not in assets:
                continue
            a = assets[ticker]
            if date not in a.df.index:
                continue

            pos["bars_held"] += 1
            high = float(a.high.loc[date])
            low = float(a.low.loc[date])

            # Check stop (long)
            if low <= pos["stop_price"]:
                to_close.append((ticker, pos["stop_price"], "stop"))
            # Check target
            elif high >= pos["target_price"]:
                to_close.append((ticker, pos["target_price"], "target"))
            # Time stop
            elif pos["bars_held"] >= MAX_BARS_HELD:
                close_price = float(a.close.loc[date])
                to_close.append((ticker, close_price, "time"))

        for ticker, exit_price, reason in to_close:
            self._close(ticker, exit_price, reason, date)

    def _close(self, ticker: str, exit_price: float, reason: str,
               date: pd.Timestamp):
        pos = self.positions.pop(ticker)
        pnl = (exit_price - pos["entry_price"]) * pos["shares"]
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
                close_price = float(assets[ticker].close.loc[date])
                self._close(ticker, close_price, "rebalance", date)

    def _mark_to_market(self, assets: dict, date: pd.Timestamp) -> float:
        mtm = self.equity
        for ticker, pos in self.positions.items():
            if ticker in assets and date in assets[ticker].df.index:
                price = float(assets[ticker].close.loc[date])
                mtm += (price - pos["entry_price"]) * pos["shares"]
        return mtm

    def _metrics(self) -> dict:
        if not self.equity_curve:
            return {"error": "No equity curve data"}

        eq_df = pd.DataFrame(self.equity_curve).set_index("date")
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

        # Exit reason breakdown
        exit_reasons = {}
        for t in trades:
            r = t["exit_reason"]
            exit_reasons[r] = exit_reasons.get(r, 0) + 1

        return {
            "asset_class": "stocks (long-only)",
            "strategy": "STR-J EUFEARIA CCI Reversal",
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
            "exit_reasons": exit_reasons,
        }


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    print("Loading stock data...")
    stock_data = load_stocks()
    print(f"  {len(stock_data)} tickers loaded")

    bt = EufeariaBacktest()
    result = bt.run(stock_data)

    # Save results
    if bt.equity_curve:
        pd.DataFrame(bt.equity_curve).to_csv(
            RESULTS_DIR / "STR-J-phase1b2-stocks-equity.csv", index=False)
    if bt.closed_trades:
        pd.DataFrame(bt.closed_trades).to_csv(
            RESULTS_DIR / "STR-J-phase1b2-stocks-trades.csv", index=False)
    if bt.rebalance_log:
        pd.DataFrame(bt.rebalance_log).to_csv(
            RESULTS_DIR / "STR-J-phase1b2-stocks-rebalances.csv", index=False)

    # Print summary
    print(f"\n{'='*60}")
    print("PHASE 1B/2 RESULTS — STR-J EUFEARIA CCI Reversal")
    print(f"{'='*60}")

    if "error" in result:
        print(f"ERROR: {result['error']}")
        return

    print(f"\n  Period:          {result['start']} to {result['end']} ({result['years']} years)")
    print(f"  Initial capital: ${INITIAL_CAPITAL:,}")
    print(f"  Final equity:    ${result['final_equity']:,.2f}")
    print(f"  Total return:    {result['total_return_pct']:+.1f}%")
    print(f"  Annual return:   {result['annual_return_pct']:+.1f}%")
    print(f"  Annual vol:      {result['annual_vol_pct']:.1f}%")
    print(f"  Sharpe:          {result['sharpe']:.3f}")
    print(f"  Sortino:         {result['sortino']:.3f}")
    print(f"  Max drawdown:    {result['max_drawdown_pct']:.1f}%")
    print(f"  Calmar:          {result['calmar']:.3f}")
    print(f"  Trades:          {result['n_trades']}")
    print(f"  Win rate:        {result['win_rate_pct']:.1f}%")
    print(f"  Avg PnL:         ${result['avg_pnl']:.2f}")
    print(f"  Avg hold:        {result['avg_hold_days']:.1f} days")
    print(f"  Rebalances:      {result['n_rebalances']}")
    print(f"  Exit reasons:    {result['exit_reasons']}")

    # Comparison with Phase 1A
    print(f"\n  Phase 1A (per-asset, frictionless): avg R +0.222, win 41.1%, 1,046 sig/yr")
    print(f"  Phase 1B/2 (portfolio, with costs): Sharpe {result['sharpe']:.3f}, "
          f"win {result['win_rate_pct']:.1f}%, {result['n_trades']} trades")

    # Save summary
    summary_path = RESULTS_DIR / "STR-J-phase1b2-summary.txt"
    with open(summary_path, "w") as f:
        f.write("PHASE 1B/2 RESULTS — STR-J EUFEARIA CCI Reversal\n")
        f.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        for k, v in result.items():
            f.write(f"  {k}: {v}\n")
    print(f"\nSummary saved → {summary_path}")


if __name__ == "__main__":
    main()
