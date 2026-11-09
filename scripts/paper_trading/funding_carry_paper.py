#!/usr/bin/env python3
"""funding_carry_paper.py — HermesForge US-229: paper-forward delta-neutral
funding carry (STR-FNDCARRY).

The FIRST strategy to clear the gauntlet to a real, persistent, net-positive
number (HYP-28 ~15-21% unlevered APR, funding-true; HYP-29 ~10-12% conservative
at MAKER fills, ~$24.5M capacity). This module stands it up PAPER-FORWARD ONLY:

  * Universe: BTC / ETH / SOL only (the liquid-spot majors).
  * Entry: short-perp + long-spot ONLY when funding is sustained — rolling 24h
    mean APR >= 8% AND >= 75% of window hours positive (funding_carry
    .delta_neutral_gate / HYP-28 pre-registered gate). Exit when the gate clears.
  * MAKER-ONLY (binding): both legs post-only/maker — enforced by
    funding_carry.assert_maker_only on EVERY entry AND exit. HYP-29: taker is
    decisively net-negative, so a taker fill is IMPOSSIBLE, not discouraged.
  * NO leverage: notional = 1x capital (return on notional).
  * PnL = funding received − maker fees − basis, with the funding-vs-basis SPLIT
    preserved as separate columns (basis flagged via basis_source, NEVER folded
    into the headline net_funding — per US-179).

Paper-forward ONLY: LIVE_TRADING_ENABLED stays OFF; there is NO promotion to
Active/Live and NO registry promotion (this module is NOT discovered by
capture_signals.py frontmatter — it is standalone, run on an hourly cadence).

Usage:
    python3 funding_carry_paper.py --dry-run          # show gate status/signals
    python3 funding_carry_paper.py                    # open/close + record PnL
    python3 funding_carry_paper.py --report           # print the ledger

Ledger:
    scripts/paper_trading/funding_carry_paper.jsonl   (append-only episodes)
    scripts/paper_trading/funding_carry_paper_state.json  (open positions)
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time
from datetime import datetime, timezone

_THIS_DIR = pathlib.Path(__file__).resolve().parent          # scripts/paper_trading
_REPO = _THIS_DIR.parent.parent
for _p in (str(_THIS_DIR), str(_REPO / "scripts" / "gauntlet"),
           str(_REPO / "scripts" / "data")):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import funding_carry as fc                                # noqa: E402
import hl_funding_store                                    # noqa: E402
import hl_assetctx_store                                   # noqa: E402
import spot_basis_store                                    # noqa: E402
from fee_source import carry_round_trip_fee_bps            # noqa: E402

# ── Constants (paper-forward) ────────────────────────────────────────────────
STRATEGY_ID = "STR-FNDCARRY"
UNIVERSE = list(fc.DELTA_NEUTRAL_UNIVERSE)                 # ["BTC", "ETH", "SOL"]
EXECUTION_FORM = "delta_neutral"
EXECUTION_TYPE = fc.EXECUTION_MAKER                        # binding maker-only

# No leverage: paper notional == paper capital (1x; return is on notional).
PAPER_NOTIONAL_USD = 100_000.0

# Maker fill cost, round-trip BOTH legs (C-6 correction). The spot hedge leg
# charges the SPOT base tier (maker 4.0 bps), NOT the perp tier (maker 1.5):
#   round_trip = 2 sides x (perp maker 1.5 + spot maker 4.0) = 11.0 bps.
# (Previously 6.0 bps — the buggy model charged BOTH legs at perp 1.5.)
DELTA_NEUTRAL_MAKER_RT_BPS = carry_round_trip_fee_bps("maker")

# Spot ask/bid spread is an ASSUMED input (NO L2 spot book is held — HYP-29
# caveat). FLAGGED and never silently credited as a fill. Per-coin RT spread
# bps from HYP-29 realistic half-spread (BTC/ETH 2.5, SOL 5.0 -> RT 5/5/10).
SPOT_SPREAD_ASSUMED_RT_BPS = {"BTC": 5.0, "ETH": 5.0, "SOL": 10.0}

LEDGER_PATH = _THIS_DIR / "funding_carry_paper.jsonl"
STATE_PATH = _THIS_DIR / "funding_carry_paper_state.json"

# Episodes + signals share this JSONL (type-tagged). Split columns preserved:
#   funding_pnl (funding received), maker_fees, basis_pnl (flagged separately),
#   net_funding (HEADLINE = funding-only), net_carry (informational, incl. basis).
EPISODE_COLUMNS = [
    "trade_id", "coin", "entry_ts", "exit_ts", "exit_reason",
    "execution_form", "execution_type", "notional",
    "funding_pnl", "maker_fees", "basis_pnl", "basis_source",
    "spot_spread_assumed_rt_bps", "net_funding", "net_carry",
]


# ── Trade ID ─────────────────────────────────────────────────────────────────
def make_carry_trade_id(coin: str, entry_ts_ms: int, seq: int = 0) -> str:
    """STR-FNDCARRY-<COIN>-MMDDS (US-229). seq=0 -> 'A', 1 -> 'B', ..."""
    dt = datetime.fromtimestamp(entry_ts_ms / 1000, tz=timezone.utc)
    mmdd = f"{dt.month:02d}{dt.day:02d}"
    seq_letter = chr(ord("A") + seq) if seq < 26 else str(seq)
    return f"{STRATEGY_ID}-{coin.upper()}-{mmdd}{seq_letter}"


# ── PnL decomposition (funding − maker fees − basis, split) ──────────────────
def compute_carry_pnl(funding_rates, notional: float,
                      entry_basis_bps: float | None,
                      exit_basis_bps: float | None,
                      maker_rt_bps: float = DELTA_NEUTRAL_MAKER_RT_BPS,
                      spot_spread_rt_bps: float | None = None) -> dict:
    """Decompose a closed carry episode. `funding_rates` are the HOURLY funding
    decimal fractions received while short-perp was in position (rates > 0 pay
    shorts). Returns the split columns (funding vs basis, never folded):
      funding_pnl = notional * sum(rates)
      maker_fees  = notional * maker_rt_bps / 1e4
      basis_pnl   = (entry_basis - exit_basis)/1e4 * notional   (mark-oracle)
      net_funding = funding_pnl - maker_fees                    (HEADLINE)
      net_carry   = net_funding + (basis_pnl or 0)              (informational)
    """
    funding_pnl = float(notional) * float(sum(float(r) for r in funding_rates))
    maker_fees = float(notional) * maker_rt_bps / 1e4
    basis_pnl = None
    basis_source = "missing"
    if entry_basis_bps is not None and exit_basis_bps is not None:
        basis_pnl = (float(entry_basis_bps) - float(exit_basis_bps)) / 1e4 * notional
        basis_source = "mark_oracle"
    net_funding = funding_pnl - maker_fees
    net_carry = net_funding + (basis_pnl if basis_pnl is not None else 0.0)
    return {
        "funding_pnl": funding_pnl, "maker_fees": maker_fees,
        "basis_pnl": basis_pnl, "basis_source": basis_source,
        "spot_spread_assumed_rt_bps": spot_spread_rt_bps,
        "net_funding": net_funding, "net_carry": net_carry,
    }


# ── Signal emission (maker-only enforced on every edge) ──────────────────────
def build_signal(coin: str, ts_ms: int, side: str, notional: float,
                 basis_bps: float | None, execution_type: str = EXECUTION_TYPE,
                 seq: int = 0, **extra) -> dict:
    """Build an entry/exit signal dict with the trade ID. Asserts maker-only on
    the delta-neutral form (raises if a taker fill is ever requested)."""
    fc.assert_maker_only(execution_type, EXECUTION_FORM)
    trade_id = make_carry_trade_id(coin, ts_ms, seq)
    d = {
        "type": "signal",
        "side": side,                     # "entry" | "exit"
        "trade_id": trade_id,
        "strategy_id": STRATEGY_ID,
        "coin": coin.upper(),
        "ts": ts_ms,
        "execution_form": EXECUTION_FORM,
        "execution_type": execution_type,  # always "maker"
        "post_only": True,                 # both legs post-only
        "leverage": "none_1x",
        "notional": notional,
        "basis_bps": basis_bps,
    }
    d.update(extra)
    return d


# ── Ledger / state persistence (append-only + atomic state) ──────────────────
def _append_jsonl(path: pathlib.Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(obj, sort_keys=True) + "\n")
        f.flush()


def read_ledger() -> list[dict]:
    if not LEDGER_PATH.exists():
        return []
    out = []
    with open(LEDGER_PATH) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {}
    try:
        with open(STATE_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_PATH.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(state, f, sort_keys=True, indent=2)
        f.flush()
    tmp.replace(STATE_PATH)


def _next_seq_for_coin(coin: str, ts_ms: int) -> int:
    """Sequence letter for a same-day re-entry (dedup trade_id per MMDD)."""
    dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
    mmdd = f"{dt.month:02d}{dt.day:02d}"
    prefix = f"{STRATEGY_ID}-{coin.upper()}-{mmdd}"
    seq = -1
    for rec in read_ledger():
        tid = rec.get("trade_id", "")
        if tid.startswith(prefix) and len(tid) > len(prefix) and tid[-1].isalpha():
            seq = max(seq, ord(tid[-1]) - ord("A"))
    return max(0, seq + 1)


# ── Live sweep (read stores, gate, open/close, record) ───────────────────────
def _now_ms() -> int:
    return int(time.time() * 1000)


def read_funding(coin: str):
    return hl_funding_store.read_funding(coin)


def read_basis(coin: str):
    """Latest mark-oracle basis (mark_px, oracle_px, basis_bps) or None."""
    df = hl_assetctx_store.read_basis(coin)
    if df.empty:
        return None
    last = df.iloc[-1]
    return {"mark_px": float(last["mark_px"]), "oracle_px": float(last["oracle_px"]),
            "basis_bps": (float(last["basis_bps"])
                          if last["basis_bps"] is not None and
                          float(last["basis_bps"]) == float(last["basis_bps"])
                          else None)}


def sweep(dry_run: bool = False) -> dict:
    """One hourly pass: gate each major, open/close the delta-neutral carry,
    record PnL (funding − maker fees − basis, split). Returns a summary dict."""
    state = load_state()
    summary = {"opened": [], "closed": [], "held": [], "gated": [],
               "skipped": []}
    for coin in UNIVERSE:
        funding = read_funding(coin)
        gate = fc.delta_neutral_gate(funding)
        basis = read_basis(coin)

        if not gate["gated"] and basis is not None:
            # Not gated, but report current status for visibility.
            summary["gated"].append({"coin": coin, "gated": False,
                                     "mean_apr": gate["mean_apr"],
                                     "positive_fraction": gate["positive_fraction"]})

        open_pos = None
        if coin in state.get("open", {}):
            open_pos = state["open"][coin]

        if gate["gated"]:
            if open_pos is not None:
                # Still gated -> hold (already open).
                summary["held"].append({"coin": coin, "trade_id": open_pos["trade_id"],
                                        "mean_apr": gate["mean_apr"]})
                continue
            # OPEN (maker-only, no leverage).
            ts = _now_ms()
            seq = _next_seq_for_coin(coin, ts)
            notional = PAPER_NOTIONAL_USD
            entry_basis = basis["basis_bps"] if basis else None
            signal = build_signal(coin, ts, "entry", notional, entry_basis, seq=seq,
                                  gate_mean_apr=round(gate["mean_apr"], 4),
                                  gate_positive_fraction=round(gate["positive_fraction"], 4))
            if not dry_run:
                state.setdefault("open", {})[coin] = {
                    "trade_id": signal["trade_id"], "entry_ts": ts,
                    "entry_basis_bps": entry_basis, "notional": notional,
                }
                save_state(state)
                _append_jsonl(LEDGER_PATH, signal)
            summary["opened"].append(signal)
            continue

        # gate cleared ...
        if open_pos is None:
            # No position and not gated -> nothing to do.
            continue

        # CLOSE (gate cleared): maker-only exit + PnL decomposition.
        ts = _now_ms()
        exit_reason = "gate_cleared"
        exit_basis = basis["basis_bps"] if basis else None
        notional = float(open_pos["notional"])
        entry_basis = open_pos.get("entry_basis_bps")

        # Funding received over the held window: hourly rates strictly after
        # entry_ts up to the latest settlement (short receives when rate > 0).
        rates = []
        if funding is not None and not funding.empty:
            held = funding[(funding["time"].astype("int64") > int(open_pos["entry_ts"]))]
            rates = [float(r) for r in held["funding_rate"]]

        pnl = compute_carry_pnl(
            rates, notional, entry_basis, exit_basis,
            spot_spread_rt_bps=SPOT_SPREAD_ASSUMED_RT_BPS.get(coin))

        signal = build_signal(coin, ts, "exit", notional, exit_basis,
                              exit_reason=exit_reason,
                              **{k: pnl[k] for k in
                                 ("funding_pnl", "maker_fees", "basis_pnl",
                                  "basis_source", "spot_spread_assumed_rt_bps",
                                  "net_funding", "net_carry")})
        episode = {
            "type": "episode",
            "trade_id": open_pos["trade_id"], "coin": coin.upper(),
            "entry_ts": open_pos["entry_ts"], "exit_ts": ts,
            "exit_reason": exit_reason, "execution_form": EXECUTION_FORM,
            "execution_type": EXECUTION_TYPE, "notional": notional,
        }
        for k in EPISODE_COLUMNS:
            if k in ("trade_id", "coin", "entry_ts", "exit_ts", "exit_reason",
                     "execution_form", "execution_type", "notional"):
                continue
            episode[k] = pnl.get(k)
        episode["basis_flagged"] = True  # NEVER folded into headline (US-179)

        if not dry_run:
            del state["open"][coin]
            if not state["open"]:
                state.pop("open", None)
            save_state(state)
            _append_jsonl(LEDGER_PATH, signal)
            _append_jsonl(LEDGER_PATH, episode)
        summary["closed"].append({"trade_id": open_pos["trade_id"], "coin": coin,
                                  "net_funding": pnl["net_funding"],
                                  "basis_pnl": pnl["basis_pnl"],
                                  "exit_reason": exit_reason})
    return summary


def report() -> str:
    """Human-readable ledger dump (funding vs basis split explicit)."""
    recs = [r for r in read_ledger() if r.get("type") == "episode"]
    lines = ["# STR-FNDCARRY paper-forward ledger", ""]
    if not recs:
        lines.append("(no closed episodes yet)")
    for r in recs:
        lines.append(
            f"{r['trade_id']}: {r['coin']} funding={r['funding_pnl']:+.2f} "
            f"maker_fees={r['maker_fees']:.2f} basis={r['basis_pnl']:+g} "
            f"(source={r['basis_source']}) -> net_funding(HEADLINE)="
            f"{r['net_funding']:+.2f}, net_carry={r['net_carry']:+.2f}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()

    if args.report:
        print(report())
        return 0

    summary = sweep(dry_run=args.dry_run)
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())