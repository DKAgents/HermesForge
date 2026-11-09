"""test_mde.py — Tests for the US-06 M-5 minimum-detectable-effect helper."""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import mde  # noqa: E402


class TestMDE(unittest.TestCase):

    def test_mde_sharpe_scales_with_sqrt_n(self):
        """MDE Sharpe halves when n quadruples (1/sqrt(n) scaling)."""
        m1 = mde.mde_sharpe(100)
        m4 = mde.mde_sharpe(400)
        self.assertAlmostEqual(m1, 2.0 * m4, places=6)

    def test_mde_sharpe_matches_closed_form(self):
        """Default alpha=0.05, beta=0.20 -> 2.8016 / sqrt(n)."""
        n = 300
        expected = (1.95996 + 0.84162) / math.sqrt(n)
        self.assertAlmostEqual(mde.mde_sharpe(n), expected, places=4)

    def test_mde_sharpe_dsr_increases_with_trials(self):
        """More prior trials -> larger MDE (selection deflation)."""
        self.assertGreater(mde.mde_sharpe_dsr(300, 168),
                           mde.mde_sharpe_dsr(300, 1))

    def test_mde_sharpe_dsr_exceeds_single(self):
        """DSR-deflated MDE is always >= single-hypothesis MDE."""
        self.assertGreaterEqual(mde.mde_sharpe_dsr(300, 168),
                                mde.mde_sharpe(300, 168))

    def test_mde_ic_breadth_scaling(self):
        """IC MDE scales by 1/sqrt(breadth)."""
        b1 = mde.mde_ic(300, 168, breadth=1.0)
        b30 = mde.mde_ic(300, 168, breadth=30.0)
        self.assertAlmostEqual(b1, math.sqrt(30.0) * b30, places=6)

    def test_ic_sharpe_roundtrip(self):
        """ic_to_sharpe / sharpe_to_ic are inverses."""
        ic = 0.04
        self.assertAlmostEqual(mde.sharpe_to_ic(mde.ic_to_sharpe(ic, 9), 9), ic, places=9)
        self.assertAlmostEqual(mde.ic_to_sharpe(ic, 9), ic * 3.0, places=9)  # sqrt(9)

    def test_mde_from_sample_length_turnover(self):
        """sample_length * turnover -> n_observations."""
        # 1 year * 300 trades/year at 168 trials == mde_sharpe_dsr(300, 168)
        self.assertAlmostEqual(
            mde.mde_from_sample_length_turnover(1.0, 300.0, 168, metric="sharpe_dsr"),
            mde.mde_sharpe_dsr(300, 168), places=6)

    def test_format_null_verdict(self):
        s = mde.format_null_verdict(0.02, 0.635, "Sharpe")
        self.assertIn("not detected above MDE Sharpe = 0.6350", s)
        self.assertIn("+0.0200", s)

    def test_dsr_null_matches_known_scale(self):
        """E[max] grows roughly like sqrt(2 ln N) for large N."""
        e_max, _ = mde._dsr_null(168)
        # sanity: within a factor of 2 of the asymptotic sqrt(2 ln 168)=3.2
        self.assertTrue(2.0 < e_max < 5.0, f"E[max]={e_max}")


if __name__ == "__main__":
    unittest.main()
