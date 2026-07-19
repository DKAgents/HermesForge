#!/usr/bin/env python3
"""
Build FTS5 full-text search index over all vault notes.
Creates ~/.hermes/vault_index/vault.db (SQLite + FTS5).

Re-running is safe: uses file mtime + content hash to skip unchanged notes.
Indexes all books under 08-Knowledge/Trading-Systems/.

Usage:
    python3 build_index.py                    # index all books
    python3 build_index.py --book <slug>      # index one book
    python3 build_index.py --force            # force re-index everything
    python3 build_index.py --stats            # show index stats only
"""

import sqlite3, sys, re, json, hashlib, argparse
from pathlib import Path
from datetime import datetime

VAULT_ROOT  = Path('/root/HermesForge')
BOOKS_DIR   = VAULT_ROOT / '08-Knowledge' / 'Trading-Systems'
VAULT_DIRS  = [                          # additional vault sections to index
    VAULT_ROOT / '00-Meta',
    VAULT_ROOT / '03-ADRs',
    VAULT_ROOT / '07-Risk',
    VAULT_ROOT / '08-Knowledge' / 'Learnings',
    VAULT_ROOT / '08-Knowledge' / 'Skills',
]
INDEX_DIR   = Path('/root/.hermes/vault_index')
INDEX_PATH  = INDEX_DIR / 'vault.db'


def get_db() -> sqlite3.Connection:
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(INDEX_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_schema(conn: sqlite3.Connection):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS notes (
        id          INTEGER PRIMARY KEY,
        filepath    TEXT UNIQUE NOT NULL,
        book_slug   TEXT NOT NULL,
        title       TEXT,
        concept_type TEXT,
        topic       TEXT,
        confidence  TEXT,
        source_book TEXT,
        source_author TEXT,
        source_chapter TEXT,
        source_page TEXT,
        body        TEXT,
        ingested_at TEXT,
        content_hash TEXT,
        indexed_at  TEXT
    );

    CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
        title,
        body,
        topic,
        concept_type,
        source_chapter,
        content='notes',
        content_rowid='id',
        tokenize='porter unicode61'
    );

    CREATE TABLE IF NOT EXISTS index_meta (
        key   TEXT PRIMARY KEY,
        value TEXT
    );

    CREATE TRIGGER IF NOT EXISTS notes_ai AFTER INSERT ON notes BEGIN
        INSERT INTO notes_fts(rowid, title, body, topic, concept_type, source_chapter)
        VALUES (new.id, new.title, new.body, new.topic, new.concept_type, new.source_chapter);
    END;

    CREATE TRIGGER IF NOT EXISTS notes_ad AFTER DELETE ON notes BEGIN
        INSERT INTO notes_fts(notes_fts, rowid, title, body, topic, concept_type, source_chapter)
        VALUES ('delete', old.id, old.title, old.body, old.topic, old.concept_type, old.source_chapter);
    END;

    CREATE TRIGGER IF NOT EXISTS notes_au AFTER UPDATE ON notes BEGIN
        INSERT INTO notes_fts(notes_fts, rowid, title, body, topic, concept_type, source_chapter)
        VALUES ('delete', old.id, old.title, old.body, old.topic, old.concept_type, old.source_chapter);
        INSERT INTO notes_fts(rowid, title, body, topic, concept_type, source_chapter)
        VALUES (new.id, new.title, new.body, new.topic, new.concept_type, new.source_chapter);
    END;
    """)
    conn.commit()


def parse_frontmatter(content: str) -> dict:
    fm = {}
    m = re.match(r'^---\n(.*?)\n---\n?(.*)', content, re.DOTALL)
    if not m:
        return fm
    raw_fm = m.group(1)

    def extract(key):
        match = re.search(rf'^{key}:\s*(.+)$', raw_fm, re.MULTILINE)
        if not match:
            return ''
        val = match.group(1).strip().strip('"\'')
        return val

    def extract_list(key):
        match = re.search(rf'^{key}:\s*\[(.+?)\]', raw_fm, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return extract(key)

    fm['concept_type']   = extract('concept_type')
    fm['confidence']     = extract('confidence')
    fm['source_book']    = extract('source_book')
    fm['source_author']  = extract('source_author')
    fm['source_chapter'] = extract('source_chapter')
    fm['source_page']    = extract('source_page_range')
    fm['ingested_at']    = extract('ingested_at')
    fm['topic']          = extract_list('topic')

    # Extract title from first # heading in body
    body = m.group(2)
    title_m = re.search(r'^#\s+(.+)$', body, re.MULTILINE)
    fm['title'] = title_m.group(1).strip() if title_m else ''

    # Body = everything after the first heading, stripping markdown
    fm['body'] = re.sub(r'^#{1,6}\s+.*$', '', body, flags=re.MULTILINE)
    fm['body'] = re.sub(r'!\[.*?\]\(.*?\)', '', fm['body'])
    fm['body'] = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', fm['body'])
    fm['body'] = re.sub(r'[*_`]', '', fm['body'])
    fm['body'] = re.sub(r'\n{3,}', '\n\n', fm['body']).strip()

    return fm


def content_hash(content: str) -> str:
    return hashlib.md5(content.encode()).hexdigest()[:16]


def index_note(conn: sqlite3.Connection, filepath: Path, book_slug: str, force: bool = False) -> bool:
    content = filepath.read_text(encoding='utf-8', errors='replace')
    chash = content_hash(content)

    # Check if already indexed with same hash
    row = conn.execute("SELECT content_hash FROM notes WHERE filepath=?",
                       (str(filepath),)).fetchone()
    if row and row['content_hash'] == chash and not force:
        return False  # unchanged

    fm = parse_frontmatter(content)
    # For non-atomic notes (risk docs, ADRs, meta), synthesize fields from type/heading
    if not fm.get('concept_type'):
        fm_type_m = re.search(r'^type:\s*(.+)$', content, re.MULTILINE)
        if fm_type_m:
            raw_type = fm_type_m.group(1).strip().strip('"\'')
            type_map = {
                'risk-framework': 'risk-rule', 'risk-guide': 'risk-rule',
                'risk-escalation': 'risk-rule', 'meta': 'meta',
                'dashboard': 'meta', 'adr': 'decision',
                'user-story': 'story', 'story': 'story',
                'literature-note': 'literature',
            }
            fm['concept_type'] = type_map.get(raw_type, raw_type)
        if not fm.get('concept_type'):
            fm['concept_type'] = 'vault-note'
    # Ensure title is always set — fall back to filename
    if not fm.get('title'):
        heading_m = re.search(r'^# (.+)$', content, re.MULTILINE)
        fm['title'] = heading_m.group(1).strip() if heading_m else filepath.stem
    # Ensure other fields have defaults
    fm.setdefault('topic', '')
    fm.setdefault('confidence', 'high')
    fm.setdefault('source_book', 'HermesForge Vault')
    fm.setdefault('source_author', 'HermesForge')
    fm.setdefault('source_chapter', '')
    fm.setdefault('source_page', '')
    fm.setdefault('ingested_at', '')
    fm.setdefault('body', '')

    now = datetime.utcnow().isoformat()
    if row:
        conn.execute("""
            UPDATE notes SET title=?, concept_type=?, topic=?, confidence=?,
                source_book=?, source_author=?, source_chapter=?, source_page=?,
                body=?, ingested_at=?, content_hash=?, indexed_at=?, book_slug=?
            WHERE filepath=?
        """, (fm['title'], fm['concept_type'], fm['topic'], fm['confidence'],
              fm['source_book'], fm['source_author'], fm['source_chapter'], fm['source_page'],
              fm['body'], fm['ingested_at'], chash, now, book_slug, str(filepath)))
    else:
        conn.execute("""
            INSERT INTO notes (filepath, book_slug, title, concept_type, topic, confidence,
                source_book, source_author, source_chapter, source_page,
                body, ingested_at, content_hash, indexed_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (str(filepath), book_slug, fm['title'], fm['concept_type'], fm['topic'],
              fm['confidence'], fm['source_book'], fm['source_author'],
              fm['source_chapter'], fm['source_page'], fm['body'],
              fm['ingested_at'], chash, now))
    return True


def index_book(conn: sqlite3.Connection, book_dir: Path, force: bool = False) -> int:
    slug = book_dir.name
    notes = [f for f in book_dir.rglob('*.md') if f.name != '00-Literature-Note.md']
    indexed = 0
    for note in notes:
        if index_note(conn, note, slug, force=force):
            indexed += 1
    conn.commit()
    return indexed


def show_stats(conn: sqlite3.Connection):
    total = conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
    by_book = conn.execute(
        "SELECT book_slug, COUNT(*) as n FROM notes GROUP BY book_slug ORDER BY n DESC"
    ).fetchall()
    by_type = conn.execute(
        "SELECT concept_type, COUNT(*) as n FROM notes GROUP BY concept_type ORDER BY n DESC"
    ).fetchall()
    print(f"\n=== Vault Index Stats ===")
    print(f"Total notes indexed: {total}")
    print(f"\nBy book:")
    for r in by_book:
        print(f"  {r['book_slug'][:50]:50s}: {r['n']}")
    print(f"\nBy concept_type:")
    for r in by_type:
        print(f"  {r['concept_type']:20s}: {r['n']}")
    print(f"\nIndex location: {INDEX_PATH}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--book', help='Index only this book slug')
    parser.add_argument('--force', action='store_true', help='Force re-index all')
    parser.add_argument('--stats', action='store_true', help='Show stats only')
    args = parser.parse_args()

    conn = get_db()
    init_schema(conn)

    if args.stats:
        show_stats(conn)
        conn.close()
        return

    if args.book:
        book_dirs = [BOOKS_DIR / args.book]
        vault_extra = []
    else:
        book_dirs = [d for d in BOOKS_DIR.iterdir() if d.is_dir()]
        vault_extra = [d for d in VAULT_DIRS if d.exists()]

    total_indexed = 0
    for book_dir in book_dirs:
        if not book_dir.exists():
            print(f"WARNING: {book_dir} not found, skipping")
            continue
        n = index_book(conn, book_dir, force=args.force)
        print(f"  {book_dir.name}: {n} notes indexed/updated")
        total_indexed += n

    # Index extra vault sections (risk, meta, ADRs, etc.)
    for vdir in vault_extra:
        notes = list(vdir.rglob('*.md'))
        indexed = 0
        slug = f"vault-{vdir.name.lower().replace(' ','-')}"
        for note in notes:
            if index_note(conn, note, slug, force=args.force):
                indexed += 1
        if indexed:
            print(f"  vault/{vdir.name}: {indexed} notes indexed/updated")
        total_indexed += indexed

    # Update meta
    conn.execute("INSERT OR REPLACE INTO index_meta VALUES ('last_indexed', ?)",
                 (datetime.utcnow().isoformat(),))
    conn.commit()

    print(f"\nDone. {total_indexed} notes indexed/updated.")
    show_stats(conn)
    conn.close()


if __name__ == '__main__':
    main()
