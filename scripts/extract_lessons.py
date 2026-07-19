#!/usr/bin/env python3
"""
HermesForge Lesson Extractor — Self-Improvement Feedback Loop
==============================================================
Takes trading activity (backtest results, paper trade logs, free-text analysis)
and extracts structured lessons that are written back into the vault.

Pipeline:
  1. Parse input (JSON backtest result, JSON trade log, or free-text)
  2. Call T2 LLM to extract a structured lesson conforming to the Lesson schema
  3. Resolve wikilinks against existing vault notes
  4. Write lesson note to 09-Journal/Lessons/YYYY-MM/
  5. If outcome is contradicts/refines → write pending-update for related strategy
  6. If outcome is confirms → increment confirmation_count on related vault notes
  7. Update lesson-seeds.yaml for the Discovery Engine (AC9)

Usage:
    python3 extract_lessons.py --input trade_log.json
    python3 extract_lessons.py --input "AAPL broke out on 2× volume but reversed — volume filter would have prevented entry"
    python3 extract_lessons.py --input trade_log.json --dry-run
    python3 extract_lessons.py --input trade_log.json --strategy STR-20260719-breakout-volume-trend
"""

import sys, os, re, json, argparse, hashlib
from pathlib import Path
from datetime import datetime, timezone

# Load .env so OPENROUTER_API_KEY is available
_env_file = Path.home() / '.hermes' / '.env'
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith('#') and '=' in _line:
            _k, _v = _line.split('=', 1)
            if _k.strip() and _k.strip() not in os.environ:
                os.environ[_k.strip()] = _v.strip()

VAULT_ROOT      = Path('/root/HermesForge')
SCRIPTS_DIR     = VAULT_ROOT / 'scripts'
LESSONS_DIR     = VAULT_ROOT / '09-Journal' / 'Lessons'
STRATEGIES_DIR  = VAULT_ROOT / '06-Strategies'
PENDING_DIR     = STRATEGIES_DIR / 'Pending-Updates'
KNOWLEDGE_DIR   = VAULT_ROOT / '08-Knowledge'
LESSON_SEEDS    = SCRIPTS_DIR / 'lesson_seeds.yaml'

OPENROUTER_URL  = 'https://openrouter.ai/api/v1/chat/completions'
LLM_MODEL       = 'anthropic/claude-sonnet-4.6'
MAX_TOKENS      = 1500
VALID_SOURCES   = {'backtest', 'paper-trade', 'analysis', 'live-trade', 'observation'}
VALID_OUTCOMES  = {'confirms', 'contradicts', 'refines', 'new-finding'}
VALID_CONF      = {'low', 'medium', 'high'}

CONFIRMATION_THRESHOLD = 3   # confidence → validated after this many confirmations


# ── LLM call ─────────────────────────────────────────────────────────────────

def llm_call(messages: list[dict], max_tokens: int = MAX_TOKENS) -> str:
    import urllib.request
    api_key = os.environ.get('OPENROUTER_API_KEY', '')
    payload = json.dumps({
        'model': LLM_MODEL,
        'messages': messages,
        'max_tokens': max_tokens,
    }).encode()
    req = urllib.request.Request(
        OPENROUTER_URL,
        data=payload,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
            return data['choices'][0]['message']['content']
    except Exception as e:
        return f'ERROR: {e}'


# ── vault note helpers ────────────────────────────────────────────────────────

def collect_vault_stems() -> dict[str, Path]:
    """Return dict of {stem: path} for all vault notes."""
    stems = {}
    for d in [KNOWLEDGE_DIR, VAULT_ROOT / '07-Risk', VAULT_ROOT / '06-Strategies',
              VAULT_ROOT / '03-ADRs']:
        if d.exists():
            for f in d.rglob('*.md'):
                stems[f.stem] = f
    return stems


def collect_strategy_stems() -> dict[str, Path]:
    """Return dict of {stem: path} for strategy notes only."""
    stems = {}
    for sd in [STRATEGIES_DIR / 'Active', STRATEGIES_DIR / 'Hypotheses']:
        if sd.exists():
            for f in sd.glob('*.md'):
                stems[f.stem] = f
    return stems


def read_frontmatter(path: Path) -> dict:
    """Parse frontmatter from a note. Returns dict."""
    try:
        text = path.read_text(encoding='utf-8', errors='replace')
        m = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.DOTALL)
        if not m:
            return {}
        fm = {}
        for line in m.group(1).splitlines():
            kv = re.match(r'^(\w[\w_-]*):\s*(.*)', line)
            if kv:
                fm[kv.group(1)] = kv.group(2).strip()
        return fm
    except Exception:
        return {}


def patch_frontmatter_field(path: Path, field: str, value) -> bool:
    """Update or add a single frontmatter field in a note. Returns True if changed."""
    try:
        text = path.read_text(encoding='utf-8', errors='replace')
        m = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.DOTALL)
        if not m:
            return False
        fm_raw = m.group(1)
        rest = text[m.end():]
        val_str = str(value)

        # Update existing field
        if re.search(rf'^{re.escape(field)}:', fm_raw, re.MULTILINE):
            fm_raw = re.sub(
                rf'^{re.escape(field)}:.*$',
                f'{field}: {val_str}',
                fm_raw, flags=re.MULTILINE
            )
        else:
            fm_raw = fm_raw + f'\n{field}: {val_str}'

        path.write_text(f'---\n{fm_raw}\n---\n{rest}')
        return True
    except Exception:
        return False


# ── input normaliser ──────────────────────────────────────────────────────────

def load_input(raw: str) -> str:
    """Load input: path to JSON file, JSON string, or free text."""
    # Try as file path
    p = Path(raw)
    if p.exists():
        content = p.read_text(encoding='utf-8', errors='replace')
        # Try to parse as JSON for pretty display
        try:
            data = json.loads(content)
            return json.dumps(data, indent=2)
        except Exception:
            return content

    # Try inline JSON
    try:
        data = json.loads(raw)
        return json.dumps(data, indent=2)
    except Exception:
        pass

    # Plain text / free-text
    return raw


# ── LLM extraction prompt ─────────────────────────────────────────────────────

EXTRACTION_PROMPT = """You are a systematic trading journal analyst. Your job is to extract a structured lesson from a trading event or analysis.

INPUT (trade log, backtest result, or free-text observation):
{input_text}

STRATEGY CONTEXT (if known):
{strategy_context}

VAULT NOTES AVAILABLE FOR LINKING (stems only — use these for wikilinks):
{available_stems}

Extract a lesson and respond in STRICT JSON format (no markdown, no text outside the JSON):

{{
  "title": "Short title for the lesson (max 10 words, starts with a verb or noun)",
  "source": "one of: backtest | paper-trade | analysis | live-trade | observation",
  "outcome": "one of: confirms | contradicts | refines | new-finding",
  "confidence": "one of: low | medium | high",
  "what_happened": "2-3 sentences: objective description of the trading event. Include specifics (ticker, price, date if available).",
  "what_was_expected": "1-2 sentences: what the strategy or vault rule predicted. Reference specific rules if possible.",
  "what_was_learned": "2-3 sentences: the actionable insight. Be specific — what should change in future behavior?",
  "vault_updates": ["list of vault note stems that should have confirmation_count incremented or be reviewed"],
  "related_strategy_stems": ["list of strategy note stems (e.g. STR-20260719-breakout-volume-trend) this lesson applies to"],
  "related_note_stems": ["list of vault note stems (from the available list) that are directly relevant"]
}}

Rules:
- outcome=confirms: the event validated a vault rule or strategy as expected
- outcome=contradicts: the event showed a rule or strategy failed in a specific condition
- outcome=refines: the event revealed a missing condition or nuance in an existing rule
- outcome=new-finding: the event revealed something not yet in the vault at all
- Only include stems that genuinely exist in the available list — do not invent stems
- Keep all text fields concise and specific"""


# ── lesson writer ─────────────────────────────────────────────────────────────

def write_lesson(lesson: dict, dry_run: bool) -> str:
    """Write a lesson note to vault. Returns path."""
    today = datetime.now(timezone.utc)
    month_dir = LESSONS_DIR / today.strftime('%Y-%m')
    month_dir.mkdir(parents=True, exist_ok=True)

    date_str = today.strftime('%Y-%m-%d')
    slug = re.sub(r'[^a-z0-9]+', '-', lesson['title'].lower()).strip('-')[:50]
    uid = hashlib.md5(f"{date_str}-{slug}".encode()).hexdigest()[:6]
    fname = month_dir / f'LSN-{date_str}-{slug}-{uid}.md'

    strat_links = '\n'.join(
        f'- [[{s}]] — outcome: {lesson["outcome"]}'
        for s in lesson.get('related_strategy_stems', [])
    ) or '- _none identified_'

    note_links = '\n'.join(
        f'- [[{n}]]'
        for n in lesson.get('related_note_stems', [])
    ) or '- _none identified_'

    vault_update_items = '\n'.join(
        f'- [ ] [[{v}]] — confirmation_count incremented'
        for v in lesson.get('vault_updates', [])
    ) or '- _none_'

    content = f"""---
id: LSN-{date_str}-{uid}
type: lesson
source: {lesson.get('source', 'analysis')}
outcome: {lesson.get('outcome', 'new-finding')}
related_strategy: {json.dumps(lesson.get('related_strategy_stems', []))}
related_notes: {json.dumps(lesson.get('related_note_stems', []))}
date: {date_str}
confidence: {lesson.get('confidence', 'medium')}
confirmation_count: 0
tags: [lesson, feedback-loop, {lesson.get('outcome', 'new-finding')}]
---

# {lesson['title']}

## What Happened

{lesson.get('what_happened', '_Not provided._')}

## What Was Expected

{lesson.get('what_was_expected', '_Not provided._')}

## What Was Learned

{lesson.get('what_was_learned', '_Not provided._')}

## Vault Updates Triggered

{vault_update_items}

## Related Strategy

{strat_links}

## Related Notes

{note_links}

## Change Log

| Date | Action | Detail |
|------|--------|--------|
| {date_str} | Lesson created | Extracted by extract_lessons.py |
"""
    if not dry_run:
        fname.write_text(content)
    return str(fname)


# ── strategy pending update ───────────────────────────────────────────────────

def write_strategy_pending_update(lesson: dict, lesson_path: str, strategy_stems: dict[str, Path], dry_run: bool) -> list[str]:
    """Write pending-update notes for strategies affected by contradicts/refines lessons."""
    if lesson.get('outcome') not in ('contradicts', 'refines'):
        return []

    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

    for stem in lesson.get('related_strategy_stems', []):
        if stem not in strategy_stems:
            continue
        slug = re.sub(r'[^a-z0-9]+', '-', lesson['title'].lower()).strip('-')[:40]
        update_file = PENDING_DIR / f'UPDATE-{today}-{stem}-lesson-{slug}.md'

        outcome_verb = 'contradicts' if lesson['outcome'] == 'contradicts' else 'refines'
        content = f"""---
type: strategy-update-suggestion
strategy: {stem}
lesson: {Path(lesson_path).stem}
outcome: {lesson['outcome']}
date: {today}
reviewed: false
tags: [pending-update, strategy, feedback-loop]
---

# Pending Update: {stem}

## Triggering Lesson

[[{Path(lesson_path).stem}]] — *{lesson['title']}*

**Outcome:** This lesson **{outcome_verb}** the strategy.

## What Was Learned

{lesson.get('what_was_learned', '')}

## Suggested Action

Review [[{stem}]] and consider:
- Does the `## Entry Criteria` need a new condition or filter?
- Does the `## Counter-Evidence` section need updating?
- Should a new note be added to `## Supporting Evidence`?

Update the strategy's `## Change Log` after making any changes.
Mark `reviewed: true` in this file's frontmatter once resolved.
"""
        if not dry_run:
            update_file.write_text(content)
        written.append(str(update_file))
        print(f"    → Pending update written for {stem} ({lesson['outcome']})")

    return written


# ── confirmation_count updater ────────────────────────────────────────────────

def update_confirmation_counts(lesson: dict, vault_stems: dict[str, Path], dry_run: bool) -> list[str]:
    """Increment confirmation_count on confirmed vault notes. Returns list of updated paths."""
    if lesson.get('outcome') != 'confirms':
        return []

    updated = []
    for stem in lesson.get('vault_updates', []):
        if stem not in vault_stems:
            print(f"    → Note not found for confirmation: {stem}")
            continue
        path = vault_stems[stem]
        fm = read_frontmatter(path)
        current = int(fm.get('confirmation_count', '0') or 0)
        new_count = current + 1
        print(f"    → {stem}: confirmation_count {current} → {new_count}")

        if not dry_run:
            patch_frontmatter_field(path, 'confirmation_count', new_count)
            # Promote to validated if threshold reached
            if new_count >= CONFIRMATION_THRESHOLD:
                current_conf = fm.get('confidence', 'high')
                if current_conf != 'validated':
                    patch_frontmatter_field(path, 'confidence', 'validated')
                    print(f"    ✅ {stem}: promoted to confidence: validated")
        updated.append(stem)
    return updated


# ── lesson seeds for discovery engine (AC9) ───────────────────────────────────

def update_lesson_seeds(lesson: dict, lesson_path: str, dry_run: bool):
    """Append lesson-derived seed to lesson_seeds.yaml for the Discovery Engine."""
    try:
        import yaml
    except ImportError:
        return

    existing = []
    if LESSON_SEEDS.exists():
        data = yaml.safe_load(LESSON_SEEDS.read_text()) or {}
        existing = data.get('lesson_seeds', [])

    # Only add if outcome is contradicts or new-finding (high signal)
    if lesson.get('outcome') not in ('contradicts', 'new-finding', 'refines'):
        return

    new_seed = {
        'id': f"lesson-{Path(lesson_path).stem[-8:]}",
        'query': lesson['title'] + ' ' + lesson.get('what_was_learned', '')[:100],
        'domains': ['rules', 'risk'],
        'priority': 'high' if lesson['outcome'] == 'contradicts' else 'medium',
        'description': f"Lesson-derived seed ({lesson['outcome']}): {lesson.get('what_was_learned', '')[:150]}",
        'source_lesson': Path(lesson_path).stem,
    }

    # Avoid duplicates
    existing_ids = {s.get('id') for s in existing}
    if new_seed['id'] not in existing_ids:
        existing.append(new_seed)
        if not dry_run:
            LESSON_SEEDS.write_text(yaml.dump({'lesson_seeds': existing}, default_flow_style=False, allow_unicode=True))
        print(f"    → Lesson seed added to {LESSON_SEEDS.name}")


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description='Extract lessons from trading activity')
    ap.add_argument('--input', required=True,
                    help='Path to JSON file, JSON string, or free-text description')
    ap.add_argument('--strategy', default='',
                    help='Known strategy stem to associate (optional, improves extraction)')
    ap.add_argument('--dry-run', action='store_true',
                    help='Show extraction results without writing to vault')
    ap.add_argument('--report', default='', help='Write JSON result to path')
    args = ap.parse_args()

    print(f"\n{'='*60}")
    print(f"  HermesForge Lesson Extractor")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"  dry_run={args.dry_run}")
    print(f"{'='*60}\n")

    # Load input
    raw_input = load_input(args.input)
    print(f"Input loaded ({len(raw_input)} chars)")

    # Collect vault context
    vault_stems = collect_vault_stems()
    strategy_stems = collect_strategy_stems()

    # Strategy context
    strategy_context = '_None specified_'
    if args.strategy and args.strategy in strategy_stems:
        strat_text = strategy_stems[args.strategy].read_text(encoding='utf-8', errors='replace')
        strategy_context = strat_text[:1500]  # cap for prompt size
    elif args.strategy:
        strategy_context = f'Strategy "{args.strategy}" not found in vault'

    # Build a representative sample of available stems (cap for prompt size)
    # Include strategies + sample of Murphy rules/indicators/patterns
    key_stems = list(strategy_stems.keys())
    murphy_stems = [s for s in vault_stems if s.startswith(('R0', 'EN', 'EX', 'RG', 'N0', 'N1',
                                                              'N2', 'P0', 'E0', 'C0', 'C1', 'C2'))][:80]
    insight_stems = [s for s in vault_stems if s.startswith('INS-')]
    available_stems_list = key_stems + murphy_stems + insight_stems
    available_stems_str = '\n'.join(available_stems_list[:120])

    # Call LLM
    print("Calling LLM for lesson extraction...")
    prompt = EXTRACTION_PROMPT.format(
        input_text=raw_input[:2000],
        strategy_context=strategy_context[:800],
        available_stems=available_stems_str,
    )
    response = llm_call([{'role': 'user', 'content': prompt}])

    if response.startswith('ERROR:'):
        print(f"✗ LLM error: {response}")
        sys.exit(1)

    # Parse JSON
    try:
        raw = re.sub(r'^```(?:json)?\s*', '', response.strip(), flags=re.MULTILINE)
        raw = re.sub(r'\s*```$', '', raw.strip(), flags=re.MULTILINE)
        lesson = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"✗ JSON parse error: {e}")
        print(f"Response: {response[:400]}")
        sys.exit(1)

    print(f"\nLesson extracted:")
    print(f"  Title    : {lesson.get('title', '?')}")
    print(f"  Outcome  : {lesson.get('outcome', '?')}")
    print(f"  Source   : {lesson.get('source', '?')}")
    print(f"  Confidence: {lesson.get('confidence', '?')}")
    if lesson.get('related_strategy_stems'):
        print(f"  Strategies: {lesson['related_strategy_stems']}")
    if lesson.get('vault_updates'):
        print(f"  Vault updates: {lesson['vault_updates']}")

    # Validate stems — filter out any hallucinated stems
    all_known = set(vault_stems.keys()) | set(strategy_stems.keys())
    lesson['related_strategy_stems'] = [s for s in lesson.get('related_strategy_stems', []) if s in all_known]
    lesson['related_note_stems'] = [s for s in lesson.get('related_note_stems', []) if s in all_known]
    lesson['vault_updates'] = [s for s in lesson.get('vault_updates', []) if s in all_known]

    # Write lesson note
    print("\nWriting lesson note...")
    lesson_path = write_lesson(lesson, args.dry_run)
    print(f"  ✅ Lesson: {Path(lesson_path).name}")

    # Strategy pending updates
    if lesson.get('outcome') in ('contradicts', 'refines'):
        print("\nPropagating to strategy pending-updates...")
        write_strategy_pending_update(lesson, lesson_path, strategy_stems, args.dry_run)

    # Confirmation counts
    if lesson.get('outcome') == 'confirms':
        print("\nUpdating confirmation counts...")
        updated = update_confirmation_counts(lesson, vault_stems, args.dry_run)
        if not updated:
            print("  (no vault notes matched for confirmation)")

    # Update lesson seeds for Discovery Engine
    update_lesson_seeds(lesson, lesson_path, args.dry_run)

    result = {
        'lesson_path': lesson_path,
        'title': lesson.get('title'),
        'outcome': lesson.get('outcome'),
        'strategy_updates': lesson.get('related_strategy_stems', []),
        'confirmation_updates': lesson.get('vault_updates', []) if lesson.get('outcome') == 'confirms' else [],
    }

    if args.report:
        Path(args.report).write_text(json.dumps(result, indent=2))

    print(f"\n{'='*60}")
    print(f"✅ Lesson extraction complete")
    print(f"   Path: {lesson_path}")
    print(f"{'='*60}\n")

    return result


if __name__ == '__main__':
    main()
