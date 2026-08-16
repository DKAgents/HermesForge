#!/usr/bin/env python3
"""
test_market_structure.py
========================
HermesForge US-115: test suite for market_structure.py.

Covers the design doc's tests:
    T1-T15  synthetic-data unit tests
    L1-L3   look-ahead regression tests (the critical suite)
    P1-P3   property / invariant tests

Runnable two ways:
    python -m pytest test_market_structure.py
    python test_market_structure.py            (stdlib assert runner)

All tests use hand-crafted synthetic DataFrames with known pivots so outcomes
are exact. The synthetic data uses FLAT OHLC at `base` with clean valleys/peaks
(only the pivot bar's low/high differs) and a CONSTANT ATR Series passed
explicitly, so Wilder-ATR warmup and swing-bar true-range pollution cannot
destabilise the assertions. Keeping close flat also keeps the EMA flat, so the
EMA dynamic-support branch never fires spuriously and the swing-low level is
the sole support (deterministic).

Run with MARKET_STRUCTURE_DEBUG=1 (forced on below) to enable the
pivot-confirmation assertion guard inside the module.
"""

import os
import sys
import unittest

import numpy as np
import pandas as pd

# Ensure sibling import works regardless of cwd.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import market_structure as ms  # noqa: E402

# Enable the debug-mode pivot-confirmation assertions for the whole suite.
os.environ["MARKET_STRUCTURE_DEBUG"] = "1"
ms._DEBUG = True


# ---------------------------------------------------------------------------
# Synthetic-data builders
# ---------------------------------------------------------------------------

def _idx(n):
    """Integer positional index 0..n-1."""
    return pd.RangeIndex(start=0, stop=n, step=1)


def struct_df(n, swing_lows=None, swing_highs=None, base=100.0):
    """Flat OHLC at `base` with clean valleys (swing lows) / peaks (swing highs).

    Only the pivot bar's low/high differs; everything else is flat at `base`.
    Close stays flat -> EMA stays flat -> EMA dynamic-support branch never fires,
    so the swing-low level is the sole support (deterministic). The real Wilder
    ATR of this df is ~0; tests that need ATR pass a CONSTANT ATR Series
    explicitly so values are exact.
    """
    h = np.full(n, base, dtype=float)
    l = np.full(n, base, dtype=float)
    c = np.full(n, base, dtype=float)
    o = np.full(n, base, dtype=float)
    if swing_lows:
        for p, val in swing_lows.items():
            l[p] = float(val)  # val < base -> clean valley (neighbors at base)
    if swing_highs:
        for p, val in swing_highs.items():
            h[p] = float(val)  # val > base -> clean peak (neighbors at base)
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c}, index=_idx(n))


def const_atr(n, val):
    """A constant ATR Series (so test stops/targets are exact)."""
    return pd.Series([float(val)] * n, index=_idx(n))


def set_bar(df, i, opn=None, high=None, low=None, close=None):
    """Override individual OHLC fields at bar i (for touches / gaps)."""
    if opn is not None:
        df.iloc[i, df.columns.get_loc("open")] = float(opn)
    if high is not None:
        df.iloc[i, df.columns.get_loc("high")] = float(high)
    if low is not None:
        df.iloc[i, df.columns.get_loc("low")] = float(low)
    if close is not None:
        df.iloc[i, df.columns.get_loc("close")] = float(close)


# ---------------------------------------------------------------------------
# T1-T15: synthetic unit tests
# ---------------------------------------------------------------------------

class TestConfirmedPivots(unittest.TestCase):
    """T1 - confirmed-pivot guard (US-114 lesson)."""

    def test_t1_confirmed_pivot_guard(self):
        # A swing low at bar 10 with PIVOT_DISTANCE=5: find_peaks(distance=5)
        # needs 5 bars on each side, so it is only knowable at bar 15.
        n = 40
        df = struct_df(n, swing_lows={10: 90.0}, base=100.0)
        # Not yet confirmed at bar 14.
        pivs_14 = ms._confirmed_pivots(df, as_of_idx=14, kind="low",
                                       pivot_distance=5, lookback=None)
        self.assertNotIn(10, pivs_14,
                         "pivot at 10 must be unknown until bar 15 (US-114)")
        # Confirmed at bar 15.
        pivs_15 = ms._confirmed_pivots(df, as_of_idx=15, kind="low",
                                       pivot_distance=5, lookback=None)
        self.assertIn(10, pivs_15,
                      "pivot at 10 must be confirmed at bar 15")


class TestComputeStructureStop(unittest.TestCase):
    """T2-T5 - compute_structure_stop long cases (flat OHLC + constant ATR)."""

    def test_t2_stop_normal_long(self):
        # entry=100, confirmed swing low at 95, ATR=2 -> stop = 95 - 0.5*2 = 94.
        # max_atr=4.0 so the cap (max_atr*ATR=8) does NOT clip risk=6.
        n = 60
        df = struct_df(n, swing_lows={20: 95.0}, base=100.0)
        atr = const_atr(n, 2.0)
        stop = ms.compute_structure_stop(
            df, decision_idx=40, direction="long", entry_price=100.0,
            max_atr=4.0, min_atr=0.5, lookback=20, pivot_distance=5,
            atr=atr, buffer_atr=0.5)
        self.assertAlmostEqual(stop, 94.0, places=6)

    def test_t3_stop_cap_long(self):
        # entry=100, nearest confirmed swing low at 80, ATR=4, max_atr=2.0.
        # struct stop = 80 - 0.5*4 = 78 -> risk=22 > max_atr*ATR=8 -> cap to 92.
        n = 60
        df = struct_df(n, swing_lows={20: 80.0}, base=100.0)
        atr = const_atr(n, 4.0)
        stop = ms.compute_structure_stop(
            df, decision_idx=40, direction="long", entry_price=100.0,
            max_atr=2.0, min_atr=0.5, lookback=20, pivot_distance=5,
            atr=atr, buffer_atr=0.5)
        self.assertAlmostEqual(stop, 92.0, places=6)

    def test_t4_stop_no_structure_long(self):
        # No confirmed swing low below entry -> ATR fallback = entry - max_atr*ATR.
        n = 60
        df = struct_df(n, base=100.0)
        atr = const_atr(n, 2.0)
        stop = ms.compute_structure_stop(
            df, decision_idx=40, direction="long", entry_price=100.0,
            max_atr=2.0, min_atr=0.5, lookback=20, pivot_distance=5,
            atr=atr, buffer_atr=0.5)
        self.assertAlmostEqual(stop, 96.0, places=6)

    def test_t5_stop_floor_long(self):
        # swing low at 99.5 (very close to entry 100), buffer_atr=0 so the
        # structural stop = 99.5 -> risk = 0.5 < min_atr*ATR = 1.0 -> floor
        # widens to entry - min_atr*ATR = 100 - 1.0 = 99.
        n = 60
        df = struct_df(n, swing_lows={20: 99.5}, base=100.0)
        atr = const_atr(n, 2.0)
        stop = ms.compute_structure_stop(
            df, decision_idx=40, direction="long", entry_price=100.0,
            max_atr=2.0, min_atr=0.5, lookback=20, pivot_distance=5,
            atr=atr, buffer_atr=0.0)  # no buffer -> clean floor test
        self.assertAlmostEqual(stop, 99.0, places=6,
                               msg="floor should widen a too-tight stop to 99")


class TestComputeNaturalTarget(unittest.TestCase):
    """T6-T9 - compute_natural_target (flat OHLC + constant ATR)."""

    def test_t6_target_meets_min_rr_long(self):
        # entry=100, stop=95 (risk=5), confirmed swing high at 108 -> R=1.6>=1.5.
        n = 60
        df = struct_df(n, swing_highs={20: 108.0}, base=100.0)
        atr = const_atr(n, 4.0)
        tgt = ms.compute_natural_target(
            df, decision_idx=40, direction="long", entry_price=100.0,
            stop_price=95.0, min_rr=1.5, lookback=50, pivot_distance=5,
            atr=atr, atr_target_mult=2.5)
        self.assertIsNotNone(tgt)
        self.assertAlmostEqual(tgt, 108.0, places=6)

    def test_t7_target_skip_too_close_take_next(self):
        # swing highs at 102 (R=0.4) and 110 (R=2.0), risk=5 -> target=110.
        n = 60
        df = struct_df(n, swing_highs={20: 102.0, 30: 110.0}, base=100.0)
        atr = const_atr(n, 4.0)
        tgt = ms.compute_natural_target(
            df, decision_idx=45, direction="long", entry_price=100.0,
            stop_price=95.0, min_rr=1.5, lookback=50, pivot_distance=5,
            atr=atr, atr_target_mult=2.5)
        self.assertAlmostEqual(tgt, 110.0, places=6)

    def test_t8_target_atr_fallback_long(self):
        # No confirmed swing high above entry. ATR=4, atr_target_mult=2.5 ->
        # atr_target = 100 + 10 = 110. risk=5 -> R=2.0 >= 1.5 -> target=110.
        n = 60
        df = struct_df(n, base=100.0)
        atr = const_atr(n, 4.0)
        tgt = ms.compute_natural_target(
            df, decision_idx=40, direction="long", entry_price=100.0,
            stop_price=95.0, min_rr=1.5, lookback=50, pivot_distance=5,
            atr=atr, atr_target_mult=2.5)
        self.assertAlmostEqual(tgt, 110.0, places=6)

    def test_t9_target_atr_fallback_fails_min_rr(self):
        # risk=10, ATR=2 -> atr_target = 100+5=105 -> R=0.5 < 1.5 -> None.
        n = 60
        df = struct_df(n, base=100.0)
        atr = const_atr(n, 2.0)
        tgt = ms.compute_natural_target(
            df, decision_idx=40, direction="long", entry_price=100.0,
            stop_price=90.0, min_rr=1.5, lookback=50, pivot_distance=5,
            atr=atr, atr_target_mult=2.5)
        self.assertIsNone(tgt, "ATR fallback below min_rr must return None")


class TestComputePullbackEntry(unittest.TestCase):
    """T10-T13 - compute_pullback_entry long cases.

    Support is a confirmed swing low at bar 10 (value 95). Signal at bar 30
    (close=100, flat). Flat OHLC => EMA flat => not a support => sole
    support = 95. Wait window bars 31..35 have low=100 > 95 (no false touch)
    unless we sculpt a touch.
    """

    SIGNAL_IDX = 30
    SUPPORT = 95.0

    def _df(self, n=45, swing_low_bar=10):
        return struct_df(n, swing_lows={swing_low_bar: self.SUPPORT}, base=100.0)

    def test_t10_pullback_touch_long(self):
        # support=95, bar signal+3 has low=94 -> entry=95, entry_idx=signal+3.
        df = self._df()
        set_bar(df, self.SIGNAL_IDX + 3, opn=100.0, high=100.0, low=94.0, close=95.5)
        entry_price, entry_idx = ms.compute_pullback_entry(
            df, signal_idx=self.SIGNAL_IDX, direction="long", max_wait_bars=5,
            pivot_distance=5, ema_span=20, fallback="signal")
        self.assertAlmostEqual(entry_price, 95.0, places=6)
        self.assertEqual(entry_idx, self.SIGNAL_IDX + 3)

    def test_t11_pullback_gap_fill_long(self):
        # bar signal+3 opens at 93 (below support 95) -> fill at open 93.
        df = self._df()
        set_bar(df, self.SIGNAL_IDX + 3, opn=93.0, high=94.0, low=92.0, close=93.5)
        entry_price, entry_idx = ms.compute_pullback_entry(
            df, signal_idx=self.SIGNAL_IDX, direction="long", max_wait_bars=5,
            pivot_distance=5, ema_span=20, fallback="signal")
        self.assertAlmostEqual(entry_price, 93.0, places=6,
                               msg="gap-below-limit must fill at the open")
        self.assertEqual(entry_idx, self.SIGNAL_IDX + 3)

    def test_t12_pullback_no_touch_fallback_signal(self):
        # No pullback touch -> fallback="signal" -> (close[signal], signal).
        df = self._df()
        entry_price, entry_idx = ms.compute_pullback_entry(
            df, signal_idx=self.SIGNAL_IDX, direction="long", max_wait_bars=5,
            pivot_distance=5, ema_span=20, fallback="signal")
        self.assertEqual(entry_idx, self.SIGNAL_IDX)
        self.assertAlmostEqual(entry_price, float(df["close"].iloc[self.SIGNAL_IDX]),
                               places=6)

    def test_t13_pullback_no_touch_fallback_window_end(self):
        # No touch -> fallback="window_end" -> (close[signal+5], signal+5).
        max_wait = 5
        n = self.SIGNAL_IDX + max_wait + 5
        df = self._df(n=n)
        entry_price, entry_idx = ms.compute_pullback_entry(
            df, signal_idx=self.SIGNAL_IDX, direction="long",
            max_wait_bars=max_wait, pivot_distance=5, ema_span=20,
            fallback="window_end")
        self.assertEqual(entry_idx, self.SIGNAL_IDX + max_wait)
        self.assertAlmostEqual(entry_price,
                              float(df["close"].iloc[self.SIGNAL_IDX + max_wait]),
                              places=6)


class TestComputeStructureTrade(unittest.TestCase):
    """T14-T15 - orchestrator."""

    def _happy_path_df(self):
        """A long setup that produces a full pullback trade.

        - Confirmed swing low at bar 10 (95) -> pullback support.
        - Signal at bar 30 (close=100, flat OHLC).
        - Bar 33 dips to 94 -> pullback fills at 95 (limit at support).
        - Confirmed swing high at bar 25 (108) -> overhead target (confirmed at 30).
        - Constant ATR=2 passed so stops/targets are exact.
        """
        n = 60
        df = struct_df(n, swing_lows={10: 95.0}, swing_highs={25: 108.0}, base=100.0)
        set_bar(df, 33, opn=100.0, high=100.0, low=94.0, close=95.5)
        return df

    def test_t14_full_happy_path(self):
        df = self._happy_path_df()
        atr = const_atr(len(df), 2.0)
        trade = ms.compute_structure_trade(
            df, signal_idx=30, direction="long", max_wait_bars=5, min_rr=1.5,
            max_atr=2.0, atr=atr, pivot_distance=5, entry_fallback="signal")
        self.assertIsNotNone(trade, "happy path must produce a trade dict")
        for key in ("entry_price", "entry_idx", "stop_price", "target_price",
                    "risk", "rr", "entry_type", "decision_idx"):
            self.assertIn(key, trade, f"missing key {key}")
        self.assertEqual(trade["entry_type"], "pullback")
        self.assertEqual(trade["entry_idx"], 33)
        self.assertAlmostEqual(trade["entry_price"], 95.0, places=6)
        # stop below entry, risk > 0.
        self.assertLess(trade["stop_price"], trade["entry_price"])
        self.assertGreater(trade["risk"], 0)
        # target = 108 (nearest confirmed overhead meeting min_rr).
        self.assertAlmostEqual(trade["target_price"], 108.0, places=6)
        self.assertGreaterEqual(trade["rr"], 1.5)

    def test_t15_target_none_returns_none(self):
        # No overhead resistance and a small ATR fallback that fails min_rr.
        # entry=100 (signal close, no pullback touch), stop below 95 (structure)
        # -> risk ~6.5. atr_target = 100 + 2.5*1 = 102.5, R ~ 0.38 < 1.5 -> None.
        n = 60
        df = struct_df(n, swing_lows={10: 95.0}, base=100.0)  # no swing highs
        atr = const_atr(n, 1.0)
        trade = ms.compute_structure_trade(
            df, signal_idx=30, direction="long", max_wait_bars=5, min_rr=1.5,
            max_atr=2.0, atr=atr, pivot_distance=5, entry_fallback="signal")
        self.assertIsNone(trade, "no valid target must yield None")


# ---------------------------------------------------------------------------
# L1-L3: look-ahead regression tests
# ---------------------------------------------------------------------------

class TestLookAheadRegression(unittest.TestCase):
    """The critical suite - US-114 lesson encoded as executable tests."""

    def _base_series(self, n=200, seed=7, base=100.0):
        """A mildly trending + noisy series with several real pivots."""
        rng = np.random.default_rng(seed)
        t = np.arange(n)
        close = base + 3.0 * np.sin(t / 12.0) + rng.normal(0, 0.3, size=n)
        opn = close + rng.normal(0, 0.2, size=n)
        high = np.maximum(opn, close) + np.abs(rng.normal(0, 0.3, size=n))
        low = np.minimum(opn, close) - np.abs(rng.normal(0, 0.3, size=n))
        return pd.DataFrame({"open": opn, "high": high, "low": low, "close": close},
                             index=_idx(n))

    def test_l1_future_bar_invariance(self):
        # Compute trade at signal_idx=100. Then append 50 future bars that
        # drastically change pivots beyond the lookback window. Re-run with
        # signal_idx=100 on the extended df. Outputs must be IDENTICAL.
        df = self._base_series(n=200, seed=11)
        signal_idx = 100
        trade_a = ms.compute_structure_trade(
            df, signal_idx=signal_idx, direction="long", max_wait_bars=5,
            min_rr=1.5, max_atr=2.0, atr=None, pivot_distance=5,
            entry_fallback="signal")

        rng = np.random.default_rng(99)
        n_ext = 50
        base = float(df["close"].iloc[-1])
        opn = base + rng.normal(0, 0.2, size=n_ext)
        close = base + np.cumsum(rng.normal(0, 1.5, size=n_ext))  # wandering
        high = np.maximum(opn, close) + np.abs(rng.normal(0, 0.5, size=n_ext))
        low = np.minimum(opn, close) - np.abs(rng.normal(0, 0.5, size=n_ext))
        future = pd.DataFrame({"open": opn, "high": high, "low": low, "close": close},
                              index=range(200, 200 + n_ext))
        df_ext = pd.concat([df, future], ignore_index=True)

        trade_b = ms.compute_structure_trade(
            df_ext, signal_idx=signal_idx, direction="long", max_wait_bars=5,
            min_rr=1.5, max_atr=2.0, atr=None, pivot_distance=5,
            entry_fallback="signal")
        self.assertEqual(trade_a, trade_b,
                         "decision at signal_idx=100 must not depend on far-future bars")

    def test_l2_pivot_confirmation_invariance(self):
        # A swing low at p; if bars in (p, p+PIVOT_DISTANCE] are mutated to be
        # lower, find_peaks(distance=D) will NO LONGER report p as a peak.
        # When decision_idx < p + PIVOT_DISTANCE, the pivot is not used anyway
        # (confirmed-only filter). When the peak was destroyed, it must NOT
        # appear in confirmed pivots even past the confirmation bar.
        n = 60
        df = struct_df(n, swing_lows={20: 90.0}, base=100.0)
        # Before mutation, pivot at 20 is confirmed at idx 25.
        pivs_clean = ms._confirmed_pivots(df, as_of_idx=25, kind="low",
                                         pivot_distance=5, lookback=None)
        self.assertIn(20, pivs_clean)
        # Mutate bars 21..25 to be LOWER than 90 -> destroys the peak at 20.
        df2 = df.copy()
        for j in range(21, 26):
            set_bar(df2, j, low=85.0)
        pivs_mut = ms._confirmed_pivots(df2, as_of_idx=30, kind="low",
                                        pivot_distance=5, lookback=None)
        self.assertNotIn(20, pivs_mut,
                         "destroyed peak must not be reported as a pivot")
        # And critically: with decision_idx < 20+5, even the clean pivot is
        # not usable (the confirmed-only filter is the US-114 fix).
        pivs_early = ms._confirmed_pivots(df, as_of_idx=24, kind="low",
                                         pivot_distance=5, lookback=None)
        self.assertNotIn(20, pivs_early,
                         "pivot at 20 must be unknown at idx 24 (needs bar 25)")

    def test_l3_pullback_level_frozen_at_signal(self):
        # Modify a bar at signal_idx+2 to create a NEW swing low that confirms
        # at signal_idx+2+PIVOT_DISTANCE (which is > signal_idx). Assert this
        # new low is NOT used as the pullback support for the signal at
        # signal_idx (it wasn't confirmed at signal time).
        n = 80
        base = 100.0
        # Established support: deep swing low at bar 10 (value 95), confirmed
        # well before signal_idx=30. Close stays flat so EMA is not a support.
        df_base = struct_df(n, swing_lows={10: 95.0}, base=base)
        signal_idx = 30

        # Baseline: add a pullback touch at 33 (low=94 <= support 95) -> fill 95.
        set_bar(df_base, 33, opn=base, high=base, low=94.0, close=95.5)
        ep_base, ei_base = ms.compute_pullback_entry(
            df_base, signal_idx=signal_idx, direction="long", max_wait_bars=5,
            pivot_distance=5, ema_span=20, fallback="signal")
        self.assertAlmostEqual(ep_base, 95.0, places=6)
        self.assertEqual(ei_base, 33)

        # Create a NEW, DEEPER swing low at bar 32 (signal_idx+2), value 90. It
        # confirms at 32+5=37 > signal_idx=30, so it was NOT knowable at signal
        # time. Surrounding bars (27..37) must stay above 90 for it to register
        # as a peak in the extended run.
        df_ext = df_base.copy()
        for j in range(27, 38):
            if j == 32:
                continue
            # raise neighbors so 32 is a clean valley, but preserve the 33 touch
            cur = float(df_ext.iloc[j, df_ext.columns.get_loc("low")])
            set_bar(df_ext, j, low=max(cur, 96.0))
        set_bar(df_ext, 32, opn=base, high=base, low=90.0, close=95.5)
        # Re-assert the touch at 33 (the loop above may have raised it to 96).
        set_bar(df_ext, 33, opn=base, high=base, low=94.0, close=95.5)

        ep_ext, ei_ext = ms.compute_pullback_entry(
            df_ext, signal_idx=signal_idx, direction="long", max_wait_bars=5,
            pivot_distance=5, ema_span=20, fallback="signal")
        # The new 90 low is NOT confirmed at signal_idx=30 (confirms at 37), so
        # it must NOT be used as the *support level*: support stays 95 and the
        # fill price is 95 (NOT 90). The fill timing does change: bar 32's deep
        # low (90) dips through the frozen 95 limit, so the resting order fills
        # on bar 32 (the first bar whose low <= 95) rather than bar 33. This is
        # correct limit-order semantics and exactly what we want to verify:
        # the SUPPORT LEVEL is frozen at signal time even though price action
        # during the wait window differs.
        self.assertAlmostEqual(ep_ext, 95.0, places=6,
                               msg="unconfirmed new low must not be used as support level")
        self.assertEqual(ei_ext, 32,
                         "limit at frozen 95 fills on first touch (bar 32 dips through it)")

        # Sanity: the new pivot IS confirmed at idx 37 (independent check).
        pivs_37 = ms._confirmed_pivots(df_ext, as_of_idx=37, kind="low",
                                       pivot_distance=5, lookback=None)
        self.assertIn(32, pivs_37, "the new low should be confirmed at idx 37")
        # But NOT confirmed at signal_idx 30.
        pivs_30 = ms._confirmed_pivots(df_ext, as_of_idx=30, kind="low",
                                       pivot_distance=5, lookback=None)
        self.assertNotIn(32, pivs_30)


# ---------------------------------------------------------------------------
# P1-P3: property / invariant tests
# ---------------------------------------------------------------------------

class TestPropertyInvariants(unittest.TestCase):
    """P1-P3 - structural invariants over randomised data."""

    def _random_df(self, n, seed, base=100.0):
        rng = np.random.default_rng(seed)
        t = np.arange(n)
        close = base + 4.0 * np.sin(t / 9.0) + rng.normal(0, 0.4, size=n)
        opn = close + rng.normal(0, 0.2, size=n)
        high = np.maximum(opn, close) + np.abs(rng.normal(0, 0.4, size=n))
        low = np.minimum(opn, close) - np.abs(rng.normal(0, 0.4, size=n))
        return pd.DataFrame({"open": opn, "high": high, "low": low, "close": close},
                             index=_idx(n))

    def test_p1_all_pivots_confirmed(self):
        # Every pivot referenced by any function output satisfies
        # p + PIVOT_DISTANCE <= decision_idx. The debug-mode assertion guard
        # (enabled at import) fires on any violation. Run many random trades
        # and ensure the guard never raises and outputs are well-formed.
        for seed in range(20):
            df = self._random_df(n=220, seed=seed)
            for direction in ("long", "short"):
                for sidx in (40, 80, 120, 150):
                    trade = ms.compute_structure_trade(
                        df, signal_idx=sidx, direction=direction,
                        max_wait_bars=5, min_rr=1.5, max_atr=2.0, atr=None,
                        pivot_distance=5, entry_fallback="signal")
                    if trade is not None:
                        self.assertGreaterEqual(trade["decision_idx"],
                                                trade["entry_idx"])
                        self.assertGreater(trade["risk"], 0)

    def test_p2_stop_correct_side_and_positive_risk(self):
        for seed in range(20):
            df = self._random_df(n=220, seed=seed + 100)
            atr = ms._compute_atr(df)
            for direction in ("long", "short"):
                for didx in (50, 100, 150):
                    entry = float(df["close"].iloc[didx])
                    stop = ms.compute_structure_stop(
                        df, decision_idx=didx, direction=direction,
                        entry_price=entry, max_atr=2.0, min_atr=0.5,
                        lookback=20, pivot_distance=5, atr=atr, buffer_atr=0.5)
                    if direction == "long":
                        self.assertLess(stop, entry, "long stop must be below entry")
                    else:
                        self.assertGreater(stop, entry,
                                           "short stop must be above entry")
                    self.assertGreater(abs(entry - stop), 0, "risk must be > 0")

    def test_p3_target_none_or_correct_side_with_min_rr(self):
        for seed in range(20):
            df = self._random_df(n=220, seed=seed + 200)
            atr = ms._compute_atr(df)
            for direction in ("long", "short"):
                for didx in (50, 100, 150):
                    entry = float(df["close"].iloc[didx])
                    stop = ms.compute_structure_stop(
                        df, decision_idx=didx, direction=direction,
                        entry_price=entry, max_atr=2.0, min_atr=0.5,
                        lookback=20, pivot_distance=5, atr=atr, buffer_atr=0.5)
                    risk = abs(entry - stop)
                    tgt = ms.compute_natural_target(
                        df, decision_idx=didx, direction=direction,
                        entry_price=entry, stop_price=stop, min_rr=1.5,
                        lookback=50, pivot_distance=5, atr=atr,
                        atr_target_mult=2.5)
                    if tgt is None:
                        continue
                    if direction == "long":
                        self.assertGreater(tgt, entry,
                                           "long target must be above entry")
                        rr = (tgt - entry) / risk
                    else:
                        self.assertLess(tgt, entry,
                                        "short target must be below entry")
                        rr = (entry - tgt) / risk
                    self.assertGreaterEqual(rr, 1.5 - 1e-9,
                                            "target R must meet min_rr when not None")


if __name__ == "__main__":
    unittest.main(verbosity=2)
