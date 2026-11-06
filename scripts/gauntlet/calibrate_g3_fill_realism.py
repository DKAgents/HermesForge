#!/usr/bin/env python3
"""
calibrate_g3_fill_realism.py — US-228 phase 1: data-gathering (read-only).

Measure the EMPIRICAL Hyperliquid perp execution cost (maker/taker fee + realized
slippage vs mark) from Ironflow tick-level fill data, to calibrate the G3
fill-realism model against reality instead of the current guessed pessimistic
assumptions (45 bps/leg taker hurdle, 90 bps round-trip; fee_source 12 bps
round-trip "realistic"; maker fill_prob 0.35).

Data source: Ironflow API (https://docs.ironflow.sh) — keyless read access,
24 h rolling history. hl.fills has per-side rows with is_taker (Bool), fee
(negative = rebate), notional, price; hl.mark_prices samples mark every ~10 s
for the slippage reference. Use POST /v1/query (read-only ClickHouse SQL).

HARD RULES: LIVE off, no orders, read-only. This script does NOT touch the G3
gate code (that is the next phase). It only measures and reports.

Usage:
    python3 calibrate_g3_fill_realism.py [--markets BTC-PERP,ETH-PERP,...]
                                         [--hours 24] [--no-write]
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request

API = "https://api.ironflow.sh/v1/query"

# Liquid tier + a broader mid/liquid tier to bracket the cross-sectional
# universe (HYP-21 ranks ALL native perps; the illiquid tail costs more).
LIQUID = ["BTC-PERP", "ETH-PERP", "SOL-PERP", "HYPE-PERP"]
BROADER = ["AVAX-PERP", "LINK-PERP", "DOGE-PERP", "XRP-PERP",
           "SUI-PERP", "ARB-PERP", "PEPE-PERP", "OP-PERP", "TIA-PERP", "INJ-PERP"]

# Current G3 model anchors (for the comparison report only — never edited here).
G3_GUESSED = {
    "hurdle_bps_per_leg": 45.0,       # revalidate_hyp20/21 COST_HURDLE_BPS_LEG
    "hurdle_bps_round_trip": 90.0,    # 2 legs charged
    "fee_source_round_trip_bps": 12.0,  # fee_source.get_round_trip_bps("crypto")
    "fee_source_both_legs_bps": 24.0,   # hyp21 cost_real = 2 * 12
    "maker_fill_prob": 0.35,
    "maker_adverse_selection_bps": 1.5,
}


def query(sql: str, timeout: int = 60) -> dict:
    req = urllib.request.Request(
        API, data=json.dumps({"sql": sql}).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def _markets_in(markets: list[str]) -> str:
    return "(" + ",".join(f"'{m}'" for m in markets) + ")"


def fee_and_split(markets: list[str], hours: int) -> list[dict]:
    """Maker/taker fee schedule + notional split, by market and taker flag."""
    sql = f"""
SELECT market AS mkt, is_taker AS taker,
       count() AS n, round(sum(notional)) AS usd,
       round(sum(fee)/sum(notional)*10000,3) AS fee_bps_wtd,
       round(quantile(0.5)(fee/notional*10000),3) AS fee_bps_med
FROM hl.fills
WHERE market IN {_markets_in(markets)} AND ts >= now() - INTERVAL {hours} HOUR
GROUP BY mkt, taker ORDER BY mkt, taker
"""
    return query(sql)["rows"]


def slippage_by_bucket(markets: list[str], hours: int) -> list[dict]:
    """Taker realized slippage vs mark (half-spread + impact), by notional bucket.

    slip = (price - mark)/mark*1e4 for buys, (mark - price)/mark*1e4 for sells
    (always >= 0 for a taker: they cross the spread). ASOF join to the most
    recent mark sample at or before the fill (no look-ahead).
    """
    sql = f"""
SELECT f.market AS mkt,
       CASE WHEN f.notional < 1000 THEN '<1k'
            WHEN f.notional < 10000 THEN '1k-10k'
            WHEN f.notional < 100000 THEN '10k-100k'
            WHEN f.notional < 1000000 THEN '100k-1m'
            ELSE '>1m' END AS bucket,
       count() AS n,
       round(quantile(0.5)(if(f.side='buy',(f.price-m.price)/m.price,
                              (m.price-f.price)/m.price)*10000),3) AS slip_med,
       round(quantile(0.9)(if(f.side='buy',(f.price-m.price)/m.price,
                              (m.price-f.price)/m.price)*10000),3) AS slip_p90
FROM hl.fills AS f
ASOF LEFT JOIN hl.mark_prices AS m ON f.market = m.market AND f.ts >= m.ts
WHERE f.market IN {_markets_in(markets)} AND f.is_taker = 1
  AND f.ts >= now() - INTERVAL {hours} HOUR
GROUP BY mkt, bucket ORDER BY mkt, bucket
"""
    return query(sql)["rows"]


def fee_by_bucket(markets: list[str], hours: int) -> list[dict]:
    sql = f"""
SELECT market AS mkt,
       CASE WHEN notional < 1000 THEN '<1k'
            WHEN notional < 10000 THEN '1k-10k'
            WHEN notional < 100000 THEN '10k-100k'
            WHEN notional < 1000000 THEN '100k-1m'
            ELSE '>1m' END AS bucket,
       count() AS n,
       round(sum(fee)/sum(notional)*10000,3) AS fee_bps
FROM hl.fills
WHERE market IN {_markets_in(markets)} AND is_taker = 1
  AND ts >= now() - INTERVAL {hours} HOUR
GROUP BY mkt, bucket ORDER BY mkt, bucket
"""
    return query(sql)["rows"]


def report(markets: list[str], hours: int, no_write: bool) -> dict:
    fs = fee_and_split(markets, hours)
    slip = slippage_by_bucket(markets, hours)
    feeb = fee_by_bucket(markets, hours)

    # merge fee + slippage per (market, bucket) for the taker all-in cost
    by_key = {}
    for r in feeb:
        by_key[(r[0], r[1])] = {"fee_bps": float(r[3])}
    for r in slip:
        k = (r[0], r[1])
        d = by_key.setdefault(k, {})
        d["slip_med"] = float(r[3]); d["slip_p90"] = float(r[4]); d["n"] = int(r[2])

    # taker all-in per leg (median slip) + round-trip (2 legs, HYP-21 "both legs")
    table = []
    for k, d in sorted(by_key.items()):
        fee = d.get("fee_bps", 0.0); smed = d.get("slip_med", 0.0)
        sp90 = d.get("slip_p90", 0.0)
        leg_med = fee + smed
        leg_p90 = fee + sp90
        table.append({
            "market": k[0], "bucket": k[1], "n": d.get("n", 0),
            "taker_fee_bps": fee, "slip_med_bps": smed, "slip_p90_bps": sp90,
            "leg_allin_med_bps": round(leg_med, 2),
            "roundtrip_2leg_med_bps": round(2 * leg_med, 2),
            "roundtrip_2leg_p90_bps": round(2 * leg_p90, 2),
        })

    out = {
        "source": "Ironflow API /v1/query (keyless, read-only)",
        "hours": hours,
        "markets": markets,
        "maker_taker_split_and_fee": [{"market": r[0], "taker": bool(r[1]),
                                        "n": int(r[2]), "usd": float(r[3]),
                                        "fee_bps_wtd": float(r[4]),
                                        "fee_bps_med": float(r[5])} for r in fs],
        "taker_cost_by_size": table,
        "g3_guessed_model": G3_GUESSED,
    }
    print(json.dumps(out, indent=2))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--markets", default=",".join(LIQUID + BROADER))
    ap.add_argument("--hours", type=int, default=24)
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()
    markets = [m.strip() for m in args.markets.split(",") if m.strip()]
    report(markets, args.hours, args.no_write)
    return 0


if __name__ == "__main__":
    sys.exit(main())