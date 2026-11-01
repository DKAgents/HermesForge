"""funding_carry.py — HermesForge US-179: funding / basis carry strategy.

Delta-neutral crypto carry (primary branch: long spot / short perp to RECEIVE
positive funding). Owns the unit normalization, sustained-funding signal, cost
gate, position sizing, kill rules, backtest, G3 wiring, and regime partition.

Design (per architect_us179_180_spec.md Part 1). All thresholds are explicit
module constants (flagged tunable). "Sustained" is ALWAYS a rolling-window
statistic over FUNDING_WINDOW_HOURS consecutive HOURLY observations — never a
single reading.

Import direction is one-way and acyclic (mirrors US-177):
  funding_carry.py -> hl_funding_store.py (+ fee_source, g3_gate constants)

CANONICAL UNIT (binding): annualized APR, converted to/from the endpoint's
HOURLY fraction. The live codebase's 8h framing (funding_state.py) is NOT
touched — those two helpers live HERE.
"""

from __future__ import annotations

import math
import pathlib
import sys

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
# "extreme-flip-risk" warning band (~55–110%/yr). Resolved to the band's floor.
FUNDING_EXTREME_APR = 0.55          # 55%/yr  -> extreme-flip-risk WARNING [tunable]


def funding_window_signal(series: pd.DataFrame) -> dict:
    """Sustained-funding entry signal over the trailing W HOURLY observations.

    series: DataFrame[time, funding_rate, premium] ascending (>= W rows).
    Returns {sustained, elevated, extreme, mean_apr, current_apr,
             positive_fraction, cost_clears, reasons}.

    ENTRY (all four must hold):
      S1  mean(hourly funding over W) >= apr_to_hourly(FUNDING_SUSTAIN_FLOOR_APR)
      S2  count(funding > 0 in window) >= FUNDING_POSITIVE_FRACTION * W
      S3  current funding_rate > 0
      S4  cost_clears(mean_apr)   [conservative taker default]
    S2 is what turns "single spike" into a non-signal (one 0.5%/hr spike + 23 ~0h
    fails both S1 and S2).
    """
    reasons: list[str] = []
    w = FUNDING_WINDOW_HOURS
    if series is None or len(series) < w:
        return {
            "sustained": False, "elevated": False, "extreme": False,
            "mean_apr": 0.0, "current_apr": 0.0, "positive_fraction": 0.0,
            "cost_clears": False,
            "reasons": [f"insufficient history: need >= {w} hourly rows"],
        }

    window = series["funding_rate"].astype(float).iloc[-w:]
    current = float(window.iloc[-1])

    mean_hourly = float(window.mean())
    mean_apr = hourly_to_apr(mean_hourly)
    current_apr = hourly_to_apr(current)
    n_pos = int((window > 0).sum())
    positive_fraction = n_pos / w

    s1 = mean_hourly >= apr_to_hourly(FUNDING_SUSTAIN_FLOOR_APR)
    s2 = positive_fraction >= FUNDING_POSITIVE_FRACTION
    s3 = current > 0.0
    s4 = cost_clears(mean_apr)
    if not s1:
        reasons.append(f"S1 mean APR {mean_apr:.4f} < {FUNDING_SUSTAIN_FLOOR_APR:.2f}")
    if not s2:
        reasons.append(f"S2 positive fraction {positive_fraction:.2f} < {FUNDING_POSITIVE_FRACTION:.2f}")
    if not s3:
        reasons.append("S3 current funding <= 0")
    if not s4:
        reasons.append(f"S4 carry does not clear cost at {mean_apr:.4f} APR")

    sustained = s1 and s2 and s3 and s4
    return {
        "sustained": sustained,
        "elevated": mean_apr >= FUNDING_ELEVATED_APR,
        "extreme": mean_apr >= FUNDING_EXTREME_APR,
        "mean_apr": mean_apr,
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


# ── Position sizing / capacity (§1.5) ───────────────────────────────────────
CAPITAL_RISK_BUDGET = 0.01    # 1% capital = max adverse-basis loss ("1R")
KILL_BASIS_BPS = 50.0         # 0.50% basis-widening stop (defines "1R"
                              # distance)  [tunable]
GROSS_NOTIONAL_CAP = 0.20     # notional <= 20% capital (hard rail)
OI_CAPACITY_FRAC = 0.02       # notional <= 2% of coin open interest
DELTA_CAP = 0.05              # |net delta|/notional <= 5% (else ineligible)


def size_position(capital: float, kill_basis_bps: float,
                  open_interest_usd: float, eligible: bool) -> dict:
    """Returns {notional, basis_risk_usd, size_capped, cap_reason}.

    notional = min( (CAPITAL_RISK_BUDGET*capital) / (kill_basis_bps/1e4),
                    GROSS_NOTIONAL_CAP*capital,
                    OI_CAPACITY_FRAC*open_interest_usd )
    basis_risk_usd = notional * kill_basis_bps/1e4   (must be <= 1% capital).
    eligible=False -> {notional: 0, ... 'ineligible: residual delta'}."""
    if not eligible:
        return {"notional": 0.0, "basis_risk_usd": 0.0, "size_capped": True,
                "cap_reason": "ineligible: residual delta"}
    basis_frac = kill_basis_bps / 1e4
    rail_basis = (CAPITAL_RISK_BUDGET * capital) / basis_frac
    rail_notional = GROSS_NOTIONAL_CAP * capital
    rail_oi = OI_CAPACITY_FRAC * open_interest_usd
    notional = min(rail_basis, rail_notional, rail_oi)
    basis_risk_usd = notional * basis_frac

    rails = {"basis-risk budget (1% capital)": rail_basis,
             "gross notional cap (20% capital)": rail_notional,
             "OI capacity (2% of open interest)": rail_oi}
    binding = min(rails, key=rails.get) if rails else "basis-risk budget"
    size_capped = notional < rail_basis - 1e-12
    return {"notional": notional, "basis_risk_usd": basis_risk_usd,
            "size_capped": size_capped, "cap_reason": binding}


# ── Kill / de-risk rules (§1.6) ─────────────────────────────────────────────
FLIP_EXIT_FLOOR = 0.0       # current hourly funding <= 0 -> exit BOTH legs
DERISK_DECAY_APR = 0.04     # rolling-mean APR < 4%/yr while positive -> de-risk


def basis_widen(perp_mark: float, spot_oracle: float) -> float:
    """basis in bps = (perp_mark - spot_oracle)/spot_oracle * 1e4 (signed)."""
    if spot_oracle <= 0:
        return 0.0
    return (perp_mark - spot_oracle) / spot_oracle * 1e4


def rate_flip(series: pd.DataFrame) -> bool:
    """current funding_rate <= FLIP_EXIT_FLOOR."""
    if series is None or series.empty:
        return False
    return float(series["funding_rate"].iloc[-1]) <= FLIP_EXIT_FLOOR


def funding_decaying(series: pd.DataFrame) -> bool:
    """rolling mean_apr < DERISK_DECAY_APR."""
    w = FUNDING_WINDOW_HOURS
    if series is None or len(series) < w:
        return False
    window = series["funding_rate"].astype(float).iloc[-w:]
    return hourly_to_apr(float(window.mean())) < DERISK_DECAY_APR


# ── Backtest (§1.7) ─────────────────────────────────────────────────────────
DEFAULT_PARAMS = {
    "capital": 1_000_000.0,
    "open_interest_usd": float("inf"),
    "kill_basis_bps": KILL_BASIS_BPS,
    "cost_bps": MAKER_ROUND_TRIP_BPS,   # default = maker-fill path (US-180)
    "cost_mode": "maker",
}


def simulate_carry(funding: pd.DataFrame, basis: pd.DataFrame | None = None,
                   params: dict | None = None) -> pd.DataFrame:
    """Hourly walk. At each hour: if flat and funding_window_signal() passes
    (S1-S4) -> enter (short perp / long spot, receive funding). While in
    position: accrue funding_pnl; check rate_flip / basis_widen / decay -> exit.
    Returns one row per episode: coin, entry_ts, exit_ts, exit_reason,
    funding_pnl, basis_pnl, execution_cost, net_carry, net_r, regime source fit
    (regime_label filled by partition_regime). 1R = basis-risk budget.

    funding: DataFrame[time, funding_rate, premium] ascending. `basis` (optional)
    overrides the premium column as the perp-vs-oracle basis proxy; when None
    the fundingHistory `premium` IS the basis proxy (spec §1.6.2).
    """
    p = dict(DEFAULT_PARAMS)
    if params:
        p.update(params)
    capital = float(p["capital"])
    oi_usd = float(p["open_interest_usd"])
    kill_basis_bps = float(p["kill_basis_bps"])
    cost_bps = float(p["cost_bps"])

    if funding is None or funding.empty:
        return pd.DataFrame(columns=[
            "coin", "entry_ts", "exit_ts", "exit_reason", "funding_pnl",
            "basis_pnl", "execution_cost", "net_carry", "net_r",
            "notional", "basis_risk_usd", "regime_label"])

    rates = funding["funding_rate"].astype(float).to_numpy()
    times = funding["time"].astype(int).to_numpy()
    if basis is not None and "premium" in basis.columns:
        prems = basis["premium"].astype(float).to_numpy()
    else:
        prems = funding["premium"].astype(float).to_numpy()

    w = FUNDING_WINDOW_HOURS
    n = len(funding)
    coin = funding.attrs.get("coin", "?")
    if isinstance(coin, list):
        coin = coin[0]
    if "coin" in p:
        coin = p["coin"]

    episodes = []
    in_pos = False
    entry_idx = 0
    entry_premium = 0.0
    entry_ts = 0
    notional = 0.0
    basis_risk = 0.0
    funding_pnl = 0.0

    for i in range(n):
        if i + 1 < w:
            continue
        sig = funding_window_signal(funding.iloc[i + 1 - w:i + 1])

        if not in_pos:
            if sig["sustained"]:
                in_pos = True
                entry_idx = i
                entry_premium = prems[i]
                entry_ts = int(times[i])
                sz = size_position(capital, kill_basis_bps, oi_usd, True)
                notional = sz["notional"]
                basis_risk = sz["basis_risk_usd"]
                funding_pnl = 0.0
            continue

        # In position -> accrue this hour's funding (short perp: sign +1).
        funding_pnl += 1.0 * rates[i] * notional

        exit_reason = None
        # 1. rate-flip kill
        if rates[i] <= FLIP_EXIT_FLOOR:
            exit_reason = "rate_flip"
        # 2. basis-widening kill (short perp adverse = premium rising from entry)
        elif (prems[i] * 1e4) - (entry_premium * 1e4) >= kill_basis_bps:
            exit_reason = "basis_widen"
        # 3. de-risk: rolling mean APR decayed below floor while still positive
        elif funding_decaying(funding.iloc[i + 1 - w:i + 1]):
            exit_reason = "decay"

        if exit_reason is None:
            continue

        basis_pnl = (entry_premium - prems[i]) * notional
        execution_cost = cost_bps / 1e4 * notional
        net_carry = funding_pnl + basis_pnl - execution_cost
        net_r = net_carry / basis_risk if basis_risk > 0 else 0.0
        episodes.append({
            "coin": coin, "entry_ts": entry_ts, "exit_ts": int(times[i]),
            "exit_reason": exit_reason, "funding_pnl": funding_pnl,
            "basis_pnl": basis_pnl, "execution_cost": execution_cost,
            "net_carry": net_carry, "net_r": float(net_r),
            "notional": notional, "basis_risk_usd": basis_risk,
            "regime_label": None,
        })
        in_pos = False

    if not episodes:
        return pd.DataFrame(columns=[
            "coin", "entry_ts", "exit_ts", "exit_reason", "funding_pnl",
            "basis_pnl", "execution_cost", "net_carry", "net_r",
            "notional", "basis_risk_usd", "regime_label"])
    return pd.DataFrame(episodes)


def _pf(rs) -> float:
    gains = sum(r for r in rs if r > 0)
    losses = abs(sum(r for r in rs if r < 0))
    return gains / losses if losses > 0 else (float("inf") if gains > 0 else 0.0)


def carry_g3_record(episodes: pd.DataFrame) -> dict:
    """Apply US-174 gate SEMANTICS to carry episodes using net_r (1R = basis-risk
    budget). Reuses g3_gate's EXACT thresholds (MIN_TRADES, EDGE_DECAY_FLOOR).

    cost assumptions (fee-basis explicit, per §1.6.3):
      optimistic  = gross carry (zero execution cost)  [diagnostic only]
      realistic   = maker-fill cost (12 bps)           [the US-180 path]
      pessimistic = taker-fill cost (24 bps) + basis-gap on the kill exit
                    (exit basis widened by +1 tick = 1 bp beyond KILL_BASIS_BPS)

    F3 FLAG: G3's per-trade R was built for directional R; here 1R is redefined
    as basis-budget R. n>=10, mean R>0, PF>1, decay>=0.6 mean what they mean,
    but the R UNIT is re-mapped (documented here, not silent).

    Returns {n, optimistic_mean_r, realistic_mean_r, pessimistic_pf, passed,
             reasons, edge_decay_ratio}.
    """
    if episodes is None or episodes.empty:
        return {"n": 0, "optimistic_mean_r": 0.0, "realistic_mean_r": 0.0,
                "pessimistic_pf": 0.0, "edge_decay_ratio": None, "passed": False,
                "reasons": ["no episodes"]}

    n = len(episodes)
    budget = episodes["basis_risk_usd"].astype(float)
    fp = episodes["funding_pnl"].astype(float)
    bp = episodes["basis_pnl"].astype(float)
    notional = episodes["notional"].astype(float)
    is_kill = (episodes["exit_reason"] == "basis_widen").to_numpy()

    gross = fp + bp
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
        "r_unit": "basis-budget R (F3 re-map)",
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