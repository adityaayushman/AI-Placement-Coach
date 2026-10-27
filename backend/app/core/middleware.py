import time
import uuid
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.logging import request_id_var


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attach an X-Request-ID to every request/response and to log records."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex
        token = request_id_var.set(rid)
        try:
            response = await call_next(request)
        finally:
            request_id_var.reset(token)
        response.headers["X-Request-ID"] = rid
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window limit per client IP on auth endpoints. In-memory, so per process; put a
    shared limiter (Redis) in front when running several API instances."""

    def __init__(self, app: object, per_minute: int, prefix: str = "/api/v1/auth") -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self.per_minute = per_minute
        self.prefix = prefix
        self.hits: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method == "POST" and request.url.path.startswith(self.prefix):
            ip = request.client.host if request.client else "unknown"
            now = time.monotonic()
            window = self.hits[ip]
            while window and now - window[0] > 60:
                window.popleft()
            if len(window) >= self.per_minute:
                return JSONResponse(
                    {"detail": "Too many requests"}, status_code=429, headers={"Retry-After": "60"}
                )
            window.append(now)
        return await call_next(request)


class Metrics:
    def __init__(self) -> None:
        self.requests: dict[str, int] = defaultdict(int)
        self.latency_ms: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=500))

    def snapshot(self) -> dict[str, object]:
        out: dict[str, object] = {}
        for key, count in sorted(self.requests.items()):
            lat = sorted(self.latency_ms[key])
            p95 = lat[int(0.95 * (len(lat) - 1))] if lat else None
            out[key] = {"count": count, "p95_ms": round(p95, 1) if p95 is not None else None}
        return out


METRICS = Metrics()


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        route = request.scope.get("route")
        key = f"{request.method} {getattr(route, 'path', 'unmatched')}"
        METRICS.requests[key] += 1
        METRICS.latency_ms[key].append((time.perf_counter() - start) * 1000)
        return response
