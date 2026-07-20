#!/usr/bin/env python3
"""
extract_lessons.py — HermesForge EPIC-010 (US-070)

Minimal lesson extractor for closed paper trades. US-053 originally
specified an LLM-based extraction pipeline; this script implements the
rule-based version needed to close the loop for paper trading specifically
(closed trade -> structured lesson note), since a full LLM-based extractor
for arbitrary free-text input did not exist and was out of scope to build
from scratch here. This satisfies US-070's acceptance criteria (verify
extract_lessons.py works for paper-trade input) without claiming to
satisfy every US-053 acceptance criterion (e.g. free-text analysis input
is not supported by this version).

Outcome classification heuristic (deterministic, not LLM-judged):
  - r_multiple >= +1.5 and quality_tier in ("A", "A (High)")  -> confirms
  - r_multiple <= -0.8 and quality_tier in ("A", "A (High)")  -> contradicts
    (a high-confidence signal that lost meaningfully is worth flagging)
  - otherwise -> refines (default; most trades are incremental data points,
    not confirming or contradicting proof points on their own)

Usage:
    python3 extract_lessons.py --test
    python3 extract_lessons.py --trade-id <trade_id>   # extract from trades.csv
"""

import sys
import re
import pathlib
import datetime
import hashlib

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import trade_log

VAULT_ROOT = pathlib.Path(__file__).parent.parent.parent
LESSONS_DIR = VAULT_ROOT / "09-Journal" / "Lessons"
PENDING_UPDATES_DIR = VAULT_ROOT / "06-Strategies" / "Pending-Updates"

CONFIRM_R_THRESHOLD = 1.5
CONTRADICT_R_THRESHOLD = -0.8
HIGH_TIER_LABELS = {"A", "A (High)"}


def classify_outcome(trade: dict) -> str:
    """Deterministic outcome classification -- see module docstring."""
    r = float(trade.get("r_multiple", 0) or 0)
    tier = trade.get("quality_tier", "")

    if r >= CONFIRM_R_THRESHOLD and tier in HIGH_TIER_LABELS:
        return "confirms"
    if r <= CONTRADICT_R_THRESHOLD and tier in HIGH_TIER_LABELS:
        return "contradicts"
    return "refines"


def _lesson_id(trade_id: str) -> str:
    date_str = datetime.date.today().isoformat()
    suffix = hashlib.sha256(trade_id.encode()).hexdigest()[:6]
    return f"LSN-{date_str}-{suffix}"


def _slugify(text: str, max_len: int = 60) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_len]


def build_lesson_note(trade: dict) -> tuple[str, str]:
    """Returns (filename, note_content) for a closed trade."""
    outcome = classify_outcome(trade)
    trade_id = trade["trade_id"]
    strategy_id = trade["strategy_id"]
    ticker = trade["ticker"]
    r_multiple = trade.get("r_multiple", "n/a")
    exit_reason = trade.get("exit_reason", "n/a")
    entry_date = trade.get("entry_date", "n/a")
    exit_date = trade.get("exit_date", "n/a")
    direction = trade.get("direction", "n/a")

    lesson_id = _lesson_id(trade_id)
    title = f"Paper Trade {outcome.title()}: {strategy_id} on {ticker}"
    slug = _slugify(f"{outcome}-{strategy_id}-{ticker}")
    filename = f"{lesson_id}-{slug}.md"

    what_happened = (
        f"Paper trade {trade_id} ({direction} {ticker}) entered {entry_date}, "
        f"exited {exit_date} via {exit_reason}. Result: {r_multiple}R."
    )

    if outcome == "confirms":
        what_learned = (
            f"This trade's outcome ({r_multiple}R) is consistent with the strategy's "
            f"documented edge at its stated quality tier. Adds one confirming data point; "
            f"does not yet constitute statistical proof (see US-081/082 for aggregate calibration)."
        )
    elif outcome == "contradicts":
        what_learned = (
            f"This was a high-confidence-tier signal that resulted in a meaningful loss "
            f"({r_multiple}R). One trade is not conclusive, but this is flagged for the "
            f"strategy's Pending-Updates review per US-084 -- if this pattern repeats, "
            f"the quality-tier logic or the strategy's entry criteria may need revision."
        )
    else:
        what_learned = (
            f"Outcome ({r_multiple}R via {exit_reason}) is within the range this strategy's "
            f"design would predict. No specific refinement identified from this single trade."
        )

    content = f"""---
id: {lesson_id}
type: lesson
source: paper-trade
outcome: {outcome}
related_strategy: ["{strategy_id}"]
related_notes: []
date: {datetime.date.today().isoformat()}
confidence: low
confirmation_count: 0
tags: [lesson, feedback-loop, paper-trading, {outcome}]
---
# {title}

## What Happened

{what_happened}

## What Was Expected

Per the strategy's documented thesis and quality-tier logic (quality_tier={trade.get('quality_tier', 'n/a')}, confirmation_level={trade.get('confirmation_level', 'n/a')}).

## What Was Learned

{what_learned}

## Vault Updates Triggered

- [ ] [[{strategy_id}]] — reviewed, outcome={outcome}

## Related Strategy

- [[{strategy_id}]] — outcome: {outcome}

## Related Notes

(none identified automatically -- rule-based extractor, not LLM-based; see module docstring)

## Change Log

| Date | Action | Detail |
|------|--------|--------|
| {datetime.date.today().isoformat()} | Lesson created | Extracted by extract_lessons.py (paper trade, rule-based) |
"""
    return filename, content


def write_lesson_note(trade: dict) -> pathlib.Path:
    filename, content = build_lesson_note(trade)
    month_dir = LESSONS_DIR / datetime.date.today().strftime("%Y-%m")
    month_dir.mkdir(parents=True, exist_ok=True)
    out_path = month_dir / filename
    out_path.write_text(content)
    return out_path


def flag_pending_update(trade: dict, lesson_path: pathlib.Path) -> pathlib.Path:
    """
    On a 'contradicts' outcome, write a Pending-Updates entry per the
    existing ADR-003/US-052 mechanism (US-084 wires this fully; this is
    the minimal version needed to satisfy US-070's acceptance criteria).
    """
    strategy_id = trade["strategy_id"]
    PENDING_UPDATES_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"UPDATE-{datetime.date.today().isoformat()}-{strategy_id}-contradicting-paper-trade.md"
    out_path = PENDING_UPDATES_DIR / filename
    content = f"""---
type: pending-update
strategy: {strategy_id}
trigger: contradicting-paper-trade
date: {datetime.date.today().isoformat()}
status: open
---
# Pending Update: {strategy_id}

Triggered by contradicting paper trade outcome. See [[{lesson_path.stem}]] for details.

Trade: {trade['trade_id']}, R-multiple: {trade.get('r_multiple')}, quality_tier: {trade.get('quality_tier')}

Review required: does this indicate the quality-tier logic or entry criteria need revision?
"""
    out_path.write_text(content)
    return out_path


def extract_from_trade_id(trade_id: str) -> dict:
    """Look up a closed trade by ID and extract a lesson."""
    rows = trade_log._read_all_rows()
    trade = next((r for r in rows if r["trade_id"] == trade_id), None)
    if trade is None:
        raise ValueError(f"trade_id not found: {trade_id}")
    if trade["status"] != "closed":
        raise ValueError(f"trade_id not closed yet: {trade_id}")

    lesson_path = write_lesson_note(trade)
    result = {"lesson_path": str(lesson_path), "outcome": classify_outcome(trade)}

    if result["outcome"] == "contradicts":
        pending_path = flag_pending_update(trade, lesson_path)
        result["pending_update_path"] = str(pending_path)

    return result


# ---------------------------------------------------------------------------
# Unit test
# ---------------------------------------------------------------------------

def _test():
    import tempfile

    orig_lessons_dir = LESSONS_DIR
    orig_pending_dir = PENDING_UPDATES_DIR
    tmp_root = pathlib.Path(tempfile.mkdtemp())
    globals()["LESSONS_DIR"] = tmp_root / "Lessons"
    globals()["PENDING_UPDATES_DIR"] = tmp_root / "Pending-Updates"

    try:
        # Confirming trade
        confirming_trade = {
            "trade_id": "STR-B-macd-histogram-divergence_NVDA_2026-07-20",
            "strategy_id": "STR-B-macd-histogram-divergence", "ticker": "NVDA",
            "direction": "short", "entry_date": "2026-07-20", "exit_date": "2026-07-25",
            "r_multiple": "3.0", "exit_reason": "target", "quality_tier": "A (High)",
            "confirmation_level": "Level 2",
        }
        assert classify_outcome(confirming_trade) == "confirms"
        path = write_lesson_note(confirming_trade)
        assert path.exists()
        assert "confirms" in path.read_text()
        print("✅ Confirming trade -> lesson note written correctly")

        # Contradicting trade
        contradicting_trade = {
            "trade_id": "STR-B-macd-histogram-divergence_AAPL_2026-07-20",
            "strategy_id": "STR-B-macd-histogram-divergence", "ticker": "AAPL",
            "direction": "long", "entry_date": "2026-07-20", "exit_date": "2026-07-22",
            "r_multiple": "-1.0", "exit_reason": "stop", "quality_tier": "A (High)",
            "confirmation_level": "Level 2",
        }
        assert classify_outcome(contradicting_trade) == "contradicts"
        lesson_path = write_lesson_note(contradicting_trade)
        pending_path = flag_pending_update(contradicting_trade, lesson_path)
        assert pending_path.exists()
        assert "contradicting" in pending_path.read_text().lower()
        print("✅ Contradicting trade -> lesson + Pending-Updates entry both written")

        # Refining (default) trade
        neutral_trade = {
            "trade_id": "STR-D-sr-role-reversal_SPY_2026-07-20",
            "strategy_id": "STR-D-sr-role-reversal", "ticker": "SPY",
            "direction": "long", "entry_date": "2026-07-20", "exit_date": "2026-07-22",
            "r_multiple": "0.3", "exit_reason": "time", "quality_tier": "B (Medium)",
        }
        assert classify_outcome(neutral_trade) == "refines"
        print("✅ Neutral trade -> refines (default) classification correct")

        print("\n✅ All extract_lessons.py unit tests passed")

    finally:
        globals()["LESSONS_DIR"] = orig_lessons_dir
        globals()["PENDING_UPDATES_DIR"] = orig_pending_dir


if __name__ == "__main__":
    if "--test" in sys.argv:
        _test()
    elif "--trade-id" in sys.argv:
        tid = sys.argv[sys.argv.index("--trade-id") + 1]
        result = extract_from_trade_id(tid)
        print(result)
    else:
        print(__doc__)
