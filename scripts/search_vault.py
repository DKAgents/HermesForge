#!/usr/bin/env python3
"""
Search the vault FTS5 index with synonym/query expansion.
Returns ranked results with snippet highlights.

Query expansion: common trading terms are automatically expanded to synonyms
so conceptual queries match notes even when exact words differ.

Usage:
    python3 search_vault.py "support resistance role reversal"
    python3 search_vault.py "rsi divergence" --type rule --limit 10
    python3 search_vault.py "stop placement" --topic risk-management
    python3 search_vault.py "trend" --book technical-analysis-financial-markets-murphy
    python3 search_vault.py "oscillator" --type entry-criteria --json
    python3 search_vault.py "key principles of trend analysis" --expand  (show expanded query)
"""

import sqlite3, sys, re, json, argparse
from pathlib import Path

INDEX_PATH = Path('/root/.hermes/vault_index/vault.db')

# ── Synonym / query expansion taxonomy ───────────────────────────────────────
# Each entry: (trigger_words, expansion_terms)
# trigger_words: if ANY appears in query, add expansion_terms to the FTS query
# expansion_terms: additional OR terms added to the FTS match expression
#
# To add new synonyms: append a tuple to SYNONYM_GROUPS below.

SYNONYM_GROUPS = [
    # Trend
    ({"trend"},
     ["trend", "trendline", "uptrend", "downtrend", "trending", "trend-following",
      "trend direction", "major trend", "primary trend", "secondary trend"]),

    # Breakout
    ({"breakout", "break out", "breaking out"},
     ["breakout", "breaks out", "upside break", "downside break",
      "penetration", "close beyond", "exceeded", "violated"]),

    # Volume
    ({"volume"},
     ["volume", "trading activity", "heavy volume", "light volume",
      "volume surge", "volume confirmation", "volume expansion",
      "open interest"]),

    # Support / Resistance
    ({"support"},
     ["support", "support level", "buying area", "floor", "demand zone",
      "support zone", "support and resistance"]),

    ({"resistance"},
     ["resistance", "resistance level", "selling area", "ceiling",
      "supply zone", "resistance zone", "support and resistance"]),

    # Stops
    ({"stop"},
     ["stop", "stop loss", "protective stop", "stop placement",
      "stop order", "trailing stop", "sell stop", "buy stop",
      "stop-loss", "exit", "protect"]),

    # Pattern
    ({"pattern"},
     ["pattern", "chart pattern", "price pattern", "formation",
      "reversal pattern", "continuation pattern", "setup"]),

    # Moving averages
    ({"moving average", "ma ", " ma", "ema", "sma"},
     ["moving average", "crossover", "exponential", "simple moving",
      "double crossover", "triple crossover", "200-day", "50-day", "20-day"]),

    # Oscillators
    ({"oscillator", "momentum"},
     ["oscillator", "momentum", "overbought", "oversold",
      "divergence", "zero line", "signal line"]),

    # RSI
    ({"rsi"},
     ["RSI", "relative strength index", "overbought", "oversold", "divergence"]),

    # MACD
    ({"macd"},
     ["MACD", "moving average convergence", "signal line", "histogram",
      "crossover", "divergence"]),

    # Stochastic
    ({"stochastic"},
     ["stochastic", "stochastics", "percent K", "percent D",
      "overbought", "oversold", "slow stochastic"]),

    # Fibonacci
    ({"fibonacci", "fib", "retracement"},
     ["fibonacci", "retracement", "38.2", "50", "61.8",
      "golden ratio", "fan", "arc"]),

    # Divergence
    ({"divergence"},
     ["divergence", "diverge", "bearish divergence", "bullish divergence",
      "negative divergence", "positive divergence", "failure swing"]),

    # Confirmation
    ({"confirm", "confirmation"},
     ["confirmation", "confirmed", "validates", "valid", "validates",
      "close beyond", "two-day rule", "filter"]),

    # Entry
    ({"entry", "enter"},
     ["entry", "enter", "buy signal", "sell signal", "breakout",
      "completion signal", "trigger", "initiate"]),

    # Risk / money management
    ({"risk", "money management", "position size"},
     ["risk", "money management", "position size", "reward",
      "maximum loss", "capital", "commitment", "drawdown"]),

    # Trend reversal
    ({"reversal"},
     ["reversal", "reverse", "reversing", "reversal signal",
      "trend change", "top", "bottom", "turning point"]),

    # Principle / rule
    ({"principle", "rule", "tenet"},
     ["principle", "rule", "tenet", "guideline", "criterion",
      "law", "axiom", "established"]),
]


def _fts_safe(term: str) -> str:
    """Make a term safe for FTS5: quote multi-word, escape special chars."""
    # Remove characters that break FTS5 (hyphens in multi-word, slashes, etc.)
    term = re.sub(r'[^a-zA-Z0-9\s%]', ' ', term).strip()
    term = re.sub(r'\s+', ' ', term)
    if not term:
        return ''
    if ' ' in term:
        return f'"{term}"'
    return term


def expand_query(query: str, verbose: bool = False) -> str:
    """
    Expand a natural language query using synonym groups.

    Strategy: for each synonym group that is triggered, replace the ORIGINAL
    trigger word(s) in the query with an OR clause of synonyms, rather than
    appending all synonyms to every word in the query.

    This keeps the FTS5 expression focused and avoids combinatorial explosion.
    """
    query_lower = query.lower()
    matched_groups = []

    for triggers, expansions in SYNONYM_GROUPS:
        if any(trig in query_lower for trig in triggers):
            matched_groups.append((triggers, expansions))

    if not matched_groups:
        return query

    # Build a focused OR-expanded query:
    # Take the original meaningful words (not stopwords) and OR-expand each
    # that matches a synonym group. Non-matching words are kept as AND context.
    stopwords = {'the', 'a', 'an', 'and', 'of', 'in', 'for', 'to', 'on',
                 'by', 'as', 'at', 'or', 'with', 'how', 'should', 'what',
                 'when', 'key', 'principles', 'rules', 'analysis', 'trading',
                 'from', 'their', 'using', 'be', 'is', 'are', 'were'}

    # Collect all expansion terms from matched groups (flat, deduplicated)
    all_expansion_terms = []
    seen = set()
    for _, expansions in matched_groups:
        for term in expansions:
            safe = _fts_safe(term)
            if safe and safe.lower() not in seen:
                seen.add(safe.lower())
                all_expansion_terms.append(safe)

    # Keep original meaningful words from query as anchor terms
    orig_meaningful = [w for w in re.findall(r'\b[a-zA-Z]{3,}\b', query)
                       if w.lower() not in stopwords]

    # Build: (orig_word1 OR orig_word2 OR ...) in FTS5 context
    # The safest FTS5 approach: run original query first, augment with synonyms as OR group
    orig_safe = [_fts_safe(w) for w in orig_meaningful if _fts_safe(w)]

    if not orig_safe and not all_expansion_terms:
        return query

    # Combine: (original_content_words) OR (synonym_terms)
    # FTS5 OR is written as: term1 OR term2 OR term3
    combined = list(dict.fromkeys(orig_safe + all_expansion_terms))  # dedup, order preserved
    # Limit to 20 terms to avoid FTS5 performance issues
    combined = combined[:20]

    expanded = ' OR '.join(combined)

    if verbose:
        print(f"[Query expansion] Original: '{query}'")
        print(f"[Query expansion] Matched groups: {len(matched_groups)}")
        print(f"[Query expansion] FTS5 expression ({len(combined)} terms): {expanded[:120]}{'...' if len(expanded) > 120 else ''}")

    return expanded


def search(query: str, concept_type: str = "", topic: str = "",
           book: str = "", limit: int = 10, confidence: str = "",
           expand: bool = True, verbose: bool = False) -> list[dict]:
    if not INDEX_PATH.exists():
        print(f"ERROR: Index not found at {INDEX_PATH}")
        print("Run: python3 /root/HermesForge/scripts/build_index.py")
        sys.exit(1)

    conn = sqlite3.connect(str(INDEX_PATH))
    conn.row_factory = sqlite3.Row

    # Expand query
    fts_query = expand_query(query, verbose=verbose) if expand else query

    where_clauses = ["notes.id = notes_fts.rowid"]
    params: list = [fts_query]

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
    except sqlite3.OperationalError as e:
        if verbose:
            print(f"[FTS5 error] {e} — falling back to safe query")
        # Escape special chars and retry without expansion
        safe_query = re.sub(r'[^\w\s]', ' ', query)
        params[0] = safe_query
        try:
            rows = conn.execute(sql, params).fetchall()
        except sqlite3.OperationalError:
            conn.close()
            return []

    conn.close()
    return [dict(r) for r in rows]


def format_results(results: list[dict], query: str, expanded: bool = True) -> str:
    if not results:
        return f"No results for: '{query}'"

    label = f"Search: '{query}' (with synonym expansion)" if expanded else f"Search: '{query}'"
    lines = [f"{label} → {len(results)} results\n{'='*60}"]
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
    parser.add_argument('query', help='Search query (natural language or keywords)')
    parser.add_argument('--type', dest='concept_type', default='', help='Filter by concept_type')
    parser.add_argument('--topic', default='', help='Filter by topic (partial match)')
    parser.add_argument('--book', default='', help='Filter by book slug')
    parser.add_argument('--confidence', default='', choices=['', 'high', 'low'])
    parser.add_argument('--limit', type=int, default=10)
    parser.add_argument('--no-expand', action='store_true',
                        help='Disable synonym expansion (use exact keywords only)')
    parser.add_argument('--expand', action='store_true',
                        help='Show expansion details')
    parser.add_argument('--json', action='store_true', dest='as_json',
                        help='Output raw JSON (for programmatic use)')
    args = parser.parse_args()

    use_expand = not args.no_expand
    results = search(
        query=args.query,
        concept_type=args.concept_type,
        topic=args.topic,
        book=args.book,
        limit=args.limit,
        confidence=args.confidence,
        expand=use_expand,
        verbose=args.expand,
    )

    if args.as_json:
        print(json.dumps(results, indent=2))
    else:
        print(format_results(results, args.query, expanded=use_expand))


if __name__ == '__main__':
    main()
