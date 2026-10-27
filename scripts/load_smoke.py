"""Load smoke test: concurrent requests against a running API, reports p50/p95 latency.

    python scripts/load_smoke.py http://127.0.0.1:8000 [requests] [concurrency]

Use 127.0.0.1 on Windows: 'localhost' tries IPv6 first and adds ~2 s per new connection.

Registers one throwaway student, then hammers non-ML read endpoints."""

import statistics
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

import httpx

ENDPOINTS = [
    "/api/v1/health",
    "/api/v1/auth/me",
    "/api/v1/me/profile",
    "/api/v1/consents",
    "/api/v1/jobs",
    "/api/v1/assessments",
]


def main(base: str, total: int = 300, workers: int = 20) -> None:
    with httpx.Client(base_url=base, timeout=30) as c:
        r = c.post(
            "/api/v1/auth/register",
            json={
                "email": f"load-{uuid.uuid4().hex[:8]}@example.com",
                "password": "load-test-pass",
            },
        )
        r.raise_for_status()
        headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    # One pooled client, as a browser or proxy would keep connections alive.
    client = httpx.Client(
        base_url=base, timeout=30, limits=httpx.Limits(max_connections=workers)
    )

    def hit(i: int) -> tuple[int, float]:
        start = time.perf_counter()
        resp = client.get(ENDPOINTS[i % len(ENDPOINTS)], headers=headers)
        return resp.status_code, (time.perf_counter() - start) * 1000

    with ThreadPoolExecutor(workers) as pool:
        results = list(pool.map(hit, range(total)))
    client.close()
    lat = sorted(ms for _, ms in results)
    errors = sum(1 for code, _ in results if code >= 400)
    p95 = lat[int(0.95 * (len(lat) - 1))]
    print(
        f"n={total} concurrency={workers} errors={errors} "
        f"p50={statistics.median(lat):.1f}ms p95={p95:.1f}ms"
    )
    sys.exit(1 if errors or p95 > 500 else 0)


if __name__ == "__main__":
    main(sys.argv[1], *(int(a) for a in sys.argv[2:4]))
