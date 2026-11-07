# HYP-24 — momentum x wide-target x regime (combined) — verdict

Date: 2026-11-07 (UTC)
Owner: backtester
Hypothesis: trading/strategies/Hypotheses/HYP-24-momentum-wide-target-regime.md (pre-registered, FIXED — no tuning)
Driver: scripts/gauntlet/revalidate_hyp24_momentum_wide_target_regime.py
Trial: data/gauntlet/trials.jsonl (HYP-24, param_hash 6e747aee…)

VERDICT: CLOSED as a tradeable symmetric momentum edge. The combined levers
(wide 3R target + regime conditioning) do NOT produce a clean, robust,
economically-motivated net-positive cell. But the zero-drift control exposed a
REAL, structure the hypothesis did not pre-register: the edge is not symmetric —
it lives entirely in the SHORT leg (short-side continuation), while the LONG leg
is net-negative (winners mean-revert). That is a follow-up hypothesis, not a
HYP-24 win.

---

## 0. What was tested

Cross-sectional 7d price momentum (long top-decile / short bottom-decile),
stop = 2x ATR14 (=1R), target = 3R (the HYP-23 wide target), resolved at hourly
first-touch. Cost = 4.5 bps/leg taker + 2.5 bps adverse entry slip + hourly
funding (longs pay positive funding). Regime = BTC 200d SMA on the CLEANED BTC
series (conditional_grid taxonomy: BAND=0.03; risk_on = above band + SMA rising,
risk_off = below band, else range). 235 native perps, 2023-05-20 -> 2026-10-31.

Regime day split: risk_on 611 / risk_off 353 / range 98 (199 days before the
200d SMA exists, excluded).

## 1. Zero-drift control — what it is and why it matters

The honesty gate: a 3R target on a log-normal asset already has a positive
gross tilt with ZERO alpha (arithmetic +3R/-1R levels are log-asymmetric). To
discount geometry, a zero-drift control was run ALONGSIDE: per-coin hourly
log-returns are demeaned (drift -> 0, realized vol preserved) and re-anchored at
each trade's REAL entry, so the control keeps identical entries, ATR sizing,
fees and funding — ONLY the forward price drift is removed. Real - control =
the momentum drift's contribution (alpha), discounting geometry.

Sanity: control fee_r and risk_pct distributions are IDENTICAL to real (both
0.0082R), so costs are matched. (An earlier naive "synthetic-ATR" control
produced a 25x fee artifact from near-zero-ATR synthetic trades — rejected.)

## 2. The matrix

### 2a. Pooled

| run     | n       | net R | win   | PF    | gross R |
|---------|--------:|------:|------:|------:|--------:|
| REAL    | 32,425  | +0.038 | 0.415 | 1.073 | +0.047  |
| CONTROL | 31,680  | +0.001 | 0.396 | 1.001 | +0.007  |

The wide 3R target does NOT manufacture net edge in the balanced long-short
book: control net is ~0 (the long-leg and short-leg geometric tilts cancel).
This refines HYP-23 — the 3R target is not a free lunch at net level.

### 2b. Per-regime (mean net R per trade: real vs control)

| regime   | n       | real   | ctrl   | delta  | PF(real) | PF(ctrl) | win(real) |
|----------|--------:|-------:|-------:|-------:|---------:|---------:|----------:|
| risk_on  | 16,916  | +0.074 | +0.023 | +0.051 | 1.146    | 1.044    | 0.435     |
| risk_off | 11,057  | +0.001 | -0.011 | +0.012 | 1.001    | 0.980    | 0.395     |
| range    |  2,958  | -0.048 | -0.139 | +0.092 | 0.913    | 0.771    | 0.383     |

risk_on is the only net-positive cell and it beats the control (+0.051R). BUT
see the year grid below — it is a decaying bull artifact, not a stable edge.

### 2c. Sub-period robustness (REAL net R/trade, year x regime)

| year | risk_on        | risk_off       | range          |
|------|----------------|----------------|----------------|
| 2023 | +0.196 (452)   | —              | +0.057 (16)    |
| 2024 | +0.064 (6572)  | -0.138 (1196)  | -0.176 (1326)  |
| 2025 | +0.094 (7512)  | -0.003 (2934)  | +0.051 (1286)  |
| 2026 | +0.015 (2380)  | +0.026 (6927)  | +0.078 (330)   |

risk_on decays monotonically toward zero (+0.20 -> +0.06 -> +0.09 -> +0.02);
risk_off FLIPS sign positive in 2026. The "regime conditions the signal" story
does not hold up across time — no cell is stable or economically clean.

### 2d. Per-asset (top by sample) — the honesty gate fires here

The eye-catching per-asset "winners" are reproduced ~1:1 by the zero-drift
control (delta near zero) — they are the geometric tilt of persistent-LONG
high-vol coins, NOT alpha:

| coin     | n    | real   | ctrl   | delta  |
|----------|-----:|-------:|-------:|-------:|
| NEIROETH | 183  | +0.645 | +0.626 | +0.019 |
| VVV      | 245  | +0.354 | +0.362 | -0.008 |
| MERL     | 348  | +0.300 | +0.292 | +0.008 |
| TRX      | 288  | +0.246 | +0.252 | -0.006 |
| KAS      | 211  | +0.123 | +0.122 | +0.001 |

(real numbers here are the strategy-level mean net R over each coin's own
trades; the control reproduces them, so they carry no alpha.)

## 3. The real structure the hypothesis missed (un-pre-registered)

Decomposing the balanced book into its two legs, real vs control:

| leg   | REAL net R | CTRL net R | alpha (real - ctrl) |
|-------|-----------:|-----------:|--------------------:|
| LONG  | -0.032     | +0.093     | -0.125              |
| SHORT | +0.109     | -0.092     | +0.201              |

The control's +0.093 / -0.092 is exactly the expected geometric tilt (long
positive, short negative), cancelling to ~0. The REAL book is the opposite sign:
the LONG leg (buying top-decile winners) is net-NEGATIVE (-0.032R, -0.125R below
geometry — winners mean-revert), and the SHORT leg (shorting bottom-decile
losers) is net-POSITIVE (+0.109R, +0.201R above geometry — losers keep
decaying).

So the entire +0.038R pooled net is the SHORT leg (+0.109R) dragging up a
LOSING long leg (-0.032R). Momentum here is a one-sided short-continuation
effect, not a symmetric long/short edge.

SHORT leg by year: 2023 -0.067, 2024 +0.091, 2025 +0.199, 2026 +0.051.
Positive from 2024 onward but again decaying into 2026.

## 4. Honest verdict

Does momentum (with a wide 3R target AND regime conditioning) produce ANY real,
non-geometric, economically-motivated net-positive cell?

As pre-registered (symmetric long/short, regime-conditional, wide target): NO.

1. The wide-target lever contributes ~0 net to the balanced book (control pooled
   = +0.001R). It is not an edge source at net — it just lets the drift run
   instead of being fee-chopped.

2. The regime lever does not yield a stable cell. risk_on is positive and beats
   the control, but it is a decaying bull drift (-> +0.015R by 2026) and the
   regime story breaks (risk_off flips positive in 2026). It would not survive
   CPCV/G4/G5 (single-regime, decaying, unconditional momentum t < 1 remains).

3. The per-asset "winners" are geometric tilt (control reproduces them), exactly
   the honesty-gate failure HYP-24 anticipated.

The one thing that IS real and non-geometric is NOT what was pre-registered: the
LONG/SHORT asymmetry. Short-side continuation (+0.20R above geometry) is a
genuine, economically-motivated structure; the long side is a net loser. This is
a candidate follow-up (HYP-25) — and it carries a serious real-world caveat:
shorting the bottom-decile means shorting tiny, illiquid, often dying/dead coins,
where borrow availability, funding sign (do shorts actually receive funding?),
delisting/halts and G3 fill-realism are the dominant concerns. That must be its
own pre-registered test with the execution gates, not a retroactive HYP-24 win.

Net: momentum as a symmetric, regime-conditioned tradeable edge is CLOSED.
Momentum as a one-sided SHORT-continuation effect is a live, un-tested follow-up.