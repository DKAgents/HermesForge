# Git sync scope

Date: 2026-09-27
/usr/local/sbin/hermes-git-sync adds scripts and campaigns only.
.env is ignored (.gitignore:45).
config.yaml is not in the add list. Do not add it. It may hold a token.
Trade history is not in the add list. Leave it out.
Off-box backup remains the copy for data that git must not store.
