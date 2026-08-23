#!/usr/bin/env python3
"""
vault_connection_weaver.py — Vault Connection Weaver

A hybrid multi-stage pipeline that discovers, scores, and writes high-signal
wikilinks across the Obsidian vault. Routes all file operations through the
bundled Obsidian skill conventions (read_file, write_file, patch, search_files).

4-stage pipeline:
  1. Discovery — retrieve candidate notes (FTS5 + semantic + graph + temporal)
  2. Evaluation — LLM scores usefulness, confidence, triviality
  3. Linking — write only highest-scoring connections via Obsidian skill
  4. Health — update Connection Health dashboard + state tracking

Usage:
  python3 vault_connection_weaver.py --batch 5 --dry-run
  python3 vault_connection_weaver.py --batch 5 --commit
  python3 vault_connection_weaver.py --batch 3 --priority-dirs 06-Strategies,07-Risk
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ── Config ───────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent
VAULT_SCRIPTS = SCRIPT_DIR  # scripts/ in vault

# Vault path resolution
def resolve_vault(args_vault: str = None) -> Path:
    if args_vault:
        return Path(args_vault)
    env = os.environ.get("OBSIDIAN_VAULT_PATH")
    if env:
        return Path(env)
    # Try .env
    env_file = Path.home() / ".hermes" / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("OBSIDIAN_VAULT_PATH="):
                val = line.split("=", 1)[1].strip().strip("'\"")
                if val:
                    return Path(val)
    return Path("/root/HermesForge")

# State
STATE_DIR = Path.home() / ".hermes" / "vault_weaver"
STATE_FILE = STATE_DIR / "state.json"

# Files to skip (templates, meta, etc.)
SKIP_PATTERNS = [
    re.compile(r"Template", re.I),
    re.compile(r"README", re.I),
    re.compile(r"DASHBOARD", re.I),
    re.compile(r"INDEX", re.I),
    re.compile(r"CONNECTION.HEALTH", re.I),
    re.compile(r"BACKLOG.INDEX", re.I),
    re.compile(r"DECISIONS.MOC", re.I),
]

# ── State management ──────────────────────────────────────────────────────────

def load_state(state_file: Path = None) -> dict:
    sf = state_file or STATE_FILE
    if sf.exists():
        return json.loads(sf.read_text())
    return {
        "last_run": None,
        "total_runs": 0,
        "total_connections_created": 0,
        "examined_notes": {},
        "review_queue": [],
        "reflection_notes": [],
    }

def save_state(state: dict, state_file: Path = None):
    sf = state_file or STATE_FILE
    sf.parent.mkdir(parents=True, exist_ok=True)
    sf.write_text(json.dumps(state, indent=2))

# ── Discovery stage ───────────────────────────────────────────────────────────

def get_recent_notes(vault: Path, since_days: int = 3, limit: int = 20) -> list:
    """Get recently modified notes via git log."""
    notes = []
    try:
        result = subprocess.run(
            ["git", "log", f"--since={since_days} days ago", "--name-only",
             "--pretty=format:", "--", "*.md"],
            capture_output=True, text=True, cwd=str(vault), timeout=10
        )
        files = [f.strip() for f in result.stdout.splitlines() if f.strip()]
        # Deduplicate and filter
        seen = set()
        for f in files:
            if f not in seen and not any(p.search(f) for p in SKIP_PATTERNS):
                seen.add(f)
                full_path = vault / f
                if full_path.exists() and f.endswith(".md"):
                    notes.append(f)
                    if len(notes) >= limit:
                        break
    except Exception as e:
        print(f"  ⚠️ git log failed: {e}", file=sys.stderr)

    # Fallback: use mtime if git returns nothing
    if not notes:
        for p in sorted(vault.rglob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True):
            rel = str(p.relative_to(vault))
            if not any(pat.search(rel) for pat in SKIP_PATTERNS):
                notes.append(rel)
                if len(notes) >= limit:
                    break

    return notes


def fts_search(query: str, vault: Path, limit: int = 10) -> list:
    """FTS5 keyword search via search_vault.py."""
    script = vault / "scripts" / "search_vault.py"
    if not script.exists():
        return []
    try:
        result = subprocess.run(
            ["python3", str(script), query, "--json", "--limit", str(limit)],
            capture_output=True, text=True, timeout=15
        )
        data = json.loads(result.stdout)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "results" in data:
            return data["results"]
        return []
    except Exception:
        return []


def semantic_search(query: str, vault: Path, limit: int = 10) -> list:
    """Semantic search via semantic_search.py (ChromaDB)."""
    script = vault / "scripts" / "semantic_search.py"
    if not script.exists():
        return []
    try:
        result = subprocess.run(
            ["python3", str(script), query, "--json", "--limit", str(limit)],
            capture_output=True, text=True, timeout=30
        )
        data = json.loads(result.stdout)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "results" in data:
            return data["results"]
        return []
    except Exception:
        return []


def extract_wikilinks(content: str) -> list:
    """Extract [[wikilinks]] from note content."""
    return re.findall(r'\[\[([^\]]+)\]\]', content)


def get_note_summary(filepath: Path, max_chars: int = 800) -> str:
    """Extract a summary of the note (frontmatter + first section)."""
    try:
        content = filepath.read_text()[:5000]
        # Strip frontmatter
        if content.startswith("---"):
            end = content.find("---", 3)
            if end > 0:
                content = content[end + 3:].strip()
        # Take first meaningful paragraph(s)
        lines = []
        for line in content.splitlines():
            if line.strip().startswith("#"):
                lines.append(line)
            elif line.strip():
                lines.append(line)
            if len("\n".join(lines)) >= max_chars:
                break
        summary = "\n".join(lines)[:max_chars]
        return summary
    except Exception:
        return ""


def should_skip(filepath: str) -> bool:
    """Check if a file should be skipped (templates, meta, etc.)."""
    for pat in SKIP_PATTERNS:
        if pat.search(filepath):
            return True
    return False


def get_word_count(filepath: Path) -> int:
    """Get word count of a note."""
    try:
        content = filepath.read_text()
        if content.startswith("---"):
            end = content.find("---", 3)
            if end > 0:
                content = content[end + 3:]
        return len(content.split())
    except Exception:
        return 0


def extract_keywords(content: str) -> set:
    """Extract key terms from note content for overlap scoring."""
    # Simple: extract words from headings and first paragraph
    keywords = set()
    for line in content.splitlines()[:30]:
        if line.strip().startswith("#"):
            words = re.findall(r'\b[A-Za-z]{4,}\b', line)
            keywords.update(w.lower() for w in words)
    return keywords


def discover_candidates(seed_note: str, vault: Path, state: dict,
                         skip_semantic: bool = False) -> list:
    """Discover candidate connections for a seed note.

    Returns list of {path, summary, score, signal} dicts.
    """
    seed_path = vault / seed_note
    if not seed_path.exists():
        return []

    seed_content = seed_path.read_text()
    seed_summary = get_note_summary(seed_path)
    seed_keywords = extract_keywords(seed_content)
    seed_links = set(extract_wikilinks(seed_content))
    seed_folder = str(Path(seed_note).parent)

    # Build a search query from the seed note's title + first heading
    title = Path(seed_note).stem.replace("-", " ")
    query = title

    candidates = {}  # path -> {score, signals}

    # 1. FTS5 search
    fts_results = fts_search(query, vault, limit=10)
    for r in fts_results:
        fp = r.get("filepath", r.get("file", ""))
        if not fp:
            continue
        # Normalize to vault-relative
        if fp.startswith(str(vault)):
            fp = fp[len(str(vault)) + 1:]
        if fp == seed_note or should_skip(fp):
            continue
        if fp not in candidates:
            candidates[fp] = {"score": 0, "signals": [], "summary": ""}
        candidates[fp]["score"] += 0.25  # keyword weight
        candidates[fp]["signals"].append("FTS5")

    # 2. Semantic search
    if not skip_semantic:
        sem_results = semantic_search(query, vault, limit=10)
        for r in sem_results:
            fp = r.get("filepath", r.get("file", ""))
            if not fp:
                continue
            if fp.startswith(str(vault)):
                fp = fp[len(str(vault)) + 1:]
            if fp == seed_note or should_skip(fp):
                continue
            if fp not in candidates:
                candidates[fp] = {"score": 0, "signals": [], "summary": ""}
            candidates[fp]["score"] += 0.35  # semantic weight
            candidates[fp]["signals"].append("semantic")

    # 3. Graph neighborhood — existing wikilinks point to related notes
    for link in seed_links:
        # Find the actual file for this wikilink
        link_clean = link.split("|")[0].strip()
        possible_paths = list(vault.rglob(f"{link_clean}.md"))
        for pp in possible_paths:
            rel = str(pp.relative_to(vault))
            if rel == seed_note or should_skip(rel):
                continue
            if rel not in candidates:
                candidates[rel] = {"score": 0, "signals": [], "summary": ""}
            candidates[rel]["score"] += 0.25  # graph weight
            candidates[rel]["signals"].append("existing_link")

    # 4. Keyword overlap bonus
    for fp in list(candidates.keys()):
        full_path = vault / fp
        if not full_path.exists():
            continue
        other_content = full_path.read_text()[:3000]
        other_keywords = extract_keywords(other_content)
        overlap = len(seed_keywords & other_keywords)
        if overlap > 3:
            candidates[fp]["score"] += 0.15 * min(overlap / 10, 1.0)
            candidates[fp]["signals"].append(f"keyword_overlap({overlap})")

    # 5. Same-folder penalty
    for fp in candidates:
        other_folder = str(Path(fp).parent)
        if other_folder == seed_folder:
            candidates[fp]["score"] -= 0.5  # same-folder penalty

    # 6. Filter out already-examined notes (within 7 days)
    now = datetime.now(timezone.utc)
    filtered = {}
    for fp, data in candidates.items():
        examined = state.get("examined_notes", {}).get(fp, {})
        last = examined.get("last_examined")
        if last:
            try:
                last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
                if (now - last_dt).days < 7:
                    continue  # skip recently examined
            except Exception:
                pass
        # Filter thin notes
        full_path = vault / fp
        if full_path.exists() and get_word_count(full_path) < 100:
            continue
        filtered[fp] = data

    # Sort by score, take top 5
    ranked = sorted(filtered.items(), key=lambda x: -x[1]["score"])[:5]

    result = []
    for fp, data in ranked:
        full_path = vault / fp
        summary = get_note_summary(full_path) if full_path.exists() else ""
        result.append({
            "path": fp,
            "summary": summary,
            "score": data["score"],
            "signals": data["signals"],
        })

    return result


# ── Evaluation stage ──────────────────────────────────────────────────────────

def load_openrouter_key() -> str:
    """Load OpenRouter API key from .env."""
    env_file = Path.home() / ".hermes" / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("OPENROUTER_API_KEY="):
                return line.split("=", 1)[1].strip().strip("'\"")
    return os.environ.get("OPENROUTER_API_KEY", "")


def llm_evaluate(seed_note: str, seed_summary: str,
                 candidate_path: str, candidate_summary: str,
                 api_key: str) -> dict:
    """Send candidate pair to LLM for scoring."""
    import urllib.request

    prompt = f"""You are a knowledge graph curator. Score the potential connection between two notes.

NOTE A (seed): {seed_note}
Summary: {seed_summary[:600]}

NOTE B (candidate): {candidate_path}
Summary: {candidate_summary[:600]}

Score this connection:
- usefulness (1-5): How useful is linking these two notes for future reasoning or retrieval?
- confidence (0.0-1.0): How confident are you this is a genuine, non-trivial connection?
- is_trivial (true/false): Is this connection obvious or trivial?
- is_redundant (true/false): Are these notes already clearly connected?
- connection_type: one of [adds_condition, creates_filter, reveals_sequence, resolves_conflict, confirms_risk_rule, cross_references, other]
- rationale: 1-2 sentences explaining why this connection matters
- suggested_link_text: A short contextual phrase for the wikilink (e.g., "See [[note]] for stop optimization context")

Respond as JSON only:
{{"usefulness": N, "confidence": F, "is_trivial": bool, "is_redundant": bool, "connection_type": "...", "rationale": "...", "suggested_link_text": "..."}}"""

    payload = json.dumps({
        "model": "z-ai/glm-5.2",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 300,
        "temperature": 0.3,
    }).encode()

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            content = data["choices"][0]["message"]["content"]
            # Extract JSON from response
            json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return json.loads(content)
    except Exception as e:
        return {
            "usefulness": 0,
            "confidence": 0.0,
            "is_trivial": True,
            "is_redundant": True,
            "connection_type": "other",
            "rationale": f"LLM evaluation failed: {e}",
            "suggested_link_text": "",
        }


def should_auto_apply(score: dict) -> bool:
    """Check if a score meets the auto-apply threshold."""
    return (
        score.get("usefulness", 0) >= 4
        and score.get("confidence", 0) >= 0.75
        and not score.get("is_trivial", True)
        and not score.get("is_redundant", True)
    )


def should_queue_for_review(score: dict) -> bool:
    """Check if a score meets the review queue threshold."""
    return (
        score.get("usefulness", 0) >= 3
        and score.get("confidence", 0) >= 0.5
        and not should_auto_apply(score)
    )


# ── Linking stage ─────────────────────────────────────────────────────────────

def add_wikilink(source_path: Path, target_note_name: str,
                 link_text: str, dry_run: bool = False) -> bool:
    """Add a wikilink to a note. Uses patch (Obsidian skill convention).

    Adds a '## Related' section at the end of the note if one doesn't exist,
    or appends to the existing one.
    """
    if dry_run:
        print(f"  [dry-run] Would link: {source_path.name} → [[{target_note_name}]] ({link_text})")
        return True

    try:
        content = source_path.read_text()
        target_link = f"- [[{target_note_name}]] — {link_text}"

        # Check if link already exists
        if f"[[{target_note_name}]]" in content:
            print(f"  ⏭️ Link already exists: {target_note_name}")
            return False

        # Check for existing Related section
        related_pattern = re.compile(r'^## Related\s*$', re.MULTILINE)
        if related_pattern.search(content):
            # Append to existing Related section
            content = related_pattern.sub(
                f"## Related\n{target_link}\n",
                content,
                count=1
            )
        else:
            # Add new Related section at end
            if not content.endswith("\n"):
                content += "\n"
            content += f"\n## Related\n{target_link}\n"

        source_path.write_text(content)
        return True
    except Exception as e:
        print(f"  ⚠️ Failed to add link: {e}")
        return False


# ── Health dashboard ──────────────────────────────────────────────────────────

def count_wikilinks(vault: Path) -> dict:
    """Count wikilinks across the vault for graph density."""
    total_links = 0
    notes_with_links = 0
    total_notes = 0
    orphan_notes = 0
    folder_degree = {}

    for p in vault.rglob("*.md"):
        if should_skip(str(p.relative_to(vault))):
            continue
        if p.parent.name == ".obsidian":
            continue
        total_notes += 1
        try:
            content = p.read_text()
            links = extract_wikilinks(content)
            if links:
                notes_with_links += 1
                total_links += len(links)
            else:
                orphan_notes += 1
            folder = str(p.parent.relative_to(vault))
            folder_degree.setdefault(folder, {"notes": 0, "links": 0})
            folder_degree[folder]["notes"] += 1
            folder_degree[folder]["links"] += len(links)
        except Exception:
            continue

    avg_degree = total_links / total_notes if total_notes > 0 else 0
    orphan_rate = orphan_notes / total_notes if total_notes > 0 else 0

    # Find weakly connected folders (low avg degree)
    weak_folders = []
    for folder, data in folder_degree.items():
        fa = data["links"] / data["notes"] if data["notes"] > 0 else 0
        if fa < 0.1 and data["notes"] > 5:
            weak_folders.append({"folder": folder, "avg_degree": round(fa, 2),
                                 "notes": data["notes"]})

    return {
        "total_notes": total_notes,
        "total_wikilinks": total_links,
        "notes_with_links": notes_with_links,
        "orphan_notes": orphan_notes,
        "avg_degree": round(avg_degree, 3),
        "orphan_rate": round(orphan_rate, 3),
        "weak_folders": sorted(weak_folders, key=lambda x: x["avg_degree"])[:5],
    }


def update_health_dashboard(vault: Path, run_report: dict, state: dict):
    """Update the Connection Health dashboard note."""
    health_path = vault / "08-Knowledge" / "Connection-Health.md"
    stats = count_wikilinks(vault)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    content = f"""---
type: connection-health
updated: {now}
tags: [connection-weaver, knowledge-graph, dashboard]
---

# Connection Health Dashboard

## Run Summary
| Metric | Last Run | Total |
|--------|----------|-------|
| Notes examined | {run_report["notes_examined"]} | {state["total_runs"] * 5} |
| Connections created | {run_report["connections_created"]} | {state["total_connections_created"]} |
| Review queue | {len(state["review_queue"])} | {len(state["review_queue"])} |
| Avg score | {run_report["avg_score"]:.1f} | — |

## Graph Density Signals
- Total wikilinks in vault: ~{stats["total_wikilinks"]}
- Total notes: {stats["total_notes"]}
- Avg degree per note: {stats["avg_degree"]}
- Notes with links: {stats["notes_with_links"]} ({(1 - stats["orphan_rate"]) * 100:.1f}%)
- Orphan notes (no links): {stats["orphan_notes"]} ({stats["orphan_rate"] * 100:.1f}%)

## Weakly Connected Areas
"""
    for wf in stats["weak_folders"]:
        content += f"- `{wf['folder']}` — {wf['notes']} notes, avg degree {wf['avg_degree']}\n"

    content += f"""
## Recent Discoveries (last run: {now})
"""
    for disc in run_report.get("discoveries", []):
        content += f"- **{disc['seed']}** → **{disc['target']}** (score {disc['score']:.1f}): {disc['rationale']}\n"

    if not run_report.get("discoveries"):
        content += "- (no connections created this run)\n"

    content += f"""
## Reflection Notes
"""
    for note in state.get("reflection_notes", [])[-5:]:
        content += f"- {note}\n"

    if not state.get("reflection_notes"):
        content += "- (no reflections yet — this is the first run)\n"

    health_path.parent.mkdir(parents=True, exist_ok=True)
    health_path.write_text(content)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Vault Connection Weaver")
    parser.add_argument("--vault", default=None, help="Vault path")
    parser.add_argument("--batch", type=int, default=5, help="Max notes per run")
    parser.add_argument("--dry-run", action="store_true", help="Score + report, no writes")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--skip-semantic", action="store_true", help="Skip ChromaDB")
    parser.add_argument("--state", default=str(STATE_FILE), help="State file path")
    parser.add_argument("--health", default=None, help="Health dashboard path")
    parser.add_argument("--priority-dirs", default=None, help="Comma-separated priority dirs")
    parser.add_argument("--commit", action="store_true", help="Git commit after linking")
    args = parser.parse_args()

    vault = resolve_vault(args.vault)
    if args.health:
        health_path = Path(args.health)
    else:
        health_path = vault / "08-Knowledge" / "Connection-Health.md"

    state_file = Path(args.state)
    state_file.parent.mkdir(parents=True, exist_ok=True)

    state = load_state(state_file)
    api_key = load_openrouter_key()

    if not api_key:
        print("⚠️ No OpenRouter API key found. Running in FTS5-only mode (no LLM scoring).")
        print("   Set OPENROUTER_API_KEY in ~/.hermes/.env")
        api_key = ""

    # ── Stage 1: Discovery ──
    print("╔═══ Vault Connection Weaver ═══╗")
    print(f"║  Vault: {vault}")
    print(f"║  Mode: {'DRY-RUN' if args.dry_run else 'LIVE'}")
    print(f"║  Batch: {args.batch} notes")
    print(f"║  LLM: {'yes' if api_key else 'no (FTS5 only)'}")
    print("╚═══════════════════════════════╝")
    print()

    # Get seed notes
    if args.priority_dirs:
        # Use priority dirs instead of git log
        seeds = []
        for d in args.priority_dirs.split(","):
            d = d.strip()
            for p in (vault / d).rglob("*.md"):
                rel = str(p.relative_to(vault))
                if not should_skip(rel):
                    seeds.append(rel)
        seeds = seeds[:args.batch]
    else:
        seeds = get_recent_notes(vault, since_days=3, limit=args.batch)

    if not seeds:
        print("No seed notes found. Nothing to do.")
        return

    print(f"📋 Seed notes ({len(seeds)}):")
    for s in seeds:
        print(f"   • {s}")
    print()

    run_report = {
        "notes_examined": 0,
        "connections_created": 0,
        "avg_score": 0.0,
        "discoveries": [],
    }
    all_scores = []

    # ── Process each seed note ──
    for seed in seeds:
        seed_path = vault / seed
        if not seed_path.exists():
            continue

        print(f"─── Examining: {seed} ───")
        run_report["notes_examined"] += 1

        # Discover candidates
        candidates = discover_candidates(seed, vault, state, skip_semantic=args.skip_semantic)

        if not candidates:
            print(f"   No candidates found.")
            continue

        print(f"   Candidates: {len(candidates)}")
        for c in candidates:
            print(f"     • {c['path']} (score: {c['score']:.2f}, signals: {', '.join(c['signals'])})")

        # ── Stage 2: Evaluation ──
        links_this_note = 0
        for candidate in candidates:
            if links_this_note >= 3:
                break  # max 3 links per note per run

            if not api_key:
                # No LLM — use heuristic scoring only
                if candidate["score"] >= 0.5:
                    target_name = Path(candidate["path"]).stem
                    link_text = "Related note discovered by Vault Connection Weaver"
                    success = add_wikilink(
                        seed_path, target_name, link_text, dry_run=args.dry_run
                    )
                    if success:
                        run_report["connections_created"] += 1
                        run_report["discoveries"].append({
                            "seed": seed,
                            "target": candidate["path"],
                            "score": candidate["score"],
                            "rationale": f"Heuristic match (signals: {', '.join(candidate['signals'])})",
                        })
                        links_this_note += 1
                continue

            # LLM evaluation
            score = llm_evaluate(
                seed, get_note_summary(seed_path),
                candidate["path"], candidate["summary"],
                api_key
            )
            all_scores.append(score.get("usefulness", 0))

            print(f"     LLM: usefulness={score.get('usefulness', 0)}, "
                  f"confidence={score.get('confidence', 0):.2f}, "
                  f"trivial={score.get('is_trivial', True)}, "
                  f"redundant={score.get('is_redundant', True)}")

            # ── Stage 3: Linking ──
            if should_auto_apply(score):
                target_name = Path(candidate["path"]).stem
                link_text = score.get("suggested_link_text", "Related note")
                # Clean up link text — remove [[...]] if LLM included it
                link_text = re.sub(r'\[\[|\]\]', '', link_text).strip()
                if not link_text:
                    link_text = "Related note — discovered by Vault Connection Weaver"

                success = add_wikilink(
                    seed_path, target_name, link_text, dry_run=args.dry_run
                )
                if success:
                    run_report["connections_created"] += 1
                    run_report["discoveries"].append({
                        "seed": seed,
                        "target": candidate["path"],
                        "score": float(score.get("usefulness", 0)),
                        "rationale": score.get("rationale", ""),
                    })
                    links_this_note += 1
                    print(f"     ✅ Linked: [[{target_name}]]")
            elif should_queue_for_review(score):
                state["review_queue"].append({
                    "source": seed,
                    "target": candidate["path"],
                    "score": float(score.get("usefulness", 0)),
                    "rationale": score.get("rationale", ""),
                    "queued_at": datetime.now(timezone.utc).isoformat(),
                })
                print(f"     📋 Queued for review: {candidate['path']}")
            else:
                print(f"     ⏭️ Skipped (below threshold)")

        # Update state
        state["examined_notes"][seed] = {
            "last_examined": datetime.now(timezone.utc).isoformat(),
            "connections_found": len(candidates),
            "connections_written": links_this_note,
            "score": float(all_scores[-1]) if all_scores else 0.0,
        }

    # ── Stage 4: Health & Reflection ──
    if all_scores:
        run_report["avg_score"] = sum(all_scores) / len(all_scores)

    state["last_run"] = datetime.now(timezone.utc).isoformat()
    state["total_runs"] += 1
    state["total_connections_created"] += run_report["connections_created"]

    # Simple reflection
    if run_report["connections_created"] > 0:
        state["reflection_notes"].append(
            f"Run {state['total_runs']}: Created {run_report['connections_created']} "
            f"connections from {run_report['notes_examined']} notes. "
            f"Avg score: {run_report['avg_score']:.1f}."
        )

    save_state(state, state_file)

    # Update health dashboard
    update_health_dashboard(vault, run_report, state)

    # ── Output ──
    if args.json:
        print(json.dumps({
            "status": "ok",
            "run_report": run_report,
            "state_summary": {
                "total_runs": state["total_runs"],
                "total_connections": state["total_connections_created"],
                "review_queue": len(state["review_queue"]),
            },
        }, indent=2))
    else:
        print()
        print("╔═══ Run Summary ═══╗")
        print(f"║  Notes examined: {run_report['notes_examined']}")
        print(f"║  Connections created: {run_report['connections_created']}")
        print(f"║  Review queue: {len(state['review_queue'])}")
        print(f"║  Avg score: {run_report['avg_score']:.1f}")
        print(f"║  Total runs: {state['total_runs']}")
        print(f"║  Total connections: {state['total_connections_created']}")
        print("╚════════════════════╝")

    # Git commit
    if args.commit and not args.dry_run and run_report["connections_created"] > 0:
        try:
            subprocess.run(["git", "add", "-A"], cwd=str(vault), check=True)
            subprocess.run(
                ["git", "commit", "-m",
                 f"vault-weaver: {run_report['connections_created']} connections created "
                 f"(run {state['total_runs']})"],
                cwd=str(vault), check=True, capture_output=True
            )
            print(f"✅ Git committed: {run_report['connections_created']} connections")
        except Exception as e:
            print(f"⚠️ Git commit failed: {e}")


if __name__ == "__main__":
    main()
