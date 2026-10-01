#!/usr/bin/env python3
"""
Jev-powered decay check on all active paper trading strategies.
US-151 pattern: uses Jev classification instead of heuristic thresholds.
"""
import sys
import csv
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '/root/HermesForge/scripts/gauntlet')
from jev_client import JevClient
from jev_decay import check_decay, _compute_stats

REPO = Path('/root/HermesForge')
ACTIVE_DIR = REPO / 'trading' / 'strategies' / 'Active'
TRADES_CSV = REPO / 'scripts' / 'paper_trading' / 'trades.csv'
HYPOTHESES_DIR = REPO / 'trading' / 'strategies' / 'Hypotheses'


def extract_strategy_id(md_path):
    """Extract strategy_id from YAML frontmatter in a .md file."""
    with open(md_path) as f:
        lines = f.readlines()
    strategy_id_val = None
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('strategy_id:'):
            strategy_id_val = stripped.split('strategy_id:', 1)[1].strip()
        elif stripped.startswith('|strategy_id:'):
            strategy_id_val = stripped.split('|strategy_id:', 1)[1].strip()
        elif stripped.startswith('id:') and 'STR-' in stripped:
            if not strategy_id_val:
                val = stripped.split('id:', 1)[1].strip()
                if val.startswith('STR-'):
                    strategy_id_val = val
        if stripped == '---' and (len(lines) > 0 and lines[0].strip() == '---'):
            if lines.index(line) > 0:
                break
    return strategy_id_val


def main():
    # 1. Discover active strategies
    print("=" * 60)
    print("JEVPOWERED DECAY CHECK — ACTIVE PAPER TRADING STRATEGIES")
    print(f"Run: {datetime.now().isoformat()}")
    print("=" * 60)

    active_map = {}
    if ACTIVE_DIR.exists():
        for fname in sorted(ACTIVE_DIR.glob('*.md')):
            sid = extract_strategy_id(fname)
            if sid:
                active_map[sid] = fname
            else:
                print(f"  WARNING: No strategy_id in {fname.name}")

    # Also check hypotheses dir if no active found
    if not active_map and HYPOTHESES_DIR.exists():
        for fname in sorted(HYPOTHESES_DIR.glob('*.md')):
            sid = extract_strategy_id(fname)
            if sid:
                active_map[sid] = fname

    print(f"\nActive strategies found: {len(active_map)}")
    for sid, path in active_map.items():
        print(f"  {sid}  \u2190  {path.name}")

    if not active_map:
        print("\nNo active paper trading strategies found.")
        return 0

    # 2. Load trades from trades.csv
    print(f"\nLoading trades from trades.csv...")
    trades_by_sid = {}
    try:
        with open(TRADES_CSV, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sid = row.get('strategy_id', '')
                if sid not in active_map:
                    continue
                if row.get('status', '') != 'closed':
                    continue
                try:
                    r_mult = float(row.get('r_multiple', 0) or 0)
                except ValueError:
                    r_mult = 0.0
                trade = {
                    'r': r_mult,
                    'date': row.get('date', row.get('exit_date', '')),
                    'ticker': row.get('ticker', row.get('symbol', '')),
                    'direction': row.get('direction', 'long'),
                }
                trades_by_sid.setdefault(sid, []).append(trade)
    except FileNotFoundError:
        print(f"  WARNING: trades.csv not found")

    for sid in sorted(active_map.keys()):
        n = len(trades_by_sid.get(sid, []))
        print(f"  {sid}: {n} closed trades")

    # 3. Run Jev-powered decay check on each active strategy
    print("\n" + "=" * 60)
    print("JEV CLASSIFICATION RESULTS")
    print("=" * 60)

    jev = JevClient()
    results = []
    any_decayed = False

    for sid in sorted(active_map.keys()):
        trades = trades_by_sid.get(sid, [])
        stats = _compute_stats(trades)

        if stats['count'] == 0:
            print(f"\n  \u23ed  {sid} \u2014 No closed trades, skipping Jev")
            results.append({
                'strategy_id': sid,
                'file': active_map[sid].name,
                'trades_loaded': 0,
                'decay_probability': 0,
                'recommendation': 'no_data',
                'jev_engaged': False,
            })
            continue

        # Run Jev decay check
        print(f"\n  -> {sid} ({active_map[sid].name}) -- {stats['count']} trades", end='')
        sys.stdout.flush()

        try:
            result = check_decay(sid, recent_trades=trades, jev=jev)

            flag = '\U0001f534' if result.recommendation in ('demote', 'watch') else '\u2705'
            print(f"\n    {flag} Decay prob: {result.decay_probability:.0%}")
            print(f"       Recommendation: {result.recommendation}")
            print(f"       Confidence: {result.confidence:.0%}")

            if result.recommendation in ('demote', 'watch') or result.decay_probability > 0.5:
                any_decayed = True

            results.append({
                'strategy_id': sid,
                'file': active_map[sid].name,
                'trades_loaded': stats['count'],
                'decay_probability': result.decay_probability,
                'confidence': result.confidence,
                'recommendation': result.recommendation,
                'jev_error': result.jev_error,
                'stats': {
                    'avg_r': stats.get('avg_r', 0),
                    'win_rate': stats.get('win_rate', 0),
                    'profit_factor': stats.get('profit_factor', 0),
                    'current_losing_streak': stats.get('current_losing_streak', 0),
                    'max_losing_streak': stats.get('max_losing_streak', 0),
                },
                'jev_engaged': True,
            })
        except Exception as e:
            print(f"\n    \u274c Jev error: {e}")
            results.append({
                'strategy_id': sid,
                'file': active_map[sid].name,
                'trades_loaded': stats['count'],
                'decay_probability': 0,
                'recommendation': 'error',
                'jev_error': True,
                'stats': stats,
                'jev_engaged': False,
                'error': str(e),
            })

    # 4. Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    if not any_decayed:
        print("\n  \u2705 ALL ACTIVE STRATEGIES HEALTHY \u2014 No intervention needed.")
    else:
        flagged = [r for r in results if r.get('recommendation') in ('demote', 'watch') or r.get('decay_probability', 0) > 0.5]
        print(f"\n  \U0001f534 {len(flagged)} strategy(ies) need attention:")
        for r in flagged:
            print(f"\n     {r['strategy_id']} ({r['file']})")
            print(f"        Decay probability: {r.get('decay_probability', 0)*100:.0f}%")
            print(f"        Recommendation: {r.get('recommendation', 'n/a')}")
            print(f"        Trades: {r.get('trades_loaded', 0)}")
            stats = r.get('stats', {})
            print(f"        Avg R: {stats.get('avg_r', 'n/a')} | Win rate: {stats.get('win_rate', 'n/a')} | PF: {stats.get('profit_factor', 'n/a')}")

    print(f"\nTimestamp: {datetime.now().isoformat()}")

    # Final JSON for downstream
    final = {
        'any_decayed': any_decayed,
        'n_active': len(active_map),
        'results': results,
        'timestamp': datetime.now().isoformat(),
    }
    print("\n--- JSON ---")
    print(json.dumps(final, indent=2, default=str))

    return 1 if any_decayed else 0


if __name__ == '__main__':
    sys.exit(main())