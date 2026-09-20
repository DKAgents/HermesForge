---
id: US-153
type: user_story
status: backlog
epic: EPIC-014-Tech-Debt
priority: high
created: 2026-09-20
tags: [security, plugins, scanning]
---

# US-153: Plugin install blocked by noisy scan

**As a** operator installing a catalog-listed community plugin on a headless VPS,
**I want** the install scanner to treat test fixtures and documented command lists as non-blocking or separately classified,
**so that** a DANGEROUS verdict is reserved for real install-time risk and `--force` is not my only (and currently invalid) escape hatch.

## Acceptance Criteria

1. Findings in `tests/` do not raise CRITICAL destructive by themselves
2. A static list of command names in plugin source (`uname`, `printenv`, etc.) is not scored as HIGH exfiltration unless those commands are executed with secrets
3. Catalog-pinned SHAs that already passed admission either install, or fail with a reviewable caution prompt — not an unoverrideable DANGEROUS block caused by tests
4. `plugins.scan_on_install: false` is not required to install a reviewed pin
5. The CLI still hard-blocks true destructive/exfil patterns outside tests

## Context

Test fixtures: `tests/test_patch_0212.py:168`
Gate logic: `gate.py:43`
Current behavior: `--force does not override a dangerous verdict`