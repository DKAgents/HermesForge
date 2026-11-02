# Architect Spec — US-202 (Required Hypothesis Frontmatter + Intake-Validation Contract)

Date: 2026-11-02
Author: Architect (HermesForge)
Status: DESIGN ONLY — schema + validation contract. No pipeline code, no cron,
no .env changes. Awaiting sign-off.
Epic: EPIC-017 (Gauntlet Pipeline Productionization), Phase 2 (Hypothesis intake)
Scope: the exact required frontmatter fields + the intake-validation rule that
rejects incomplete hypotheses BEFORE G0.

Ground truth read:
- 02-Backlog/Stories/US-202-Hypothesis-Frontmatter.md
- scripts/gauntlet/hypothesis_register.py  (current register() schema)
- PROP-001 §01 (seed pool fields) + §03 (validate_strategy.py frontmatter extension)
- EPIC-017 hard constraints (web-mined content is untrusted; scraper summarizes only)

Summary of the defect this fixes: the current register() emits
{hypothesis_id, description, falsification_criteria, expected_effect_size_bps,
tier, venue, timeframe, holding_class, primitives, registered_at, trials, status}
and the ~35 strategy notes in the registry are freeform .md with NO structured
frontmatter (diagnostic §3). There is no `source`, no `counterparty`, no
`instruments`, no `cost_hurdle`, no `data_dependencies`, no `entry/exit logic`
field. A hypothesis can therefore reach G0 with no statement of WHO is on the
other side of the trade accepting the loss — the single most important
falsifiability question for a claimed edge — and no machine-checkable reason it
should not.

---

# PART 1 — Required frontmatter schema

Every hypothesis (seed-pool, vault-to-hypothesis, web-scraped, generated) MUST
carry the following fields. Type + required + example are given. Fields are
validated at INTAKE, before G0 (Part 2).

## 1.1 Field table

| # | Field                | Type        | Required | Notes / example |
|---|----------------------|-------------|----------|-----------------|
| 1 | `hypothesis_id`      | string      | yes      | unique, e.g. `HYP-11`; matches trials-ledger key |
| 2 | `source`             | enum        | yes      | `human` \| `council` \| `web` \| `generated` |
| 3 | `venue`              | string      | yes      | `hyperliquid` (only supported venue today) |
| 4 | `instruments`        | list[str]   | yes      | explicit ticker list or universe selector, e.g. `["BTC","ETH","SOL"]` or `universe:liq-filtered` |
| 5 | `horizon`            | string      | yes      | holding/exit horizon, e.g. `5m`, `1h-6h`, `1-5d` (contrast with `timeframe`, the signal bar) |
| 6 | `entry_logic`        | string      | yes      | human-readable entry trigger (conditions → action) |
| 7 | `exit_logic`         | string      | yes      | human-readable exit / stop / target logic |
| 8 | `expected_gross_edge_bps` | number | yes    | pre-registered expected gross edge in bps (feeds G0/G1 power floor) |
| 9 | `cost_hurdle_bps`    | number      | yes      | min gross capture required to clear cost (the 4× all-in cost figure) |
| 10 | `data_dependencies`  | list[string]| yes      | every data source the hypothesis depends on, e.g. `["hl:fundingHistory","hl:l2Book","okx:funding-rate"]` |
| 11 | `counterparty`       | string      | yes      | who is on the other side and WHY they structurally accept the loss (see 1.2) |
| 12 | `execution_mode`     | enum        | yes      | `taker` \| `maker` (feeds G0 maker/taker screen, ADR-009) |
| 13 | `falsification_criteria` | string | yes     | measurable criteria that would falsify the hypothesis (carried forward from current register) |
| 14 | `primitives`         | list[string]| yes      | entry-primitive modules used (carried forward) |
| —  | (optional)           | —           | no       | `tier`, `holding_class`, `description` retained but optional |

Fields 1–14 are REQUIRED. `tier` (discovery tier) and `holding_class` may remain
optional; they do not affect intake admission. A hypothesis record with any of
1–14 missing is rejected at intake.

## 1.2 `counterparty` — the load-bearing field (binding)

`counterparty` is the explicit statement of WHO accepts the other side of the
trade and WHY they accept the (structural/expected) loss. It is not optional, not
freeform filler, and not "the market." Requirements:

- It must name a class of counterparty with a plausible informational or
  structural reason they are on the other side (e.g. "late retail longs chasing
  a crowded funding regime — they accept negative funding carry because they are
  momentum-chasing, not carry-aware," or "liquidity providers resting passively
  to earn the spread — they accept adverse selection when a taker has better
  short-term information").

- If the answer is "no identifiable counterparty who loses," the hypothesis is
  REJECTED at intake — an edge with no loser is a repackaged beta or a data
  artifact, not alpha.

- Web/generated sources (x-strategy-scout, External Edge Discovery, Edge Factory)
  are UNTRUSTED (EPIC-017). Their content is summarized into `entry_logic` /
  `exit_logic` only; the `counterparty` field for such a source must STILL be
  reasoned by the intake agent from first principles, not copied from the web
  text. A scraped hypothesis that cannot articulate a counterparty is rejected.

## 1.3 Enum constraints

- `source`: exactly one of `human`, `council`, `web`, `generated`.
- `execution_mode`: exactly one of `taker`, `maker` (matches ADR-009).
- `venue`: `hyperliquid` today; any other value is rejected at intake (no other
  venue exists; adding one is human-gated per ADR-011).

---

# PART 2 — Intake-validation contract

## 2.1 Validation function (binding shape)

```python
# hypothesis_register.py — validate_frontmatter(entry: dict) -> (ok: bool, errors: list[str])
REQUIRED_FIELDS = [
    "hypothesis_id", "source", "venue", "instruments", "horizon",
    "entry_logic", "exit_logic", "expected_gross_edge_bps",
    "cost_hurdle_bps", "data_dependencies", "counterparty",
    "execution_mode", "falsification_criteria", "primitives",
]
SOURCE_ENUM = {"human", "council", "web", "generated"}
EXEC_MODE_ENUM = {"taker", "maker"}
```

`register()` and `pre_register_from_seed_pool()` MUST call `validate_frontmatter`
and REFUSE to write a ledger entry (raise, or return a structured rejection)
when validation fails. Rejection happens at INTAKE — before G0 — never at a
later gate.

## 2.2 Rejection rules (ordered, first failure stops)

1. Any field in `REQUIRED_FIELDS` missing or empty string / empty list → reject
   with the missing field name. **`counterparty` is treated identically to every
   other field** (no softer treatment).
2. `source ∉ SOURCE_ENUM` → reject.
3. `execution_mode ∉ EXEC_MODE_ENUM` → reject.
4. `venue != "hyperliquid"` → reject.
5. `expected_gross_edge_bps` or `cost_hurdle_bps` not a finite number → reject.
6. `instruments` / `data_dependencies` / `primitives` not non-empty lists → reject.
7. Duplicate `hypothesis_id` → reject (already existing behavior).

## 2.3 Acceptance verification (how "rejected at intake, not G0" is proven)

- Unit test: `register()` with a seed missing `counterparty` (all other fields
  present) is rejected and writes NOTHING to `hypotheses.jsonl`.
- Unit test: a `source="web"` seed whose `counterparty` is empty is rejected.
- Unit test: the full 14-field seed pool entries still register (no regression).
- A dry-run intake that emits the rejection reason per field (so a scraper agent
  can be corrected) rather than a bare boolean.

## 2.4 Migration note (do not touch old notes)

The ~35 existing freeform registry notes (diagnostic §3) are NOT retroactively
migrated in this story — backfilling their frontmatter is a separate, explicit
decision. They remain readable; they simply do not pass the new intake until
their fields are authored.

---

# PART 3 — Assumptions & open questions

- A1 The `horizon` vs `timeframe` distinction (signal bar vs. holding/exit
  window) is proposed but not yet canonical; confirm we need BOTH fields rather
  than folding `horizon` into `exit_logic`.
- A2 `cost_hurdle_bps` vs a *derived* cost-hurdle: the field is required to be
  pre-stated, but G0 recomputes it from `fee_source`. OPEN — is `cost_hurdle_bps`
  a claim to be CHECKED against G0, or just a recorded assumption?
- A3 `instruments` as a universe selector string (e.g. `universe:liq-filtered`)
  needs a defined grammar; a bare string may be ambiguous vs. a literal ticker
  list.
- A4 Whether `counterparty` should also require a *magnitude* (how many of them,
  how much flow) or just a *class + reason*. OPEN — recommend "class + reason"
  as the minimum, magnitude optional.
- A5 The structured schema is a superset of the current `register()` args; the
  seed pool in `hypothesis_register.py` (§SEED_POOL) must be updated to carry the
  new fields, which is a mechanical change for the coder, not a design open item.

END OF DESIGN.