---
id: US-058
epic: EPIC-009
type: story
status: backlog
created: 2026-07-20
points: 2
tags: [discord, strategy, frontmatter, publish-control]
---

# US-058: Strategy Frontmatter — Publish Control Fields

## Story
As a strategy operator, I want to control which strategies post alerts to Discord and to which channel, via frontmatter fields in each strategy note, so that I can enable or disable publishing per strategy without touching code.

## Acceptance Criteria
- [ ] Two new frontmatter fields defined and documented:
  - `publish_enabled: true | false` — whether this strategy posts alerts to Discord
  - `publish_channel: stocks | crypto` — which channel to publish to
- [ ] `validate_strategy.py` updated to:
  - Accept (not require) these fields
  - Warn if `publish_enabled: true` but `publish_channel` is missing
  - Warn if `publish_channel` is not one of: stocks, crypto
- [ ] All four existing strategy notes updated with appropriate values:
  - STR-A (MA Pullback): `publish_enabled: false`, `publish_channel: stocks` (not yet validated enough)
  - STR-B (MACD Divergence): `publish_enabled: true`, `publish_channel: stocks` (Phase 1B passed)
  - STR-C (Breakout+Volume): `publish_enabled: false`, `publish_channel: stocks` (killed in Phase 1A)
  - STR-D (S/R Reversal): `publish_enabled: false`, `publish_channel: stocks` (watch band)
- [ ] ADR-003 updated to document new fields
- [ ] validate_strategy.py passes 4/4 with zero errors

## Definition of Done
- All strategy notes updated
- validate_strategy.py validates new fields
- Committed to main
