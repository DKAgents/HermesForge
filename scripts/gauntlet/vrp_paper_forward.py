"""vrp_paper_forward.py — HermesForge US-181 daily paper-forward accumulation.

Runs the short-vol / VRP strategy in PAPER-FORWARD mode (spec §5.4 fallback 1,
§6.3 item 6): every UTC day it reads the accumulating DVOL / ATM-IV / 5m-bar
stores, emits ONE morning snapshot per currency (BTC + ETH), registers a PAPER
short straddle, and — for positions already open — applies the MANDATORY
vol-spike stop (§3.1) or settles the held-to-expiry payoff (§1.2).

This is NOT a promotion path: it writes ONLY to vrp_paper_store (never
trades.csv / the journal / the strategy registry), carries no G3 claim, and
labels every row ``paper-forward-hypothesis``. There is no LIVE/WATCH entry and
no "proven" label anywhere. The strategy stays a HYPOTHESIS until the minimum
6–12 month data window is accumulated (US-181 §5.4) and the backtest stub is
un-blocked.

Import direction (driver): vrp_paper_forward -> vrp_paper_store + iv_store +
hl_bar_store + vol_of_vol_gate + vol_vrp.

Usage:
    python3 vrp_paper_forward.py [--dry-run] [--capital 1000000.0]
                                 [--target-dte 7.0] [--no-settle]
"""

from __future__ import annotations

import argparse
import pathlib
import sys
import time
from datetime import datetime, timezone

_THIS_DIR = pathlib.Path(__file__).resolve().parent          # scripts/gauntlet
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))
_DATA_DIR = _THIS_DIR.parent / "data"                        # scripts/data
if str(_DATA_DIR) not in sys.path:
    sys.path.insert(0, str(_DATA_DIR))

import vol_vrp as vrp          # noqa: E402
import vol_of_vol_gate as vog  # noqa: E402
import iv_store                # noqa: E402
import hl_bar_store            # noqa: E402
import vrp_paper_store as ps   # noqa: E402

CURRENCIES = ("BTC", "ETH")
TARGET_DTE_DAYS = 7.0          # weekly straddle horizon (paper assumption)
PAPER_CAPITAL = 1_000_000.0    # PAPER sizing capital (no real money)


def _utc_day(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d")


def _morning_ts(now_ms: int) -> int:
    """UTC day boundary (00:00 UTC) of `now_ms` — the morning anchor (F9)."""
    return (now_ms // 86_400_000) * 86_400_000


def _latest_dvol(currency: str) -> dict | None:
    df = iv_store.read_dvol(currency)
    if df is None or df.empty:
        return None
    last = df.iloc[-1]
    return {"ts": int(last["ts"]), "close": float(last["close"])}


def _latest_atm(currency: str, target_dte: float) -> dict | None:
    """Select the ATM-IV row (latest snapshot) nearest `target_dte` days."""
    df = iv_store.read_crypto_atm_iv(currency)
    if df is None or df.empty:
        return None
    df = df.dropna(subset=["atm_iv", "spot", "dte"])
    if df.empty:
        return None
    lat = df[df["dte"] > 0.0]           # skip already-expired rows
    if lat.empty:
        return None
    row = lat.iloc[(lat["dte"] - target_dte).abs().argsort().iloc[0]]
    return {"ts": int(row["ts"]), "atm_iv": float(row["atm_iv"]),
            "spot": float(row["spot"]), "dte": float(row["dte"]),
            "expiry": int(row["expiry"])}


def _realized_vol(currency: str) -> float:
    try:
        bars = hl_bar_store.read_bars(currency, "5m")
    except Exception:
        return 0.0
    if bars is None or bars.empty:
        return 0.0
    return vrp.realized_vol_5m(bars["close"].tolist())


def _build_morning(currency: str, now_ms: int, target_dte: float) -> dict | None:
    dvol = _latest_dvol(currency)
    atm = _latest_atm(currency, target_dte)
    if dvol is None or atm is None:
        return None
    vov = vog.vol_of_vol_level(currency, window_hours=vrp.VOV_WINDOW_HOURS)
    rv = _realized_vol(currency)
    sigma = atm["atm_iv"] / 100.0
    T = atm["dte"] / 365.0
    strike = atm["spot"]  # ATM: K ~= S0 (per spec §1.1)
    premium = vrp.straddle_premium(atm["spot"], strike, T, sigma)

    pred = vrp.enter_short_vol(vov, atm["atm_iv"], rv or None, morning=True,
                               vov_threshold=None)
    return {
        "currency": currency, "snap_ts": _morning_ts(now_ms),
        "day": _utc_day(now_ms),
        "dvol_close": dvol["close"], "vol_of_vol": vov,
        "atm_iv": atm["atm_iv"], "spot": atm["spot"], "dte": atm["dte"],
        "expiry": atm["expiry"], "realized_vol": rv,
        "straddle_premium": premium, "strike": strike, "sigma": sigma, "T": T,
        "vrp_rich": pred["vrp_rich"], "morning": True,
        "vov_threshold": None, "vov_calm": None, "enter": pred["enter"],
        "predicate": pred,
    }


def _process_currency(conn, currency: str, now_ms: int, target_dte: float,
                      capital: float, dry_run: bool, settle: bool) -> list[str]:
    lines: list[str] = []
    m = _build_morning(currency, now_ms, target_dte)
    if m is None:
        lines.append(f"  {currency}: no DVOL/ATM-IV yet — skipping")
        return lines

    # Sizing (paper): 1R = 1% capital, no leverage.
    sz = vrp.size_straddle(capital, m["spot"], m["straddle_premium"])

    if dry_run:
        pred = m["predicate"]
        lines.append(
            f"  {currency} [DRY-RUN] day={m['day']} spot={m['spot']:.2f} "
            f"atm_iv={m['atm_iv']:.2f}% dv(dvol)={m['vol_of_vol']:.4f} "
            f"RV={m['realized_vol']:.4f} premium={m['straddle_premium']:.4f}")
        lines.append(
            f"    VOV_CALM={pred['vov_calm']} VRP_RICH={pred['vrp_rich']} "
            f"MORNING={pred['morning']} ENTER={pred['enter']}")
        lines.append(
            f"    size: notional={sz['notional']:.2f} contracts="
            f"{sz['contracts']:.6f} risk_usd={sz['risk_usd']:.2f} "
            f"capped={sz['size_capped']} ({sz['cap_reason']})")
        lines.append(f"    ({'; '.join(pred['reasons'])})")
        return lines

    ps.upsert_snapshot(conn, m)

    # Register the paper short straddle (idempotent on (currency, entry_ts, expiry)).
    pos = {
        "currency": currency, "entry_ts": m["snap_ts"], "expiry": m["expiry"],
        "strike": m["strike"], "premium_collected": m["straddle_premium"],
        "contracts": sz["contracts"], "notional": sz["notional"],
        "margin_deployed": sz["margin_deployed"], "risk_usd": sz["risk_usd"],
        "size_capped": sz["size_capped"], "cap_reason": sz["cap_reason"],
        "entry_dvol": m["dvol_close"], "entry_atm_iv": m["atm_iv"],
    }
    new_pos = ps.open_position(conn, pos)
    lines.append(
        f"  {currency}: day={m['day']} spot={m['spot']:.2f} atm_iv={m['atm_iv']:.2f}% "
        f"premium={m['straddle_premium']:.4f} risk_usd={sz['risk_usd']:.2f} "
        f"({'new' if new_pos else 'already open'}) "
        f"[entered={int(m['enter'])} capped={sz['size_capped']}]")

    if settle:
        _settle_open(conn, currency, now_ms, lines)
    return lines


def _settle_open(conn, currency: str, now_ms: int, lines: list[str]) -> None:
    """Close open paper positions via vol-spike stop (§3.1) or expiry (§1.2)."""
    open_df = ps.read_open_positions(conn, currency)
    if open_df.empty:
        return
    dvol = _latest_dvol(currency)
    atm = _latest_atm(currency, TARGET_DTE_DAYS)
    cur_dvol = dvol["close"] if dvol else None
    cur_iv = atm["atm_iv"] if atm else None

    for _, p in open_df.iterrows():
        entry_ts = int(p["entry_ts"])
        expiry = int(p["expiry"])
        sp = vrp.vol_spike(cur_dvol, p.get("entry_dvol"), cur_iv, p.get("entry_atm_iv"))
        if sp["triggered"]:
            # Buy-to-cover at the current mark (mark-to-market, §1.2).
            strike = float(p["strike"])
            # Approximate remaining DTE / IV from the latest snapshot.
            T1 = atm["dte"] / 365.0 if atm else 0.0
            sigma1 = atm["atm_iv"] / 100.0 if atm else p.get("entry_atm_iv", 0) / 100.0
            cost = vrp.option_execution_cost(float(p["strike"]), float(p["contracts"]))
            mtm = vrp.close_straddle_mtm(strike, strike, T1, sigma1,
                                         float(p["premium_collected"]), cost)
            net_r = mtm["mtm_pnl"] / float(p["risk_usd"]) if float(p["risk_usd"]) > 0 else 0.0
            ps.close_position(conn, currency, entry_ts, expiry, now_ms, "vol_spike",
                              0.0, mtm["mtm_pnl"], cost, mtm["mtm_pnl"], net_r)
            lines.append(f"    vol-spike STOP {currency}: legs={sp['legs']} "
                         f"dvol_ratio={sp['dvol_ratio']} iv_ratio={sp['iv_ratio']} "
                         f"net_r={net_r:.4f}")
        elif now_ms >= expiry:
            # Held to expiry: S_T = last 5m close <= expiry; payoff |S_T - K|.
            S_T = _underlying_at(currency, expiry)
            cost = vrp.option_execution_cost(float(p["strike"]), float(p["contracts"]))
            pnl = vrp.held_to_expiry_pnl(float(p["premium_collected"]), S_T,
                                         float(p["strike"]), cost)
            net_r = pnl["net_pnl"] / float(p["risk_usd"]) if float(p["risk_usd"]) > 0 else 0.0
            ps.close_position(conn, currency, entry_ts, expiry, now_ms, "expiry",
                              pnl["realized_payoff"], pnl["gross_pnl"], cost,
                              pnl["net_pnl"], net_r)
            lines.append(f"    expiry SETTLE {currency}: S_T={S_T:.2f} "
                         f"gross={pnl['gross_pnl']:.4f} net={pnl['net_pnl']:.4f} "
                         f"net_r={net_r:.4f}")


def _underlying_at(currency: str, expiry_ms: int) -> float:
    try:
        bars = hl_bar_store.read_bars(currency, "5m", end_ts=expiry_ms)
    except Exception:
        return 0.0
    if bars is None or bars.empty:
        return 0.0
    return float(bars["close"].iloc[-1])


def main() -> int:
    ap = argparse.ArgumentParser(description="US-181 short-vol paper-forward runner")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--capital", type=float, default=PAPER_CAPITAL)
    ap.add_argument("--target-dte", type=float, default=TARGET_DTE_DAYS)
    ap.add_argument("--no-settle", action="store_true",
                    help="skip settling open positions (snapshot/register only)")
    args = ap.parse_args()

    now_ms = int(time.time() * 1000)
    mode = "DRY-RUN" if args.dry_run else "ACCUMULATE"
    print(f"[{mode}] US-181 short-vol paper-forward "
          f"(hypothesis, NOT promoted) "
          f"{datetime.now(timezone.utc).isoformat()}")

    conn = ps.open_store() if not args.dry_run else None
    try:
        for currency in CURRENCIES:
            try:
                lines = _process_currency(conn, currency, now_ms, args.target_dte,
                                          args.capital, args.dry_run,
                                          not args.no_settle)
                for ln in lines:
                    print(ln)
            except Exception as e:  # noqa: BLE001 — one coin must not kill the run
                print(f"  {currency}: FAILED {e}")
    finally:
        if conn is not None:
            conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())