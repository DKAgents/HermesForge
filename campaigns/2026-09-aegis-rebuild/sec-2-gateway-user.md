# SEC-2: Gateway user drop failed

Date: 2026-09-27
hermesbot cannot run hermes-gateway.service.
env_loader.py opens /root/.hermes/.env. An ACL that hides that file makes the process exit 1.
Rollback restored User=root. Discord answers mentions.
redact_secrets is already true. command_allowlist is an approval list, not a path deny.
Unused: hermesbot, /usr/local/sbin/hermes-gateway-drop, /var/lib/hermes.
