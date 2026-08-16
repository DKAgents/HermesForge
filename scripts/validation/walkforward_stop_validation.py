#!/usr/bin/env python3
"""
US-110: Walk-Forward Validation of US-109 Stop Optimization

CRITICAL: Tests whether the per-level-type stop caps (swing_high=0.6R, swing_low=0.7R)
are curve-fitted or genuinely improve OOS performance.

Methodology:
  1. Split 696-trade dataset by time into IS (first 60%) and OOS (last 40%)
  2. On IS only: find optimal stop distances per level type (grid search 0.1R-1.0R)
  3. Apply IS-optimal stops to OOS trades
  4. Compare OOS performance: optimized vs baseline (1.0R for all)
  5. Statistical significance test (bootstrap or t-test)

If OOS improvement is positive and statistically significant → stop optimization is real.
If OOS improvement is negative or not significant → it's curve-fitted, revert to 1.0R.
"""
import sys, os, json, time
sys.path.insert(0, '/root/HermesForge/scripts/data')
sys.path.insert(0, '/root/HermesForge/scripts/validation/scanners')

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

# ── Step 1: Re-run backtest with full MAE/MFE tracking ──
# (Same as stop_optimization_mae_mfe.py but we need the raw data with timestamps)

symbols = ['AAPL', 'NVDA', 'MSFT', 'SPY', 'AMZN', 'GOOGL', 'META', 'TSLA']
all_trades = []

print("=== US-110: Walk-Forward Validation ===\n")
print("Step 1: Building trade dataset with MAE/MFE...")

for sym in symbols:
    t0 = time.time()
    df = get_alpaca_bars(sym, '5m', 50000, start='2025-08-01T00:00:00Z', end='2026-08-15T23:00:00Z')
    if len(df) < 100:
        continue
    
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
            sp = sweep.stop_price  # ORIGINAL stop (1.0R baseline, no caps in detect_liquidity_sweeps)
            tp = sweep.target_price
            risk = ep - sp if d == 'bullish' else sp - ep
            
            # Walk forward with MAE/MFE tracking
            exit_type = 'time'
            xp = df['close'].iloc[min(ei + 15, len(df) - 1)]
            mae_price = 0.0
            mfe_price = 0.0
            
            for j in range(ei + 1, min(ei + 16, len(df))):
                b = df.iloc[j]
                if d == 'bullish':
                    mfe_price = max(mfe_price, b['high'] - ep)
                    mae_price = min(mae_price, b['low'] - ep)
                    if b['low'] <= sp:
                        exit_type, xp = 'stop', sp; break
                    if b['high'] >= tp:
                        exit_type, xp = 'target', tp; break
                else:
                    mfe_price = max(mfe_price, ep - b['low'])
                    mae_price = min(mae_price, ep - b['high'])
                    if b['high'] >= sp:
                        exit_type, xp = 'stop', sp; break
                    if b['low'] <= tp:
                        exit_type, xp = 'target', tp; break
            
            mae_r = mae_price / risk if risk > 0 else 0
            mfe_r = mfe_price / risk if risk > 0 else 0
            r = ((xp - ep) / risk if d == 'bullish' else (ep - xp) / risk) if risk > 0 else 0
            
            trades.append({
                'symbol': sym,
                'direction': d,
                'level_type': sweep.level_type,
                'entry_price': ep,
                'stop_price': sp,
                'target_price': tp,
                'risk': risk,
                'exit_type': exit_type,
                'exit_price': xp,
                'r_multiple': round(r, 3),
                'mae_r': round(mae_r, 3),
                'mfe_r': round(mfe_r, 3),
                'quality_score': sweep.quality_score,
                'timestamp': str(et),
                'date': et.strftime('%Y-%m-%d'),
                'epoch': et.timestamp(),
            })
            used_times.add(sweep.timestamp)
            break
    
    print(f"  {sym}: {len(trades)} trades in {time.time()-t0:.1f}s")
    all_trades.extend(trades)

dt = pd.DataFrame(all_trades)
total = len(dt)
print(f"\nTotal trades: {total}")

# ── Step 2: Split IS/OOS by time (60/40) ──
dt_sorted = dt.sort_values('epoch').reset_index(drop=True)
split_idx = int(len(dt_sorted) * 0.6)
is_data = dt_sorted.iloc[:split_idx].copy()
oos_data = dt_sorted.iloc[split_idx:].copy()

split_date = is_data['date'].iloc[-1]
print(f"\nStep 2: Time-based 60/40 split")
print(f"  IS (in-sample):  {len(is_data)} trades, up to {split_date}")
print(f"  OOS (out-of-sample): {len(oos_data)} trades, from {oos_data['date'].iloc[0]} onwards")

# ── Step 3: Optimize stops on IS only ──
print(f"\nStep 3: Optimizing stop distances on IS data only...")

def simulate_stops(trades_df, stop_caps):
    """Simulate trades with per-level-type stop caps.
    Returns list of R multiples.
    stop_caps: dict of level_type -> cap (fraction of 1.0R)
    """
    results = []
    for _, row in trades_df.iterrows():
        cap = stop_caps.get(row['level_type'], 1.0)
        # If MAE exceeds the capped stop, trade exits at -cap
        if row['mae_r'] <= -cap:
            results.append(-cap)
        else:
            # Trade follows original path
            results.append(row['r_multiple'])
    return results

def find_optimal_stops(trades_df, level_types=None):
    """Grid search optimal stop cap per level type."""
    if level_types is None:
        level_types = [lt for lt in trades_df['level_type'].unique() 
                       if len(trades_df[trades_df['level_type'] == lt]) >= 10]
    
    optimal = {}
    for lt in level_types:
        lt_data = trades_df[trades_df['level_type'] == lt]
        best_cap = 1.0
        best_exp = lt_data['r_multiple'].mean()
        
        for cap in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
            rs = simulate_stops(lt_data, {lt: cap})
            exp = np.mean(rs)
            if exp > best_exp:
                best_exp = exp
                best_cap = cap
        
        optimal[lt] = best_cap
    
    return optimal

# Find optimal stops on IS data
is_optimal = find_optimal_stops(is_data)
print(f"\n  IS-optimal stop caps:")
for lt, cap in sorted(is_optimal.items()):
    is_data_lt = is_data[is_data['level_type'] == lt]
    print(f"    {lt}: {cap:.1f}R (n={len(is_data_lt)}, IS exp={is_data_lt['r_multiple'].mean():.3f})")

# ── Step 4: Apply IS-optimal stops to OOS ──
print(f"\nStep 4: Testing IS-optimal stops on OOS data...")

# Baseline: all 1.0R (no caps)
oos_baseline_rs = [row['r_multiple'] for _, row in oos_data.iterrows()]
oos_baseline_exp = np.mean(oos_baseline_rs)
oos_baseline_wr = sum(1 for r in oos_baseline_rs if r > 0) / len(oos_baseline_rs) * 100

# Optimized: IS-optimal caps
oos_optimized_rs = simulate_stops(oos_data, is_optimal)
oos_optimized_exp = np.mean(oos_optimized_rs)
oos_optimized_wr = sum(1 for r in oos_optimized_rs if r > 0) / len(oos_optimized_rs) * 100

# Also test the US-109 caps (hardcoded from prior analysis)
us109_caps = {"swing_high": 0.6, "swing_low": 0.7}
oos_us109_rs = simulate_stops(oos_data, us109_caps)
oos_us109_exp = np.mean(oos_us109_rs)
oos_us109_wr = sum(1 for r in oos_us109_rs if r > 0) / len(oos_us109_rs) * 100

print(f"\n  {'Metric':<25} {'Baseline':>10} {'IS-opt':>10} {'US-109':>10}")
print(f"  {'Avg R':<25} {oos_baseline_exp:>10.3f} {oos_optimized_exp:>10.3f} {oos_us109_exp:>10.3f}")
print(f"  {'Win Rate':<25} {oos_baseline_wr:>10.1f}% {oos_optimized_wr:>10.1f}% {oos_us109_wr:>10.1f}%")
print(f"  {'Sum R':<25} {sum(oos_baseline_rs):>10.1f} {sum(oos_optimized_rs):>10.1f} {sum(oos_us109_rs):>10.1f}")

# ── Step 5: Statistical significance (bootstrap) ──
print(f"\nStep 5: Bootstrap significance test (1000 iterations)...")

def bootstrap_exp_delta(rs_baseline, rs_optimized, n_bootstrap=1000):
    """Bootstrap the difference in expectancy."""
    n = len(rs_baseline)
    deltas = []
    for _ in range(n_bootstrap):
        idx = np.random.choice(n, n, replace=True)
        base_sample = [rs_baseline[i] for i in idx]
        opt_sample = [rs_optimized[i] for i in idx]
        delta = np.mean(opt_sample) - np.mean(base_sample)
        deltas.append(delta)
    
    deltas = np.array(deltas)
    mean_delta = np.mean(deltas)
    ci_lower = np.percentile(deltas, 2.5)
    ci_upper = np.percentile(deltas, 97.5)
    p_value = np.mean(deltas <= 0)  # fraction of bootstrap samples where delta <= 0
    return mean_delta, ci_lower, ci_upper, p_value

# Test IS-optimal vs baseline on OOS
mean_delta, ci_lo, ci_hi, p_val = bootstrap_exp_delta(oos_baseline_rs, oos_optimized_rs)
print(f"\n  IS-optimal vs baseline (OOS):")
print(f"    Delta: {mean_delta:+.4f}R (95% CI: {ci_lo:+.4f} to {ci_hi:+.4f})")
print(f"    p-value: {p_val:.4f} ({'SIGNIFICANT' if p_val < 0.05 else 'NOT significant'})")

# Test US-109 caps vs baseline on OOS
mean_delta2, ci_lo2, ci_hi2, p_val2 = bootstrap_exp_delta(oos_baseline_rs, oos_us109_rs)
print(f"\n  US-109 caps vs baseline (OOS):")
print(f"    Delta: {mean_delta2:+.4f}R (95% CI: {ci_lo2:+.4f} to {ci_hi2:+.4f})")
print(f"    p-value: {p_val2:.4f} ({'SIGNIFICANT' if p_val2 < 0.05 else 'NOT significant'})")

# ── Step 6: Per-level-type OOS comparison ──
print(f"\nStep 6: Per-level-type OOS performance (IS-optimal vs baseline)")
print(f"  {'Level Type':<20} {'N':>4} {'Base_R':>8} {'Opt_R':>8} {'Delta':>8} {'Verdict'}")

for lt in sorted(oos_data['level_type'].unique()):
    lt_oos = oos_data[oos_data['level_type'] == lt]
    if len(lt_oos) < 5:
        continue
    
    base_rs = [row['r_multiple'] for _, row in lt_oos.iterrows()]
    cap = is_optimal.get(lt, 1.0)
    opt_rs = simulate_stops(lt_oos, {lt: cap})
    
    base_exp = np.mean(base_rs)
    opt_exp = np.mean(opt_rs)
    delta = opt_exp - base_exp
    
    verdict = "✅ KEEP" if delta > 0.02 else ("⚠️ MARGINAL" if abs(delta) <= 0.02 else "❌ REVERT")
    
    print(f"  {lt:<20} {len(lt_oos):>4} {base_exp:>+8.3f} {opt_exp:>+8.3f} {delta:>+8.3f}  {verdict}")

# ── Step 7: Final verdict ──
print(f"\n{'='*60}")
print(f"US-110: WALK-FORWARD VERDICT")
print(f"{'='*60}")

# Compare IS performance to OOS performance (overfit check)
is_base_exp = is_data['r_multiple'].mean()
is_opt_rs = simulate_stops(is_data, is_optimal)
is_opt_exp = np.mean(is_opt_rs)

print(f"\n  IS baseline exp:     {is_base_exp:+.4f}R")
print(f"  IS optimized exp:    {is_opt_exp:+.4f}R (improvement: {is_opt_exp - is_base_exp:+.4f}R)")
print(f"  OOS baseline exp:    {oos_baseline_exp:+.4f}R")
print(f"  OOS optimized exp:   {oos_optimized_exp:+.4f}R (improvement: {oos_optimized_exp - oos_baseline_exp:+.4f}R)")

is_improvement = is_opt_exp - is_base_exp
oos_improvement = oos_optimized_exp - oos_baseline_exp
overfit_ratio = is_improvement / oos_improvement if oos_improvement != 0 else float('inf')

print(f"\n  IS improvement:  {is_improvement:+.4f}R")
print(f"  OOS improvement: {oos_improvement:+.4f}R")
print(f"  Overfit ratio:   {overfit_ratio:.2f}x (1.0 = perfect, >2 = overfit)")

if oos_improvement > 0.05 and p_val < 0.05:
    print(f"\n  ✅ VERDICT: Stop optimization is VALID. OOS improvement is positive and significant.")
    print(f"     Recommended caps: {is_optimal}")
    print(f"     Deploy IS-optimal caps to production.")
elif oos_improvement > 0 and p_val < 0.10:
    print(f"\n  ⚠️ VERDICT: Stop optimization shows MARGINAL OOS improvement.")
    print(f"     Not statistically significant (p={p_val:.3f}). Use with caution.")
    print(f"     Recommended: keep US-109 caps but monitor live performance closely.")
else:
    print(f"\n  ❌ VERDICT: Stop optimization is CURVE-FIT. OOS improvement is not significant.")
    print(f"     Revert to 1.0R stops for all level types.")
    print(f"     The IS improvement ({is_improvement:+.4f}R) does not generalize to OOS.")

# Save results
results = {
    'total_trades': total,
    'split': {'is': len(is_data), 'oos': len(oos_data), 'split_date': split_date},
    'is_optimal_caps': is_optimal,
    'us109_caps': us109_caps,
    'is_baseline_exp': round(is_base_exp, 4),
    'is_optimized_exp': round(is_opt_exp, 4),
    'oos_baseline_exp': round(oos_baseline_exp, 4),
    'oos_optimized_exp': round(oos_optimized_exp, 4),
    'oos_us109_exp': round(oos_us109_exp, 4),
    'is_improvement': round(is_improvement, 4),
    'oos_improvement': round(oos_improvement, 4),
    'overfit_ratio': round(overfit_ratio, 2),
    'bootstrap_p_value': round(p_val, 4),
    'bootstrap_ci': [round(ci_lo, 4), round(ci_hi, 4)],
    'verdict': 'VALID' if oos_improvement > 0.05 and p_val < 0.05 else ('MARGINAL' if oos_improvement > 0 else 'CURVE_FIT'),
}

with open('/root/HermesForge/scripts/validation/results/US-110-walkforward-stop-opt.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nResults saved to scripts/validation/results/US-110-walkforward-stop-opt.json")
