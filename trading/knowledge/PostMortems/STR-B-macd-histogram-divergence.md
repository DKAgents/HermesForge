---
type: postmortem
source: postmortem
strategy_id: STR-B-macd-histogram-divergence
strategy_class: macd-histogram-divergence
signal_class: retail-ta
gate: G3
gate_subject: execution-realism
status: demoted
date: 2026-11-02
tags: [postmortem, feedback, generation, retail-ta]
confidence: high
topic: general
has_quotes: false
---
# STR-B MACD-Histogram-Divergence — Post-Mortem

Demoted at **G3 (execution-realism re-grade)** — not killed, but stripped of any sizeable-edge claim. The realistic-fill re-backtest (next-open entry + 3 bp stock cost + realistic exit) pinned the honest expectancy at **+0.38 R/trade long-only (t = 6.3)** and **+0.14 R/trade bidirectional (t = 5.3)**, roughly **3× / 9× below** the "+1.25 R robust edge" that had justified its size. The root reason is that the +1.25 R figure was produced by a close-entry / naive-exit implementation whose exit distribution was carried by a handful of unbounded time-exit winners priced off look-ahead fills (mean +0.88 vs median −0.68 pre-fix); under realistic fills the sign survives (positive in 7 of 8 years, ~48% win rate long-only) but the magnitude is a robust-yet-small residual. For a variant to pass, the realistic-fill expectancy would have to clear the sizing bar — a **magnitude** fix (e.g. a higher-quality confirmation that widens the genuine divergence edge, or reduced fill drag), not a sign fix — because +0.14–0.38 R/trade does not justify a 1%-risk base allocation.