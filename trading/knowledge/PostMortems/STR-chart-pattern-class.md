---
type: postmortem
source: postmortem
strategy_id: STR-chart-pattern-class
strategy_class: chart-pattern
signal_class: chart-pattern
gate: G0
gate_subject: cost-and-capacity
status: failed
date: 2026-11-02
tags: [postmortem, feedback, generation, chart-pattern]
confidence: high
topic: general
has_quotes: false
---
# Chart-Pattern Class (16 strategies) — Post-Mortem

Died at **G0 (cost pre-screen)**, exposed retroactively at **G3**. The 16 chart-pattern strategies (STR-R, STR-T, STR-U, STR-V, STR-W, STR-AB, STR-AG, STR-AJ plus the "already-trusted" STR-X/Z/AA/AC/AD/AE/AF) were promoted to LIVE on **frictionless, close-entry** out-of-sample R-multiples of **0.08–0.22 R/trade** — edges that sit at or below realistic friction (~0.1–0.3 R/trade once the look-ahead close-entry drag and taker cost are applied), which the team's own US-114 scrub doc had already flagged as "thin-margin; Phase 1B must account for friction." The root reason is the class-level pattern, not any single bug: classic chart-pattern edges are small by nature and were promoted-and-died as a class because the friction accounting was never run before promotion. For a variant to pass, the gross out-of-sample edge would have to clear realistic friction by a real margin — i.e., a **net-positive R under next-open, trade-through, costed fills materially above ~0.3 R** (roughly 2–3× the 0.08–0.22 R tier these class members actually carried), or a venue/fill where per-trade cost is a small fraction of the edge; until then this entire mechanism class is hard-blocked at intake (US-191).