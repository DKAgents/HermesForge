#!/usr/bin/env python3
"""
Auto-generate wikilinks in vault notes using anchor-phrase matching.

For each note, searches its body text for anchor phrases derived from other
note titles and inserts wikilinks in the Related Notes section.

Anchor phrases: most specific 2-3 consecutive meaningful words from each title.
Safe to re-run — only adds links not already present. Dry-run mode available.

Usage:
    python3 generate_wikilinks.py <book_folder>
    python3 generate_wikilinks.py /root/HermesForge/08-Knowledge/Trading-Systems/technical-analysis-financial-markets-murphy
    python3 generate_wikilinks.py --all
    python3 generate_wikilinks.py --dry-run <book_folder>
"""

import sys, re, json, argparse
from pathlib import Path
from collections import defaultdict

MAX_LINKS_PER_NOTE = 8

STOPWORDS = {
    'the','a','an','and','of','in','for','to','on','by','as','at','or',
    'with','from','its','this','that','when','how','what','which','after',
    'before','during','using','used','basic','general','important','key',
    'main','simple','common','typical','standard','also','both','each',
    'other','same','some','such','these','those','very','well','can','may',
    'will','would','should','has','have','are','were','been','via','per',
    'two','three','four','five','six','seven','eight','nine','ten',
}


def get_anchors(title: str) -> list[str]:
    """Return candidate anchor phrases (3-word, then 2-word) from meaningful title words."""
    words = re.findall(r'\b[a-zA-Z]{3,}\b', title.lower())
    meaningful = [w for w in words if w not in STOPWORDS]
    if len(meaningful) < 2:
        return []
    anchors = []
    for i in range(len(meaningful) - 2):
        anchors.append(' '.join(meaningful[i:i+3]))
    for i in range(len(meaningful) - 1):
        anchors.append(' '.join(meaningful[i:i+2]))
    return anchors


def build_anchor_index(book_dir: Path) -> dict[str, tuple[str, str]]:
    """
    Build map: anchor_phrase → (display_title, stem).
    Each note registers its best (most specific) uncontested anchor.
    """
    # First pass: collect all anchors per note
    note_anchors: list[tuple[str, list[str], str]] = []  # (title, anchors, stem)
    for fpath in book_dir.rglob('*.md'):
        if fpath.name == '00-Literature-Note.md':
            continue
        content = fpath.read_text(encoding='utf-8')
        m = re.search(r'^# (.+)$', content, re.MULTILINE)
        if not m:
            continue
        title = m.group(1).strip()
        if len(title) < 8 or len(title.split()) < 2:
            continue
        anchors = get_anchors(title)
        if anchors:
            note_anchors.append((title, anchors, fpath.stem))

    # Second pass: assign best uncontested anchor per note
    anchor_claims: dict[str, list[str]] = defaultdict(list)  # anchor → [stems]
    for title, anchors, stem in note_anchors:
        for a in anchors:
            anchor_claims[a].append(stem)

    # Only register anchors claimed by exactly one note (unambiguous)
    anchor_index: dict[str, tuple[str, str]] = {}
    for title, anchors, stem in note_anchors:
        for a in anchors:
            if len(anchor_claims[a]) == 1:  # uncontested
                anchor_index[a] = (title, stem)
                break  # best anchor registered

    return anchor_index


def get_existing_links(content: str) -> set[str]:
    existing = set()
    if '## Related Notes' not in content:
        return existing
    rel_section = content.split('## Related Notes')[-1]
    for m in re.finditer(r'\[\[([^\]|]+)', rel_section):
        existing.add(m.group(1).strip())
    return existing


def find_links_for_note(fpath: Path, anchor_index: dict) -> list[tuple[str, str]]:
    content = fpath.read_text(encoding='utf-8')
    fm_end = content.find('---', 3)
    body = content[fm_end+3:] if fm_end > 0 else content
    rel_idx = body.find('## Related Notes')
    body_text = (body[:rel_idx] if rel_idx >= 0 else body).lower()

    existing_stems = get_existing_links(content)
    found_stems: set[str] = set(existing_stems)
    found_links: list[tuple[str, str]] = []

    for anchor, (display, stem) in anchor_index.items():
        if stem == fpath.stem or stem in found_stems:
            continue
        if anchor in body_text:
            found_stems.add(stem)
            found_links.append((display, stem))
            if len(found_links) >= MAX_LINKS_PER_NOTE:
                break

    return found_links


def apply_links(fpath: Path, links: list[tuple[str, str]], dry_run: bool = False) -> int:
    if not links:
        return 0
    content = fpath.read_text(encoding='utf-8')
    link_lines = '\n'.join(f'- [[{stem}|{display}]]' for display, stem in links)

    if '## Related Notes\n_None identified_' in content:
        new_content = content.replace(
            '## Related Notes\n_None identified_',
            f'## Related Notes\n{link_lines}'
        )
    elif '## Related Notes\n' in content:
        idx = content.index('## Related Notes\n') + len('## Related Notes\n')
        new_content = content[:idx] + link_lines + '\n' + content[idx:]
    else:
        new_content = content.rstrip() + f'\n\n## Related Notes\n{link_lines}\n'

    if new_content != content:
        if not dry_run:
            fpath.write_text(new_content, encoding='utf-8')
        return len(links)
    return 0


def process_book(book_dir: Path, dry_run: bool = False) -> dict:
    notes = [f for f in book_dir.rglob('*.md') if f.name != '00-Literature-Note.md']
    print(f"\nProcessing: {book_dir.name} ({len(notes)} notes)")

    anchor_index = build_anchor_index(book_dir)
    print(f"  Anchor index: {len(anchor_index)} unambiguous anchors")

    total_added = 0
    notes_linked = 0
    report = []

    for fpath in notes:
        links = find_links_for_note(fpath, anchor_index)
        if not links:
            continue
        added = apply_links(fpath, links, dry_run=dry_run)
        if added:
            total_added += added
            notes_linked += 1
            report.append({'note': fpath.name, 'links': [s for _, s in links]})

    prefix = '[DRY RUN] ' if dry_run else ''
    print(f"  {prefix}Notes linked: {notes_linked}")
    print(f"  {prefix}Total links added: {total_added}")

    return {
        'book': book_dir.name,
        'anchor_index_size': len(anchor_index),
        'notes_processed': len(notes),
        'notes_linked': notes_linked,
        'total_links_added': total_added,
        'sample': report[:20],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('book_dir', nargs='?')
    parser.add_argument('--all', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    base = Path('/root/HermesForge/08-Knowledge/Trading-Systems')

    if args.all:
        book_dirs = [d for d in base.iterdir() if d.is_dir()]
    elif args.book_dir:
        book_dirs = [Path(args.book_dir)]
    else:
        print("Usage: generate_wikilinks.py <book_folder> | --all [--dry-run]")
        sys.exit(1)

    results = []
    for bd in book_dirs:
        if not bd.exists():
            print(f"WARNING: {bd} not found"); continue
        results.append(process_book(bd, dry_run=args.dry_run))

    report_path = Path('/root/HermesForge/scripts/wikilink_report.json')
    report_path.write_text(json.dumps(results, indent=2))
    print(f"\nReport: {report_path}")
    print(f"Grand total links {'(would be) ' if args.dry_run else ''}added: {sum(r['total_links_added'] for r in results)}")


if __name__ == '__main__':
    main()
