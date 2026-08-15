#!/usr/bin/env python3
"""
US-109: STR-Q Stop Optimization via MAE/MFE Analysis

Re-runs the deep backtest but records the actual Maximum Adverse Excursion (MAE)
and Maximum Favorable Excursion (MFE) for each trade by walking the 5m bars
during the holding period.

This allows us to answer:
  - "How far does price go against us before hitting target?"
  - "Could we tighten the stop and still capture the winners?"
  - "What is the optimal stop distance per level type?"

Output: CSV + markdown report with stop optimization recommendations.
"""
import sys, os, time, json
sys.path.insert(0, '/root/HermesForge/scripts/data')
sys.path.insert(0, '/root/HermesForge/scripts/validation/scanners')

# Load env
with open('/root/.hermes/.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, _, val = line.partition('=')
            os.environ[key.strip()] = val.strip()

import pandas as pd
import numpy as np
from collections import defaultdict
from alpaca_connector import get_alpaca_bars
from detect_liquidity_sweeps import (
    _compute_atr, identify_liquidity_levels, detect_sweep_at_level,
)

symbols = ['AAPL', 'NVDA', 'MSFT', 'SPY', 'AMZN', 'GOOGL', 'META', 'TSLA']
all_trades = []

for sym in symbols:
    t0 = time.time()
    print(f"Fetching {sym}...", flush=True)
    df = get_alpaca_bars(sym, '5m', 50000, start='2025-08-01T00:00:00Z', end='2026-08-15T23:00:00Z')
    if len(df) < 100:
        print(f"  Skipping: only {len(df)} bars")
        continue
    print(f"  {len(df)} bars, scanning with MAE/MFE tracking...", flush=True)
    
    atr = _compute_atr(df)
    df['date'] = df['timestamp'].dt.date
    daily = df.groupby('date').agg({'open':'first','high':'max','low':'min','close':'last'}).reset_index()
    
    trades = []
    used_times = set()
    
    for ws in range(100, len(df) - 200, 50):
        we = min(ws + 500, len(df))
        window = df.iloc[ws:we].reset_index(drop=True)
        wa = atr.iloc[ws:we].reset_index(drop=True)
        if len(window) < 50:
            continue
        
        cd = window['timestamp'].iloc[-1].date()
        pd_rows = daily[daily['date'] < cd].tail(2)
        dl = {}
        if len(pd_rows) >= 1:
            p = pd_rows.iloc[-1]
            dl = {'prior_high': float(p['high']), 'prior_low': float(p['low']),
                  'prior_close': float(p['close']), 'prior_date': str(p['date'])}
        
        cp = window['close'].iloc[-1]
        levels = identify_liquidity_levels(window, dl, {}, cp)
        if not levels:
            continue
        
        for level in levels[:3]:
            sweep = detect_sweep_at_level(window, level, wa, sym, '5m', 'stock', lookback=15)
            if sweep is None or sweep.quality_score < 40 or sweep.confirmation != 'confirmed':
                continue
            if sweep.timestamp in used_times:
                continue
            
            et = pd.Timestamp(sweep.timestamp)
            mask = df['timestamp'] == et
            if not mask.any():
                continue
            ei = df.index[mask][0]
            if ei + 15 >= len(df):
                continue
            
            d = sweep.direction
            ep = sweep.entry_price
            sp = sweep.stop_price
            tp = sweep.target_price
            risk = ep - sp if d == 'bullish' else sp - ep
            
            # Walk forward and track MAE/MFE
            exit_type = 'time'
            xp = df['close'].iloc[min(ei + 15, len(df) - 1)]
            mae_price = 0.0  # worst adverse price
            mfe_price = 0.0  # best favorable price
            
            for j in range(ei + 1, min(ei + 16, len(df))):
                b = df.iloc[j]
                
                # Track MFE (best favorable excursion)
                if d == 'bullish':
                    mfe_price = max(mfe_price, b['high'] - ep)
                    mae_price = min(mae_price, b['low'] - ep) if mae_price != 0 else b['low'] - ep
                    mae_price = min(mae_price, b['low'] - ep)
                    
                    if b['low'] <= sp:
                        exit_type, xp = 'stop', sp; break
                    if b['high'] >= tp:
                        exit_type, xp = 'target', tp; break
                else:
                    mfe_price = max(mfe_price, ep - b['low'])
                    mae_price = min(mae_price, ep - b['high']) if mae_price != 0 else ep - b['high']
                    mae_price = min(mae_price, ep - b['high'])
                    
                    if b['high'] >= sp:
                        exit_type, xp = 'stop', sp; break
                    if b['low'] <= tp:
                        exit_type, xp = 'target', tp; break
            
            # Convert MAE/MFE to R multiples
            mae_r = mae_price / risk if risk > 0 else 0  # negative = adverse
            mfe_r = mfe_price / risk if risk > 0 else 0   # positive = favorable
            
            # Also compute MAE/MFE in ATR terms
            current_atr = float(atr.iloc[ei]) if ei < len(atr) else 0
            mae_atr = mae_price / current_atr if current_atr > 0 else 0
            mfe_atr = mfe_price / current_atr if current_atr > 0 else 0
            stop_dist_atr = abs(ep - sp) / current_atr if current_atr > 0 else 0
            
            r = ((xp - ep) / risk if d == 'bullish' else (ep - xp) / risk) if risk > 0 else 0
            
            trades.append({
                'symbol': sym,
                'direction': d,
                'level_type': sweep.level_type,
                'entry_price': round(ep, 2),
                'stop_price': round(sp, 2),
                'target_price': round(tp, 2),
                'stop_distance_atr': round(stop_dist_atr, 3),
                'exit_type': exit_type,
                'exit_price': round(xp, 2),
                'r_multiple': round(r, 3),
                'mae_r': round(mae_r, 3),        # negative = how far against us
                'mfe_r': round(mfe_r, 3),         # positive = how far in our favor
                'mae_atr': round(mae_atr, 3),
                'mfe_atr': round(mfe_atr, 3),
                'current_atr': round(current_atr, 2),
                'quality_score': sweep.quality_score,
                'date': str(et),
            })
            used_times.add(sweep.timestamp)
            break
    
    print(f"  {len(trades)} trades in {time.time()-t0:.1f}s")
    all_trades.extend(trades)

print(f"\n{'='*60}")
print(f"STR-Q MAE/MFE Analysis (1 year, 5m, Alpaca IEX)")
print(f"{'='*60}")
print(f"Total trades: {len(all_trades)}")

if not all_trades:
    print("No trades found!")
    sys.exit(1)

dt = pd.DataFrame(all_trades)

# Save raw data
out_csv = '/root/HermesForge/scripts/validation/results/STR-Q-mae-mfe-deep.csv'
dt.to_csv(out_csv, index=False)
print(f"Raw data saved to {out_csv}")

# ── Analysis ──

# 1. Overall MAE/MFE stats
print(f"\n── Overall MAE/MFE ──")
print(f"  Avg MAE: {dt['mae_r'].mean():.3f}R (min: {dt['mae_r'].min():.3f}R)")
print(f"  Avg MFE: {dt['mfe_r'].mean():.3f}R (max: {dt['mfe_r'].max():.3f}R)")
print(f"  Avg stop distance: {dt['stop_distance_atr'].mean():.3f} ATR")
print(f"  Median MAE: {dt['mae_r'].median():.3f}R")
print(f"  Median MFE: {dt['mfe_r'].median():.3f}R")

# 2. MAE by exit type
print(f"\n── MAE/MFE by Exit Type ──")
for et in ['target', 'stop', 'time']:
    s = dt[dt['exit_type'] == et]
    if len(s) > 0:
        print(f"  {et}: n={len(s)}, avg MAE={s['mae_r'].mean():.3f}R, avg MFE={s['mfe_r'].mean():.3f}R, "
              f"avg R={s['r_multiple'].mean():.3f}")

# 3. MAE/MFE by level type
print(f"\n── MAE/MFE by Level Type ──")
print(f"  {'Level Type':<20} {'N':>4} {'MAE_avg':>8} {'MAE_med':>8} {'MFE_avg':>8} {'MFE_med':>8} "
      f"{'Stop%':>6} {'Tgt%':>6} {'AvgR':>7} {'StopDist':>9}")
for lt in sorted(dt['level_type'].unique()):
    s = dt[dt['level_type'] == lt]
    if len(s) < 5:
        continue
    stop_pct = (s['exit_type'] == 'stop').mean() * 100
    tgt_pct = (s['exit_type'] == 'target').mean() * 100
    print(f"  {lt:<20} {len(s):>4} {s['mae_r'].mean():>8.3f} {s['mae_r'].median():>8.3f} "
          f"{s['mfe_r'].mean():>8.3f} {s['mfe_r'].median():>8.3f} "
          f"{stop_pct:>6.1f} {tgt_pct:>6.1f} {s['r_multiple'].mean():>7.3f} "
          f"{s['stop_distance_atr'].mean():>9.3f}")

# 4. MAE distribution for WINNERS (trades that hit target)
print(f"\n── MAE Distribution for Winners (target exits) ──")
winners = dt[dt['exit_type'] == 'target']
if len(winners) > 0:
    mae_vals = winners['mae_r'].values
    percentiles = [10, 25, 50, 75, 90]
    print(f"  n={len(winners)}")
    for p in percentiles:
        val = np.percentile(mae_vals, p)
        print(f"  {p}th percentile MAE: {val:.3f}R")
    print(f"  Max MAE for winners: {mae_vals.max():.3f}R")
    print(f"  → If we tightened stop to {np.percentile(mae_vals, 90):.3f}R, "
          f"we'd capture {len(winners[winners['mae_r'] >= np.percentile(mae_vals, 90)])} "
          f"out of {len(winners)} winners (90th percentile)")

# 5. For each candidate stop distance, compute new expectancy
print(f"\n── Stop Optimization Simulation ──")
print(f"  Testing tighter stops to see if expectancy improves...")
print(f"  {'Stop_dist':>10} {'Would_stop':>10} {'Saved_wins':>10} {'Lost_wins':>10} "
      f"{'New_exp':>8} {'Old_exp':>8} {'Delta':>8}")

original_exp = dt['r_multiple'].mean()
original_wr = (dt['r_multiple'] > 0).mean() * 100

# Test stop distances from 0.1R to 1.0R
for stop_r in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
    new_rs = []
    would_stop = 0
    saved_wins = 0
    lost_wins = 0
    
    for _, row in dt.iterrows():
        # If original exit was target (winner), check if tighter stop would have triggered
        if row['exit_type'] == 'target':
            if row['mae_r'] <= -stop_r:
                # Tighter stop would have triggered — this winner becomes a loser at -stop_r
                new_rs.append(-stop_r)
                lost_wins += 1
            else:
                # Winner still wins
                new_rs.append(row['r_multiple'])
        elif row['exit_type'] == 'stop':
            # Original stop at -1R, tighter stop at -stop_r would trigger earlier
            # But if MAE is worse than -stop_r, the tighter stop triggers
            if row['mae_r'] <= -stop_r:
                new_rs.append(-stop_r)
                would_stop += 1
            else:
                # MAE wasn't as bad as -stop_r, so the tighter stop wouldn't trigger
                # The trade continues to its original outcome
                new_rs.append(row['r_multiple'])
                if row['r_multiple'] > 0:
                    saved_wins += 1
        else:  # time exit
            if row['mae_r'] <= -stop_r:
                new_rs.append(-stop_r)
                would_stop += 1
            else:
                new_rs.append(row['r_multiple'])
    
    new_exp = np.mean(new_rs)
    delta = new_exp - original_exp
    print(f"  {stop_r:>10.1f}R {would_stop:>10} {saved_wins:>10} {lost_wins:>10} "
          f"{new_exp:>8.3f} {original_exp:>8.3f} {delta:>+8.3f}")

# 6. Per-level-type optimal stop
print(f"\n── Per-Level-Type Optimal Stop ──")
print(f"  {'Level Type':<20} {'N':>4} {'Best_stop':>10} {'Best_exp':>10} {'Orig_exp':>10} {'Delta':>8}")
for lt in sorted(dt['level_type'].unique()):
    s = dt[dt['level_type'] == lt]
    if len(s) < 10:
        continue
    
    orig_exp = s['r_multiple'].mean()
    best_stop = 1.0
    best_exp = orig_exp
    
    for stop_r in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
        new_rs = []
        for _, row in s.iterrows():
            if row['mae_r'] <= -stop_r:
                new_rs.append(-stop_r)
            else:
                new_rs.append(row['r_multiple'])
        new_exp = np.mean(new_rs)
        if new_exp > best_exp:
            best_exp = new_exp
            best_stop = stop_r
    
    delta = best_exp - orig_exp
    print(f"  {lt:<20} {len(s):>4} {best_stop:>10.1f}R {best_exp:>10.3f} {orig_exp:>10.3f} {delta:>+8.3f}")

# 7. Stop distance in ATR per level type
print(f"\n── Stop Distance in ATR by Level Type ──")
print(f"  {'Level Type':<20} {'N':>4} {'Avg_dist':>10} {'Med_dist':>10} {'Min':>8} {'Max':>8}")
for lt in sorted(dt['level_type'].unique()):
    s = dt[dt['level_type'] == lt]
    if len(s) < 5:
        continue
    print(f"  {lt:<20} {len(s):>4} {s['stop_distance_atr'].mean():>10.3f} "
          f"{s['stop_distance_atr'].median():>10.3f} "
          f"{s['stop_distance_atr'].min():>8.3f} {s['stop_distance_atr'].max():>8.3f}")

# Save analysis results for report
results = {
    'total_trades': len(dt),
    'original_avg_r': round(original_exp, 4),
    'original_win_rate': round(original_wr, 1),
    'avg_mae_r': round(dt['mae_r'].mean(), 4),
    'avg_mfe_r': round(dt['mfe_r'].mean(), 4),
    'avg_stop_distance_atr': round(dt['stop_distance_atr'].mean(), 4),
    'by_level_type': {},
    'by_exit_type': {},
}
for lt in sorted(dt['level_type'].unique()):
    s = dt[dt['level_type'] == lt]
    if len(s) < 5:
        continue
    
    # Find optimal stop
    orig = s['r_multiple'].mean()
    best_stop, best_exp = 1.0, orig
    for stop_r in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
        new_rs = []
        for _, row in s.iterrows():
            if row['mae_r'] <= -stop_r:
                new_rs.append(-stop_r)
            else:
                new_rs.append(row['r_multiple'])
        new_exp = np.mean(new_rs)
        if new_exp > best_exp:
            best_exp = new_exp
            best_stop = stop_r
    
    results['by_level_type'][lt] = {
        'n': len(s),
        'avg_r': round(orig, 4),
        'avg_mae_r': round(s['mae_r'].mean(), 4),
        'avg_mfe_r': round(s['mfe_r'].mean(), 4),
        'avg_stop_dist_atr': round(s['stop_distance_atr'].mean(), 4),
        'stop_pct': round((s['exit_type'] == 'stop').mean() * 100, 1),
        'target_pct': round((s['exit_type'] == 'target').mean() * 100, 1),
        'optimal_stop_r': best_stop,
        'optimal_exp': round(best_exp, 4),
        'exp_delta': round(best_exp - orig, 4),
    }

for et in ['target', 'stop', 'time']:
    s = dt[dt['exit_type'] == et]
    if len(s) > 0:
        results['by_exit_type'][et] = {
            'n': len(s),
            'avg_mae_r': round(s['mae_r'].mean(), 4),
            'avg_mfe_r': round(s['mfe_r'].mean(), 4),
            'avg_r': round(s['r_multiple'].mean(), 4),
        }

with open('/root/HermesForge/scripts/validation/results/STR-Q-mae-mfe-summary.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n✅ Analysis complete. Summary saved to results/STR-Q-mae-mfe-summary.json")
