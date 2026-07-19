---
id: LSN-2026-07-19-d62601
type: lesson
source: live-trade
outcome: confirms
related_strategy: ["STR-20260719-breakout-volume-trend"]
related_notes: ["INS-2026-07-19-volume-confirmation-as-binary-entry-gate-reducing-position-r", "INS-2026-07-19-multi-filter-breakout-system-with-volume-triggered-stop-plac", "RG032-3-to-1-reward-to-risk-ratio", "RG038-minimum-3-to-1-reward-to-risk-ratio", "RG036-let-profits-run-cut-losses-short", "RG009-responding-to-failed-patterns-exit-losing-trades-quickly", "RG010-accepting-false-signals-as-part-of-trading", "RG017-overboughtoversold-readings-in-strong-trends", "E014-volume-divergence-as-warning-signal", "E023-channel-breakout-systems-show-superior-results", "RG037-use-protective-stops-to-limit-losses", "RG043-exit-design-more-important-than-entry-design"]
date: 2026-07-19
confidence: high
confirmation_count: 0
tags: [lesson, feedback-loop, confirms]
---

# Volume and Weekly Trend Filter Confirm Breakout Edge

## What Happened

NVDA broke out of a bull flag on the daily chart on 2026-07-18 with 2.3x average volume, RSI at 62, and price above the 20-week MA. Entry at 138.5 with a stop at 134.2 and target at 151.4. The trade reached 150.8 by 2026-07-25, delivering 2.87R without the stop ever being threatened. A similar setup in META the same week was filtered out because META was below its 20-week MA; that breakout subsequently failed.

## What Was Expected

The strategy STR-20260719-breakout-volume-trend predicts that breakouts from consolidation patterns with volume confirmation (above-average volume on breakout bar) combined with a weekly trend filter (price above 20-week MA) produce high-probability, smooth-trending trades. The META filter outcome was specifically anticipated: setups failing the weekly trend condition were expected to carry meaningfully higher failure risk.

## What Was Learned

The combination of volume confirmation (≥2x average) and weekly trend alignment (price above 20-week MA) appears to be a robust dual-gate filter that both improves win rate and reduces trade stress, as evidenced by the position never threatening the stop. The META contrast in the same week provides a clean controlled comparison strengthening the causal case for the weekly trend filter specifically. Future execution should treat either filter failing as a hard no-entry condition, not a soft caution.

## Vault Updates Triggered

- [ ] [[STR-20260719-breakout-volume-trend]] — confirmation_count incremented
- [ ] [[INS-2026-07-19-volume-confirmation-as-binary-entry-gate-reducing-position-r]] — confirmation_count incremented
- [ ] [[INS-2026-07-19-multi-filter-breakout-system-with-volume-triggered-stop-plac]] — confirmation_count incremented
- [ ] [[RG032-3-to-1-reward-to-risk-ratio]] — confirmation_count incremented
- [ ] [[RG036-let-profits-run-cut-losses-short]] — confirmation_count incremented

## Related Strategy

- [[STR-20260719-breakout-volume-trend]] — outcome: confirms

## Related Notes

- [[INS-2026-07-19-volume-confirmation-as-binary-entry-gate-reducing-position-r]]
- [[INS-2026-07-19-multi-filter-breakout-system-with-volume-triggered-stop-plac]]
- [[RG032-3-to-1-reward-to-risk-ratio]]
- [[RG038-minimum-3-to-1-reward-to-risk-ratio]]
- [[RG036-let-profits-run-cut-losses-short]]
- [[RG009-responding-to-failed-patterns-exit-losing-trades-quickly]]
- [[RG010-accepting-false-signals-as-part-of-trading]]
- [[RG017-overboughtoversold-readings-in-strong-trends]]
- [[E014-volume-divergence-as-warning-signal]]
- [[E023-channel-breakout-systems-show-superior-results]]
- [[RG037-use-protective-stops-to-limit-losses]]
- [[RG043-exit-design-more-important-than-entry-design]]

## Change Log

| Date | Action | Detail |
|------|--------|--------|
| 2026-07-19 | Lesson created | Extracted by extract_lessons.py |
