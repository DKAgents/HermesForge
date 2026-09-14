"""
Classification tests for oi_delta.py (PROP-001).
Python stdlib unittest — no pytest dependency.
"""

import sys
import os
import math
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from oi_delta import (
    classify_oi_delta,
    compute_oi_delta_z,
    participation_score,
    interpret_quadrant,
    QUADRANT_NEW_LONGS,
    QUADRANT_SHORT_COVERING,
    QUADRANT_NEW_SHORTS,
    QUADRANT_LONG_LIQUIDATION,
    QUADRANT_NEUTRAL,
    QUADRANT_UNKNOWN,
)


class TestOIClassification(unittest.TestCase):
    """Quadrant classification golden-vector tests."""

    # ── O1: price_up + oi_up → NEW_LONGS ──────────────────────────────
    def test_O1_new_longs(self):
        self.assertEqual(classify_oi_delta(0.02, 0.03), QUADRANT_NEW_LONGS)

    # ── O2: price_up + oi_down → SHORT_COVERING ───────────────────────
    def test_O2_short_covering(self):
        self.assertEqual(classify_oi_delta(0.02, -0.03), QUADRANT_SHORT_COVERING)

    # ── O3: price_down + oi_up → NEW_SHORTS ───────────────────────────
    def test_O3_new_shorts(self):
        self.assertEqual(classify_oi_delta(-0.02, 0.03), QUADRANT_NEW_SHORTS)

    # ── O4: price_down + oi_down → LONG_LIQUIDATION ───────────────────
    def test_O4_long_liquidation(self):
        self.assertEqual(classify_oi_delta(-0.02, -0.03), QUADRANT_LONG_LIQUIDATION)

    # ── O5: zero price change, positive OI → neutral (price below threshold) ──
    def test_O5_zero_price_positive_oi(self):
        # Price change 0.0 is below threshold → neutral
        self.assertEqual(classify_oi_delta(0.0, 0.03), QUADRANT_NEUTRAL)

    # ── O6: zero OI change → bias from price only → neutral ───────────
    def test_O6_zero_oi_change(self):
        self.assertEqual(classify_oi_delta(0.03, 0.0), QUADRANT_NEUTRAL)

    # ── O7: NaN inputs return 'unknown' ───────────────────────────────
    def test_O7_nan_price(self):
        self.assertEqual(classify_oi_delta(float('nan'), 0.03), QUADRANT_UNKNOWN)

    def test_O7b_nan_oi(self):
        self.assertEqual(classify_oi_delta(0.03, float('nan')), QUADRANT_UNKNOWN)

    def test_O7c_both_nan(self):
        self.assertEqual(classify_oi_delta(float('nan'), float('nan')), QUADRANT_UNKNOWN)

    # ── O8: threshold respected ───────────────────────────────────────
    def test_O8_tiny_change_classified_neutral(self):
        """0.0005 < 0.001 → treated as zero for both → neutral."""
        self.assertEqual(classify_oi_delta(0.0005, 0.0005), QUADRANT_NEUTRAL)

    def test_O8b_at_threshold_still_neutral(self):
        """Exactly at threshold is still neutral (strict > and <)."""
        self.assertEqual(classify_oi_delta(0.001, 0.001), QUADRANT_NEUTRAL)

    def test_O8c_just_above_threshold(self):
        self.assertEqual(classify_oi_delta(0.0011, 0.0011), QUADRANT_NEW_LONGS)

    # ── O9: interpret_quadrant returns valid structure ────────────────
    def test_O9_interpret_new_longs(self):
        result = interpret_quadrant(QUADRANT_NEW_LONGS, 2.5, 0.85)
        self.assertIsInstance(result, dict)
        self.assertIn('directional_bias', result)
        self.assertIn('conviction', result)
        self.assertIn('narrative', result)
        self.assertEqual(result['directional_bias'], +1)
        self.assertEqual(result['conviction'], 'high')

    def test_O9b_interpret_new_shorts(self):
        result = interpret_quadrant(QUADRANT_NEW_SHORTS, 1.5, 0.6)
        self.assertEqual(result['directional_bias'], -1)
        self.assertEqual(result['conviction'], 'med')

    def test_O9c_interpret_short_covering(self):
        result = interpret_quadrant(QUADRANT_SHORT_COVERING, 0.5, 0.3)
        self.assertEqual(result['directional_bias'], +1)
        self.assertEqual(result['conviction'], 'low')

    def test_O9d_interpret_long_liquidation(self):
        result = interpret_quadrant(QUADRANT_LONG_LIQUIDATION, 3.0, 0.95)
        self.assertEqual(result['directional_bias'], -1)
        self.assertEqual(result['conviction'], 'high')

    def test_O9e_interpret_neutral(self):
        result = interpret_quadrant(QUADRANT_NEUTRAL, 0.0, 0.0)
        self.assertEqual(result['directional_bias'], 0)
        self.assertIn(result['conviction'], ('low', 'med'))

    def test_O9f_interpret_unknown(self):
        result = interpret_quadrant(QUADRANT_UNKNOWN, 0.0, 0.0)
        self.assertEqual(result['directional_bias'], 0)
        self.assertIsInstance(result['narrative'], str)


class TestOIDeltaZ(unittest.TestCase):
    """Z-score computation for OI changes."""

    def test_zscore_known_distribution(self):
        history = [0.01, -0.02, 0.03, 0.01, -0.01, 0.05]  # latest = 0.05
        z = compute_oi_delta_z(history)
        # mean of first 5 = (0.01 - 0.02 + 0.03 + 0.01 - 0.01)/5 = 0.004
        # stdev ≈ 0.0195, z ≈ (0.05 - 0.004) / 0.0195 ≈ 2.36
        self.assertGreater(z, 1.5)
        self.assertLess(z, 3.5)

    def test_zscore_empty(self):
        self.assertEqual(compute_oi_delta_z([]), 0.0)

    def test_zscore_single(self):
        self.assertEqual(compute_oi_delta_z([0.05]), 0.0)


class TestParticipationScore(unittest.TestCase):
    """Participation score tests."""

    def test_low_participation(self):
        score = participation_score(0.0, 0.0)
        self.assertGreater(score, 0.0)
        self.assertLess(score, 0.5)

    def test_high_participation(self):
        score = participation_score(3.0, 3.0)
        self.assertGreater(score, 0.85)

    def test_range(self):
        """Participation score stays in [0,1] for a range of inputs."""
        for oi_z in (-5, -3, -1, 0, 1, 3, 5):
            for vol_z in (-5, -3, -1, 0, 1, 3, 5):
                score = participation_score(oi_z, vol_z)
                self.assertGreaterEqual(score, 0.0)
                self.assertLessEqual(score, 1.0)

    def test_nan_inputs(self):
        """NaN z-scores should not crash."""
        score = participation_score(float('nan'), 1.0)
        self.assertTrue(math.isnan(score))
        score = participation_score(1.0, float('nan'))
        self.assertTrue(math.isnan(score))


if __name__ == '__main__':
    unittest.main()