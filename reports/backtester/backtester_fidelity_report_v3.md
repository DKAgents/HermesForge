# Backtester Fidelity Report v3 — Full Bar-Level Hostile-Fill Re-Simulation (US-168, FINAL)

Author: backtester (HermesForge)
Date: 2026-11-01
Interpreter: `/usr/bin/python3` (system Python 3.12 — pandas 2.1.4, numpy 1.26.4, pyarrow 25.0.1)
Window: `entry_date >= 2026-09-14` (through 2026-10-30, last bar 2026-11-01 00:10 UTC)
Fills: pessimistic / realistic (hostile model v1 — `hostile_fills_strq.py`).

Scope: read-only on all repo data. No code modified, no post/cron/.env touched.
The three tracker JSONL files (`hostile_fill_report*.jsonl`) were backed up to
`/root/.hermes/cache/scratch/us168_backup/` first and verified byte-identical after the
run (md5 unchanged). `trades.csv` and `trade_journal.jsonl` mtimes unchanged.

---

## 0. What was actually run (real code, real bars — not mocked)

The production hostile-fill entry/exit functions were imported and executed directly
against real OHLCV bars:

  check_entry_hostile / check_exit_hostile  (hostile_fills_strq.py)   — STR-Q, 5m
  check_entry_hostile / check_exit_hostile  (hostile_fills.py)         — swing strategies, daily
  _compute_r / _paper_r / _reconcile_signal_dedup / DEGENERATE_RISK_FLOOR  (pnl_accounting.py)
  fee_source.get_taker_bps / get_round_trip_bps  (dynamic venue fee, US-165)

Fill rules applied exactly as the current code specifies:
  STR-Q entry lag  = signal bar + 1 + CONFIRMATION_BARS(=2)  →  3-bar lag.
  Entry           = fill at triggering bar OPEN + taker fee (pessimistic, worse than a true limit).
  Stop exit       = worst print of the crossing bar (low for long, high for short) + taker fee.
  Target exit     = limit — requires trade-THROUGH; touches only never fill.
  Time stop       = 15 bars (STR-Q) at worst print + fee.
  Dynamic fee     = crypto taker 4.5 bps/side (Hyperliquid base tier), stock 1.0 bps/side.

---

## 1. Bar source — determination and feasibility (the key constraint)

| asset  | live path (intraday_provider)         | full 46-day backfill?                          |
|--------|---------------------------------------|------------------------------------------------|
| crypto | Hyperliquid `candleSnapshot` (5m)     | **NO** — returns only ~5,000 trailing 5m bars ≈ 17 days (10-14 → 11-01). `endTime` in the past returns `[]`. |
| stock  | Alpaca IEX `/v2/stocks/bars` (5m)     | **YES** — paginated via `next_page_token`, full window (09-14 → 10-30). |
| crypto (cross-venue proxy) | OKX `history-candles` (5m) | **YES** — full window, 14,100 bars/ticker, all 32 crypto tickers listed. |

Hyperliquid's public candle endpoint cannot backfill a 46-day window. The repo's live bar
source (`get_intraday_candles(..., lookback_bars=1000)`) could never see more than the
trailing ~3.5 days in any case. A genuinely full-window crypto re-simulation therefore
requires a historical provider. OKX is reachable, lists every crypto ticker in the window
(including Hyperliquid-native HYPE/FARTCOIN/PUMP/XPL/TRUMP/ENA/ONDO), and supports full
history — so it was used as the crypto bar source, then **cross-validated** against the
same-venue Hyperliquid slice (below).

---

## 2. Cross-venue validation (OKX used only after this passed)

On the 477 crypto trades whose signal bar falls in the Hyperliquid-retained window
(entry >= 10-14), the re-simulation was run on BOTH sets of bars:

  overlap trades:            477
  both-scored subtrades:     408
  per-trade R correlation:   r = 0.789  (OKX vs Hyperliquid)
  outcome-class agreement:   467 / 477  = 97.9%
  net R on the same 477:     Hyperliquid -672.54 R (408 scored)  ≈  OKX -708.70 R (417 scored)

The two venues agree within ~5% in aggregate and 97.9% on per-trade outcome class. OKX is
a valid proxy for the same-venue Hyperliquid price action on this universe, so it was
applied to the full window.

---

## 3. Authoritative per-strategy table (net R after costs, bar level, full window)

Trade count = deduped, non-quarantined. Win rate = wins / scored. scored = closed under
hostile rules AND non-degenerate (setup risk >= 0.10%). net R = Σ hostile R (entry+exit
taker fees + worst-print stops + 3-bar lag all inside).

| Strategy       | Trades (dedup, non-quar) | Scored | Net R after costs | Win rate | Avg R/trade |
|----------------|--------------------------|--------|-------------------|----------|-------------|
| STR-Q          | 5,897                    | 5,309  | **-8,447.07**     | 24.7%    | **-1.591**  |
|   — crypto     | 5,630                    | 5,136  | -8,217.41         | 24.5%    | -1.600      |
|   — stock      |   267                    |   173  |   -229.66         | 31.2%    | -1.327      |
| STR-A          | 3                        | 3      | -4.011            |  0.0%    | -1.337      |
| STR-B          | 16                       | 16     | +1.381            | 62.5%    | +0.086      |
| STR-D          | 1                        | 1      | +0.704            | 100%     | +0.704      |
| STR-DEBASEMENT | 0                        | 0      |   0.000           | n/a      | n/a         |
| STR-VIXC       | 3                        | 3      | +1.401            | 100%     | +0.467      |

STR-Q crypto exit-reason mix (scored, full window): stop 3,419 (66.6%), target 998
(19.4%), time 719 (14.0%); skip 158. Median bars held = 3 (15 minutes).

STR-Q crypto mean R = -1.600, sd = 2.782, n = 5,136 → **t-stat = -41.2**. This is not a
vanishing edge; it is a strongly *negative* expectancy.

The swing strategies (STR-A/B/D/DEBASEMENT/VIXC) carry 3 / 16 / 1 / 0 / 3 trades — far
below any sample that could support an edge claim. STR-B (+1.381 over 16) and STR-VIXC
(+1.401 over 3) are noise, not signal.

---

## 4. Did the bar-level sim change the paper-layer number? Yes — and violently.

  Paper layer (STR-Q, post US-165 dynamic fee):   **+1,568.30 R**, win 47.0%, avg +0.287 R
  Bar level  (STR-Q, full window hostile fills):  **-8,447.07 R**, win 24.7%, avg -1.591 R

Direction: positive → decisively negative. Magnitude: a ~-10,015 R swing (sign flip and
~5.4× the paper magnitude). Why the paper +1,568 R was an artifact:

  1. Paper fills at the sweep reversal close (effectively "buy the exact bottom"); the
     hostile model only fills when price TRADES BACK THROUGH the entry level, which for a
     tight-stop sweep (stop 0.1–0.3% away) is nearly always already on the way to the stop.
  2. 3-bar confirmation lag lets the favorable reversal slip before a fill is even possible.
  3. Worst-print stops and both-side taker fees turn the (tight) risk into a large per-trade
     cost: median stop-out is ~-1.7 R, and the entry is filled at the bar OPEN (above the
     paper entry for longs), adding entry slippage on top.
  4. Target trade-through requirement means targets that merely touch never fill — winners
     fall through the time stop instead of realizing.

Note the paper layer itself moved since v2 (+634.668 → +1,568.30 R) only because US-165's
dynamic fee (12 bps crypto round trip) replaced the prior 20 bps adversarial placeholder;
that change flatters the paper bound further, which makes the bar-level collapse even more
striking, not less.

---

## 5. Verdict (blunt)

**No.** No strategy shows a genuine, statistically-meaningful positive net-R-after-costs edge.

  STR-Q is the only strategy with a meaningful sample, and at bar level its full-window
  outcome is **-8,447 R after costs** (t = -41.2, win 24.7%, avg -1.59 R/trade). The prior
  paper-layer "+1,568 R" (and the earlier "+634 R") was a fill-pricing artifact that does not
  survive realistic fills + the dynamic fee. The three swing strategies that look positive on
  paper (STR-B +1.38, STR-D +0.70, STR-VIXC +1.40) rest on 16 / 1 / 3 trades respectively —
  no power, no claim.

  STR-Q's bar-level edge is not "Flat" and not "weakly negative — it is strongly and
  statistically significant NEGATIVE. Whatever informational edge the sweep detector has is
  smaller than the transaction cost of actually trading it.

---

## 6. Coverage statement (explicit)

  crypto: full window (09-14 → 10-30) covered via OKX (cross-venue, validated on a 477-trade
          Hyperliquid overlap, r=0.789 / 97.9% agreement). 5,630 of 5,630 deduped crypto trades
          had a matched signal bar (0 no-signal, 0 no-bars).
  stock:  full window covered via Alpaca. 267 of 267 deduped stock trades matched a signal bar.
  Overall: 100% of the deduped, non-quarantined STR-Q window (5,897 trades) re-simulated on
  real bars. No extrapolation required — the full window was driven.

  Caveat: crypto bars are OKX rather than the same-venue Hyperliquid feed (which only retains
  ~17 days). The cross-validation in §2 bounds this at ~5% aggregate R error and 2.1% outcome
  disagreement on the overlap — far too small to move the verdict. If same-venue Hyperliquid
  full-history data becomes available, this should be re-run to confirm the exact -8,447 R
  figure, but the sign and the ~-1.6 R/trade magnitude are not in question.