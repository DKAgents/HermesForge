#!/usr/bin/env python3
"""
Parameter sweep for AdaptiveTrend scanner with trend filter.
Tests L, theta, alpha, max_bars on a representative sample.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "paper_trading"))

import pandas as pd
import numpy as np
from scanners.scanner_i_adaptive_trend import _compute_atr, _compute_momentum, _simulate_trailing_exit
import scanners.scanner_i_adaptive_trend as mod
from fetch_data import load_all

data = load_all()
print(f"Loaded {len(data)} tickers")

# Representative sample: 20 liquid stocks + 5 crypto
sample_tickers = ['AAPL','MSFT','NVDA','AMZN','GOOGL','META','TSLA','JPM','V','JNJ',
                  'SPY','QQQ','IWM','XLF','XLK','GLD','SLV','XLE','XLY','XLU',
                  'BTC','ETH','SOL','AVAX','DOGE']
sample = {k: v for k, v in data.items() if k in sample_tickers}
print(f"Sample: {len(sample)} tickers")

lookbacks = [10, 20, 30, 50]
thresholds = [0.05, 0.08, 0.10, 0.15, 0.20]
alphas = [2.0, 2.5, 3.0, 3.5]
max_bars_list = [40, 60, 80, 120]

results = []

for L in lookbacks:
    for theta in thresholds:
        for alpha in alphas:
            for mb in max_bars_list:
                mod.MAX_BARS_HELD = mb
                all_r = []

                for ticker, df in sample.items():
                    if len(df) < max(L + 14 + 1, 201):
                        continue
                    close = df["close"]
                    mom = _compute_momentum(close, L)
                    atr = _compute_atr(df, 14)
                    sma200 = close.rolling(200, min_periods=50).mean()

                    n = len(df)
                    next_allowed = 0
                    for i in range(max(L + 14, 200), n - 1):
                        if i < next_allowed:
                            continue
                        mv = mom.iloc[i]
                        if np.isnan(mv) or np.isnan(atr.iloc[i]):
                            continue
                        sv = sma200.iloc[i]
                        if np.isnan(sv):
                            continue

                        # Trend filter: long above SMA200, short below
                        if mv > theta and close.iloc[i] > sv:
                            direction = "long"
                        elif mv < -theta and close.iloc[i] < sv:
                            direction = "short"
                        else:
                            continue

                        entry_price = close.iloc[i]
                        atr_val = atr.iloc[i]

                        if direction == "long":
                            initial_stop = entry_price - alpha * atr_val
                        else:
                            initial_stop = entry_price + alpha * atr_val

                        try:
                            exit_price, exit_reason, bars_held, final_stop = _simulate_trailing_exit(
                                df, i, direction, entry_price, initial_stop, atr
                            )
                        except:
                            continue

                        next_allowed = i + bars_held + 1

                        if direction == "long":
                            risk = entry_price - initial_stop
                            reward = exit_price - entry_price
                        else:
                            risk = initial_stop - entry_price
                            reward = entry_price - exit_price

                        if risk <= 0 or np.isnan(risk) or np.isnan(reward):
                            continue
                        all_r.append(reward / risk)

                if len(all_r) < 10:
                    continue

                avg_r = np.mean(all_r)
                win_rate = np.mean([r > 0 for r in all_r])
                years = 7.2
                sigs_per_year = len(all_r) / years * (529 / len(sample))

                results.append({
                    'L': L, 'theta': theta, 'alpha': alpha, 'max_bars': mb,
                    'n_signals': len(all_r),
                    'est_sig_per_year': sigs_per_year,
                    'avg_r': avg_r,
                    'win_rate': win_rate,
                })

results.sort(key=lambda x: x['avg_r'], reverse=True)

print(f"\n{'L':>4} {'theta':>6} {'alpha':>5} {'max_bars':>8} {'n_sig':>6} {'est_sig/yr':>10} {'avg_r':>7} {'win%':>6}")
print("-" * 65)
for r in results[:20]:
    print(f"{r['L']:>4} {r['theta']:>6.2f} {r['alpha']:>5.1f} {r['max_bars']:>8} {r['n_signals']:>6} {r['est_sig_per_year']:>10.0f} {r['avg_r']:>7.3f} {r['win_rate']:>6.1%}")

print(f"\nTotal combinations tested: {len(results)}")
if results:
    b = results[0]
    print(f"\nBest: L={b['L']}, theta={b['theta']}, alpha={b['alpha']}, max_bars={b['max_bars']}")
    print(f"  avg_r={b['avg_r']:.3f}, win_rate={b['win_rate']:.1%}")
