# Platform gaps — live-tree assessment

Assessed: 2026-09-27, approximately 15:13 PDT. Starting revision: `d91d2864`, branch `main`.
Scope: read-only inspection; this report is the only authorized project write. No implementation, service restart, config edit, credential access, orders, threshold changes, STR-Q un-kill, or backlog mutation. Paper only; US-121 remains blocked.

## Verdict

Reuse the existing fleet and Python workflows. The principal gaps are enforceable authority, inconsistent status/outcome provenance, and incomplete/unsafe Git staging—not missing agents or a graph framework. No model downgrade has demonstrated zero quality loss.

Completed migrations, the auto-kill summary reason (`6e15ae78`), SOUL-versus-config discovery, off-box backup, and the failed gateway user drop are accepted, not proposed again. The campaign brief files exist, but their historical inventories/cost estimates are not current measurements.

Each goal below names one file and whether it exists. “Closure limit” identifies where one file cannot truthfully deliver the whole goal. Proposed changes are not authorization to implement them.

## 1. Souls that actually constrain tools

Gap: role prose is not an execution permission boundary. Existing tool scope/hooks are usable machinery, but no inspected Forge-specific role authorization gate binds a workflow owner to allowed effects. A root process with arbitrary terminal/code tools can bypass a path blacklist.

Evidence: `scripts/governance/validate_handoff.py:10-16` explicitly calls itself skippable. The installed runtime `/usr/local/lib/hermes-agent/agent/tool_executor.py:622-636` lets pre-tool hook exceptions pass; `:639-689` is the actual scope → hook → guardrail → dispatch boundary. `/usr/local/lib/hermes-agent/agent/agent_runtime_helpers.py:2210-2223` and `/usr/local/lib/hermes-agent/model_tools.py:755-769` also fail open on hook errors. These are inspected on-disk sources, not proof that the already-running gateway has loaded them.

One file: `/usr/local/lib/hermes-agent/agent/tool_executor.py` — EXISTS.
Smallest meaningful change: fail-closed, trusted-role authorization at the existing dispatch boundary, before side effects; reject unknown roles and unauthorized terminal/code/delegation capabilities rather than interpreting SOUL prose. Verify sequential, concurrent, nested and bridged calls with denied-effect tests.
Closure limit: this closes an agent-loop boundary, not OS isolation or every alternative dispatch entry. Full confinement needs audited coverage of the sibling paths and separately approved runtime/OS deployment. Do not pretend one SOUL edit or an unregistered plugin solves it. Gateway remains root; do not retry the failed user drop here.
Owner: architect + coder, with security/risk review.

## 2. New agents only for unowned workflows

Gap: ownership is documented, but accountable owner and actual executor are not the same thing. No new unowned workflow was established.

Evidence: `/root/.hermes/profiles/orchestrator/SOUL.md:6-31` assigns coordination and specialist routing; `code/forge-loop/FORGE_LOOP.md:57-66` already assigns research, design, coding, backtesting, risk, documentation and backlog. Publisher ownership is separately established in `/root/.hermes/profiles/publisher/SOUL.md:4-17`.

One file: `code/forge-loop/FORGE_LOOP.md` — EXISTS.
Close the ownership gap there with a workflow → existing accountable profile → actual script/cron → input/output → escalation table. Assign operations incidents to orchestrator, implementation to coder, and post-run evidence/RCA to documenter/Aegis as appropriate. A script-only job does not need a new persona. Create no agent unless that table demonstrates a genuinely ownerless current workflow.
Owner: product-owner + orchestrator.

## 3. Workflow reuse, token cost and graph shape

Gap: dependency shape already exists; comparable measured run cost and explicit reuse contracts do not.

Evidence: `code/forge-loop/FORGE_LOOP.md:15-21` defines seven phases; `/root/.hermes/profiles/orchestrator/SOUL.md:36-63` defines fan-out followed by dependent review. `scripts/research/full_research_pipeline.py:116-145` actually calls the existing research runner instead of replacing it. `scripts/governance/validate_handoff.py:29-41` contains stage/tier and consumes/produces contracts. `campaigns/2026-09-aegis-rebuild/cost-30d.md:6` labels its figures estimates, not billing.

One file: `scripts/research/full_research_pipeline.py` — EXISTS and already substantially built.
Extend its existing orchestration with explicit stage results, dependencies and run receipts; reuse collectors and pass bounded structured artifacts to judgment stages. Record actual model, input/output tokens, cache accounting when available, elapsed time, retries and total cost—including failed/delegated calls. Do not equate bytes of removed skill descriptions with billed-token savings.
Graph: collect independent evidence in parallel → synthesize → implement/backtest only after prerequisites → independent risk review → publish/document. Keep mechanical jobs no-agent. Do not combine unrelated schedules into one giant run.
Closure limit: instrumenting this runner covers research, not every fleet workflow. There is no justification here for a new graph framework; extend this file, not a replacement platform.
Owner: architect + coder.

## 4. One error log and a post-run root-cause note

Gap: failures generate alerts/raw output, not a durable correlated incident and closure record. An error message is not a root cause.

Evidence: `/root/.hermes/scripts/cron_watchdog.py:39-50,75-82` checks job status and alerts, then exits without an incident/RCA record. It also exits before checking anything when its posting token is absent (`:17-18`). The repository copy, `scripts/discord/cron_watchdog.py`, has the same relevant behavior. `campaigns/2026-09-aegis-rebuild/failure-log.md:1-4` is only a historical list. The Hostile Fill Report output `/root/.hermes/cron/output/5041c3c5103f/2026-09-27_22-10-45.md:3-8` records a 600-second timeout; which child/stage caused it is unproven.

One file: `/root/.hermes/scripts/cron_watchdog.py` — EXISTS; this is the scheduled copy, not merely the repository copy.
Close the detected-run reporting gap by appending deduplicated incident records to the existing campaign `failure-log.md`, regardless of Discord availability: run/job ID, stage if known, raw evidence link, impact, owner, remediation story and verification status. Append a post-run note to that same log: proven cause, or explicitly “cause unknown; investigation required.” Preserve raw logs; do not invent an RCA or automatically widen timeouts. Orchestrator owns closure and Aegis/documenter supplies the evidence note.
Closure limit: a watchdog cannot recover missing internal stage timing or guarantee an evidence-proven RCA automatically. Instrumenting producers is separately scoped work. Publisher owns this alerting file; no edits or posts here.

## 5. Shared Discord template and setup-linked updates

Gap: setup-link machinery exists, but format duplication and missing metadata produce inconsistent/unlinked updates.

Evidence: `scripts/discord/embed_publisher.py:392-410,678-705` assembles separate daily/sweep fields. `:590-600` registers successful setup message/channel IDs and URL when trade identifiers are present. `scripts/paper_trading/trade_id.py:102-124` already constructs canonical Discord links. `scripts/paper_trading/trade_monitor.py:265-281` links an update only if IDs exist; otherwise it silently displays a bare ID. Sweep updates have a second formatter in `scripts/paper_trading/capture_sweep_signals.py:528-572`.

One file: `scripts/discord/embed_publisher.py` — EXISTS.
Make this existing publisher module the common rendering contract rather than create a competing publisher: paper/permission status, exact trade ID, price provenance, chart, timestamp, and original setup URL. Keep strategy-specific fields as extensions. Treat missing setup metadata as an explicit linkage failure, not a fabricated URL or evidence of successful posting.
Closure limit: sharing update renderers end-to-end requires separately authorized caller adoption in both update paths. A one-file renderer edit alone cannot make those consumers reuse it. Publisher owns all such changes; this audit sends no test posts.

## 6. Prioritized story backlog before code

Gap: the requirement already exists, but it is procedural, and the handoff contract does not require a ready, prioritized story.

Evidence: `02-Backlog/BACKLOG_INDEX.md:12` requires a story for every initiative/fix/infrastructure change. `code/forge-loop/FORGE_LOOP.md:51-55` specifies ready-first, dependency checks, elevated risk priority and a selection cap. `scripts/governance/validate_handoff.py:41,46-80` checks stage/tier and artifact fields, not story identity/readiness/priority. Its own `:10-16` warns it can be skipped. `Templates/User-Story-Template.md:21-38` has AC/dependency/DoD fields but not the campaign's explicit one-file/ban/verify/fail gate.

One file: `scripts/governance/validate_handoff.py` — EXISTS.
Extend the existing contract check to require an existing prioritized backlog story, owner, ready status, satisfied dependencies, exact allowed file, acceptance/verification command and bans. No code-changing handoff should pass without that receipt. Product-owner prioritizes; orchestrator dispatches to the appropriate specialist.
Closure limit: enriching the validator does not make it unskippable. Runtime enforcement belongs at the boundary in goal 1. This report files no stories; the next changes below must enter the existing backlog before implementation. US-121 remains blocked.

## 7. Git backup: code/configs yes, trade history no

Gap: hourly coverage is too narrow for code/config recovery and too broad inside `scripts/` for history safety.

Evidence: `/usr/local/sbin/hermes-git-sync:3-9` stages only `scripts campaigns`, commits the entire staged index, then pushes. The root crontab invokes it hourly. It misses `tests/`, `docs/`, `Templates/`, `02-Backlog/`, `code/forge-loop/`, root `.gitignore`, and runtime files outside the repository: default/profile configuration, SOULs, cron definitions, `/root/.hermes/scripts/` wrappers, service definitions and the sync script itself. Tracked runtime config snapshots were not found in the inspected index.

Read-only `git ls-files` also found already-tracked history, including `scripts/discord/published_signals.csv`, `scripts/paper_trading/hostile_fill_report.jsonl`, `scripts/paper_trading/hostile_fill_report_strq.jsonl`, `scripts/paper_trading/hostile_fill_report_strq_v2.jsonl`, and validation trade CSVs. `.gitignore:46-51` excludes the main ledger/journal/snapshots, but ignoring does not untrack these other histories. During this audit, Git reported the tracked STR-Q hostile JSONL modified by background activity; it was not touched or staged by this audit.

One file: `/usr/local/sbin/hermes-git-sync` — EXISTS.
Use explicit code/config/document allowlists and a fail-closed staged-payload check excluding trade history, snapshots, market data, secrets and account state—even if already tracked or staged by someone else. Refuse a foreign staged index. Export only approved non-secret config fields into versioned snapshots; never copy raw configs, `.env`, auth/token stores or full cron prompts blindly. Cover tests and the synchronization code itself. Raw secret recovery stays outside Git.
Closure limit: safely removing already-tracked histories from future tracking requires separate approval/index work; do not delete local data or rewrite history. A one-file sync change can stop future accidental history commits but cannot erase past commits. Off-box backup already exists; do not rebuild it or confuse it with Git.
Owner: coder via orchestrator.

## 8. JEV remains the entry decision; closed-outcome learning

Gap: outcome provenance, not absence of a trainer. The supplied “not called from capture or cron” is true of a direct trainer invocation, but the live call graph contains an indirect connection worth preserving.

Evidence: `scripts/paper_trading/capture_sweep_signals.py:388-415` calls the Jev prefilter before opening a paper trade. `scripts/gauntlet/jev_prefilter.py:49-61,120-130` lazily creates `MLPredictor`, obtains a prediction and includes it in Jev's state. `:197-220` leaves tier selection to Jev's probabilities. `scripts/gauntlet/jev_ml_predictor.py:49-82` loads a cache or trains from closed-trade features, labeling positive R as wins. This is static wiring evidence, not proof that a recent runtime call successfully trained.

The extractor `scripts/gauntlet/jev_feature_extractor.py:60-80` silently substitutes paper `r_multiple` when `gauntlet_r` is absent, filters by exit rather than entry date, and admits unparseable dates. Independent read-only CSV parsing found 7,500 eligible closed rows, of which 4,491 lack `gauntlet_r`.

One file: `scripts/gauntlet/jev_feature_extractor.py` — EXISTS.
Make the closed-outcome dataset provenance-strict: distinguish cost-adjusted outcomes from paper arithmetic, reject malformed/non-finite labels and ambiguous timestamps, and use entry-time feature provenance. Do not silently label optimistic fills as execution-adjusted evidence. Preserve existing cutover and decision thresholds; report unavailable/insufficient evidence rather than manufacture labels. Deduplicate outcomes by stable trade identity.
Closure limit: this fixes future training input, not an already-cached model; validate offline and let an explicitly approved refresh consume the corrected data. No new trainer, cron, threshold tuner or second entry authority. No training/cache writes were performed here.
Owner: coder + backtester; Risk Guardian review.

## 9. STR-Q research: book, kill state, file status and post must agree

Gap: paper research/book results, kill recommendation, and presentation status are separate sources. Positive paper mean R is not permission to run live or undo a kill.

Evidence: `scripts/research/auto_kill_manager.py:62-70,86-109` uses the maximum streak of non-positive R in CSV order, with the existing threshold 8, independently of mean R. `:154-190` returns recommendations; it does not persist a strategy permission flag. The summary reason is already fixed at `:245-252`. `scripts/discord/strategy_status.py:176-181` nevertheless hardcodes STR-Q as `LIVE`; `:348-369` renders that table. The sweep capture entry path (`scripts/paper_trading/capture_sweep_signals.py:431-482`) is self-contained, not a hypothesis-status loader. No canonical base STR-Q hypothesis/permission file was established by the inspected strategy paths; the wide-stop hypothesis is a separate variant, not a replacement authority.

One file: `scripts/discord/strategy_status.py` — EXISTS.
Remove its independent LIVE claim: derive its displayed status/reason from the existing kill result and any explicitly identified canonical permission record; if missing or contradictory, show KILLED/BLOCKED with the mismatch. Show separate fields for paper observation, execution permission, rule metric/order/window and evidence timestamp. Preserve the supplied result: maximum streak 22 versus threshold 8 despite mean paper R approximately +0.80. Do not reinterpret it as a trailing streak or quietly change ordering/window/threshold.

Consistency contract: one versioned decision receipt must identify strategy, book snapshot/window, rule result, permission status, reason and authorized owner. The post and file status must reference the same receipt; disagreement blocks an eligibility claim. A `RUN` recommendation or favorable regime cannot clear the standing STR-Q kill. Keep the frozen hostile -104R reference separate from growing hostile-file totals.
Closure limit: this one file closes the false dashboard claim, not a missing durable permission consumer across capture/research. That integration requires its own reviewed story. Do not mutate hypotheses/kill flags or recommend un-kill. US-121 remains blocked.
Owner: publisher, reviewed by Risk Guardian.

## 10. Price and trade history: one check, three PnL-sensitive signals

One consistency check performed, using an existing closed ledger row (no price fetch or pipeline run):

- ID: `STR-Q-liquidity-sweep_ZEC_2026-09-27_2140`.
- Long entry 1596.8; stop 1594.575714; exit 1594.5757.
- Recomputed `(exit-entry)/(entry-stop)` = -1.000006294R; stored R = -1.0. PASS at recorded ledger precision.
- `gauntlet_r` and setup URL are blank. This validates internal paper arithmetic only—not the market quote, execution realism, journal reconciliation, or Discord delivery.

At most three signals to investigate, not new trading indicators or proven alpha:

1. Booked versus posted fill divergence: the trade opens at `scripts/paper_trading/capture_sweep_signals.py:415-426`, while `:223-234` replaces only the posting dictionary's entry with a G3 realistic entry. This can make displayed and booked PnL disagree.
2. Pre-entry/chronologically ambiguous exits: `scripts/paper_trading/capture_sweep_signals.py:619-647` aggregates five candles without filtering by entry time, then checks stop before target. This can select an event that preceded entry or a later stop over an earlier target.
3. Mixed outcome labels: `scripts/gauntlet/jev_feature_extractor.py:62-80` can contaminate learning with optimistic paper R. That can change future paper selection, not retroactively establish real PnL.

One file: `scripts/paper_trading/capture_sweep_signals.py` — EXISTS.
For a separately approved paper-only story, preserve one booked/posted price provenance and evaluate post-entry candles chronologically, with an explicit conservative same-bar ambiguity result. Do not revise historical rows, change thresholds, or add a data vendor. Goal 8 separately addresses the third signal.
Owner: coder for ledger/exit logic; publisher must own any posting-path edits, with Risk Guardian review.

## 11. Model tiers: frontier to cheap without quality loss

Answer: none is proven safe to downgrade with zero quality loss. The concrete frontier-configured candidate is Aegis-Auditor's bounded evidence-gathering/drafting work, not its entire architecture/security judgment role.

Evidence: `/root/.hermes/profiles/aegis-auditor/config.yaml:5-6` selects `anthropic/claude-opus-4.8`; `scripts/governance/validate_handoff.py:29-36` permits T3 explore/draft but T2 decide/synthesize/commit. Safe field inspection found the default at v4-pro and red-team at v4-flash; most other profiles have no separate config. The live Weaver cron already uses `deepseek/deepseek-v4-flash`, so proposing its old T2→T3 downgrade would redo completed work. Blank delegation model overrides do not guarantee cheap children.

One file: `campaigns/2026-09-aegis-rebuild/cost-30d.md` — EXISTS.
Close the evidence gap there with a paired frozen-input comparison: citation accuracy, omissions, invariant violations, appropriate escalation, reviewer effort and total measured cost. Candidate: Aegis evidence extraction/draft on v4-flash, retaining higher-tier synthesis/acceptance and all code-changing floors. Deterministic extraction should use no LLM where possible.
Closure limit: this is an evaluation artifact, not a routing change or a quality guarantee. Actual routing requires separately approved configuration work; `config.yaml` is not edited here. No savings figures are claimed from stale estimates.

## 12. Hyperliquid, Schwab and Polymarket delegation

Gap: vendor delegation capability is not the same as a wired, least-privilege Forge adapter. No inspected local delegate API unifies these platforms. Do not substitute a master wallet key or ordinary bearer credential for scoped delegation.

- Hyperliquid: upstream delegation EXISTS. The official Exchange documentation exposes “Approve an API wallet,” and the official SDK `hyperliquid/exchange.py:635-657` implements `approve_agent`/`approveAgent`. Locally, `scripts/hyperliquid/connection_test.py:15-25,43-48` loads environment credentials but only queries testnet user state; that is not signed authentication or proof of an authorized delegate. No approval/funding/order request was made. Deployment remains blocked on explicit owner authorization, constrained adapter policy and secure credential delivery.
- Schwab: BLOCKED. No Schwab adapter/delegate API was found in inspected local scripts. The official public portal extraction exposed no usable delegation contract, and a browser attempt returned Access Denied. Ordinary app/account OAuth must not be asserted to provide a scoped autonomous-agent delegation API. Require verified supported delegation/permission semantics; if no such API exists, remain blocked rather than improvise one.
- Polymarket: scoped delegation EXISTS in the current official Session Keys documentation: a separate signer, venue scopes, expiry, revocation, and no withdrawals; Deposit Wallets only. Authorization requires owner action and Builder credentials. Safe/Proxy wallets are not automatically eligible. Local `scripts/gauntlet/polymarket_feed.py:3-16,29-35` is merely an unauthenticated research feed, not a delegated trading client. Integration/eligibility remain unverified and blocked for activation.

One file: `scripts/governance/platform_delegation.py` — DOES NOT EXIST (proposed).
A future paper-only capability validator could represent each vendor's supported scope, network, expiry/revocation evidence and credential handle, refusing unsupported delegates and all live execution. It must not invent a common order API, generate keys, authorize signers or place orders. Existing architect/coder/risk owners suffice; no broker agents needed.
Closure limit: a validator cannot create a missing vendor API or provide OS credential isolation. Owner-controlled secret-manager/systemd encrypted credentials should reach only an isolated adapter through credential handles/files—not `.env`, Git, chat or ordinary agent context. Provisioning is separate approval-required work; nothing is provisioned here.

Public evidence inspected:
- https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint
- https://raw.githubusercontent.com/hyperliquid-dex/hyperliquid-python-sdk/master/hyperliquid/exchange.py
- https://docs.polymarket.com/trading/session-keys.md
- https://docs.polymarket.com/trading/wallets-auth.md
- https://developer.schwab.com/products/trader-api--individual (access limitation above)
- https://hermes-agent.nousresearch.com/docs/user-guide/configuration
- https://hermes-agent.nousresearch.com/docs/developer-guide/plugins

## Verification and boundaries

Read source/callers and selected non-secret profile/cron fields; checked Git branch/status/tracked paths and proposed-file existence. Independently recomputed the one ledger arithmetic check and trainer-label counts with Python. No pipeline, validator with logging side effects, trainer, account connection test, posting function or order function was executed. No service/config/state/threshold changes; no `.env` or credential-file reads. Runtime data can change under existing jobs; this is an inspected snapshot, not a frozen backup. No commit or push was requested or performed by this audit.

## Next three code changes — each one file, no live trading

These are ordered backlog candidates, not filed or authorized implementations. Product-owner must create/prioritize ready stories before orchestrator delegates them; tests use isolated fixtures, never production data or Discord posts.

1. `/usr/local/sbin/hermes-git-sync` — explicit source/config coverage plus fail-closed history/secret/foreign-index exclusions. Coder via orchestrator. Acceptance: a disposable repo includes tests and approved sanitized config snapshots, excludes already-tracked trade histories, and refuses unrelated staged payloads; no live push, data deletion or history rewrite.
2. `scripts/discord/strategy_status.py` — eliminate the independent STR-Q LIVE claim and render kill/permission mismatch with the existing reason/rule evidence. Publisher via orchestrator. Acceptance: pure renderer fixtures retain STR-Q KILLED/BLOCKED even with positive mean paper R, include streak 22/threshold 8, and never post or alter any kill flag/threshold.
3. `scripts/gauntlet/jev_feature_extractor.py` — provenance-strict closed-outcome inputs for the already-connected trainer. Coder + backtester via orchestrator, Risk Guardian review. Acceptance: isolated fixtures reject ambiguous/non-finite outcomes and silent paper-to-cost-adjusted substitution, preserve valid entry-time features, and leave Jev entry authority, thresholds, live CSV and model cache untouched.
