"""
Tests for xsmom.py — the US-182 cost-aware cross-sectional momentum strategy.

Golden-vector tests for the momentum signal, realized vol, cross-sectional rank,
inverse-vol target weights, the BTC 200-DMA overlay, the rebalance rule (the
membership-change-full / band+partial distinction), sizing (1R == 1% capital),
the G3 record, and a synthetic end-to-end simulate smoke test.
"""

import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd

import xsmom as x


# ── 1. momentum signal ──────────────────────────────────────────────────────
def test_momentum_flat_series_is_zero():
    flat = pd.Series([1.0] * 40)
    m = x.momentum_series(flat)
    tail = m.dropna()
    assert len(tail) > 0
    assert abs(float(tail.iloc[-1]) - 0.0) < 1e-12
    assert abs(x.momentum_at(flat) - 0.0) < 1e-12


def test_momentum_linear_series_golden():
    # closes = 1..32 (index + 1). At t=30: P[t-1]=30, P[t-30]=1 -> 29.0
    closes = pd.Series(np.arange(1.0, 33.0))
    m = x.momentum_series(closes)
    assert abs(float(m.iloc[30]) - 29.0) < 1e-9


def test_momentum_skip_convention():
    # skip=1 means the most-recent bar is NOT the numerator.
    closes = pd.Series([10.0, 10.0, 20.0])  # length 3; lookback=2 -> t=2
    m = x.momentum_series(closes, skip=1, lookback=2)
    # t=2: num = closes[1]=10, den = closes[0]=10 -> 0.0 (the +100% jump at
    # clique[2] is the SKIPPED bar, so it must NOT show up).
    assert abs(float(m.iloc[2]) - 0.0) < 1e-12


# ── 2. realized vol ─────────────────────────────────────────────────────────
def test_vol_constant_series_is_zero():
    c = pd.Series([100.0] * 60)  # constant price -> zero log returns
    v = x.realized_vol_daily(c)
    tail = v.dropna()
    assert abs(float(tail.iloc[-1])) < 1e-9


# ── 3. cross-sectional rank ─────────────────────────────────────────────────
def test_rank_splits_descending():
    moms = pd.Series({"SLOW": 0.1, "FAST": 0.5, "MID": 0.2})
    long_names, ranked = x.cross_sectional_rank(moms, top_frac=0.34)  # top 1 of 3
    assert ranked[0] == "FAST"
    assert long_names == ["FAST"]


def test_rank_drops_nan():
    moms = pd.Series({"A": 0.1, "B": np.nan, "C": 0.2})
    long_names, ranked = x.cross_sectional_rank(moms, top_frac=0.5)
    assert "B" not in ranked
    assert long_names == ["C"]


# ── 4. target weights ───────────────────────────────────────────────────────
def test_target_weights_sum_to_gross():
    moms = pd.Series({"A": 0.3, "B": 0.2, "C": 0.1})
    vols = pd.Series({"A": 0.5, "B": 0.5, "C": 0.5})
    w, capped = x.target_weights(moms, vols, long_gross=0.5, top_frac=1.0,
                                 max_name_weight=1.0)
    assert abs(sum(w.values()) - 0.5) < 1e-9
    assert not capped
    assert abs(w["A"] - 0.5 / 3) < 1e-9


def test_target_weights_name_cap_binds():
    moms = pd.Series({"A": 0.3, "B": 0.2, "C": 0.1})
    vols = pd.Series({"A": 0.5, "B": 0.6, "C": 0.7})
    # inverse-vol favors A -> A > 10% -> capped.
    w, capped = x.target_weights(moms, vols, long_gross=1.0, top_frac=1.0,
                                 max_name_weight=0.10)
    assert capped
    assert max(w.values()) <= 0.10 + 1e-12


# ── 5. BTC 200-DMA overlay ──────────────────────────────────────────────────
def test_overlay_flips_at_crossing():
    # 200 bars at 100 then 50 bars at 200 -> overlay up at the last bar.
    up = pd.Series([100.0] * 200 + [200.0] * 50)
    assert x.btc_200dma_overlay(up, t=249) is True
    # 200 bars at 200 then 50 bars at 100 -> overlay down at the last bar.
    down = pd.Series([200.0] * 200 + [100.0] * 50)
    assert x.btc_200dma_overlay(down, t=249) is False
    # flat series: close == DMA (strict >) -> not up.
    flat = pd.Series([100.0] * 201)
    assert x.btc_200dma_overlay(flat, t=200) is False


# ── 6. rebalance rule ───────────────────────────────────────────────────────
def test_membership_change_trades_full():
    w_new, delta, turnover = x.rebalance_step({}, {"A": 0.3}, kappa=0.5,
                                              band_frac=0.25)
    assert abs(delta["A"] - 0.3) < 1e-12
    assert abs(turnover - 0.3) < 1e-12


def test_inleg_drift_under_band_trades_zero():
    w_new, delta, turnover = x.rebalance_step({"A": 0.30}, {"A": 0.31},
                                              kappa=0.5, band_frac=0.25)
    assert abs(delta["A"] - 0.0) < 1e-12
    assert turnover == 0.0


def test_inleg_drift_over_band_partial():
    w_new, delta, turnover = x.rebalance_step({"A": 0.30}, {"A": 0.50},
                                              kappa=0.5, band_frac=0.25)
    # band = 0.25*0.5 = 0.125; d=0.20 > band -> kappa*d = 0.10
    assert abs(delta["A"] - 0.10) < 1e-12
    assert abs(turnover - 0.10) < 1e-12
    assert abs(w_new["A"] - 0.40) < 1e-12


# ── 7. sizing ───────────────────────────────────────────────────────────────
def test_size_book_risk_unit_is_1pct_capital():
    sz = x.size_book(1_000_000.0, {"A": 0.3, "B": 0.2}, max_name_weight=1.0)
    assert abs(sz["risk_usd"] - 10_000.0) < 1e-6   # 1% of $1M
    assert sz["size_capped"] is False
    assert abs(sz["gross_notional"] - 500_000.0) < 1e-6


def test_size_book_gross_cap_binds():
    sz = x.size_book(1_000_000.0, {"A": 0.8, "B": 0.8}, gross_cap=1.0,
                     max_name_weight=1.0)
    assert sz["size_capped"] is True
    assert abs(sz["gross_notional"] - 1_000_000.0) < 1e-6


# ── 8. G3 record ────────────────────────────────────────────────────────────
def test_xsmom_g3_record_no_episodes():
    r = x.xsmom_g3_record(pd.DataFrame(columns=x._EPISODE_COLUMNS))
    assert r["passed"] is False
    assert "no episodes" in r["reasons"]


def test_xsmom_g3_record_insufficient_data():
    eps = pd.DataFrame([{"gross_return": 0.0, "turnover": 0.0, "cost_frac": 0.0,
                         "net_return": 0.0, "net_r": 0.0}])
    r = x.xsmom_g3_record(eps)
    assert any("INSUFFICIENT DATA" in s for s in r["reasons"])
    assert r["passed"] is False


# ── 9. synthetic end-to-end simulate ────────────────────────────────────────
def test_simulate_runs_and_produces_episodes():
    rng = np.random.default_rng(7)
    T = 500
    idx = pd.RangeIndex(T)
    # BTC trending up (overlay up regime most of the run)
    btc = pd.Series(100.0 * np.exp(np.cumsum(rng.normal(0.0005, 0.02, T))), index=idx)
    names = ["UP1", "UP2", "DOWN1", "DOWN2"]
    data = {}
    data["UP1"] = btc * np.exp(np.cumsum(rng.normal(0.003, 0.02, T)))   # strong uptrend
    data["UP2"] = btc * np.exp(np.cumsum(rng.normal(0.002, 0.02, T)))
    data["DOWN1"] = 100 * np.exp(-np.cumsum(rng.normal(0.003, 0.02, T)))  # downtrend
    data["DOWN2"] = 100 * np.exp(-np.cumsum(rng.normal(0.002, 0.02, T)))
    panel = pd.DataFrame(data, index=idx)

    nav, eps, diag = x.simulate_xsmom(panel, btc)
    assert not nav.empty
    assert len(eps) >= 10             # plenty of weekly rebalances over 500 days
    assert diag["n_rebalances"] == len(eps)
    assert {"gross_return", "turnover", "net_r"} <= set(eps.columns)
    # NAV must remain finite.
    assert np.isfinite(nav["nav"].iloc[-1])