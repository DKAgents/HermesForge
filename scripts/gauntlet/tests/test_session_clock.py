"""
Golden-vector tests for session_clock.py (PROP-001).
Python stdlib unittest — no pytest dependency.
"""

import sys
import os
import unittest
import time
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from session_clock import (
    current_session,
    liquidity_tier,
    minutes_to_settlement,
    session_overlap,
    is_cme_gap_window,
    weekend_flag,
)


def _make_timestamp(weekday: int, hour: int, minute: int = 0, second: int = 0) -> float:
    """
    Create a POSIX timestamp for a specific weekday/time in UTC.

    Uses a known reference Monday and adjusts to the requested weekday/time.
    """
    # 2026-08-31 is a Monday
    base = datetime(2026, 8, 31, tzinfo=timezone.utc)
    target = base + timedelta(days=weekday, hours=hour, minutes=minute, seconds=second)
    return target.timestamp()


class TestSessionClock(unittest.TestCase):
    """Golden-vector tests for session clock and related utilities."""

    # ── SC1: ASIA session times correct ────────────────────────────────

    def test_SC1_asia_session(self):
        """00:00-08:00 UTC should be ASIA."""
        self.assertEqual(current_session(_make_timestamp(0, 0, 0)), 'ASIA')    # Mon 00:00
        self.assertEqual(current_session(_make_timestamp(0, 3, 30)), 'ASIA')   # Mon 03:30
        self.assertEqual(current_session(_make_timestamp(0, 7, 59)), 'ASIA')   # Mon 07:59
        self.assertEqual(current_session(_make_timestamp(2, 4, 15)), 'ASIA')   # Wed 04:15

    def test_SC1b_asia_boundary(self):
        """08:00 UTC should be EU, not ASIA."""
        self.assertEqual(current_session(_make_timestamp(1, 8, 0)), 'EU')     # Tue 08:00

    # ── SC2: EU session times correct ──────────────────────────────────

    def test_SC2_eu_session(self):
        """08:00-13:30 UTC should be EU."""
        self.assertEqual(current_session(_make_timestamp(0, 8, 0)), 'EU')      # Mon 08:00
        self.assertEqual(current_session(_make_timestamp(0, 10, 0)), 'EU')     # Mon 10:00
        self.assertEqual(current_session(_make_timestamp(0, 13, 0)), 'EU')     # Mon 13:00

    def test_SC2b_eu_boundary(self):
        """13:30 UTC should be US."""
        self.assertEqual(current_session(_make_timestamp(1, 13, 30)), 'US')   # Tue 13:30

    # ── SC3: US session times correct ──────────────────────────────────

    def test_SC3_us_session(self):
        """13:30-21:00 UTC should be US."""
        self.assertEqual(current_session(_make_timestamp(0, 13, 30)), 'US')    # Mon 13:30
        self.assertEqual(current_session(_make_timestamp(0, 16, 0)), 'US')     # Mon 16:00
        self.assertEqual(current_session(_make_timestamp(0, 20, 59)), 'US')    # Mon 20:59

    def test_SC3b_us_boundary(self):
        """21:00 UTC should be LOW_LIQUIDITY."""
        self.assertEqual(current_session(_make_timestamp(2, 21, 0)), 'LOW_LIQUIDITY')  # Wed 21:00

    # ── SC4: Weekend detection ─────────────────────────────────────────

    def test_SC4_weekend_saturday(self):
        """Saturday should be WEEKEND."""
        self.assertEqual(current_session(_make_timestamp(5, 0, 0)), 'WEEKEND')   # Sat 00:00
        self.assertEqual(current_session(_make_timestamp(5, 14, 30)), 'WEEKEND') # Sat 14:30

    def test_SC4_weekend_sunday(self):
        """Sunday should be WEEKEND."""
        self.assertEqual(current_session(_make_timestamp(6, 0, 0)), 'WEEKEND')   # Sun 00:00
        self.assertEqual(current_session(_make_timestamp(6, 23, 59)), 'WEEKEND') # Sun 23:59

    def test_SC4_weekend_friday_late(self):
        """Friday after 21:00 UTC → WEEKEND."""
        self.assertEqual(current_session(_make_timestamp(4, 21, 0)), 'WEEKEND')  # Fri 21:00
        self.assertEqual(current_session(_make_timestamp(4, 23, 0)), 'WEEKEND')  # Fri 23:00

    def test_SC4_friday_not_weekend(self):
        """Friday before 21:00 UTC should NOT be weekend."""
        self.assertEqual(current_session(_make_timestamp(4, 20, 59)), 'US')      # Fri 20:59

    # ── SC5: Liquidity tiers per session ───────────────────────────────

    def test_SC5_liquidity_tiers(self):
        """Verify correct tier mapping for each session."""
        self.assertEqual(liquidity_tier('US'), 'HIGH')
        self.assertEqual(liquidity_tier('EU'), 'HIGH')
        self.assertEqual(liquidity_tier('ASIA'), 'MEDIUM')
        self.assertEqual(liquidity_tier('LOW_LIQUIDITY'), 'LOW')
        self.assertEqual(liquidity_tier('WEEKEND'), 'LOW')

    # ── SC6: minutes_to_settlement 0-59 ────────────────────────────────

    def test_SC6_minutes_to_settlement(self):
        """Minutes to settlement should be 0-59."""
        # At exactly HH:00:00, should be 0
        ts = _make_timestamp(0, 14, 0, 0)
        self.assertEqual(minutes_to_settlement(ts), 0)

        # At HH:30:00, should be 30
        ts = _make_timestamp(0, 14, 30, 0)
        self.assertEqual(minutes_to_settlement(ts), 30)

        # At HH:00:01, should be 59 (60 - 0 - 1)
        ts = _make_timestamp(0, 14, 0, 1)
        self.assertEqual(minutes_to_settlement(ts), 59)

        # At HH:59:59, should be 0 (60 - 59 - 1 = 0 for seconds)
        ts = _make_timestamp(0, 14, 59, 59)
        remaining = minutes_to_settlement(ts)
        self.assertEqual(remaining, 0)

    def test_SC6b_settlement_boundary(self):
        """At HH:59:00, should be 1."""
        ts = _make_timestamp(0, 14, 59, 0)
        self.assertEqual(minutes_to_settlement(ts), 1)

    def test_SC6c_settlement_range(self):
        """Any result should be in [0, 60)."""
        for m in range(0, 60, 5):
            ts = _make_timestamp(0, 10, m, 0)
            result = minutes_to_settlement(ts)
            self.assertGreaterEqual(result, 0)
            self.assertLess(result, 60)

    # ── SC7: session_overlap during EU+US window ───────────────────────

    def test_SC7_eu_us_overlap(self):
        """13:30-16:00 UTC should be EU+US overlap."""
        self.assertEqual(session_overlap(_make_timestamp(1, 13, 30)), 'EU+US')  # Tue 13:30
        self.assertEqual(session_overlap(_make_timestamp(1, 15, 0)), 'EU+US')   # Tue 15:00
        self.assertEqual(session_overlap(_make_timestamp(1, 15, 59)), 'EU+US')  # Tue 15:59

    def test_SC7b_eu_us_boundary(self):
        """16:00 UTC should return just 'US' (no overlap)."""
        result = session_overlap(_make_timestamp(1, 16, 0))
        self.assertNotEqual(result, 'EU+US')

    def test_SC7c_asia_eu_overlap(self):
        """07:30-08:00 UTC should be ASIA+EU overlap."""
        self.assertEqual(session_overlap(_make_timestamp(2, 7, 30)), 'ASIA+EU')  # Wed 07:30
        self.assertEqual(session_overlap(_make_timestamp(2, 7, 59)), 'ASIA+EU')  # Wed 07:59

    # ── SC8: CME gap window Friday/Sunday ──────────────────────────────

    def test_SC8_cme_gap_friday_close(self):
        """Friday 21:00+ should be CME gap window."""
        self.assertTrue(is_cme_gap_window(_make_timestamp(4, 21, 0)))
        self.assertTrue(is_cme_gap_window(_make_timestamp(4, 23, 59)))

    def test_SC8_cme_gap_saturday(self):
        """Saturday all day should be CME gap window."""
        self.assertTrue(is_cme_gap_window(_make_timestamp(5, 0, 0)))
        self.assertTrue(is_cme_gap_window(_make_timestamp(5, 12, 0)))
        self.assertTrue(is_cme_gap_window(_make_timestamp(5, 23, 59)))

    def test_SC8_cme_gap_sunday(self):
        """Sunday before 22:00 UTC should be CME gap window."""
        self.assertTrue(is_cme_gap_window(_make_timestamp(6, 0, 0)))
        self.assertTrue(is_cme_gap_window(_make_timestamp(6, 21, 59)))

    def test_SC8d_cme_gap_sunday_after_open(self):
        """Sunday 22:00 UTC should NOT be CME gap window."""
        self.assertFalse(is_cme_gap_window(_make_timestamp(6, 22, 0)))

    def test_SC8e_no_cme_gap_weekday(self):
        """Monday-Thursday should not be CME gap window."""
        self.assertFalse(is_cme_gap_window(_make_timestamp(0, 12, 0)))  # Mon
        self.assertFalse(is_cme_gap_window(_make_timestamp(3, 12, 0)))  # Thu

    # ── weekend_flag ───────────────────────────────────────────────────

    def test_weekend_flag_true(self):
        """weekend_flag should match current_session WEEKEND."""
        self.assertTrue(weekend_flag(_make_timestamp(5, 12, 0)))  # Saturday
        self.assertTrue(weekend_flag(_make_timestamp(6, 12, 0)))  # Sunday
        self.assertTrue(weekend_flag(_make_timestamp(4, 22, 0)))  # Friday late

    def test_weekend_flag_false(self):
        """weekend_flag should be False for weekday sessions."""
        self.assertFalse(weekend_flag(_make_timestamp(0, 12, 0)))  # Mon
        self.assertFalse(weekend_flag(_make_timestamp(4, 14, 0)))  # Fri afternoon


if __name__ == '__main__':
    unittest.main()