"""vol_vrp.py — HermesForge US-181: short-vol / variance-risk-premium strategy.

Short an ATM straddle (BTC + ETH, Deribit) and collect the variance-risk
premium (implied > realized), CONDITIONED on a vol-of-vol timing filter so the
position is skipped in the high-vol-of-vol regimes where unconditional short-vol
gets steamrolled. Tail risk is de-risked by a MANDATORY vol-spike stop (short
gamma + short vega -> unbounded loss on a vol spike).

STATUS (binding, per architect spec §5.4): HYPOTHESIS / PAPER-FORWARD ONLY.
The IV store has ~30d of DVOL + a single ATM-IV snapshot. There is NOT enough
history to derive VOV_THRESHOLD (§2.2) or to meet G3 (n >= 10 with a meaningful
tail sample). This module is NOT promotable; nothing here claims a proven edge.

This module is a PURE strategy (mirrors funding_carry.py): numbers in, numbers
out — NO store I/O. The store reads live in the driver (vrp_paper_forward.py);
the vol-of-vol LEVEL itself is read via vol_of_vol_gate.vol_of_vol_level().

Import direction (one-way, acyclic):
  vol_vrp.py -> fee_source (option cost class, lazy) [+ vol_of_vol_gate via the
                driver, NOT here]

Black-Scholes here is r = 0 (FLAG F12, crypto — no risk-free rate) and is an
APPROXIMATION for coin-settled ("reversed") Deribit options (FLAG F5): mark_iv
is quoted directly, and the held-to-expiry payoff |S_T - K| is EXACT regardless
of settlement. BS greeks are flagged approximate, never silently exact.

The BS helpers below mirror options_recommender.py's _norm_cdf/_norm_pdf/_bs_d1
(do not re-derive) and add _bs_price / _bs_vega per spec §1.3. They are kept
self-contained here (NOT imported from scripts/discord) to preserve the acyclic
import boundary and avoid dragging yfinance into the gauntlet strategy layer.
"""

from __future__ import annotations

import math

# ── Timing / tail-risk constitution constants (§2, §3) ──────────────────────
HOURS_PER_YEAR = 8760                    # hours/year (hourly DVOL annualization)
MINUTES_PER_YEAR = 365 * 24 * 60           # 525600
FIVE_MIN_BARS_PER_YEAR = MINUTES_PER_YEAR / 5  # 105120 (5m-bar annualization)

VOV_WINDOW_HOURS = 30 * 24               # vol-of-vol trailing window (§2.1)
REALIZED_VOL_LOOKBACK_DAYS = 30          # realized-vol trailing window (§2.1)

VRP_MULT = 1.0                           # implied must exceed realized (§F10)
VOL_SPIKE_PCT = 0.20                     # DVOL +20% from entry -> close (§F2a)
IV_SPIKE_PCT = 0.15                      # ATM IV +15% from entry -> close (§F2a)

# ── Margin / sizing constitution (§4) ───────────────────────────────────────
TAIL_LOSS_FRAC = 0.10                    # worst-case straddle loss @ stop (F6)
MARGIN_UNDERLYING_FRAC = 0.20            # "premium + ~20% of underlying" (F7)
MARGIN_CAP_FRAC = 1.0                    # NO leverage: margin <= 1x capital (F7b)
CAPITAL_RISK_BUDGET = 0.01               # 1R = 1% capital (reuse funding_carry)

# Morning anchor (F9): entries evaluated only on the first hourly candle of the
# UTC day (hour 00:00 UTC). The runner emits ONE snapshot per UTC day.
MORNING_HOUR_UTC = 0

# Minimum data window for threshold derivation / backtest (§5.4). 6–12 months
# spanning a full vol cycle is the BINDING requirement; 180d is the floor.
MIN_WINDOW_DAYS = 180


# ── Black-Scholes (r = 0, sigma in DECIMAL) ─────────────────────────────────
def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _norm_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def _bs_d1(S: float, K: float, T: float, r: float, sigma: float) -> float:
    if T <= 0 or sigma <= 0:
        return 0.0
    return (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))


def _bs_d2(S: float, K: float, T: float, r: float, sigma: float) -> float:
    return _bs_d1(S, K, T, r, sigma) - sigma * math.sqrt(T)


def _bs_price(S: float, K: float, T: float, sigma: float,
              option_type: str = "call", r: float = 0.0) -> float:
    """Black-Scholes premium (spec §1.3, r=0 default). sigma is DECIMAL."""
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return 0.0
    d1 = _bs_d1(S, K, T, r, sigma)
    d2 = d1 - sigma * math.sqrt(T)
    if option_type == "call":
        return S * _norm_cdf(d1) - K * math.exp(-r * T) * _norm_cdf(d2)
    return K * math.exp(-r * T) * _norm_cdf(-d2) - S * _norm_cdf(-d1)


def _bs_vega(S: float, K: float, T: float, sigma: float, r: float = 0.0) -> float:
    """Vega per 1 vol point (1% sigma), spec §1.3. sigma DECIMAL."""
    if T <= 0 or sigma <= 0 or S <= 0:
        return 0.0
    d1 = _bs_d1(S, K, T, r, sigma)
    return S * math.sqrt(T) * _norm_pdf(d1) / 100.0


def _bs_gamma(S: float, K: float, T: float, sigma: float, r: float = 0.0) -> float:
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return 0.0
    d1 = _bs_d1(S, K, T, r, sigma)
    return _norm_pdf(d1) / (S * sigma * math.sqrt(T))


def _bs_theta(S: float, K: float, T: float, sigma: float, r: float = 0.0) -> float:
    """Theta per DAY (call ~= put at ATM), spec §1.3."""
    if T <= 0 or sigma <= 0 or S <= 0:
        return 0.0
    d1 = _bs_d1(S, K, T, r, sigma)
    return -(S * _norm_pdf(d1) * sigma) / (2.0 * math.sqrt(T)) / 365.0


# ── Instrument + construction (§1) ──────────────────────────────────────────
def straddle_premium(S0: float, K: float, T: float, sigma: float,
                     r: float = 0.0) -> float:
    """C + P at the same strike K (ATM straddle). sigma DECIMAL."""
    return _bs_price(S0, K, T, sigma, "call", r) + \
        _bs_price(S0, K, T, sigma, "put", r)


def straddle_greeks(S0: float, K: float, T: float, sigma: float,
                    r: float = 0.0) -> dict:
    """Net straddle greeks (short straddle earns theta, loses gamma/vega)."""
    return {
        "vega": _bs_vega(S0, K, T, sigma, r) * 2.0,      # per 1 vol point
        "gamma": _bs_gamma(S0, K, T, sigma, r) * 2.0,
        "theta": _bs_theta(S0, K, T, sigma, r) * 2.0,    # per day
    }


# ── PnL identity (§1.2) ─────────────────────────────────────────────────────
def held_to_expiry_pnl(premium_collected: float, S_T: float, K: float,
                       execution_cost: float = 0.0) -> dict:
    """HELD-TO-EXPIRY (primary — the VRP itself): premium − |S_T − K| − cost."""
    realized_payoff = abs(S_T - K)
    gross_pnl = premium_collected - realized_payoff
    return {
        "premium_collected": premium_collected,
        "realized_payoff": realized_payoff,
        "gross_pnl": gross_pnl,
        "net_pnl": gross_pnl - execution_cost,
    }


def close_straddle_mtm(S1: float, K: float, T1: float, sigma1: float,
                       premium_collected: float, execution_cost: float = 0.0,
                       r: float = 0.0) -> dict:
    """MARK-TO-MARKET early exit (vol-spike stop, §3): buy-to-cover both legs."""
    premium_at_exit = straddle_premium(S1, K, T1, sigma1, r)
    mtm_pnl = premium_collected - premium_at_exit - execution_cost
    return {"premium_at_exit": premium_at_exit, "mtm_pnl": mtm_pnl}


# ── Timing predicate (§2.1) ─────────────────────────────────────────────────
def enter_short_vol(vov_level: float | None, atm_iv: float | None,
                    realized_vol: float | None, morning: bool,
                    vov_threshold: float | None = None,
                    vrp_mult: float = VRP_MULT) -> dict:
    """The entry predicate: VOV_CALM AND VRP_RICH AND MORNING.

    VOV_CALM is computable ONLY once VOV_THRESHOLD has been derived (§2.2,
    needs 6–12 months of DVOL). Until then it is None (underivable) and the
    entry is NOT authorised — the strategy stays paper-forward-hypothesis.
    A vol-of-vol reading authorises an entry on ITS day only; the runner passes
    ``morning`` for the first hourly candle of the UTC day (§2.3).
    """
    reasons: list[str] = []

    if vov_threshold is None:
        vov_calm = None
        reasons.append("VOV_CALM underivable: VOV_THRESHOLD not yet derived "
                       f"(needs >= {MIN_WINDOW_DAYS}d of DVOL)")
    elif vov_level is None:
        vov_calm = None
        reasons.append("VOV_CALM: no vol-of-vol level (insufficient DVOL history)")
    else:
        vov_calm = bool(vov_level < vov_threshold)
        if not vov_calm:
            reasons.append(f"VOV_CALM false: vol-of-vol {vov_level:.4f} "
                           f">= threshold {vov_threshold:.4f}")

    vrp_rich = (atm_iv is not None and realized_vol is not None
                and atm_iv > realized_vol * vrp_mult)
    if not vrp_rich:
        iv = atm_iv if atm_iv is not None else float("nan")
        rv = realized_vol if realized_vol is not None else float("nan")
        reasons.append(f"VRP_RICH false: atm_iv {iv:.4f} <= "
                       f"{vrp_mult}*realized_vol {rv:.4f}")

    if not morning:
        reasons.append("MORNING false: not the first hourly candle of the UTC day")

    enter = bool(vov_calm) and vrp_rich and bool(morning)

    return {
        "vov_calm": vov_calm,
        "vrp_rich": vrp_rich,
        "morning": bool(morning),
        "vov_level": vov_level,
        "vov_threshold": vov_threshold,
        "vp_mult": vrp_mult,
        "enter": enter,
        "reasons": reasons,
    }


# ── Vol-spike stop (§3.1) ───────────────────────────────────────────────────
def vol_spike(dvol_now: float | None, dvol_entry: float | None,
              atm_iv_now: float | None, atm_iv_entry: float | None,
              vol_spike_pct: float = VOL_SPIKE_PCT,
              iv_spike_pct: float = IV_SPIKE_PCT) -> dict:
    """MANDATORY de-risk: close the short straddle on a vol spike (either leg).

    Triggers when DVOL rises > vol_spike_pct from entry, OR ATM IV rises >
    iv_spike_pct from entry. Evaluated on every hourly snapshot while in
    position. Covers the unbounded short-gamma/vega loss.
    """
    triggers: list[str] = []
    dvol_ratio = None
    iv_ratio = None
    if dvol_entry is not None and dvol_now is not None and dvol_entry > 0:
        dvol_ratio = dvol_now / dvol_entry - 1.0
        if dvol_ratio > vol_spike_pct:
            triggers.append("dvol")
    if atm_iv_entry is not None and atm_iv_now is not None and atm_iv_entry > 0:
        iv_ratio = atm_iv_now / atm_iv_entry - 1.0
        if iv_ratio > iv_spike_pct:
            triggers.append("iv")
    return {
        "triggered": bool(triggers),
        "legs": triggers,
        "dvol_ratio": dvol_ratio,
        "iv_ratio": iv_ratio,
        "vol_spike_pct": vol_spike_pct,
        "iv_spike_pct": iv_spike_pct,
    }


# ── Margin / sizing (§4) ────────────────────────────────────────────────────
def margin_per_contract(premium: float, S0: float,
                        margin_underlying_frac: float = MARGIN_UNDERLYING_FRAC) -> float:
    """margin = premium + ~20% of underlying (conservative approx, F7)."""
    return premium + margin_underlying_frac * S0


def size_straddle(capital: float, S0: float, premium: float,
                  tail_loss_frac: float = TAIL_LOSS_FRAC,
                  margin_underlying_frac: float = MARGIN_UNDERLYING_FRAC,
                  margin_cap_frac: float = MARGIN_CAP_FRAC) -> dict:
    """Size a short straddle (spec §4.2). 1R = 1% capital; notional is the
    DEPENDENT variable; risk_usd is re-derived from ACTUAL notional.

    Returns {notional, contracts, margin_deployed, risk_usd, size_capped,
             cap_reason, tail_loss_frac}.
    """
    mpc = margin_per_contract(premium, S0, margin_underlying_frac)
    risk_notional = (CAPITAL_RISK_BUDGET * capital) / tail_loss_frac
    margin_notional = (margin_cap_frac * capital) / mpc * S0 if mpc > 0 \
        else float("inf")
    notional = min(risk_notional, margin_notional)
    contracts = notional / S0 if S0 > 0 else 0.0
    margin_deployed = contracts * mpc
    risk_usd = notional * tail_loss_frac

    rails = {"risk-budget (1% capital / tail_loss_frac)": risk_notional,
             "margin cap (MARGIN_CAP_FRAC x capital)": margin_notional}
    positive_rails = {k: v for k, v in rails.items() if v > 0}
    size_capped = notional < risk_notional - 1e-12
    if not positive_rails:
        cap_reason = "no positive capacity rails"
    elif size_capped:
        cap_reason = min(positive_rails, key=lambda k: positive_rails[k])
    else:
        cap_reason = None

    return {
        "notional": notional,
        "contracts": contracts,
        "margin_deployed": margin_deployed,
        "risk_usd": risk_usd,
        "size_capped": size_capped,
        "cap_reason": cap_reason,
        "tail_loss_frac": tail_loss_frac,
    }


# ── Cost model (§5.2) + realized vol (§2.1) ─────────────────────────────────
def option_execution_cost(S0: float, contracts: float,
                          taker_bps: float | None = None,
                          slippage_bps: float | None = None) -> float:
    """Deribit option round-trip cost (§5.2): taker + slip, x 2 legs, fail-closed
    (no maker rebate credited). Defaults sourced from fee_source's "option"
    class (exactly one fee table, US-181 F4)."""
    if taker_bps is None or slippage_bps is None:
        from fee_source import get_venue_costs  # lazy (keeps module importable)
        o = get_venue_costs()["option"]
        taker_bps = o["taker_bps"] if taker_bps is None else taker_bps
        slippage_bps = o["slippage_bps"] if slippage_bps is None else slippage_bps
    return (taker_bps + slippage_bps) / 1e4 * S0 * contracts * 2.0


def realized_vol_5m(closes, lookback_days: int = REALIZED_VOL_LOOKBACK_DAYS) -> float:
    """Annualized realized vol of the underlying from 5m closes (std of
    log-returns x sqrt(105120)) over the trailing `lookback_days`. 0.0 if < 2
    usable observations. This is the SAME quantity funding_carry computes, but
    on 5m bars rather than hourly (FLAG F11)."""
    closes = [float(c) for c in closes if c is not None]
    closes = [c for c in closes if c > 0]
    if len(closes) < 2:
        return 0.0
    lookback = min(len(closes) - 1, lookback_days * 288)  # 288 5m bars/day
    closes = closes[-(lookback + 1):]
    lr = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))]
    lr = [x for x in lr if math.isfinite(x)]
    if len(lr) < 2:
        return 0.0
    mean = sum(lr) / len(lr)
    var = sum((x - mean) ** 2 for x in lr) / (len(lr) - 1)
    return math.sqrt(var) * math.sqrt(FIVE_MIN_BARS_PER_YEAR)


# ── Threshold derivation (§2.2) — blocked until 6–12 months of history ──────
def derive_vov_threshold(records: list[dict], n_deciles: int = 10,
                         min_days: int = MIN_WINDOW_DAYS) -> dict:
    """Derive VOV_THRESHOLD from data, never a magic constant (spec §2.2).

    records: [{vov_level, forward_net_pnl}, ...] one per morning snapshot.
    Buckets days by vol-of-vol level into deciles, reports mean forward
    net_pnl per bucket, and sets the threshold at the "steamroller boundary"
    where mean forward net_pnl crosses from positive to negative.

    Returns {blocked, reason, threshold, buckets}. blocked=True (threshold=
    None) when there is < min_days of history — on 30d this is the honest result
    and the strategy stays paper-forward-hypothesis. CPCV (N=12, k=2)
    cross-validation of boundary stability is a follow-on exercised in the
    backtest stub once the minimum window is met (§2.2 step 6).
    """
    usable = [r for r in records if r.get("vov_level") is not None
              and r.get("forward_net_pnl") is not None]
    if len(usable) < min_days:
        return {
            "blocked": True,
            "reason": f"insufficient history for threshold derivation: "
                      f"{len(usable)} < {min_days} morning snapshots",
            "threshold": None,
            "buckets": [],
        }
    usable = sorted(usable, key=lambda r: r["vov_level"])
    n = len(usable)
    buckets = []
    for d in range(n_deciles):
        lo = int(d * n / n_deciles)
        hi = int((d + 1) * n / n_deciles)
        chunk = usable[lo:hi]
        if not chunk:
            continue
        vov_lo = chunk[0]["vov_level"]
        vov_hi = chunk[-1]["vov_level"]
        mean_pnl = sum(r["forward_net_pnl"] for r in chunk) / len(chunk)
        buckets.append({"decile": d, "vov_lo": vov_lo, "vov_hi": vov_hi,
                        "n": len(chunk), "mean_forward_net_pnl": mean_pnl})
    # Lowest decile with a non-positive mean forward net_pnl = the steamroller
    # boundary. Threshold = the LOWER edge (vov_lo) of that bucket — the level
    # above which forward PnL turns non-positive, so "calm" == vov_level < it.
    threshold = None
    for b in buckets:
        if b["mean_forward_net_pnl"] <= 0.0:
            threshold = b["vov_lo"]
            break
    return {
        "blocked": False,
        "reason": None,
        "threshold": threshold,
        "buckets": buckets,
    }