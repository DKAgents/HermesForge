# LU-06b: Watch Strategies Require hostile_pass

**Status**: implemented (one loader change)
**Date**: 2026-09-25
**Campaign**: 2026-09-aegis-rebuild

`scripts/paper_trading/capture_signals.py` `_discover_strategies()` now skips
any `STR-*.md` with `status: watch` unless its frontmatter contains
`hostile_pass: true`. Live strategies are unaffected. No file has been given
`hostile_pass: true`; STR-Q stays as-is (un-killed, untouched).