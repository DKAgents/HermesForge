# Conditional-edge grid — xsmom + OI-level (HYP-21 C-positioning)

Date: 2026-11-07 (UTC)
Owner: backtester (HermesForge)
Module: scripts/gauntlet/conditional_grid.py (reusable)
Driver: scripts/gauntlet/run_conditional_grid.py
Trials: XSMOM-COND (9a465037…), HYP21-COND (a295fd6b…), chain verified OK, N=135

Question asked: does per-regime x per-asset conditioning surface any REAL,
economically-motivated edge that the aggregate null hid — or do these two
near-misses stay net-negative/noise in every regime/asset cell?

Short answer: NO. Conditioning does not rescue either. xsmom's positive cell is
the same crypto beta the aggregate already diagnosed; OI-level's only
positive-portfolio cell is a small-sample (n=17) "range" cell that is textbook
noise. No economically-motivated sub-edge emerges.

---

## 1. Regime classifier (pre-registered, objective)

REGIME = BTC trend on Hyperliquid native-perp mark_price DAILY close
(~/.hermes/market_data/hl_oi_hf/), 200-day SMA, band +/-3% (documented):

    (1) range     if  |close/SMA200 - 1| <= 3%
    (2) risk_off  if  close < SMA200          (pct < -3%)
    (3) risk_on   if  close > SMA200 AND SMA200 rising  (sma[t] > sma[t-1])
    (4) range     otherwise                   (above band but SMA not rising)

Asymmetry is deliberate: risk_off needs only "below the SMA"; risk_on needs the
up-trend CONFIRMED (both above-the-band AND SMA rising). "Above band but SMA not
rising" resolves to range (unconfirmed).

No look-ahead: regime[d] uses only BTC closes through day d. xsmom's signal uses
closes through t-1, so its trades read regime as of t-1 (series shifted 1 day);
the OI spread forms its signal at close t and fills next-open, so it reads regime
as of t. Both are strictly pre-fill.

Coverage: 1,062 days classified (2023-12-05 -> 2026-10-31), split risk_on 611 /
risk_off 353 / range 98. The xsmom panel starts 2022-11, so its first ~29 weekly
episodes fall BEFORE regime coverage (reported as no-regime, excluded). The OI
panel (2023-05-20 -> 2026-10-31) is fully covered after the SMA warm-up.

Unit note: all nets below are in bps. For xsmom, net is also expressible in R
(1R = 100 bps = 1% capital). Cost = fee_source single table: 4.5 bps taker/leg,
one position round-trip = 12 bps (4.5*2 + 2.5 slip + 0.5 funding); OI spread
"both legs" = 24 bps (the DECISION cost). No leverage, LIVE off, no re-tuning.

---

## 2. xsmom (cross-sectional momentum; G3-pass / G4-G5-fail)

Shipping config (kappa=0.5, band=0.25, weekly rebalance, top-quintile LONG-only,
BTC 200-DMA overlay). Re-run on current HL 1d bars: 180 episodes, mean net R
+0.5284. 151 episodes fall in a classified regime.

Regime sample split (holding periods): range = 17, risk_off = 47, risk_on = 87.

### (a) per-regime net (portfolio = official strategy P&L)

    regime    n     net_total(bps)   PF     win%
    range     17       -493.6        0.83   58.8
    risk_off  47       +264.4        1.04   40.4
    risk_on   87      +6673.2        1.36   48.3

    per-name (single-name) nets by regime:
    range     92      +2760.4        1.06   46.7
    risk_off 278     +11689.8        1.09   43.9
    risk_on  478     +69958.8        1.26   43.9

The edge is CONCENTRATED in risk_on (PF 1.36, +6,673 bps across 87 weeks).
risk_off is ~flat (PF 1.04; win rate only 40.4% but payoff-skewed positive),
range is NEGATIVE (PF 0.83).

### (b) per-asset net (single-name 7d forward, net of 12 bps; top by trade count)

    coin   n   net(bps)  PF     coin   n   net(bps)  PF
    TRX   62   +7638    1.89    JUP   38   -6737    0.73
    ZEC   53  +32802    1.91    XRP   37  +13254    2.05
    NEAR  47   +4488    1.15    BNB   37   -8219    0.45
    BCH   43   -5009    0.73    BTC   36    +956    1.14
    UNI   43     -27    1.00    SUI   36    -779    0.97
    AAVE  43   +7197    1.44    WLD   34    -845    0.96
    SOL   41  +11349    1.69    (rest 16)  +48732
    HYPE  41  +11805    1.75
    ETH   38   +4834    1.69

The per-asset net is DIFFUSE and broadly positive (most coins up, a few down:
BNB, JUP, BCH, SUI, WLD). This is not a few names carrying the book — it is a
long-only momentum book riding a rising-tide market.

### (c) economically-motivated positive cells? — NO, it is beta.

The risk_on positive cell is the SAME Bitcoin-trend beta the aggregate audit
already flagged ("directional beta book, not a market-neutral spread"). Momentum
works in confirmed up-trends and stalls/reverses in risk-off/range — that is the
known empirical regularity for momentum, and it is exactly what we see. There is
no coin- or regime-specific mechanism beyond "long recent winners during a BTC
uptrend." The per-asset winners (ZEC +32.8k bps, XRP PF 2.05) are momentum names,
not a curated sub-edge. Sample sizes are healthy (n=87 for risk_on) but the
aggregate already failed G4/G5 (PBO 0.56, DSR 0.66) — conditioning on risk_on
just re-labels the same beta, it does not resurrect a robust, generalizing edge.

> VERDICT xsmom: stays a directional beta artifact. No new edge surfaced.

---

## 3. OI-level composite (HYP-21 C-positioning = z(OI-change 7d) + z(OI-level 90d))

Long top-decile / short bottom-decile, equal weight. Two horizons:

### hold = 1d (daily rebalance; n = 781 classified rebalances)

Regime split: range 90, risk_off 221, risk_on 470.

    (a) per-regime net (portfolio, 24bps both-legs):
    regime    n     net_total(bps)   PF     win%
    range     90       -1743.4      0.77   42.2
    risk_off 221       -2154.3      0.88   44.3
    risk_on  470       -1558.9      0.97   46.2

    per-name nets: range PF 0.96, risk_off PF 0.98, risk_on PF 1.00.

Net NEGATIVE in EVERY regime at 1d. No green cell at all. The signal is
transaction-cost-dead intraday (consistent with the correct-cost report's
"-5.47 bps/reb" at 1d).

### hold = 5d (non-overlapping stride-5 resample; n = 156 classified rebalances)

Regime split: range 17, risk_off 47, risk_on 92.

    (a) per-regime net (portfolio, 24bps both-legs):
    regime    n     net_total(bps)   PF     win%
    range     17      +2591.3       2.42   47.1
    risk_off  47       -220.2       0.97   42.6
    risk_on   92      +1224.1       1.07   47.8

    per-name nets: range PF 1.15, risk_off PF 0.99, risk_on PF 1.03.

    (b) per-asset net (top by trade count): ZEN +14954 (PF 1.67), DOGE +12428
    (PF 2.01), ZRO +13090 (PF 2.15), but BANANA -9766, ENS -14532, POLYX -8257,
    kLUNC -9408. The "rest" 211 coins net +55,451 bps.

At 5d the portfolio is marginally positive in range (+2,591 bps, PF 2.42) and
risk_on (+1,224 bps, PF 1.07), flat-to-negative in risk_off (-220 bps, PF 0.97).
But the NAME-level PF in range is only 1.15 and in risk_on 1.03 — there is no
per-trade edge, just a thin positive drift on a small, high-variance sample.

### (c) economically-motivated positive cells? — NO.

The ONLY visually-positive portfolio cell is "range @ 5d" with PF 2.42 — on
n = 17 non-overlapping 5-day rebalances. That is the canonical "green cell on a
small sample = noise" case the brief warns about. There is no mechanism tying
C-positioning (OI change + OI level) to ranging markets specifically; the more
parsimonious read is that ranging markets simply have less directional beta to
swamp the weak signal, and 17 samples is far too few to distinguish that from
luck. The correct-cost G4/G5 verdict (10th-pct split PF 0.66, DSR 0.33, PBO 0.39)
stands: the signal is too weak relative to its own ~500 bps/reb noise to claim
as non-overfit, and conditioning on regime/asset does not change that. The
per-asset "winners" (ZEN, DOGE, ZRO) rotate and show no persistence or economic
story.

> VERDICT OI-level: net-negative (1d) or noise (5d) in every regime/asset cell.

---

## 4. Honest read (the answer)

Per-regime x per-asset conditioning surfaces NO real, economically-motivated
edge that the aggregate null hid, in either strategy.

- xsmom: positive ONLY in risk_on, and that is the crypto-trend beta the
  aggregate audit already diagnosed — momentum-in-an-uptrend, not a decoupled
  cross-sectional alpha. risk_off flat, range negative. No new edge.
- OI-level: net-negative in every 1d regime; at 5d only a small-n (n=17) "range"
  cell with PF 2.42 that fails the noise test (name-level PF 1.15, no mechanism,
  no persistence). Every other cell is ~PF 1.0.

Both near-misses stay net-negative or noise in every regime/asset cell. The
conditional grid confirms rather than overturns the aggregate null. No
promotion. LIVE off.

Method notes (for audit): path-scoped commit only; one fresh-param_hash trial
per strategy (regime definition + cost model are part of the param dict, so
these hashes differ from every prior run); no look-ahead (regime read pre-fill);
cost charged from the single fee_source table (4.5 bps taker/leg).
