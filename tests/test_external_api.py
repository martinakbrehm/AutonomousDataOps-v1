import asyncio
from tools.external_api import register_provider, get_provider, MockProvider, HttpProvider


def test_register_and_get_mock():
    mock = MockProvider({"ok": True})
    register_provider("tmp_mock", mock)
    p = get_provider("tmp_mock")
    resp = asyncio.run(p.request('/test', {'q': 1}))
    assert resp['response']['ok'] is True


def test_default_mock_available():
    p = get_provider('mock')
    resp = asyncio.run(p.request('/x', None))
    assert 'mock' in resp or 'response' in resp
