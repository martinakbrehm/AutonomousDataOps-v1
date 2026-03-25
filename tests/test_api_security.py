import os
from fastapi.testclient import TestClient
import pipelines.etl_pipeline as etl


def test_health():
    from api.main import app
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200


def test_run_requires_key(tmp_path, monkeypatch):
    from api.main import app
    client = TestClient(app)
    p = tmp_path / 's.csv'
    p.write_text("id,name\n1,A\n")
    with open(p, 'rb') as f:
        r = client.post("/run", files={"file": ("s.csv", f, "text/csv")}, data={"clean": "true"})
    assert r.status_code == 401


def test_run_with_key(tmp_path, monkeypatch):
    monkeypatch.setenv('API_KEY', 'testkey')
    # patch heavy pipeline to a lightweight stub
    monkeypatch.setattr(etl, 'run_pipeline_from_file', lambda path, req: (None, {"rows": 1}))
    from api.main import app
    client = TestClient(app)
    p = tmp_path / 's.csv'
    p.write_text("id,name\n1,A\n")
    with open(p, 'rb') as f:
        headers = {"x-api-key": "testkey"}
        r = client.post("/run", files={"file": ("s.csv", f, "text/csv")}, headers=headers, data={"clean": "true"})
    assert r.status_code == 200


def test_rate_limit_exceeded(tmp_path, monkeypatch):
    monkeypatch.setenv('API_KEY', 'rlkey')
    monkeypatch.setenv('RATE_LIMIT_MAX', '2')
    monkeypatch.setenv('RATE_LIMIT_WINDOW', '60')
    # patch heavy pipeline to a lightweight stub
    monkeypatch.setattr(etl, 'run_pipeline_from_file', lambda path, req: (None, {"rows": 1}))
    # ensure Redis is mocked so tests run without external deps
    try:
        import fakeredis
        import redis
        monkeypatch.setenv('REDIS_URL', 'redis://localhost:6379/0')
        # monkeypatch redis.Redis.from_url to return fakeredis instance
        monkeypatch.setattr(redis.Redis, 'from_url', staticmethod(lambda url: fakeredis.FakeRedis()))
    except Exception:
        pass
    from api.main import app
    client = TestClient(app)
    p = tmp_path / 's.csv'
    p.write_text("id,name\n1,A\n")
    headers = {"x-api-key": "rlkey"}
    # first two should pass
    with open(p, 'rb') as f:
        r1 = client.post("/run", files={"file": ("s.csv", f, "text/csv")}, headers=headers, data={"clean": "true"})
    assert r1.status_code == 200
    with open(p, 'rb') as f:
        r2 = client.post("/run", files={"file": ("s.csv", f, "text/csv")}, headers=headers, data={"clean": "true"})
    assert r2.status_code == 200
    # third should be rate limited
    with open(p, 'rb') as f:
        r3 = client.post("/run", files={"file": ("s.csv", f, "text/csv")}, headers=headers, data={"clean": "true"})
    assert r3.status_code == 429
