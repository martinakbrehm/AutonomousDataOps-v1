import os
import time
from fastapi import HTTPException, status
from typing import Optional

_REDIS_CLIENT = None
_REDIS_URL = os.getenv("REDIS_URL")
if _REDIS_URL:
    try:
        import redis

        _REDIS_CLIENT = redis.Redis.from_url(_REDIS_URL)
    except Exception:
        _REDIS_CLIENT = None


_RATE_STATE: dict = {}


def verify_api_key(key: str | None, sql_memory: Optional[object] = None):
    expected = os.getenv("API_KEY", "dev-key")
    if not key or key != expected:
        if sql_memory is not None and hasattr(sql_memory, "log"):
            try:
                sql_memory.log("auth", "failed_auth", "invalid_api_key_attempt")
            except Exception:
                pass
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key")
    # check rate limit for this key
    max_requests = int(os.getenv("RATE_LIMIT_MAX", "60"))
    window = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    check_rate_limit(key, max_requests=max_requests, window_seconds=window, sql_memory=sql_memory)


def check_rate_limit(key: str, max_requests: int = 60, window_seconds: int = 60, sql_memory: Optional[object] = None):
    # Prefer Redis-backed rate limiting when available
    if _REDIS_CLIENT is not None:
        try:
            redis_key = f"rl:{key}"
            current = _REDIS_CLIENT.incr(redis_key)
            if current == 1:
                _REDIS_CLIENT.expire(redis_key, window_seconds)
            if current > max_requests:
                if sql_memory is not None and hasattr(sql_memory, "log"):
                    try:
                        sql_memory.log("auth", "rate_limited", f"key={key} exceeded {max_requests}/{window_seconds}s")
                    except Exception:
                        pass
                raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
            return True
        except Exception:
            # fall back to in-memory
            pass

    now = time.time()
    rec = _RATE_STATE.get(key)
    if rec is None:
        _RATE_STATE[key] = [now]
        return True
    # keep timestamps within window
    rec = [t for t in rec if now - t <= window_seconds]
    if len(rec) >= max_requests:
        if sql_memory is not None and hasattr(sql_memory, "log"):
            try:
                sql_memory.log("auth", "rate_limited", f"key={key} exceeded {max_requests}/{window_seconds}s")
            except Exception:
                pass
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
    rec.append(now)
    _RATE_STATE[key] = rec
    return True


def save_upload_file(upload_file, dest_path: str, allowed_exts=None, max_size: int = 10 * 1024 * 1024):
    """Save uploaded file in streaming manner and enforce extension and size limits.

    - allowed_exts: list of lowercase extensions (e.g. ['.csv', '.xlsx'])
    - max_size: maximum bytes allowed
    """
    if allowed_exts is None:
        allowed_exts = [".csv", ".xls", ".xlsx"]
    fname = upload_file.filename or "upload"
    _, ext = os.path.splitext(fname)
    ext = ext.lower()
    if ext not in allowed_exts:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported file extension: {ext}")

    total = 0
    chunk_size = 1024 * 64
    with open(dest_path, "wb") as out:
        while True:
            chunk = upload_file.file.read(chunk_size)
            if not chunk:
                break
            total += len(chunk)
            if total > max_size:
                out.close()
                try:
                    os.remove(dest_path)
                except Exception:
                    pass
                raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")
            out.write(chunk)
