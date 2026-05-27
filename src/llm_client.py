"""
llm_client.py
-------------
Provider-agnostic LLM adapter. Supports Anthropic (Claude) and OpenAI (GPT-4o).
The agent logic never imports anthropic or openai directly — it always goes
through this adapter, so swapping providers is a one-line .env change.

Features:
- Automatic retry with exponential backoff on rate-limit / transient errors
- Token usage tracking per call and cumulative session total
- Structured JSON extraction with fence-stripping
- Provider detection from environment (ANTHROPIC_API_KEY takes priority)
"""

import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger(__name__)


# ── Response dataclass ────────────────────────────────────────────────────────
@dataclass
class LLMResponse:
    content: str                  # raw text from the model
    provider: str                 # "anthropic" | "openai"
    model: str
    input_tokens: int  = 0
    output_tokens: int = 0
    attempts: int      = 1        # how many attempts it took

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def extract_json(self) -> dict | list:
        """
        Strip markdown fences and parse JSON from the response.
        Raises json.JSONDecodeError if content is not valid JSON after cleaning.
        """
        cleaned = re.sub(r"```json\s*", "", self.content)
        cleaned = re.sub(r"```\s*",     "", cleaned).strip()
        return json.loads(cleaned)


# ── Session token tracker ─────────────────────────────────────────────────────
@dataclass
class TokenBudget:
    max_tokens: int = 50_000          # soft limit per pipeline run
    used_input:  int = field(default=0, init=False)
    used_output: int = field(default=0, init=False)

    def record(self, response: LLMResponse) -> None:
        self.used_input  += response.input_tokens
        self.used_output += response.output_tokens

    @property
    def total_used(self) -> int:
        return self.used_input + self.used_output

    def is_over_budget(self) -> bool:
        return self.total_used > self.max_tokens

    def summary(self) -> str:
        return (
            f"Tokens used: {self.total_used:,} "
            f"(input={self.used_input:,}, output={self.used_output:,}) "
            f"/ budget={self.max_tokens:,}"
        )


# ── Retry decorator ───────────────────────────────────────────────────────────
def _with_retry(fn, max_attempts: int = 3, base_delay: float = 2.0):
    """Retry with exponential backoff on transient errors."""
    for attempt in range(1, max_attempts + 1):
        try:
            return fn(), attempt
        except Exception as e:
            err_str = str(e).lower()
            is_retryable = any(k in err_str for k in [
                "rate_limit", "rate limit", "529", "503", "502",
                "overloaded", "timeout", "connection"
            ])
            if not is_retryable or attempt == max_attempts:
                raise
            delay = base_delay * (2 ** (attempt - 1))
            log.warning("Attempt %d/%d failed (%s). Retrying in %.1fs...", attempt, max_attempts, e, delay)
            time.sleep(delay)


# ── Anthropic adapter ─────────────────────────────────────────────────────────
class AnthropicAdapter:
    DEFAULT_MODEL = "claude-sonnet-4-20250514"

    def __init__(self, api_key: str, model: Optional[str] = None) -> None:
        try:
            import anthropic as _anthropic
            self._client = _anthropic.Anthropic(api_key=api_key)
        except ImportError:
            raise ImportError("Run: pip install anthropic")
        self.model = model or self.DEFAULT_MODEL

    def call(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 1500,
        max_attempts: int = 3,
    ) -> LLMResponse:
        def _call():
            return self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )

        result, attempts = _with_retry(_call, max_attempts=max_attempts)
        content = result.content[0].text
        return LLMResponse(
            content=content,
            provider="anthropic",
            model=self.model,
            input_tokens=result.usage.input_tokens,
            output_tokens=result.usage.output_tokens,
            attempts=attempts,
        )


# ── OpenAI adapter ────────────────────────────────────────────────────────────
class OpenAIAdapter:
    DEFAULT_MODEL = "gpt-4o"

    def __init__(self, api_key: str, model: Optional[str] = None) -> None:
        try:
            import openai as _openai
            self._client = _openai.OpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("Run: pip install openai")
        self.model = model or self.DEFAULT_MODEL

    def call(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 1500,
        max_attempts: int = 3,
    ) -> LLMResponse:
        def _call():
            return self._client.chat.completions.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_message},
                ],
                response_format={"type": "json_object"},  # enforces JSON mode
            )

        result, attempts = _with_retry(_call, max_attempts=max_attempts)
        content = result.choices[0].message.content or ""
        usage   = result.usage
        return LLMResponse(
            content=content,
            provider="openai",
            model=self.model,
            input_tokens=usage.prompt_tokens,
            output_tokens=usage.completion_tokens,
            attempts=attempts,
        )


# ── Factory — auto-detects provider from environment ─────────────────────────
def build_llm_client(
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> AnthropicAdapter | OpenAIAdapter:
    """
    Returns the correct adapter based on available API keys.
    Priority: explicit provider arg > ANTHROPIC_API_KEY > OPENAI_API_KEY

    Usage:
        client = build_llm_client()                  # auto-detect
        client = build_llm_client("anthropic")       # force Anthropic
        client = build_llm_client("openai", "gpt-4o-mini")
    """
    provider = (provider or "").lower()

    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    openai_key    = os.getenv("OPENAI_API_KEY", "")

    if provider == "anthropic" or (not provider and anthropic_key):
        if not anthropic_key:
            raise EnvironmentError("ANTHROPIC_API_KEY is not set.")
        log.info("Using Anthropic adapter (model=%s)", model or AnthropicAdapter.DEFAULT_MODEL)
        return AnthropicAdapter(api_key=anthropic_key, model=model)

    if provider == "openai" or (not provider and openai_key):
        if not openai_key:
            raise EnvironmentError("OPENAI_API_KEY is not set.")
        log.info("Using OpenAI adapter (model=%s)", model or OpenAIAdapter.DEFAULT_MODEL)
        return OpenAIAdapter(api_key=openai_key, model=model)

    raise EnvironmentError(
        "No LLM API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY in your .env file."
    )
