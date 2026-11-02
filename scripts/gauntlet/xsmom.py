"""xsmom.py — HermesForge US-182: cost-aware cross-sectional momentum (crypto).

Cross-sectional momentum over the deep daily-bar crypto universe, built to be
transaction-cost-aware: a partial-rebalance + no-trade-band construction that
moves TOWARD the inverse-vol target rather than turning the whole book over each
week, plus a binary BTC 200-DMA regime overlay and an inverse-vol risk
constitution.

FLAG RESOLUTIONS (principal-locked, do NOT re-open):
  F1  LONG-FLAT — long-only top quintile. NO short leg (moots F8).
  F2  lookback 30d, skip 1d.
  F3  weekly rebalance (7d).
  F4  quintile cut (TOP_FRAC = 0.20).
  F5  KAPPA = 0.5, BAND_FRAC = 0.25.
  F6  BTC 200-DMA binary: overlay up -> full 1.0 inverse-vol long; down -> 0.5
      long-only (DOWN_SCALE).
  F8  MOOT (long-flat, no short-leg funding to accrue).
  F9  cost = get_round_trip_bps("crypto") (= 12 bps) per unit one-way turnover,
      charged ONCE (lifetime-correct, fail-closed). NEVER re-add a per-side taker.
  F10 G3 = xsmom_g3_record (internal cost model) mirroring carry_g3_record —
      NOT literal assert_g3_gate.compute_cost_drag (which would double-count).
  F11 no leverage: GROSS_EXPOSURE_CAP = 1.0, MARGIN_CAP_FRAC = 1.0.
  F12 inverse-vol on daily closes (sqrt(365)).
  F13 provenance floor (applied by the driver, not here).

Import direction (one-way, acyclic — mirrors funding_carry.py):
  xsmom.py -> fee_source + g3_gate (MIN_TRADES / EDGE_DECAY_FLOOR only).
Read-only research: writes NO live state.
"""

from __future__ import annotations

import math
import pathlib
import sys

import numpy as np
import pandas as pd

_THIS_DIR = pathlib.Path(__file__).resolve().parent          # scripts/gauntlet
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

from g3_gate import MIN_TRADES, EDGE_DECAY_FLOOR  # noqa: E402  (reuse exact thresholds)
from fee_source import get_round_trip_bps, get_taker_bps  # noqa: E402  (single fee table)

# ── Signal constants ─────────────────────────────────────────────────────────
MOMENTUM_LOOKBACK_DAYS = 30     # [F2] primary lookback; 7/90 are sensitivity legs
MOMENTUM_SKIP_DAYS = 1          # [F2] drop the most-recent daily bar (1-day reversal dodge)

# ── Construction constants ───────────────────────────────────────────────────
TOP_FRAC = 0.20                 # [F4] top quintile is the long leg
LONG_GROSS_UP = 1.0             # [F1/F6] overlay up -> full 1.0 inverse-vol long
DOWN_SCALE = 0.5                # [F6] overlay down -> long-only at 0.5 gross
KAPPA = 0.5                     # [F5] partial-rebalance speed (fraction of drift)
BAND_FRAC = 0.25                # [F5] no-trade band width (fraction of |target|)
VOL_LOOKBACK_DAYS = 30          # [F12] realized-vol window (daily closes)
VOL_ANNUALIZATION = math.sqrt(365.0)   # daily -> annual
BTC_DMA_WINDOW = 200            # BTC 200-DMA regime overlay window
REBALANCE_PERIOD = 7            # [F3] weekly rebalance (daily is a sensitivity leg)

# ── Risk constitution (binding rails) ────────────────────────────────────────
GROSS_EXPOSURE_CAP = 1.0        # [F11] sum |w| <= 1.0, NO leverage
MAX_NAME_WEIGHT = 0.10          # no single name > 10% gross (diversification floor)
CAPITAL_RISK_BUDGET = 0.01      # 1R = 1% capital (identical to funding_carry)
MARGIN_CAP_FRAC = 1.0           # [F11] margin deployed <= 1x capital

# ── Universe floors (F7 defaults, applied by the driver) ─────────────────────
MIN_DAILY_NOTIONAL_USD = 250_000.0
MIN_VOL_GATE = 0.20

ASSET_CLASS = "crypto"


# ── 1. Momentum signal ───────────────────────────────────────────────────────
def momentum_series(closes, skip: int = MOMENTUM_SKIP_DAYS,
                    lookback: int = MOMENTUM_LOOKBACK_DAYS):
    """momentum[t] = closes[t - skip] / closes[t - lookback] - 1 (verbatim §1.1).

    The numerator is the bar SKIP back from t (the most-recent bar is dropped to
    dodge the 1-day reversal) and the denominator is LOOKBACK bars back from t,
    so with skip=1/lookback=30 the score is (P[t-1]/P[t-30] - 1). Requires
    t >= lookback; NaN where insufficient history or a non-finite price.
    """
    closes = pd.Series(closes, dtype=float)
    n = len(closes)
    vals = closes.to_numpy(dtype=float)
    out = np.full(n, np.nan)
    for t in range(lookback, n):
        num = vals[t - skip]
        den = vals[t - lookback]
        if den is not None and np.isfinite(num) and np.isfinite(den) and den > 0:
            out[t] = num / den - 1.0
    return pd.Series(out, index=closes.index)


def momentum_at(closes, skip: int = MOMENTUM_SKIP_DAYS,
                lookback: int = MOMENTUM_LOOKBACK_DAYS) -> float:
    """Scalar momentum at the most-recent computable point (for the current
    window probe). Returns nan if insufficient history."""
    s = momentum_series(closes, skip=skip, lookback=lookback)
    if s.empty:
        return float("nan")
    tail = s.dropna()
    return float(tail.iloc[-1]) if not tail.empty else float("nan")


# ── 2. Realized volatility (inverse-vol denominator) ─────────────────────────
def realized_vol_daily(closes, lookback: int = VOL_LOOKBACK_DAYS):
    """sigma_ann[t] = std( log-returns over the trailing `lookback` daily bars
    ending at t ) * sqrt(365). NaN where < 2 usable returns in the window."""
    closes = pd.Series(closes, dtype=float)
    logret = np.log(closes / closes.shift(1))
    vol = logret.rolling(window=lookback).std(ddof=1) * VOL_ANNUALIZATION
    return vol


# ── 3. Cross-section ranking ─────────────────────────────────────────────────
def cross_sectional_rank(momentums: pd.Series, top_frac: float = TOP_FRAC):
    """Rank names by momentum descending; return the top-`top_frac` names (the
    long leg). skips names with NaN momentum. Returns (long_names, all_ranked)."""
    mom = momentums.dropna()
    if mom.empty:
        return [], []
    ranked = mom.sort_values(ascending=False)
    n_long = max(1, int(round(len(ranked) * top_frac)))
    long_names = list(ranked.index[:n_long])
    return long_names, list(ranked.index)


# ── 4. Target weights (inverse-vol, normalized to leg gross) ─────────────────
def target_weights(momentums: pd.Series, vols: pd.Series, long_gross: float,
                   top_frac: float = TOP_FRAC, max_name_weight: float = MAX_NAME_WEIGHT):
    """Inverse-vol target weights for the top-quintile long leg only.

    sigma_i = vols[name]; raw = 1/sigma_i; w*_i = raw/sum(raw) * long_gross.
    Each name is then capped at max_name_weight (the diversification rail); the
    cap only ever REDUCES gross (never re-normalizes up — a 6-name quintile at a
    10% cap cannot fill a 1.0 gross, and that under-deployment is reported, not
    silently hidden). Returns (weights: dict, capped: bool)."""
    long_names, _ = cross_sectional_rank(momentums, top_frac=top_frac)
    weights: dict = {}
    if not long_names:
        return weights, False
    raw = {}
    for name in long_names:
        v = vols.get(name) if hasattr(vols, "get") else vols[name]
        try:
            v = float(v)
        except (TypeError, ValueError):
            v = float("nan")
        if np.isfinite(v) and v > 0:
            raw[name] = 1.0 / v
    if not raw:
        return weights, False
    s = sum(raw.values())
    capped = False
    for name, rw in raw.items():
        w = (rw / s) * long_gross
        if w > max_name_weight:
            w = max_name_weight
            capped = True
        weights[name] = w
    return weights, capped


# ── 5. BTC 200-DMA regime overlay ────────────────────────────────────────────
def btc_200dma_overlay(btc_close: pd.Series, t: int, window: int = BTC_DMA_WINDOW,
                       lookback_shift: int = 1) -> bool:
    """OVERLAY_UP(t) = close_BTC[t - lookback_shift] > mean(trailing `window`
    closes ending at t - lookback_shift). lookback_shift=1 avoids lookahead (uses
    data through the prior bar). False when insufficient history."""
    vals = btc_close.to_numpy(dtype=float) if hasattr(btc_close, "to_numpy") \
        else np.asarray(btc_close, dtype=float)
    idx = t - lookback_shift
    if idx - window + 1 < 0:
        return False
    window_vals = vals[idx - window + 1: idx + 1]
    if not np.all(np.isfinite(window_vals)):
        return False
    return float(vals[idx]) > float(window_vals.mean())


# ── 6. Rebalance rule (the heart of US-182, verbatim §2.2) ───────────────────
def rebalance_step(w_current, w_target, kappa: float = KAPPA,
                   band_frac: float = BAND_FRAC):
    """Apply the partial-rebalance + no-trade-band rule.

    Membership change (w_i == 0 XOR w*_i == 0): trade FULL delta immediately.
    In-leg drift (both non-zero, same sign): band + partial (KAPPA * d).
    Returns (w_new: dict, delta: dict, turnover: float)."""
    names = set(w_current) | set(w_target)
    delta: dict = {}
    for i in names:
        wc = float(w_current.get(i, 0.0))
        wt = float(w_target.get(i, 0.0))
        if wc == 0.0 and wt == 0.0:
            continue
        if wc == 0.0 or wt == 0.0:
            delta[i] = wt - wc                      # membership change -> full
        else:
            d = wt - wc
            band = band_frac * abs(wt)
            if abs(d) <= band:
                delta[i] = 0.0                       # no-trade band
            else:
                delta[i] = kappa * d                 # partial move toward target
    w_new = dict(w_current)
    for i, d in delta.items():
        w_new[i] = w_new.get(i, 0.0) + d
    turnover = float(sum(abs(d) for d in delta.values()))
    return w_new, delta, turnover


# ── 7. Risk constitution / sizing ────────────────────────────────────────────
def size_book(capital: float, weights: dict, gross_cap: float = GROSS_EXPOSURE_CAP,
              margin_cap_frac: float = MARGIN_CAP_FRAC,
              max_name_weight: float = MAX_NAME_WEIGHT) -> dict:
    """Apply the binding rails to a signed-weight book and report the deployment.

    Returns {weights, notional_per_name, gross_notional, net_notional,
             margin_deployed, size_capped, cap_reason, risk_usd}.

    CRITICAL INVARIANT (§4.2): if any rail scales a weight down, the reduction is
    recorded as size_capped with the binding reason. risk_usd is the FIXED 1R
    unit = CAPITAL_RISK_BUDGET * capital (1% capital) — the labelled R unit the
    G3 record divides by (§5.3) — never silently shrunk."""
    w = dict(weights)
    cap_reason = None
    # name cap
    for i, v in list(w.items()):
        if abs(v) > max_name_weight:
            w[i] = math.copysign(max_name_weight, v)
            cap_reason = "name weight cap"
    gross_notional = sum(abs(v) for v in w.values()) * capital
    # gross cap
    if gross_notional > gross_cap * capital + 1e-9:
        scale = (gross_cap * capital) / gross_notional
        w = {i: v * scale for i, v in w.items()}
        gross_notional = sum(abs(v) for v in w.values()) * capital
        cap_reason = "gross notional cap"
    # margin cap
    margin_deployed = gross_notional
    if margin_deployed > margin_cap_frac * capital:
        cap_reason = "margin cap"
    notional = {i: v * capital for i, v in w.items()}
    net_notional = sum(notional.values())
    return {
        "weights": w,
        "notional_per_name": notional,
        "gross_notional": gross_notional,
        "net_notional": net_notional,
        "margin_deployed": margin_deployed,
        "size_capped": cap_reason is not None,
        "cap_reason": cap_reason,
        "risk_usd": CAPITAL_RISK_BUDGET * capital,
    }


# ── 8. Simulation ────────────────────────────────────────────────────────────
_DEFAULT_PARAMS = {
    "capital": 1_000_000.0,
    "kappa": KAPPA,
    "band_frac": BAND_FRAC,
    "rebalance_period": REBALANCE_PERIOD,
    "lookback": MOMENTUM_LOOKBACK_DAYS,
    "skip": MOMENTUM_SKIP_DAYS,
    "top_frac": TOP_FRAC,
    "long_gross_up": LONG_GROSS_UP,
    "down_scale": DOWN_SCALE,
    "max_name_weight": MAX_NAME_WEIGHT,
    "vol_lookback": VOL_LOOKBACK_DAYS,
}

_EPISODE_COLUMNS = ["reb_ts", "overlay_up", "regime_label", "gross_return",
                    "turnover", "cost_frac", "net_return", "net_r"]


def _correlate_returns(sym: np.ndarray, btc: np.ndarray, window: int = 30) -> float:
    """Rolling 30d BTC beta (OLS) at the latest overlapping window."""
    sym = sym[np.isfinite(sym)]
    n = min(len(sym), len(btc))
    if n < 2:
        return 0.0
    s = sym[-window:]
    b = btc[-window:]
    nn = min(len(s), len(b))
    s, b = s[-nn:], b[-nn:]
    if nn < 2:
        return 0.0
    sv = np.var(b)
    if sv == 0:
        return 0.0
    return float(np.cov(s, b)[0, 1] / sv)


def simulate_xsmom(close_panel: pd.DataFrame, btc_close: pd.Series,
                   params: dict | None = None) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Daily walk, weekly rebalance, cost on turnover (§5.2).

    close_panel: DataFrame[T x N] of daily closes (index = ms timestamps), with
                 forward-filled gaps (caller responsibility). NaN = missing.
    btc_close:   Series indexed to the same timestamps as close_panel.

    Returns (nav_df, episodes_df, diagnostics):
      nav_df      — T rows {ts, gross_ret, cost_frac, net_ret, nav, gross_w}.
      episodes_df — one row per holding period (_EPISODE_COLUMNS).
      diagnostics — {n_rebalances, avg_turnover, avg_gross_w, names_observed}.
    """
    p = dict(_DEFAULT_PARAMS)
    if params:
        p.update(params)

    capital = float(p["capital"])
    kappa = float(p["kappa"])
    band_frac = float(p["band_frac"])
    rebal = int(p["rebalance_period"])
    top_frac = float(p["top_frac"])
    long_gross_up = float(p["long_gross_up"])
    down_scale = float(p["down_scale"])
    max_name_w = float(p["max_name_weight"])
    vol_lb = int(p["vol_lookback"])

    names = list(close_panel.columns)
    n_names = len(names)
    if n_names == 0:
        empty = pd.DataFrame(columns=_EPISODE_COLUMNS)
        return pd.DataFrame(), empty, {"n_rebalances": 0, "avg_turnover": 0.0,
                                       "avg_gross_w": 0.0, "names_observed": 0}

    ts = close_panel.index.to_numpy()
    C = close_panel.to_numpy(dtype=float).T          # (N, T)
    btc = btc_close.reindex(close_panel.index).to_numpy(dtype=float)

    rtb = get_round_trip_bps(ASSET_CLASS)            # 12.0 bps (single fee table)
    T = len(ts)

    # Precompute momentum / vol (indexed at t; data through t-1 via skip).
    mom = np.full((n_names, T), np.nan)
    vol = np.full((n_names, T), np.nan)
    for i in range(n_names):
        m = momentum_series(pd.Series(C[i]), skip=int(p["skip"]),
                            lookback=int(p["lookback"])).to_numpy(dtype=float)
        mom[i] = m
        v = realized_vol_daily(pd.Series(C[i]), lookback=vol_lb).to_numpy(dtype=float)
        vol[i] = v

    # BTC daily returns (for beta clustering input) + 30d return (regime).
    btc_ret = np.full(T, np.nan)
    btc_ret[1:] = btc[1:] / btc[:-1] - 1.0

    start = BTC_DMA_WINDOW + 1     # need DMA(200) + momentum(30) + vol(30) history

    # weights held (length n_names)
    w = np.zeros(n_names)
    nav = 1.0
    nav_rows = []
    episodes = []
    diag_names = set()

    # open-episode accumulator
    ep_open = None               # dict with reb_ts, overlay_up, regime, turnover, cost_frac, gross_cum
    # running per-episode geometric gross
    ep_gross = None

    def _close_episode():
        nonlocal ep_open, ep_gross
        if ep_gross is None:
            return None
        gross_return = math.exp(ep_gross) - 1.0 if np.isfinite(ep_gross) else ep_gross
        turnover = ep_open["turnover"]
        cost_frac = ep_open["cost_frac"]
        net_return = gross_return - cost_frac
        net_r = net_return / CAPITAL_RISK_BUDGET if CAPITAL_RISK_BUDGET > 0 else 0.0
        row = {"reb_ts": ep_open["reb_ts"], "overlay_up": ep_open["overlay_up"],
               "regime_label": ep_open["regime"], "gross_return": gross_return,
               "turnover": turnover, "cost_frac": cost_frac,
               "net_return": net_return, "net_r": net_r}
        ep_open = None
        ep_gross = None
        return row

    for t in range(start, T):
        # daily gross portfolio return using weights held entering day t
        with np.errstate(divide="ignore", invalid="ignore"):
            r = C[:, t] / C[:, t - 1] - 1.0
        r[~np.isfinite(r)] = 0.0
        gross_t = float(np.dot(w, r))

        cost_t = 0.0
        is_rebal = ((t - start) % rebal == 0)
        turnover_t = 0.0
        overlay_up = False
        if is_rebal:
            # close prior episode first (its holding period just ended at t-1)
            closed = _close_episode()
            if closed is not None:
                episodes.append(closed)

            overlay_up = btc_200dma_overlay(pd.Series(btc), t)
            gross_target = long_gross_up if overlay_up else long_gross_up * down_scale
            moms = pd.Series(mom[:, t], index=names)
            vols = pd.Series(vol[:, t], index=names)
            wstar_dict, _ = target_weights(moms, vols, gross_target,
                                           top_frac=top_frac, max_name_weight=max_name_w)
            wstar = np.zeros(n_names)
            for name, wt in wstar_dict.items():
                wstar[names.index(name)] = wt
            w_dict = {names[i]: w[i] for i in range(n_names) if w[i] != 0.0}
            w_new, _, turnover_t = rebalance_step(
                w_dict, wstar_dict, kappa=kappa, band_frac=band_frac)
            w = np.zeros(n_names)
            for name, wv in w_new.items():
                w[names.index(name)] = wv
            diag_names.update(wstar_dict.keys())
            cost_t = rtb / 1e4 * turnover_t

            # BTC 30d regime label (bull/bear/neutral) at t-1
            btc30 = (btc[t - 1] / btc[t - 30] - 1.0) if np.isfinite(btc[t - 1]) and np.isfinite(btc[t - 30]) and btc[t - 30] > 0 else 0.0
            regime = "bull" if btc30 > 0.02 else ("bear" if btc30 < -0.02 else "neutral")
            ep_open = {"reb_ts": int(ts[t]), "overlay_up": overlay_up,
                       "regime": regime, "turnover": turnover_t,
                       "cost_frac": cost_t}
            ep_gross = 0.0

        if ep_gross is not None:
            ep_gross += math.log1p(gross_t)

        net_t = gross_t - cost_t
        nav *= (1.0 + net_t)
        nav_rows.append((int(ts[t]), gross_t, cost_t, net_t, nav,
                         float(np.abs(w).sum()), turnover_t, overlay_up))

    # close trailing episode
    closed = _close_episode()
    if closed is not None:
        episodes.append(closed)

    nav_df = pd.DataFrame(nav_rows, columns=["ts", "gross_ret", "cost_frac",
                                             "net_ret", "nav", "gross_w",
                                             "turnover", "overlay_up"])
    eps_df = pd.DataFrame(episodes, columns=_EPISODE_COLUMNS) if episodes else \
        pd.DataFrame(columns=_EPISODE_COLUMNS)

    diag = {
        "n_rebalances": len(episodes),
        "avg_turnover": float(nav_df["turnover"].mean()) if not nav_df.empty else 0.0,
        "avg_gross_w": float(nav_df["gross_w"].mean()) if not nav_df.empty else 0.0,
        "names_observed": len(diag_names),
    }
    return nav_df, eps_df, diag


# ── 9. G3 record (mirror carry_g3_record — internal cost model, no double-count)
def _pf(rs) -> float:
    gains = sum(r for r in rs if r > 0)
    losses = abs(sum(r for r in rs if r < 0))
    return gains / losses if losses > 0 else (float("inf") if gains > 0 else 0.0)


def xsmom_g3_record(episodes: pd.DataFrame) -> dict:
    """Apply G3 gate SEMANTICS with the strategy's OWN cost model (§5.3, F10).

    Unit of observation = one rebalance holding period. R = net period return /
    risk_usd (= 1% capital). The strategy's 12-bps turnover cost is ALREADY
    netted internally, so this computes:
      optimistic_r  = gross period return / risk_usd (zero cost, diagnostic only)
      realistic_r   = (gross - turnover*12bps) / risk_usd        (the cost-aware net)
      pessimistic_r = realistic_r - (taker_bps/1e4 * turnover) / risk_usd
                      (one extra adverse taker leg per side = worst-fill stand-in)

    Returns {n, optimistic_mean_r, realistic_mean_r, pessimistic_pf,
             edge_decay_ratio, passed, reasons, avg_turnover, cost_bps, r_unit}.
    """
    if episodes is None or episodes.empty:
        return {"n": 0, "optimistic_mean_r": 0.0, "realistic_mean_r": 0.0,
                "pessimistic_pf": 0.0, "edge_decay_ratio": None, "passed": False,
                "avg_turnover": 0.0, "cost_bps": 0.0,
                "reasons": ["no episodes"], "r_unit": "1R = 1% capital"}

    n = len(episodes)
    gross = episodes["gross_return"].astype(float).to_numpy()
    turnover = episodes["turnover"].astype(float).to_numpy()
    rtb = get_round_trip_bps(ASSET_CLASS)
    taker = get_taker_bps(ASSET_CLASS)
    budget = CAPITAL_RISK_BUDGET

    opt_r = gross / budget
    cost_frac = rtb / 1e4 * turnover
    real_r = (gross - cost_frac) / budget
    pess_r = real_r - (taker / 1e4 * turnover) / budget

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
        "avg_turnover": round(float(turnover.mean()), 6),
        "cost_bps": rtb,
        "r_unit": "1R = 1% capital",
    }


# ── 10. Net Sharpe (per-episode, annualized to weekly) ───────────────────────
def net_sharpe(episodes: pd.DataFrame, periods_per_year: float = 52.0) -> float:
    """Annualized Sharpe of per-episode net_r (weekly -> *sqrt(52))."""
    if episodes is None or episodes.empty:
        return 0.0
    rs = episodes["net_r"].astype(float).to_numpy()
    sd = float(np.std(rs))
    if sd == 0 or not np.isfinite(sd):
        return 0.0
    return float(np.mean(rs) / sd * math.sqrt(periods_per_year))


def _annualized_sharpe_of(rs: np.ndarray, periods_per_year: float) -> float:
    rs = rs[np.isfinite(rs)]
    if len(rs) < 2:
        return 0.0
    sd = float(np.std(rs))
    if sd == 0:
        return 0.0
    return float(np.mean(rs) / sd * math.sqrt(periods_per_year))


# ── 11. Regime + beta-cluster partition (§5.4) ───────────────────────────────
def partition_regime(episodes: pd.DataFrame) -> dict:
    """Partition episode net_r by overlay (up/down) and BTC 30d regime
    (bull/bear/neutral) — reported, not gated here."""
    if episodes is None or episodes.empty:
        return {"overlay_up": {"n": 0}, "overlay_down": {"n": 0},
                "bull": {"n": 0}, "bear": {"n": 0}, "neutral": {"n": 0}}
    out = {}
    for key in ("overlay_up", "overlay_down"):
        sub = episodes[episodes["overlay_up"] == (key == "overlay_up")]
        rs = sub["net_r"].astype(float).tolist()
        out[key] = {"n": len(rs), "mean_r": round(sum(rs) / len(rs), 4) if rs else 0.0,
                    "pf": round(_pf(rs), 4) if rs else 0.0}
    for reg in ("bull", "bear", "neutral"):
        sub = episodes[episodes["regime_label"] == reg]
        rs = sub["net_r"].astype(float).tolist()
        out[reg] = {"n": len(rs), "mean_r": round(sum(rs) / len(rs), 4) if rs else 0.0,
                    "pf": round(_pf(rs), 4) if rs else 0.0}
    return out


def name_btc_betas(close_panel: pd.DataFrame, btc_close: pd.Series,
                   window: int = 30) -> dict:
    """Rolling 30d BTC beta per name (OLS of daily returns vs BTC)."""
    btc = btc_close.reindex(close_panel.index).to_numpy(dtype=float)
    btc_ret = np.full(len(btc), np.nan)
    if len(btc) > 1:
        btc_ret[1:] = btc[1:] / btc[:-1] - 1.0
    out = {}
    for name in close_panel.columns:
        c = close_panel[name].to_numpy(dtype=float)
        r = np.full(len(c), np.nan)
        if len(c) > 1:
            r[1:] = c[1:] / c[:-1] - 1.0
        out[name] = _correlate_returns(r, btc_ret, window=window)
    return out


def beta_cluster_pnl(weighted_episode_pnl_by_name: dict, betas: dict,
                     low: float = 0.7, high: float = 1.3) -> dict:
    """Attribute per-name P&L to beta clusters {low, med, high} by rolling BTC
    beta thresholds. weighted_episode_pnl_by_name: {name: total net return}. """
    clusters = {"low": 0.0, "med": 0.0, "high": 0.0}
    for name, pnl in weighted_episode_pnl_by_name.items():
        b = betas.get(name, 0.0)
        key = "low" if b < low else ("high" if b > high else "med")
        clusters[key] += pnl
    return clusters