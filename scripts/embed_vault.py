#!/usr/bin/env python3
"""
Embed all vault notes into ChromaDB for semantic search.
Model: all-MiniLM-L6-v2 (22MB, 384 dims, CPU-friendly)
Store: ~/.hermes/vault_index/chroma/

Re-running is safe: only re-embeds notes whose content hash changed.
Downloads model on first run (~22MB).

Usage:
    python3 embed_vault.py                    # embed all books
    python3 embed_vault.py --book <slug>      # embed one book only
    python3 embed_vault.py --force            # force re-embed everything
    python3 embed_vault.py --stats            # show collection stats
"""

import sys, re, json, argparse, hashlib, os
from pathlib import Path
from datetime import datetime, timezone

VAULT_ROOT  = Path('/root/HermesForge')
BOOKS_DIR   = VAULT_ROOT / 'trading/knowledge' / 'Trading-Systems'
VAULT_DIRS  = [
    VAULT_ROOT / '00-Meta',
    VAULT_ROOT / '03-ADRs',
    VAULT_ROOT / 'trading' / 'risk',
    VAULT_ROOT / 'trading/knowledge' / 'Learnings',
    VAULT_ROOT / 'trading/knowledge' / 'Skills',
]
CHROMA_DIR  = Path('/root/.hermes/vault_index/chroma')
MODEL_NAME  = 'all-MiniLM-L6-v2'
COLLECTION  = 'vault_notes'
BATCH_SIZE  = 64
# Prune scope = VAULT_ROOT umbrella prefix (NOT the current walk-dir list).
# The reorg renamed dirs (07-Risk -> trading/risk, 08-Knowledge ->
# trading/knowledge), so old entries point under dirs no longer walked. A
# trailing os.sep guards prefix false-positives (e.g. /root/HermesForge2).
PRUNE_SCOPE = str(VAULT_ROOT) + os.sep
PRUNE_SAFETY_FLOOR = 0.20   # abort prune if orphans exceed 20% of entries


def get_collection():
    import chromadb
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    col = client.get_or_create_collection(
        name=COLLECTION,
        metadata={"hnsw:space": "cosine"}
    )
    return col


def load_model():
    from sentence_transformers import SentenceTransformer
    print(f"Loading model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    print(f"  Embedding dim: {model.get_sentence_embedding_dimension()}")
    return model


def parse_note(filepath: Path) -> dict | None:
    content = filepath.read_text(encoding='utf-8', errors='replace')
    m = re.match(r'^---\n(.*?)\n---\n?(.*)', content, re.DOTALL)
    if not m:
        return None

    raw_fm, body = m.group(1), m.group(2)

    def extract(key):
        match = re.search(rf'^{key}:\s*(.+)$', raw_fm, re.MULTILINE)
        return match.group(1).strip().strip('"\'') if match else ''

    def extract_list(key):
        match = re.search(rf'^{key}:\s*\[(.+?)\]', raw_fm, re.MULTILINE)
        return match.group(1).strip() if match else extract(key)

    ct = extract('concept_type')
    if not ct:
        # For vault docs without concept_type, infer from type: field
        type_m = re.search(r'^type:\s*(.+)$', raw_fm, re.MULTILINE)
        if type_m:
            raw_t = type_m.group(1).strip().strip('"\'')
            type_map = {
                'risk-framework': 'risk-rule', 'risk-guide': 'risk-rule',
                'risk-escalation': 'risk-rule', 'meta': 'meta',
                'dashboard': 'meta', 'adr': 'decision',
                'user-story': 'story', 'story': 'story',
            }
            ct = type_map.get(raw_t, raw_t)
        if not ct:
            ct = 'vault-note'

    title_m = re.search(r'^#\s+(.+)$', body, re.MULTILINE)
    title = title_m.group(1).strip() if title_m else ''

    # Clean body for embedding
    clean_body = re.sub(r'^#{1,6}\s+.*$', '', body, flags=re.MULTILINE)
    clean_body = re.sub(r'>\s+"(.+?)".*', r'\1', clean_body)  # keep quote text
    clean_body = re.sub(r'[*_`\[\]]', '', clean_body)
    clean_body = re.sub(r'\n{3,}', '\n\n', clean_body).strip()

    # Text to embed: title + topic context + body (truncated to ~512 tokens = ~2000 chars)
    topic = extract_list('topic')
    embed_text = f"{title}. Topics: {topic}. {clean_body}"[:2000]

    chash = hashlib.md5(content.encode()).hexdigest()[:16]

    return {
        'id': str(filepath),
        'text': embed_text,
        'metadata': {
            'filepath':      str(filepath),
            'filename':      filepath.name,
            'title':         title,
            'concept_type':  ct,
            'topic':         topic,
            'confidence':    extract('confidence'),
            'source_book':   extract('source_book'),
            'source_author': extract('source_author'),
            'source_page':   extract('source_page_range'),
            'book_slug':     filepath.parts[-3] if len(filepath.parts) >= 3 else '',
            'content_hash':  chash,
        }
    }


def embed_book(col, model, book_dir: Path, force: bool = False) -> int:
    notes = [f for f in book_dir.rglob('*.md') if f.name != '00-Literature-Note.md']
    slug = book_dir.name
    print(f"  {slug}: {len(notes)} notes")

    # Get existing hashes from collection
    existing = {}
    if not force:
        try:
            existing_data = col.get(
                where={"book_slug": slug},
                include=["metadatas"]
            )
            for meta in existing_data['metadatas']:
                existing[meta['filepath']] = meta.get('content_hash', '')
        except Exception:
            pass

    # Parse and filter
    to_embed = []
    for note in notes:
        parsed = parse_note(note)
        if not parsed:
            continue
        chash = parsed['metadata']['content_hash']
        if existing.get(str(note)) == chash and not force:
            continue
        to_embed.append(parsed)

    if not to_embed:
        print(f"    All {len(notes)} notes up to date")
        return 0

    print(f"    Embedding {len(to_embed)} notes (skipping {len(notes)-len(to_embed)} unchanged)...")

    # Process in batches
    embedded = 0
    for i in range(0, len(to_embed), BATCH_SIZE):
        batch = to_embed[i:i+BATCH_SIZE]
        texts = [n['text'] for n in batch]
        ids   = [n['id']   for n in batch]
        metas = [n['metadata'] for n in batch]

        embeddings = model.encode(texts, show_progress_bar=False).tolist()

        # Upsert (handles both insert and update)
        col.upsert(
            ids=ids,
            embeddings=embeddings,
            metadatas=metas,
            documents=[n['text'] for n in batch],
        )
        embedded += len(batch)
        if len(to_embed) > BATCH_SIZE:
            print(f"    Progress: {min(i+BATCH_SIZE, len(to_embed))}/{len(to_embed)}", flush=True)

    return embedded


def show_stats(col):
    count = col.count()
    print(f"\n=== Chroma Collection Stats ===")
    print(f"Total embeddings: {count}")
    print(f"Collection: {COLLECTION}")
    print(f"Store: {CHROMA_DIR}")


def prune_stale(col, scope_prefix, dry_run=False, force_prune=False):
    """Delete embeddings whose metadata['filepath'] is under scope_prefix and
    whose file no longer exists on disk. Uses the Chroma collection API only
    (no raw SQL). Returns list of deleted filepaths."""
    data = col.get(include=["metadatas"])
    ids = data.get("ids", [])
    metas = data.get("metadatas", []) or []
    orphans = []
    for i, meta in enumerate(metas):
        if not meta:
            continue
        fp = meta.get("filepath", "")
        if not fp.startswith(scope_prefix):
            continue
        if not os.path.exists(fp):
            orphans.append(ids[i])
    if orphans and not dry_run:
        total = len(ids)
        if not force_prune and len(orphans) > PRUNE_SAFETY_FLOOR * total:
            pct = 100.0 * len(orphans) / total if total else 0.0
            print(f"WARNING: prune would remove {len(orphans)} orphan entries "
                  f"({pct:.1f}% of {total}) which exceeds the "
                  f"{PRUNE_SAFETY_FLOOR*100:.0f}% safety floor. "
                  f"Aborting — re-run with --force-prune to confirm bulk prune.")
            return []
        for i in range(0, len(orphans), 256):
            col.delete(ids=orphans[i:i + 256])
    return orphans


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--book', default='', help='Embed only this book slug')
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--stats', action='store_true')
    parser.add_argument('--dry-run', action='store_true', help='Prune listing only, delete nothing')
    parser.add_argument('--no-prune', action='store_true', help='Skip pruning entirely')
    parser.add_argument('--force-prune', action='store_true', help='Bypass prune safety floor for bulk prune')
    args = parser.parse_args()

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    col = get_collection()

    if args.stats:
        show_stats(col)
        return

    model = load_model()

    book_dirs = ([BOOKS_DIR / args.book] if args.book
                 else [d for d in BOOKS_DIR.iterdir() if d.is_dir()])
    vault_extra = [] if args.book else [d for d in VAULT_DIRS if d.exists()]

    t0 = datetime.now(timezone.utc)
    total = 0
    for bd in book_dirs:
        if not bd.exists():
            print(f"WARNING: {bd} not found"); continue
        n = embed_book(col, model, bd, force=args.force)
        total += n

    # Embed extra vault sections
    for vdir in vault_extra:
        slug = f"vault-{vdir.name.lower()}"
        n = embed_book(col, model, vdir, force=args.force)
        total += n

    # Single-book/partial runs must not bulk-delete entries for directories not
    # walked this run, so skip the global VAULT_ROOT prune unless --book is off.
    if not args.no_prune and not args.book:
        orphans = prune_stale(col, PRUNE_SCOPE, dry_run=args.dry_run, force_prune=args.force_prune)
        print(f"\nPruned {len(orphans)} stale embeddings" + (" (DRY RUN)" if args.dry_run else ""))
        for fp in orphans:
            print(f"  - {fp}")

    elapsed = (datetime.now(timezone.utc) - t0).total_seconds()
    print(f"\nDone. {total} notes embedded in {elapsed:.1f}s")
    show_stats(col)


if __name__ == '__main__':
    main()
