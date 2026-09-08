---
type: backlog-index
created: 2026-06-27
updated: 2026-09-08
tags: [backlog]
---

# HermesForge Backlog Index

This index tracks all epics and user stories for the HermesForge Trading System. Each epic groups related stories toward a major system capability milestone.

**Going-forward rule (established 2026-08-07):** All initiatives, bug fixes, and infrastructure work must be assigned a user story (US-XXX) and tracked in this backlog before implementation. No exceptions.

---

## Epics

| Epic | Status | Description | Stories |
|------|--------|-------------|---------|
| [[EPIC-001-Foundation\|EPIC-001]] | In Progress | Setting up vault, Hermes profiles, and core infrastructure | US-001 to US-006, US-063 |
| [[EPIC-002-Research\|EPIC-002]] | In Progress | Research swing/position trading strategies for US stocks and crypto | US-010 to US-017, US-089, US-093 |
| [[EPIC-003-PaperTrading\|EPIC-003]] | Backlog | Building and validating strategies in paper mode (stocks + crypto) | US-020 to US-026 |
| [[EPIC-004-Risk\|EPIC-004]] | Backlog | Implementing risk rules, position sizing, and guardian workflow | US-030 to US-034 |
| [[EPIC-005-ForgeLoop\|EPIC-005]] | In Progress | Automating the continuous improvement loop | US-040 to US-044 |
| [[EPIC-006-KnowledgeEvolution\|EPIC-006]] | Backlog | Knowledge graph evolution and vault maintenance | US-050 to US-053 |
| [[EPIC-007-StrategyValidation\|EPIC-007]] | Done | Strategy validation infrastructure (walk-forward framework) | US-054 to US-056 |
| [[EPIC-008-UserControlledAutoExecution\|EPIC-008]] | Backlog | User-controlled auto-execution of trades | US-057 to US-062 |
| [[EPIC-010-AutoPaperTrading\|EPIC-010]] | In Progress | Automatic paper trading engine | US-065 to US-071 |
| [[EPIC-011-HyperliquidTestnet\|EPIC-011]] | Backlog | Hyperliquid testnet integration | US-072 to US-076 |
| [[EPIC-012-AlpacaPaperTrading\|EPIC-012]] | Backlog | Alpaca paper trading integration | US-077 to US-080 |
| [[EPIC-013-ClosedLoopImprovements\|EPIC-013]] | In Progress | Closed-loop self-improvement, research pipeline, publishing | US-081 to US-088, US-090, US-092 |
| [[EPIC-014-TechDebt\|EPIC-014]] | Backlog | Known bugs, infrastructure quirks, and workarounds | US-091, US-094 to US-100 |

---

## Recently Completed (August 2026)

| Story | Epic | Description | Commit |
|-------|------|-------------|--------|
| US-085 | EPIC-013 | Research pipeline (5 modules, weekly cron) | `7942f30` |
| US-086 | EPIC-013 | Research publisher with Discord embeds | `9942c6f`, `67c2734` |
| US-087 | EPIC-013 | Strategy status dashboard expansion (24 strategies) | - |
| US-088 | EPIC-013 | Webhook-based crossposting system | `9d7ce4a`, `af4c7f8` |
| US-089 | EPIC-002 | STR-H Hype strategy (crypto-only, walk-forward tested) | `592ab75`, `6e254ce` |
| US-090 | EPIC-013 | LinkedIn cron style refinement (3 rounds, 24 rules) | cron update |
| US-091 | EPIC-014 | Webhook global fallback bugfix | `2949676` |
| US-092 | EPIC-013 | Per-channel webhooks for all 7 channels | `cf88b89` |
| US-094 | EPIC-014 | Programmatic em-dash filter for LinkedIn | `e5426c5` |
| US-095 | EPIC-014 | LinkedIn topic uniqueness guard (programmatic) | `e5426c5` |
| US-096 | EPIC-014 | Remove stale CROSSPOST_WEBHOOK_URL env var | `e5426c5` |
| US-101 | EPIC-013 | STR-B/STR-I signal recency window fix + trades.csv dedup | `cf88b89` |
| US-113 | EPIC-013 | Autonomous pipeline: VIX contango breakout strategy (walk-forward OOS ROBUST EDGE, deployed WATCH) | this run |
| US-114 | EPIC-013 | Autonomous pipeline: Low-correlation regime stock picker (Phase 1A positive, deployed WATCH, walk-forward incomplete) | this run |
| US-071 | EPIC-010 | Paper Trading Performance Report (Discord, cron cb22b038a6d6) | `4dc81e5` |
| US-115 | EPIC-013 | Autonomous pipeline: Treasury buyback debasement BTC regime trade (Phase 1A p=0.157 SPECULATIVE, walk-forward OOS mean R +0.131 → WATCH, deployed to paper trading at 0.5% risk) | this run |
|| US-120 | EPIC-013 | Autonomous pipeline: Oil shock sector rotation (Phase 1A mean R=+0.183 p=0.1069, walk-forward OOS mean R=+0.171, deployed WATCH at 0.5% risk) | this run |
| US-122 | EPIC-013 | Autonomous pipeline: BTC supply crunch / thin-float breakout (Phase 1A mean R=+0.256 p=0.0651, walk-forward OOS mean R=+0.146, deployed WATCH at 0.5% risk — STR-20260906-BTC-SUPPLY-CRUNCH) | this run |
| US-142 | EPIC-013 | Autonomous pipeline: Predicted skewness factor (Phase 1A mean R=+0.079 p=0.0, walk-forward OOS mean R=+0.0457 p=0.0005, deployed WATCH at 0.25% risk — STR-20260908-SKEW-PREDICTED) | this run |

---

## Current Backlog (Unfixed / Pending)

| Story | Epic | Description | Priority | Blocked by |
|-------|------|-------------|----------|------------|
| US-093 | EPIC-002 | STR-H improvements (social data, 4h, survivorship-free) | Medium | LunarCrush API key from user |
| US-097 | EPIC-014 | headroom_retrieve upstream bug (#1077) | Low | PR #1176 merge |
| US-098 | EPIC-014 | hermes config set CLI bug (#16493) | Low | Upstream fix |
| US-099 | EPIC-014 | write_file truncation guard | Low | None |
| US-100 | EPIC-014 | send_message text+MEDIA drop | Low | Upstream fix |
| US-118 | EPIC-009 | Posting agent for channel routing validation | Low | None |
| US-119 | EPIC-009 | Real-time market event monitoring (liquidation webhook) | Medium | None |
| US-120 | EPIC-009 | Advanced options strategies (iron condors, straddles, calendars) | Medium | IV rank data source |
| US-121 | EPIC-004 | STR-Q position size re-evaluation (1% → conditional) | Blocked | ≥200 stable OOS trades + principal-signed ADR |

---

## Campaign 2026-09-aegis-rebuild (Aegis Rebuild — Pass 2 GRADED, filed 2026-09-07)

Read-only T1 campaign. Reports: `reports/campaigns/2026-09-aegis-rebuild/`.
Pass 1 (2026-09-06) was DEGRADED (stub inventory/cost). Pass 2 grades on the real
`inventory.yaml`/`cost-30d.md` and on-disk state. Train 0 durability has largely
shipped; its only open items are US-136 (off-box) and US-137 (drill proof), which
gate any Hermes upgrade. Profile/cron changes are handed to their owners with
evidence — Aegis does not edit cron defs or live souls.

| Story | Train | Priority | Owner | Status | Description |
|-------|-------|----------|-------|--------|-------------|
| US-123 | 0 | P0 | coder | ✅ shipped | Append-only journal; trades.csv is derived projection (journal 1,687 rows) |
| US-124 | 0 | P0 | no-agent | ✅ shipped | Brief-builder: real inventory.yaml + cost-30d.md |
| US-125 | 0 | P0 | coder | ✅ shipped | Single exit authority (`closer` field; ADR-006 STR-Q skip) |
| US-126 | 0 | P0 | no-agent | ⚠ partial | Snapshots shipped; off-box + drill open (→US-136/137) |
| US-127 | 3 | P2 | coder | ready | Coded strategy seeder feeding the reject-heavy filter |
| US-128 | 0 | P1 | no-agent | ready | Fear & Greed freshness + fail-closed regime gate |
| US-129 | 0 | P1 | product-owner | ✅ shipped | Vault retention audit — 14d gap found, retention → 35d |
| US-130 | 5 | P2 | publisher | ✅ shipped | Crosspost overlap — `356f3c` paused, `61cccd` sole path |
| US-131 | 0 | P1 | publisher | ✅ shipped | Protect crosspost_state.json (guard + snapshot class) |
| US-132 | 2 | Medium | coder | ready | Evaluate Microsoft MarkItDown for document ingestion |
| US-133 | 0 | P1 | coder | ✅ shipped | Extend cron output retention to 35 days |
| US-134 | 0 | P2 | coder | ready | Add cron output + maintenance logs to snapshot payload |
| US-135 | 0 | P3 | coder | ready | Add incident log + guardian decisions to snapshot payload |
| US-136 | 0 | P1 | no-agent | ready (pass 2) | Activate off-box snapshot copy (offbox_copied=false, path unset) |
| US-137 | 0 | P1 | no-agent | ready (pass 2) | Capture restore-drill evidence + restore_drill_last_ok |
| US-138 | 1 | P2 | coder | ready (pass 2) | Right-size Vault Connection Weaver (tier/cadence/toolset allowlist) |
| US-139 | 1 | P2 | no-agent | ready (pass 2) | Fill context-budgets.md (last stub brief file) |
| US-140 | 1 | P3 | no-agent | ready (pass 2) | Close signal_charts purge gap (826 MB / 8,497 files) |
| US-141 | 4 | P3 | product-owner | ready (pass 2) | Swarm diet — documenter→skill, trading/consulting surfaces (evidence-gated) |

---

## Deferred Items (Not Yet User Stories)

These items are known but have not been promoted to user stories yet. They should be assigned US numbers when ready to work.

| Item | Category | Notes |
|------|----------|-------|
| STR-L walk-forward validation | Strategy | Only 6 signals in 7 years. No path forward without more data. |
| Murphy book cross-linking (Phase B) | Knowledge | 1,257 files not yet cross-linked. |
| Dataview dashboards (Phase C) | Knowledge | Not started. |
| Stock intraday confirmation | Data | Needs paid data source. Phase 2 deferred. |
| 6h crypto bars | Data | Deferred. |
| Polymarket/futures integration | Data | Deferred. |

---

## Backlog Health

- **Total Epics:** 14 (1 done: EPIC-007, EPIC-010)
- **Total Stories Defined:** 75 (US-001 to US-142)
- **Completed (September 2026):** US-142 (Predicted Skewness Factor deployment)
- **Epics Done:** EPIC-007 (Strategy Validation), EPIC-010 (Auto Paper Trading)
- **In Progress:** EPIC-001 (Foundation), EPIC-002 (Research), EPIC-005 (Forge Loop), EPIC-010 (Auto Paper Trading), EPIC-013 (Closed Loop)
- **Backlog / Not Started:** EPIC-003, EPIC-004, EPIC-006, EPIC-008, EPIC-011, EPIC-012, EPIC-014
- **Next Story Number:** US-143
- **Going-forward rule:** All new initiatives, bug fixes, and infrastructure work must be assigned a US-XXX number and tracked in this index before implementation begins.

---

## Related Notes
- [[00-Enhancement-Backlog]] - Strategy-specific enhancement ideas (A-001 to B-010, F-001 to F-006)
- [[EPIC-014-Tech-Debt]] - Infrastructure quirks and workarounds
