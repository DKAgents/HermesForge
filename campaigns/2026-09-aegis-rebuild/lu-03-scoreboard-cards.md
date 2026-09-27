# LU-03: Scoreboard Cards — Paper PnL vs Hostile Reality

**Status**: note-only (no code edits)
**Date**: 2026-09-25
**Campaign**: 2026-09-aegis-rebuild

---

## Which Files Build Which Cards

**Paper-trading scoreboard** → channel `<#1537225420120793088>`

- `scripts/paper_trading/performance_report.py` — reads `trades.csv`, computes
  PnL from the `r_multiple` / `gauntlet_r` column, builds sections for open
  positions, recently closed, 7-day/30-day PnL trend, and running totals by
  strategy and asset class. Posts via `--post 1537225420120793088`.

**Auto-kill card** (divergence alert) → same channel

- `scripts/paper_trading/live_performance_tracker.py` — reads `trades.csv`,
  computes per-strategy live stats (win rate, avg R, stop rate) and compares
  them against `BACKTEST_EXPECTATIONS` (hardcoded dict of backtest results
  for each strategy). Flags divergence at 1.5σ and posts a red 🚨 embed if
  any HIGH-severity divergence is found.

---

## The Bug

### Paper Card: +1857R with no hostile reference

`performance_report.py` computes PnL exclusively from the `r_multiple` (or
`gauntlet_r`) column of `trades.csv`. These values are the **paper fill**
outcomes — the simulator's idealized exit at stop/target levels without
accounting for whether the market actually traded through those levels at
the right time. A 30-day report can show `+1857R` because STR-Q produces
many trades and the paper simulator credits full R-multiples on hit stops
and targets.

None of the PnL sections (`Last 7 days`, `Last 30 days`, `Running Totals`)
reference the hostile fill data in `hostile_fill_report_strq.jsonl`. The
report conveys paper reality as if it were tradable reality.

### Auto-Kill Card: flags STR-Q against backtests, not hostile data

`live_performance_tracker.py` compares live stats against
`BACKTEST_EXPECTATIONS["STR-Q-liquidity-sweep"]`, which was derived from
a 696-trade deep backtest on 1yr Alpaca 5m data (`expected_avg_r = 0.597`,
`expected_win_rate = 46.2`). When live paper results diverge from these
backtest expectations at ≥1.5σ, it generates a HIGH or MEDIUM severity flag.
If STR-Q paper results happen to align with backtest expectations, the
auto-kill card shows ✅ — **even though the hostile fill model says the
actual tradable PnL is -104R**.

The auto-kill card is structured as a divergence detector between **paper
fills** and **backtest expectations**. It is not a tradability test. It has
no awareness of `hostile_fill_report_strq.jsonl`.

### The Gap

Neither card cites the hostile R from `hostile_fill_report_strq.jsonl`. The
paper card can show `+1857R` for STR-Q over 30 days while the hostile
baseline is `-104R`. The two numbers exist in separate universes:

- `trades.csv` → `r_multiple` → paper PnL (used by both cards)
- `hostile_fill_report_strq.jsonl` → `hostile_entry_price` / `hostile_r` →
  realistic PnL (used by nothing in the reporting pipeline)

---

## Required End State (do not implement)

1. **Paper card** (`performance_report.py`): when displaying STR-Q PnL, the
   card MUST cite both paper R (from `trades.csv`) and hostile R (from
   `hostile_fill_report_strq.jsonl`). The hostile R must appear
   **alongside** the paper R — not hidden in a footnote, not in a separate
   channel. The reader must see both numbers on the same card.

2. **Auto-kill card** (`live_performance_tracker.py`): the divergence check
   for STR-Q MUST include a hostile-R threshold. If the hostile cumulative R
   is below a survivability floor (e.g., ≤ 0 after 100+ trades), the card
   MUST cite the hostile R explicitly, regardless of how well paper stats
   align with backtest expectations.

Until both cards cite the hostile fill data, the paper card is **wrong** by
omission — it presents an untradable number as if it were actionable.

---

## Frozen Scoreboard (inviolable)

The authoritative STR-Q comparison, run once against the full trade ledger,
remains:

- **Paper**: +1305R (from `trades.csv` `r_multiple`)
- **Hostile**: -104R (from `hostile_fill_report_strq.jsonl`)
- **Delta**: 1409R — hostile fills erase the entire paper edge and then some

This is the go/no-go reference. Do not un-kill STR-Q. The hostile engine
continues to run daily at 22:00 UTC, appending to
`hostile_fill_report_strq.jsonl` (12,674 records as of Sep 26). The
cumulative hostile R drifts but remains the continuous reference.

---

## Invariants

- **Do NOT edit** `scripts/discord/` or publisher files.
- **Do NOT change** STR-Q status.
- **Do NOT post. Do NOT trade.**
- The paper card and auto-kill card are live as-is. The bug is documented
  but not fixed.

---

## Verified

```bash
$ grep -l -E 'paper-trading|auto-kill|hostile' \
    scripts/discord/* scripts/paper_trading/*.py 2>/dev/null
scripts/discord/crosspost_webhook_all.sh
scripts/discord/portfolio_publish.py
scripts/discord/post_heatmaps.py
scripts/discord/validate_crosspost.py
scripts/paper_trading/extract_lessons.py
scripts/paper_trading/fetch_crypto_data.py
scripts/paper_trading/hostile_fills.py
scripts/paper_trading/hostile_fills_strq.py
scripts/paper_trading/hostile_fills_strq_v2.py
scripts/paper_trading/live_performance_tracker.py
```

---

## Key Takeaway

`performance_report.py` runs the paper scoreboard. `live_performance_tracker.py`
runs the auto-kill card. Neither reads `hostile_fill_report_strq.jsonl`. The
paper card can show `+1857R` for a strategy whose hostile baseline is `-104R`.
The required end state is both cards citing both numbers, or the paper card
is wrong.