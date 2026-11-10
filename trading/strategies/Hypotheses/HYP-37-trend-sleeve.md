---
hypothesis_id: HYP-37
source: internal (directive §8 — "HYP-33 · Time-series trend on majors, volatility-targeted")
venue: hyperliquid (perp price series; daily bars)
instruments: BTC, ETH, SOL (majors)
horizon: daily rebalance; 20/60/120-day lookbacks; forward horizons 1-20d for IC
signal: time-series trend = 0.5*mom20 + 0.3*mom60 + 0.2*mom120 (log-return momentum blend)
data_dependencies:
  - ~/.hermes/market_data/crypto/{BTC,ETH,SOL}.parquet (daily OHLC, 2020-08-19 -> 2026-11-08)
  - ~/.hermes/market_data/hl_funding/funding.db (hourly HL funding, 2025-09-27 -> 2026-11-08;
    carry-sleeve correlation + funding sensitivity only)
cost_hurdle_bps: maker 6.0 round-trip / taker 12.0 round-trip (fee_source crypto: fee*2 + slip 2.5
  + funding 0.5); per-leg txn = fee + slip/2 (maker 2.75, taker 5.75). Funding accrual on the
  held position reported separately from real HL funding (13.5mo window).
counterparty: slow information diffusion + trend-following flows (the most widely documented
  crypto return pattern). The other side is the mean-reversion / counter-trend trader and the
  impatient liquidity provider who pays up to fade or front-run the trend.
topic: structural (time-series momentum / trend-following sleeve)
confidence: medium (mechanism is well-documented; but prior program found every signal null at
  taker cost — this test exists to check whether MAKER execution + buffering + vol-targeting
  rescues it, per M-2/M-3)
note: |
  RENUMBER COLLISION FLAG — the directive labeled this "HYP-33", but HYP-33 is already taken
  (crowd long/short ratio, DATA-GATED) and HYP-36 is taken (Polymarket longshot, directive
  HYP-28). Rather than overwrite an existing pre-registration (data loss is unacceptable), this
  is registered as HYP-37 (next free number). Cross-reference: directive §8 HYP-33 == HYP-37.
has_quotes: false
tags: []
---
# HYP-37 — Time-series trend on majors, volatility-targeted (sleeve alongside carry)

## Motivation

The directive §8's ONE remaining price signal in the new program. HYP-16 showed that a *bare
trend filter* carried the effect that open interest had been credited with — i.e. the only thing
with content in the OI test was trend itself, not OI. This tests whether a clean time-series
trend on the majors, executed as a MAKER (not taker — the prior program screened every signal at
taker cost and found null), with M-3 buffering and HAR-RV vol-targeting, survives the amended
gates.

## Mechanism / counterparty (M-8)

Slow information diffusion and trend-following flows — the most widely documented crypto return
pattern. The counterparty is the mean-reversion/counter-trend trader and the impatient liquidity
provider: they accept the loss because they are fading a persistent drift (reverting against a
trend that has not ended) or paying the spread to chase a move late. They stop (the edge dies)
when the trend is arbitraged — which is exactly what the original program claimed was happening
to momentum; M-9 requires that any "decay" claim carry a >=6-subperiod trend test, so this run
reports year-by-year subperiod P&L rather than asserting decay.

## Pre-registered operationalization (FIXED — no tuning)

- Universe: BTC, ETH, SOL daily.
- Trend signal: s_t = 0.5*log(close_t/close_{t-20}) + 0.3*log(close_t/close_{t-60}) +
  0.2*log(close_t/close_{t-120}).
- Vol forecast (HAR-RV): rv_d = daily squared log-return; rv_w = 5d mean(rv_d); rv_m = 21d
  mean(rv_d); forecast_var = 0.25*rv_d + 0.35*rv_w + 0.40*rv_m; sigma_hat = sqrt(forecast_var).
- Vol-target: scale = min(1.0, sigma_daily_target / sigma_hat), sigma_daily_target =
  0.20/sqrt(365). NO leverage (position cap 1.0).
- Position (pre-buffer): long/short -> sign(s_t)*scale; long/flat -> (s_t>0)*scale.
- M-3 buffer: sign hysteresis — flip direction only when |s_t| >= B (round-trip cost), B_maker =
  6 bps = 6e-4, B_taker = 12 bps = 1.2e-3. Otherwise hold the prior direction.
- Cost: per-leg txn = fee + slip/2 (maker 2.75, taker 5.75 bps); charged on |delta w|.
- Sampling: NON-OVERLAPPING for all inferential stats (weekly blocks for CPCV/DSR; stride-h for
  IC-by-horizon). The overlapping-return inflation pitfall is the whole reason for this.

## Variants (pre-registered)

- long/flat vs long/short.
- maker vs taker (M-2 cost symmetry — maker must be evaluated, not taker-only).

## Falsification / promotion (amended gates)

Fail (do not promote) if, AT MAKER COST:
- 10th-percentile CPCV fold PF < 1.0 (G4), OR
- DSR below threshold under M-6 family accounting (G5, DSR < 0.95), OR
- edge not present at maker cost (M-2) — i.e. the maker net is not materially better than taker.

## Sleeve evaluation (required, not optional)

Report correlation of the trend sleeve with the delta-neutral funding carry (real HL funding,
overlap window), and the COMBINED drawdown. Load-bearing interaction: a long-trend sleeve PAYS
funding while the carry HARVESTS it — quantify the funding sign/P&L interaction explicitly.
