#!/usr/bin/env python3
"""STR-Q Deep Backtest with Alpaca 1-year 5m data."""
import sys, os, time
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
    print(f"  {len(df)} bars, scanning...", flush=True)
    
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
            exit_type = 'time'
            xp = df['close'].iloc[min(ei + 15, len(df) - 1)]
            
            for j in range(ei + 1, min(ei + 16, len(df))):
                b = df.iloc[j]
                if d == 'bullish':
                    if b['low'] <= sp:
                        exit_type, xp = 'stop', sp; break
                    if b['high'] >= tp:
                        exit_type, xp = 'target', tp; break
                else:
                    if b['high'] >= sp:
                        exit_type, xp = 'stop', sp; break
                    if b['low'] <= tp:
                        exit_type, xp = 'target', tp; break
            
            risk = ep - sp if d == 'bullish' else sp - ep
            r = ((xp - ep) / risk if d == 'bullish' else (ep - xp) / risk) if risk > 0 else 0
            
            trades.append({
                'symbol': sym, 'direction': d, 'level_type': sweep.level_type,
                'entry_price': round(ep, 2), 'stop_price': round(sp, 2),
                'target_price': round(tp, 2), 'exit_type': exit_type,
                'exit_price': round(xp, 2), 'r_multiple': round(r, 3),
                'quality_score': sweep.quality_score, 'date': str(et),
            })
            used_times.add(sweep.timestamp)
            break
    
    print(f"  {len(trades)} trades in {time.time()-t0:.1f}s")
    all_trades.extend(trades)

print(f"\n{'='*60}")
print(f"STR-Q Deep Backtest (1 year, 5m, Alpaca IEX)")
print(f"{'='*60}")
print(f"Total trades: {len(all_trades)}")

if all_trades:
    dt = pd.DataFrame(all_trades)
    wr = (dt['r_multiple'] > 0).mean() * 100
    avg_r = dt['r_multiple'].mean()
    sum_r = dt['r_multiple'].sum()
    pos = dt[dt['r_multiple'] > 0]['r_multiple'].sum()
    neg = abs(dt[dt['r_multiple'] < 0]['r_multiple'].sum())
    pf = pos / neg if neg > 0 else float('inf')
    
    print(f"Win rate: {wr:.1f}%")
    print(f"Average R: {avg_r:.3f}")
    print(f"Sum R: {sum_r:.1f}")
    print(f"Profit factor: {pf:.2f}")
    print(f"Max win: {dt['r_multiple'].max():.3f}R")
    print(f"Max loss: {dt['r_multiple'].min():.3f}R")
    
    print(f"\nBy direction:")
    for d in ['bullish', 'bearish']:
        s = dt[dt['direction'] == d]
        if len(s) > 0:
            print(f"  {d}: {len(s)} trades, WR={((s['r_multiple']>0).mean()*100):.1f}%, avg R={s['r_multiple'].mean():.3f}")
    
    print(f"\nBy level type:")
    for lt in dt['level_type'].unique():
        s = dt[dt['level_type'] == lt]
        if len(s) >= 5:
            print(f"  {lt}: {len(s)} trades, WR={((s['r_multiple']>0).mean()*100):.1f}%, avg R={s['r_multiple'].mean():.3f}")
    
    print(f"\nBy exit type:")
    for et in ['target', 'stop', 'time']:
        s = dt[dt['exit_type'] == et]
        if len(s) > 0:
            print(f"  {et}: {len(s)} trades, avg R={s['r_multiple'].mean():.3f}")
    
    print(f"\nBy quality score:")
    for lo, hi in [(40,50),(50,60),(60,70),(70,80),(80,100)]:
        s = dt[(dt['quality_score']>=lo)&(dt['quality_score']<hi)]
        if len(s) >= 5:
            print(f"  {lo}-{hi}: {len(s)} trades, WR={((s['r_multiple']>0).mean()*100):.1f}%, avg R={s['r_multiple'].mean():.3f}")
    
    # By month
    dt['month'] = pd.to_datetime(dt['date']).dt.to_period('M')
    print(f"\nBy month:")
    for m in sorted(dt['month'].unique()):
        s = dt[dt['month'] == m]
        print(f"  {m}: {len(s)} trades, WR={((s['r_multiple']>0).mean()*100):.1f}%, avg R={s['r_multiple'].mean():.3f}")
    
    dt.to_csv('/root/HermesForge/scripts/validation/results/STR-Q-stocks-deep-phase1a.csv', index=False)
    print(f"\nResults saved.")
