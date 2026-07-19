---
id: US-056
epic: EPIC-007
type: story
status: backlog
created: 2026-07-20
points: 3
tags: [validation, analysis, phase1a, decisions]
depends-on: US-055
---

# US-056: Phase 1A Results Analysis + Kill/Pass Decisions

## Story
As a strategy validator, I need a structured analysis of Phase 1A scanner results so that I can make documented kill/pass/watch decisions for each strategy before committing to Phase 1B work.

## Acceptance Criteria
- [ ] Analysis script reads all four Phase 1A CSVs and produces a summary report
- [ ] Report shows per strategy: signal count/year, avg R, median R, win rate, sub-period breakdown
- [ ] Kill/pass/watch classification applied per ADR-004 criteria
- [ ] Kill: < 12 signals/year OR avg R < 0.2
- [ ] Watch: 12–24 signals/year OR avg R 0.2–0.4
- [ ] Pass: >= 25 signals/year AND avg R >= 0.6 AND positive in >= 2 of 3 sub-periods
- [ ] Friction sensitivity flag: strategies with avg R < 0.5 flagged for Phase 1B cost check
- [ ] Decision documented in `06-Strategies/Hypotheses/STR-XXX.md` (Phase 1A Results section added)
- [ ] Enhancement backlog updated with findings (00-Enhancement-Backlog.md)
- [ ] Kill decisions move strategy to `06-Strategies/Deprecated/`
- [ ] Watch/Pass strategies advance to Phase 1B planning

## Output Format
Markdown report saved to `scripts/validation/results/phase1a-summary.md` with:
- Per-strategy table (frequency, R stats, sub-period, classification)
- Recommended Phase 1B sequence (which strategies, which Open Questions)
- Pre-registered perturbations for Phase 1B (locked before running)

## Definition of Done
- Summary report generated and readable
- Kill/pass/watch decision recorded for all 4 strategies
- Strategy notes updated with Phase 1A Results section
- Committed to main
