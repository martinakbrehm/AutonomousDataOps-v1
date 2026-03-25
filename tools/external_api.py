import httpx
from typing import Any, Optional, Dict
import asyncio


class APIProvider:
    """Base class for external API providers."""

    name: str = "base"

    async def request(self, path: str, params: Optional[Dict] = None) -> Any:
        raise NotImplementedError()


class HttpProvider(APIProvider):
    name = "http"

    def __init__(self, base_url: str):
        self.base_url = base_url

    async def request(self, path: str, params: Optional[Dict] = None) -> Any:
        async with httpx.AsyncClient() as client:
            r = await client.get(self.base_url + path, params=params)
            r.raise_for_status()
            return r.json()


class MockProvider(APIProvider):
    name = "mock"

    def __init__(self, response: Optional[Any] = None):
        self._response = response or {"mock": True}

    async def request(self, path: str, params: Optional[Dict] = None) -> Any:
        # emulate async behavior
        await asyncio.sleep(0)
        return {"path": path, "params": params, "response": self._response}


# simple registry for providers
_PROVIDERS: Dict[str, APIProvider] = {}


def register_provider(name: str, provider: APIProvider):
    _PROVIDERS[name] = provider


def get_provider(name: str) -> APIProvider:
    if name in _PROVIDERS:
        return _PROVIDERS[name]
    raise KeyError(f"Provider {name} not registered")


# Register a default mock provider
register_provider("mock", MockProvider())

