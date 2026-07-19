#!/usr/bin/env python3
"""
Tag vault notes with topic: frontmatter field.
Scans note title slug + body keywords to assign one or more topics.
Safe to re-run — skips notes that already have a topic: field.

Usage:
    python3 tag_vault_topics.py <book_folder>
    python3 tag_vault_topics.py /root/HermesForge/08-Knowledge/Trading-Systems/technical-analysis-financial-markets-murphy
    python3 tag_vault_topics.py --all   # all books under 08-Knowledge/Trading-Systems/
    python3 tag_vault_topics.py --dry-run <book_folder>
"""

import sys, re, argparse
from pathlib import Path
from collections import Counter

# ── Topic taxonomy ────────────────────────────────────────────────────────────
# Each topic: list of slug-fragment keywords (matched against filename stem)
# Order matters: first match wins for primary topic; all matches included
TOPICS = {
    'trend':              ['trend', 'trendline', 'channel', 'fan-principle',
                           'uptrend', 'downtrend', 'speed-line'],
    'support-resistance': ['support', 'resistance', 'role-reversal', 'round-number',
                           'penetration-criterion', 'price-objective'],
    'chart-patterns':     ['head-and-shoulders', 'double-top', 'double-bottom', 'triple-top',
                           'triple-bottom', 'flag', 'pennant', 'wedge', 'rectangle', 'gap',
                           'breakaway', 'exhaustion', 'island-reversal', 'key-reversal',
                           'weekly-reversal', 'broadening', 'ascending-triangle',
                           'descending-triangle', 'symmetrical-triangle', 'triangle',
                           'saucer', 'rounding', 'fulcrum', 'neckline', 'return-move',
                           'measuring-technique', 'price-pattern'],
    'moving-averages':    ['moving-average', 'crossover', 'exponential-smoothing',
                           'double-crossover', 'triple-crossover', 'envelopes',
                           'bollinger', 'keltner', 'price-channel', 'weekly-rule',
                           'starc-band'],
    'oscillators':        ['oscillator', 'momentum', 'rsi', 'macd', 'stochastic', 'roc',
                           'rate-of-change', 'cci', 'williams', 'dmi', 'adx', 'parabolic',
                           'zero-line', 'overbought', 'oversold', 'divergence',
                           'relative-strength-index', 'slow-stochastic', 'fast-stochastic'],
    'volume':             ['volume', 'open-interest', 'obv', 'on-balance', 'money-flow',
                           'demand-index', 'force-index', 'ease-of-movement', 'hpi',
                           'herrick-payoff', 'chaikin'],
    'candlesticks':       ['candlestick', 'candle', 'doji', 'hammer', 'engulf', 'star',
                           'harami', 'morning-star', 'evening-star', 'piercing',
                           'dark-cloud', 'spinning-top', 'marubozu', 'three-methods',
                           'window-candle', 'rising-three', 'falling-three'],
    'elliott-wave':       ['elliott', 'impulse-wave', 'corrective-wave', 'five-wave',
                           'three-wave', 'wave-extension', 'rule-of-alternation',
                           'wave-4', 'wave-3', 'wave-equality'],
    'fibonacci':          ['fibonacci', 'retracement', 'fibonacci-fan', 'golden-ratio',
                           'phi', '0618', '382'],
    'intermarket':        ['intermarket', 'commodity', 'sector-rotation', 'crb',
                           'dollar', 'gold', 'oil', 'bond-stock', 'asset-allocation',
                           'deflationary', 'inflation', 'mutual-fund'],
    'cycles':             ['cycle', 'seasonal', 'presidential', 'kondratieff', 'mesa',
                           'dominant-cycle', 'translation', 'cycle-length', 'trough-to-trough',
                           'january-barometer', '4-year', '54-year'],
    'risk-management':    ['stop', 'money-management', 'reward-to-risk', 'drawdown',
                           'pyramiding', 'position-size', 'protective', 'trailing',
                           'capital-limit', 'margin', 'losing-trade', 'winning-streak',
                           'let-profits', 'cut-losses', 'exit-design', 'multiple-positions',
                           'risk-per-trade', 'maximum-risk', 'equity-curve'],
    'point-and-figure':   ['point-and-figure', 'pf-', 'box-reversal', 'horizontal-count',
                           'vertical-count', '3-box', '1-box', 'box-size', 'catapult',
                           'bullish-signal', 'bearish-signal'],
    'market-breadth':     ['breadth', 'advance-decline', 'mcclellan', 'new-high', 'new-low',
                           'arms-index', 'trin', 'tick', 'summation', 'ad-line',
                           'put-call', 'short-interest', 'insider'],
    'system-design':      ['system', 'backtesting', 'robustness', 'parameter', 'walk-forward',
                           'optimization', 'objective-rules', '5-step', 'trading-idea',
                           'false-signal', 'whipsaw', 'transaction-cost'],
    'dow-theory':         ['dow-theory', 'dow-averages', 'dow-tenet', 'primary-trend',
                           'secondary-trend', 'dow-confirmation', 'dow-divergence',
                           'industrial-average', 'transport-average'],
    'market-psychology':  ['contrary-opinion', 'sentiment', 'psychology', 'behavioral',
                           'strong-hands', 'weak-hands', 'panic', 'commitment-of-traders',
                           'cot-report', 'speculator', 'hedger'],
    'relative-strength':  ['relative-strength-analysis', 'rs-line', 'ratio-chart',
                           'sector-rs', 'stock-rs'],
    'chart-construction': ['chart-construction', 'bar-chart', 'arithmetic-scale',
                           'logarithmic-scale', 'price-scale', 'weekly-chart', 'monthly-chart',
                           'long-term-chart', 'continuation-chart', 'perpetual-contract',
                           'daily-chart', 'intraday-chart', 'open-high-low', 'candlestick-chart',
                           'equivolume', 'kagi', 'renko', 'three-line-break'],
    'market-profile':     ['market-profile', 'tpo', 'time-price-opportunity', 'value-area',
                           'market-balance', 'single-print', 'range-extension', 'extremes-formation',
                           'point-of-control', 'buying-count', 'selling-count'],
    'general-principles': ['philosophy', 'three-premises', 'definition-of-technical',
                           'three-elements', 'universality', 'flexibility', 'adaptability',
                           'successful-trading', 'checklist', 'keys-to', 'top-down',
                           'market-action-discounts', 'prices-move-in-trends',
                           'history-repeats', 'technical-vs-fundamental'],
    'program-trading':    ['program-trading', 'sp-500-futures', 'fair-value', 'premium-narrows',
                           'cash-futures', 'index-arbitrage'],
}

# Fallback for completely uncategorised notes
FALLBACK_TOPIC = 'general'


def classify_note(filepath: Path) -> list[str]:
    """Return list of topics for this note based on filename + first 400 chars of body."""
    stem = filepath.stem.lower()
    # Strip prefix (C001-, RG003-, EN012-, etc.)
    slug = re.sub(r'^[a-z]+\d+-', '', stem)

    content = filepath.read_text(encoding='utf-8')
    # Also scan first 300 chars of body text (after frontmatter)
    fm_end = content.find('---', 3)
    body_preview = content[fm_end+3:fm_end+400].lower() if fm_end > 0 else ''

    search_text = slug + ' ' + body_preview

    matched = []
    for topic, keywords in TOPICS.items():
        if any(kw in search_text for kw in keywords):
            matched.append(topic)

    return matched if matched else [FALLBACK_TOPIC]


def tag_note(filepath: Path, topics: list[str], dry_run: bool = False) -> bool:
    """Insert topic: field into frontmatter. Returns True if modified."""
    content = filepath.read_text(encoding='utf-8')

    # Skip if already tagged
    if 'topic:' in content[:400]:
        return False

    # Find insertion point: after confidence: line, or before ingested_at:
    topic_yaml = f"topic: [{', '.join(topics)}]"

    # Insert after confidence: line
    new_content = re.sub(
        r'(confidence:\s*\S+)',
        r'\1\n' + topic_yaml,
        content,
        count=1
    )

    if new_content == content:
        # Fallback: insert before ingested_at:
        new_content = content.replace(
            'ingested_at:',
            topic_yaml + '\ningested_at:',
            1
        )

    if new_content == content:
        return False  # Couldn't insert

    if not dry_run:
        filepath.write_text(new_content, encoding='utf-8')
    return True


def process_book(book_dir: Path, dry_run: bool = False) -> dict:
    notes = [f for f in book_dir.rglob('*.md') if f.name != '00-Literature-Note.md']
    print(f"\nProcessing: {book_dir.name} ({len(notes)} notes)")

    topic_counter = Counter()
    modified = 0
    skipped = 0

    for note in notes:
        topics = classify_note(note)
        changed = tag_note(note, topics, dry_run=dry_run)
        if changed:
            modified += 1
            for t in topics:
                topic_counter[t] += 1
        else:
            skipped += 1

    print(f"  {'[DRY RUN] ' if dry_run else ''}Tagged: {modified} | Already tagged / skipped: {skipped}")
    print(f"  Topic distribution:")
    for topic, count in topic_counter.most_common():
        print(f"    {topic:25s}: {count}")

    return {'modified': modified, 'skipped': skipped, 'topics': dict(topic_counter)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('book_dir', nargs='?', help='Path to book folder')
    parser.add_argument('--all', action='store_true', help='Process all books under 08-Knowledge/Trading-Systems/')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    base = Path('/root/HermesForge/08-Knowledge/Trading-Systems')

    if args.all:
        book_dirs = [d for d in base.iterdir() if d.is_dir()]
    elif args.book_dir:
        book_dirs = [Path(args.book_dir)]
    else:
        print("Usage: tag_vault_topics.py <book_folder> | --all [--dry-run]")
        sys.exit(1)

    total_modified = 0
    for bd in book_dirs:
        result = process_book(bd, dry_run=args.dry_run)
        total_modified += result['modified']

    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Total notes tagged: {total_modified}")
    if args.dry_run:
        print("Re-run without --dry-run to apply changes.")


if __name__ == '__main__':
    main()
