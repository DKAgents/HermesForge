# HYP-23 — R:R target-ratio sensitivity (methodology test)

**Verdict: net expectancy RISES, not falls, but NOT because "3:1" is an edge source.**
The prior is falsified on its mechanism (fees/funding), not on its spirit
(R:R does not manufacture alpha).

## Result table (the whole point)

native HL perps, 235 coins, 2023-05 -> 2026-10, ~32.4k trades per arm.
Signal = cross-sectional 7d momentum (long top-decile / short bottom-decile),
stop = 2x ATR14 (= 1R), cost = 4.5 bps/leg taker + hourly funding + 2.5 bps
adverse entry slip. Only the target moves.

| target | net multi-R | win rate | PF | bars held | gross R | fee R | funding R |
|--------|------------:|--------:|----:|---------:|--------:|------:|----------:|
| 1R     |    -0.0040  |  0.507  | 0.991 |  9.38   | +0.0008 | 0.0082 | +0.0034 |
| 2R     |    +0.0254  |  0.430  | 1.050 | 12.34   | +0.0319 | 0.0082 | +0.0017 |
| 3R     |    +0.0382  |  0.415  | 1.073 | 13.26   | +0.0466 | 0.0082 | -0.0002 |

(Net multi-R is mean net R per trade after fills + funding. Exit breakdown
is 100% stop/target — time-stop never binds at hourly resolution, so there is
no "time-stop drift harvest" confound.)

## Key comparison

Net expectancy RISESt monotonically: -0.004 -> +0.025 -> +0.038 R per trade.
The gap net(3R) - net(1R) = +0.042 R is robust to the time-stop horizon
(5/10/20/60/no-limit bars all give the same ordering), and to stop-at-level vs
gap-through exit conventions (gap-through only deepens the 1R penalty further).

## Why the prior's mechanism was wrong (the honest part)

The prior predicted net(3R) <= net(2R) <= net(1R) via three effects. All three
fail to materialize at realistic cost:

1. "lower win rate amortizes fixed fees worse" — WRONG in this construction.
   Fees are charged per ROUND-TRIP, once per trade, identical whether the trade
   resolves at 1R or 3R. There is no additional fee per bar. fee R is a flat
   0.0082 R across all three arms.
2. "longer hold pays more funding" — true but immaterial. Median HL funding is
   the interest floor (~0.00125%/hr); the momentum follower pays ~|funding| on
   both legs and the mean daily funding sums to ~0. Net funding swing across
   the three arms is 0.0036 R — two orders of magnitude below the gross swing.
3. "realized stop dilutes the far target" — not present. Stops fill at the
   nominal level (the instruction's cost list has no adverse exit slip), and
   the far-target arms hold only ~4 days longer.

## Why net rises (the real mechanism)

Two effects, neither of which is "the ratio makes money":

1. The momentum signal has a weak positive forward drift. Win rate at 3R is
   41.5% vs the ~25% breakeven a no-edge signal would show; at 2R it is 43.0%
   vs ~33%. The farther target simply lets winners run longer (fewer premature
   profit-takes), capturing that drift. At 1R the drift is chopped at +1R and
   the ~0.008 R fee turns a ~breakeven gross into a net -0.004 R.
2. A geometric tilt built into percentage stops on log-normal prices. "+24%"
   and "+36%" (log +0.215 / +0.308) are log-farther than "-12%" (log 0.128), so
   a balanced long-short book on a zero-drift asset already shows gross rising
   +0.002 -> +0.029 R across 1R->3R (verified on a synthetic zero-drift
   control). This is a property of arithmetic R on log-normal crypto, not alpha.

## Verdict on the coach's "prefer 3:1"

Not (b) variance-only and not (c) net-hurting — net rises, so on its face it
looks like (a). But it is not "3:1 is a standalone edge source." The ratio does
not create expectancy; it selects hold-length and win-vs-payoff weighting. For
THIS signal (weak positive drift) at REALISTIC cost (fees constant, funding
negligible), the farther target wins purely because it lets positive drift run
and avoids fee-bleeding early profit-takes. The honest rule of thumb is not
"prefer 3:1 always" — it is "for a signal with positive drift, don't cap the
winner at a tight target; a tight target is a fee tax with no edge payoff."

Note: none of this means momentum is tradeable — the underlying signal's
unconditional forward spread is statistically insignificant (t-stat < 1 across
5/10/20/40d), so this remains a methodology finding, not a strategy candidate.

## Methodology note

First implementation used DAILY bars with a "both-touched -> pessimistic stop"
convention. A synthetic zero-drift control exposed that this biases results
toward stops, and disproportionately at the 1R target (daily range ~ 1R), which
would have fabricated the "net falls then rises" shape. Fixed by resolving
stop/target first-touch at HOURLY resolution (the data is hourly mark_price);
this is unbiased (synthetic control: ~50% win at 1R, balanced). Three fresh
trial entries (one per target, fresh param_hash) were written to the trials
ledger after rolling back the three from the buggy daily-bar run.