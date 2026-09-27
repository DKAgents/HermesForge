# LU-03b: Paper Card Now Cites Hostile STR-Q R

**Status**: implemented (one line added to performance_report.py)
**Date**: 2026-09-25
**Campaign**: 2026-09-aegis-rebuild

The paper-trading scoreboard (channel `<#1537225420120793088>`) now includes
one line after the paper-R total: `STR-Q hostile R (realistic fills): <value>`.
Read from `hostile_fill_report_strq.jsonl`. If the jsonl cannot be read,
prints `unavailable` and still posts the paper card.