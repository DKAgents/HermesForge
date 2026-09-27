# One thesis pipeline

Status: read-only design; this document is the sole authorized write. Read `quant-path.md` and `platform-gaps.md` first. No implementation or launch is authorized.

Every new thesis follows the same sequence:

**Propose → register with timeframe and venue → paper with one booked fill equal to the posted fill → hostile rerun on that timeframe's bars → streak and heat limit → launch only through a delegated wallet.**

Timeframe is a required parameter, not a separate pipeline. STR-Q is only the current book used below as a worked example, not the template for every thesis. A positive paper card cannot skip any stage. Missing implementation, missing evidence, failure or ambiguity means BLOCKED, not PASS.

## Required timeframe contract

`timeframe` must be exactly one of `scalp`, `day`, `swing`, or `position`. `venue` must be explicit. Registration binds the selected timeframe to one approved, versioned policy containing:

- `bar_size`: the bars used for the thesis, paper evidence and hostile rerun;
- `hold_limit`: the maximum holding period, with explicit units and venue/session semantics;
- `heat_cap`: the permitted concurrent capital at risk, with explicit units, equity basis and aggregation scope.

The same policy travels with the thesis ID/version, trial ID, trade IDs and data window through every stage. Timeframe selects these settings; it never selects a shortcut or an independent research-to-launch path. A timeframe heat allocation cannot override the governing portfolio-wide limits or the single-idea risk ceiling of 1% of capital. Heat is concurrent open risk, not average R, not notional exposure and not historical drawdown.

No verified four-class policy mapping was found in the inspected registration/risk paths. Therefore this report supplies no invented bar sizes, holding periods or heat percentages. Missing approved values block registration; do not silently inherit STR-Q's settings or choose among unrelated constants. Resolving policy authority is prerequisite work, not permission to change a threshold.

## 1. Propose

One existing file: `scripts/research/full_research_pipeline.py` — EXISTS; reusable proposal orchestration, not an enforced end-to-end admission gate.

Evidence: lines 63–79 collect discovered edges and optionally stage candidates; lines 116–145 reuse the existing research runner. Researcher can supply any falsifiable thesis through this workflow, including a book-grounded or manually proposed thesis; automated discovery is not mandatory.

Output: a mechanism, source, entry/exit specification, universe, intended timeframe and venue, expected effect after existing costs, comparison baseline and falsification criteria. Mark discovery results as exploratory; they cannot become out-of-sample proof by registering them afterward. Freeze the next trial before its testing. Reuse existing researcher/backtester/Risk Guardian ownership, not new agents or a second swing pipeline.

## 2. Register with timeframe and venue

One existing file: `scripts/gauntlet/hypothesis_register.py` — EXISTS, PARTIAL; the required timeframe-policy admission contract is MISSING.

Evidence: lines 202–254 require venue and timeframe as function arguments, reject duplicate IDs and persist a registration timestamp. But timeframe is a free-form signal interval (documented as `5m` or `1h` at line 222), not the required four-class field. The record does not resolve bar size, hold limit and heat cap or bind their policy provenance.

Required output before paper: immutable trial identity, explicit venue, valid timeframe class, resolved approved policy and source/version, entry/exit rules, cost assumptions and unchanged failure criteria. Empty/unknown timeframe, missing venue or unresolved policy must block. Preserve earlier trials and legacy evidence; do not silently relabel old registrations or rewrite failures. Registration grants research eligibility only, never execution permission.

## 3. Paper with one booked fill equal to the posted fill

One existing file: `scripts/paper_trading/capture_sweep_signals.py` — EXISTS as the current-book implementation; PARTIAL and STR-Q-specific, not a universal fill-equality gate.

Evidence: lines 388–426 assess the setup through JEV, open the paper trade and then post. Lines 223–236 separately simulate a posting-only fill, replace the outgoing entry and allow an optimistic fallback. Thus an existing capture file does not establish booked/posted equality for a new thesis.

Required behavior for every thesis: resolve one canonical simulated executable fill with timestamp, method and provenance; present that setup to JEV; book and render that same fill under one trade ID. Compare displayed prices at declared precision. Keep the fixed stop/target rules and risk limits; reject invalid setups rather than alter thresholds. A failed post retains the one booking and retries the identical payload without booking another trade. Missing fill evidence or missing setup linkage cannot pass this stage.

JEV remains the entry decision. JEV approval is not a launch approval and cannot override a kill. The trainer is neither an entry replacement nor a launch gate. Paper exits must also use valid post-entry chronology; the current-book exit defect recorded in `quant-path.md:66` remains a separate blocker, not an authorized repair here.

## 4. Hostile rerun on the registered timeframe's bars

One existing file: `scripts/paper_trading/hostile_fills.py` — EXISTS, PARTIAL; a complete registration-driven, all-timeframe hostile gate is MISSING.

Evidence: lines 35–45 use strategy-specific holding limits; lines 54–78 load cached bars without accepting the required timeframe-policy contract. This is reusable hostile-report machinery, not proof that an arbitrary swing thesis receives its registered bars and hold limit.

Backtester must replay the exact admitted cohort using the registered venue, bar size, hold limit, strategy version and unchanged cost rules. Preserve no-fills, coverage gaps, entry delay, fees, adverse exits, same-bar ambiguity and the paper-to-hostile trade reconciliation. Insufficient history, a wrong bar interval or a timeout is unknown/BLOCKED. No fallback to another timeframe's bars and no substitution of current quotes for historical evidence. Existing leakage, out-of-sample and multiple-testing checks remain supporting requirements, not bypasses.

## 5. Streak and heat limit

One existing file: `scripts/research/auto_kill_manager.py` — EXISTS for streak recommendations; the combined, timeframe-aware streak-and-heat promotion gate is MISSING.

Evidence: lines 62–109 calculate maximum non-positive-R streak and apply the existing threshold; lines 154–190 return recommendations rather than a durable permission transition. They do not enforce the registered timeframe's heat cap.

Risk Guardian requires ordered, cohort-specific streak evidence plus a time-indexed reconstruction of overlapping positions and their capital at risk. Evaluate paper and hostile results separately against unchanged approved limits. Apply the registered heat cap and governing portfolio limits; retain existing drawdown checks rather than treating heat as a replacement. Missing overlap/equity data cannot count as zero heat. A favorable average or trailing streak cannot erase a maximum-streak failure or standing kill.

Existing heat machinery is not absent: `scripts/paper_trading/portfolio_risk_guard.py:187-219` checks aggregate open risk, but its interface has no timeframe policy. This supporting helper is not the complete stage or a second path. No limit is selected, reconciled or changed here.

## 6. Launch only through a delegated wallet

Existing complete gate file: **MISSING**. The previously proposed `scripts/governance/platform_delegation.py` does not exist.

Only an eligible thesis with explicit passes from all earlier stages may request Risk Guardian review and separate human launch approval. Execution must then be confined to a supported delegated wallet/venue authority with verified scopes, expiry, revocation, denied-action behavior and isolated credential delivery. Master credentials are not a substitute. Keys must not be added to `.env`, Git, prompts or this report; use owner-controlled secret handles or OS credentials under separate approval.

`platform-gaps.md:145-155` distinguishes upstream capabilities from missing local integration: Hyperliquid and Polymarket support forms of delegation, but local activation remains blocked; Schwab's required delegation contract is unverified. An unsupported venue stays blocked. Neither a capability document nor a validator alone constitutes a usable delegated wallet. No live order, funding, signer authorization or account interaction is authorized here.

## STR-Q: worked example, not another path

Use the supplied snapshot in `quant-path.md:7-20`: 11,443 paper trades, +0.80 mean R, 51.1% win rate, profit factor 2.73, maximum loss streak 22 against threshold 8, file status `hypothesis`, and frozen hostile scoreboard -104R. These are not fresh ledger aggregates.

Its current hostile implementation explicitly uses 5m bars and a 75-minute hold (`scripts/paper_trading/hostile_fills_strq.py:3-15,40-45,100-109`). Those are existing STR-Q assumptions, not the new swing policy. Its divergent booked/posted fill fails stage 3; its frozen hostile result does not support stage 4 promotion; its streak breaches stage 5. STR-Q remains killed and US-121 remains blocked. A positive card, later sample, trainer score or JEV approval cannot change that. The growing hostile-file sum is not the frozen scoreboard.

## Verification and boundaries

Read-only source inspection checked the cited functions and file existence, including the absent delegation gate. No production module was imported or executed. Source existence establishes partial machinery, not runtime enforcement. No code/config/threshold edits, service restarts, strategy un-kills, credential reads, `.env` output, posts, orders, backlog writes, commits or pushes are part of this task. Only this report is written.

## First missing stage for a new swing thesis — one file, no live order

**Stage 2: registration with an enforced timeframe-policy contract. One file: `scripts/gauntlet/hypothesis_register.py`.** A proposal can already be produced, but merely storing `timeframe="swing"` does not resolve or validate its bars, hold limit and heat cap. This is the first unmet dependency for a new swing thesis, earlier than the current-book fill repair prioritized in `quant-path.md`.

A separately approved, orchestrator-delegated coder task would make that existing registration boundary require the four-class timeframe and venue, bind approved policy values/provenance, and reject unresolved policies without a write. Offline acceptance: valid swing registration retains all three approved settings; missing/unknown timeframe, absent venue or missing policy fails closed; legacy records remain untouched. Do not invent policy values, migrate history or claim this one-file change fixes downstream consumers. No live order; no implementation in this report.
