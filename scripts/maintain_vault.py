#!/usr/bin/env python3
"""
HermesForge Vault Maintenance Pipeline
=======================================
Single entry point that runs all vault maintenance steps in order:

  1. Detect new/changed notes since last run (via checkpoint)
  2. Check & fix frontmatter on changed notes
  3. Re-index FTS (incremental — only changed notes)
  4. Re-embed (incremental — only changed notes)
  5. Generate wikilinks for changed notes
  6. Run dedup scan and alert on near-duplicates
  7. Write checkpoint and summary report

Usage:
    python3 maintain_vault.py                       # normal incremental run
    python3 maintain_vault.py --scope all           # force full vault run
    python3 maintain_vault.py --dry-run             # simulate, no writes
    python3 maintain_vault.py --skip-embed          # skip embedding (faster)
    python3 maintain_vault.py --skip-dedup          # skip dedup scan
    python3 maintain_vault.py --report /tmp/r.json  # write JSON report to path
"""

import sys, os, json, argparse, subprocess, hashlib
from pathlib import Path
from datetime import datetime, timezone

VAULT_ROOT    = Path('/root/HermesForge')
SCRIPTS_DIR   = VAULT_ROOT / 'scripts'
INDEX_DIR     = Path('/root/.hermes/vault_index')
CHECKPOINT    = INDEX_DIR / 'checkpoint.json'
DEDUP_REPORT  = INDEX_DIR / 'dedup_report.json'
LOG_DIR       = VAULT_ROOT / '04-ForgeLoop' / 'Maintenance'

MURPHY_DIR    = VAULT_ROOT / '08-Knowledge' / 'Trading-Systems' / 'technical-analysis-financial-markets-murphy'

# All directories that are part of "the vault" for maintenance purposes
VAULT_DIRS = [
    VAULT_ROOT / '08-Knowledge',
    VAULT_ROOT / '07-Risk',
    VAULT_ROOT / '05-Research',
    VAULT_ROOT / '06-Strategies',
    VAULT_ROOT / '09-Journal',
    VAULT_ROOT / '00-Meta',
    VAULT_ROOT / '03-ADRs',
]


# ── checkpoint ────────────────────────────────────────────────────────────────

def load_checkpoint() -> dict:
    if CHECKPOINT.exists():
        return json.loads(CHECKPOINT.read_text())
    return {'last_run': None, 'file_hashes': {}}


def save_checkpoint(data: dict):
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    CHECKPOINT.write_text(json.dumps(data, indent=2))


def file_hash(path: Path) -> str:
    try:
        return hashlib.md5(path.read_bytes()).hexdigest()
    except Exception:
        return ''


def detect_changed(checkpoint: dict) -> list[Path]:
    """Return list of .md files that are new or have changed content since last checkpoint."""
    old_hashes = checkpoint.get('file_hashes', {})
    changed = []
    for d in VAULT_DIRS:
        if not d.exists():
            continue
        for f in d.rglob('*.md'):
            h = file_hash(f)
            if str(f) not in old_hashes or old_hashes[str(f)] != h:
                changed.append(f)
    return changed


def update_hashes(checkpoint: dict) -> dict:
    """Recompute all hashes and return updated checkpoint."""
    hashes = {}
    for d in VAULT_DIRS:
        if not d.exists():
            continue
        for f in d.rglob('*.md'):
            hashes[str(f)] = file_hash(f)
    checkpoint['file_hashes'] = hashes
    checkpoint['last_run'] = datetime.now(timezone.utc).isoformat()
    return checkpoint


# ── subprocess runner ─────────────────────────────────────────────────────────

def run(cmd: list[str], step: str, dry_run: bool = False) -> dict:
    """Run a subprocess and return result dict."""
    if dry_run:
        print(f"  [DRY RUN] Would run: {' '.join(cmd)}")
        return {'step': step, 'status': 'dry_run', 'output': ''}

    print(f"  Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=600,
            cwd=str(SCRIPTS_DIR)
        )
        output = (result.stdout + result.stderr).strip()
        status = 'ok' if result.returncode == 0 else 'error'
        if output:
            # Print last 5 lines for visibility
            lines = output.splitlines()
            for line in lines[-5:]:
                print(f"    {line}")
        return {'step': step, 'status': status, 'returncode': result.returncode,
                'output': output[-2000:]}  # cap output size in report
    except subprocess.TimeoutExpired:
        return {'step': step, 'status': 'timeout', 'output': 'Timed out after 600s'}
    except Exception as e:
        return {'step': step, 'status': 'error', 'output': str(e)}


# ── report writer ─────────────────────────────────────────────────────────────

def write_run_log(summary: dict, dry_run: bool):
    """Write a dated maintenance log note to the vault."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    date_str = now.strftime('%Y-%m-%d')
    time_str = now.strftime('%H:%M UTC')
    fname = LOG_DIR / f'Maintenance-{now.strftime("%Y-%m-%dT%H%M")}.md'

    steps = summary.get('steps', [])
    step_lines = '\n'.join(
        f"| {s['step']:<30} | {'✅' if s['status'] == 'ok' else '⏭️' if s['status'] == 'dry_run' else '❌'} {s['status']} |"
        for s in steps
    )

    changed_count = summary.get('changed_files', 0)
    prefix = '[DRY RUN] ' if dry_run else ''

    content = f"""---
type: maintenance-log
date: {date_str}
status: {'dry-run' if dry_run else 'complete'}
changed_files: {changed_count}
tags: [maintenance, forge-loop]
---

# {prefix}Vault Maintenance — {date_str} {time_str}

## Summary

| Metric | Value |
|--------|-------|
| Changed files detected | {changed_count} |
| Scope | {summary.get('scope', 'incremental')} |
| Duration | {summary.get('duration_s', 0):.1f}s |
| Dedup candidates | {summary.get('dedup_candidates', 0)} |

## Steps

| Step | Status |
|------|--------|
{step_lines}

## Notes
{summary.get('notes', '_No issues detected._')}
"""
    if not dry_run:
        fname.write_text(content)
    return str(fname), content


# ── discord summary ───────────────────────────────────────────────────────────

def discord_summary(summary: dict, dry_run: bool) -> str:
    """Return a compact Discord message for the maintenance run."""
    ok = sum(1 for s in summary['steps'] if s['status'] == 'ok')
    err = sum(1 for s in summary['steps'] if s['status'] == 'error')
    changed = summary.get('changed_files', 0)
    dedup = summary.get('dedup_candidates', 0)
    dur = summary.get('duration_s', 0)

    status_icon = '✅' if err == 0 else '⚠️'
    prefix = '[DRY RUN] ' if dry_run else ''

    lines = [
        f"{status_icon} **{prefix}Vault Maintenance Complete** ({dur:.0f}s)",
        f"• Changed files: **{changed}**",
        f"• Steps OK / Errors: **{ok}** / **{err}**",
    ]
    if dedup > 0:
        lines.append(f"• ⚠️ Dedup candidates: **{dedup}** — check `dedup_report.json`")
    if err > 0:
        failed = [s['step'] for s in summary['steps'] if s['status'] == 'error']
        lines.append(f"• Failed steps: {', '.join(failed)}")
    return '\n'.join(lines)


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description='HermesForge vault maintenance pipeline')
    ap.add_argument('--scope', choices=['new', 'all'], default='new',
                    help='"new" = incremental (default), "all" = full vault rebuild')
    ap.add_argument('--dry-run', action='store_true',
                    help='Simulate run — no file writes, no index updates')
    ap.add_argument('--skip-embed', action='store_true',
                    help='Skip embedding step (faster, loses semantic search freshness)')
    ap.add_argument('--skip-dedup', action='store_true',
                    help='Skip deduplication scan')
    ap.add_argument('--report', default='', help='Write JSON report to this path')
    args = ap.parse_args()

    start = datetime.now(timezone.utc)
    print(f"\n{'='*60}")
    print(f"  HermesForge Vault Maintenance")
    print(f"  {start.strftime('%Y-%m-%d %H:%M UTC')}  |  scope={args.scope}  |  dry_run={args.dry_run}")
    print(f"{'='*60}\n")

    checkpoint = load_checkpoint()
    steps = []
    notes_text = []

    # ── Step 1: Detect changed files ─────────────────────────────────────────
    print("Step 1/6 — Detecting changed files...")
    if args.scope == 'all':
        changed_files = []
        for d in VAULT_DIRS:
            if d.exists():
                changed_files.extend(d.rglob('*.md'))
        print(f"  Full scan: {len(changed_files)} notes")
    else:
        changed_files = detect_changed(checkpoint)
        print(f"  {len(changed_files)} new/changed notes since last run")

    steps.append({'step': 'detect_changes', 'status': 'ok',
                  'output': f'{len(changed_files)} files'})

    if not changed_files and args.scope == 'new':
        print("\nNo changes detected — vault is up to date.")
        summary = {
            'scope': args.scope, 'changed_files': 0,
            'steps': steps, 'duration_s': 0, 'dedup_candidates': 0,
            'notes': 'No changes detected — vault is up to date.'
        }
        print(discord_summary(summary, args.dry_run))
        return summary

    # Write changed file list to a temp file for scripts that accept --files
    tmp_filelist = INDEX_DIR / 'changed_files.txt'
    if not args.dry_run:
        INDEX_DIR.mkdir(parents=True, exist_ok=True)
        tmp_filelist.write_text('\n'.join(str(f) for f in changed_files))

    # ── Step 2: Frontmatter check ─────────────────────────────────────────────
    print(f"\nStep 2/6 — Checking frontmatter on {len(changed_files)} notes...")
    fm_files = [str(f) for f in changed_files]
    if fm_files:
        # Batch into chunks of 200 to avoid OS arg-length limits
        BATCH = 200
        batches = [fm_files[i:i+BATCH] for i in range(0, len(fm_files), BATCH)]
        fm_ok = fm_err = 0
        fm_out_lines = []
        for batch in batches:
            cmd = [sys.executable, str(SCRIPTS_DIR / 'check_frontmatter.py'), '--files'] + batch
            r = run(cmd, 'frontmatter_check', args.dry_run)
            if r['status'] == 'ok':
                fm_ok += 1
            else:
                fm_err += 1
            fm_out_lines.append(r.get('output', ''))
        r = {'step': 'frontmatter_check',
             'status': 'ok' if fm_err == 0 else 'error',
             'output': '\n'.join(fm_out_lines[-3:])}
        steps.append(r)
    else:
        steps.append({'step': 'frontmatter_check', 'status': 'ok', 'output': 'no files'})

    # ── Step 3: FTS re-index ──────────────────────────────────────────────────
    print(f"\nStep 3/6 — Re-indexing FTS...")
    if args.scope == 'all':
        cmd = [sys.executable, str(SCRIPTS_DIR / 'build_index.py'), '--force']
    else:
        cmd = [sys.executable, str(SCRIPTS_DIR / 'build_index.py')]
    r = run(cmd, 'fts_index', args.dry_run)
    steps.append(r)

    # ── Step 4: Re-embed ──────────────────────────────────────────────────────
    if not args.skip_embed:
        print(f"\nStep 4/6 — Re-embedding...")
        if args.scope == 'all':
            cmd = [sys.executable, str(SCRIPTS_DIR / 'embed_vault.py'), '--force']
        else:
            cmd = [sys.executable, str(SCRIPTS_DIR / 'embed_vault.py')]
        r = run(cmd, 'embedding', args.dry_run)
        steps.append(r)
    else:
        print(f"\nStep 4/6 — Embedding skipped (--skip-embed)")
        steps.append({'step': 'embedding', 'status': 'skipped', 'output': 'skipped'})

    # ── Step 5: Wikilinks ─────────────────────────────────────────────────────
    print(f"\nStep 5/6 — Generating wikilinks...")
    # generate_wikilinks.py operates on folders; run on murphy (main corpus) always
    # For new notes outside murphy, run on their parent dirs
    wikilink_dirs = set()
    wikilink_dirs.add(str(MURPHY_DIR))
    for f in changed_files:
        if MURPHY_DIR not in f.parents:
            wikilink_dirs.add(str(f.parent))

    wl_results = []
    for wdir in list(wikilink_dirs)[:5]:  # cap at 5 dirs per run
        p = Path(wdir)
        if p.exists() and any(p.rglob('*.md')):
            cmd = [sys.executable, str(SCRIPTS_DIR / 'generate_wikilinks.py'), wdir]
            r = run(cmd, f'wikilinks:{p.name}', args.dry_run)
            wl_results.append(r)

    if wl_results:
        steps.extend(wl_results)
    else:
        steps.append({'step': 'wikilinks', 'status': 'ok', 'output': 'no dirs to process'})

    # ── Step 6: Dedup ─────────────────────────────────────────────────────────
    dedup_candidates = 0
    if not args.skip_dedup:
        print(f"\nStep 6/6 — Running dedup scan (murphy scope)...")
        cmd = [sys.executable, str(SCRIPTS_DIR / 'dedup_notes.py'),
               '--scope', 'murphy', '--dry-run',
               '--report', str(DEDUP_REPORT)]
        r = run(cmd, 'dedup_scan', args.dry_run)
        steps.append(r)
        # Parse candidate count from output
        if DEDUP_REPORT.exists() and not args.dry_run:
            try:
                dr = json.loads(DEDUP_REPORT.read_text())
                dedup_candidates = len(dr.get('candidates', []))
                if dedup_candidates > 0:
                    notes_text.append(f"⚠️ {dedup_candidates} dedup candidates found — review dedup_report.json")
            except Exception:
                pass
    else:
        print(f"\nStep 6/6 — Dedup skipped (--skip-dedup)")
        steps.append({'step': 'dedup_scan', 'status': 'skipped', 'output': 'skipped'})

    # ── Step 7: Lesson extraction (optional — fires when new paper trade logs appear) ──
    # Checks for any new files in 09-Journal/ that look like trade logs (JSON)
    new_trade_logs = [f for f in changed_files
                      if '09-Journal' in str(f) and f.suffix == '.json'
                      and 'trade' in f.name.lower()]
    if new_trade_logs:
        print(f"\nStep 7 — Auto-extracting lessons from {len(new_trade_logs)} new trade log(s)...")
        for log_file in new_trade_logs[:3]:  # cap at 3 per run
            cmd = [sys.executable, str(SCRIPTS_DIR / 'extract_lessons.py'),
                   '--input', str(log_file)]
            r = run(cmd, f'lesson_extract:{log_file.name}', args.dry_run)
            steps.append(r)
    else:
        steps.append({'step': 'lesson_extract', 'status': 'skipped', 'output': 'no new trade logs'})

    # ── Checkpoint + summary ──────────────────────────────────────────────────
    end = datetime.now(timezone.utc)
    duration = (end - start).total_seconds()

    if not args.dry_run:
        checkpoint = update_hashes(checkpoint)
        save_checkpoint(checkpoint)
        print(f"\n  Checkpoint saved.")

    summary = {
        'scope': args.scope,
        'changed_files': len(changed_files),
        'steps': steps,
        'duration_s': duration,
        'dedup_candidates': dedup_candidates,
        'notes': '\n'.join(notes_text) if notes_text else '_No issues detected._',
        'timestamp': end.isoformat(),
    }

    # Write vault log
    log_path, _ = write_run_log(summary, args.dry_run)
    print(f"\n  Log written: {log_path}")

    if args.report:
        Path(args.report).write_text(json.dumps(summary, indent=2))

    # Final summary
    print(f"\n{'='*60}")
    msg = discord_summary(summary, args.dry_run)
    print(msg)
    print(f"{'='*60}\n")

    # Print Discord message to stdout for cron delivery
    if not sys.stdout.isatty():
        print(f"\n__DISCORD_MESSAGE__\n{msg}")

    return summary


if __name__ == '__main__':
    main()
