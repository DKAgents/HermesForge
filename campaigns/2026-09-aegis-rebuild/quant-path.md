# Quant path: paper evidence before delegated live eligibility

Status: plan only. Read `platform-gaps.md` first. This document is the sole authorized write; no code, config, services, thresholds, credentials, orders, strategy status or kill flags are changed.

## Starting point

Use the principal's supplied STR-Q book snapshot, not a fresh aggregate over a moving ledger:

| Item | Supplied baseline |
|---|---|
| Paper trades | 11443 |
| Mean R | +0.80 |
| Win rate | 51.1% |
| Profit factor | 2.73 |
| Maximum consecutive losses | 22 |
| Kill threshold | 8 |
| File status | hypothesis |
| Hostile scoreboard | -104R |

The paper book is a hypothesis-generating record, not evidence of live tradability. STR-Q remains killed: positive mean R and profit factor do not override its streak breach. The frozen hostile -104R scoreboard is separate from a growing hostile JSONL sum; do not combine populations or erase the frozen result. File status `hypothesis` is not execution permission. US-121 remains blocked.

JEV remains the entry model. For this plan, the logistic trainer in `scripts/gauntlet/jev_ml_predictor.py` is not an authorized entry decision path and must not replace JEV. Evidence qualification: `platform-gaps.md:90-100` found static indirect predictor calls through the prefilter; that is not proof of successful runtime use or authority to promote the trainer. Resolve that discrepancy in a separate read-only trace before any future wiring. It is not the first change proposed here.

Hyperliquid, Schwab and Polymarket remain blocked until a supported delegate API is integrated and verified without placing keys in `.env`. Public vendor capability alone does not satisfy the local delegation gate.

## Reuse the books and workflow already on disk

Use the existing Forge Loop, researcher, backtester, Risk Guardian, publisher and orchestrator. Product-owner puts every implementation into the prioritized backlog first. Do not add agents, a graph framework, a broker platform or a data vendor.

The verified local book source is John J. Murphy, *Technical Analysis of the Financial Markets*: `Inbox/John_J._Murphy_-_Technical_Analysis_Of_The_Financial_Markets.pdf`. Its ingested notes are under `trading/knowledge/Trading-Systems/technical-analysis-financial-markets-murphy/`. No additional book is assumed merely because the task refers to books.

Use these existing notes as research inputs, not automatic trade rules:

- `rules/R052-filters-for-confirming-breakouts.md:18-25`: close-confirmation and volume as ways to distinguish a breakout from an intraday penetration; source metadata cites page 122. A candidate can test whether confirmation improves net outcomes over a pre-registered baseline. It must account for the later entry and associated fill cost, not give the confirmed signal an earlier price.
- `risk-guidelines/RG033-handling-drawdowns-and-losing-streaks.md:18-25`: losing streaks and equity recovery matter beyond average return; source metadata cites page 399. This motivates preserving failure evidence, not relaxing a kill rule.
- `risk-guidelines/RG045-maximum-intraday-drawdown.md:18-27`: drawdown is peak-to-trough equity loss, distinct from average trade R; source metadata cites page 501. Mark intratrade exposure when available; a closed-trade-only curve must be labeled as such.

These are ingested book notes, not newly verified PDF quotations. Researcher should carry exact note references into the candidate and check the source passage when operationalizing an ambiguous rule. Book percentages or historical examples do not authorize changing current thresholds. Do not relabel a STR-Q variant to bypass its kill or reuse its rejected evidence as an independent success.

## Required gate order

Candidate → paper fill matches posted fill → hostile rerun → streak and drawdown rule → live only through delegation.

A missing input, failed gate, ambiguous outcome or missing implementation means BLOCKED, never implied PASS. Keep the same candidate version, trade IDs, data window and fill provenance across gates. Changing the hypothesis creates a new recorded trial; it does not overwrite a failed result. The existing gauntlet's leakage, out-of-sample, multiple-testing and robustness checks remain supporting evidence within this sequence, not something five labels replace.

### Gate 1 — Candidate

One implementation file: `scripts/gauntlet/hypothesis_register.py` — EXISTS; registration is implemented, automatic book-grounded admission is incomplete.

Evidence: `:202-254` records a unique hypothesis ID, description, falsification criteria, expected effect, venue, timeframe, primitives and registration timestamp. It does not itself demonstrate an edge or verify the book citation.

Researcher proposes one falsifiable mechanism from the local notes. Before testing, record its source, exact entry/exit rules, allowed universe, information available at decision time, expected gross effect, existing cost assumptions, comparison baseline and unchanged kill/drawdown rules. Use the existing trials ledger to retain every attempt, including failures; do not search many variants and report only the winner.

Admission requires an identified backlog owner, reproducible specification and cost/leakage plausibility. Unsupported book analogy or an effect that disappears under existing costs stays a candidate/rejection—not paper-validated. JEV approval of an individual setup is not candidate-level statistical validation.

### Gate 2 — Paper fill that matches the posted fill

One implementation file: `scripts/paper_trading/capture_sweep_signals.py` — EXISTS, but the required equality gate is NOT implemented correctly.

Evidence: `:415-426` books the paper trade before posting. In `:223-236`, the posting path separately obtains a G3 fill and replaces only the outgoing entry, with an optimistic fallback on error. The paper book and setup can therefore describe different trades.

Required behavior: resolve one simulated executable fill from the available data, freeze its timestamp/method/provenance, and use that same record for JEV's entry assessment, the paper ledger and the existing publisher. Distinguish signal price, simulated fill and stress fill; do not present one as another. Recompute derived paper quantities consistently without moving the strategy's stop, target, risk limits or thresholds. If the fixed setup becomes invalid at the simulated fill, reject it rather than repair the edge by changing its rules.

The setup and updates must carry the same trade ID and booked prices; compare rendered prices at the declared display precision. Posting failure is a delivery failure: retain the paper record and retry the identical payload without opening a duplicate trade. It cannot count as a matched-post gate pass until the original setup is linked. Missing fill evidence must not silently become a realistic fill.

This gate also needs trustworthy exits: the same file's `:619-647` aggregates recent candles without entry-time filtering. That is a separately scoped chronological-exit defect, not permission to expand the first fill-consistency change. Until resolved or excluded with evidence, affected outcomes cannot validate the strategy.

### Gate 3 — Hostile rerun

One implementation file: `scripts/paper_trading/hostile_fills_strq.py` — EXISTS for STR-Q; it is a reporting engine, not an enforced promotion gate.

Evidence: `:3-15` describes delayed/trade-through entries, fees, adverse stop fills and time exits; `:40-45` fixes its existing assumptions and output. `:293-331` contains report persistence. Do not edit this protected engine, change its cost assumptions or invoke destructive rescore options under this plan.

Backtester reruns the exact admitted paper cohort against the existing hostile model in an isolated replay, with the same source bars and strategy version. Preserve no-fills, missing bars, coverage, costs, risk denominator and trade-by-trade paper/hostile differences. An incomplete or timed-out rerun is unknown, not a pass. Use existing data; if the required historical window cannot be reconstructed, report the gap rather than substitute current prices.

Progress requires the pre-registered hostile criteria and existing gauntlet evidence to pass—not merely a positive paper book. The supplied -104R hostile scoreboard does not support promoting STR-Q. A subsequent result must identify its own cohort and cannot silently replace that frozen reference. This STR-Q-specific engine is not automatically a valid hostile model for an unrelated strategy or venue.

### Gate 4 — Streak and drawdown rule

One integration target: `scripts/research/auto_kill_manager.py` — EXISTS for streak/kill analysis. A single implementation enforcing the combined streak-and-drawdown promotion gate DOES NOT EXIST in the inspected path.

Evidence: `:62-70,86-109` computes maximum non-positive-R streak in CSV order and applies the existing threshold 8. It returns a KILL recommendation rather than enforcing a durable permission transition. Existing drawdown machinery is separately available in `scripts/gauntlet/position_manager.py:295-356`; reuse it rather than invent a second risk model. Its empty-curve behavior can report no breach, so missing equity evidence must not qualify as a promotion pass.

The future integration in the named target must evaluate both rules over explicitly identified, ordered records and a documented equity curve, using the existing approved thresholds. Preserve the current streak result; do not swap maximum streak for trailing streak, reorder history to obtain a pass or infer percentage drawdown directly from mean R. Report paper and hostile risk results separately, including starting equity, cost basis, window and whether intratrade marks exist. If the governing drawdown rule or necessary inputs cannot be established, remain blocked; do not invent a threshold.

STR-Q fails on the supplied maximum streak 22 versus threshold 8 regardless of +0.80 mean R. The file status remains `hypothesis`, the kill remains set, and the post must communicate killed/paper-research status—not LIVE. Publish one reviewed decision receipt with the book/window, both rule results and reason; file status and Discord presentation must agree with it. A favorable new sample or JEV score does not clear a standing kill automatically.

### Gate 5 — Live only through delegation

One proposed gate file: `scripts/governance/platform_delegation.py` — DOES NOT EXIST. No inspected file implements this complete final authorization gate.

Only after the preceding gates pass for an eligible strategy may Risk Guardian review a promotion request and the principal explicitly authorize live use. Passing research gates is necessary, not sufficient, and this plan grants no live approval. STR-Q is not a promotion candidate here.

For each of Hyperliquid, Schwab and Polymarket, require a verified supported delegate API, owner-granted limited authority, expiry/revocation behavior, permission checks and isolated credential delivery through a secret handle or OS credential mechanism. No keys in `.env`, Git, prompts or reports; no master-account credential substitution. Missing delegate API or unverified semantics means BLOCKED for that venue, even if the other venues eventually pass.

Validate denied actions and revoked/expired authority offline before any separately authorized deployment. Preserve paper-only defaults, existing risk limits and human control. No live order, funding action, signer authorization or account interaction is part of this plan.

## Close the learning loop without manufacturing permission

Reuse `scripts/research/full_research_pipeline.py` as the existing research orchestrator and the Forge Loop for ownership. Each completed vetting run produces a bounded evidence receipt: candidate/trial ID, source note, code/data version, gate results, exact failure reason and next backlog story. Append failures and a post-run root-cause note to the existing campaign failure log; unknown causes stay unknown.

Researcher uses failed fills, hostile losses and risk breaches to propose a new falsifiable edge—not to lower the hurdle. Backtester supplies reproducible evidence; Risk Guardian reviews independently; publisher renders the same decision; orchestrator never equates a post with authorization. Closed outcomes may later inform offline trainer evaluation, with paper and cost-adjusted labels kept distinct. The trainer does not become another entry authority, and JEV cannot override any gate or kill.

## First change that improves the vetting loop

One file: `scripts/paper_trading/capture_sweep_signals.py`.

First backlog story: eliminate the second, posting-only fill decision. Prepare one canonical simulated-fill record before JEV assessment and paper persistence, then pass that same entry and provenance to the existing publisher; remove the later independent entry substitution and prohibit silent optimistic fallback from qualifying as verified fill evidence. Keep existing entry/exit thresholds, stop/target rules, kill state and JEV authority unchanged.

Publisher owns the posting-path work, coordinated through orchestrator with coder and Risk Guardian review. Acceptance uses isolated deterministic fixtures and the actual pipeline functions with all persistence/network effects redirected: booked fill equals posted fill at display precision; changed simulated fill reaches both consumers; missing simulation cannot pass; a failed post retains one trade and retries the same payload. Do not post, retrain, rewrite historical trades, repair exits in the same story, or place a live order. This improves the evidence entering hostile and risk vetting; it does not un-kill STR-Q or confer live eligibility.
