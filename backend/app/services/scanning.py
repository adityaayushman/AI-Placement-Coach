"""Optional malware scanning of uploads through a clamd daemon (ClamAV INSTREAM protocol).

Off unless CLAMAV_HOST is set. When it is set the check fails closed: if clamd cannot be reached,
the upload is rejected rather than stored unscanned."""

import socket
import struct

from fastapi import HTTPException, status

from app.config import get_settings

CHUNK = 64 * 1024


class ScanError(RuntimeError):
    pass


def clamd_scan(data: bytes, host: str, port: int, timeout: float = 10.0) -> str | None:
    """Return the signature name if clamd flags the data, else None."""
    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.sendall(b"zINSTREAM\0")
        for i in range(0, len(data), CHUNK):
            chunk = data[i : i + CHUNK]
            sock.sendall(struct.pack("!L", len(chunk)) + chunk)
        sock.sendall(struct.pack("!L", 0))
        reply = b""
        while not reply.endswith(b"\0"):
            part = sock.recv(4096)
            if not part:
                break
            reply += part
    text = reply.rstrip(b"\0").decode(errors="replace")
    if text.endswith("OK"):
        return None
    if text.endswith("FOUND"):
        return text.split(":", 1)[-1].removesuffix("FOUND").strip()
    raise ScanError(f"unexpected clamd reply: {text!r}")


def ensure_clean(data: bytes) -> None:
    s = get_settings()
    if not s.clamav_host:
        return
    try:
        signature = clamd_scan(data, s.clamav_host, s.clamav_port)
    except (OSError, ScanError):
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "Virus scanner unavailable; try again later"
        ) from None
    if signature:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "The file was rejected by the virus scanner"
        )
