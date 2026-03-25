import os
from typing import Optional
import json
from cachetools import TTLCache

from tools.external_api import get_provider, register_provider, MockProvider


class LLMAdapter:
    """Adapter to call different LLM API providers registered in tools.external_api.

    The adapter expects a provider registered under a name (eg. 'mock' or 'http').
    """

    def __init__(self, provider_name: str = "mock"):
        self.provider_name = provider_name
        # Configurável via env: tamanho do cache e TTL em segundos
        cache_size = int(os.environ.get("LLM_CACHE_SIZE", "1024"))
        cache_ttl = int(os.environ.get("LLM_CACHE_TTL", "300"))
        self._cache = TTLCache(maxsize=cache_size, ttl=cache_ttl)
        try:
            self.provider = get_provider(provider_name)
        except KeyError:
            # fallback to mock
            mock = MockProvider({"text": "[MOCK LLM] clean->analyze->transform"})
            register_provider("mock", mock)
            self.provider = mock

    def is_available(self) -> bool:
        return self.provider is not None

    def generate(self, prompt: str) -> str:
        # Check cache first (keyed by provider + prompt)
        key = (self.provider_name, prompt)
        if key in self._cache:
            return self._cache[key]

        # Synchronous wrapper calling async provider
        import asyncio

        async def _call():
            return await self.provider.request("/llm", {"prompt": prompt})

        resp = asyncio.run(_call())
        # If provider returns dict, try to return a sensible string
        if isinstance(resp, dict):
            # prefer 'text' or 'response' fields
            if "text" in resp:
                return resp["text"]
            if "response" in resp and isinstance(resp["response"], dict):
                out = json.dumps(resp["response"])
                self._cache[key] = out
                return out
            out = json.dumps(resp)
            self._cache[key] = out
            return out
        out = str(resp)
        self._cache[key] = out
        return out

