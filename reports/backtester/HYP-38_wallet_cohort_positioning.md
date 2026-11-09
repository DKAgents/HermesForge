# HYP-38 — Wallet-cohort positioning (on-chain Commitment of Traders) — first look

*Pre-registered 2026-11-09. PRELIMINARY run on the ~30-day free-key window:
this proves the LABELING MACHINERY end-to-end + a directional sniff. The real
90-day test runs once the Explorer tier is live. See HYP-38-wallet-cohort-positioning.md
for the frozen rubric.*

---

## 0. Two findings that reframe the directive (flagged before any code)

1. **HYP-29 is already assigned.** The directive labels wallet-cohort as "HYP-29",
   but `HYP-29` is already taken by *Funding carry: G3 fill-realism + capacity
   gate* (hypothesis file `HYP-29-funding-carry-g3-capacity.md`, backtest script,
   report, and a `trials.jsonl` entry under `hypothesis_id: "HYP-29"`). The
   `ingest_hl_fills.py` docstring and `US-07` report carry the same stale
   "wallet-cohort (HYP-29)" label. Following the established HYP-37 collision-chain
   convention, this hypothesis is pre-registered as the next free ID **HYP-38**.

2. **The window is ~30 days, not 14.** Live `tier_limits()` returns
   `history_days=30`, and the compact `hl.wallet_daily` table spans
   2026-10-10 → 2026-11-09 (31 days). The directive's "~14 days" note is stale.

---

## 1. Verdict (short)

**Machinery validated; signal not detected above MDE — as expected at this depth.**

Labeling works: 106,992 wallets are labelable; 2,212 skilled, 12,372 unskilled
(skew expected — losing flow is more common than consistently profitable flow).
The first-look gives **16 signal days (45 coin×day forward observations)**, which
is far too few to resolve the cohort signal: the M-5 MDE floor is
**IC = 0.4175** (and DSR-deflated Sharpe 1.64), so the observed point estimates —
follow-skilled IC −0.171, fade-unskilled IC −0.106, combined −0.010 — are all
**"not detected above MDE"**, i.e. indistinguishable from noise at this sample.
The combined signal is directionally positive (+303 bps over 45 obs at maker
cost) but this is a sniff, not evidence.

## 2. What was measured

- **Source**: `hl.wallet_daily` (Ironflow free key) for BTC-PERP / ETH-PERP /
  SOL-PERP, 2026-10-10 → 2026-11-09. 1,138,289 wallet-day rows pulled (day-granule
  keyset pagination, budget-paced), cached to
  `~/.hermes/market_data/hl_fills/wallet_daily_cache.parquet`.
- **Labels** (frozen rubric, ex-ante window 10-10..10-24): realized PnL > 0 AND
  win_rate >= 0.5 AND maker_ratio >= 0.5 → skilled; realized PnL < 0 AND
  win_rate < 0.5 AND maker_ratio < 0.5 → unskilled; min 10 fills / 3 active days /
  5 closing fills.  Holding period is **DATA-GATED** (not computable from
  wallet_daily; deferred to the 90-day raw-fills run) and does not enter the label.
- **Signal**: cohort net position = Σ `net_size_signed` over skilled vs unskilled
  wallets per coin/day (after 10-24). follow-skilled, fade-unskilled, combined.
- **Forward return**: next-day close→close from `bars_1d.db` (BTC/ETH/SOL).
- **Cost**: maker round-trip 3 bps per held day. No leverage. Live off.

## 3. First-look results (maker cost)

| signal | n obs (L/S) | IC (Pearson) | IC (Spearman) | mean sign-matched ret | net P&L | net P&L/obs |
|---|---|---|---|---|---|---|
| follow-skilled | 45 (23/22) | −0.079 | −0.171 | −19.7 bps | −1021.5 bps | −22.7 bps |
| fade-unskilled | 45 (21/24) | −0.104 | −0.106 | −19.5 bps | −1012.3 bps | −22.5 bps |
| combined | 45 (21/24) | +0.023 | −0.010 | +9.8 bps | +303.5 bps | +6.8 bps |

M-5 MDE at n=45, n_trials=170: **mde_ic (breadth 1) = 0.4175**, mde_sharpe_dsr =
1.6431. Every observed |IC| sits below 0.42 → all three are
"**not detected above MDE IC = 0.42**". Nothing here is "no edge" — it is "edge
smaller than this sample could resolve."

## 4. What the 90-day Explorer tier adds (exact sample-depth delta)

1. **3× forward sample** (~45 → ~135-180 coin×day obs), shrinking MDE IC from
   ~0.42 to ~0.20-0.24 by 1/√n — the region where a real cohort IC (if it exists
   at the typical 0.03-0.10 single-signal range) actually becomes resolvable.
2. **Holding-period feature** — the raw-fills 90-day window supplies per-wallet
   open→close timestamps, closing the DATA-GATED gap in the 5-dimension rubric.
3. **Label stability** — skill is re-measurable across multiple non-overlapping
   30-day subsamples (does the "skilled" cohort persist, or are they 30-day
   winners reverting?).
4. **Regime coverage** — funding-carry / unwind / liquidation-cycle regimes that
   a 30-day slice cannot span, plus multi-coin cross-sectional breadth.

## 5. Boundaries (stated plainly)

This run does NOT establish skill persistence or a stable cohort signal — 30 days
cannot. It proves the machinery (pull → label → cohort → forward-return → MDE →
ledger) works leak-free on real data and produces a defensible "not detected above
MDE 0.42" first look. Treat the combined +303 bps as a directional sniff only.

Artifacts: `scripts/research/hyp38_wallet_cohort.py`,
`trading/strategies/Hypotheses/HYP-38-wallet-cohort-positioning.md`, this report,
`reports/backtester/HYP-38_wallet_cohort_first_look.json`, trials ledger entry
HYP-38 (chain verified).