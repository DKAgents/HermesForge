"""backtest_vrp_stub.py — HermesForge US-181 backtest harness STUB.

BLOCKED-ON-DATA (binding, spec §5.4). The IV store has ~30d of DVOL + a single
ATM-IV snapshot. A daily-entry short-vol backtest needs MULTIPLE vol regimes and
a meaningful tail sample to (a) derive VOV_THRESHOLD (§2.2) and (b) meet G3
(n >= 10). Running it on 30d would FABRICATE a result — this harness therefore
REFUSES to execute until >= MIN_WINDOW_DAYS (6 months) of settled paper-forward
records exist in vrp_paper_store.

The harness is fully implemented so it "becomes real" the moment the data
window closes: read the accumulated paper store, derive the threshold, split
timed-vs-unconditional, score the §5.1 dominance test, and gate via G3. It does
NOT promote anything (no LIVE/WATCH registry write) even when un-blocked — that
decision belongs to the swarm/orchestrator through g3_gate.promote_strategy.

Usage:
    python3 backtest_vrp_stub.py           # prints BLOCKED-ON-DATA today
    python3 backtest_vrp_stub.py --force   # FORCE-run (diagnostic only; the
                                           # result is explicitly NOT validation)
"""

from __future__ import annotations

import argparse
import math
import pathlib
import sys

_THIS_DIR = pathlib.Path(__file__).resolve().parent          # scripts/gauntlet
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))
_DATA_DIR = _THIS_DIR.parent / "data"                        # scripts/data
if str(_DATA_DIR) not in sys.path:
    sys.path.insert(0, str(_DATA_DIR))

import vol_vrp as vrp          # noqa: E402
import vrp_paper_store as ps   # noqa: E402


# ── Dominance + G3 score (implemented, exercised only when un-blocked) ──────
def _pf(rs) -> float:
    gains = sum(r for r in rs if r > 0)
    losses = abs(sum(r for r in rs if r < 0))
    return gains / losses if losses > 0 else (float("inf") if gains > 0 else 0.0)


def _set_stats(rs: list[float]) -> dict:
    """Per-set stats (§5.1): n, mean net_pnl, mean R, Sharpe, PF, maxDD, tail."""
    if not rs:
        return {"n": 0, "mean_net_pnl": 0.0, "mean_r": 0.0, "sharpe": 0.0,
                "pf": 0.0, "max_dd": 0.0, "worst5_skew": 0.0}
    n = len(rs)
    mean = sum(rs) / n
    std = math.sqrt(sum((r - mean) ** 2 for r in rs) / n) if n > 1 else 0.0
    sharpe = mean / std * math.sqrt(365) if std > 0 else 0.0
    worst5 = sorted(rs)[: max(1, n // 20)]
    skew = sum(worst5) / len(worst5)
    return {"n": n, "mean_net_pnl": mean, "mean_r": mean,
            "sharpe": sharpe, "pf": _pf(rs), "max_dd": min(rs),
            "worst5_skew": skew}


def dominance_report(records: list[dict], threshold: float | None) -> dict:
    """§5.1 timed-vs-unconditional dominance test over settled paper records.

    records: [{vov_level, net_pnl, risk_usd}, ...] (one per settled position).
    UNCONDITIONAL = every record; TIMED = only those entered when
    vov_level < threshold. Acceptance: TIMED Sharpe ~2–3x unconditional AND
    TIMED pessimistic PF > 1.0 while unconditional's is < 1.0.
    """
    if threshold is None:
        return {"blocked": True,
                "reason": "VOV_THRESHOLD not yet derived (derive first)"}
    usable = [r for r in records if r.get("vov_level") is not None
              and r.get("net_pnl") is not None]
    uncond_r = [r["net_pnl"] / r["risk_usd"] if r.get("risk_usd") else 0.0
                for r in usable]
    timed_r = [r["net_pnl"] / r["risk_usd"] if r.get("risk_usd") else 0.0
               for r in usable if r["vov_level"] < threshold]
    return {"blocked": False,
            "unconditional": _set_stats(uncond_r),
            "timed": _set_stats(timed_r),
            "threshold": threshold}


def vrp_g3_record(timed_records: list[dict]) -> dict:
    """US-174 G3 SEMANTICS on the timed set (mirrors funding_carry.carry_g3_record).

    Cost legs (fee-basis explicit): the record net_pnl is ALREADY net of Deribit
    option cost (§5.2); the pessimistic leg adds the g3_gate bar-level drag as a
    conservative FLOOR (spec F13 double-count, accepted). Returns {n,
    optimistic_mean_r, realistic_mean_r, pessimistic_pf, passed, reasons}.
    """
    if not timed_records:
        return {"n": 0, "optimistic_mean_r": 0.0, "realistic_mean_r": 0.0,
                "pessimistic_pf": 0.0, "passed": False, "reasons": ["no trades"]}
    opt_rs = [r["net_pnl"] / r["risk_usd"] if r.get("risk_usd") else 0.0
              for r in timed_records]
    opt_mean = sum(opt_rs) / len(opt_rs)
    # Conservative pessimistic floor: deduct one extra taker round-trip in R.
    from g3_gate import MIN_TRADES  # reuse exact threshold
    pess_rs = [o - 0.006 for o in opt_rs]   # ~6 bps/R conservative floor (F13)
    pess_pf = _pf(pess_rs)

    n = len(opt_rs)
    reasons = []
    if n < MIN_TRADES:
        reasons.append(f"INSUFFICIENT DATA: n={n} < {MIN_TRADES}")
    if opt_mean <= 0:
        reasons.append(f"realistic mean R = {opt_mean:.4f} <= 0")
    if pess_pf <= 1.0:
        reasons.append(f"pessimistic PF = {pess_pf:.4f} <= 1.0")
    return {"n": n, "optimistic_mean_r": round(opt_mean, 4),
            "realistic_mean_r": round(opt_mean, 4),
            "pessimistic_pf": round(pess_pf, 4),
            "passed": len(reasons) == 0, "reasons": reasons}


def _collect(conn) -> list[dict]:
    """Join settled positions to their morning vol-of-vol level."""
    snap = ps.read_snapshots(conn).set_index(["currency", "day"])
    pos = ps.read_positions(conn)
    records = []
    for _, p in pos.iterrows():
        if p.get("status") != "closed" or p.get("net_pnl") is None:
            continue
        day = _day_of(int(p["entry_ts"]))
        if (p["currency"], day) not in snap.index:
            continue
        s = snap.loc[(p["currency"], day)]
        records.append({"vov_level": s["vol_of_vol"] if s["vol_of_vol"] is not None
                        and math.isfinite(s["vol_of_vol"]) else None,
                        "net_pnl": float(p["net_pnl"]),
                        "risk_usd": float(p["risk_usd"])})
    return records


def _day_of(ms: int) -> str:
    from datetime import datetime, timezone
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true",
                    help="RUN anyway (diagnostic; result is NOT validation)")
    args = ap.parse_args()

    conn = ps.open_store()
    try:
        snaps = ps.read_snapshots(conn)
        n_days = 0 if snaps.empty else snaps["day"].nunique()
        print(f"US-181 short-vol backtest — status: HYPOTHESIS / PAPER-FORWARD")
        print(f"morning snapshots accumulated: {n_days} "
              f"(min window = {vrp.MIN_WINDOW_DAYS} days)")

        if n_days < vrp.MIN_WINDOW_DAYS and not args.force:
            print()
            print("BLOCKED-ON-DATA: the store has fewer than "
                  f"{vrp.MIN_WINDOW_DAYS} days of morning snapshots. Running a "
                  "short-vol backtest on this window would FABRICATE a result — "
                  "it is NOT executed. Continue paper-forward accumulation; "
                  "re-run once >= 6–12 months of DVOL + ATM-IV + underlying "
                  "bars spanning a full vol cycle are present (§5.4).")
            return 0

        # FORCE / un-blocked path (diagnostic only).
        records = _collect(conn)
        threshold = vrp.derive_vov_threshold(
            [{"vov_level": r["vov_level"], "forward_net_pnl": r["net_pnl"]}
             for r in records])
        if threshold["blocked"]:
            print(f"threshold derivation blocked: {threshold['reason']}")
            return 0
        rep = dominance_report(records, threshold["threshold"])
        g3 = vrp_g3_record(rep["timed"] if not rep["blocked"] else [])
        print(f"derived VOV_THRESHOLD = {threshold['threshold']:.4f}")
        print(f"unconditional: {rep['unconditional']}")
        print(f"timed:          {rep['timed']}")
        print(f"G3 (timed):     {g3}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())