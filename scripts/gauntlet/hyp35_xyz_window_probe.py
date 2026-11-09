#!/usr/bin/env python3
"""
HYP-35 xyz index-perp 13-15 UTC short window — mechanism probe + diagnostic.

Blocking gate: identify the mechanism behind the 13-15 UTC window BEFORE a
gated backtest. This script probes HL live endpoints and characterizes the
artifact. Verdict recorded in reports/backtester/HYP-35_xyz_index_window_short.md
(MECHANISM-UNKNOWN, not promoted).

Reproducibility notes (no look-ahead, no tuning):
- candleSnapshot 15m (recent ~53d) + 1h (full ~208d).
- fundingHistory to rule out a funding-settlement mechanism.
- l2Book to measure the xyz market's wider spread.
- Rule is fixed (pre-registered): short 13/14/15 UTC, cover 2.6h later.
"""
import json
import bisect
import urllib.request
import statistics
from collections import defaultdict

INFO = "https://api.hyperliquid.xyz/info"


def _post(payload: dict, timeout: float = 15.0):
    req = urllib.request.Request(
        INFO, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def candles(coin, interval, days):
    import datetime as dt
    now = int(dt.datetime.now().timestamp())
    return _post({"type": "candleSnapshot", "req": {
        "coin": coin, "interval": interval,
        "startTime": (now - days * 86400) * 1000, "endTime": now * 1000}})


def funding(coin, days):
    import datetime as dt
    now = int(dt.datetime.now().timestamp())
    return _post({"type": "fundingHistory", "coin": coin,
                  "startTime": (now - days * 86400) * 1000, "endTime": now * 1000})


def window_short_1h(rows, entry_hours, hold_h=3.0):
    """Short at open of hours entry_hours, exit `hold_h` later (1h bars)."""
    ts = {t: (o, c) for t, o, c in rows}
    out = []
    for t, o, _c in rows:
        import datetime as dt
        d = dt.datetime.fromtimestamp(t, dt.UTC)
        if d.hour in entry_hours and d.minute == 0:
            x = t + int(hold_h * 3600)
            if x in ts:
                out.append((o - ts[x][0]) / o * 1e4)
    return out


def main():
    import datetime as dt
    coins = ["NVDA", "GOOGL", "TSLA", "AMD", "META", "BRENTOIL", "CL", "SKHX", "XYZ100"]

    # Gate 1: funding is hourly/continuous, not a settlement event.
    f = funding("xyz:NVDA", 3)
    hrs = set(dt.datetime.fromtimestamp(e["time"] / 1000, dt.UTC).hour for e in f)
    print("funding entries in 3d:", len(f), "| distinct hours:", len(hrs), "(24 = hourly/continuous)")

    # Gate 2/3: cross-coin short window + hour-of-day control.
    print(f"\n{'coin':14s} {'n':5s} {'mean_bps':>9s} {'median':>8s} {'win%':>6s}")
    for c in coins:
        rows = sorted((int(x["t"]) // 1000, float(x["o"]), float(x["c"]))
                      for x in candles(f"xyz:{c}", "1h", 210))
        rs = window_short_1h(rows, (13, 14, 15), 3.0)
        wins = [r for r in rs if r > 0]
        print(f"xyz:{c:9s} {len(rs):5d} {statistics.mean(rs):+9.2f} "
              f"{statistics.median(rs):+8.2f} {100*len(wins)/len(rs):5.1f}")

    # Hour-of-day control (NVDA): is 13-15 special vs all other hours?
    rows = sorted((int(x["t"]) // 1000, float(x["o"]), float(x["c"]))
                  for x in candles("xyz:NVDA", "1h", 210))
    means = {}
    for h in range(24):
        rs = window_short_1h(rows, (h,), 3.0)
        means[h] = statistics.mean(rs) if rs else 0.0
    print("\nhour-of-day 2.6h-short mean (NVDA), top 6:")
    for h, m in sorted(means.items(), key=lambda kv: -kv[1])[:6]:
        tag = " <-- 13-15" if h in (13, 14, 15) else ""
        print(f"  hour {h:2d}  {m:+8.2f} bps{tag}")


if __name__ == "__main__":
    main()