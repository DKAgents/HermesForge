# HermesForge level-up invariants

Frozen 2026-09-27. Desktop Fable and Grok Expert reason over this. They do not edit it. Cheap CLI models gather evidence and later build one PASS story at a time.

## What this pass is

Read-only audit and stories. No production trading, no vault moves, no model swaps, no soul rewrites, no strategy edits.

## Scoreboard

- Paper R is operational fiction until hostile agrees.
- STR-Q frozen hostile: paper +1,305R vs hostile −104R on 1,721 scored trades (2,285 outside the 1k-bar cache).
- T1-01 Phase 1B: hostile −1,040R. T1 scanners stay OFF (`T1_ENABLED` false).
- `#paper-trading` 30-day card (+1,858R, 51% WR, STR-Q = 99.9% of closes) is the paper book.
- Auto-kill on STR-Q is consistent with hostile. Do not un-kill from the green card.
- Every public card must cite paper R and hostile R, or it is wrong.

## Trading

- Paper only. No product fills have occurred. US-121 stays blocked.
- Jev (`typesafe/jev-1.13` or Jev Router) classifies. It is not a T1/T2/T3 chat model. It does not order, journal, or post. A Jev BUY is not a ship signal.
- Hyperliquid later: agent-per-user. Master key never on the VPS. Agent cannot withdraw.
- Polymarket later: L2 API credentials only. Signer stays off the box. L2 can still trade the account to zero.
- Schwab later: Individual API = own account. Group needs Trader API – Commercial approval. No invented delegate.
- Secrets live outside `/root/.hermes/.env`. Discord and the default profile cannot read the secrets dir.
- Do not register wallets, create agents, or request production broker keys in this pass.

## Vault

- One vault. Roots `vault/code/` and `vault/trading/`. Not a second vault.
- Do not move files in this pass. Map broken links only.
- Code agents do not write trade notes. Trade agents do not write code notes.

## Research pipeline

- Insider thread (2026-08-30) is a checklist: hypothesis, shift(1), leakage critic, trial-counted deflated Sharpe, walk-forward on the worst fold, path sizing, kill rule before deploy.
- Do not vendor that post’s code. A public review found deflated-Sharpe unit bugs and walk-forward warmup/purge gaps.
- Hostile fill remains the label. Generation is not the job.

## Souls and graph

- Souls required only for profiles that post, commit, or could order.
- Crons get a wrapper, not a soul. Jev gets a schema, not a soul.
- Inventory missing bans. Do not rewrite souls here.
- Graph work is skill-load waste only. No rewire.

## Git

- Commit the story diff. No auto-commit-on-edit.
- Never commit `.env`, `.secrets`, journals, or snapshot payloads.
- One rebuild dry-run is a later story, not this pass.

## Who does what

1. Cheap CLI: evidence bundle, redacted, no secrets.
2. Desktop Fable: stories in the fixed format.
3. Desktop Grok Expert: PASS/FAIL each story.
4. Cheap CLI: confirm every path exists. Build one PASS story.
5. Desktop Fable: accept the diff.

Story format:

```
ID:
Files (must exist):
Ban:
Verify command:
Fail if:
Builder: cheap
```

No verify command = FAIL.

## Out of scope

ML training, live or group execution, second-brain file moves, strategy rule changes, cache widening, hermes update, un-kill STR-Q, new scanners.
