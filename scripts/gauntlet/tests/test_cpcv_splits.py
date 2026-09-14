"""
test_cpcv_splits.py — Tests for CPCV harness (PROP-001 Strategy Gauntlet).

11 tests covering split generation, purge/embargo, path reconstruction,
metric computation, PBO, and DSR.
"""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from cpcv_harness import (
    compute_dsr,
    compute_pbo,
    compute_split_metrics,
    generate_cpcv_splits,
    purge_and_embargo,
    reconstruct_paths,
    run_cpcv,
    split_trades_into_groups,
)


# ── Synthetic trade data helpers ────────────────────────────────────────────

def make_trades(n: int = 120, seed: int = 42) -> list[dict]:
    """
    Generate n chronologically ordered synthetic trades.

    Each trade has: entry_time, exit_time, pnl_bps.
    Timestamps are sequential; pnl alternates to give known win_rate and avg.
    """
    trades = []
    for i in range(n):
        entry = i * 10
        exit_t = entry + 5 + (i % 3)  # variable holding period
        pnl = 10.0 if i % 2 == 0 else -5.0  # predictable pattern
        trades.append({
            "entry_time": entry,
            "exit_time": exit_t,
            "pnl_bps": pnl,
        })
    return trades


def make_trades_with_known_metrics() -> list[dict]:
    """
    Generate trades with easily verifiable metrics:
    All wins = +10, no losses → sharpe = inf, pf can verify.
    6 trades, all winning.
    """
    return [
        {"entry_time": i * 10, "exit_time": i * 10 + 5, "pnl_bps": 10.0}
        for i in range(6)
    ]


def make_trades_mixed() -> list[dict]:
    """Mixed wins and losses for realistic metric testing."""
    pnls = [10.0, -5.0, 10.0, -3.0, 8.0, -2.0, 12.0, -4.0, 6.0, -1.0]
    return [
        {"entry_time": i * 10, "exit_time": i * 10 + 5, "pnl_bps": pnls[i]}
        for i in range(len(pnls))
    ]


# ── Test class ──────────────────────────────────────────────────────────────

class TestCPCVHarness(unittest.TestCase):
    """All CPCV harness tests."""

    # ── C1: split count ─────────────────────────────────────────────────

    def test_c1_split_count(self):
        """n_groups=12, k_test=2 produces exactly C(12,2) = 66 splits."""
        trades = make_trades(120)
        splits = generate_cpcv_splits(trades, n_groups=12, k_test=2)
        expected = math.comb(12, 2)  # 66
        self.assertEqual(
            len(splits), expected,
            f"Expected {expected} splits, got {len(splits)}",
        )

    # ── C2: splits are distinct ─────────────────────────────────────────

    def test_c2_splits_distinct(self):
        """No two splits have identical test group combinations."""
        trades = make_trades(120)
        splits = generate_cpcv_splits(trades, n_groups=12, k_test=2)
        test_group_sets = [frozenset(s["test_groups"]) for s in splits]
        self.assertEqual(
            len(test_group_sets), len(set(test_group_sets)),
            "Duplicate test group combinations found",
        )

    # ── C3: path count ──────────────────────────────────────────────────

    def test_c3_path_count(self):
        """reconstruct_paths produces 11 paths for n_groups=12, k_test=2."""
        trades = make_trades(120)
        splits = generate_cpcv_splits(trades, n_groups=12, k_test=2)
        paths = reconstruct_paths(splits)
        # Each group appears in k*C(N,k)/N = 2*66/12 = 11 paths
        # Path count is C(N-1, k_test-1) = C(11,1) = 11
        expected_paths = math.comb(12 - 1, 2 - 1)  # 11
        self.assertEqual(
            len(paths), expected_paths,
            f"Expected {expected_paths} paths, got {len(paths)}",
        )

    # ── C4: each path covers every trade exactly once ────────────────────

    def test_c4_full_coverage(self):
        """Each path's test groups cover all groups exactly once."""
        trades = make_trades(120)
        splits = generate_cpcv_splits(trades, n_groups=12, k_test=2)
        paths = reconstruct_paths(splits)

        n_groups = 12
        k_test = 2

        for path_idx, path in enumerate(paths):
            # Verify each path has the right number of splits
            expected_splits_per_path = n_groups // k_test  # 6
            self.assertEqual(
                len(path), expected_splits_per_path,
                f"Path {path_idx}: expected {expected_splits_per_path} splits, got {len(path)}",
            )

            # Verify test groups are disjoint within each path
            all_test_groups: set[int] = set()
            for split in path:
                for g in split["test_groups"]:
                    self.assertNotIn(
                        g, all_test_groups,
                        f"Path {path_idx}: group {g} appears in multiple splits",
                    )
                    all_test_groups.add(g)

            # Verify all groups are covered
            self.assertEqual(
                all_test_groups, set(range(n_groups)),
                f"Path {path_idx}: not all groups covered; missing {set(range(n_groups)) - all_test_groups}",
            )

    # ── C5: purge removes trades within holding_horizon ──────────────────

    def test_c5_purge_holding_horizon(self):
        """Purge removes training trades closing within holding_horizon of test start."""
        # Train group: trades at t=0..4, exit at t=5..9
        train = [[
            {"entry_time": 0, "exit_time": 5, "pnl_bps": 10},
            {"entry_time": 1, "exit_time": 7, "pnl_bps": 10},
            {"entry_time": 8, "exit_time": 14, "pnl_bps": 10},
        ]]
        # Test group: trade at t=20, exit at t=25
        test = [[
            {"entry_time": 20, "exit_time": 25, "pnl_bps": 5},
        ]]

        # holding_horizon_bars = 10 → purge boundary = test_start(20) - 10 = 10
        # Trade 0: exit=5 < 10 → KEPT
        # Trade 1: exit=7 < 10 → KEPT
        # Trade 2: exit=14 >= 10 AND entry=8 <= 25 → PURGED (overlaps)
        clean = purge_and_embargo(train, test, holding_horizon_bars=10, embargo_bars=5)
        kept_times = sorted(t["entry_time"] for t in clean)
        self.assertEqual(kept_times, [0, 1], f"Expected [0, 1], got {kept_times}")

    # ── C6: embargo removes trades within embargo ────────────────────────

    def test_c6_embargo(self):
        """Embargo removes training trades opening within embargo_bars after test end."""
        train = [[
            {"entry_time": 0, "exit_time": 5, "pnl_bps": 10},
            {"entry_time": 28, "exit_time": 35, "pnl_bps": 10},  # opens right after test
            {"entry_time": 50, "exit_time": 55, "pnl_bps": 10},  # way after, safe
        ]]
        test = [[
            {"entry_time": 20, "exit_time": 25, "pnl_bps": 5},
        ]]

        # embargo_bars = 10 → embargo boundary = test_end(25) + 10 = 35
        # Trade at entry=28: 28 <= 35 AND 28 > 25 → EMBARGOED
        # Trade at entry=50: 50 > 35 → KEPT
        clean = purge_and_embargo(train, test, holding_horizon_bars=5, embargo_bars=10)
        kept_times = sorted(t["entry_time"] for t in clean)
        self.assertIn(0, kept_times, "Trade at entry=0 should be kept")
        self.assertIn(50, kept_times, "Trade at entry=50 should be kept")
        self.assertNotIn(28, kept_times, "Trade at entry=28 should be embargoed")

    # ── C7: no train touches test after purge+embargo ────────────────────

    def test_c7_no_overlap(self):
        """After purge+embargo, no training index is in the test index set."""
        trades = make_trades(120)
        splits = generate_cpcv_splits(trades, n_groups=12, k_test=2)

        for split in splits:
            train_set = set(split["train_indices"])
            test_set = set(split["test_indices"])
            overlap = train_set & test_set
            self.assertEqual(
                len(overlap), 0,
                f"Overlap found: {overlap} in split with test_groups={split['test_groups']}",
            )

    # ── C8: split metrics on known data ──────────────────────────────────

    def test_c8_metrics_on_known_data(self):
        """compute_split_metrics produces correct values on known data."""
        # All wins: 6 trades at +10 each
        trades = make_trades_with_known_metrics()
        split = {
            "test_trades": trades,
            "test_indices": list(range(len(trades))),
        }
        m = compute_split_metrics(split)
        self.assertEqual(m["avg_r"], 10.0)
        self.assertEqual(m["win_rate"], 1.0)
        self.assertEqual(m["trade_count"], 6)
        self.assertGreater(m["pf"], 0)  # all profit, pf > 0

        # Now test with mixed results
        mixed = make_trades_mixed()
        split2 = {
            "test_trades": mixed,
            "test_indices": list(range(len(mixed))),
        }
        m2 = compute_split_metrics(split2)
        pnls = [t["pnl_bps"] for t in mixed]
        expected_avg = sum(pnls) / len(pnls)
        self.assertAlmostEqual(m2["avg_r"], expected_avg, places=4)

        wins = sum(1 for p in pnls if p > 0)
        expected_wr = wins / len(pnls)
        self.assertAlmostEqual(m2["win_rate"], expected_wr, places=4)

        gross_profit = sum(p for p in pnls if p > 0)
        gross_loss = abs(sum(p for p in pnls if p < 0))
        expected_pf = gross_profit / gross_loss if gross_loss > 0 else 0.0
        self.assertAlmostEqual(m2["pf"], expected_pf, places=4)

    # ── C9: PBO on known rank distribution ──────────────────────────────

    def test_c9_pbo_known_distribution(self):
        """PBO computes correctly on a known rank distribution."""
        # All splits have identical Sharpe → ranks all 0 → PBO = 0
        metrics = [{"sharpe": 1.0} for _ in range(10)]
        pbo = compute_pbo(metrics)
        self.assertEqual(pbo, 0.0, f"PBO with identical Sharpes should be 0, got {pbo}")

        # Strictly declining Sharpes: [1.0, 0.9, 0.8, ..., 0.1]
        # Ranks: 0,1,2,...,9 (0=best)
        # IS rank vs OOS rank (next split): 0>1=F, 1>2=F, ..., 8>9=F, 9>0=T
        # Only 1/10 has IS rank worse than OOS → PBO = 0.1
        metrics2 = [{"sharpe": 1.0 - i * 0.1} for i in range(10)]
        pbo2 = compute_pbo(metrics2)
        self.assertAlmostEqual(pbo2, 0.1, places=4)

        # Strictly increasing: [0.0, 0.1, ..., 0.9]
        # Ranks: 9,8,...,0
        # IS rank > OOS rank: 9>8=T, 8>7=T, ..., 1>0=T, 0>9=F
        # 9/10 → PBO = 0.9
        metrics3 = [{"sharpe": i * 0.1} for i in range(10)]
        pbo3 = compute_pbo(metrics3)
        self.assertAlmostEqual(pbo3, 0.9, places=4)

    # ── C10: DSR with known inputs ──────────────────────────────────────

    def test_c10_dsr_known_inputs(self):
        """DSR matches expected value with known inputs (approximate)."""
        # With sharpe=0, DSR should be very low (poor strategy)
        dsr_low = compute_dsr(0.0, 0.0, 0.0, n_trials=100, n_observations=100)
        self.assertLess(dsr_low, 0.5, f"DSR with sharpe=0 should be < 0.5, got {dsr_low}")

        # With very high sharpe relative to trials, DSR should be high
        dsr_high = compute_dsr(2.0, 0.0, 0.0, n_trials=10, n_observations=500)
        self.assertGreater(dsr_high, 0.9, f"DSR with high sharpe should be > 0.9, got {dsr_high}")

        # Basic sanity: DSR ∈ [0, 1]
        test_cases = [
            (0.0, 0.0, 0.0, 1, 100),
            (1.0, 0.0, 0.0, 50, 200),
            (0.5, -0.5, 1.0, 100, 300),
            (1.5, 0.2, 2.0, 20, 150),
            (-0.5, 0.0, 0.0, 10, 100),
        ]
        for sharpe, skew, kurt, n_trials, n_obs in test_cases:
            dsr = compute_dsr(sharpe, skew, kurt, n_trials, n_obs)
            self.assertGreaterEqual(dsr, 0.0, f"DSR={dsr} < 0")
            self.assertLessEqual(dsr, 1.0, f"DSR={dsr} > 1")

        # With n_trials=1, DSR should be close to Φ(sharpe * √n_obs)
        # since E[max] ≈ 0 for single trial
        import math as _math
        from cpcv_harness import _norm_cdf

        dsr_single = compute_dsr(0.3, 0.0, 0.0, n_trials=1, n_observations=100)
        expected = _norm_cdf(0.3 * _math.sqrt(100))  # ≈ Φ(3.0) ≈ 0.9987
        self.assertGreater(dsr_single, 0.99, f"DSR single-trial should be ≈ {expected:.4f}, got {dsr_single}")

    # ── C11: empty trades returns clean empty ────────────────────────────

    def test_c11_empty_trades(self):
        """Empty trades list returns clean empty results."""
        result = run_cpcv([], n_groups=12, k_test=2)
        self.assertEqual(result["n_splits"], 0)
        self.assertEqual(result["n_paths"], 0)
        self.assertEqual(result["split_metrics"], [])
        self.assertEqual(result["pbo"], 0.0)
        self.assertEqual(result["splits"], [])

        # split_trades_into_groups with empty
        groups = split_trades_into_groups([], n_groups=12)
        self.assertEqual(len(groups), 12)
        for g in groups:
            self.assertEqual(g, [])

        # generate_cpcv_splits with empty
        splits = generate_cpcv_splits([], n_groups=12, k_test=2)
        self.assertEqual(splits, [])

        # reconstruct_paths with empty
        paths = reconstruct_paths([])
        self.assertEqual(paths, [])

        # compute_split_metrics with empty trades
        empty_split = {"test_trades": [], "test_indices": []}
        m = compute_split_metrics(empty_split)
        self.assertEqual(m["trade_count"], 0)
        self.assertEqual(m["sharpe"], 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)