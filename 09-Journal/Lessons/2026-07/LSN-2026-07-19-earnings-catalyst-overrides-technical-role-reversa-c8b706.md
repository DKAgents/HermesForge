---
id: LSN-2026-07-19-c8b706
type: lesson
source: live-trade
outcome: refines
related_strategy: ["STR-20260719-sr-role-reversal-entry"]
related_notes: ["RG037-use-protective-stops-to-limit-losses", "RG035-combining-technical-factors-with-money-management-for-stop-p", "RG032-3-to-1-reward-to-risk-ratio", "RG009-responding-to-failed-patterns-exit-losing-trades-quickly", "RG010-accepting-false-signals-as-part-of-trading", "RG043-exit-design-more-important-than-entry-design", "E003-futility-of-short-term-fundamental-trading", "INS-2026-07-19-layer-gap-and-role-reversal-levels-to-anchor-position-sized-"]
date: 2026-07-19
confidence: high
confirmation_count: 0
tags: [lesson, feedback-loop, refines]
---

# Earnings Catalyst Overrides Technical Role-Reversal Setup

## What Happened

On 2026-07-15, a short was entered on AMD at $159.80 based on a support/resistance role-reversal setup — price had broken below $160 (3 prior touches) and rallied back to test it as resistance. The trade was stopped out the next morning at $161.60 for a -1.0R loss when AMD gapped up on an earnings guidance revision. AMD was 6 days from its earnings announcement at entry.

## What Was Expected

The STR-20260719-sr-role-reversal-entry strategy predicted that the prior $160 support level, once broken, would act as resistance on the retest, offering a short entry with a defined stop above the zone. The setup was technically valid with a proper stop at $161.50 per role-reversal criteria.

## What Was Learned

A pre-trade earnings calendar check must be added as a mandatory binary filter to the role-reversal entry criteria — if earnings are within 7 days, the trade should be skipped regardless of technical validity. Fundamental catalysts such as earnings guidance revisions can instantly invalidate technically correct setups and produce gap-through stops. The strategy needs an explicit 'no-trade' condition: do not enter short role-reversal setups on individual stocks within 7 days of a scheduled earnings event.

## Vault Updates Triggered

- [ ] [[STR-20260719-sr-role-reversal-entry]] — confirmation_count incremented
- [ ] [[RG037-use-protective-stops-to-limit-losses]] — confirmation_count incremented
- [ ] [[RG035-combining-technical-factors-with-money-management-for-stop-p]] — confirmation_count incremented
- [ ] [[RG009-responding-to-failed-patterns-exit-losing-trades-quickly]] — confirmation_count incremented
- [ ] [[RG010-accepting-false-signals-as-part-of-trading]] — confirmation_count incremented

## Related Strategy

- [[STR-20260719-sr-role-reversal-entry]] — outcome: refines

## Related Notes

- [[RG037-use-protective-stops-to-limit-losses]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[RG032-3-to-1-reward-to-risk-ratio]]
- [[RG009-responding-to-failed-patterns-exit-losing-trades-quickly]]
- [[RG010-accepting-false-signals-as-part-of-trading]]
- [[RG043-exit-design-more-important-than-entry-design]]
- [[E003-futility-of-short-term-fundamental-trading]]
- [[INS-2026-07-19-layer-gap-and-role-reversal-levels-to-anchor-position-sized-]]

## Change Log

| Date | Action | Detail |
|------|--------|--------|
| 2026-07-19 | Lesson created | Extracted by extract_lessons.py |
