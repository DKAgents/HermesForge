---
type: do-not-touch
campaign: 2026-09-aegis-rebuild
generated_utc: 2026-09-06
display_tz: America/Los_Angeles
---

# DO-NOT-TOUCH

Hard boundaries for every story in this campaign and for any implementer picking
them up. Aegis (T1) is read-only and has already honored all of these.

## Governance invariants (never modify by instruction)

- **1% single-position risk cap** — Risk Guardian's non-overridable ceiling
  (ADR-001 class). No story may raise, condition, or bypass it.
- **US-121 STR-Q size gate** — stays blocked without ≥200 stable OOS trades AND
  a principal-signed ADR. This campaign does not unblock it.
- **Paper trading only** — live orders require explicit principal approval + ADR.

## Ownership monopolies

- **Publisher owns all 9 publish files** (embed / chart / alert / template /
  publishing code). Stories touching Discord output (US-130, US-131) are routed
  to publisher; no other owner may edit these.
- **Risk Guardian owns the 1% cap and promotion gates.**

## Files Aegis and this campaign will NOT write or edit

- Live `SOUL.md` of any other profile
- Production `config.yaml`
- `.env` / any credential file
- `scripts/paper_trading/trades.csv` (the DATA file — stories change the code
  path around it, never the file itself; append-only journal is additive)
- Journals / Parquet / historical data (append-only; truncate-then-write is P0)
- `crosspost_state.json` (publisher-owned; guarded via US-131, not edited by Aegis)
- Publisher-owned embed/alert/chart/template/publishing files
- Cron definitions — no create / update / pause / remove in this session
- New production profiles

## Data integrity law

Historical data is **append-only**. Truncate-then-write is a **P0 defect**. The
existing v1 fuse in `trade_log.py` is a stopgap, not the target; it must not be
removed until the append-only journal (US-123) replaces it.

## Output hygiene

- No credentials, webhook URLs, or `.env` values in any story, ADR, RCA, or
  report. Discord targets referenced by numeric ID or channel name only.
- Display timestamps in Pacific Time; compute in UTC.

## If a path is unclear

Do not write it. File a blocked story. (This run filed brief-builder stories
US-123/US-124 rather than guessing at missing inventory.)
