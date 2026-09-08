# STR-20260908-SKEW-PREDICTED: Predicted Skewness Factor

**Status:** WATCH (experimental, 0.25% risk)
**Deployed:** 2026-09-08
**Scanner:** `scanner_skew_predicted.py`
**Paper Trading:** `capture_signals.py` (via frontmatter discovery)
**Sizing:** `position_sizing.py` → `size_strategy_skewp` (0.25%)
**Regime:** `regime_strategy_selector.py` → `STR-SKEWP`

## Backtest Results

| Test | Mean R | p-value | Verdict |
|------|--------|---------|---------|
| Phase 1A | +0.079 | 0.0 | ❌ KILL (friction-flagged, avg R < 0.2) |
| Walk-Forward OOS | +0.0457 | 0.0005 | ✅ ROBUST EDGE (overall) |
| 2022 OOS | +0.0045 | 0.869 | ❌ NO EDGE |
| 2023 OOS | +0.0213 | 0.458 | ❌ NO EDGE |
| 2024 OOS | +0.0719 | 0.017 | ✅ ROBUST EDGE |
| 2025 OOS | +0.0959 | 0.001 | ✅ ROBUST EDGE |
| 2026 OOS | +0.0290 | 0.402 | ❌ NO EDGE |

## Key Limitations
1. **Tiny effect size** — OOS mean R = 0.0457 means ~0.05R per trade on average. With 12bp round-trip costs, the net edge is near zero.
2. **Regime-dependent** — 3/5 windows show NO EDGE; the edge only appeared in 2024-2025 bull market.
3. **No short-term practical edge** — friction-flagged in Phase 1A means transaction costs likely eliminate any edge.
4. **Academic paper effect** — the original paper's +5.45%/yr result is based on 18 anomalies across 5,000+ stocks. Our single-factor replication on 529 stocks shows much weaker results.

## Next Steps
- Monitor paper trading performance for 3 months
- If avg R < 0 in paper trading, kill the strategy
- Consider as a factor weighting technique (not standalone strategy)
- Potential combination with STR-Q (momentum) — skewness-weighted momentum