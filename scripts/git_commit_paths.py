#!/usr/bin/env python3
"""Path-scoped, idempotent, race-safe git commit helper.

Stages ONLY the given repo paths (honors .gitignore), commits ONLY those
paths (path-scoped, ignores unrelated pre-staged index entries), and no-ops
when nothing new. Serializes concurrent maintenance commits via an exclusive
flock. Never pushes.
"""
import argparse, fcntl, subprocess, sys, time
from pathlib import Path

LOCK_DIR = Path("/root/.hermes/vault_maintenance")
LOCK_PATH = LOCK_DIR / "git_commit.lock"
LOCK_TIMEOUT = 120.0

def acquire_lock():
    LOCK_DIR.mkdir(parents=True, exist_ok=True)
    fh = open(LOCK_PATH, "w")
    deadline = time.time() + LOCK_TIMEOUT
    while True:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return fh
        except BlockingIOError:
            if time.time() >= deadline:
                fh.close()
                raise RuntimeError(f"git commit lock timeout after {LOCK_TIMEOUT}s")
            time.sleep(2)

def git(repo, *args, check=False):
    return subprocess.run(["git", *args], cwd=str(repo),
                          capture_output=True, text=True, check=check)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--message", required=True)
    ap.add_argument("--path", action="append", required=True,
                    help="repo-relative path to stage+commit (repeatable)")
    a = ap.parse_args()
    repo = Path(a.repo).resolve()
    paths = [str(p) for p in a.path]

    fh = acquire_lock()
    try:
        git(repo, "add", "--", *paths, check=True)
        r = git(repo, "diff", "--cached", "--quiet", "--", *paths)
        if r.returncode == 0:
            git(repo, "reset", "-q", "--", *paths)
            print("git_commit_paths: no changes — no-op")
            return 0
        git(repo, "commit", "-m", a.message, "--", *paths, check=True)
        git(repo, "reset", "-q", "--", *paths)
        print(f"git_commit_paths: committed -> {a.message}")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"git_commit_paths: FAILED: {e.stderr.strip()}", file=sys.stderr)
        return 1
    finally:
        fcntl.flock(fh, fcntl.LOCK_UN)
        fh.close()

if __name__ == "__main__":
    sys.exit(main())
