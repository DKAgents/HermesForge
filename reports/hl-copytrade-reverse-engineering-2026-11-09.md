# HL Top-Trader Reverse-Engineering Report

Date: 2026-11-09
Scope: read-only reconstruction of the mechanical signatures of "genuine" top traders
(after gain-harvester screening) from stored fills + clearinghouse state.
Data: ~/.hermes/market_data/hl_copytrade/{screener,fills,clearinghouse}

## TL;DR (honest headline)

After reconstructing the mechanical signature of every genuine (non-harvester) trader in
the ranked list, the top of the Hyperliquid leaderboard is **not** a catalogue of
copy-tradable edges. It decomposes into five archetypes, and only **one** trader shows a
clean, mechanical, rule-like signature worth a gauntlet backtest on its own merits; a
second is mechanical but is funding-carry, and the rest are either directional
thesis-holders (whose "edge" is being short crypto during a downtrend / long ETH during a
bull — i.e. beta + timing, not a rule) or market makers whose edge is infrastructure
(spread + rebates) that a discretionary retail account cannot replicate.

I will not force a rule onto a trader who made money discretionarily. Most of them did.

## Data caveats (important for interpreting everything below)

1. **Fill truncation.** The pipeline captured at most 10,000 fills per address
   (`checkpoint.json` shows almost every address at exactly 10000). The earliest fills are
   therefore *closes* of pre-existing positions whose *opens* are not in the dataset.
   Consequence: my FIFO round-trip reconstruction under-attributes PnL (the orphaned
   closes' `closedPnl` is dropped). I therefore use the screener's `net_pnl` (already the
   clean sum of `closedPnl`) for absolute PnL, and my reconstruction only for *relative*
   structure: hold time, win-rate shape, direction, sizing, time-of-day.
2. **Fees vs funding.** `fee` is the taker/maker fee on each fill. Funding is *not* in the
   fills — it lives in `clearinghouse/*.json` `cumFunding`. For short thesis-holders this
   is decisive (see 0x218a65 below): headline "realized PnL" ignores a massive funding
   bleed.
3. **`crossed` = taker.** `crossed:true` is an aggressive/taker fill; `crossed:false` is a
   resting maker fill. Maker-heavy + sub-hour holds = market-making inventory, not
   directional intent.
4. **`xyz:*` coins** (e.g. `xyz:SKHX`, `xyz:BRENTOIL`, `xyz:NVDA`, `xyz:GOOGL`) are
   Hyperliquid's *index/marketcap perpetuals* (equity / commodity / pre-launch names), not
   spot or standard crypto perps. Several top traders trade *nothing* but these.

## Archetypes found

| # | Archetype | Count in ranked list | Replicable? |
|---|---|---|---|
| 1 | Directional thesis-holder (short majors) | ~8 | No — discretionary/beta |
| 2 | Market maker / liquidity provider | ~6 | No — infra edge |
| 3 | Time-scheduled bot (DCA / carry) | 2 | Yes mechanically, but beta or funding-only |
| 4 | Buy-and-hold liquidation | 2 | No — pure beta |
| 5 | Zero-hold 100%-win arb/MEV/wash | ~4 | No — not tradable |

---

## Per-trader characterization (genuine traders, ranked list order)

### 0xb695651daa... (rank 0, #1 by true_performance) — MARKET MAKER, short inventory
- net $336.9k realized + $11.1M unrealized; acct $33.7M; ~2.9x gross leverage; 9 coins.
- Universe: LIT (4876 fills), BTC (2095), HYPE (1039), XMR, NEAR, ETH, ZEC, xyz:NBIS, xyz:SNDK.
- Direction: 95.6% short notional. Sizing: persistent ~-782 BTC inventory.
- Execution: **99.5% maker** (taker 0.5%), median hold ~2.9h.
- Verdict: liquidity provider running inventory across a few names; edge is spread/rebate.
  **NOT replicable** for a directional account.

### 0xca4903c207... (rank 1) — SHORT ETH/XRP/SOL thesis-holder
- net realized only $85.7k; true_perf $9.97M is **~$9.9M unrealized** (still-open short).
- 100% win on close legs (ETH 754 legs / 14.2d hold; XRP 125; SOL 91), but per-leg wins
  are tiny. 3.2x leverage, acct $17.2M.
- Verdict: one directional short thesis that happens to be in profit. The "100% win rate"
  is an artifact of never being stopped on a winning trend, not a repeatable rule.
  **DISCRETIONARY — not reverse-engineerable.**

### 0x218a65e21e... (rank 2) — SHORT BTC/ETH whale (the key cautionary case)
- net realized $4.84M (3rd-highest realized); acct $11.5M; 6.1x leverage; BTC + ETH only.
- Direction: **100% short** (no longs at all). Entries between BTC 63.5k–85k, ETH 1981–2957.
- BTC side: 96.2% win rate, median hold **3.8 days**, avg win +$646 vs avg loss -$591,
  R median +3.0% / p90 +7.5%.
- ETH side (same trader): **0.3% win rate**, median hold **223 days**, avg loss -$443,
  R median -5.9% — they got buried shorting ETH and are still bleeding it.
- **Funding: `cumFunding` = -$1.45M (BTC) + -$1.50M (ETH) ≈ -$3M paid** to hold these shorts.
  Clearinghouse: BTC short -841.9 @ 78859 (8x isolated), ETH short -3465 @ 2208 (10x cross).
- Verdict: this is a *directional short-the-majors thesis*, not a mechanical system. The
  96% BTC win rate is the market (BTC down) rewarding the thesis; the ETH leg proves the
  trader is not selectively timing — they short both, and one won while the other lost
  $1.2M + 7 months of funding. Headline PnL flatters them because funding isn't in it.
  **DISCRETIONARY — not reverse-engineerable.**

### 0x024294c53a... (rank 44) — SHORT xyz index perps, 13–15 UTC window  ← GAUNTLET #1
- net $1.05M realized (now flat, acct $45M); 37 coins, **all `xyz:` index perps**
  (SKHX, BRENTOIL, CL, NVDA, SKHY, NATGAS, AMD, META, GOOGL, TSLA…). 100% taker.
- Direction: 79% short. Sizing: many small legs on a very large account.
- **Horizon: median hold 2.6h.** Win rate 75.6%; avg win +$57 vs avg loss -$11 (5.2:1);
  R median +0.9% / p90 +4.5%.
- **Entry pattern: opens cluster overwhelmingly at 13:00–15:00 UTC**
  (1074 + 1488 + 1454 opens vs a near-empty rest of day). This is a *time-window*
  trigger, not a price trigger.
- Verdict: the cleanest mechanical signature in the dataset — short a basket of xyz index
  perps in a fixed afternoon window, cover ~2.6h later. **Rule-like and REPLICABLE
  candidate**, *provided* the xyz-index funding/oracle/settlement mechanics are understood
  and verified before backtesting (see shortlist).

### 0xda3768e929... (rank 6) — SHORT xyz index-perp basket swing
- net $980k realized; acct $20.6M; 38 coins, again almost all `xyz:` (GOOGL, SOXL, INTC,
  MU, DRAM, NVDA, PURRDAT…); 93% short; median hold ~24h; 54% win (PF ~2.06).
- Verdict: a slower, wider-basket version of the 13–15 UTC strategy, but no clean time
  trigger (opens spread across the day) and only 54% win. Likely the same *family* of
  xyz-index-arb but executed more loosely. **Borderline — not clean enough to call
  mechanical; flag for further study of the xyz mechanism, not a standalone gauntlet.**

### 0x2ea18c23f7... (rank 27) — ETH time-scheduled accumulator bot
- net $6.2M realized (highest realized); acct **now ~$2** (everything withdrawn).
- ETH only, 4465 legs, 100% win, median hold ~50 days.
- **Entry pattern: every one of 6912 opens at 15:00 UTC.** A literal scheduled bot.
- Verdict: mechanically perfect, but the "strategy" is *buy ETH at 15:00 UTC and hold*.
  That is dollar-cost-average beta, not alpha. **Mechanically replicable, but there is no
  edge to test** — exclude from gauntlet (or run only as a benchmark baseline).

### 0x35d1151ef1... (rank 53) — short-funding / meme carry bot  ← GAUNTLET #2
- net $167k; acct ~$1 now (withdrew); 4 coins (FARTCOIN 7756 fills, BTC, PUMP, ETH).
- 100% short; opens perfectly uniform across all 24 hours (24/7 bot).
- **Horizon: median hold 17.1 days with an unusually tight band (15.8–18.5 d)** — a
  fixed rotation schedule, not discretionary timing. Win 44.6%, avg win +$4.4 vs -$1.8
  (2.4:1), PF ~12.25, tiny R (median -0.2%).
- Verdict: a systematic short on high-funding names (FARTCOIN/memes) harvested on a fixed
  ~17-day cycle. The pattern (short the highest-funding meme perp, rotate) is mechanical
  and *plausibly* a funding-carry edge — but we do not currently store funding history, so
  the carry hypothesis is unverified. **REPLICABLE candidate, gated on funding data.**

### 0x5d2f4460ac... (rank 28) — short-BTC trend/momentum
- net $5.35M realized (2nd-highest); acct $3.1M; BTC (5849 legs) + xyz:XYZ100 + ETH + HYPE.
- 27.5% win rate, avg win +$2380 vs avg loss -$618 (3.85:1), median hold ~27 days.
  BTC entries clustered 108k–119.5k (shorted the highs), plus a 100%-win xyz:XYZ100 sleeve.
- Verdict: genuine positive expectancy from a trend-short (small frequent losers, big
  winners), but the *trigger* is "I think BTC has topped" — discretionary, no clean entry
  rule in the fills. **DISCRETIONARY (trend thesis), not cleanly replicable as a rule.**

### 0xbde2ddc49a... (rank 35) — buy-and-hold liquidation
- net $1.73M; acct ~$1 now; 14 coins long, 100% win, median hold ~60 days.
- Verdict: classic buy-and-hold during a bull; edge is beta. **Not a tradable rule.**

### 0x484bc16082... (rank 7), 0x936cf4fb95... (rank 45), 0xfc667adba8... (rank 46) — market makers
- Accts $42.4M / $26.2M / $79.7M; realized $624k / $540k / $336k.
- Universes: alt-perps (MON/ZRO/PENDLE/FET/ONDO/PUMP) and 32–55 coins; 97–98% short;
  maker-heavy; median holds ~30 min to ~11h; win-rate shape shows consistent small
  spread-capture losses/ticks with occasional larger wins — the MM fingerprint.
- Verdict: **NOT replicable** — infra edge (spread + rebate), not a directional signal.

### Zero-hold 100%-win accounts (not flagged GH, but still not tradable)
- 0x5b5d51203a (net $1.77M, 0s hold, 100% win), 0x20c2d95a3d (1 coin, 15s hold, 100% win,
  $10.9M, 89% taker), 0x77375a8c9d (0s hold, 100% win). These are arb/MEV/wash patterns,
  not directional strategies — **exclude** (and note the screener's gain-harvester filter
  does *not* catch pure zero-hold arb; the `freak_day` / ROI gates are not aimed at it).

### Honesty check: many "genuine" ranked traders are net losers
The below are *not* gain-harvesters yet finished deeply negative — a reminder that the
post-screen "genuine" set still contains a long left tail, and the positive tail is
dominated by beta and infra, not portable rules:
0x99967871e6 -$2.09M, 0xa312114b57 -$2.55M, 0x656c8da58d -$1.06M, 0x45d26f2819 -$1.01M,
0x88560b7202 -$410k, 0x51156f7002 -$581k, 0x4e14fc11f5 -$668k, 0x0a776abbaa -$102k (realized; large unrealized drag).

---

## Ranking by (replicability × true edge)

| Rank | Trader | Replicability | True edge | Gauntlet? |
|---|---|---|---|---|
| 1 | 0x024294c53a (short xyz index perps, 13–15 UTC, 2.6h hold, 75.6% win) | High (time+universe rule) | Real & realized ($1.05M) | **YES — candidate #1** |
| 2 | 0x35d1151ef1 (short high-funding memes, 17-day rotation, bot) | High (schedule rule) | Plausible funding-carry, unverified | **YES — candidate #2 (needs funding data)** |
| 3 | 0x2ea18c23f7 (15:00 UTC ETH DCA) | High (mechanical) | ~zero (pure beta) | No — baseline only |
| 4 | 0x5d2f4460ac (short-BTC trend) | Low (discretionary trigger) | Positive (3.85:1) | No without a concrete entry rule |
| 5-6 | 0x218a65e21e, 0xca4903c207 (short majors thesis) | None (thesis) | Beta + timing, funding-negative | No |
| rest | market makers, buy-and-hold, arb/MEV | None/low | infra/beta | No |

## Gauntlet shortlist (what is actually worth backtesting)

1. **0x024294c53a — "short the xyz index-perp basket in the 13–15 UTC window."**
   - Concrete rule *as observed*: at ~13:00 UTC, open a short basket of xyz index perps
     (the ones this trader repeatedly shorts: equity index names, oil/CL/BRENTOIL,
     natgas, marketcap indices); cover ~2.6h later. 75.6% win, 5.2:1, median R +0.9%.
   - **Gate before backtesting (mandatory):** explain *why* this window works. The xyz
     perps have index/oracle/funding mechanics that may re-price at a fixed UTC time. A
     gauntlet must pre-register the mechanism hypothesis (e.g. "index marks re-rate at
     session X, creating a systematic reversion to short into"). Without the mechanism the
     backtest is curve-fitting to an address's habits.

2. **0x35d1151ef1 — "short the highest-funding meme perp on a ~17-day rotation."**
   - Concrete rule *as observed*: hold a short in FARTCOIN-class high-funding names, in
     24/7-bot fashion, flat-entry on a fixed ~17-day cycle; 44.6% win, 2.4:1, PF ~12.25.
   - **Gate:** funding-rate history for these coins is *not in the stored data*. The
     carry hypothesis must be validated against actual funding before this is gauntlet-worthy.

3. **0x2ea18c23f7 — "15:00 UTC ETH DCA"** — recommend *not* testing as a strategy; at most
   include as the beta benchmark against which #1/#2 must show excess return.

## Bottom line

Reverse-engineering the leaderboard top is, for the most part, a negative result that is
worth stating plainly: the genuine top traders are overwhelmingly **(a)** directional
thesis-holders whose PnL is beta and timing (short crypto in a downtrend, long ETH in a
bull — and for the big short, heavily funding-negative), or **(b)** market makers whose
edge is maker rebates and spread, not a signal a retail account can copy. Exactly **one**
trader (0x024294c53a) shows a genuinely mechanical, time-windowed, rule-like signature on
a specific instrument class, and a second (0x35d1151ef1) shows a mechanical schedule
consistent with funding-carry. Both are worth a gauntlet run, but each requires a
mechanism/data dependency to be satisfied first — otherwise we would be regression-testing
what is, in fact, just two more forms of beta.

I did not fabricate a rule for any trader; where the money was made discretionarily, that
is labelled DISCRETIONARY and excluded from the shortlist.
