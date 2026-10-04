---
id: US-157
type: user_story
status: done
epic: EPIC-014-Tech-Debt
priority: high
created: 2026-10-04
updated: 2026-10-04
tags: [bug, jev, security, fix]
---

# US-157: JevClient._load_api_key dead file-read path (unconditional return None)

## Story
**As a** HermesForge pipeline running in cron or execute_code (no shell env),
**I want** JevClient to load TYPESAFE_API_KEY from ~/.hermes/.env,
**So that** JEV works without requiring the key to be exported in the shell environment.

## Root Cause
`scripts/gauntlet/jev_client.py` line 41: `return None` should be `return key`.

The `_load_api_key()` function reads `os.environ` correctly (early return), but the
file-read fallback loop assigns `key` on line 40 and then falls through to `return None`
on line 41 — unconditionally discarding the loaded key.

```python
# Before (broken):
def _load_api_key():
    key = os.environ.get("TYPESAFE_API_KEY")  # works
    if key:
        return key
    # ... reads .env, assigns key ...
        key = line.split("=", 1)[1].strip().strip('"').strip("'")
    return None  # <-- BUG: always None, ignores loaded key

# After (fixed):
    ...
    return key  # returns loaded key or None if not found
```

## Impact
- JEV only worked when TYPESAFE_API_KEY was exported in shell env
- Cron jobs using JEV would fail silently (fail-closed: tier="rejected")
- execute_code kernels could not init JevClient
- Any process without the shell env would fail
- This bug is likely WHY the key was exported to shell in the first place (US-155 workaround)

## Discovery
2026-10-04: while building the JEV browser research pipeline, noticed that
`JevClient()` worked in terminal but failed in execute_code. Traced to
`_load_api_key()` always returning None from the file path.

## Fix
One-word change: `return None` -> `return key` (line 41).
Applied 2026-10-04. Verified: execute_code kernel now loads key from .env successfully.

## Commit Status
⚠ UNCOMMITTED — git commit blocked by approval timeout (2026-10-04 session).
Fix is applied to working tree but needs commit + push.

## Acceptance Criteria
- [x] _load_api_key() returns key from .env file when no env var set
- [x] JevClient() initializes in execute_code (no shell env) from .env
- [x] No behavior change when key IS in env (early return path unchanged)
- [ ] Git commit + push applied

## Related
- US-155: Secrets Not In History (TYPESAFE key echo'd in CLI shell — likely needed because of this bug)
- US-156: Jev stays out-of-process (architectural constraint — not affected)
- `scripts/gauntlet/jev_client.py`
- `campaigns/2026-09-aegis-rebuild/lu-04-jev.md` (JEV authority boundary)