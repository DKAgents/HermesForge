#!/usr/bin/env python3
"""
Enforce standard frontmatter on vault notes.

Scans notes and adds missing required fields with sensible defaults.
Logs every patch so you can review what was changed.

Required frontmatter fields:
    topic, confidence, has_quotes, tags, source

Usage:
    python3 check_frontmatter.py                    # scan all vault notes
    python3 check_frontmatter.py --scope new        # only notes in changed list (stdin, one path per line)
    python3 check_frontmatter.py --dry-run          # report without writing
    python3 check_frontmatter.py --stats            # show coverage summary only
    python3 check_frontmatter.py --files a.md b.md  # specific files
"""

import sys, re, json, argparse
from pathlib import Path
from datetime import date

VAULT_ROOT = Path('/root/HermesForge')

# Which directories to scan when running in --all mode
SCAN_DIRS = [
    VAULT_ROOT / '08-Knowledge',
    VAULT_ROOT / '07-Risk',
    VAULT_ROOT / '05-Research',
    VAULT_ROOT / '06-Strategies',
    VAULT_ROOT / '09-Journal',
    VAULT_ROOT / '00-Meta',
    VAULT_ROOT / '03-ADRs',
]

# Fields that MUST exist; value is the default factory (callable -> str)
REQUIRED_FIELDS = {
    'topic':      lambda p: _guess_topic(p),
    'confidence': lambda p: 'high',
    'has_quotes': lambda p: _detect_has_quotes(p),
    'tags':       lambda p: '[]',
    'source':     lambda p: _guess_source(p),
}

# ── helpers ──────────────────────────────────────────────────────────────────

def _guess_topic(path: Path) -> str:
    """Infer topic from folder name."""
    parts = path.parts
    for part in reversed(parts):
        if part.startswith('0') and '-' in part:
            slug = part.split('-', 1)[-1].lower().replace('-', ' ')
            return slug
    return 'general'


def _guess_source(path: Path) -> str:
    """Infer source from folder path."""
    s = str(path)
    if 'murphy' in s.lower():
        return 'Murphy - Technical Analysis of the Financial Markets'
    if '07-Risk' in s:
        return 'HermesForge Risk Framework'
    if '03-ADRs' in s:
        return 'HermesForge ADR'
    if '06-Strategies' in s:
        return 'HermesForge Strategies'
    if '09-Journal' in s:
        return 'HermesForge Journal'
    return 'unknown'


def _detect_has_quotes(path: Path) -> str:
    try:
        text = path.read_text(encoding='utf-8', errors='replace')
        # look for blockquotes or > lines in body (after frontmatter)
        body = re.split(r'^---\s*$', text, maxsplit=2, flags=re.MULTILINE)
        body_text = body[2] if len(body) >= 3 else text
        has = bool(re.search(r'^\s*>', body_text, re.MULTILINE))
        return 'true' if has else 'false'
    except Exception:
        return 'false'


def _parse_frontmatter(text: str):
    """Return (fm_dict, fm_raw_str, body_str) or (None, '', text) if no FM."""
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.DOTALL)
    if not m:
        return None, '', text
    raw = m.group(1)
    body = text[m.end():]
    fm = {}
    for line in raw.splitlines():
        kv = re.match(r'^(\w[\w_-]*):\s*(.*)', line)
        if kv:
            fm[kv.group(1)] = kv.group(2).strip()
    return fm, raw, body


def _rebuild_frontmatter(fm_raw: str, patches: dict) -> str:
    """Insert missing keys just before the closing ---."""
    lines = fm_raw.splitlines()
    additions = []
    for key, val in patches.items():
        additions.append(f'{key}: {val}')
    return '\n'.join(lines + additions)


def process_file(path: Path, dry_run: bool) -> dict | None:
    """Check and optionally fix a single note. Returns patch report or None."""
    try:
        text = path.read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return {'file': str(path), 'error': str(e)}

    fm, fm_raw, body = _parse_frontmatter(text)

    patches = {}
    if fm is None:
        # No frontmatter at all — inject minimal block
        today = date.today().isoformat()
        fm_lines = ['---']
        for field, factory in REQUIRED_FIELDS.items():
            val = factory(path)
            fm_lines.append(f'{field}: {val}')
            patches[field] = val
        fm_lines += [f'created: {today}', '---', '']
        new_text = '\n'.join(fm_lines) + text
        if not dry_run:
            path.write_text(new_text, encoding='utf-8')
        return {'file': str(path), 'action': 'injected_frontmatter', 'fields': patches}

    # Existing frontmatter — check missing fields
    missing = {}
    for field, factory in REQUIRED_FIELDS.items():
        if field not in fm:
            missing[field] = factory(path)

    if not missing:
        return None  # nothing to do

    new_fm_raw = _rebuild_frontmatter(fm_raw, missing)
    new_text = f'---\n{new_fm_raw}\n---\n{body}'
    if not dry_run:
        path.write_text(new_text, encoding='utf-8')
    return {'file': str(path), 'action': 'patched', 'fields': missing}


def collect_files(args) -> list[Path]:
    if args.files:
        return [Path(f) for f in args.files if Path(f).exists()]
    if args.scope == 'new':
        # Read file list from stdin
        paths = []
        for line in sys.stdin:
            p = Path(line.strip())
            if p.exists() and p.suffix == '.md':
                paths.append(p)
        return paths
    # Default: scan all
    files = []
    for d in SCAN_DIRS:
        if d.exists():
            files.extend(d.rglob('*.md'))
    return files


def main():
    ap = argparse.ArgumentParser(description='Check and fix vault frontmatter')
    ap.add_argument('--scope', choices=['all', 'new'], default='all')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--stats', action='store_true')
    ap.add_argument('--files', nargs='+')
    ap.add_argument('--report', default='', help='Write JSON report to this path')
    args = ap.parse_args()

    files = collect_files(args)
    print(f"Scanning {len(files)} notes...", file=sys.stderr)

    results = []
    total = patched = errors = 0

    for path in files:
        total += 1
        r = process_file(path, dry_run=args.dry_run or args.stats)
        if r:
            results.append(r)
            if 'error' in r:
                errors += 1
            else:
                patched += 1

    # Summary
    print(f"\n{'[DRY RUN] ' if args.dry_run or args.stats else ''}Frontmatter check complete:")
    print(f"  Total scanned : {total}")
    print(f"  Patched       : {patched}")
    print(f"  Errors        : {errors}")
    print(f"  Clean         : {total - patched - errors}")

    if results and not args.stats:
        print(f"\nPatched files:")
        for r in results[:20]:
            f = r.get('fields', {})
            print(f"  {Path(r['file']).name}: +{list(f.keys())}")
        if len(results) > 20:
            print(f"  ... and {len(results)-20} more")

    if args.report:
        Path(args.report).write_text(json.dumps(results, indent=2))
        print(f"\nReport written to {args.report}")

    return {'total': total, 'patched': patched, 'errors': errors, 'patches': results}


if __name__ == '__main__':
    main()
