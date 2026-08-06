#!/usr/bin/env python3
"""
webhook_utils.py — HermesForge Webhook Cross-Posting Utilities

Handles posting and deleting messages via Discord webhooks, replacing
the native announcement channel crosspost system. With webhooks, we
have full control over message lifecycle in the follower server's
channel — no tombstones left behind when deleting.

Webhook URL format: https://discord.com/api/webhooks/{webhook_id}/{webhook_token}

State tracking: message IDs are stored in a JSON state file per source
channel, so we can delete them later.

Usage:
    from webhook_utils import WebhookCrossposter

    wx = WebhookCrossposter(
        webhook_url="https://discord.com/api/webhooks/123/abc",
        source_channel_id="1528555885310513213",
    )
    # Post a message
    msg_id = wx.post({"embeds": [embed]})
    # Delete all previously posted messages
    wx.delete_all()
"""

import os
import json
import subprocess
import time
import pathlib
from typing import Optional

API_BASE = "https://discord.com/api/v10"

# State file for tracking webhook message IDs
STATE_DIR = pathlib.Path.home() / ".hermes"
STATE_FILE = STATE_DIR / "webhook_crosspost_state.json"


class WebhookCrossposter:
    """Manages webhook-based cross-posting to a follower server channel."""

    def __init__(self, webhook_url: str, source_channel_id: str,
                 webhook_name: str = "HermesForge", webhook_avatar: str = ""):
        """
        Initialize with a webhook URL and the source channel ID it mirrors.

        Args:
            webhook_url: Full Discord webhook URL
            source_channel_id: The source announcement channel ID (for state tracking)
            webhook_name: Display name for webhook messages
            webhook_avatar: Optional avatar URL
        """
        self.webhook_url = webhook_url
        self.source_channel_id = str(source_channel_id)
        self.webhook_name = webhook_name
        self.webhook_avatar = webhook_avatar

        # Parse webhook ID and token from URL
        # URL format: https://discord.com/api/webhooks/{id}/{token}
        parts = webhook_url.rstrip("/").split("/")
        self.webhook_id = parts[-2] if len(parts) >= 2 else ""
        self.webhook_token = parts[-1] if len(parts) >= 1 else ""

        if not self.webhook_id or not self.webhook_token:
            raise ValueError(f"Invalid webhook URL: {webhook_url}")

    def _api_request(self, method: str, url: str, data: dict = None) -> dict:
        """Make a Discord API request via curl."""
        cmd = ["curl", "-s", "-X", method]
        if data:
            cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(data)]
        cmd += [url]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if not result.stdout.strip():
            # Empty response (204 No Content) — success for DELETE, failure for POST without wait
            return {"success": True}
        try:
            return json.loads(result.stdout)
        except (json.JSONDecodeError, ValueError):
            return {"error": result.stdout[:500]}

    def _load_state(self) -> dict:
        """Load the webhook message state."""
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text())
        return {}

    def _save_state(self, state: dict) -> None:
        """Save the webhook message state."""
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state, indent=2))

    def _get_tracked_ids(self) -> list:
        """Get list of tracked message IDs for this source channel."""
        state = self._load_state()
        return state.get(self.source_channel_id, {}).get("message_ids", [])

    def _track_id(self, message_id: str) -> None:
        """Track a webhook message ID."""
        state = self._load_state()
        if self.source_channel_id not in state:
            state[self.source_channel_id] = {"message_ids": []}
        state[self.source_channel_id]["message_ids"].append(message_id)
        self._save_state(state)

    def _untrack_id(self, message_id: str) -> None:
        """Remove a tracked message ID."""
        state = self._load_state()
        if self.source_channel_id in state:
            ids = state[self.source_channel_id].get("message_ids", [])
            if message_id in ids:
                ids.remove(message_id)
                state[self.source_channel_id]["message_ids"] = ids
                self._save_state(state)

    def post(self, payload: dict) -> Optional[str]:
        """
        Post a message via the webhook.

        Args:
            payload: Discord message payload (embeds, content, etc.)
                     The webhook name/avatar are added automatically.

        Returns:
            Message ID if successful, None if failed.
        """
        # Add webhook display options
        payload = dict(payload)  # shallow copy
        payload["username"] = self.webhook_name
        if self.webhook_avatar:
            payload["avatar_url"] = self.webhook_avatar

        url = f"{API_BASE}/webhooks/{self.webhook_id}/{self.webhook_token}?wait=true"
        result = self._api_request("POST", url, payload)

        msg_id = result.get("id")
        if msg_id:
            self._track_id(msg_id)
            return msg_id
        else:
            print(f"  ⚠️ Webhook post failed: {result}", file=__import__('sys').stderr)
            return None

    def delete_message(self, message_id: str) -> bool:
        """
        Delete a webhook message using the webhook token.

        Returns True if deleted (or already gone), False if failed.
        """
        url = f"{API_BASE}/webhooks/{self.webhook_id}/{self.webhook_token}/messages/{message_id}"
        result = self._api_request("DELETE", url)

        # Success cases:
        # - Empty response (204 No Content) = deleted successfully
        # - code 10008 (Unknown Message) = already deleted
        # - {"success": True} from our _api_request wrapper for empty responses
        if not result or result.get("success") or result.get("code") == 10008:
            self._untrack_id(message_id)
            return True
        return False

    def delete_all(self) -> int:
        """
        Delete all tracked webhook messages for this source channel.

        Returns the number of messages successfully deleted.
        """
        tracked_ids = self._get_tracked_ids()
        deleted = 0
        for msg_id in tracked_ids:
            if self.delete_message(msg_id):
                deleted += 1
                time.sleep(0.6)  # Rate limit safety
        print(f"  Deleted {deleted}/{len(tracked_ids)} webhook messages", file=__import__('sys').stderr)
        return deleted

    def post_and_crosspost(self, payload: dict, source_msg_id: str = None) -> Optional[str]:
        """
        Post via webhook. This replaces the native crosspost feature.

        Args:
            payload: Discord message payload
            source_msg_id: Not used (kept for API compatibility with old crosspost callers)

        Returns:
            Webhook message ID if successful.
        """
        return self.post(payload)


def get_webhook_for_channel(source_channel_id: str) -> Optional[str]:
    """
    Look up the webhook URL for a given source channel ID.

    Checks environment variables:
      CROSSPOST_WEBHOOK_{CHANNEL_ID} — per-channel webhook URL
      CROSSPOST_WEBHOOK_URL — fallback for all channels

    Returns the webhook URL or None if not configured.
    """
    # Check per-channel env var first
    env_key = f"CROSSPOST_WEBHOOK_{source_channel_id}"
    webhook_url = os.environ.get(env_key, "")
    if webhook_url:
        return webhook_url

    # Check fallback
    webhook_url = os.environ.get("CROSSPOST_WEBHOOK_URL", "")
    if webhook_url:
        return webhook_url

    return None


def create_crossposter(source_channel_id: str,
                       webhook_name: str = "HermesForge") -> Optional[WebhookCrossposter]:
    """
    Factory: create a WebhookCrossposter for a source channel if a webhook
    is configured. Returns None if no webhook is configured.

    Usage:
        wx = create_crossposter("1528555885310513213")
        if wx:
            wx.post({"embeds": [embed]})
    """
    webhook_url = get_webhook_for_channel(str(source_channel_id))
    if not webhook_url:
        return None
    try:
        return WebhookCrossposter(
            webhook_url=webhook_url,
            source_channel_id=str(source_channel_id),
            webhook_name=webhook_name,
        )
    except ValueError as e:
        print(f"  ⚠️ Invalid webhook URL for channel {source_channel_id}: {e}", file=__import__('sys').stderr)
        return None
