# MIG-1: Git Hygiene — .env Untracked

**Date**: 2026-09-27

**Confirmed**: `/root/HermesForge/.env` is 23 bytes, 1 line:
`LUNARCRUSH_API_KEY=***` (masked placeholder, not a real key).

**Action**: Added `.env` to `.gitignore` and removed from git index
(`git rm --cached .env`). The file remains on disk but is no longer
tracked. Real secrets continue to live at `/root/.hermes/.env` (0600).