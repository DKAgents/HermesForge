#!/usr/bin/env python3
"""
HYP-36 Phase 1 — Polymarket longshot overpricing vs Deribit-implied fair value.

LIVE cross-sectional snapshot (Phase 1). Computes, for every OPEN BTC/ETH market
on Polymarket, the fair risk-neutral probability from the Deribit IV smile and the
wedge = Polymarket "Yes" price - fair value. Classifies longshot (fair <= 0.20),
charges Polymarket fees/spread + a capital charge, and reports cluster structure.

Market types (parsed from the free-text question + resolution rule):
  - "reach $X"  -> up one-touch barrier  (resolves Yes if ANY 1m candle High >= X)
  - "dip to $X" -> down one-touch barrier (resolves Yes if ANY 1m candle Low  <= X)
  - "above $X" / "below $X" on a fixed date -> European digital (threshold)
  - range -> two European digitals
Touch markets are priced as one-touch barriers under GBM (reflection principle).
Threshold/range markets are priced as European digitals via Breeden-Litzenberger
call spreads from the smile.
"""
import json, math, time, urllib.request, urllib.parse, sys
from datetime import datetime, timezone
from collections import defaultdict

GAMMA = "https://gamma-api.polymarket.com"
DERIBIT = "https://www.deribit.com/api/v2/public"
NORM = math.erf  # we'll use scipy-free normal CDF via erf

def norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def http_json(url, timeout=30, retries=3):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json",
                                                       "User-Agent": "hermesforge-research/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if i == retries - 1:
                raise
            time.sleep(1.5 * (i + 1))

# ---------- Deribit smile ----------
def fetch_smile(currency):
    url = f"{DERIBIT}/get_book_summary_by_currency?currency={currency}&kind=option"
    res = http_json(url)["result"]
    # smile[expiry][strike] = (mark_iv, underlying)
    smile = defaultdict(dict)
    spot = None
    for inst in res:
        name = inst["instrument_name"]  # BTC-10NOV26-77500-P
        parts = name.split("-")
        exp = parts[1]
        strike = int(parts[2])
        mark_iv = inst.get("mark_iv")
        if mark_iv is None:
            continue
        smile[exp][strike] = mark_iv / 100.0  # Deribit mark_iv is in percentage points
        if spot is None and inst.get("underlying_price"):
            spot = inst["underlying_price"]
    return smile, spot

def black_call(S, K, T, sigma, r=0.0):
    if T <= 0 or sigma <= 0:
        return max(S - K, 0.0)
    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    return S * norm_cdf(d1) - K * math.exp(-r * T) * norm_cdf(d2)

def black_digital_above(S, K, T, sigma, r=0.0):
    """P(S_T > K) under flat-vol GBM (European digital)."""
    if T <= 0:
        return 1.0 if S > K else 0.0
    d2 = (math.log(S / K) + (r - 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))
    return norm_cdf(d2)

def touch_up_prob(S, K, T, sigma, r=0.0):
    """P(max S_t >= K for t in [0,T]) one-touch up barrier, GBM, K > S.
    Reflection principle: P = Phi((mu*T - a)/(sig sqrtT)) + (K/S)^(2mu/sig^2) * Phi((-mu*T - a)/(sig sqrtT))
    where a = ln(K/S) > 0, mu = r - 0.5 sig^2.
    """
    if K <= S:
        return 1.0
    if T <= 0 or sigma <= 0:
        return 0.0
    mu = r - 0.5 * sigma * sigma
    a = math.log(K / S)              # > 0
    denom = sigma * math.sqrt(T)
    p = norm_cdf((mu * T - a) / denom) + (K / S) ** (2.0 * mu / sigma ** 2) * norm_cdf((-mu * T - a) / denom)
    return min(max(p, 0.0), 1.0)

def touch_down_prob(S, K, T, sigma, r=0.0):
    """P(min S_t <= K for t in [0,T]) one-touch down barrier, GBM, K < S.
    b = ln(K/S) < 0: P = Phi((b - mu*T)/(sig sqrtT)) + (K/S)^(2mu/sig^2) * Phi((b + mu*T)/(sig sqrtT))
    """
    if K >= S:
        return 1.0
    if T <= 0 or sigma <= 0:
        return 0.0
    mu = r - 0.5 * sigma * sigma
    b = math.log(K / S)              # < 0
    denom = sigma * math.sqrt(T)
    p = norm_cdf((b - mu * T) / denom) + (K / S) ** (2.0 * mu / sigma ** 2) * norm_cdf((b + mu * T) / denom)
    return min(max(p, 0.0), 1.0)

def expiry_to_unix(exp, ref_year=2026):
    """Deribit expiry string like '25DEC26' -> unix seconds (08:00 UTC)."""
    months = {"JAN":1,"FEB":2,"MAR":3,"APR":4,"MAY":5,"JUN":6,"JUL":7,"AUG":8,
              "SEP":9,"OCT":10,"NOV":11,"DEC":12}
    day = int(exp[:2]); mon = months[exp[2:5]]; yr = int(exp[5:7]) + 2000
    return int(datetime(yr, mon, day, 8, 0, tzinfo=timezone.utc).timestamp())

# ---------- Polymarket ----------
CRYPTO_EVENT_SLUGS = [
    "what-price-will-bitcoin-hit-before-2027",
    "what-price-will-ethereum-hit-before-2027",
    "what-price-will-bitcoin-hit-in-november-2026",
    "what-price-will-ethereum-hit-in-november-2026",
]

def fetch_pm_markets():
    """Fetch all markets under the BTC/ETH price-level series events."""
    out = []
    for slug in CRYPTO_EVENT_SLUGS:
        url = f"{GAMMA}/events?slug={urllib.parse.quote(slug)}"
        events = http_json(url)
        for e in events:
            out.extend(e.get("markets", []))
    return out

def parse_market(m):
    q = m.get("question") or ""
    ql = q.lower()
    outcomes = json.loads(m.get("outcomes") or '["Yes","No"]')
    yes = m.get("outcomePrices")
    # current price
    best_bid = m.get("bestBid"); best_ask = m.get("bestAsk")
    last = m.get("lastTradePrice")
    # extract price target
    import re
    dollars = re.findall(r"\$([0-9][0-9,]*\.?[0-9]*)", q)
    target = None
    if dollars:
        target = float(dollars[0].replace(",", ""))
    end = m.get("endDate")  # ISO
    # type
    if "reach" in ql:
        typ = "up_touch"
    elif "dip" in ql:
        typ = "down_touch"
    elif "above" in ql:
        typ = "above"
    elif "below" in ql:
        typ = "below"
    else:
        typ = "other"
    # underlying
    if "bitcoin" in ql or "btc" in ql:
        und = "BTC"
    elif "ethereum" in ql or "eth" in ql:
        und = "ETH"
    else:
        und = "?"
    return {
        "question": q, "type": typ, "und": und, "target": target,
        "end": end, "best_bid": best_bid, "best_ask": best_ask, "last": last,
        "closed": m.get("closed", False), "active": m.get("active", True),
        "liquidity": m.get("liquidity"), "volume": m.get("volume"),
        "outcomes": outcomes,
    }

def end_to_unix(end):
    if not end:
        return None
    try:
        return int(datetime.fromisoformat(end.replace("Z", "+00:00")).timestamp())
    except Exception:
        return None

def main():
    now = time.time()
    print(f"snapshot_utc = {datetime.utcfromtimestamp(now).isoformat()}Z")
    print("fetching Deribit smiles ...")
    btc_smile, btc_spot = fetch_smile("BTC")
    eth_smile, eth_spot = fetch_smile("ETH")
    print(f"  BTC spot={btc_spot} expiries={len(btc_smile)}  ETH spot={eth_spot} expiries={len(eth_smile)}")

    print("fetching Polymarket BTC/ETH markets ...")
    markets = fetch_pm_markets()
    parsed = [parse_market(m) for m in markets]
    # dedupe by question (series can duplicate)
    seen = set(); uniq = []
    for p in parsed:
        key = (p["question"], p["closed"])
        if key in seen:
            continue
        seen.add(key); uniq.append(p)
    print(f"  raw={len(parsed)} unique={len(uniq)}")

    open_mkts = [p for p in uniq if not p["closed"] and p["active"]]
    resolved = [p for p in uniq if p["closed"]]
    print(f"  open={len(open_mkts)} resolved={len(resolved)}")

    # build rows
    rows = []
    for p in open_mkts:
        if p["und"] not in ("BTC", "ETH") or p["target"] is None or p["end"] is None:
            continue
        smile = btc_smile if p["und"] == "BTC" else eth_smile
        spot = btc_spot if p["und"] == "BTC" else eth_spot
        endu = end_to_unix(p["end"])
        if endu is None:
            continue
        T = (endu - now) / 86400.0 / 365.0  # years (approx)
        # pick nearest Deribit expiry >= end, else nearest
        exps = sorted(smile.keys(), key=lambda e: expiry_to_unix(e))
        # map exp->unix
        exp_unix = {e: expiry_to_unix(e) for e in exps}
        # choose expiry closest to endu (prefer >= endu)
        best_exp = None; best_gap = 1e18
        for e in exps:
            gap = exp_unix[e] - endu
            if gap >= 0 and gap < best_gap:
                best_gap = gap; best_exp = e
        if best_exp is None:  # all before end
            best_exp = max(exps, key=lambda e: exp_unix[e])
        strikes = sorted(smile[best_exp].keys())
        if not strikes:
            continue
        # ATM IV of that expiry
        atm_iv = smile[best_exp][min(strikes, key=lambda k: abs(k - spot))]
        target = p["target"]

        # Robust vol: use the smile IV at the barrier strike only if it is sane
        # (0.10 <= iv <= 1.50). Deep-wing Deribit marks are degenerate (illiquid /
        # extrapolated to >100% IV) and would corrupt the barrier probability.
        strike_iv = smile[best_exp].get(target)
        if strike_iv is not None and 0.10 <= strike_iv <= 1.50:
            iv = strike_iv
        else:
            iv = atm_iv

        # fair value by type (T = Polymarket horizon; sigma from nearest Deribit expiry smile)
        if p["type"] in ("up_touch", "down_touch"):
            if p["type"] == "up_touch":
                fair = touch_up_prob(spot, target, max(T, 0), iv) if target > spot else 1.0
            else:
                fair = touch_down_prob(spot, target, max(T, 0), iv) if target < spot else 1.0
            method = "barrier_gbm"
        elif p["type"] == "above":
            fair = black_digital_above(spot, target, max(T, 0), iv)
            method = "digital_bs"
        elif p["type"] == "below":
            fair = 1.0 - black_digital_above(spot, target, max(T, 0), iv)
            method = "digital_bs"
        else:
            continue

        yes_price = None
        if p["best_ask"] is not None and p["best_bid"] is not None:
            yes_price = (p["best_ask"] + p["best_bid"]) / 2.0
        elif p["last"] is not None:
            yes_price = p["last"]
        if yes_price is None:
            continue
        wedge = yes_price - fair
        rows.append({
            "und": p["und"], "exp": best_exp, "type": p["type"], "target": target,
            "T_days": round((endu - now) / 86400.0, 1), "fair": fair,
            "yes_price": yes_price, "wedge": wedge, "method": method,
            "iv": round(iv, 4), "atm_iv": round(atm_iv, 4),
            "question": p["question"], "liquidity": p["liquidity"],
            "bid": p["best_bid"], "ask": p["best_ask"],
        })

    # summary
    print(f"\n=== OPEN-market wedge snapshot ({len(rows)} priced markets) ===\n")
    if not rows:
        print("no rows"); return
    # sort by wedge desc
    rows.sort(key=lambda r: -r["wedge"])
    print(f"{'und':3} {'exp':7} {'type':9} {'target':>8} {'fair':>6} {'yes':>6} {'wedge':>7}  T(d)")
    for r in rows:
        print(f"{r['und']:3} {r['exp']:7} {r['type']:9} {r['target']:>8} {r['fair']:6.3f} "
              f"{r['yes_price']:6.3f} {r['wedge']:7.3f}  {r['T_days']:5.1f}")

    # aggregate stats
    wedges = [r["wedge"] for r in rows]
    longs = [r for r in rows if r["fair"] <= 0.20]
    longs_wedges = [r["wedge"] for r in longs]
    nonlongs = [r for r in rows if r["fair"] > 0.20]
    print(f"\nn={len(rows)}  mean wedge={sum(wedges)/len(wedges):+.4f}  "
          f"median={sorted(wedges)[len(wedges)//2]:+.4f}")
    print(f"longshot (fair<=0.20): n={len(longs)}  mean wedge={sum(longs_wedges)/len(longs_wedges):+.4f}" if longs else "no longshots")
    if nonlongs:
        nw = [r["wedge"] for r in nonlongs]
        print(f"non-longshot: n={len(nonlongs)}  mean wedge={sum(nw)/len(nw):+.4f}")

    # cluster structure
    clusters = defaultdict(list)
    for r in rows:
        clusters[(r["und"], r["exp"])].append(r)
    print(f"\nindependent (underlying,expiry) clusters = {len(clusters)}")

    # fee/spread/capital-charge impact (hold-to-resolution variant)
    print("\n=== net edge per $1 at risk (hold-to-resolution), longshot only ===")
    print(f"{'und':3} {'exp':7} {'target':>8} {'fair':>6} {'yes':>6} {'spread':>6} {'cap.chg':>7} {'net':>7}")
    for r in longs:
        # buy No at (1 - bid_yes) vs fair (1-fair). Selling overpriced Yes = buy No.
        # spread = ask_yes - bid_yes; buy No cost basis ~ ask_yes -> edge on No = (1-fair) - (1-bid) roughly
        bid = r["bid"] if r["bid"] is not None else r["yes_price"]
        ask = r["ask"] if r["ask"] is not None else r["yes_price"]
        # capital locked = $1 per No share; charge carry over T
        carry = 0.0321 * (r["T_days"] / 365.0)
        # No edge: we buy No, hold to resolution, collect $1 if No. Fair value of No = 1-fair.
        # entry cost for No = ask_no = (1 - bid_yes). profit if fair = (1-fair) - ask_no - carry
        no_edge = (1 - r["fair"]) - (1 - bid) - carry
        print(f"{r['und']:3} {r['exp']:7} {r['target']:>8} {r['fair']:6.3f} {r['yes_price']:6.3f} "
              f"{ask-bid:6.3f} {carry:7.4f} {no_edge:7.4f}")

    # dump JSON for report
    with open("/tmp/hyp36_snapshot.json", "w") as f:
        json.dump({"snapshot_utc": datetime.utcfromtimestamp(now).isoformat() + "Z",
                   "btc_spot": btc_spot, "eth_spot": eth_spot,
                   "n_open": len(open_mkts), "n_resolved": len(resolved),
                   "n_priced": len(rows), "n_clusters": len(clusters), "rows": rows}, f, indent=2)
    print(f"\nsaved /tmp/hyp36_snapshot.json")

if __name__ == "__main__":
    main()
