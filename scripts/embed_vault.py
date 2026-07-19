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

import sys, re, json, argparse, hashlib
from pathlib import Path
from datetime import datetime

VAULT_ROOT  = Path('/root/HermesForge')
BOOKS_DIR   = VAULT_ROOT / '08-Knowledge' / 'Trading-Systems'
VAULT_DIRS  = [
    VAULT_ROOT / '00-Meta',
    VAULT_ROOT / '03-ADRs',
    VAULT_ROOT / '07-Risk',
    VAULT_ROOT / '08-Knowledge' / 'Learnings',
    VAULT_ROOT / '08-Knowledge' / 'Skills',
]
CHROMA_DIR  = Path('/root/.hermes/vault_index/chroma')
MODEL_NAME  = 'all-MiniLM-L6-v2'
COLLECTION  = 'vault_notes'
BATCH_SIZE  = 64


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--book', default='', help='Embed only this book slug')
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--stats', action='store_true')
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

    t0 = datetime.utcnow()
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

    elapsed = (datetime.utcnow() - t0).total_seconds()
    print(f"\nDone. {total} notes embedded in {elapsed:.1f}s")
    show_stats(col)


if __name__ == '__main__':
    main()
