#!/usr/bin/env python3
"""
Jev Client — thin wrapper around TypeSafe's System One API.

POST https://api.typesafe.ai/v1/systemone
Three question types: noul (yes/no), score (spectrum), choice (pick one).

Pricing: $0.042/M input tokens, output free. ~70-500ms latency.
API key from TYPESAFE_API_KEY env var or ~/.hermes/.env.

Usage:
    from jev_client import JevClient
    jev = JevClient()
    result = jev.ask(state="...", questions={...})
"""

import json
import os
import time
from pathlib import Path
from typing import Any, Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ENDPOINT = "https://api.typesafe.ai/v1/systemone"
DEFAULT_MODEL = "jev-latest"
MAX_RETRIES = 3
RETRY_DELAY = 1.0


def _load_api_key() -> Optional[str]:
    """Load TYPESAFE_API_KEY from env or .hermes/.env."""
    key = os.environ.get("TYPESAFE_API_KEY")
    if key:
        return key
    env_file = Path.home() / ".hermes" / ".env"
    if env_file.exists():
        for line in env_file.read_text().split('\n'):
            line = line.strip()
            if line.startswith("TYPESAFE_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


class JevError(Exception):
    """API or client error from Jev."""
    pass


class JevClient:
    """TypeSafe Jev System One client."""

    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL):
        self.api_key = api_key or _load_api_key()
        if not self.api_key:
            raise JevError("TYPESAFE_API_KEY not found in env or ~/.hermes/.env")
        self.model = model

    def ask(self, state: Any, questions: dict[str, dict]) -> dict:
        """
        Send a state + questions map to Jev, return answers dict.

        Args:
            state: string, dict, or list — the content to evaluate
            questions: {"question_id": {"type": "noul"|"score"|"choice", ...}}

        Returns:
            {"answers": {"question_id": {...}}} — one answer per question
        """
        body = {
            "state": state,
            "model": self.model,
            "questions": questions,
        }
        payload = json.dumps(body).encode("utf-8")

        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                req = Request(
                    ENDPOINT,
                    data=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    method="POST",
                )
                with urlopen(req, timeout=30) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except HTTPError as e:
                status = e.code
                if status in (429, 529):
                    delay = RETRY_DELAY * (2 ** attempt)
                    time.sleep(delay)
                    last_error = e
                    continue
                body = e.read().decode("utf-8", errors="replace")
                raise JevError(f"HTTP {status}: {body[:500]}")
            except URLError as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (2 ** attempt))
                    continue
                raise JevError(f"Connection error after {MAX_RETRIES} retries: {e}")

        raise JevError(f"Failed after {MAX_RETRIES} retries: {last_error}")

    def noul(self, state: Any, instructions: str,
             true_criteria: Optional[str] = None,
             false_criteria: Optional[str] = None) -> float:
        """
        Ask a yes/no question. Returns probability (0-1) the answer is yes.

        Args:
            state: content to evaluate
            instructions: the yes/no question
            true_criteria: optional description of what 'yes' means
            false_criteria: optional description of what 'no' means

        Returns:
            float 0.0-1.0 (probability of yes)
        """
        question = {"type": "noul", "instructions": instructions}
        if true_criteria or false_criteria:
            criteria = {}
            if true_criteria:
                criteria["true"] = true_criteria
            if false_criteria:
                criteria["false"] = false_criteria
            question["criteria"] = criteria

        result = self.ask(state, {"q": question})
        return result["answers"]["q"]["noul"]

    def score(self, state: Any, instructions: str, levels: list[str]) -> dict:
        """
        Score on a spectrum. Returns {score: float, probabilities: dict, confidence: float}.

        Args:
            state: content to evaluate
            instructions: what to score
            levels: ordered list of level descriptions (2-10 items)

        Returns:
            {"score": float, "probabilities": {str: float}, "confidence": float}
        """
        question = {
            "type": "score",
            "instructions": instructions,
            "criteria": levels,
        }
        result = self.ask(state, {"q": question})
        return result["answers"]["q"]

    def choice(self, state: Any, instructions: str, options: dict[str, str]) -> dict:
        """
        Pick one of N options. Returns {choice: str, probabilities: dict, confidence: float}.

        Args:
            state: content to evaluate
            instructions: the classification question
            options: {"option_key": "description", ...}

        Returns:
            {"choice": str, "probabilities": {str: float}, "confidence": float}
        """
        question = {
            "type": "choice",
            "instructions": instructions,
            "criteria": options,
        }
        result = self.ask(state, {"q": question})
        return result["answers"]["q"]


# ── Convenience for quick testing ──

if __name__ == "__main__":
    jev = JevClient()
    # Quick test
    prob = jev.noul(
        state={"market": "BTC down 5% in 2 hours, VIX at 28, funding deeply negative"},
        instructions="Is this market in a fear/capitulation regime?",
        true_criteria="Fear/capitulation: panic selling, extreme negative sentiment",
        false_criteria="Normal or bullish: orderly selling, no panic"
    )
    print(f"Fear probability: {prob:.3f}")