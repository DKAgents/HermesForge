"""
US-223 — performance_report leads with fill-realistic R, never the optimistic
gauntlet_r.

Asserts:
  (a) the headline number equals the summed bar-level hostile_r (not gauntlet_r),
      even when the two disagree by a large margin;
  (b) an unavailable fill-realistic R renders an explicit "unavailable" message,
      NOT an optimistic gauntlet_r fallback.

Run: python3 scripts/paper_trading/tests/test_performance_report_fill_realistic.py
"""

import sys
import os
import json
import tempfile
import pathlib
import contextlib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import performance_report as pr


def _write_ledger(path, rows):
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


@contextlib.contextmanager
def _ledgers(swing_rows=(), strq_rows=()):
    """Temporarily point pr.STRQ_LEDGER / pr.SWING_LEDGER at temp jsonls."""
    swing = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
    strq = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
    if swing_rows:
        _write_ledger(swing.name, swing_rows)
    if strq_rows:
        _write_ledger(strq.name, strq_rows)
    _swing, _strq = pr.SWING_LEDGER, pr.STRQ_LEDGER
    pr.SWING_LEDGER = pathlib.Path(swing.name)
    pr.STRQ_LEDGER = pathlib.Path(strq.name)
    try:
        yield
    finally:
        pr.SWING_LEDGER, pr.STRQ_LEDGER = _swing, _strq
        os.unlink(swing.name)
        os.unlink(strq.name)


def _closed_row(strategy_id, key, gauntlet_r):
    """A minimal closed trade row for resolve_fill_realistic()."""
    return {
        "strategy_id": strategy_id,
        "r_multiple": str(gauntlet_r),
        "gauntlet_r": str(gauntlet_r),
        "signal_id": key,
        "trade_id": key,
    }


def test_headline_is_fill_realistic_not_gauntlet():
    """When hostile_r is available, the headline equals summed hostile_r,
    even though gauntlet_r is wildly more optimistic."""
    with _ledgers(
        swing_rows=[
            {"trade_id": "STR-B-macd-histogram-divergence_AAPL_2026-09-28",
             "stage": "closed", "hostile_r": -2.0, "entry_date": "2026-09-28",
             "timestamp_utc": "2026-09-29T00:00:00+00:00"},
            {"trade_id": "STR-B-macd-histogram-divergence_MSFT_2026-09-29",
             "stage": "closed", "hostile_r": -1.0, "entry_date": "2026-09-29",
             "timestamp_utc": "2026-09-30T00:00:00+00:00"},
        ],
    ):
        closed = [
            _closed_row("STR-B-macd-histogram-divergence",
                        "STR-B-macd-histogram-divergence_AAPL_2026-09-28", 500.0),
            _closed_row("STR-B-macd-histogram-divergence",
                        "STR-B-macd-histogram-divergence_MSFT_2026-09-29", 500.0),
        ]
        resolution = pr.resolve_fill_realistic(closed)
        headline = "\n".join(pr._emit_fill_realistic_headline(resolution))

        assert resolution["summary"]["available"] is True
        # Headline shows the hostile sum (-3.00), NOT the optimistic +1000.
        assert "-3.00R" in headline
        assert "1000.0" not in headline
        assert "+3.00R" not in headline
        # The gauntlet_r total lives only in the secondary emitter.
        secondary = "\n".join(pr._emit_gauntlet_secondary(resolution))
        assert "+1000.00R" in secondary
        assert "NOT fill-realistic" in secondary


def test_unavailable_fill_realistic_is_explicit_not_optimistic_fallback():
    """No ledger rows resolvable -> explicit 'unavailable' headline, never a
    gauntlet_r number in the headline slot."""
    with _ledgers(
        swing_rows=[
            {"trade_id": "STR-B-macd-histogram-divergence_AAPL_2026-09-28",
             "stage": "skip", "hostile_r": None, "entry_date": "2026-09-28",
             "timestamp_utc": "2026-09-29T00:00:00+00:00"},
        ],
    ):
        closed = [
            _closed_row("STR-B-macd-histogram-divergence",
                        "STR-B-macd-histogram-divergence_AAPL_2026-09-28", 500.0),
        ]
        resolution = pr.resolve_fill_realistic(closed)
        headline = "\n".join(pr._emit_fill_realistic_headline(resolution))

        assert resolution["summary"]["available"] is False
        assert "unavailable" in headline
        # The optimistic number must NOT appear in the headline slot.
        assert "500.0" not in headline
        assert "+500.00R" not in headline


def test_build_report_leads_with_fill_realistic():
    """End-to-end: build_report() leads with the fill-realistic headline and the
    optimistic gauntlet number is demoted to the secondary section."""
    with _ledgers(
        swing_rows=[
            {"trade_id": "STR-B-macd-histogram-divergence_AAPL_2026-09-28",
             "stage": "closed", "hostile_r": -2.0, "entry_date": "2026-09-28",
             "timestamp_utc": "2026-09-29T00:00:00+00:00"},
        ],
    ):
        orig_rows = pr._rows
        pr._rows = lambda: [
            {"strategy_id": "STR-B-macd-histogram-divergence",
             "trade_id": "STR-B-macd-histogram-divergence_AAPL_2026-09-28",
             "signal_id": "STR-B-macd-histogram-divergence_AAPL_2026-09-28",
             "status": "closed", "exit_date": "2026-09-30",
             "gauntlet_r": "500.0", "r_multiple": "500.0",
             "entry_date": "2026-09-28",
             "ticker": "AAPL", "asset_class": "stock", "position_size_pct": "1.0",
             "direction": "long"},
        ]
        try:
            report = pr.build_report(since_date=None)
        finally:
            pr._rows = orig_rows

        # Fill-realistic headline appears before the cost-adjusted section.
        assert report.index("Fill-Realistic R") < report.index("Cost-adjusted only")
        assert "NOT fill-realistic" in report
        assert "-2.00R" in report


if __name__ == "__main__":
    import inspect
    funcs = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    for fn in funcs:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"all {len(funcs)} performance_report fill-realistic tests passed")