"""funding_carry.py — HermesForge US-185: funding / basis carry strategy.

Reconstituted for the FULL Hyperliquid perp universe (long AND short):
  * funding > 0  -> SHORT perp receives funding  ('directional_short', or
                    'delta_neutral' long-spot/short-perp where a liquid HL spot
                    leg exists — GATED off by default, see §F2 below).
  * funding < 0  -> LONG  perp receives funding   ('directional_long'; no spot
                    short needed).
  * funding ~ 0  -> no carry                      ('skip').

The directional forms carry FULL spot-level (directional) risk on top of the
funding carry, so each gets its own risk unit — a 2% MANDATORY hard stop
(DIRECTIONAL_STOP_BPS) — and its own entry hurdle (DIRECTIONAL_LAMBDA × realized
vol). This turns a "blank-check short" into a gated trade.

Honest decomposition (US-179 validation §6 / US-185 §2):
  * HEADLINE edge = funding_pnl - execution_cost (funding-only). The basis
    component is reported as a SEPARATE, flagged column and is NEVER folded
    into the headline R.
  * The basis is sourced from the REAL mark-oracle spread (assetCtxs markPx/
    oraclePx, via hl_assetctx_store.read_basis), NOT the compressed
    fundingHistory `premium`. When no real mark-oracle history exists yet,
    basis_pnl = None and basis_source = 'proxy' (flagged, not silently credited,
    not silently dropped).

Import direction is one-way and acyclic (mirrors US-177 / US-185 §0):
  funding_carry.py -> hl_funding_store.py + hl_assetctx_store.py
                      + fee_source + g3_gate

CANONICAL UNIT (binding): annualized APR, converted to/from the endpoint's
HOURLY fraction.
"""

from __future__ import annotations

import math
import pathlib
import sys

import numpy as np
import pandas as pd

# g3_gate lives in scripts/gauntlet; make it importable regardless of caller
# sys.path (same convention as the hostile*/pnl_accounting modules).
_THIS_DIR = pathlib.Path(__file__).resolve().parent          # scripts/gauntlet
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

from g3_gate import MIN_TRADES, EDGE_DECAY_FLOOR  # noqa: E402  (reuse exact thresholds)

# ── Unit normalization (canonical APR) ──────────────────────────────────────
HOURS_PER_YEAR = 8760


def hourly_to_apr(rate_hourly: float) -> float:
    """Convert an HOURLY funding fraction to annualized APR (rate * 8760)."""
    return rate_hourly * HOURS_PER_YEAR


def apr_to_hourly(apr: float) -> float:
    """Convert annualized APR to the HOURLY funding fraction (apr / 8760)."""
    return apr / HOURS_PER_YEAR


# ── Signal thresholds (§1.3) ────────────────────────────────────────────────
FUNDING_WINDOW_HOURS = 24       # rolling window length (hourly obs)  [tunable]
FUNDING_SUSTAIN_FLOOR_APR = 0.08    # 8%/yr  = hourly 9.132e-6   [tunable]
FUNDING_ELEVATED_APR = 0.18         # 18%/yr = hourly 2.055e-5  (boost tier)
FUNDING_POSITIVE_FRACTION = 0.75    # >= 18 of 24 trailing hours positive
# FLAG + RESOLUTION: the spec did not give an explicit constant for the
# "extreme-flip-risk" warning band (~55-110%/yr). Resolved to the band's floor.
FUNDING_EXTREME_APR = 0.55          # 55%/yr  -> extreme-flip-risk WARNING [tunable]


def funding_window_signal(series: pd.DataFrame, sign: int = 1) -> dict:
    """Sustained-funding entry signal over the trailing W HOURLY observations.

    series: DataFrame[time, funding_rate, premium] ascending (>= W rows).
    sign: +1 -> sustained POSITIVE funding (short-perp receives funding);
          -1 -> sustained NEGATIVE funding (long-perp receives funding).
    Every threshold is evaluated in the RECEIVING direction (sign × rate), so
    the two branches are exact mirrors.

    Returns {sustained, elevated, extreme, mean_apr (signed), mean_mag_apr,
             current_apr, positive_fraction, cost_clears, reasons}.

    ENTRY (all four must hold, in the receiving direction):
      S1  mean(sign*funding over W) >= apr_to_hourly(FUNDING_SUSTAIN_FLOOR_APR)
      S2  count(sign*funding > 0 in window) >= FUNDING_POSITIVE_FRACTION * W
      S3  current sign*funding > 0
      S4  cost_clears(|mean_apr|)   [conservative taker default]
    """
    reasons: list[str] = []
    w = FUNDING_WINDOW_HOURS
    if series is None or len(series) < w:
        return {
            "sustained": False, "elevated": False, "extreme": False,
            "mean_apr": 0.0, "mean_mag_apr": 0.0, "current_apr": 0.0,
            "positive_fraction": 0.0, "cost_clears": False,
            "reasons": [f"insufficient history: need >= {w} hourly rows"],
        }

    window = series["funding_rate"].astype(float).iloc[-w:]
    current = float(window.iloc[-1])
    mean_hourly = float(window.mean())
    mean_apr = hourly_to_apr(mean_hourly)                 # signed
    current_apr = hourly_to_apr(current)
    receiving = window * sign                             # >0 = receiving dir
    mean_mag_apr = hourly_to_apr(float(receiving.mean()))  # magnitude (>=0 in-dir)
    n_pos = int((receiving > 0).sum())
    positive_fraction = n_pos / w

    s1 = mean_mag_apr >= FUNDING_SUSTAIN_FLOOR_APR
    s2 = positive_fraction >= FUNDING_POSITIVE_FRACTION
    s3 = current * sign > 0.0
    s4 = cost_clears(mean_mag_apr)

    if not s1:
        reasons.append(f"S1 mean |APR| {mean_mag_apr:.4f} < {FUNDING_SUSTAIN_FLOOR_APR:.2f}")
    if not s2:
        reasons.append(f"S2 positive fraction {positive_fraction:.2f} < {FUNDING_POSITIVE_FRACTION:.2f}")
    if not s3:
        reasons.append("S3 current funding not in receiving direction")
    if not s4:
        reasons.append(f"S4 carry does not clear cost at {mean_mag_apr:.4f} APR")

    return {
        "sustained": s1 and s2 and s3 and s4,
        "elevated": mean_mag_apr >= FUNDING_ELEVATED_APR,
        "extreme": mean_mag_apr >= FUNDING_EXTREME_APR,
        "mean_apr": mean_apr,          # signed (negative for the long branch)
        "mean_mag_apr": mean_mag_apr,  # receiving-direction magnitude
        "current_apr": current_apr,
        "positive_fraction": positive_fraction,
        "cost_clears": s4,
        "reasons": reasons,
    }


# ── Cost gate (§1.6.3) ──────────────────────────────────────────────────────
MIN_HOLD_HOURS = 168               # 1 week minimum amortization hold   [tunable]
CARRY_ROUND_TRIP_BPS = 24.0        # conservative two-leg taker (2 x 12 bps)
MAKER_ROUND_TRIP_BPS = 12.0        # both legs limit/maker (US-180 path)


def cost_clears(mean_apr: float, cost_bps: float = CARRY_ROUND_TRIP_BPS,
                hold_hours: float = MIN_HOLD_HOURS) -> bool:
    """mean_apr * (hold_hours/8760) >= cost_bps/1e4 — the carry must clear its
    two-leg friction over the minimum hold. Break-even APR (taker 24bps, 1wk) =
    12.5%/yr; (maker 12bps, 1wk) = 6.3%/yr."""
    return mean_apr * (hold_hours / HOURS_PER_YEAR) >= cost_bps / 1e4


# ── Delta-neutral sustained-funding gate (US-229; HYP-28/29 pre-registered) ──
def delta_neutral_gate(series: pd.DataFrame,
                       window: int = FUNDING_WINDOW_HOURS) -> dict:
    """EXACT HYP-28/29 delta-neutral entry gate (short-perp / long-spot).

    Entry requires BOTH, over the trailing `window` HOURLY observations:
      G1  rolling mean funding APR >= FUNDING_SUSTAIN_FLOOR_APR (8%/yr)
      G2  >= FUNDING_POSITIVE_FRACTION (75%) of window hours strictly positive

    This is the PRE-REGISTERED HYP-28 gate (mean APR >= 8% AND >= 75% hours
    positive) — deliberately does NOT apply the directional-form S3/S4 hurdles
    (current-sign and cost_clears); the MAKER-ONLY cost is realized at PnL time,
    not at the gate. Exit is when this gate CLEARS (returns gated=False).

    Returns {gated, mean_apr (signed), positive_fraction, reasons}.
    """
    reasons: list[str] = []
    if series is None or len(series) < window:
        return {"gated": False, "mean_apr": 0.0, "positive_fraction": 0.0,
                "reasons": [f"insufficient history: need >= {window} hourly rows"]}
    win = series["funding_rate"].astype(float).iloc[-window:]
    mean_apr = hourly_to_apr(float(win.mean()))
    positive_fraction = float((win > 0).mean())
    g1 = mean_apr >= FUNDING_SUSTAIN_FLOOR_APR
    g2 = positive_fraction >= FUNDING_POSITIVE_FRACTION
    if not g1:
        reasons.append(f"G1 mean APR {mean_apr:.4f} < {FUNDING_SUSTAIN_FLOOR_APR:.2f}")
    if not g2:
        reasons.append(f"G2 positive fraction {positive_fraction:.2f} "
                       f"< {FUNDING_POSITIVE_FRACTION:.2f}")
    return {"gated": g1 and g2, "mean_apr": mean_apr,
            "positive_fraction": positive_fraction, "reasons": reasons}


# ── Directional risk model (§1.4) ────────────────────────────────────────────
DIRECTIONAL_STOP_BPS = 200.0   # naked-short/-long hard stop distance (2%) [tunable]
DIRECTIONAL_LAMBDA = 0.5       # funding must exceed λ × realized vol       [tunable]
VOL_LOOKBACK_DAYS = 30         # realized-vol window (hourly markPx closes) [tunable]
# (DIRECTIONAL_MIN_HOLD reuses MIN_HOLD_HOURS above — 168h cost amortization.)


def realized_annualized_vol(mark_px_closes: pd.Series) -> float:
    """σ_ann = std(log-returns over the trailing VOL_LOOKBACK_DAYS*24 hourly
    closes) * sqrt(8760). 0.0 if < 2 usable observations. Closes are HOURLY
    (assetCtxs snapshot cadence), hence the sqrt(8760) = hours/year annuization.
    """
    closes = pd.to_numeric(mark_px_closes, errors="coerce").dropna()
    closes = closes[closes > 0]
    if len(closes) < 2:
        return 0.0
    lookback = min(len(closes) - 1, VOL_LOOKBACK_DAYS * 24)
    closes = closes.iloc[-(lookback + 1):]
    log_ret = np.log(closes.to_numpy() / closes.shift(1).to_numpy())[1:]
    log_ret = log_ret[np.isfinite(log_ret)]
    if len(log_ret) < 2:
        return 0.0
    return float(log_ret.std(ddof=1) * math.sqrt(HOURS_PER_YEAR))


def directional_hurdle_apr(ann_vol: float, lam: float = DIRECTIONAL_LAMBDA) -> float:
    """Funding hurdle for a directional entry = max(FUNDING_SUSTAIN_FLOOR_APR,
    lam * ann_vol). The funding must more than compensate the expected
    directional volatility cost — a REAL risk rule, not a blank check. `lam` is
    the DIRECTIONAL_LAMBDA override (sensitivity-tested in the backtest)."""
    return max(FUNDING_SUSTAIN_FLOOR_APR, lam * ann_vol)


def directional_risk_gate(mean_apr: float, ann_vol: float,
                          lam: float = DIRECTIONAL_LAMBDA) -> dict:
    """Returns {eligible, hurdle_apr, reason}. eligible = mean_apr >=
    directional_hurdle_apr(ann_vol, lam). mean_apr is the RECEIVING-direction APR
    magnitude (>= 0)."""
    hurdle = directional_hurdle_apr(ann_vol, lam)
    eligible = mean_apr >= hurdle
    reason = "" if eligible else (
        f"directional hurdle: mean APR {mean_apr:.4f} < "
        f"max({FUNDING_SUSTAIN_FLOOR_APR:.2f}, {lam}×vol "
        f"{ann_vol:.4f} = {hurdle:.4f})")
    return {"eligible": eligible, "hurdle_apr": hurdle, "reason": reason}


# ── Spot availability resolver (§1.2) ────────────────────────────────────────
SPOT_MIN_DAY_NTL_VLM_USD = 500_000.0   # spot leg must clear 24h USD notional [tunable]
SPOT_MAX_SPREAD_BPS = 25.0             # spot mark-vs-mid spread cap            [tunable]

# Wrapped-variant candidate suffixes/prefixes for spot naming (best-effort; the
# authoritative mapping is read live from spotMetaAndAssetCtxs each snapshot).
_SPOT_VARIANT_PREFIXES = ("", "U")
_SPOT_VARIANT_SUFFIXES = ("", "0", "1")


def _parse_f(v):
    """float(), preserving None for missing/empty/non-numeric. Never raises."""
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def resolve_spot_leg(perp_name: str, spot_snap: dict | None = None) -> dict:
    """Resolve whether `perp_name` has a tradeable HL spot hedge.

    spot_snap: one parsed spotMetaAndAssetCtxs result, shaped as:
        {
          "by_name": { "<spot token name>": {"day_ntl_vlm_usd": float,
                                             "spread_bps": float} },
          "available_names": ["BTC", "BTC0", "UBTC", ...],
        }
    (produced by parse_spot_snapshot(); see below). Candidate names are exact
    first, then wrapped variants: {name}, {name}0, {name}1, U{name}.

    Returns {available, spot_name, day_ntl_vlm_usd, spread_bps, reason}.
    available = a candidate exists AND day_ntl_vlm_usd >= SPOT_MIN_DAY_NTL_VLM_USD
                AND spread_bps <= SPOT_MAX_SPREAD_BPS.
    """
    by_name = (spot_snap or {}).get("by_name", {})
    if not by_name:
        return {"available": False, "spot_name": None, "day_ntl_vlm_usd": 0.0,
                "spread_bps": None, "reason": "no spot snapshot"}

    # Exact first, then wrapped variants (ordered, deterministic).
    candidates = [perp_name]
    for suffix in _SPOT_VARIANT_SUFFIXES:
        candidates.append(perp_name + suffix)
    for prefix in _SPOT_VARIANT_PREFIXES:
        if prefix:
            candidates.append(prefix + perp_name)

    for name in candidates:
        if name not in by_name:
            continue
        info = by_name[name]
        vlm = float(info.get("day_ntl_vlm_usd", 0.0) or 0.0)
        spread = info.get("spread_bps")
        if vlm >= SPOT_MIN_DAY_NTL_VLM_USD and (
                spread is None or float(spread) <= SPOT_MAX_SPREAD_BPS):
            s = float(spread) if spread is not None else None
            return {"available": True, "spot_name": name,
                    "day_ntl_vlm_usd": vlm, "spread_bps": s,
                    "reason": "liquid spot leg"}
    return {"available": False, "spot_name": None, "day_ntl_vlm_usd": 0.0,
            "spread_bps": None,
            "reason": "no liquid HL spot leg (5candidates checked)"}


def parse_spot_snapshot(spot_meta: dict, spot_ctxs: list[dict]) -> dict:
    """Parse a raw spotMetaAndAssetCtxs POST into the spot_snap consumed by
    resolve_spot_leg(). spot_meta = {universe:[{name,tokens:[baseIdx,quoteIdx]}]
    , tokens:[{name}]}; spot_ctxs indexed like spot_meta.universe with
    dayNtlVlm / markPx / midPx. Resolution:
      * token index -> name via tokens[idx].name.
      * spot market name = tokenName(baseIdx) (the perp-underlying name).
      * spread_bps = |markPx - midPx| / midPx * 1e4.  (midPx<=0 -> None)
      * day_ntl_vlm_usd = dayNtlVlm (quote USD)."""
    tokens = spot_meta.get("tokens", []) or []
    universe = spot_meta.get("universe", []) or []

    def token_name(idx):
        if idx is None or idx < 0 or idx >= len(tokens):
            return None
        return tokens[idx].get("name")

    by_name: dict = {}
    for i, m in enumerate(universe):
        toks = m.get("tokens") or []
        base_idx = toks[0] if toks else None
        quote_idx = toks[1] if len(toks) > 1 else None
        base = token_name(base_idx)
        quote = token_name(quote_idx)
        # Only fiat (USDC-quoted) spot markets are valid hedges for a perp.
        if not base or quote != "USDC":
            continue
        ctx = spot_ctxs[i] if i < len(spot_ctxs) else {}
        mid = _parse_f(ctx.get("midPx"))
        mark = _parse_f(ctx.get("markPx"))
        spread = None
        if mid is not None and mark is not None and mid > 0:
            spread = abs(mark - mid) / mid * 1e4
        by_name[base] = {
            "day_ntl_vlm_usd": _parse_f(ctx.get("dayNtlVlm")) or 0.0,
            "spread_bps": spread,
        }
    return {"by_name": by_name, "available_names": sorted(by_name)}


# ── Execution-form dispatch (§1.3) ───────────────────────────────────────────
def dispatch_execution_form(funding_sign: float, spot: dict | None = None,
                            in_universe: bool = True, delisted: bool = False,
                            coin: str | None = None) -> str:
    """Returns one of 'skip' / 'delta_neutral' / 'directional_short' /
    'directional_long'.

    funding_sign>0 & spot available & coin in DELTA_NEUTRAL_UNIVERSE
        (and ENABLE_DELTA_NEUTRAL) -> delta_neutral
    funding_sign>0 & (no spot / non-major) -> directional_short (naked short perp)
    funding_sign<0            -> directional_long   (naked long perp; no spot
                                                      short exists for majors)
    funding_sign==0 / delisted -> skip

    US-229: delta_neutral is dispatched ONLY for the liquid-spot majors
    (DELTA_NEUTRAL_UNIVERSE = BTC/ETH/SOL). `coin` is the canonical perp name;
    when omitted (backward-compatible callers), delta_neutral is never
    dispatched (coin not a major) — preserving the directional short-perp form
    as the load-bearing construction for the full universe.

    `in_universe` is accepted for spec-fidelity but is intentionally UNUSED —
    the full universe is every non-delisted perp, so in-universe restriction no
    longer applies (US-185 §1.1). Delta-neutral for funding<0 would require a
    SHORT spot leg, which HL does not support for the majors -> never dispatched.
    """
    if delisted:
        return "skip"
    if funding_sign > 0:
        if (ENABLE_DELTA_NEUTRAL and coin in DELTA_NEUTRAL_UNIVERSE
                and isinstance(spot, dict) and spot.get("available")):
            return "delta_neutral"
        return "directional_short"
    if funding_sign < 0:
        return "directional_long"
    return "skip"


# ── Position sizing / capacity (§1.5, corrected §3) ──────────────────────────
CAPITAL_RISK_BUDGET = 0.01    # 1% capital = max adverse loss ("1R") [unchanged]
KILL_BASIS_BPS = 50.0         # 0.50% basis-widening stop (delta-neutral) [tunable]
GROSS_NOTIONAL_CAP = 1.0      # notional <= 1× capital (NO leverage)  [F2 GATED]
OI_CAPACITY_FRAC = 0.02       # notional <= 2% of coin open interest [unchanged]
DELTA_CAP = 0.05              # |net delta|/notional <= 5% (else ineligible) [kept]

# Delta-neutral ENABLING (US-229): the delta-neutral form (long spot / short
# perp) is now ENABLED for the liquid-spot majors only, after HYP-28 (~15-21%
# unlevered APR, funding-true) and HYP-29 (survives G3 fill-realism at MAKER
# fills — ~10-12% conservative — with ~$24.5M capacity). PAPER-FORWARD ONLY:
# LIVE_TRADING_ENABLED stays OFF; no promotion. MAKER-ONLY (binding): taker is
# decisively net-negative, so a taker fill must be IMPOSSIBLE, not discouraged.
ENABLE_DELTA_NEUTRAL = True
DN_GROSS_NOTIONAL_CAP = 1.0      # delta-neutral cap = 1× (NO leverage; 2× is a
                                 # later, separately-signed risk)
# Liquid-spot majors ONLY — the HYP-28/29 universe. Delta-neutral is dispatched
# for these coins and NOTHING else (dispatch_execution_form enforces membership).
DELTA_NEUTRAL_UNIVERSE = ("BTC", "ETH", "SOL")

# ── MAKER-ONLY execution guard (US-229, binding) ────────────────────────────
EXECUTION_MAKER = "maker"
EXECUTION_TAKER = "taker"
_EXECUTION_TYPES = (EXECUTION_MAKER, EXECUTION_TAKER)


def assert_maker_only(execution_type: str, execution_form: str) -> None:
    """Hard guard: the delta-neutral form may ONLY execute as maker/post-only.

    HYP-29 established taker execution is decisively net-negative (−7% to −14%
    APR), so a taker fill on either leg must be IMPOSSIBLE — this RAISES
    (fail-closed) on any non-maker request, rather than merely discouraging it.
    """
    if execution_type not in _EXECUTION_TYPES:
        raise ValueError(
            f"REFUSED: unknown execution_type={execution_type!r} — must be "
            f"one of {_EXECUTION_TYPES}")
    if execution_form == "delta_neutral" and execution_type != EXECUTION_MAKER:
        raise ValueError(
            "REFUSED: delta-neutral funding carry is MAKER-ONLY (US-229). "
            f"execution_type={execution_type!r} — BOTH legs must be post-only/"
            "maker; a taker fill is impossible by construction (HYP-29: taker "
            "is decisively net-negative).")


def gross_cap(capital: float, execution_form: str) -> float:
    """Notional backstop rail per execution form. delta_neutral -> the (gated)
    DN_GROSS_NOTIONAL_CAP; directional_* -> GROSS_NOTIONAL_CAP (already bound by
    their hard stop; this is a backstop only)."""
    if execution_form == "delta_neutral":
        return DN_GROSS_NOTIONAL_CAP * capital
    return GROSS_NOTIONAL_CAP * capital


def size_position(capital: float, stop_bps: float, open_interest_usd: float,
                  execution_form: str, eligible: bool = True) -> dict:
    """Returns {notional, risk_usd, size_capped, cap_reason, stop_bps}.

    notional = min( (CAPITAL_RISK_BUDGET*capital)/(stop_bps/1e4),   # risk budget
                    gross_cap(capital, execution_form),              # §3.3 backstop
                    OI_CAPACITY_FRAC*open_interest_usd )             # capacity
    risk_usd  = notional * stop_bps/1e4     # RE-derived from ACTUAL notional

    CRITICAL INVARIANT (§3.3): 1R = 1% capital, notional is the DEPENDENT
    variable. If ANY rail caps notional below the risk budget, risk_usd is
    re-derived from the ACTUAL notional and size_capped=True with the binding
    reason — the labelled risk unit is NEVER silently shrunk while a P&L keeps
    the "R" label. stop_bps = KILL_BASIS_BPS (delta_neutral) or
    DIRECTIONAL_STOP_BPS (directional). eligible=False -> zeroed.
    """
    if not eligible:
        return {"notional": 0.0, "risk_usd": 0.0, "size_capped": True,
                "cap_reason": "ineligible", "stop_bps": stop_bps}
    stop_frac = stop_bps / 1e4
    rail_budget = (CAPITAL_RISK_BUDGET * capital) / stop_frac
    rail_notional = gross_cap(capital, execution_form)
    rail_oi = OI_CAPACITY_FRAC * open_interest_usd
    notional = min(rail_budget, rail_notional, rail_oi)
    risk_usd = notional * stop_frac

    rails = {"risk-budget (1% capital)": rail_budget,
             "gross notional cap": rail_notional,
             "OI capacity (2% of open interest)": rail_oi}
    # Filter out non-positive rails (e.g. zero OI) so min() picks a real binder.
    positive_rails = {k: v for k, v in rails.items() if v > 0}
    size_capped = notional < rail_budget - 1e-12
    if not positive_rails:
        cap_reason = "no positive capacity rails"
    elif size_capped:
        cap_reason = min(positive_rails, key=positive_rails.get)
    else:
        cap_reason = None    # risk budget bound (honest 1R)
    return {"notional": notional, "risk_usd": risk_usd,
            "size_capped": size_capped, "cap_reason": cap_reason,
            "stop_bps": stop_bps}


# ── Kill / de-risk rules (§1.6) ─────────────────────────────────────────────
FLIP_EXIT_FLOOR = 0.0       # current hourly funding <= 0 -> exit (short branch)
DERISK_DECAY_APR = 0.04     # rolling-mean APR < 4%/yr while positive -> de-risk


def basis_widen(perp_mark: float, spot_oracle: float) -> float:
    """basis in bps = (perp_mark - spot_oracle)/spot_oracle * 1e4 (signed)."""
    if spot_oracle <= 0:
        return 0.0
    return (perp_mark - spot_oracle) / spot_oracle * 1e4


def mark_oracle_basis(mark_px: float, oracle_px: float) -> float:
    """Alias for basis_widen with the HONEST mark-oracle naming (§2.2)."""
    return basis_widen(mark_px, oracle_px)


def rate_flip(series: pd.DataFrame, sign: int = 1) -> bool:
    """current funding_rate * sign <= FLIP_EXIT_FLOOR (funding left the
    receiving direction). sign=+1 -> short branch (exit when funding<=0);
    sign=-1 -> long branch (exit when funding>=0)."""
    if series is None or series.empty:
        return False
    return float(series["funding_rate"].iloc[-1]) * sign <= FLIP_EXIT_FLOOR


def funding_decaying(series: pd.DataFrame, sign: int = 1) -> bool:
    """rolling mean |APR| (in the receiving direction) < DERISK_DECAY_APR."""
    w = FUNDING_WINDOW_HOURS
    if series is None or len(series) < w:
        return False
    window = series["funding_rate"].astype(float).iloc[-w:]
    mean_mag = hourly_to_apr(float((window * sign).mean()))
    return mean_mag < DERISK_DECAY_APR


# ── Backtest (§1.7, reconstituted §2) ────────────────────────────────────────
DEFAULT_PARAMS = {
    "capital": 1_000_000.0,
    "open_interest_usd": float("inf"),
    "cost_bps": MAKER_ROUND_TRIP_BPS,   # default = maker-fill path (US-180)
    "cost_mode": "maker",
}

_EPISODE_COLUMNS = [
    "coin", "entry_ts", "exit_ts", "exit_reason", "execution_form",
    "funding_pnl", "basis_pnl", "basis_source", "direction_pnl",
    "execution_cost", "net_funding", "net_carry", "notional", "risk_usd",
    "net_r", "regime_label",
]

_FORM_SIGN = {"delta_neutral": 1, "directional_short": 1, "directional_long": -1}
_DIRECTIONAL_FORMS = ("directional_short", "directional_long")


def _align_to_funding(basis_real: pd.DataFrame, funding_times_ms: np.ndarray,
                      column: str) -> np.ndarray | None:
    """ffill (asof-backward) `column` of basis_real onto funding_times_ms.
    Returns a float ndarray aligned to funding rows (NaN where no prior value)."""
    if basis_real is None or basis_real.empty or column not in basis_real.columns:
        return None
    src = pd.DataFrame({
        "time": pd.to_numeric(basis_real["time"], errors="coerce"),
        column: pd.to_numeric(basis_real[column], errors="coerce"),
    }).dropna(subset=["time"]).sort_values("time")
    if src.empty:
        return None
    tgt = pd.DataFrame({"time": funding_times_ms.astype("int64")})
    merged = pd.merge_asof(tgt, src, on="time", direction="backward")
    return merged[column].to_numpy(dtype=float)


def simulate_carry(funding: pd.DataFrame, basis_real: pd.DataFrame | None = None,
                   spot: dict | None = None, params: dict | None = None) -> pd.DataFrame:
    """Hourly walk (per coin). One row per episode with the explicit funding-vs-
    basis decomposition (§2.4).

    funding:    DataFrame[time, funding_rate, premium] ascending (from
                hl_funding_store.read_funding). The `premium` column is NO LONGER
                used as a basis proxy (US-185 §2.2).
    basis_real: DataFrame[time, mark_px, oracle_px, basis_bps] from
                hl_assetctx_store.read_basis() (REAL mark-oracle) — OR a
                mark_px-only frame (basis_bps NaN) for a directional-only walk.
                When None/absent:
                  * basis_pnl=None, basis_source='proxy', basis_widen DISABLED.
                  * directional entries are SKIPPED (D3: no mark_px -> cannot
                    realize the hard stop).
    spot:       parsed spot snapshot (§1.2) for delta-neutral dispatch (gated).

    Exit precedence (unambiguous, §4): directional hard stop (directional forms
    only), then rate_flip, then real basis_widen (delta-neutral only), then decay.

    Returns one row per episode with columns _EPISODE_COLUMNS. net_r (headline):
      * delta_neutral -> net_funding / risk_usd (funding-only; basis is a
        separate reported column, NOT folded in — §2.2/§2.4).
      * directional_* -> (net_funding + direction_pnl) / risk_usd (the directional
        mark-p&l — incl. the -1R hard stop — IS netted, because the directional
        form must honestly prove profitable; the "funding-only" decomposition
        rule targets the delta-neutral basis-proxy confusion, not naked price
        risk).
    """
    p = dict(DEFAULT_PARAMS)
    if params:
        p.update(params)
    capital = float(p["capital"])
    oi_usd = float(p["open_interest_usd"])
    cost_bps = float(p["cost_bps"])
    dlam = float(p.get("directional_lambda", DIRECTIONAL_LAMBDA))

    empty = pd.DataFrame(columns=_EPISODE_COLUMNS)
    if funding is None or funding.empty:
        return empty

    rates = funding["funding_rate"].astype(float).to_numpy()
    times = funding["time"].astype(int).to_numpy()

    # Real basis / mark-price series aligned to funding rows (asof-backward).
    mark_px = _align_to_funding(basis_real, times, "mark_px")
    basis_bps = _align_to_funding(basis_real, times, "basis_bps") if basis_real is not None else None

    w = FUNDING_WINDOW_HOURS
    n = len(funding)
    coin = funding.attrs.get("coin", "?")
    if isinstance(coin, list):
        coin = coin[0]
    if "coin" in p:
        coin = p["coin"]

    episodes: list[dict] = []
    in_pos = False
    entry_idx = 0
    entry_ts = 0
    entry_sign = 0
    entry_form = ""
    entry_mark = float("nan")
    entry_basis = float("nan")
    notional = 0.0
    risk_usd = 0.0
    stop_bps = 0.0
    funding_pnl = 0.0

    for i in range(n):
        if i + 1 < w:
            continue

        if not in_pos:
            sig_pos = funding_window_signal(funding.iloc[i + 1 - w:i + 1], sign=1)
            sig_neg = funding_window_signal(funding.iloc[i + 1 - w:i + 1], sign=-1)
            # S3 mutual exclusion: at most one direction can be sustained.
            direction = None
            sig = None
            if sig_pos["sustained"]:
                direction, sig = 1, sig_pos
            elif sig_neg["sustained"]:
                direction, sig = -1, sig_neg
            if direction is None:
                continue

            form = dispatch_execution_form(float(direction), spot, coin=coin)
            if form == "skip":
                continue

            stop_bps = KILL_BASIS_BPS if form == "delta_neutral" else DIRECTIONAL_STOP_BPS

            if form in _DIRECTIONAL_FORMS:
                # D3: a realizable stop requires a mark_px series to track the leg.
                if mark_px is None or not np.isfinite(mark_px[i]):
                    continue  # cannot risk-manage -> skip (no blank-check short)
                # D2: funding must clear λ × realized vol (on top of S1-S4).
                vol = realized_annualized_vol(pd.Series(mark_px[:i + 1]))
                gate = directional_risk_gate(sig["mean_mag_apr"], vol, lam=dlam)
                if not gate["eligible"]:
                    continue
            else:
                # delta_neutral: basis_widen stop is usable only with real basis.
                if basis_bps is None or not np.isfinite(basis_bps[i]):
                    # Built but (a) gated off by default and (b) no real basis ->
                    # cannot run the basis stop; skip rather than use a proxy.
                    continue

            sz = size_position(capital, stop_bps, oi_usd, form, eligible=True)
            notional = sz["notional"]
            risk_usd = sz["risk_usd"]
            if notional <= 0.0 or risk_usd <= 0.0:
                continue  # OI/capacity zeroed the position

            in_pos = True
            entry_idx = i
            entry_ts = int(times[i])
            entry_sign = direction
            entry_form = form
            entry_mark = float(mark_px[i]) if mark_px is not None else float("nan")
            entry_basis = float(basis_bps[i]) if basis_bps is not None else float("nan")
            funding_pnl = 0.0
            continue

        # ── In position ──────────────────────────────────────────────────────
        # Accrue this hour's funding (sign=+1 short / -1 long receive funding).
        funding_pnl += float(entry_sign) * float(rates[i]) * notional

        exit_reason = None
        on_stop = False

        # 1. directional hard stop (directional forms only; MANDATORY).
        if entry_form in _DIRECTIONAL_FORMS and mark_px is not None \
                and np.isfinite(entry_mark) and np.isfinite(mark_px[i]) and entry_mark > 0:
            move_bps = (mark_px[i] - entry_mark) / entry_mark * 1e4
            adverse = move_bps >= DIRECTIONAL_STOP_BPS if entry_sign == 1 \
                else move_bps <= -DIRECTIONAL_STOP_BPS
            if adverse:
                exit_reason = "directional_stop"
                on_stop = True

        # 2. rate flip (funding left the receiving direction).
        if exit_reason is None and rate_flip(funding.iloc[i:i + 1], sign=entry_sign):
            exit_reason = "rate_flip"

        # 3. real basis-widening kill (delta-neutral only, real basis available).
        if exit_reason is None and entry_form == "delta_neutral" \
                and basis_bps is not None \
                and np.isfinite(entry_basis) and np.isfinite(basis_bps[i]):
            if (basis_bps[i] - entry_basis) >= KILL_BASIS_BPS:
                exit_reason = "basis_widen"

        # 4. de-risk: rolling |APR| decayed below floor while still in direction.
        if exit_reason is None and funding_decaying(
                funding.iloc[i + 1 - w:i + 1], sign=entry_sign):
            exit_reason = "decay"

        if exit_reason is None:
            continue

        # ── close the episode ────────────────────────────────────────────────
        exit_mark = float(mark_px[i]) if mark_px is not None else float("nan")

        # direction_pnl (directional mark move, incl. the -1R hard stop).
        direction_pnl = 0.0
        if entry_form in _DIRECTIONAL_FORMS:
            if on_stop:
                direction_pnl = -risk_usd
            elif np.isfinite(entry_mark) and np.isfinite(exit_mark) and entry_mark > 0:
                if entry_sign == 1:   # short: profit when mark falls
                    direction_pnl = (entry_mark - exit_mark) / entry_mark * notional
                else:                 # long: profit when mark rises
                    direction_pnl = (exit_mark - entry_mark) / entry_mark * notional

        # basis_pnl (real mark-oracle convergence; delta-neutral only).
        basis_pnl = None
        basis_source = "none"
        if entry_form == "delta_neutral":
            if basis_bps is not None and np.isfinite(entry_basis) and np.isfinite(basis_bps[i]):
                basis_pnl = (entry_basis - basis_bps[i]) / 1e4 * notional
                basis_source = "mark_oracle"
            else:
                basis_source = "proxy"

        execution_cost = cost_bps / 1e4 * notional
        net_funding = funding_pnl - execution_cost
        net_carry = (net_funding + direction_pnl
                     + (basis_pnl if basis_pnl is not None else 0.0))

        if entry_form == "delta_neutral":
            net_r = net_funding / risk_usd if risk_usd > 0 else 0.0
        else:
            net_r = (net_funding + direction_pnl) / risk_usd if risk_usd > 0 else 0.0

        episodes.append({
            "coin": coin, "entry_ts": entry_ts, "exit_ts": int(times[i]),
            "exit_reason": exit_reason, "execution_form": entry_form,
            "funding_pnl": funding_pnl, "basis_pnl": basis_pnl,
            "basis_source": basis_source, "direction_pnl": direction_pnl,
            "execution_cost": execution_cost, "net_funding": net_funding,
            "net_carry": net_carry, "notional": notional, "risk_usd": risk_usd,
            "net_r": float(net_r), "regime_label": None,
        })
        in_pos = False

    if not episodes:
        return empty
    return pd.DataFrame(episodes, columns=_EPISODE_COLUMNS)


def _pf(rs) -> float:
    gains = sum(r for r in rs if r > 0)
    losses = abs(sum(r for r in rs if r < 0))
    return gains / losses if losses > 0 else (float("inf") if gains > 0 else 0.0)


def carry_g3_record(episodes: pd.DataFrame) -> dict:
    """Apply US-174 gate SEMANTICS to carry episodes. Scores against the
    HONEST net_r (funding-only for delta-neutral, funding+directional for the
    directional forms — see simulate_carry). basis_pnl is REPORTED separately
    with its source flag, never folded into the headline R.

    cost assumptions (fee-basis explicit, per §1.6.3):
      optimistic  = gross funding (zero execution cost)   [diagnostic only]
      realistic   = maker-fill cost (12 bps)              [the US-180 path]
      pessimistic = taker-fill cost (24 bps) + basis-gap on the kill exit
                    (exit basis widened by +1 tick = 1 bp beyond KILL_BASIS_BPS)

    Returns {n, optimistic_mean_r, realistic_mean_r, pessimistic_pf, passed,
             reasons, edge_decay_ratio, basis_source, basis_mean, r_unit}.
    """
    if episodes is None or episodes.empty:
        return {"n": 0, "optimistic_mean_r": 0.0, "realistic_mean_r": 0.0,
                "pessimistic_pf": 0.0, "edge_decay_ratio": None, "passed": False,
                "basis_source": None, "basis_mean": None,
                "reasons": ["no episodes"]}

    n = len(episodes)
    budget = episodes["risk_usd"].astype(float)
    fp = episodes["funding_pnl"].astype(float)
    notional = episodes["notional"].astype(float)
    has_dir = "direction_pnl" in episodes.columns
    dr_pnl = (episodes["direction_pnl"].astype(float)
              if has_dir else pd.Series(0.0, index=episodes.index))
    is_kill = (episodes["exit_reason"] == "basis_widen").to_numpy()

    # The honest gross = funding + directional (the directional risk is NOT a
    # disposable credit; basis stays out of the headline).
    gross = fp + dr_pnl
    opt_r = (gross / budget.where(budget > 0, float("nan"))).fillna(0.0)

    maker_cost = MAKER_ROUND_TRIP_BPS / 1e4
    real_r = ((gross - maker_cost * notional)
              / budget.where(budget > 0, float("nan"))).fillna(0.0)

    taker_cost = CARRY_ROUND_TRIP_BPS / 1e4
    basis_gap = 1.0 / 1e4     # +1 tick (1 bp) beyond the kill stop
    gap_loss = pd.Series([basis_gap if k else 0.0 for k in is_kill]) * notional
    pess_r = ((gross - taker_cost * notional - gap_loss)
              / budget.where(budget > 0, float("nan"))).fillna(0.0)

    opt_mean = float(opt_r.mean())
    real_mean = float(real_r.mean())
    pess_pf = _pf(pess_r.tolist())
    decay = (real_mean / opt_mean) if opt_mean > 0 else float("inf")

    # Basis reporting (separate, flagged — never in the headline).
    basis_col = episodes["basis_pnl"].astype(float) \
        if "basis_pnl" in episodes.columns else pd.Series(float("nan"), index=episodes.index)
    basis_credit = basis_col[basis_col.notna()]
    basis_source = (
        set(episodes["basis_source"].dropna().tolist())
        if "basis_source" in episodes.columns else set()
    )

    reasons = []
    if n < MIN_TRADES:
        reasons.append(f"INSUFFICIENT DATA: n={n} < {MIN_TRADES}")
    if real_mean <= 0:
        reasons.append(f"realistic mean R = {real_mean:.4f} <= 0")
    if pess_pf <= 1.0:
        reasons.append(f"pessimistic PF = {pess_pf:.4f} <= 1.0")
    if opt_mean > 0 and real_mean < EDGE_DECAY_FLOOR * opt_mean:
        reasons.append(f"edge decay: realistic {real_mean:.4f} < {EDGE_DECAY_FLOOR}*{opt_mean:.4f}")

    return {
        "n": n,
        "optimistic_mean_r": round(opt_mean, 4),
        "realistic_mean_r": round(real_mean, 4),
        "pessimistic_pf": round(pess_pf, 4),
        "edge_decay_ratio": round(decay, 4) if math.isfinite(decay) else None,
        "passed": len(reasons) == 0,
        "reasons": reasons,
        "basis_source": sorted(basis_source) if basis_source else None,
        "basis_mean": round(float(basis_credit.mean()), 4) if len(basis_credit) else None,
        "r_unit": "1R = 1% capital (corrected; funding-only headline)",
    }


BULL_THRESHOLD = 0.02      # BTC 30d ret > +2%  -> bull
BEAR_THRESHOLD = -0.02     # BTC 30d ret < -2%  -> bear


def partition_regime(episodes: pd.DataFrame, btc_30d_ret: pd.Series) -> dict:
    """Partition episodes by BTC trend regime using btc_30d_ret (a Series indexed
    by timestamp) via backward-fill .asof(entry_ts). bull (>+2%), bear (<-2%),
    neutral (else). Report net_r mean / PF per regime. Returns a dict and also
    labels episodes in place via a returned label Series."""
    if episodes is None or episodes.empty:
        return {"bull": {"n": 0}, "bear": {"n": 0}, "neutral": {"n": 0},
                "labels": pd.Series(dtype=object)}

    def label_at(ts):
        try:
            v = btc_30d_ret.asof(pd.Timestamp(ts, unit="ms", tz="UTC"))
        except Exception:
            return "neutral"
        if v is None or (isinstance(v, float) and math.isnan(v)):
            return "neutral"
        if v > BULL_THRESHOLD:
            return "bull"
        if v < BEAR_THRESHOLD:
            return "bear"
        return "neutral"

    labels = episodes["entry_ts"].map(label_at)
    out = {}
    for reg in ("bull", "bear", "neutral"):
        rs = episodes.loc[labels == reg, "net_r"].astype(float).tolist()
        out[reg] = {"n": len(rs), "mean_r": round(sum(rs) / len(rs), 4) if rs else 0.0,
                    "pf": round(_pf(rs), 4) if rs else 0.0}
    out["labels"] = labels
    return out