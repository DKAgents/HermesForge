---
id: SKILL-SSHFS-VPS-Vault-Mount
type: skill-doc
created: 2026-06-27
updated: 2026-06-27
status: active
tags: [skill, sshfs, mac, vault, obsidian]
---

# Skill: Mount HermesForge Vault via SSHFS on Mac

## Trigger
Use this when you want to access the HermesForge Obsidian vault on the VPS from your Mac — so Obsidian on Mac reads/writes files directly on the VPS filesystem.

## VPS Details
| Item | Value |
|---|---|
| VPS IP | `104.207.156.197` |
| SSH User | `root` |
| SSH Port | `22` |
| Vault path on VPS | `/root/HermesForge` |
| Suggested local mount | `~/HermesForge` |

---

## Prerequisites (Mac)

### 1. Install macFUSE
macFUSE is the FUSE kernel extension required by SSHFS on macOS.

```bash
brew install --cask macfuse
```

> ⚠️ After installing macFUSE, you **must** go to:
> **System Settings → Privacy & Security → Security** and click **Allow** for the macFUSE kernel extension.
> Then **restart your Mac**.

### 2. Install SSHFS
```bash
brew install sshfs
```

> If `brew install sshfs` fails (it was removed from Homebrew core), install via:
> ```bash
> brew install gromgit/fuse/sshfs-mac
> ```

---

## Setup Steps

### Step 1 — Ensure your SSH key is on the VPS
Your VPS already has this key authorized:
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAILavGSK2KVPQaWxhCR2JjaxV8mCQoKD1OkO7nYp3gMfK trading-swarm-tunnel
```

Test SSH access from your Mac first:
```bash
ssh root@104.207.156.197 "echo SSH OK"
```

If this fails, add your Mac's public key to the VPS:
```bash
# On your Mac — copy your public key
cat ~/.ssh/id_ed25519.pub   # or id_rsa.pub

# On VPS — add it
echo "YOUR_MAC_PUBLIC_KEY" >> ~/.ssh/authorized_keys
```

### Step 2 — Create local mount point
```bash
mkdir -p ~/HermesForge
```

### Step 3 — Mount the vault
```bash
sshfs root@104.207.156.197:/root/HermesForge ~/HermesForge \
  -o reconnect \
  -o ServerAliveInterval=15 \
  -o ServerAliveCountMax=3 \
  -o follow_symlinks \
  -o local \
  -o volname=HermesForge
```

### Step 4 — Verify the mount
```bash
ls ~/HermesForge
# Should show: 00-Meta  01-Agents  02-Backlog  03-ADRs  04-ForgeLoop  ...
```

### Step 5 — Open in Obsidian
1. Open **Obsidian**
2. Click **Open folder as vault**
3. Navigate to `~/HermesForge`
4. Click **Open**

---

## Auto-Mount on Login (Optional)

Create a shell script and add it to your Mac's Login Items:

```bash
# Save as ~/bin/mount-hermesforge.sh
#!/bin/bash
sleep 5  # wait for network
mkdir -p ~/HermesForge
sshfs root@104.207.156.197:/root/HermesForge ~/HermesForge \
  -o reconnect \
  -o ServerAliveInterval=15 \
  -o ServerAliveCountMax=3 \
  -o follow_symlinks \
  -o local \
  -o volname=HermesForge
```

```bash
chmod +x ~/bin/mount-hermesforge.sh
```

Then: **System Settings → General → Login Items** → add the script.

---

## Unmount

```bash
umount ~/HermesForge
# or
diskutil unmount ~/HermesForge
```

---

## Pitfalls

| Problem | Fix |
|---|---|
| `mount_macfuse: exec: No such file or directory` | macFUSE not installed or kernel extension not allowed in Security settings |
| `ssh: connect to host 104.207.156.197 port 22: Connection refused` | Check VPS is up; verify SSH port |
| `remote host has disconnected` | Add `-o ServerAliveInterval=15` (already in command above) |
| Obsidian shows vault but files don't save | Check file permissions on VPS: `chmod -R 755 ~/HermesForge` |
| Mount looks empty after sleep/wake | Unmount and remount; or use auto-reconnect option |
| `brew install sshfs` fails | Use `brew install gromgit/fuse/sshfs-mac` instead |

---

## Verification Checklist
- [ ] `ssh root@104.207.156.197 "echo SSH OK"` returns `SSH OK`
- [ ] `ls ~/HermesForge` shows vault folders after mount
- [ ] Obsidian opens vault and shows all folders
- [ ] Creating a test note in Obsidian appears on VPS: `ls /root/HermesForge/09-Journal/`
- [ ] Editing a note on VPS is visible in Obsidian within seconds

---

## Related
- [[02-Backlog/Stories/US-001-SSHFS-Mount]]
- [[00-Meta/HERMES_CONTEXT]]
