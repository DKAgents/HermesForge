"""US-197 — Stop purging 5m bars; retain all going forward.

Asserts the store's retention invariant directly against a THROWAWAY temp dir
(NEVER the production ~/.hermes/market_data/hl_bars):

  1. Bars far apart in time BOTH remain queryable — i.e. there is no purge /
     delete / trim horizon. An old bar stays readable.
  2. `append_bars` is idempotent and never deletes — row count is monotonic
     non-decreasing across re-appends (INSERT OR IGNORE, no DELETE exists).

These are the two behavioral guarantees the story's "unbounded, disk-limited"
acceptance criterion reduces to. Uses only stdlib `unittest` (no pytest dep),
so it runs on any interpreter (interpreter-drift-safe, cf. US-163).
"""

import importlib.util
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

_SPEC = importlib.util.spec_from_file_location(
    "hl_bar_store", str(REPO / "scripts" / "data" / "hl_bar_store.py"))
hl_bar_store = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(hl_bar_store)


def _bar(ts, o=1.0):
    return {"ts": ts, "open": o, "high": o, "low": o, "close": o,
            "volume": 1.0, "trades": 1}


class RetentionTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="hlbars_retention_")
        self._saved = hl_bar_store.STORE_DIR
        hl_bar_store.STORE_DIR = Path(self._tmp)
        self.conn = hl_bar_store.open_store("5m")

    def tearDown(self):
        self.conn.close()
        hl_bar_store.STORE_DIR = self._saved

    def test_old_bar_remains_queryable_no_purge(self):
        t0 = 1_700_000_000_000          # far in the past
        t1 = t0 + 30 * 86400_000        # +30 days
        hl_bar_store.append_bars(self.conn, "BTC", "5m", [_bar(t0), _bar(t1)])
        df = hl_bar_store.read_bars("BTC", "5m")
        self.assertEqual(len(df), 2, "expected 2 bars retained")
        self.assertEqual(df["ts"].min(), t0, "oldest bar was purged")

    def test_append_is_idempotent_and_never_deletes(self):
        bars = [_bar(1_700_000_000_000 + i * 300_000) for i in range(5)]
        n1 = hl_bar_store.append_bars(self.conn, "BTC", "5m", bars)
        self.assertEqual(n1, 5)
        n2 = hl_bar_store.append_bars(
            self.conn, "BTC", "5m",
            bars + [_bar(1_700_000_000_000 + 5 * 300_000)])
        self.assertEqual(n2, 1, "existing keys must insert 0")
        df = hl_bar_store.read_bars("BTC", "5m")
        self.assertEqual(len(df), 6, "row count must only grow")
        self.assertEqual(df["ts"].min(), 1_700_000_000_000)


if __name__ == "__main__":
    unittest.main()