#!/usr/bin/env python3
"""
Deduplicate vault notes using TF-IDF cosine similarity.

Groups notes by body similarity and reports/removes near-duplicates.
Auto-deletion only fires above 0.98; below that only reports.

Usage:
    python3 dedup_notes.py                          # scan, report only (safe)
    python3 dedup_notes.py --dry-run                # same as above
    python3 dedup_notes.py --auto-delete            # delete above 0.98 threshold
    python3 dedup_notes.py --threshold 0.90         # lower threshold for reporting
    python3 dedup_notes.py --scope murphy           # only murphy notes
    python3 dedup_notes.py --report /tmp/dedup.json # write report to path
    python3 dedup_notes.py --files a.md b.md        # specific files to compare
"""

import sys, re, json, argparse, math
from pathlib import Path
from collections import defaultdict

VAULT_ROOT = Path('/root/HermesForge')
MURPHY_DIR = VAULT_ROOT / '08-Knowledge' / 'Trading-Systems' / 'technical-analysis-financial-markets-murphy'

SCAN_DIRS = [
    VAULT_ROOT / '08-Knowledge',
    VAULT_ROOT / '07-Risk',
    VAULT_ROOT / '06-Strategies',
    VAULT_ROOT / '09-Journal',
]

REPORT_THRESHOLD = 0.90   # report duplicates above this
AUTO_DELETE_THRESHOLD = 0.98  # auto-delete only above this


# ── TF-IDF similarity ─────────────────────────────────────────────────────────

def tokenize(text: str) -> list[str]:
    return re.findall(r'\b[a-z]{3,}\b', text.lower())


def build_tfidf(docs: list[list[str]]) -> list[dict]:
    """Return TF-IDF vectors as dicts for each document."""
    N = len(docs)
    df = defaultdict(int)
    for tokens in docs:
        for t in set(tokens):
            df[t] += 1

    vecs = []
    for tokens in docs:
        tf = defaultdict(int)
        for t in tokens:
            tf[t] += 1
        vec = {}
        for t, count in tf.items():
            vec[t] = (count / len(tokens)) * math.log((N + 1) / (df[t] + 1))
        vecs.append(vec)
    return vecs


def cosine(a: dict, b: dict) -> float:
    common = set(a) & set(b)
    if not common:
        return 0.0
    dot = sum(a[t] * b[t] for t in common)
    na = math.sqrt(sum(v*v for v in a.values()))
    nb = math.sqrt(sum(v*v for v in b.values()))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


# ── note loading ──────────────────────────────────────────────────────────────

def get_body(path: Path) -> str:
    """Return note body (stripped frontmatter) as string."""
    try:
        text = path.read_text(encoding='utf-8', errors='replace')
        parts = re.split(r'^---\s*$', text, maxsplit=2, flags=re.MULTILINE)
        return parts[2].strip() if len(parts) >= 3 else text.strip()
    except Exception:
        return ''


def get_score_key(path: Path) -> int:
    """Prefer notes with more body content (longer = richer)."""
    return len(get_body(path))


def collect_files(args) -> list[Path]:
    if args.files:
        return [Path(f) for f in args.files if Path(f).suffix == '.md']
    if args.scope == 'murphy':
        return list(MURPHY_DIR.rglob('*.md'))
    files = []
    for d in SCAN_DIRS:
        if d.exists():
            files.extend(d.rglob('*.md'))
    return files


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description='Deduplicate vault notes by similarity')
    ap.add_argument('--dry-run', action='store_true', default=True,
                    help='Report only, no deletions (default)')
    ap.add_argument('--auto-delete', action='store_true',
                    help=f'Delete notes above {AUTO_DELETE_THRESHOLD} threshold')
    ap.add_argument('--threshold', type=float, default=REPORT_THRESHOLD,
                    help=f'Reporting threshold (default {REPORT_THRESHOLD})')
    ap.add_argument('--scope', choices=['all', 'murphy'], default='all')
    ap.add_argument('--report', default='', help='Path to write JSON report')
    ap.add_argument('--files', nargs='+')
    args = ap.parse_args()

    # --auto-delete overrides dry-run default
    dry_run = not args.auto_delete

    files = collect_files(args)
    print(f"Loading {len(files)} notes...", file=sys.stderr)

    # Filter to notes with non-empty bodies
    valid = [(p, get_body(p)) for p in files]
    valid = [(p, b) for p, b in valid if len(b) > 50]
    print(f"  {len(valid)} notes with body content", file=sys.stderr)

    if len(valid) < 2:
        print("Not enough notes to compare.")
        return

    paths, bodies = zip(*valid)
    tokens = [tokenize(b) for b in bodies]

    print("Building TF-IDF vectors...", file=sys.stderr)
    vecs = build_tfidf(list(tokens))

    print("Computing pairwise similarities (this may take a moment for large vaults)...", file=sys.stderr)

    # For large vaults, only compare notes in the same subfolder to keep O(n²) manageable
    # Group by parent dir
    groups = defaultdict(list)
    for i, p in enumerate(paths):
        groups[p.parent].append(i)

    # Also do a global sample (first 200 notes) for cross-folder duplication
    global_sample = list(range(min(200, len(paths))))

    pairs = set()
    for group_indices in groups.values():
        for ii in range(len(group_indices)):
            for jj in range(ii + 1, len(group_indices)):
                pairs.add((group_indices[ii], group_indices[jj]))

    for ii in range(len(global_sample)):
        for jj in range(ii + 1, len(global_sample)):
            pairs.add((global_sample[ii], global_sample[jj]))

    print(f"  Comparing {len(pairs):,} pairs...", file=sys.stderr)

    candidates = []
    for i, j in pairs:
        sim = cosine(vecs[i], vecs[j])
        if sim >= args.threshold:
            candidates.append({
                'note_a': str(paths[i]),
                'note_b': str(paths[j]),
                'similarity': round(sim, 4),
                'keep': str(paths[i]) if get_score_key(paths[i]) >= get_score_key(paths[j]) else str(paths[j]),
                'delete': str(paths[j]) if get_score_key(paths[i]) >= get_score_key(paths[j]) else str(paths[i]),
                'auto_delete': sim >= AUTO_DELETE_THRESHOLD,
            })

    candidates.sort(key=lambda x: -x['similarity'])

    print(f"\nDuplication report:")
    print(f"  Pairs above {args.threshold:.0%}   : {len(candidates)}")
    auto = [c for c in candidates if c['auto_delete']]
    print(f"  Auto-delete candidates (≥{AUTO_DELETE_THRESHOLD:.0%}): {len(auto)}")

    if candidates:
        print(f"\nTop duplicates:")
        for c in candidates[:10]:
            flag = "🔴 AUTO-DELETE" if c['auto_delete'] else "🟡 report"
            print(f"  {flag} ({c['similarity']:.3f})")
            print(f"    A: {Path(c['note_a']).name}")
            print(f"    B: {Path(c['note_b']).name}")

    deleted = 0
    if not dry_run and auto:
        print(f"\nDeleting {len(auto)} near-exact duplicates...")
        for c in auto:
            del_path = Path(c['delete'])
            try:
                del_path.unlink()
                deleted += 1
                print(f"  Deleted: {del_path.name}")
            except Exception as e:
                print(f"  Error deleting {del_path}: {e}")
        print(f"  Deleted {deleted} files.")
    elif dry_run and auto:
        print(f"\n[DRY RUN] Would delete {len(auto)} files. Pass --auto-delete to execute.")

    if args.report:
        report = {
            'total_compared': len(valid),
            'pairs_checked': len(pairs),
            'candidates': candidates,
            'deleted': deleted,
            'dry_run': dry_run,
        }
        Path(args.report).write_text(json.dumps(report, indent=2))
        print(f"\nReport written to {args.report}")

    return {'candidates': len(candidates), 'auto_delete': len(auto), 'deleted': deleted}


if __name__ == '__main__':
    main()
