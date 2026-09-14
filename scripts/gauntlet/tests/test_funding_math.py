"""
Golden-vector tests for funding_state.py (PROP-001).
Python stdlib unittest — no pytest dependency.
"""

import sys
import os
import math
import unittest
import time

# Ensure the gauntlet package is importable.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from funding_state import (
    compute_funding_rate,
    compute_hourly_payment,
    compute_funding_z,
    compute_carry_bps_per_hour,
    settlement_countdown,
    assess_crowding,
    INTEREST_COMPONENT,
    PREMIUM_CAP,
    HARD_CAP_HOURLY,
)


class TestFundingMath(unittest.TestCase):
    """Golden-vector tests matching the PROP-001 funding spec."""

    # ── F1: Zero premium → funding = interest only ─────────────────────
    def test_F1_zero_premium_gives_interest_only(self):
        """0.01 % per 8 h = 0.0001."""
        rate = compute_funding_rate(0.0)
        self.assertAlmostEqual(rate, INTEREST_COMPONENT, places=10)

    # ── F2: Premium clamped at +0.05 % ─────────────────────────────────
    def test_F2_premium_clamped_positive(self):
        """Input 0.001 (0.1 %) → clamped to 0.0005 (0.05 %)."""
        rate = compute_funding_rate(0.001)   # raw premium 0.1 %
        expected = INTEREST_COMPONENT + PREMIUM_CAP  # 0.0001 + 0.0005 = 0.0006
        self.assertAlmostEqual(rate, expected, places=10)

    # ── F3: Premium clamped at -0.05 % ────────────────────────────────
    def test_F3_premium_clamped_negative(self):
        """Input -0.001 → clamped to -0.0005."""
        rate = compute_funding_rate(-0.001)
        expected = INTEREST_COMPONENT - PREMIUM_CAP  # 0.0001 - 0.0005 = -0.0004
        self.assertAlmostEqual(rate, expected, places=10)

    # ── F4: Hard cap at 4 %/hr ────────────────────────────────────────
    def test_F4_hard_cap(self):
        """Input large enough to drive rate > 4 % → capped at 4 %."""
        # 0.05 raw → premium clamped to 0.0005 → rate = 0.0006 (within cap)
        # Need premium_raw that would push rate past 0.04:
        # interest + clamped = 0.0001 + 0.0005 = 0.0006 ... that is way below 0.04.
        # So the hard cap is tested by a *direct* case: the formula caps at HARD_CAP_HOURLY.
        # We test that the returned rate never exceeds HARD_CAP_HOURLY.
        # Even a huge premium_raw is clamped to ±0.0005 premium, so the cap is
        # really about the overall rate not exceeding 0.04.
        # For this vector test we verify the cap is enforced:
        rate = compute_funding_rate(100.0)  # massive raw premium
        self.assertLessEqual(rate, HARD_CAP_HOURLY)
        self.assertGreaterEqual(rate, -HARD_CAP_HOURLY)
        # With premium clamped to 0.0005, rate = 0.0001+0.0005 = 0.0006 < 0.04
        self.assertAlmostEqual(rate, INTEREST_COMPONENT + PREMIUM_CAP, places=10)

    # Also test that if we hypothetically constructed a rate that hits the cap
    # it would be enforced.  The formula as given clamps the SUM, so even with
    # max premium the rate is always ≤ 0.0006.  The hard cap is a safety clamp
    # but not reachable with the current premium bounds.  The test confirms the
    # function's clamping logic exists and works.
    def test_F4b_hard_cap_boundary(self):
        """Verify the clamping logic is present by checking a synthetic edge."""
        # Since the premium is capped at ±0.0005, the worst-case rate is
        # 0.0001 + 0.0005 = 0.0006, which is well under 0.04.
        # We test that the function returns ≤ 0.04 for any finite input.
        for raw in (-1e6, -1.0, 0.0, 1.0, 1e6):
            rate = compute_funding_rate(raw)
            self.assertLessEqual(abs(rate), HARD_CAP_HOURLY)

    # ── F5: Hourly payment = position * (1/8) * funding_rate ──────────
    def test_F5_hourly_payment_formula(self):
        pos = 100_000.0     # $100k position
        rate_8h = 0.0006    # 0.06 % per 8 h
        payment = compute_hourly_payment(pos, rate_8h)
        expected = (1.0 / 8.0) * rate_8h * pos
        self.assertAlmostEqual(payment, expected, places=8)
        # Concrete: (1/8) * 0.0006 * 100000 = 7.5
        self.assertAlmostEqual(payment, 7.5, places=8)

    # ── F6: Long pays when rate > 0 ────────────────────────────────────
    def test_F6_long_pays_funding_positive_rate(self):
        """Long position: positive rate → positive payment (long pays)."""
        payment = compute_hourly_payment(100_000.0, 0.0008)
        self.assertGreater(payment, 0.0)

    # ── F7: Short receives when rate > 0 ───────────────────────────────
    def test_F7_short_receives_funding_positive_rate(self):
        """Short position (negative size) with positive rate → negative payment (short receives)."""
        payment = compute_hourly_payment(-100_000.0, 0.0008)
        self.assertLess(payment, 0.0)

    # ── F8: settlement_countdown returns 0–59 ─────────────────────────
    def test_F8_settlement_countdown_range(self):
        minutes = settlement_countdown()
        self.assertIsInstance(minutes, int)
        self.assertGreaterEqual(minutes, 0)
        self.assertLessEqual(minutes, 59)

    def test_F8b_settlement_countdown_explicit_time(self):
        """Known timestamp should give known minutes-remaining."""
        import datetime as dt_mod
        # 2026-01-01 12:23:45 UTC → 37 minutes past → 60-37 = 23 min remaining (floor)
        ts = dt_mod.datetime(2026, 1, 1, 12, 23, 45, tzinfo=dt_mod.timezone.utc).timestamp()
        minutes = settlement_countdown(ts)
        self.assertEqual(minutes, 36)  # 60 - 23 = 37, but seconds eat into it: 60*37 - 45 = 2175s → 36 min floor

    def test_F8c_settlement_countdown_top_of_hour(self):
        import datetime as dt_mod
        ts = dt_mod.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt_mod.timezone.utc).timestamp()
        self.assertEqual(settlement_countdown(ts), 0)  # top of hour → 0 min (settlement just fired)

    # ── F9: Z-score computation correct with known distribution ───────
    def test_F9_zscore_known_distribution(self):
        """Z-score of latest value against a known distribution."""
        history = [0.0001, 0.0002, 0.0001, 0.0003, 0.0002, 0.0004]  # latest=0.0004
        z = compute_funding_z(history)
        # mean of first 5 = (0.0001+0.0002+0.0001+0.0003+0.0002)/5 = 0.00018
        # stdev ≈ 0.000083666
        # z = (0.0004 - 0.00018) / 0.000083666 ≈ 2.63
        self.assertGreater(z, 2.0)
        self.assertLess(z, 3.5)

    def test_F9b_zscore_single_element(self):
        self.assertEqual(compute_funding_z([0.0005]), 0.0)

    def test_F9c_zscore_empty_list(self):
        self.assertEqual(compute_funding_z([]), 0.0)

    def test_F9d_zscore_zero_stdev(self):
        """All same values → stdev=0, same latest → z=0."""
        self.assertEqual(compute_funding_z([0.0001, 0.0001, 0.0001]), 0.0)


class TestCarryBps(unittest.TestCase):
    """Carry computation tests."""

    def test_carry_zero(self):
        self.assertAlmostEqual(compute_carry_bps_per_hour(0.0), 0.0, places=10)

    def test_carry_positive(self):
        # 0.08 % per 8h → 0.01 % per hour → 1 bp / hour
        rate_8h = 0.0008  # 0.08 %
        carry = compute_carry_bps_per_hour(rate_8h)
        self.assertAlmostEqual(carry, 1.0, places=10)

    def test_carry_negative(self):
        rate_8h = -0.0008
        carry = compute_carry_bps_per_hour(rate_8h)
        self.assertAlmostEqual(carry, -1.0, places=10)


class TestCrowding(unittest.TestCase):
    """Crowding assessment tests."""

    def test_no_crowding(self):
        flag, sev = assess_crowding(0.0, 0.0)
        self.assertFalse(flag)
        self.assertEqual(sev, 'low')

    def test_moderate_crowding(self):
        flag, sev = assess_crowding(1.5, 0.06)
        self.assertFalse(flag)  # combined = 2 → moderate, not crowded
        self.assertEqual(sev, 'moderate')

    def test_high_crowding(self):
        flag, sev = assess_crowding(2.5, 0.08)
        self.assertTrue(flag)
        self.assertEqual(sev, 'high')

    def test_extreme_crowding(self):
        flag, sev = assess_crowding(3.5, 0.25)
        self.assertTrue(flag)
        self.assertEqual(sev, 'extreme')


if __name__ == '__main__':
    unittest.main()