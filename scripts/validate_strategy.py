#!/usr/bin/env python3
"""
Strategy Validator for HermesForge vault.

Checks that every strategy note:
  1. Has required frontmatter fields (id, type, status, asset_class, trade_style,
     timeframe, confidence, evidence_links, last_reviewed)
  2. Contains ≥1 wikilink in ## Supporting Evidence pointing to an existing vault note
  3. Has all required sections present
  4. Is in the correct folder (Active/ Hypotheses/ Deprecated/)

Usage:
    python3 validate_strategy.py                       # validate all strategies
    python3 validate_strategy.py --file path/to/STR.md # single file
    python3 validate_strategy.py --fix                 # attempt auto-fix of minor issues
    python3 validate_strategy.py --report /tmp/r.json  # write JSON report
"""

import sys, re, json, argparse
from pathlib import Path
from datetime import date

VAULT_ROOT      = Path('/root/HermesForge')
STRATEGIES_DIR  = VAULT_ROOT / '06-Strategies'
STRATEGY_DIRS   = [
    STRATEGIES_DIR / 'Active',
    STRATEGIES_DIR / 'Hypotheses',
    STRATEGIES_DIR / 'Deprecated',
]

REQUIRED_FM_FIELDS = [
    'id', 'type', 'status', 'asset_class', 'trade_style',
    'timeframe', 'confidence', 'last_reviewed',
]

REQUIRED_SECTIONS = [
    '## Thesis',
    '## Entry Criteria',
    '## Exit Criteria',
    '## Risk Rules Applied',
    '## Supporting Evidence',
    '## Counter-Evidence',
    '## Change Log',
]

VALID_STATUSES  = {'hypothesis', 'tested', 'validated', 'deprecated'}
VALID_STYLES    = {'swing', 'position', 'day', 'scalp'}
VALID_CLASSES   = {'stocks', 'crypto', 'options', 'futures', 'forex', 'mixed'}
VALID_TF        = {'1m', '5m', '15m', '1h', '4h', 'daily', 'weekly', 'monthly', 'multi'}
VALID_CONF      = {'low', 'medium', 'high', 'validated'}


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return (fm_dict, body). fm_dict is empty if no frontmatter."""
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.DOTALL)
    if not m:
        return {}, text
    raw = m.group(1)
    body = text[m.end():]
    fm = {}
    for line in raw.splitlines():
        kv = re.match(r'^(\w[\w_-]*):\s*(.*)', line)
        if kv:
            fm[kv.group(1)] = kv.group(2).strip()
    return fm, body


def collect_vault_note_stems() -> set[str]:
    """Return set of all vault note stems (filename without .md) for wikilink validation."""
    stems = set()
    for d in [VAULT_ROOT / '08-Knowledge', VAULT_ROOT / '07-Risk',
              VAULT_ROOT / '06-Strategies', VAULT_ROOT / '03-ADRs']:
        if d.exists():
            for f in d.rglob('*.md'):
                stems.add(f.stem)
    return stems


def extract_wikilinks(text: str) -> list[str]:
    """Extract [[target]] and [[target|alias]] wikilinks from text."""
    raw = re.findall(r'\[\[([^\]]+)\]\]', text)
    links = []
    for r in raw:
        target = r.split('|')[0].strip()
        if target:
            links.append(target)
    return links


def extract_section(body: str, heading: str) -> str:
    """Extract text of a section from body."""
    pattern = re.compile(
        rf'^{re.escape(heading)}\s*\n(.*?)(?=\n## |\Z)',
        re.MULTILINE | re.DOTALL
    )
    m = pattern.search(body)
    return m.group(1).strip() if m else ''


def validate_file(path: Path, vault_stems: set[str]) -> dict:
    """Validate a single strategy file. Returns a result dict."""
    errors = []
    warnings = []

    try:
        text = path.read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return {'file': str(path), 'status': 'error', 'errors': [str(e)], 'warnings': []}

    fm, body = parse_frontmatter(text)

    # ── Frontmatter checks ────────────────────────────────────────────────────
    if not fm:
        errors.append('Missing frontmatter block entirely')
    else:
        # Required fields
        for field in REQUIRED_FM_FIELDS:
            if field not in fm:
                errors.append(f'Missing required frontmatter field: {field}')

        # type must be 'strategy'
        if fm.get('type', '') != 'strategy':
            errors.append(f"type must be 'strategy', got: '{fm.get('type','')}'")

        # Enum validations
        status = fm.get('status', '')
        if status and status not in VALID_STATUSES:
            errors.append(f"Invalid status '{status}'. Must be one of: {VALID_STATUSES}")

        trade_style = fm.get('trade_style', '')
        if trade_style and trade_style not in VALID_STYLES:
            warnings.append(f"Unusual trade_style '{trade_style}'. Expected: {VALID_STYLES}")

        asset_class = fm.get('asset_class', '')
        if asset_class and asset_class not in VALID_CLASSES:
            warnings.append(f"Unusual asset_class '{asset_class}'. Expected: {VALID_CLASSES}")

        confidence = fm.get('confidence', '')
        if confidence and confidence not in VALID_CONF:
            warnings.append(f"Unusual confidence '{confidence}'. Expected: {VALID_CONF}")

        # last_reviewed — must be a valid date
        lr = fm.get('last_reviewed', '')
        if lr:
            try:
                date.fromisoformat(lr)
            except ValueError:
                errors.append(f"last_reviewed must be ISO date (YYYY-MM-DD), got: '{lr}'")

    # ── Required sections ────────────────────────────────────────────────────
    for section in REQUIRED_SECTIONS:
        if section not in body:
            errors.append(f'Missing required section: {section}')

    # ── Supporting Evidence: requires ≥1 valid wikilink ──────────────────────
    evidence_text = extract_section(body, '## Supporting Evidence')
    if not evidence_text:
        errors.append('## Supporting Evidence section is empty')
    else:
        ev_links = extract_wikilinks(evidence_text)
        # Filter out empty placeholder links [[]]
        real_links = [lnk for lnk in ev_links if lnk and lnk != '']
        if not real_links:
            errors.append('## Supporting Evidence has no wikilinks — must link to ≥1 vault note')
        else:
            # Check each link resolves to an existing note
            broken = []
            for lnk in real_links:
                stem = lnk.split('#')[0].strip()  # strip anchor
                if stem and stem not in vault_stems:
                    broken.append(lnk)
            if broken:
                errors.append(f'Broken wikilinks in Supporting Evidence (note not found): {broken}')

    # ── Folder check ─────────────────────────────────────────────────────────
    expected_status = fm.get('status', '') if fm else ''
    parent = path.parent.name
    if expected_status == 'deprecated' and parent != 'Deprecated':
        warnings.append(f"Strategy is deprecated but lives in '{parent}/', should be in Deprecated/")
    elif expected_status in ('hypothesis',) and parent not in ('Hypotheses', 'Active'):
        warnings.append(f"Strategy status is '{expected_status}' but lives in '{parent}/'")

    # ── Determine pass/fail ──────────────────────────────────────────────────
    status = 'pass' if not errors else 'fail'

    return {
        'file': str(path),
        'name': path.stem,
        'status': status,
        'errors': errors,
        'warnings': warnings,
        'evidence_link_count': len([lnk for lnk in extract_wikilinks(
            extract_section(body, '## Supporting Evidence')
        ) if lnk]),
    }


def collect_files(args) -> list[Path]:
    if args.file:
        return [Path(args.file)]
    files = []
    for d in STRATEGY_DIRS:
        if d.exists():
            files.extend(d.glob('*.md'))
    return files


def auto_fix(path: Path, result: dict) -> list[str]:
    """Attempt to fix minor issues automatically. Returns list of fixes applied."""
    fixes = []
    text = path.read_text(encoding='utf-8', errors='replace')
    fm, body = parse_frontmatter(text)
    changed = False

    # Fix missing last_reviewed
    if fm and 'last_reviewed' not in fm:
        today = date.today().isoformat()
        # Insert before closing ---
        text = re.sub(
            r'(\n---\n)',
            f'\nlast_reviewed: {today}\n---\n',
            text, count=1
        )
        fixes.append(f'Added last_reviewed: {today}')
        changed = True

    if changed:
        path.write_text(text)

    return fixes


def main():
    ap = argparse.ArgumentParser(description='Validate HermesForge strategy notes')
    ap.add_argument('--file', default='', help='Validate a single file')
    ap.add_argument('--fix', action='store_true', help='Auto-fix minor issues')
    ap.add_argument('--report', default='', help='Write JSON report to path')
    args = ap.parse_args()

    files = collect_files(args)
    if not files:
        print("No strategy files found.")
        return

    print(f"Validating {len(files)} strategy file(s)...")
    vault_stems = collect_vault_note_stems()

    results = []
    passed = failed = 0

    for path in files:
        r = validate_file(path, vault_stems)

        if args.fix and r['status'] == 'fail':
            fixes = auto_fix(path, r)
            if fixes:
                # Re-validate after fix
                r = validate_file(path, vault_stems)
                r['auto_fixed'] = fixes

        results.append(r)
        icon = '✅' if r['status'] == 'pass' else '❌'
        print(f"\n{icon} {path.name}")
        if r['errors']:
            for e in r['errors']:
                print(f"   ERROR: {e}")
        if r['warnings']:
            for w in r['warnings']:
                print(f"   WARN:  {w}")
        if r.get('auto_fixed'):
            for f in r['auto_fixed']:
                print(f"   FIXED: {f}")
        if r['status'] == 'pass':
            passed += 1
            print(f"   Evidence links: {r['evidence_link_count']}")
        else:
            failed += 1

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")

    if args.report:
        Path(args.report).write_text(json.dumps(results, indent=2))
        print(f"Report written to {args.report}")

    sys.exit(0 if failed == 0 else 1)


if __name__ == '__main__':
    main()
