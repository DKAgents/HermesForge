"""
Golden-vector tests for liquidation_pressure.py (PROP-001).
Python stdlib unittest — no pytest dependency.
"""

import sys
import os
import math
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from liquidation_pressure import (
    estimate_liquidation_clusters,
    distance_to_cluster_atr,
    detect_cascade,
    exhaustion_flag,
    CASCADE_WINDOW,
    CASCADE_WICK_ATR_MULT,
    CASCADE_OI_DROP_PCT,
)


class TestLiquidationPressure(unittest.TestCase):
    """Golden-vector tests for liquidation cluster, cascade, and exhaustion logic."""

    # ── LP1: Clusters group within 0.5% bands ──────────────────────────

    def test_LP1_clusters_group_within_bands(self):
        """Liquidations within 0.5% of each other should be grouped."""
        liquidations = [
            {'price': 50000.0, 'size': 10.0, 'side': 'long'},
            {'price': 50100.0, 'size': 5.0, 'side': 'long'},   # 0.2% away → same cluster
            {'price': 50250.0, 'size': 2.0, 'side': 'long'},   # 0.3% from first → same cluster
            {'price': 51000.0, 'size': 8.0, 'side': 'long'},   # 2% away → new cluster
        ]
        result = estimate_liquidation_clusters(liquidations)
        self.assertEqual(len(result['long_clusters']), 2)
        # First cluster should have sizes 10+5+2=17
        self.assertAlmostEqual(result['long_clusters'][0][1], 17.0, places=1)
        # Second cluster should have size 8
        self.assertEqual(len(result['short_clusters']), 0)

    def test_LP1b_clusters_boundary(self):
        """Exactly at 0.5% boundary stays in same cluster."""
        liquidations = [
            {'price': 50000.0, 'size': 1.0, 'side': 'long'},
            {'price': 50250.0, 'size': 1.0, 'side': 'long'},  # exactly 0.5%
        ]
        result = estimate_liquidation_clusters(liquidations)
        self.assertEqual(len(result['long_clusters']), 1)

    def test_LP1c_clusters_outside_band(self):
        """Just over 0.5% boundary splits."""
        liquidations = [
            {'price': 50000.0, 'size': 1.0, 'side': 'long'},
            {'price': 50251.0, 'size': 1.0, 'side': 'long'},  # > 0.5%
        ]
        result = estimate_liquidation_clusters(liquidations)
        self.assertEqual(len(result['long_clusters']), 2)

    # ── LP2: Empty liquidations returns empty clusters ─────────────────

    def test_LP2_empty_liquidations(self):
        """Empty input returns empty clusters for both sides."""
        result = estimate_liquidation_clusters([])
        self.assertEqual(result['long_clusters'], [])
        self.assertEqual(result['short_clusters'], [])

    # ── LP3: distance_to_cluster_atr correct math ──────────────────────

    def test_LP3_distance_to_cluster_atr(self):
        """Distance to nearest cluster in ATR units."""
        clusters = [(50000.0, 100.0), (51000.0, 50.0)]
        current_price = 50500.0
        atr = 200.0
        # Nearest cluster is 50000.0 → distance = 500
        # In ATR units: 500 / 200 = 2.5
        dist = distance_to_cluster_atr(current_price, clusters, atr)
        self.assertAlmostEqual(dist, 2.5, places=10)

    def test_LP3b_distance_empty_clusters(self):
        """No clusters → distance 0."""
        dist = distance_to_cluster_atr(50000.0, [], 100.0)
        self.assertEqual(dist, 0.0)

    def test_LP3c_distance_zero_atr(self):
        """Zero ATR → distance 0."""
        dist = distance_to_cluster_atr(50000.0, [(50000.0, 10.0)], 0.0)
        self.assertEqual(dist, 0.0)

    # ── LP4: Cascade detection with wick + OI drop + funding snap ──────

    def test_LP4_cascade_detected(self):
        """All three conditions met → cascade active."""
        # Build wicks: last one is outsized (3x ATR)
        wicks = []
        for i in range(CASCADE_WINDOW - 1):
            wicks.append({'high': 50100.0 + i, 'low': 50000.0 + i, 'close': 50050.0 + i})
        # Outsized wick: 3x the mean (each prior wick was ~100)
        wicks.append({'high': 50350.0, 'low': 50000.0, 'close': 50175.0})  # wick=350, others ~100

        # OI changes: cumulative > 3% drop
        oi_changes = [-0.004] * (CASCADE_WINDOW - 1) + [-0.008]  # ~ -5.6% cumulative

        # Funding changes: snap toward zero
        funding_changes = [0.0002] * (CASCADE_WINDOW - 3) + [-0.0005, -0.0006, -0.0007]

        active, direction, severity = detect_cascade(wicks, oi_changes, funding_changes)
        self.assertTrue(active)
        self.assertIn(direction, ('long_squeeze', 'short_squeeze'))
        self.assertIn(severity, ('mild', 'moderate', 'severe'))

    # ── LP5: Cascade NOT detected when only one condition met ──────────

    def test_LP5_no_cascade_single_condition(self):
        """Only outsized wick but no OI drop, no funding snap → no cascade."""
        wicks = []
        for i in range(CASCADE_WINDOW - 1):
            wicks.append({'high': 50100.0 + i, 'low': 50000.0 + i, 'close': 50050.0 + i})
        wicks.append({'high': 50350.0, 'low': 50000.0, 'close': 50175.0})  # outsized wick

        # OI changes: flat (no drop)
        oi_changes = [0.0] * CASCADE_WINDOW

        # Funding changes: no snap
        funding_changes = [0.00001] * CASCADE_WINDOW

        active, direction, severity = detect_cascade(wicks, oi_changes, funding_changes)
        self.assertFalse(active)
        self.assertEqual(direction, 'none')
        self.assertEqual(severity, 'none')

    def test_LP5b_no_cascade_oi_only(self):
        """Only OI drop, no outsized wick or funding snap."""
        wicks = []
        for i in range(CASCADE_WINDOW):
            wicks.append({'high': 50100.0 + i, 'low': 50000.0 + i, 'close': 50050.0 + i})

        oi_changes = [-0.005] * CASCADE_WINDOW  # big OI drop
        funding_changes = [0.00001] * CASCADE_WINDOW

        active, _, _ = detect_cascade(wicks, oi_changes, funding_changes)
        self.assertFalse(active)

    # ── LP6: Exhaustion flag after cascade + retrace distance ──────────

    def test_LP6_exhaustion_after_cascade(self):
        """After a cascade ends and distance > 1.5 ATR, exhaustion flags."""
        # Cascade was active, then ended
        cascade_history = [False, False, True, True, False]
        distance = 2.0  # 2.0 ATR > 1.5 threshold
        atr = 100.0

        flag, confidence = exhaustion_flag(cascade_history, distance, atr)
        self.assertTrue(flag)
        self.assertGreater(confidence, 0.0)

    def test_LP6b_exhaustion_not_enough_distance(self):
        """Cascade ended but distance ≤ 1.5 ATR → no exhaustion."""
        cascade_history = [False, False, True, True, False]
        distance = 1.0  # below threshold
        atr = 100.0

        flag, confidence = exhaustion_flag(cascade_history, distance, atr)
        self.assertFalse(flag)
        self.assertEqual(confidence, 0.0)

    # ── LP7: Exhaustion flag false during active cascade ───────────────

    def test_LP7_no_exhaustion_during_cascade(self):
        """Cascade is still active (last entry True) → no exhaustion."""
        cascade_history = [False, False, True, True, True]  # still active
        distance = 3.0  # well above threshold
        atr = 100.0

        flag, confidence = exhaustion_flag(cascade_history, distance, atr)
        self.assertFalse(flag)
        self.assertEqual(confidence, 0.0)

    def test_LP7b_no_recent_cascade(self):
        """No recent cascade at all → no exhaustion."""
        cascade_history = [False, False, False, False, False]
        distance = 3.0
        atr = 100.0

        flag, confidence = exhaustion_flag(cascade_history, distance, atr)
        self.assertFalse(flag)
        self.assertEqual(confidence, 0.0)


if __name__ == '__main__':
    unittest.main()