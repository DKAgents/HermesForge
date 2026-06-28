---
id: US-001-SSHFS-Mount
type: user-story
epic: "[[Epics/EPIC-001-Foundation]]"
status: ready
priority: high
effort: S
created: 2026-06-27
updated: 2026-06-27
assigned_to: human
tags: [backlog, story, sshfs, mac, obsidian]
---

# US-001: Set Up SSHFS Mount on Mac

## Story
**As a** developer,  
**I want** to mount the VPS vault via SSHFS on my Mac,  
**So that** I can edit notes in Obsidian on my Mac as if they were local files.

## Acceptance Criteria
- [ ] SSHFS mounts successfully from Mac to `/root/HermesForge` on VPS
- [ ] `ls ~/HermesForge` on Mac shows vault folders (00-Meta, 01-Agents, etc.)
- [ ] Obsidian on Mac opens the vault and displays all folders and notes
- [ ] Changes made in Obsidian on Mac persist to VPS filesystem
- [ ] Changes made on VPS are visible in Obsidian within seconds
- [ ] Mount procedure is documented in vault ✅

## VPS Connection Details
| Item | Value |
|---|---|
| VPS IP | `104.207.156.197` |
| SSH User | `root` |
| SSH Port | `22` |
| Vault path | `/root/HermesForge` |
| Authorized key | `trading-swarm-tunnel` (ed25519) |

## Quick Mount Command
```bash
mkdir -p ~/HermesForge
sshfs root@104.207.156.197:/root/HermesForge ~/HermesForge \
  -o reconnect \
  -o ServerAliveInterval=15 \
  -o ServerAliveCountMax=3 \
  -o follow_symlinks \
  -o local \
  -o volname=HermesForge
```

## Full Instructions
See: [[08-Knowledge/Skills/SSHFS-VPS-Vault-Mount]]

## Dependencies
- Blocks: US-003 (Obsidian plugin config — needs vault open in Obsidian)
- Blocked by: None

## Definition of Done
- [ ] SSHFS mounted and stable
- [ ] Obsidian vault open on Mac
- [ ] Bi-directional sync verified
- [ ] Mount procedure documented in vault ✅ (done)
