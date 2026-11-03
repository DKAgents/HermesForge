---
type: postmortem
source: postmortem
strategy_id: STR-xsmom-cross-sectional
strategy_class: cross-sectional-momentum
signal_class: systematic
gate: G4
gate_subject: cpcv
status: failed
date: 2026-11-02
tags: [postmortem, feedback, generation, cross-sectional-momentum]
confidence: high
topic: general
has_quotes: false
---
# Cross-Sectional Momentum (Raw) — Post-Mortem

**Passed G3, failed G4/G5 (overfit controls)**, and was demoted to Hypothesis. The cost-aware construction cleared G3 (realistic mean net R +0.59, pessimistic PF 1.34) but failed the overfit controls: CPCV 10th-percentile split PF **0.72 < 1.0** (G4), PBO **0.56 > 0.30** and DSR **0.66 < 0.95** (G5). The root reason is that the apparent ~22%/yr edge is **directional Bitcoin beta, not cross-sectional alpha**: the P&L is concentrated in BTC bull regimes (bull +1.39 R / PF 1.82 vs bear −0.17 R / neutral −0.36 R), and per-name rolling 30-day BTC betas are almost all ≥ +1.3 (ENA +3.0, NEAR +2.9, OP +2.7), so the "long the top decile" construction is a long-beta directional book that does not generalize out-of-sample. For a variant to pass, the cross-sectional spread must prove alpha that is **independent of the market beta** — a beta-hedged or market-neutral long-short form with the beta residual removed before scoring — and must clear the DSR/PBO thresholds on that beta-free edge, not merely re-harvest the BTC trend.