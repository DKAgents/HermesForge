# LU-07: Soul Audit — Who Can Post, Commit, or Order

**Status**: note-only (no code edits)
**Date**: 2026-09-25
**Campaign**: 2026-09-aegis-rebuild

**Source directory**: `01-Agents/Profiles/` (8 profiles)

---

## Profile Capability Matrix

### Can Post?

| Profile | Discord tool? | Webhook? | Latent path |
|---|---|---|---|
| Orchestrator | No | No | terminal → curl with env DISCORD_BOT_TOKEN |
| Architect | No | No | terminal → curl |
| Coder | No | No | terminal → curl |
| Risk Guardian | No | No | terminal → curl |
| Product Owner | No | No | terminal → curl |
| Researcher | No | No | terminal → curl |
| Backtester | No | No | terminal → curl |
| Documenter | No | No | terminal → curl |

**Finding**: No profile has an explicit Discord or webhook tool. However,
ALL profiles have `terminal` — and the `DISCORD_BOT_TOKEN` environment
variable is available to any process that sources `~/.hermes/.env`. A
`curl` to `discord.com/api/v10/channels/.../messages` is within reach of
every agent that can run a shell command. The tool gate is one `os.environ`
read away from nonexistent.

### Can Commit?

ALL profiles have `terminal` + `file`. Any agent can `git add`, `git commit`,
and write to the repository. There is no per-profile git restriction.

### Can Order?

No profile has a broker API, exchange SDK, or order-routing tool listed.
However:

- **Coder** has `coding` tool — can generate and write order-placement code
  into the codebase. If that code is then executed by any other agent (or
  by a cron job), it becomes an order path.
- All profiles have `terminal` — can execute any script already on disk,
  including scripts that import and invoke broker SDKs if they exist.
- `scripts/hyperliquid/connection_test.py` already imports the Hyperliquid
  SDK — no agent is explicitly blocked from modifying or running it.

The order path is gated by code review (Coder → Orchestrator → human), not
by a soul-level prohibition. No soul says "I cannot place an order."

---

## Soul Gap Analysis

Every profile was checked for four safety constraints. None has all four.

### Key

- ✅ = present and explicit
- ⚠️ = partial or implied
- ❌ = absent

| Profile | Owner | Bans list | Paper-only | Hostile-R-is-scoreboard |
|---|---|---|---|---|
| Orchestrator | ❌ | ❌ | ⚠️ "Never executes trades directly" | ❌ |
| Architect | ❌ | ❌ | ❌ | ❌ |
| Coder | ❌ | ❌ | ⚠️ PAPER_MODE default but can flip | ❌ |
| Risk Guardian | ❌ | ❌ | ⚠️ Veto on live, but no hard paper-only | ❌ |
| Product Owner | ❌ | ❌ | ❌ | ❌ |
| Researcher | ❌ | ❌ | ⚠️ "Do not recommend live trades" | ❌ |
| Backtester | ❌ | ❌ | ⚠️ "Cannot recommend live deployment" | ❌ |
| Documenter | ❌ | ❌ | ❌ | ❌ |

### Specific gaps

**Owner** — No soul names who is responsible for the agent or who may modify
its constraints. A soul edit by any agent with `file` access can silently
remove safety rules.

**Bans list** — No soul explicitly prohibits: editing `trades.csv`, posting
to Discord, calling broker APIs, reading `.env`, flipping `PAPER_MODE`,
touching STR-Q files, writing to `hostile_fill_report_strq.jsonl`, or
modifying `_SCANNER_ALIASES`. The ban on touching hostile files and STR-Q
exists only in this agent's **session state** (Memory + LU instructions),
not in any profile soul.

**Paper-only** — Coder has `PAPER_MODE` as a default env flag, but it is an
environment variable check — not a soul-level prohibition. If `PAPER_MODE`
is unset or set to `false`, the code path exists. Risk Guardian has veto
power but can be bypassed if code changes are made without its review.
Backtester and Researcher have "cannot recommend live" but that is a
recommendation constraint, not an execution block.

**Hostile-R-is-the-scoreboard** — No soul references `hostile_fill_report_strq.jsonl`
or states that the hostile fill series is the authoritative tradability
reference. The frozen scoreboard (Paper +1305R vs Hostile -104R) exists only
in LU documentation and the active agent's Memory — not in any profile soul.

---

## Profiles That Should NOT Get a Soul

Per the user directive:

- **Crons do not get a soul.** The 9 scheduled cron jobs run as simple
  processes; they have no persistent identity or session memory.
- **Jev does not get a soul.** Jev is a classification sidecar with a single
  API endpoint (see LU-04). It classifies; it does not decide.

---

## Invariants

- **Do NOT rewrite** any soul file.
- **Do NOT post. Do NOT order.**
- **Do NOT un-kill STR-Q.**
- Soul gaps are documented but not fixed in this story.

---

## Verified

```bash
$ ls 01-Agents/Profiles/
Architect.md    Coder.md        Documenter.md   Orchestrator.md
Product-Owner.md  Researcher.md   Risk-Guardian.md  Backtester.md
```

8 profiles, all read and checked.

---

## Key Takeaway

No profile has an explicit post/order tool, but all have `terminal` + `file`
— meaning any agent can commit code and potentially curl to Discord with the
env token. The soul safety constraints (owner, bans list, paper-only,
hostile-R-is-the-scoreboard) are absent from all 8 profiles. The bans that
protect STR-Q and hostile fill files exist only in this agent's session
state, not in any persistent soul.