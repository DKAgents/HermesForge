#!/usr/bin/env python3
"""
HermesForge Novel Connection Discovery Engine
==============================================
Searches for non-obvious, high-value connections across the vault knowledge base.

Pipeline:
  1. Load seed prompts from discovery_seeds.yaml
  2. For each seed: run FTS + semantic search → collect candidate note pairs
  3. Cross-cluster filter: deprioritize same-subfolder pairs (obvious), elevate cross-domain pairs
  4. LLM synthesis: T2 model evaluates each candidate group for actionability
  5. Write accepted insights (actionability ≥ 3) to 08-Knowledge/Insights/
  6. Write weekly discovery report to 04-ForgeLoop/Discovery/

Usage:
    python3 discover_connections.py                         # full weekly run
    python3 discover_connections.py --dry-run               # no writes, show candidates
    python3 discover_connections.py --seed vol_confirm_risk # single seed
    python3 discover_connections.py --limit 5               # cap LLM calls (cost control)
    python3 discover_connections.py --force                 # re-process existing insights
"""

import sys, os, re, json, argparse, math, hashlib, subprocess
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

# Load .env so OPENROUTER_API_KEY is available
env_file = Path.home() / '.hermes' / '.env'
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            if k.strip() and k.strip() not in os.environ:
                os.environ[k.strip()] = v.strip()

import yaml  # after env load

VAULT_ROOT   = Path('/root/HermesForge')
SCRIPTS_DIR  = VAULT_ROOT / 'scripts'
INSIGHTS_DIR = VAULT_ROOT / '08-Knowledge' / 'Insights'
DISCOVERY_DIR = VAULT_ROOT / '04-ForgeLoop' / 'Discovery'
INDEX_DIR    = Path('/root/.hermes/vault_index')
SEEDS_FILE   = SCRIPTS_DIR / 'discovery_seeds.yaml'
STATE_FILE   = INDEX_DIR / 'discovery_state.json'

OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions'
LLM_MODEL    = 'anthropic/claude-sonnet-4.6'
MAX_TOKENS   = 1200
DEDUP_SIMILARITY_THRESHOLD = 0.85  # skip if existing insight is this similar to new one
ACTIONABILITY_MIN = 3              # write to vault only if score >= this


# ── LLM call ─────────────────────────────────────────────────────────────────

def llm_call(messages: list[dict], max_tokens: int = MAX_TOKENS) -> str:
    """Call LLM via Headroom proxy. Returns content string."""
    import urllib.request
    api_key = os.environ.get('OPENROUTER_API_KEY', '')
    payload = json.dumps({
        'model': LLM_MODEL,
        'messages': messages,
        'max_tokens': max_tokens,
    }).encode()
    req = urllib.request.Request(
        OPENROUTER_URL,
        data=payload,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
            return data['choices'][0]['message']['content']
    except Exception as e:
        return f'ERROR: {e}'


# ── search helpers ────────────────────────────────────────────────────────────

def _normalize_result(r: dict) -> dict:
    """Normalize result dicts so 'path' key is always present."""
    # search_vault.py uses 'filepath'; semantic_search.py uses 'file'
    if 'path' not in r:
        r['path'] = r.get('filepath') or r.get('file', '')
    return r


def fts_search(query: str, limit: int = 8) -> list[dict]:
    """Run FTS search via search_vault.py, return list of result dicts."""
    cmd = [sys.executable, str(SCRIPTS_DIR / 'search_vault.py'), query,
           '--limit', str(limit), '--json']
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if r.returncode == 0 and r.stdout.strip():
            return [_normalize_result(x) for x in json.loads(r.stdout)]
        return []
    except Exception:
        return []


def semantic_search(query: str, limit: int = 8) -> list[dict]:
    """Run semantic search via semantic_search.py, return list of result dicts."""
    cmd = [sys.executable, str(SCRIPTS_DIR / 'semantic_search.py'), query,
           '--limit', str(limit), '--json']
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if r.returncode == 0 and r.stdout.strip():
            return [_normalize_result(x) for x in json.loads(r.stdout)]
        return []
    except Exception:
        return []


def read_note_body(path_str: str) -> str:
    """Read a note's body (strip frontmatter)."""
    try:
        text = Path(path_str).read_text(encoding='utf-8', errors='replace')
        parts = re.split(r'^---\s*$', text, maxsplit=2, flags=re.MULTILINE)
        return parts[2].strip() if len(parts) >= 3 else text.strip()
    except Exception:
        return ''


def note_domain(path_str: str) -> str:
    """Infer domain from note path."""
    p = path_str.lower()
    if '/indicators/' in p:  return 'indicators'
    if '/patterns/' in p:    return 'patterns'
    if '/rules/' in p:       return 'rules'
    if '/risk-guidelines/' in p: return 'risk-guidelines'
    if '/edge-conditions/' in p: return 'edge-conditions'
    if '/concepts/' in p:    return 'concepts'
    if '07-risk' in p:       return 'risk'
    if '05-research' in p:   return 'research'
    if '06-strategies' in p: return 'strategies'
    return 'general'


# ── dedup check ───────────────────────────────────────────────────────────────

def tokenize(text: str) -> dict:
    tokens = re.findall(r'\b[a-z]{3,}\b', text.lower())
    tf = defaultdict(int)
    for t in tokens:
        tf[t] += 1
    total = len(tokens) or 1
    return {t: c/total for t, c in tf.items()}


def cosine(a: dict, b: dict) -> float:
    common = set(a) & set(b)
    if not common: return 0.0
    dot = sum(a[t]*b[t] for t in common)
    na = math.sqrt(sum(v*v for v in a.values()))
    nb = math.sqrt(sum(v*v for v in b.values()))
    if na == 0 or nb == 0: return 0.0
    return dot / (na * nb)


def is_duplicate_insight(title: str, synthesis: str) -> bool:
    """Check if a very similar insight already exists in the Insights folder."""
    if not INSIGHTS_DIR.exists():
        return False
    candidate_vec = tokenize(title + ' ' + synthesis)
    for existing in INSIGHTS_DIR.rglob('*.md'):
        body = read_note_body(str(existing))
        existing_vec = tokenize(body)
        sim = cosine(candidate_vec, existing_vec)
        if sim >= DEDUP_SIMILARITY_THRESHOLD:
            return True
    return False


# ── state management ──────────────────────────────────────────────────────────

def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {'processed_seeds': {}, 'insight_count': 0}


def save_state(state: dict):
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


# ── insight writer ────────────────────────────────────────────────────────────

def write_insight(insight: dict, dry_run: bool) -> str:
    """Write an insight note to vault. Returns the path."""
    INSIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    # Sanitize title for filename
    slug = re.sub(r'[^a-z0-9]+', '-', insight['title'].lower()).strip('-')[:60]
    fname = INSIGHTS_DIR / f"INS-{today}-{slug}.md"

    sources_links = '\n'.join(f'- [[{Path(s).stem}]]' for s in insight['source_notes'])
    domains_str = ', '.join(sorted(set(insight['domains'])))

    content = f"""---
type: insight
date: {today}
actionability: {insight['actionability']}
connection_type: {insight['connection_type']}
domains: [{domains_str}]
sources: {json.dumps([Path(s).stem for s in insight['source_notes']])}
seed_id: {insight['seed_id']}
tags: [insight, discovery, knowledge-evolution]
---

# {insight['title']}

## Discovery Summary

{insight['synthesis']}

## Trading Implication

{insight['trading_implication']}

## Supporting Notes

{sources_links}

## Connection Type

**{insight['connection_type']}** — Actionability score: {insight['actionability']}/5
"""
    if not dry_run:
        fname.write_text(content)
        # AC6: check if any existing strategy should be updated with this insight
        _check_strategy_updates(insight, str(fname))
    return str(fname)


def _check_strategy_updates(insight: dict, insight_path: str):
    """If insight is semantically close to a strategy thesis, write a pending-update suggestion."""
    STRATEGIES_DIR = VAULT_ROOT / '06-Strategies'
    PENDING_DIR    = STRATEGIES_DIR / 'Pending-Updates'
    STRATEGY_DIRS_LOCAL  = [STRATEGIES_DIR / 'Active', STRATEGIES_DIR / 'Hypotheses']
    SIMILARITY_THRESHOLD = 0.70

    insight_vec = tokenize(insight['title'] + ' ' + insight['synthesis'])

    for sdir in STRATEGY_DIRS_LOCAL:
        if not sdir.exists():
            continue
        for strat_file in sdir.glob('*.md'):
            try:
                text = strat_file.read_text(encoding='utf-8', errors='replace')
                m = re.search(r'## Thesis\s*\n(.*?)(?=\n## )', text, re.DOTALL)
                thesis = m.group(1).strip() if m else ''
                if not thesis:
                    continue
                strat_vec = tokenize(thesis)
                sim = cosine(insight_vec, strat_vec)
                if sim >= SIMILARITY_THRESHOLD:
                    PENDING_DIR.mkdir(parents=True, exist_ok=True)
                    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
                    slug = re.sub(r'[^a-z0-9]+', '-', insight['title'].lower()).strip('-')[:40]
                    update_file = PENDING_DIR / f'UPDATE-{today}-{strat_file.stem}-{slug}.md'
                    update_content = f"""---
type: strategy-update-suggestion
strategy: {strat_file.stem}
insight: {Path(insight_path).stem}
similarity: {sim:.3f}
date: {today}
reviewed: false
tags: [pending-update, strategy, knowledge-evolution]
---

# Pending Update: {strat_file.stem}

## Triggering Insight

[[{Path(insight_path).stem}]] — *{insight['title']}* (actionability {insight['actionability']}/5)

**Similarity to strategy thesis:** {sim:.1%}

## Insight Summary

{insight['synthesis']}

## Trading Implication

{insight['trading_implication']}

## Suggested Action

Review whether this insight should be incorporated into [[{strat_file.stem}]]:
- Does it add a new entry/exit condition?
- Does it strengthen or weaken the supporting evidence?
- Should it be linked in `## Supporting Evidence`?

Mark `reviewed: true` in this file's frontmatter once you've made a decision.
"""
                    update_file.write_text(update_content)
                    print(f"    → Pending update written for strategy: {strat_file.name} (sim={sim:.2f})")
            except Exception:
                continue


# ── synthesis prompt ──────────────────────────────────────────────────────────

SYNTHESIS_PROMPT = """You are a systematic trading research analyst reviewing connections between concepts from a technical analysis knowledge base.

I will give you a SET OF RELATED NOTES from different domains of the knowledge base (indicators, patterns, risk guidelines, trading rules, concepts). Your job is to determine if there is a NON-OBVIOUS, ACTIONABLE connection between them that could improve trading performance.

NOTES:
{notes_text}

SEED QUESTION: {seed_description}

Please evaluate this set and respond in STRICT JSON format (no markdown, no commentary outside the JSON):

{{
  "title": "Short title capturing the insight (max 10 words)",
  "connection_type": "one of: confirms_risk_rule | creates_filter | resolves_conflict | reveals_sequence | adds_condition | contradicts_assumption",
  "actionability": <integer 1-5 where 1=theoretical 3=usable 5=immediately tradeable>,
  "synthesis": "2-4 sentence explanation of the connection. Be specific — cite note titles, page numbers, or rule names where possible.",
  "trading_implication": "1-2 sentences: what a trader should DO differently based on this insight",
  "is_trivial": <true if the connection is obvious or already well-known, false if genuinely non-obvious>,
  "domains_connected": ["list", "of", "domains"]
}}

Key rules:
- Score actionability 1-2 if it's just theory. Score 3+ only if it produces a specific decision rule.
- Set is_trivial=true if notes are from the same subfolder or make the same point.
- Do NOT invent information not present in the notes."""


# ── main discovery loop ───────────────────────────────────────────────────────

def run_seed(seed: dict, state: dict, args) -> list[dict]:
    """Run one seed query → search → deduplicate → return candidate groups."""
    sid = seed['id']
    print(f"\n  [{sid}] {seed['query'][:60]}...")

    # Search both FTS and semantic
    fts_results = fts_search(seed['query'], limit=6)
    sem_results = semantic_search(seed['query'], limit=6)

    # Merge and deduplicate by path
    seen_paths = set()
    all_results = []
    for r in fts_results + sem_results:
        path = r.get('path') or r.get('file', '')
        if path and path not in seen_paths:
            seen_paths.add(path)
            all_results.append(r)

    if len(all_results) < 2:
        print(f"    → Only {len(all_results)} results, skipping")
        return []

    # Cross-domain filter: prefer notes from different subfolders
    by_domain = defaultdict(list)
    for r in all_results:
        path = r.get('path') or r.get('file', '')
        by_domain[note_domain(path)].append(r)

    # Build cross-domain groups (note from domain A + note from domain B)
    candidate_groups = []
    domains = list(by_domain.keys())

    if len(domains) >= 2:
        # Cross-domain group: best note from each of up to 3 distinct domains
        cross_notes = []
        for d in domains[:3]:
            cross_notes.append(by_domain[d][0])
        candidate_groups.append(cross_notes)
    else:
        # Same domain — still worth checking if query returned diverse results
        candidate_groups.append(all_results[:3])

    return candidate_groups


def synthesize_group(notes: list[dict], seed: dict, state: dict, dry_run: bool) -> dict | None:
    """Call LLM to synthesize a candidate group. Returns insight dict or None."""
    note_texts = []
    note_paths = []
    for n in notes:
        path = n.get('path') or n.get('file', '')
        if not path:
            continue
        body = read_note_body(path)[:600]  # cap per-note to keep prompt size sane
        title = Path(path).stem
        domain = note_domain(path)
        note_texts.append(f"**[{domain}] {title}**\n{body}")
        note_paths.append(path)

    if len(note_texts) < 2:
        return None

    notes_block = '\n\n---\n\n'.join(note_texts)
    prompt = SYNTHESIS_PROMPT.format(
        notes_text=notes_block,
        seed_description=seed.get('description', seed['query'])
    )

    print(f"    → Calling LLM for {len(note_texts)} notes across domains: {[note_domain(p) for p in note_paths]}")
    response = llm_call([{'role': 'user', 'content': prompt}])

    if response.startswith('ERROR:'):
        print(f"    ✗ LLM error: {response}")
        return None

    # Parse JSON
    try:
        # Strip markdown code fences if present
        raw = re.sub(r'^```(?:json)?\s*', '', response.strip(), flags=re.MULTILINE)
        raw = re.sub(r'\s*```$', '', raw.strip(), flags=re.MULTILINE)
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"    ✗ JSON parse error: {e}")
        print(f"    Response preview: {response[:200]}")
        return None

    if data.get('is_trivial', False):
        print(f"    → Trivial connection, skipping")
        return None

    actionability = int(data.get('actionability', 0))
    title = data.get('title', 'Unnamed Insight')

    print(f"    → '{title}' | actionability={actionability}/5 | type={data.get('connection_type','?')}")

    if actionability < ACTIONABILITY_MIN:
        print(f"    → Below threshold ({ACTIONABILITY_MIN}), not writing to vault")
        return None

    # Dedup check
    if is_duplicate_insight(title, data.get('synthesis', '')):
        print(f"    → Duplicate of existing insight, skipping")
        return None

    return {
        'title': title,
        'connection_type': data.get('connection_type', 'unknown'),
        'actionability': actionability,
        'synthesis': data.get('synthesis', ''),
        'trading_implication': data.get('trading_implication', ''),
        'domains': data.get('domains_connected', [note_domain(p) for p in note_paths]),
        'source_notes': note_paths,
        'seed_id': seed['id'],
    }


# ── report writer ─────────────────────────────────────────────────────────────

def write_report(insights: list[dict], seeds_run: int, total_llm_calls: int, dry_run: bool) -> str:
    DISCOVERY_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    week = now.strftime('%Y-W%U')
    fname = DISCOVERY_DIR / f'Discoveries-{week}.md'

    prefix = '[DRY RUN] ' if dry_run else ''
    date_str = now.strftime('%Y-%m-%d %H:%M UTC')

    if not insights:
        body = '_No new insights discovered this run._'
    else:
        rows = '\n'.join(
            f"| [[{Path(i.get('file', 'unknown')).stem if 'file' in i else i['title'].replace(' ','-')[:40]}\\|{i['title'][:40]}]] "
            f"| {i['actionability']}/5 | {i['connection_type']} | {', '.join(i['domains'][:2])} |"
            for i in sorted(insights, key=lambda x: -x['actionability'])
        )
        body = f"""| Insight | Actionability | Type | Domains |
|---------|---------------|------|---------|
{rows}"""

    content = f"""---
type: discovery-report
week: {week}
date: {date_str}
insights_found: {len(insights)}
seeds_run: {seeds_run}
llm_calls: {total_llm_calls}
tags: [discovery, knowledge-evolution, forge-loop]
---

# {prefix}Discovery Report — {week}

Generated: {date_str}

## Summary

| Metric | Value |
|--------|-------|
| Seeds queried | {seeds_run} |
| LLM synthesis calls | {total_llm_calls} |
| Insights accepted (actionability ≥ {ACTIONABILITY_MIN}) | {len(insights)} |

## New Insights

{body}
"""
    if not dry_run:
        fname.write_text(content)
    return str(fname)


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description='HermesForge Novel Connection Discovery')
    ap.add_argument('--dry-run', action='store_true', help='No vault writes')
    ap.add_argument('--seed', default='', help='Run only this seed ID')
    ap.add_argument('--limit', type=int, default=0,
                    help='Max LLM synthesis calls (0=unlimited)')
    ap.add_argument('--force', action='store_true',
                    help='Re-process seeds even if recently run')
    args = ap.parse_args()

    print(f"\n{'='*60}")
    print(f"  HermesForge Connection Discovery")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"  dry_run={args.dry_run} | seed_filter={args.seed or 'all'} | limit={args.limit or '∞'}")
    print(f"{'='*60}")

    # Load seeds
    seeds_data = yaml.safe_load(SEEDS_FILE.read_text())
    all_seeds = seeds_data.get('seeds', [])

    # AC9: also load lesson-derived seeds from extract_lessons.py
    LESSON_SEEDS = SCRIPTS_DIR / 'lesson_seeds.yaml'
    if LESSON_SEEDS.exists() and not args.seed:
        try:
            lesson_seed_data = yaml.safe_load(LESSON_SEEDS.read_text()) or {}
            lesson_seeds = lesson_seed_data.get('lesson_seeds', [])
            if lesson_seeds:
                print(f"  Loading {len(lesson_seeds)} lesson-derived seed(s) from {LESSON_SEEDS.name}")
                all_seeds = all_seeds + lesson_seeds
        except Exception as e:
            print(f"  Warning: could not load lesson seeds: {e}")

    if args.seed:
        all_seeds = [s for s in all_seeds if s['id'] == args.seed]
        if not all_seeds:
            print(f"ERROR: seed '{args.seed}' not found in {SEEDS_FILE}")
            sys.exit(1)

    # Sort by priority
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    all_seeds.sort(key=lambda s: priority_order.get(s.get('priority', 'medium'), 1))

    state = load_state()
    insights_written = []
    total_llm_calls = 0
    seeds_run = 0

    for seed in all_seeds:
        if args.limit and total_llm_calls >= args.limit:
            print(f"\n  Reached LLM call limit ({args.limit}), stopping.")
            break

        # Gather candidates
        candidate_groups = run_seed(seed, state, args)
        seeds_run += 1

        for group in candidate_groups:
            if args.limit and total_llm_calls >= args.limit:
                break

            insight = synthesize_group(group, seed, state, args.dry_run)
            total_llm_calls += 1

            if insight:
                path = write_insight(insight, args.dry_run)
                insight['file'] = path
                insights_written.append(insight)
                print(f"    ✅ Insight written: {Path(path).name}")

    # Write report
    report_path = write_report(insights_written, seeds_run, total_llm_calls, args.dry_run)

    # Update state
    if not args.dry_run:
        state['insight_count'] = state.get('insight_count', 0) + len(insights_written)
        state['last_run'] = datetime.now(timezone.utc).isoformat()
        save_state(state)

    # Final summary
    print(f"\n{'='*60}")
    prefix = '[DRY RUN] ' if args.dry_run else ''
    status = '✅' if insights_written else '🔍'
    print(f"{status} {prefix}Discovery Complete")
    print(f"• Seeds queried    : {seeds_run}")
    print(f"• LLM calls made   : {total_llm_calls}")
    print(f"• Insights accepted: {len(insights_written)}")
    if insights_written:
        print(f"• Top insights:")
        for ins in sorted(insights_written, key=lambda x: -x['actionability'])[:3]:
            print(f"    [{ins['actionability']}/5] {ins['title']}")
    print(f"• Report: {report_path}")
    print(f"{'='*60}\n")

    return {
        'seeds_run': seeds_run,
        'llm_calls': total_llm_calls,
        'insights': len(insights_written),
        'insight_details': [{'title': i['title'], 'actionability': i['actionability']} for i in insights_written],
    }


if __name__ == '__main__':
    main()
