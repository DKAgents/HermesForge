---
type: connection-health
updated: 2026-09-01T05:57:08Z
tags: [connection-weaver, knowledge-graph, dashboard]
---

# Connection Health Dashboard

## Run Summary
| Metric | Last Run | Total |
|--------|----------|-------|
| Notes examined | 5 | 260 |
| Connections created | 4 | 138 |
| Review queue | 60 | 60 |
| Avg score | 2.3 | — |

## Graph Density Signals
- Total wikilinks in vault: ~3952
- Total notes: 2026
- Avg degree per note: 1.951
- Notes with links: 771 (38.1%)
- Orphan notes (no links): 1254 (61.9%)

## Weakly Connected Areas
- `04-ForgeLoop` — 26 notes, avg degree 0.0
- `04-ForgeLoop/Maintenance` — 47 notes, avg degree 0.0
- `05-Research/Market-Intelligence` — 19 notes, avg degree 0.0
- `05-Research/Edge-Candidates` — 28 notes, avg degree 0.04
- `02-Backlog/Stories` — 67 notes, avg degree 0.09

## Recent Discoveries (last run: 2026-09-01T05:57:08Z)
- **08-Knowledge/Insights/INS-2026-08-02-multi-filter-bull-trap-detection-with-volume-triggered-stop-.md** → **08-Knowledge/Trading-Systems/technical-analysis-financial-markets-murphy/risk-guidelines/RG035-combining-technical-factors-with-money-management-for-stop-p.md** (score 4.0): INS-2026-08-02 describes volume-triggered stop logic for bull trap exits, while RG035 mandates that protective stops must always be placed at valid technical levels. This creates a cross-reference where the volume-based trigger must still respect RG035's technical support/resistance placement rules, preventing purely mechanical stop placement.
- **08-Knowledge/Insights/INS-2026-08-02-multi-filter-bull-trap-detection-with-volume-triggered-stop-.md** → **08-Knowledge/Trading-Systems/technical-analysis-financial-markets-murphy/rules/R082-breakouts-must-be-accompanied-by-heavy-volume.md** (score 5.0): Note A synthesizes a two-step sequence where R052's price filters precede volume analysis; Note B provides the foundational volume rule (heavy volume required for valid breakouts) that, when absent, triggers Note A's bull trap detection logic.
- **08-Knowledge/Insights/INS-2026-08-02-multi-filter-bull-trap-detection-with-volume-triggered-stop-.md** → **08-Knowledge/Trading-Systems/technical-analysis-financial-markets-murphy/risk-guidelines/RG003-protective-stop-placement-relative-to-round-numbers.md** (score 4.0): Linking these notes refines the volume-triggered stop placement strategy by adding a filter to avoid round numbers, where protective stops are likely to be clustered and prematurely triggered.
- **08-Knowledge/Insights/INS-2026-08-02-multi-method-stop-trailing-p-f-columns-meet-pivot-intraday-r.md** → **08-Knowledge/Trading-Systems/technical-analysis-financial-markets-murphy/risk-guidelines/RG020-protective-sell-stops-on-point-and-figure-charts.md** (score 4.0): RG020 introduces box size sensitivity as a parameter for P&F stop placement, which directly refines the RG023 trailing mechanism described in Note A by specifying that smaller box sizes yield more frequent O-columns for tighter trailing. This adds a concrete optimization dimension to the two-phase exit architecture.

## Reflection Notes
- Run 48: Created 5 connections from 5 notes. Avg score: 3.1.
- Run 49: Created 4 connections from 5 notes. Avg score: 4.4.
- Run 50: Created 2 connections from 5 notes. Avg score: 2.7.
- Run 51: Created 4 connections from 5 notes. Avg score: 1.9.
- Run 52: Created 4 connections from 5 notes. Avg score: 2.3.
