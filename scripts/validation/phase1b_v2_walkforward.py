#!/usr/bin/env python3
"""Phase 1B v2 deep walk-forward validation for STR-Q backtest."""
import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path
import json

CSV = "/root/HermesForge/scripts/validation/results/STR-Q-stocks-deep-phase1a.csv"
OUT = "/root/HermesForge/06-Strategies/Backtests/STR-Q-phase1b-v2.md"

df = pd.read_csv(CSV)
print(f"Total trades: {len(df)}")
print(f"Columns: {list(df.columns)}")

# Parse date and sort chronologically
df['date'] = pd.to_datetime(df['date'], utc=True)
df = df.sort_values('date').reset_index(drop=True)

# Chronological split: IS first 60%, OOS last 40%
split_idx = int(len(df) * 0.60)
is_df = df.iloc[:split_idx].copy()
oos_df = df.iloc[split_idx:].copy()

print(f"\nIS: {len(is_df)} trades  ({is_df['date'].min()} -> {is_df['date'].max()})")
print(f"OOS: {len(oos_df)} trades ({oos_df['date'].min()} -> {oos_df['date'].max()})")

def metrics(d):
    n = len(d)
    wins = d[d['r_multiple'] > 0]
    losses = d[d['r_multiple'] < 0]
    win_rate = len(wins) / n if n else 0
    avg_r = d['r_multiple'].mean()
    gross_profit = wins['r_multiple'].sum() if len(wins) else 0
    gross_loss = abs(losses['r_multiple'].sum()) if len(losses) else 0
    pf = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    expectancy = avg_r
    median_r = d['r_multiple'].median()
    std_r = d['r_multiple'].std()
    max_r = d['r_multiple'].max()
    min_r = d['r_multiple'].min()
    return {
        'n': n,
        'wins': len(wins),
        'losses': len(losses),
        'win_rate': win_rate,
        'avg_r': avg_r,
        'median_r': median_r,
        'std_r': std_r,
        'profit_factor': pf,
        'gross_profit_r': gross_profit,
        'gross_loss_r': gross_loss,
        'expectancy_r': expectancy,
        'max_r': max_r,
        'min_r': min_r,
    }

is_m = metrics(is_df)
oos_m = metrics(oos_df)
full_m = metrics(df)

print("\n=== IS (In-Sample, first 60%) ===")
for k, v in is_m.items():
    print(f"  {k}: {v}")
print("\n=== OOS (Out-of-Sample, last 40%) ===")
for k, v in oos_m.items():
    print(f"  {k}: {v}")

# T-test: OOS R-multiples vs 0 (one-sample t-test)
t_stat, p_val = stats.ttest_1samp(oos_df['r_multiple'], 0.0)
print(f"\nT-test (OOS R vs 0): t={t_stat:.4f}, p={p_val:.6f}")

# Also: two-sample t-test IS vs OOS
t_stat_2, p_val_2 = stats.ttest_ind(is_df['r_multiple'], oos_df['r_multiple'], equal_var=False)
print(f"T-test (IS vs OOS Welch): t={t_stat_2:.4f}, p={p_val_2:.6f}")

# Confidence interval on OOS mean R
n_oos = len(oos_df)
mean_oos = oos_df['r_multiple'].mean()
se_oos = oos_df['r_multiple'].std(ddof=1) / np.sqrt(n_oos)
ci95 = stats.t.interval(0.95, df=n_oos-1, loc=mean_oos, scale=se_oos)
print(f"OOS mean R 95% CI: [{ci95[0]:.4f}, {ci95[1]:.4f}]")

# Degradation analysis
def pct(new, base):
    if base == 0:
        return float('inf')
    return (new - base) / base * 100

deg_win = pct(oos_m['win_rate'], is_m['win_rate'])
deg_avg = pct(oos_m['avg_r'], is_m['avg_r']) if is_m['avg_r'] != 0 else float('inf')
deg_pf = pct(oos_m['profit_factor'], is_m['profit_factor']) if is_m['profit_factor'] != 0 else float('inf')

print(f"\nDegradation (OOS vs IS):")
print(f"  Win rate: {deg_win:+.1f}%")
print(f"  Avg R:    {deg_avg:+.1f}%")
print(f"  PF:       {deg_pf:+.1f}%")

# Monthly breakdown
df['month'] = df['date'].dt.to_period('M').astype(str)
monthly = df.groupby('month').agg(
    trades=('r_multiple', 'count'),
    win_rate=('r_multiple', lambda x: (x > 0).mean()),
    avg_r=('r_multiple', 'mean'),
    total_r=('r_multiple', 'sum'),
).reset_index()
print("\n=== Monthly ===")
print(monthly.to_string(index=False))

# Per-symbol OOS breakdown
oos_sym = oos_df.groupby('symbol').agg(
    trades=('r_multiple', 'count'),
    win_rate=('r_multiple', lambda x: (x > 0).mean()),
    avg_r=('r_multiple', 'mean'),
    total_r=('r_multiple', 'sum'),
).reset_index().sort_values('total_r', ascending=False)
print("\n=== OOS per symbol ===")
print(oos_sym.to_string(index=False))

# Exit type breakdown OOS
oos_exit = oos_df.groupby('exit_type').agg(
    trades=('r_multiple', 'count'),
    avg_r=('r_multiple', 'mean'),
    total_r=('r_multiple', 'sum'),
).reset_index()
print("\n=== OOS exit types ===")
print(oos_exit.to_string(index=False))

# Build markdown report
def fmt(x, d=2):
    if isinstance(x, float) and (abs(x) > 1e6 or (abs(x) < 1e-4 and x != 0)):
        return f"{x:.2e}"
    if isinstance(x, float):
        return f"{x:.{d}f}"
    return str(x)

monthly_md = monthly.to_markdown(index=False, floatfmt=".3f")
oos_sym_md = oos_sym.to_markdown(index=False, floatfmt=".3f")
oos_exit_md = oos_exit.to_markdown(index=False, floatfmt=".3f")

tip_block = ""
if p_val < 0.05 and p_val_2 >= 0.05:
    tip_block = (":::tip PASS\n"
                 "The OOS segment retains a statistically significant positive edge (p < 0.05),\n"
                 "and IS vs OOS means are not significantly different — no evidence of overfitting.\n:::")
if p_val >= 0.05:
    tip_block += (":::warning\n"
                  "The OOS edge is NOT statistically significant at α=0.05. Treat results with caution.\n:::")
if p_val_2 < 0.05:
    tip_block += (":::warning\n"
                  "IS and OOS means differ significantly (p < 0.05) — possible overfitting or regime change.\n:::")

verdict_pass = (oos_m['avg_r'] > 0 and oos_m['profit_factor'] > 1.0
                and p_val < 0.05 and p_val_2 >= 0.05
                and abs(deg_win) < 10 and abs(deg_avg) < 25)
verdict_cond = (oos_m['avg_r'] > 0 and oos_m['profit_factor'] > 1.0)
overall = "PASS" if verdict_pass else ("CONDITIONAL" if verdict_cond else "FAIL")

report = f"""---
title: "STR-Q Phase 1B v2 — Deep Walk-Forward Validation"
strategy: STR-Q
phase: "1B v2"
data_source: "STR-Q-stocks-deep-phase1a.csv"
total_trades: {full_m['n']}
date_range: "{df['date'].min().date()} to {df['date'].max().date()}"
split_method: "chronological 60/40 (IS/OOS)"
validation_date: "{pd.Timestamp.now(tz='UTC').strftime('%Y-%m-%d')}"
status: complete
---

# STR-Q Phase 1B v2 — Deep Walk-Forward Validation

## Overview

Deep walk-forward validation of the STR-Q strategy across **{full_m['n']} trades** spanning
**{df['date'].min().date()}** to **{df['date'].max().date()}** (1 full year of 5-minute bars).

The trade ledger was sorted chronologically by entry date and split into:

| Segment | Trades | Date Range | Share |
|---------|--------|------------|-------|
| IS (In-Sample) | {is_m['n']} | {is_df['date'].min().date()} → {is_df['date'].max().date()} | 60% |
| OOS (Out-of-Sample) | {oos_m['n']} | {oos_df['date'].min().date()} → {oos_df['date'].max().date()} | 40% |

This is a true walk-forward split — no re-optimization is performed on the OOS segment.

## Headline Metrics

| Metric | IS (60%) | OOS (40%) | Full | Degradation (OOS vs IS) |
|--------|----------|-----------|------|-------------------------|
| Trades | {is_m['n']} | {oos_m['n']} | {full_m['n']} | — |
| Win Rate | {is_m['win_rate']:.1%} | {oos_m['win_rate']:.1%} | {full_m['win_rate']:.1%} | {deg_win:+.1f}% |
| Avg R | {is_m['avg_r']:.4f} | {oos_m['avg_r']:.4f} | {full_m['avg_r']:.4f} | {deg_avg:+.1f}% |
| Median R | {is_m['median_r']:.4f} | {oos_m['median_r']:.4f} | {full_m['median_r']:.4f} | — |
| Std R | {is_m['std_r']:.4f} | {oos_m['std_r']:.4f} | {full_m['std_r']:.4f} | — |
| Profit Factor | {is_m['profit_factor']:.4f} | {oos_m['profit_factor']:.4f} | {full_m['profit_factor']:.4f} | {deg_pf:+.1f}% |
| Gross Profit (R) | {is_m['gross_profit_r']:.2f} | {oos_m['gross_profit_r']:.2f} | {full_m['gross_profit_r']:.2f} | — |
| Gross Loss (R) | {is_m['gross_loss_r']:.2f} | {oos_m['gross_loss_r']:.2f} | {full_m['gross_loss_r']:.2f} | — |
| Expectancy (R/trade) | {is_m['expectancy_r']:.4f} | {oos_m['expectancy_r']:.4f} | {full_m['expectancy_r']:.4f} | — |
| Max R | {is_m['max_r']:.2f} | {oos_m['max_r']:.2f} | {full_m['max_r']:.2f} | — |
| Min R | {is_m['min_r']:.2f} | {oos_m['min_r']:.2f} | {full_m['min_r']:.2f} | — |

## Statistical Significance

### One-sample t-test (OOS R-multiples vs 0)

Tests whether the OOS sample mean R-multiple is statistically distinguishable from zero
(i.e., whether the strategy has a real edge on unseen data).

| Statistic | Value |
|-----------|-------|
| Sample size (n) | {n_oos} |
| Mean R | {mean_oos:.4f} |
| Std R | {oos_df['r_multiple'].std(ddof=1):.4f} |
| Std Error | {se_oos:.4f} |
| t-statistic | {t_stat:.4f} |
| p-value (two-tailed) | {p_val:.6f} |
| 95% CI for mean R | [{ci95[0]:.4f}, {ci95[1]:.4f}] |
| Significant at α=0.05? | {'**YES**' if p_val < 0.05 else 'NO'} |
| Significant at α=0.01? | {'**YES**' if p_val < 0.01 else 'NO'} |

### Two-sample Welch's t-test (IS vs OOS)

Tests whether the IS and OOS segments have statistically different mean R-multiples
(a regime-change / overfitting indicator).

| Statistic | Value |
|-----------|-------|
| t-statistic | {t_stat_2:.4f} |
| p-value (two-tailed) | {p_val_2:.6f} |
| Significant difference? | {'**YES**' if p_val_2 < 0.05 else 'NO'} |

{tip_block}

## Monthly Breakdown

{monthly_md}

## OOS Per-Symbol Breakdown

{oos_sym_md}

## OOS Exit-Type Breakdown

{oos_exit_md}

## Interpretation

- **Edge persistence:** The OOS avg R of {oos_m['avg_r']:.4f} vs IS avg R of {is_m['avg_r']:.4f}
  represents a {deg_avg:+.1f}% shift. {'Reasonable stability.' if abs(deg_avg) < 25 else 'Material degradation — investigate.'}
- **Win-rate stability:** {deg_win:+.1f}% shift IS→OOS.
- **Profit factor:** OOS PF {oos_m['profit_factor']:.2f} vs IS PF {is_m['profit_factor']:.2f}.
- **Statistical verdict:** OOS mean R is {'statistically significant' if p_val < 0.05 else 'NOT statistically significant'}
  at α=0.05 (p={p_val:.4f}). IS/OOS {'do not differ significantly' if p_val_2 >= 0.05 else 'differ significantly'}
  (p={p_val_2:.4f}).

## Verdict

| Check | Result |
|-------|--------|
| OOS positive expectancy | {'PASS' if oos_m['avg_r'] > 0 else 'FAIL'} |
| OOS profit factor > 1.0 | {'PASS' if oos_m['profit_factor'] > 1.0 else 'FAIL'} |
| OOS edge statistically significant (p<0.05) | {'PASS' if p_val < 0.05 else 'FAIL'} |
| IS/OOS mean R not significantly different | {'PASS' if p_val_2 >= 0.05 else 'FAIL'} |
| Win-rate degradation < 10pp | {'PASS' if abs(deg_win) < 10 else 'FAIL'} |
| Avg R degradation < 25% | {'PASS' if abs(deg_avg) < 25 else 'FAIL'} |

**Overall: {overall}**

---

*Generated by `phase1b_v2_walkforward.py`. Do not edit by hand.*
"""

Path(OUT).parent.mkdir(parents=True, exist_ok=True)
Path(OUT).write_text(report)
print(f"\nReport written to {OUT}")
print(f"Report size: {len(report)} bytes")
