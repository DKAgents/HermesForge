---
id: US-085
epic: EPIC-013
type: story
status: done
created: 2026-08-06
points: 8
tags: [backlog, story]
---

# US-085: Research Pipeline

## Story
**As a** strategy research system,
**I want** an automated research pipeline that screens factors, tests killed strategies for revival, monitors edge decay, and generates hypothesis combinations,
**So that** new trading edges are discovered without manual intervention.

## Acceptance Criteria
- [x] 5 modules built: `factor_screener.py`, `revival_tester.py`, `decay_monitor.py`, `hypothesis_generator.py`, `research_runner.py`
- [x] Weekly cron registered (ID `9202661b7823`, Sundays 12:00 UTC)
- [x] First run completed in 276s, producing 8 action items
- [x] RSI14 inverted finding surfaced (strongest factor but inverted — momentum-dominant regime)
- [x] STR-N fragile revival detected (Mean R=0.41, p=0.064, 71% hit rate)
- [x] All 4 monitored strategies confirmed stable

## Notes / Context
> Commit 7942f30. Key findings: RSI14 strongest but inverted (momentum-dominant regime), STR-N showing fragile edge (Mean R=0.41, p=0.064, 71% hit rate), all 4 monitored strategies stable. First pipeline run validates the end-to-end research loop.

## Dependencies
- Blocks: US-086 (publisher depends on pipeline output)
- Blocked by: None

## Definition of Done
- [x] Code/config implemented
- [x] Tests passing (paper mode verified)
- [x] Risk Guardian reviewed (if applicable)
- [x] Documented in vault
- [x] ADR created (if architectural decision)
