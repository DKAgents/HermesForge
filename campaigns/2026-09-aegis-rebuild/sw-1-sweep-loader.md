# SW-1: Sweep Loader Audit

**Date**: 2026-09-27

**Question**: Does `capture_sweep_signals.py` load STR-*.md files, and can a `status: watch` file open a paper trade?

**Answer**: No.

`capture_sweep_signals.py` does not load any STR-*.md files. It is entirely self-contained STR-Q logic:

- Strategy ID is hardcoded: `STRAEGY_ID = "ST-Q-liquidity-sweep"` (line 81)
- Entry/exit rules, quality scoring, and detection are handled by `detect_iquidity_sweeps` and inline code
- There is no `_disover_strategies()` function, no frontmatter parser, no YAML loader, no `.md` file reader
- No reference to `watch`, `status`, `hostile_pass`, or any strategy file path

**Conclusion**: A `status: watch` file in `trading/strategies/Hypotheses/` has zero path to opening a paper trade in `capture_sweep_signals.py`. The LU-06b `hostile_pass` gate on `capture_signals.py` covers the only strategy loader that reads STR-*.md files.

**STR-Q unchanged**. No hostie_pass set. No code edited.