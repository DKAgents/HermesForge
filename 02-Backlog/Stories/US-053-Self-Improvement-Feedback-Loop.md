---
id: US-053
type: user-story
epic: EPIC-006
status: backlog
priority: medium
effort: L
created: 2026-06-30
updated: 2026-06-30
assigned_to: ""
tags: [backlog, feedback-loop, lessons, backtesting, paper-trading, self-improvement]
---

# US-053: Self-Improvement Feedback Loop

## Story
**As a** systematic trader running backtests and paper trades,  
**I want** lessons extracted from trading activity to be automatically written back into the vault as structured knowledge notes linked to relevant strategies and concepts,  
**So that** the system learns from every trade and analysis session, the knowledge base reflects real-world performance, and future decisions are informed by accumulated experience rather than theory alone.

## Acceptance Criteria
- [ ] **AC1 — Lesson schema:** Define a `Lesson` frontmatter schema: `id`, `type: lesson`, `source` (backtest/paper-trade/analysis), `outcome` (confirms/contradicts/refines/new-finding), `related_strategy[]`, `related_notes[]`, `date`, `confidence`.
- [ ] **AC2 — Lesson template:** `Templates/Lesson-Template.md` with sections: `## What Happened`, `## What Was Expected`, `## What Was Learned`, `## Vault Updates Triggered`, `## Related Strategy`, `## Related Notes`.
- [ ] **AC3 — Lesson extractor:** A `extract_lessons.py` script (or Hermes prompt workflow) takes a structured input — a backtest result JSON, paper trade log entry, or free-text analysis — and uses a T2 LLM call to extract structured lessons conforming to the Lesson schema.
- [ ] **AC4 — Auto-write to vault:** Extracted lessons are written to `06-Journal/Lessons/YYYY-MM/` automatically, with wikilinks resolved against existing strategy and knowledge notes.
- [ ] **AC5 — Strategy update propagation:** After a lesson is written, if `outcome` is `contradicts` or `refines` for a specific strategy, a pending update entry is created in `05-Strategies/Pending-Updates/` (same mechanism as US-052 AC6).
- [ ] **AC6 — Knowledge reinforcement:** If a lesson `confirms` a Murphy rule or insight note, that note's frontmatter `confirmation_count` field is incremented (or added if missing). Notes with `confirmation_count ≥ 3` are flagged as `confidence: validated`.
- [ ] **AC7 — Repeatable trigger:** The extraction workflow can be triggered: (a) manually via CLI (`python extract_lessons.py --input trade_log.json`), (b) automatically after each paper trade session log is written to vault (file watcher or cron step in US-050 pipeline).
- [ ] **AC8 — Lesson index:** `06-Journal/00-Lesson-Index.md` lists all lessons via Dataview, filterable by outcome type, strategy, and date range.
- [ ] **AC9 — Feedback to Discovery:** Weekly, the Discovery Engine (US-051) includes confirmed/contradicted lessons as additional seed context when searching for new connections.

## Notes / Context
> The feedback loop is: Trade/Backtest → extract_lessons.py → Lesson note → strategy pending update → discovery seed → new insight → strategy update. This is the core self-improvement cycle.
>
> Initially this runs on paper trade logs from EPIC-003. But the lesson extractor should work on any structured or semi-structured input: a Discord message, a JSON backtest result, a free-text analysis session. The input format is normalized in AC3's LLM extraction step.
>
> `confirmation_count` on knowledge notes is a simple but powerful signal: Murphy rules that consistently predict profitable trades gain evidence weight; rules that are frequently contradicted by lessons get flagged for review.
>
> This story has a dependency on EPIC-003 (paper trade logs) for full value, but AC3/AC4/AC7a can be tested with synthetic trade inputs before EPIC-003 is complete.

## Dependencies
- **Blocks:** EPIC-005 US-044 (Forge Loop reflection uses lesson extraction as one of its steps)
- **Blocked by:** US-052 (lesson notes reference strategies; strategy structure must exist), US-050 (vault must be fresh)
- **Partial dependency:** EPIC-003 US-023 (paper trade logs; can use synthetic data initially)

## Definition of Done
- [ ] `extract_lessons.py` implemented, tested on ≥1 synthetic backtest result
- [ ] ≥2 lesson notes written to `06-Journal/Lessons/` with correct wikilinks
- [ ] Strategy pending-update mechanism works end-to-end
- [ ] `confirmation_count` incremented correctly on a confirmed knowledge note
- [ ] `00-Lesson-Index.md` Dataview query working
- [ ] Cron/auto-trigger documented and optionally registered
