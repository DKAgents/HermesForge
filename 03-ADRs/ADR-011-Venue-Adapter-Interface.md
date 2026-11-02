---
id: ADR-011
type: adr
status: accepted
created: 2026-11-02
revised: 2026-11-02
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

**Revision 2 (2026-11-02) — response to risk-guardian admission-bar rejection:**
the draft stated the live safety invariants in prose but did not pin them to a
**hard test contract**. The risk-guardian's objection is that an invariant that
lives only in a docstring/prose can regress silently when a future edit touches
the adapter boundary. Every invariant below is now mapped — by name — to a test
in the regression suite, and the reduce-only stop coupling is explicitly
required to be tested **at the adapter boundary** (driving `VenueAdapter.place`,
not the concrete executor). Where a required test does not yet exist, it is
listed as a named mandatory addition. Details in "Risk-Guardian Objections
Closed" and "Test Contract (binding)".

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

## Live Safety Invariants (binding — each pinned to a named test, §5)

1. **Kill switch blocks OPEN only, never CLOSE.** The
   `KILL_SWITCH_FILE` (`/root/HermesForge/.live_kill_switch`, `PAUSED=true`)
   must gate `place` (open) but MUST NOT gate `cancel`/`stop`/`positions`/reads
   or any flatten path. Closing risk must remain possible when paused.

2. **Fail-closed protective stop.** Every `place` must submit a reduce-only
   protective stop USED to open the opposite side, and if the stop cannot be
   confirmed, the opened position is FLATTENED immediately (never hold an
   unprotected position).

3. **Size-cap defense-in-depth.** The executor enforces the hard size cap
   (`MAX_POSITION_SIZE_USD`, default $500) INDEPENDENTLY of the risk manager, so
   no caller path can open above the cap. The risk manager (`check_trade`)
   additionally enforces day-loss, concurrent-position, and total-exposure
   limits — every live order passes through BOTH.

4. **`LIVE_TRADING_ENABLED` explicit + default-off.** Live execution requires an
   explicit, human-set gate (ADR-002 `paper_mode=True` default; ADR-007 go-live
   and first-fill are human-gated). No adapter, config, or cron may set it.

## Test Contract (binding) — invariants are a hard test requirement, not prose

Every invariant in §4 is pinned to the regression suite
`scripts/live_trading/tests/test_live_safety.py` by name. An invariant is
considered violated if its named test does not pass against the **adapter
implementation** (not a simplified mock of the interface). Acceptance of any
adapter is refused until all named tests below pass through the adapter boundary.

| Invariant (§4) | Required test (name) | Status |
|---|---|---|
| 1 — kill switch gates OPEN | `test_open_position_blocked_when_kill_switch_armed` | **exists** (must be re-driven at the adapter boundary) |
| 1 — kill switch never gates CLOSE | `test_close_position_allowed_when_kill_switch_armed` | **exists** (adapter boundary) |
| 2 — protective stop is reduce-only + opposite side | `test_open_position_places_stop_loss` | **exists** — see boundary note below |
| 2 — flatten when stop placement fails | `test_flatten_when_stop_loss_placement_fails` | **exists** (adapter boundary) |
| 2 — reduce-only stop coupling AT THE ADAPTER BOUNDARY | `test_stop_still_reduce_only_at_adapter_boundary` | **MANDATORY NEW** |
| 3 — size cap enforced without caller check | `test_open_position_rejects_oversized_without_caller_check` | **exists** (adapter boundary) |
| 3 — in-cap size allowed | `test_open_position_allows_size_within_cap` | **exists** (adapter boundary) |
| 3 — risk manager enforces cap | `test_risk_manager_enforces_max_size` | **exists** |
| 4 — `LIVE_TRADING_ENABLED` default-off blocks open | `test_live_trading_disabled_by_default_blocks_open` | **MANDATORY NEW** |

**Reduce-only stop coupling — explicit boundary requirement.** The reduce-only
nature of the protective stop must be asserted **at the adapter boundary**: a
test must call `VenueAdapter.place(...)` (the interface, not `LiveExecutor`
directly) and assert that the stop order it places is `reduce_only=True` and on
the closing side — so a future adapter re-wiring cannot quietly drop the
`reduce_only=True` coupling that `LiveExecutor._place_stop_loss` currently
carries. This is the specific gap the risk-guardian called out, and it must be
closed by the new `test_stop_still_reduce_only_at_adapter_boundary`.

The two MANDATORY NEW tests do not exist today; their addition is part of the
implementation's acceptance criteria and must land with (not after) the adapter.

## Consequences

**Positive:** strategy code stops depending on the HL client concretely; adding/
swapping a venue becomes a config + adapter-implementation exercise without
strategy rewrites; HL stays the safe default; and every safety invariant is now
enforced by a named regression test rather than a prose promise.

**Negative / trade-offs:** an abstraction boundary is a place for a well-meaning
future edit to accidentally relax an invariant (e.g., reorder the kill-switch
check around a new `place`). Mitigation: the test contract is no longer
advisory — it is the acceptance gate (§5), so a regressed invariant fails CI.

**Risks:** the adapter interface invites "venue swap" as an easy future path,
which is precisely the platform-risk / counterparty decision that must stay
human-gated. The ADR therefore forbids implementing new venues under this record.

## Risk-Guardian Objections Closed

The single objection was: **the safety invariants lived only in this document
(prose/docstring) and could regress without detection.** Closed by §5 — every
invariant is pinned to a named test in the regression suite, acceptance requires
those tests to pass **through the adapter boundary**, and the two missing tests
(the adapter-boundary reduce-only coupling, and the LIVE_TRADING_ENABLED
default-off) are declared mandatory additions that ship with the adapter. The
reduce-only stop coupling is now explicitly required to be tested at the adapter
boundary, not only against the concrete executor.

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
- A5 The two MANDATORY NEW tests (§5) must be authored in
  `scripts/live_trading/tests/test_live_safety.py` as part of implementation;
  their exact assertion fixtures are owned by the coder under this contract.

## Review Date
Revisit at human approval to implement, or 2027-01-02.

## Related
- [[US-219-Venue-Adapter]] · [[ADR-002-Paper-Trading-First]] · [[ADR-007-Self-Healing-System]]
- [[scripts/live_trading/live_executor.py]] · [[scripts/live_trading/live_risk_manager.py]] · [[scripts/live_trading/create_agent_key.py]]
- [[scripts/live_trading/tests/test_live_safety.py]]