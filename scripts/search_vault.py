#!/usr/bin/env python3
"""
Search the vault FTS5 index. Returns ranked results with snippet highlights.

Usage:
    python3 search_vault.py "support resistance role reversal"
    python3 search_vault.py "rsi divergence" --type rule --limit 10
    python3 search_vault.py "stop placement" --topic risk-management
    python3 search_vault.py "trend" --book technical-analysis-financial-markets-murphy
    python3 search_vault.py "oscillator" --type entry-criteria --json
"""

import sqlite3, sys, re, json, argparse
from pathlib import Path

INDEX_PATH = Path('/root/.hermes/vault_index/vault.db')


def search(query: str, concept_type: str = "", topic: str = "",
           book: str = "", limit: int = 10, confidence: str = "") -> list[dict]:
    if not INDEX_PATH.exists():
        print(f"ERROR: Index not found at {INDEX_PATH}")
        print("Run: python3 /root/HermesForge/scripts/build_index.py")
        sys.exit(1)

    conn = sqlite3.connect(str(INDEX_PATH))
    conn.row_factory = sqlite3.Row

    where_clauses = ["notes.id = notes_fts.rowid"]
    params: list = [query]

    if concept_type:
        where_clauses.append("notes.concept_type = ?")
        params.append(concept_type)
    if topic:
        where_clauses.append("notes.topic LIKE ?")
        params.append(f'%{topic}%')
    if book:
        where_clauses.append("notes.book_slug = ?")
        params.append(book)
    if confidence:
        where_clauses.append("notes.confidence = ?")
        params.append(confidence)

    where_sql = " AND ".join(where_clauses)
    params.append(limit)

    sql = f"""
        SELECT
            notes.filepath,
            notes.title,
            notes.concept_type,
            notes.topic,
            notes.confidence,
            notes.source_book,
            notes.source_author,
            notes.source_chapter,
            notes.source_page,
            notes.book_slug,
            snippet(notes_fts, 1, '**', '**', '...', 32) AS snippet,
            rank
        FROM notes_fts
        JOIN notes ON notes.id = notes_fts.rowid
        WHERE notes_fts MATCH ?
          AND {where_sql}
        ORDER BY rank
        LIMIT ?
    """

    try:
        rows = conn.execute(sql, params).fetchall()
    except sqlite3.OperationalError:
        # FTS5 syntax error — escape special chars and retry
        safe_query = re.sub(r'[^\w\s]', ' ', query)
        params[0] = safe_query
        rows = conn.execute(sql, params).fetchall()

    conn.close()
    return [dict(r) for r in rows]


def format_results(results: list[dict], query: str) -> str:
    if not results:
        return f"No results for: '{query}'"

    lines = [f"Search: '{query}' → {len(results)} results\n{'='*60}"]
    for i, r in enumerate(results, 1):
        lines.append(f"\n[{i}] {r['title']}")
        lines.append(f"    Type: {r['concept_type']} | Topic: {r['topic']} | "
                     f"Confidence: {r['confidence']} | Page: {r['source_page']}")
        lines.append(f"    Book: {r['source_book']}")
        if r['snippet']:
            lines.append(f"    > ...{r['snippet']}...")
        lines.append(f"    File: {Path(r['filepath']).name}")
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('query', help='Search query')
    parser.add_argument('--type', dest='concept_type', default='', help='Filter by concept_type')
    parser.add_argument('--topic', default='', help='Filter by topic (partial match)')
    parser.add_argument('--book', default='', help='Filter by book slug')
    parser.add_argument('--confidence', default='', choices=['', 'high', 'low'])
    parser.add_argument('--limit', type=int, default=10)
    parser.add_argument('--json', action='store_true', dest='as_json',
                        help='Output raw JSON (for programmatic use)')
    args = parser.parse_args()

    results = search(
        query=args.query,
        concept_type=args.concept_type,
        topic=args.topic,
        book=args.book,
        limit=args.limit,
        confidence=args.confidence,
    )

    if args.as_json:
        print(json.dumps(results, indent=2))
    else:
        print(format_results(results, args.query))


if __name__ == '__main__':
    main()
