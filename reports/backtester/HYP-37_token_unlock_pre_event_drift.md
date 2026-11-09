---
hypothesis_id: HYP-37
backtester: hermes-forge (backtester)
status: DATA-GATED (D-7 unlock calendar not reachable at free tier — untested, not rejected)
date: 2026-11-09
venue: hyperliquid
instruments: HL perps on tokens with a scheduled unlock >= 1%/2%/5% of circulating supply
data: stored HL mark/oracle (hl_oi_hf_clean, 2023-05+) + funding (hl_funding_hf, 2023-05+) + daily OHLC (crypto/*.parquet, 2020-08+). No fabrication.
note: renumbered from directive §8. Directive label "HYP-31" collides with the existing HYP-31 (cross-venue basis); assigned next free ID HYP-37.
---

# HYP-37 — Token-unlock pre-event drift (short): DATA-GATED verdict

VERDICT: DATA-GATED. The one binding dependency — D-7, a token-unlock
calendar (token / date / % of circulating supply, historically and
as-known-at-time) — is not obtainable at the free tier. Every reachable source
is paid or bot-blocked. The price, funding, and BTC-reference legs are already
stored and deep. This hypothesis is therefore **untested, not rejected** —
the same disposition as HYP-33, reopens automatically once the calendar is
reachable (paid tier or forward accumulation). No backtest trial is logged
(nothing was tested; logging a drift number on a missing calendar would itself
be fabrication).

---

## 0. Renumber note (collision chain)

The directive (§8) labeled this "HYP-31", but HYP-31 is already taken
(cross-venue funding/basis spread, committed 2026-11-08). The next free number
at first glance was HYP-36, but HYP-36 is claimed in-flight by a concurrent
agent (polymarket longshot overpricing — itself renumbered from a "HYP-28"
collision, still uncommitted). Reusing either would corrupt the hypothesis
register and the append-only trials ledger. Assigned the next unambiguously
free ID: **HYP-37**.

This is the second collision in this directive round, both caused by the
directive mapping its §items onto stale HYP numbers (28/31) that were already
consumed by the recent HYP-30..35 wave. Recommendation (permanent fix): the
orchestrator should allocate hypothesis IDs from a single central counter
rather than hand-numbering directive items.

## 1. D-7 data gate — what was verified (2026-11-09)

| Source | Result |
|---|---|
| Tokenomist (primary, named in directive) | `api.tokenomist.com` unreachable — TLS "unrecognized name" (SNI); site serves a JS-redirect lander. API is subscription-gated. |
| DefiLlama `/emissions` | HTTP **402** — "Upgrade to the paid API plan at defillama.com/subscription". |
| DefiLlama `/unlocks` | HTTP 404 — route does not exist. |
| CoinGecko (free) | `/coins/{id}` has supply-breakdown / ICO flags but **no unlock schedule**; `/coins/.../unlocks` -> 404. |
| CoinMarketCap | HTTP 401 — API key required (paid Pro). |
| CryptoRank | HTTP 403 — Cloudflare bot-block. |
| Local stores | no `unlocks` / `token_unlocks` / `unlock_calendar` data under `~/.hermes/market_data/`. |

Conclusion: the unlock calendar is **paid-only**. A historical calendar with
per-event % of circulating supply (and the "as-known-at-time" snapshot the
leakage rule demands) is precisely the data only Tokenomist/DefiLlama-Pro
provide. Free sources expose at most a shallow forward list, not deep
backfill — and no survivorship-safe history.

## 2. What IS ready (price + funding legs, already stored)

- Perp prices: `hl_oi_hf_clean/*.parquet` — hourly `mark_price`/`oracle_price`
  for the HL perp universe, 2023-05 -> present (42 monthly files).
- Funding: `hl_funding_hf/*.parquet` — hourly `funding_rate`/`premium`,
  2023-05 -> present, 494 distinct coins.
- BTC reference: `crypto/BTC.parquet` — daily OHLC 2020-08 -> present.
- Daily OHLC for the wider token set: `crypto/*.parquet` (2020-08 -> present).

So once a calendar is in hand, the full pipeline (event build -> BTC-beta
neutralization -> funding P&L -> net P&L per threshold) is immediately runnable.

## 3. G0 cost screen (real data — the one analysis runnable now)

The prior literature reports a median ~-14.7% (~1470 bps) pre-event drift on
large unlocks. The question G0 answers is whether funding + taker cost would
swamp that. It does not:

- Taker round-trip: ~4.5 bps/leg x 2 = ~9 bps.
- Funding P&L on a 30-day short (stored history, 494 coins):
  median **+0.55 bps**, min -15.97 bps, max +43.20 bps.
- All-in cost ~9.6 bps median vs ~1470 bps gross. **Funding is not the
  binding constraint; the calendar is.**

Note the funding tail: a few thin-float tokens run persistently *negative*
funding (short pays, up to ~-16 bps/30d) — the very tokens where the prior
says the drift is largest. That is a real interaction the full test must price,
but it is an order of magnitude below the gross effect and does not gate the
hypothesis.

## 4. Unblock path

- Pay for Tokenomist or DefiLlama-Pro unlock history (the only clean,
  survivorship-safe, as-known-at-time source), OR
- Forward-accumulate a free unlock calendar (token/date/% supply) starting
  now, so that a forward paper test (G7-style) becomes runnable in ~6-12
  months without any paid tier.
- Both paths re-open HYP-37 automatically; the pre-registered thresholds
  (1%/2%/5%), windows (T-30->T-1, T-14->T+3), BTC-beta neutralization,
  funding P&L, and falsification rule (median BTC-relative return >= 0 OR
  10th-pct PF < 1.0 net) are fixed and unchanged.

## 5. Honest verdict

A scheduled-fundamental-supply short is a genuinely different edge class from
the price/positioning/flow signals already searched to null, and the prior is
concrete (Tokenomist -14.7% median; Keyrock ~16k events). But it cannot be
tested without the calendar, and I will not manufacture drift numbers from a
missing input. DATA-GATED — untested, not rejected. No trial logged; live is
OFF.
