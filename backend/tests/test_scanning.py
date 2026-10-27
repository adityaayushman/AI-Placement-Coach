import socket
import socketserver
import struct
import threading
from collections.abc import Callable, Iterator
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.services.scanning import clamd_scan, ensure_clean
from tests.conftest import Headers
from tests.fixtures import STRONG_RESUME

# The standard, harmless antivirus test string.
EICAR = rb"X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"


class FakeClamd(socketserver.BaseRequestHandler):
    """Speaks enough of clamd's INSTREAM protocol to flag the EICAR string."""

    def handle(self) -> None:
        assert self.request.recv(10) == b"zINSTREAM\0"
        data = b""
        while True:
            (size,) = struct.unpack("!L", self._read(4))
            if size == 0:
                break
            data += self._read(size)
        verdict = b"stream: Eicar-Test-Signature FOUND" if EICAR in data else b"stream: OK"
        self.request.sendall(verdict + b"\0")

    def _read(self, n: int) -> bytes:
        buf = b""
        while len(buf) < n:
            buf += self.request.recv(n - len(buf))
        return buf


@pytest.fixture
def clamd() -> Iterator[int]:
    server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), FakeClamd)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server.server_address[1]
    server.shutdown()
    server.server_close()


def _settings(port: int) -> SimpleNamespace:
    return SimpleNamespace(clamav_host="127.0.0.1", clamav_port=port)


def test_clamd_protocol_clean_and_infected(clamd: int) -> None:
    assert clamd_scan(b"plain resume text" * 10_000, "127.0.0.1", clamd) is None
    assert clamd_scan(b"prefix " + EICAR, "127.0.0.1", clamd) == "Eicar-Test-Signature"


def test_scanning_off_by_default() -> None:
    ensure_clean(EICAR)  # no CLAMAV_HOST configured: nothing to call, no error


def test_fails_closed_when_scanner_unreachable() -> None:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        dead_port = s.getsockname()[1]  # bound but not listening
    with (
        patch("app.services.scanning.get_settings", return_value=_settings(dead_port)),
        pytest.raises(HTTPException) as exc,
    ):
        ensure_clean(b"anything")
    assert exc.value.status_code == 503


def test_upload_rejected_when_infected(
    client: TestClient, make_student: Callable[..., Headers], clamd: int
) -> None:
    h = make_student()
    with patch("app.services.scanning.get_settings", return_value=_settings(clamd)):
        bad = client.post(
            "/api/v1/resumes",
            headers=h,
            files={"file": ("cv.txt", STRONG_RESUME.encode() + EICAR, "text/plain")},
        )
        good = client.post(
            "/api/v1/resumes",
            headers=h,
            files={"file": ("cv.txt", STRONG_RESUME.encode(), "text/plain")},
        )
    assert bad.status_code == 422
    assert "virus scanner" in bad.json()["detail"]
    assert good.status_code == 201
