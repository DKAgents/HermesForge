---
type: user-story
epic: EPIC-017
priority: P0
status: backlog
created: 2026-11-02
owner: coder
tags: [ops, python, dependency, drift]
---

# US-193 — Collapse to a single Python environment for cron wrappers

## Description
Interpreter drift (4 Pythons: system / tools / Forge venv / resolve_python target) causes `ModuleNotFoundError` in `.sh` wrappers. Collapse all cron wrappers to one interpreter with the full trading dep set.

## Acceptance Criteria
- All cron `.sh` wrappers resolve the same interpreter, provisioned with the full trading dep set (pandas/numpy/scipy/mplfinance/sklearn/yfinance + vault ML stack).
- A `python3 -c "import pandas, numpy, sklearn, yfinance"` succeeds under the exact interpreter every cron uses.
- Documented the single source-of-truth interpreter in the pipeline-health skill.

## Owner / RACI
- Owner (A): coder · Responsible (R): coder · Consulted (C): risk-guardian · Informed (I): orchestrator