# adapters/__init__.py — Public exports for the cognitive adapters package.
# Created: feat/cognitive-adapters — exposes all engine adapters and the engine_from_env()
#   auto-detection helper. All adapters use soft imports (never hard-fail on missing deps).

from __future__ import annotations

from soul_protocol.runtime.cognitive.adapters._auto import engine_from_env
from soul_protocol.runtime.cognitive.adapters._callable import CallableEngine
from soul_protocol.runtime.cognitive.adapters.anthropic import AnthropicEngine
from soul_protocol.runtime.cognitive.adapters.litellm import LiteLLMEngine
from soul_protocol.runtime.cognitive.adapters.ollama import OllamaEngine
from soul_protocol.runtime.cognitive.adapters.openai import OpenAIEngine

__all__ = [
    "AnthropicEngine",
    "OpenAIEngine",
    "OllamaEngine",
    "LiteLLMEngine",
    "CallableEngine",
    "engine_from_env",
]
