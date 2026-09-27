# LU-08: Vault Map — Current Roots and a Two-Root End State

**Status**: note-only (no code edits, no file moves)
**Date**: 2026-09-25
**Campaign**: 2026-09-aegis-rebuild

**Source directories**: `vault/`, `08-Knowledge/`, `04-Strategies/`, plus the
repo root (`/root/HermesForge`).

---

## Current Roots

The "vault" today is the **repo root itself**, with two distinct numbering
schemes and several un-numbered artifacts interleaved. There is no single
authoritative root — content is scattered across three overlapping
conventions.

### Numbered tree (Obsidian vault — 00 through 10)

| Root | Contents |
|---|---|
| `00-Meta/` | Project meta, cross-cutting index |
| `01-Agents/` | Agent profiles / souls (`Profiles/`) |
| `01-System/` | System configuration |
| `02-Backlog/` | User stories, epics, ADRs-adjacent backlog |
| `03-ADRs/` | Architecture Decision Records |
| `04-ForgeLoop/` | Forge loop outputs + `Discovery/` (weekly `Discoveries-*.md`) |
| `04-Strategies/` | Strategy notes (phase1a results, T1 discoveries, STR-Q variants) |
| `05-Proposals/` | Proposals (e.g. PROP-001 gauntlet) |
| `05-Research/` | Research + `Strategy-Validation/` |
| `06-Strategies/` | Hypotheses, Active, Backtests, Live, Regimes, Failure-Modes, Deprecated |
| `07-Risk/` | Risk rules, incident log |
| `08-Knowledge/` | `Insights/`, `Learnings/`, `Skills/`, `Trading-Systems/`, MOC |
| `09-Journal/` | Trading journal |
| `10-Operations/` | Ops documentation |

### Un-numbered tree (git/code artifacts)

| Root | Contents |
|---|---|
| `scripts/` | All Python/bash code (the executable system) |
| `tests/` | Test suite |
| `docs/` | Documentation |
| `campaigns/` | Campaign working docs (incl. this LU series) |
| `data/` | Data storage |
| `reports/` | Report outputs |
| `Inbox/` | Capture-inbox (unfiled notes) |
| `Templates/` | Note/story templates |

### `vault/` subdirectory

A small legacy folder holding only `vault/research/research-2026-08-06.md`
and `research-2026-08-09.md`. It is a dead stub — real research lives in
`05-Research/`. The name `vault/` is now misleading: the actual vault is
the repo root.

### Root collision

Two trees both claim "04": `04-ForgeLoop/` (process output) and
`04-Strategies/` (trading ideas). This is a smell of accreted growth, not
deliberate design.

---

## Broken Links

Checked wikilinks from `04-Strategies/`, `08-Knowledge/`,
`06-Strategies/Hypotheses/`, `05-Research/Strategy-Validation/`,
`09-Journal/`. Reference classes:

- **Resolvable**: `ADR-001-Model-Routing-Strategy` → `03-ADRs/ADR-001-*.md`
  (exists), `ADR-004-Phase1-Validation-Framework` → exists, `Backtester` →
  `01-Agents/Profiles/Backtester.md` (exists).
- **Knowledge-graph nodes, not files**: `C024`, `C065`, `C084`, `E005`,
  `EN008`, `EX001`, `FAIL-STR-*`, `CAND-*`, `FACTOR-*` — these are semantic
  nodes from the trading-book ingestion (Murphy / technical-analysis graph),
  intentionally not one-file-per-node. They resolve inside the knowledge
  graph, not the filesystem.
- **Resolvable in an unexpected location**: `Discoveries-2026-W31-graph-aware`
  and `Discoveries-2026-W32-high-vol` resolve to
  `04-ForgeLoop/Discovery/Discoveries-2026-W31-graph-aware.md` and
  `...W32-high-vol.md` — they exist, just under `04-ForgeLoop/` rather than
  `08-Knowledge/`.

**No broken filesystem link could be demonstrated.** Every non-graph wikilink
traces to an existing file. The apparent "breaks" are either (a) graph nodes
that are not files by design, or (b) files living in an unexpected numbered
root (`04-ForgeLoop/Discovery/` vs `08-Knowledge/Insights/`).

---

## Recommended End State (do not implement here)

One vault, **two roots**:

```
/root/HermesForge/
├── code/          ← executable system + governance
│   ├── scripts/
│   ├── tests/
│   ├── docs/
│   ├── 00-Meta/
│   ├── 01-Agents/        (souls)
│   ├── 01-System/
│   ├── 02-Backlog/
│   ├── 03-ADRs/
│   ├── 04-ForgeLoop/
│   ├── campaigns/
│   ├── data/
│   └── Templates/
│
└── trading/       ← research, strategy, risk, knowledge
    ├── strategies/       (merge 04-Strategies + 06-Strategies)
    ├── research/         (05-Research + 05-Proposals)
    ├── risk/             (07-Risk)
    ├── knowledge/        (08-Knowledge + legacy vault/research)
    ├── journal/          (09-Journal)
    └── operations/       (10-Operations)
```

Rationale:

- **`code/`** groups everything that changes under git for the executable
  system: scripts, tests, agent souls, backlog, ADRs, forge-loop output,
  campaigns, and data. This is the "how the machine runs" root.
- **`trading/`** groups everything that accumulates as trading knowledge:
  strategies (hypotheses → active → backtests → live), research, proposals,
  risk rules, the knowledge base, the journal, and ops notes. This is the
  "what we know and trade" root.
- The collision between `04-ForgeLoop` and `04-Strategies` dissolves — one
  goes under `code/`, the other under `trading/strategies/`.
- `08-Knowledge/Insights/` and `04-ForgeLoop/Discovery/` are unified as the
  single knowledge/insight home, ending the "Discovery lives under ForgeLoop"
  surprise.

This is a **reorganization proposal**, not a change order. No directory is
created, renamed, or moved in this story.

---

## Invariants

- **Do NOT move** any files or directories.
- **Do NOT create** `code/` or `trading/` (or any second vault).
- **Do NOT edit** any soul file.
- **Do NOT post. Do NOT trade.**

---

## Verified

```bash
$ find vault 08-Knowledge 04-Strategies -maxdepth 2 -type d | head -40
vault
vault/research
08-Knowledge
08-Knowledge/Insights
08-Knowledge/Skills
08-Knowledge/Trading-Systems
08-Knowledge/Learnings
04-Strategies
```

---

## Key Takeaway

The vault is the repo root, with a numbered Obsidian tree (00–10) and an
un-numbered code tree (`scripts/`, `tests/`, `docs/`, `campaigns/`, etc.)
interleaved, plus a dead `vault/` stub. No broken filesystem links were
found — apparent breaks are knowledge-graph nodes or misplaced Discovery
files. The recommended end state is one vault with two roots: `code/`
(executable system) vs `trading/` (knowledge + strategy + risk).