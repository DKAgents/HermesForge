---
type: strategy-update-suggestion
strategy: STR-20260719-sr-role-reversal-entry
lesson: LSN-2026-07-19-earnings-catalyst-overrides-technical-role-reversa-c8b706
outcome: refines
date: 2026-07-19
reviewed: false
tags: [pending-update, strategy, feedback-loop]
---

# Pending Update: STR-20260719-sr-role-reversal-entry

## Triggering Lesson

[[LSN-2026-07-19-earnings-catalyst-overrides-technical-role-reversa-c8b706]] — *Earnings Catalyst Overrides Technical Role-Reversal Setup*

**Outcome:** This lesson **refines** the strategy.

## What Was Learned

A pre-trade earnings calendar check must be added as a mandatory binary filter to the role-reversal entry criteria — if earnings are within 7 days, the trade should be skipped regardless of technical validity. Fundamental catalysts such as earnings guidance revisions can instantly invalidate technically correct setups and produce gap-through stops. The strategy needs an explicit 'no-trade' condition: do not enter short role-reversal setups on individual stocks within 7 days of a scheduled earnings event.

## Suggested Action

Review [[STR-20260719-sr-role-reversal-entry]] and consider:
- Does the `## Entry Criteria` need a new condition or filter?
- Does the `## Counter-Evidence` section need updating?
- Should a new note be added to `## Supporting Evidence`?

Update the strategy's `## Change Log` after making any changes.
Mark `reviewed: true` in this file's frontmatter once resolved.
