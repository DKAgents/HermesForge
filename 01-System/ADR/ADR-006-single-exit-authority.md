# ADR-006: Single Exit Authority per Strategy

**Status:** ACCEPTED  
**Date:** 2026-09-06  
**Campaign:** 2026-09-aegis-rebuild (US-125)  
**Supersedes:** None (new governance rule)

---

## Context

Two cron jobs act on open paper-trading positions:

- **STR-Q Intraday Sweep Capture** (`b9fb0af`, `*/5`, no-agent) — monitors 5m
  candle data for STR-Q liquidity-sweep trades. On detecting a stop/target/time
  condition, it closes the trade.
- **HermesForge Trade Monitor** (`d1e07c`, `every 60m`, T3) — monitors daily
  bar data for all open trades (STR-A, B, D, I, L, P, V, Q). On detecting exit
  conditions, it closes the trade through `trade_log.close_trade()`.

Both processes read `trades.csv` (now rebuilt from the append-only journal),
find the same open STR-Q trade, and potentially detect exit conditions on
different timeframes. Whichever writes first wins; the loser encounters
`ValueError` from `close_trade()`'s double-close guard. The exit reason is
non-deterministic — it depends on cron timing, not on which price level was
actually hit first.

This is a **split-brain**. The system has two exit authorities for the same
position class, with different data sources (5m live vs cached daily) and
different detection latencies (5m vs 60m).

## Decision

**Each paper-trading strategy has exactly one exit authority.**

The authority is encoded in a `closer` field on every closed trade row.

| Strategy | Exit Authority | Closer Value | Process |
|----------|---------------|--------------|---------|
| STR-Q-liquidity-sweep | STR-Q 5m sweep | `"STR-Q-5m-sweep"` | `b9fb0af` (every 5 min) |
| STR-A, B, D, I, L, P, V, VIXC | Trade Monitor | `"trade-monitor-60m"` | `d1e07c` (every 60 min) |
| All future intraday strategies | Same-cadence sweep | Named per strategy | Per-strategy cron |

The Trade Monitor **explicitly skips** any trade with `strategy_id ==
"STR-Q-liquidity-sweep"` in both its pending-entry and entered-exit loops.
The STR-Q sweep uses `trade_log.close_trade()` (not the raw
`_write_all_rows` bypass) with `closer="STR-Q-5m-sweep"`.

The `closer` field is appended to the journal close event so the audit trail
is preserved.

## Consequences

- **Deterministic exit reason.** A STR-Q trade always closes through its 5m
  sweep. There is no second closer that could win a race.
- **Exit alert SLA.** STR-Q exits are detected within ~5 minutes (next sweep
  cycle after the condition is met). Swing exits are detected within ~60
  minutes (Trade Monitor cycle). The STR-Q sweep posts exit alerts directly;
  swing exit alerts route through Trade Monitor's existing `_post_alert`.
- **`close_trade()` guard remains.** The double-close guard in `close_trade()`
  (ValueError on already-closed trade) is a defense-in-depth backstop, not
  the primary enforcement mechanism.
- **No data migration.** Existing closed trades gain `closer=""` on read
  (empty string, backwards-compatible). New closes set the field.
- **Rollback.** Revert the `continue` skip in Trade Monitor and the
  `closer` parameter becomes optional. Both crons would race as before.
  No data loss on rollback.

## Risk Guardian Review

**Verdict: ACCEPT (2026-09-06).**

All three governance invariants verified clean:
- 1% cap unchanged — no risk calculation, position_sizing, or cap logic modified
- Paper trading only — all modified files under scripts/paper_trading/
- Publisher files unmodified — none of the 9 publisher-owned files in the diff

The ADR contains no credentials and no live SOUL.md edits. Double-close guard
in `close_trade()` remains as defense-in-depth backstop. Journal close events
include `closer` field for audit trail.

**SLA note:** STR-Q exit detection remains ~5 minutes (next sweep cycle).
Swing exit detection remains ~60 minutes (Trade Monitor cycle). Both
unchanged from pre-ADR state.

## Compliance

- Paper trading only. No live orders.
- 1% cap unchanged (Risk Guardian hard limit, ADR-001).
- Publisher files not modified (exit-alert code stays publisher-owned).
- No credentials in this ADR.
- All timestamps in UTC (compute) / PT (display).