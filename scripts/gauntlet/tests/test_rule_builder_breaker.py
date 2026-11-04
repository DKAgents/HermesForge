"""
test_rule_builder_breaker.py — US-222 synthetic acceptance (fixtures A & B).

Hermetic and deterministic (seeded): no network, no real record, no store I/O.

  Fixture A (KNOWN rule): synthesize an OHLC/funding/OI series, generate the
    record by applying sma_cross_above(n=10). The builder must recover the exact
    feature family (SMA-cross) + parameter (n=10), and the breaker must confirm
    the rule holds OOS (advance).

  Fixture B (OVERFIT): the record's TRAIN half carries a spurious deterministic
    SMA-cross pattern (high IS agreement by construction), but the OOS half is
    seeded coin-flip noise (zero signal). The builder may rebuild it (high IS),
    but the breaker must KILL it (agreement_OOS collapses below the no-skill
    baseline).

The structural invariants (§5.3) are the acceptance: A recovered + confirmed,
B killed OOS. Threshold magnitudes are the documented Q5/Q6 constants, not the
test's assertions.
"""

import os
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import rule_builder as rb
import breaker_harness as bh


# ---------------------------------------------------------------------------
# Seeded synthetic series + record generators
# ---------------------------------------------------------------------------

def make_series(n, seed):
    """Deterministic OHLC random walk + funding noise + OI random walk."""
    rng = random.Random(seed)
    close = []
    price = 100.0
    for _ in range(n):
        price *= (1 + rng.gauss(0, 0.01))
        close.append(price)
    open_ = [close[0]] + close[:-1]
    high = [max(o, c) * (1 + abs(rng.gauss(0, 0.002))) for o, c in zip(open_, close)]
    low = [min(o, c) * (1 - abs(rng.gauss(0, 0.002))) for o, c in zip(open_, close)]
    funding = [rng.gauss(0.0001, 0.00005) for _ in range(n)]
    oi = []
    oiv = 10000.0
    for _ in range(n):
        oiv *= (1 + rng.gauss(0, 0.01))
        oi.append(oiv)
    # 1h bars, ms epoch, ascending
    ts = [1_700_000_000_000 + i * 3_600_000 for i in range(n)]
    return rb.BarSeries(ts, open_, high, low, close, funding, oi)


def make_record(instrument, states, ts):
    """Build the canonical record dict from a per-bar state list."""
    dmap = {1: "long", -1: "short", 0: "flat", None: "flat"}
    records = [{"timestamp": ts[i], "direction": dmap[s]}
               for i, s in enumerate(states)]
    return {
        "instrument": instrument, "venue": "hyperliquid",
        "asset_class": "crypto", "timeframe": "1h", "source": "record",
        "records": records,
    }


# ---------------------------------------------------------------------------
# Fixture A — KNOWN rule: recover AND confirm OOS
# ---------------------------------------------------------------------------

def test_fixture_A_known_rule_recovered_and_confirmed():
    n = 600
    series = make_series(n, seed=1234)
    true_states = rb.apply_feature(series, "sma_cross_above", {"n": 10})
    record = make_record("BTC", true_states, series.ts)

    result = rb.reconstruct(record, series)
    assert result["status"] == "ok", f"builder failed: {result.get('reason')}"
    rule = result["rule"]

    # Builder pass: feature FAMILY exact (SMA-cross), param matches within grid.
    assert rule["feature"] == "sma_cross_above", \
        f"recovered family {rule['feature']!r} != sma_cross_above"
    assert rule["params"]["n"] == 10, \
        f"recovered n={rule['params']['n']} != 10"
    assert rule["agreement_is"] >= 0.99, \
        f"agreement_is={rule['agreement_is']} should be ~1.0 on the true rule"

    # Breaker pass: the rule holds OOS (deterministic signal => advance).
    report = bh.run(record, series, run_gauntlet=False)
    assert report["verdict"] == "advance", \
        f"expected advance, got {report['verdict']}: {report['verdict_reason']}"
    assert report["agreement_oos"] >= 0.95, \
        f"agreement_oos={report['agreement_oos']} should be ~1.0 (real signal)"
    # Q7: reconstructed rule always diagnostic; retail-TA surfaced, never blocked.
    assert report["diagnostic"] is True
    assert report["signal_class"] == "retail-ta", \
        f"expected retail-ta signal class, got {report['signal_class']}"
    assert report["verdict"] == "advance", \
        "retail-TA rule must still be measured (advance), not silently blocked"

    print(f"A PASS: recovered {rule['feature']}(n={rule['params']['n']}), "
          f"agreement_is={rule['agreement_is']:.4f}, "
          f"agreement_oos={report['agreement_oos']:.4f}, "
          f"verdict={report['verdict']}")


# ---------------------------------------------------------------------------
# Fixture B — OVERFIT record: rebuild allowed, breaker must KILL
# ---------------------------------------------------------------------------

def test_fixture_B_overfit_noise_killed_oos():
    n = 600
    series = make_series(n, seed=5678)
    sma_states = rb.apply_feature(series, "sma_cross_above", {"n": 10})

    # Train half = deterministic SMA-cross (high IS by construction);
    # OOS half = seeded coin-flip noise (zero signal). Align to the builder's
    # own chronological-midpoint split so the spurious pattern never leaks OOS.
    min_ts = series.ts[0]
    max_ts = series.ts[-1]
    t_split = min_ts + (max_ts - min_ts) * rb.SPLIT_FRACTION
    rng = random.Random(99)
    states = []
    for i, ts in enumerate(series.ts):
        if ts < t_split:
            states.append(sma_states[i])
        else:
            states.append(rng.choice([-1, 0, 1]))
    record = make_record("BTC", states, series.ts)

    result = rb.reconstruct(record, series)
    # Builder MAY rebuild it (high IS agreement expected).
    assert result["status"] == "ok", f"builder should rebuild: {result.get('reason')}"
    assert result["rule"]["agreement_is"] >= 0.90, \
        f"high IS agreement expected by construction, got {result['rule']['agreement_is']}"

    # Breaker pass = it KILLS it: OOS agreement collapses below no-skill baseline.
    report = bh.run(record, series, run_gauntlet=False)
    baseline = report["no_skill_baseline"]["baseline"]
    assert report["verdict"] == "kill", \
        f"expected kill, got {report['verdict']}: {report['verdict_reason']}"
    assert report["advance"] is False
    assert report["agreement_oos"] < baseline, \
        f"agreement_oos={report['agreement_oos']} should be < baseline={baseline}"

    print(f"B PASS: agreement_is={report['agreement_is']:.4f}, "
          f"agreement_oos={report['agreement_oos']:.4f}, "
          f"baseline={baseline:.4f}, verdict={report['verdict']}")


# ---------------------------------------------------------------------------
# Fail-closed data-gate (Q5) + series requirement (Q8)
# ---------------------------------------------------------------------------

def test_flat_record_is_data_gated():
    """A record flat throughout has 0 transitions -> declined, never scored."""
    n = 200
    series = make_series(n, seed=1)
    states = [0] * n  # flat everywhere
    record = make_record("BTC", states, series.ts)
    result = rb.reconstruct(record, series)
    assert result["status"] == "data_gated", f"got {result['status']}: {result.get('reason')}"
    assert "transition" in result["reason"].lower()
    print(f"flat-record PASS: {result['reason']}")


def test_missing_series_is_data_gated():
    """Q8: no series -> data-gated, never imputed."""
    series = make_series(200, seed=2)
    record = make_record("BTC", rb.apply_feature(series, "sma_cross_above", {"n": 10}),
                         series.ts)
    result = rb.reconstruct(record, None)
    assert result["status"] == "data_gated"
    assert "series" in result["reason"].lower()
    print(f"missing-series PASS: {result['reason']}")


def test_param_hash_stable_and_distinct():
    """Every rule carries a fresh, stable param_hash (invariant)."""
    h1 = rb.param_hash("sma_cross_above", {"n": 10})
    h2 = rb.param_hash("sma_cross_above", {"n": 10})
    h3 = rb.param_hash("sma_cross_above", {"n": 20})
    h4 = rb.param_hash("momentum", {"n": 10, "k_bps": 50})
    assert h1 == h2, "same feature+params must hash identically"
    assert h1 != h3 and h1 != h4, "different params/features must hash differently"
    print(f"param_hash PASS: {h1} (n=10) vs {h3} (n=20) vs {h4} (momentum)")


# ---------------------------------------------------------------------------
# Gauntlet handoff: fees charged (Q9) + trial written (no network)
# ---------------------------------------------------------------------------

def _gauntlet_handoff_checks(ledger_path):
    """Run the fee-charging handoff checks against an isolated ledger path.

    Shared by the pytest test and the __main__ runner. Patches fee_source (no
    HTTP) and trials_ledger.LEDGER_PATH directly, restoring afterwards.
    """
    import fee_source
    import trials_ledger

    orig_costs = fee_source.get_venue_costs
    orig_ledger = trials_ledger.LEDGER_PATH
    orig_ledger_dir = trials_ledger.LEDGER_DIR
    try:
        fee_source.get_venue_costs = lambda: fee_source.FAIL_CLOSED_FALLBACK
        trials_ledger.LEDGER_PATH = ledger_path
        trials_ledger.LEDGER_DIR = ledger_path.parent

        n = 600
        series = make_series(n, seed=1234)
        true_states = rb.apply_feature(series, "sma_cross_above", {"n": 10})
        record = make_record("BTC", true_states, series.ts)

        result = rb.reconstruct(record, series)
        rule = dict(result["rule"])
        rule["instrument"] = "BTC"

        gauntlet = bh.hand_to_gauntlet(rule, series, asset_class="crypto",
                                       timeframe="1h")

        trades = bh.reconstruct_trades(
            rb.apply_feature(series, rule["feature"], rule["params"]),
            series, asset_class="crypto")
        gross_total = sum(t["gross_bps"] for t in trades)
        net_total = sum(t["pnl_bps"] for t in trades)
        rt = fee_source.get_round_trip_bps("crypto")
        assert rt > 0
        # every round trip is reduced by exactly the round-trip taker fee
        assert abs((gross_total - net_total) - rt * len(trades)) < 1e-6, \
            "fees must be charged via fee_source (taker round-trip)"
        assert gauntlet["trial"] is not None and "error" not in gauntlet["trial"]
        assert trials_ledger.count() == 1, "exactly one trial per run"

        print(f"handoff PASS: {len(trades)} trades, gross={gross_total:.1f} bps, "
              f"net={net_total:.1f} bps, rt_fee={rt} bps/trade, trial written")
    finally:
        fee_source.get_venue_costs = orig_costs
        trials_ledger.LEDGER_PATH = orig_ledger
        trials_ledger.LEDGER_DIR = orig_ledger_dir


def test_gauntlet_handoff_charges_fees_and_writes_trial(tmp_path):
    """Fixture A rule advances -> handoff charges fees and writes one trial."""
    _gauntlet_handoff_checks(tmp_path / "trials.jsonl")


if __name__ == "__main__":
    import tempfile
    from pathlib import Path as _P
    print("US-222 synthetic acceptance fixtures\n")
    test_fixture_A_known_rule_recovered_and_confirmed()
    test_fixture_B_overfit_noise_killed_oos()
    test_flat_record_is_data_gated()
    test_missing_series_is_data_gated()
    test_param_hash_stable_and_distinct()
    with tempfile.TemporaryDirectory() as d:
        _gauntlet_handoff_checks(_P(d) / "trials.jsonl")
    print("\nAll US-222 fixture tests passed.")
