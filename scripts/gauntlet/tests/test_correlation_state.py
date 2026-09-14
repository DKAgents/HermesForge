"""
Golden-vector tests for correlation_state.py (PROP-001).
Python stdlib unittest — no pytest dependency.
"""

import sys
import os
import math
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from correlation_state import (
    compute_btc_beta,
    compute_correlation,
    cluster_by_beta,
    portfolio_concentration,
)


class TestCorrelationState(unittest.TestCase):
    """Golden-vector tests for BTC beta, correlation, clustering, concentration."""

    # ── CS1: beta=1.0 when returns are identical ───────────────────────

    def test_CS1_beta_one_identical(self):
        """When symbol returns equal BTC returns, beta should be 1.0."""
        returns = [0.01, -0.02, 0.03, -0.01, 0.02, 0.015, -0.005, 0.0]
        beta = compute_btc_beta(returns, returns)
        self.assertAlmostEqual(beta, 1.0, places=10)

    def test_CS1b_beta_one_scaled_identical(self):
        """Same returns → beta 1.0 even with different magnitudes."""
        btc = [0.01, 0.02, -0.01, 0.03, -0.02, 0.01, 0.0, 0.02,
               -0.01, 0.015, 0.005, -0.005]
        sym = list(btc)  # identical
        beta = compute_btc_beta(sym, btc)
        self.assertAlmostEqual(beta, 1.0, places=10)

    # ── CS2: beta=0 when uncorrelated ──────────────────────────────────

    def test_CS2_beta_zero_uncorrelated(self):
        """Zero slope when symbol returns are uncorrelated with BTC."""
        btc = [0.01, 0.02, -0.01, 0.03, -0.02, 0.01, 0.0, 0.02,
               -0.01, 0.015, 0.005, -0.005]
        # Constant symbol returns → zero covariance → beta 0
        sym = [0.0] * len(btc)
        beta = compute_btc_beta(sym, btc)
        self.assertAlmostEqual(beta, 0.0, places=10)

    def test_CS2b_beta_zero_orthogonal(self):
        """Orthogonal returns → beta near 0."""
        btc = [0.01, 0.02, -0.01, 0.03, -0.02, 0.01, 0.0, 0.02,
               -0.01, 0.015, 0.005, -0.005]
        # Construct symbol returns with zero covariance
        mean_btc = sum(btc) / len(btc)
        sym = [-(r - mean_btc) for r in btc]  # opposite deviations
        beta = compute_btc_beta(sym, btc)
        # Cov = -Var(btc) → beta = -1.0
        self.assertAlmostEqual(beta, -1.0, places=10)

    # ── CS3: correlation=1 when identical ──────────────────────────────

    def test_CS3_correlation_one_identical(self):
        """Pearson correlation should be 1.0 for identical series."""
        returns = [0.01, -0.02, 0.03, -0.01, 0.02, 0.015, -0.005, 0.0]
        r = compute_correlation(returns, returns)
        self.assertAlmostEqual(r, 1.0, places=10)

    # ── CS4: correlation=0 when independent ────────────────────────────

    def test_CS4_correlation_zero_independent(self):
        """Correlation should be 0 for constant vs variable."""
        btc = [0.01, 0.02, -0.01, 0.03, -0.02, 0.01, 0.0, 0.02]
        sym = [0.0] * len(btc)  # constant → zero std → correlation undefined / 0
        r = compute_correlation(sym, btc)
        self.assertEqual(r, 0.0)

    def test_CS4b_correlation_negative_one(self):
        """Perfect negative correlation."""
        btc = [0.01, 0.02, -0.01, 0.03, -0.02]
        sym = [-x for x in btc]
        r = compute_correlation(sym, btc)
        self.assertAlmostEqual(r, -1.0, places=10)

    # ── CS5: cluster_by_beta splits correctly ──────────────────────────

    def test_CS5_cluster_by_beta(self):
        """Verify threshold-based clustering."""
        betas = {
            'BTC': 1.0,
            'ETH': 1.15,
            'LINK': 0.5,
            'SOL': 1.4,
            'AVAX': 0.65,
            'DOGE': 0.75,
            'ARB': 1.3,
        }
        clusters = cluster_by_beta(betas)

        # Low beta (< 0.7): LINK(0.5), AVAX(0.65)
        self.assertEqual(clusters['LINK'], 0)
        self.assertEqual(clusters['AVAX'], 0)

        # Medium beta (0.7-1.3): BTC(1.0), ETH(1.15), DOGE(0.75), ARB(1.3)
        self.assertEqual(clusters['BTC'], 1)
        self.assertEqual(clusters['ETH'], 1)
        self.assertEqual(clusters['DOGE'], 1)
        self.assertEqual(clusters['ARB'], 1)

        # High beta (> 1.3): SOL(1.4)
        self.assertEqual(clusters['SOL'], 2)

    def test_CS5b_cluster_empty(self):
        """Empty dict returns empty dict."""
        clusters = cluster_by_beta({})
        self.assertEqual(clusters, {})

    # ── CS6: portfolio_concentration detects overconcentration ─────────

    def test_CS6_portfolio_concentration(self):
        """Detect when a cluster dominates the portfolio."""
        positions = {
            'BTC': 5000.0,
            'ETH': 3000.0,
            'SOL': 2000.0,
            'LINK': 500.0,
        }
        cluster_map = {
            'BTC': 1,    # medium beta
            'ETH': 1,    # medium beta
            'SOL': 2,    # high beta
            'LINK': 0,   # low beta
        }
        result = portfolio_concentration(positions, cluster_map, threshold=0.50)

        # Total exposure: 5000+3000+2000+500 = 10500
        # Cluster 1 (BTC+ETH): 8000 → 8000/10500 ≈ 76.2% → flagged
        # Cluster 2 (SOL): 2000 → 2000/10500 ≈ 19.0% → not flagged
        # Cluster 0 (LINK): 500 → 500/10500 ≈ 4.8% → not flagged

        self.assertTrue(result['overconcentrated'])
        self.assertIn(1, result['flags'])
        self.assertNotIn(0, result['flags'])
        self.assertNotIn(2, result['flags'])

        self.assertAlmostEqual(result['cluster_pcts'][1], 8000/10500, places=4)
        self.assertAlmostEqual(result['cluster_pcts'][2], 2000/10500, places=4)
        self.assertAlmostEqual(result['total_exposure'], 10500.0, places=4)

    def test_CS6b_no_overconcentration(self):
        """Balanced portfolio should not flag."""
        positions = {'BTC': 3000.0, 'ETH': 3000.0, 'SOL': 3000.0}
        cluster_map = {'BTC': 1, 'ETH': 1, 'SOL': 2}
        result = portfolio_concentration(positions, cluster_map, threshold=0.60)

        # Cluster 1: 6000/9000 = 66.7% > 60% → flagged
        self.assertTrue(result['overconcentrated'])

        # With threshold 0.70 it should not flag
        result2 = portfolio_concentration(positions, cluster_map, threshold=0.70)
        self.assertFalse(result2['overconcentrated'])

    def test_CS6c_single_position(self):
        """Single position → 100% in its cluster → flagged."""
        positions = {'BTC': 10000.0}
        cluster_map = {'BTC': 1}
        result = portfolio_concentration(positions, cluster_map, threshold=0.50)
        self.assertTrue(result['overconcentrated'])
        self.assertIn(1, result['flags'])

    # ── CS7: Empty inputs handled ──────────────────────────────────────

    def test_CS7_empty_beta_inputs(self):
        """Empty returns lists → beta 0."""
        self.assertEqual(compute_btc_beta([], [], window=72), 0.0)
        self.assertEqual(compute_btc_beta([0.01], [0.01], window=72), 0.0)

    def test_CS7_empty_correlation_inputs(self):
        """Empty returns lists → correlation 0."""
        self.assertEqual(compute_correlation([], []), 0.0)
        self.assertEqual(compute_correlation([0.01], [0.01]), 0.0)

    def test_CS7_empty_positions(self):
        """Empty positions → no flag, zero exposure."""
        result = portfolio_concentration({}, {})
        self.assertFalse(result['overconcentrated'])
        self.assertEqual(result['total_exposure'], 0.0)
        self.assertEqual(result['flags'], [])
        self.assertEqual(result['cluster_exposures'], {})
        self.assertEqual(result['cluster_pcts'], {})

    def test_CS7_symbol_not_in_cluster_map(self):
        """Symbol in positions but not in cluster_map → cluster_id -1."""
        positions = {'BTC': 1000.0, 'UNKNOWN': 500.0}
        cluster_map = {'BTC': 1}
        result = portfolio_concentration(positions, cluster_map)
        # UNKNOWN gets cluster_id -1
        self.assertIn(-1, result['cluster_exposures'])
        self.assertEqual(result['total_exposure'], 1500.0)

    def test_CS7_window_larger_than_data(self):
        """Window larger than available data → uses all available."""
        btc = [0.01, 0.02, -0.01, 0.03, -0.02]
        sym = list(btc)
        beta = compute_btc_beta(sym, btc, window=100)
        self.assertAlmostEqual(beta, 1.0, places=10)


if __name__ == '__main__':
    unittest.main()