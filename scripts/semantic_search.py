#!/usr/bin/env python3
"""
Semantic search over vault embeddings using ChromaDB + MiniLM.
Complements FTS5 keyword search with meaning-based retrieval.

Usage:
    python3 semantic_search.py "when does a trend end"
    python3 semantic_search.py "false breakout signals" --type rule --limit 8
    python3 semantic_search.py "how to size positions" --topic risk-management
    python3 semantic_search.py "bearish reversal confirmation" --json
"""

import sys, re, json, argparse
from pathlib import Path

CHROMA_DIR = Path('/root/.hermes/vault_index/chroma')
MODEL_NAME = 'all-MiniLM-L6-v2'
COLLECTION = 'vault_notes'


def semantic_search(query: str, concept_type: str = "", topic: str = "",
                    book: str = "", limit: int = 8) -> list[dict]:
    if not CHROMA_DIR.exists():
        print(f"ERROR: Chroma store not found at {CHROMA_DIR}")
        print("Run: python3 /root/HermesForge/scripts/embed_vault.py")
        sys.exit(1)

    import chromadb
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(MODEL_NAME)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    col = client.get_collection(COLLECTION)

    # Encode query
    query_embedding = model.encode([query])[0].tolist()

    # Build metadata filter
    where_filters = []
    if concept_type:
        where_filters.append({"concept_type": {"$eq": concept_type}})
    if topic:
        where_filters.append({"topic": {"$contains": topic}})
    if book:
        where_filters.append({"book_slug": {"$eq": book}})

    where = ({"$and": where_filters} if len(where_filters) > 1
             else where_filters[0] if where_filters
             else None)

    kwargs = dict(
        query_embeddings=[query_embedding],
        n_results=limit,
        include=["metadatas", "distances", "documents"],
    )
    if where:
        kwargs["where"] = where

    results = col.query(**kwargs)

    output = []
    for i, (meta, dist, doc) in enumerate(zip(
            results['metadatas'][0],
            results['distances'][0],
            results['documents'][0])):
        similarity = 1.0 - dist  # cosine distance → similarity
        # Extract body preview (first 200 chars of doc after title)
        snippet = doc[100:350].replace('\n', ' ').strip()
        output.append({
            'rank':         i + 1,
            'similarity':   round(similarity, 3),
            'title':        meta.get('title', ''),
            'concept_type': meta.get('concept_type', ''),
            'topic':        meta.get('topic', ''),
            'confidence':   meta.get('confidence', ''),
            'source_page':  meta.get('source_page', ''),
            'source_book':  meta.get('source_book', ''),
            'book_slug':    meta.get('book_slug', ''),
            'filename':     meta.get('filename', ''),
            'filepath':     meta.get('filepath', ''),
            'snippet':      snippet,
        })

    return output


def format_results(results: list[dict], query: str) -> str:
    if not results:
        return f"No semantic results for: '{query}'"

    lines = [f"Semantic search: '{query}' → {len(results)} results\n{'='*60}"]
    for r in results:
        sim_bar = '█' * int(r['similarity'] * 10) + '░' * (10 - int(r['similarity'] * 10))
        lines.append(f"\n[{r['rank']}] {r['title']}  (sim: {r['similarity']:.3f} {sim_bar})")
        lines.append(f"    Type: {r['concept_type']} | Topic: {r['topic']} | Page: {r['source_page']}")
        if r['snippet']:
            lines.append(f"    > {r['snippet'][:200]}...")
        lines.append(f"    File: {r['filename']}")
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('query', help='Natural language query')
    parser.add_argument('--type', dest='concept_type', default='')
    parser.add_argument('--topic', default='')
    parser.add_argument('--book', default='')
    parser.add_argument('--limit', type=int, default=8)
    parser.add_argument('--json', action='store_true', dest='as_json')
    args = parser.parse_args()

    results = semantic_search(
        query=args.query,
        concept_type=args.concept_type,
        topic=args.topic,
        book=args.book,
        limit=args.limit,
    )

    if args.as_json:
        print(json.dumps(results, indent=2))
    else:
        print(format_results(results, args.query))


if __name__ == '__main__':
    main()
