---
id: ADR-011
type: adr
status: proposed
created: 2026-11-02
deciders: [architect]
tags: [adr, execution, abstraction, venue-adapter, hyperliquid, safety]
topic: adrs
confidence: high
has_quotes: false
source: HermesForge ADR
---
# ADR-011: Venue Adapter Interface (Design-Only) — Hyperliquid Preserved

## Status
**proposed** — DESIGN ONLY. No live enablement. Implementation is gated on
human approval. This ADR authorizes nothing that runs against real money; it
defines the abstraction and restates the invariant set the implementation must
preserve verbatim.

## Context

`scripts/live_trading/live_executor.py` binds order execution directly to the
Hyperliquid mainnet client (`hyperliquid.exchange.Exchange`, `base_url =
https://api.hyperliquid.xyz`), with agent-custody keys produced by
`create_agent_key.py`. Every strategy that (eventually) needs to execute must
speak to that concrete object. If a second venue is ever added, or the HL client
surface changes, strategy code would have to change alongside it.

US-219 asks for a **venue adapter** — an interface behind the executor
(`place` / `cancel` / `stop` / `positions` / `fills`) so a live venue can be
swapped *by configuration* without touching strategy code — while **preserving
the existing Hyperliquid integration as the default venue** and **every live
safety invariant**.

The binding constraint is explicit and non-negotiable: **Hyperliquid remains the
default/primary venue.** The existing `live_executor.py` → `api.hyperliquid.xyz`
path and the `create_agent_key.py` agent-custody path must **never be severed**.
The adapter is *additive*: it wraps HL, it does not replace HL.

## Decision

### 1. The adapter interface

The executor is abstracted behind a `VenueAdapter` protocol with five
(read-side × write-side) methods. Signatures follow the existing
`LiveExecutor` behavior so the HL implementation is a thin delegation, not a
rewrite.

```python
class VenueAdapter(Protocol):
    def place(self, *, coin: str, direction: str, size_usd: float,
              stop_loss_pct: float) -> ExecutionResult: ...
    def cancel(self, *, order_id: str) -> ExecutionResult: ...
    def stop(self, *, coin: str, direction: str, size: float,
             stop_price: float) -> ExecutionResult: ...   # protective stop
    def positions(self) -> list[dict]: ...               # open positions
    def fills(self, *, start_ts=None, end_ts=None) -> list[dict]: ...  # fill audit
```

- `place` / `stop` are the **write** path and carry all safety enforcement (§4).
- `cancel` targets an order id and must be safe to call when the kill switch is
  armed (cancelling a resting order reduces risk).
- `positions` / `fills` are the **read** path and are unaffected by the kill
  switch (you must always be able to inspect/flatten).
- A `venue` selector (a config key, e.g. `execution.venue = "hyperliquid"`)
  chooses the concrete adapter at startup. Default and only-implemented value:
  `"hyperliquid"`.

### 2. Hyperliquid is the default and is preserved (binding)

- `HyperliquidAdapter` is a **delegation** over the existing `LiveExecutor` —
  the same `Exchange(agent_acct, base_url=MAINNET_URL, account_address=main)`
  construction, the same agent-custody model from `create_agent_key.py`, the
  same `MAINNET_URL = "https://api.hyperliquid.xyz"`.
- The adapter does NOT change how HL credentials are sourced
  (`HYPERLIQUID_AGENT_KEY` + `HYPERLIQUID_ACCOUNT` agent mode preferred;
  `HYPERLIQUID_PRIVATE_KEY` direct mode fallback).
- No other venue is implemented by this ADR. Adding a venue is a FUTURE,
  human-gated decision (ADR-001 escalation trigger #10, counterparty/platform
  risk analysis; ADR-007 Tier 2 — human sign-off, never auto).

### 3. Config-driven swap, but no live enablement

The adapter is selectable by config so that strategy code is venue-agnostic, but
`LIVE_TRADING_ENABLED` remains **off** and default **off**. The config swap is a
*construction-time* wiring concern; it does not, by itself, turn on live
trading. No venue adapter may open a live order unless the full live gate is
satisfied (§4 invariant 4).

## Live Safety Invariants (restated — MUST be preserved verbatim by any adapter)

1. **Kill switch blocks OPEN only, never CLOSE.** The
   `KILL_SWITCH_FILE` (`/root/HermesForge/.live_kill_switch`, `PAUSED=true`)
   must gate `place` (open) but MUST NOT gate `cancel`/`stop`/`positions`/reads
   or any flatten path. Closing risk must remain possible when paused
   (`test_close_position_allowed_when_kill_switch_armed`).

2. **Fail-closed protective stop.** Every `place` must submit a reduce-only
   protective stop USED to open the opposite side, and if the stop cannot be
   confirmed, the opened position is FLATTENED immediately (never hold an
   unprotected position). `test_flatten_when_stop_loss_placement_fails`.

3. **Size-cap defense-in-depth.** The executor enforces the hard size cap
   (`MAX_POSITION_SIZE_USD`, default $500) INDEPENDENTLY of the risk manager, so
   no caller path can open above the cap
   (`test_open_position_rejects_oversized_without_caller_check`). The risk
   manager (`check_trade`) additionally enforces day-loss, concurrent-position,
   and total-exposure limits — every live order passes through BOTH.

4. **`LIVE_TRADING_ENABLED` explicit + default-off.** Live execution requires an
   explicit, human-set gate (ADR-002 `paper_mode=True` default; ADR-007 go-live
   and first-fill are human-gated). No adapter, config, or cron may set it.

## Consequences

**Positive:** strategy code stops depending on the HL client concretely; adding/
swapping a venue becomes a config + adapter-implementation exercise without
strategy rewrites; HL stays the safe default.

**Negative / trade-offs:** an abstraction boundary is a place for a well-meaning
future edit to accidentally relax an invariant (e.g., reorder the kill-switch
check around a new `place`). Mitigation: the invariant set above is the
acceptance contract AND must be pinned by the existing
`tests/test_live_safety.py` regression suite (unchanged behavior = tests must
still pass against the adapter).

**Risks:** the adapter interface invites "venue swap" as an easy future path,
which is precisely the platform-risk / counterparty decision that must stay
human-gated. The ADR therefore forbids implementing new venues under this record.

## Assumptions & Open Questions (explicit)

- A1 `fills()` semantics (a venue that does not expose historical fills) —
  the interface lists it, but HL's `fills` may be userFillHistory-based. OPEN —
  define the minimum fill fields (coin, side, size, px, ts, fee).
- A2 The exact `venue` config key and its location (`.env` vs `~/.hermes/config.yaml`
  vs a registry) is unspecified. OPEN.
- A3 Whether `cancel`/`stop` should verify order state after placement (a
  confirmation read-back) before returning success. OPEN — recommend yes
  (fail-closed), but it is not yet specified.
- A4 This ADR does not decide the pre-live execution audit scope (ADR-001
  trigger #11); that audit remains a separate, dispatchable Opus task and is
  OUT of scope here.

## Review Date
Revisit at human approval to implement, or 2027-01-02.

## Related
- [[US-219-Venue-Adapter]] · [[ADR-002-Paper-Trading-First]] · [[ADR-007-Self-Healing-System]]
- [[scripts/live_trading/live_executor.py]] · [[scripts/live_trading/live_risk_manager.py]] · [[scripts/live_trading/create_agent_key.py]]