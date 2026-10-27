import io
import wave
from collections.abc import Callable

import numpy as np
from fastapi.testclient import TestClient

from app.ml.interview.audio import prosody
from app.ml.interview.scoring import score_answer
from tests.conftest import Headers

REF = (
    "Use two pointers: slow moves one step, fast moves two. If they meet there is a cycle. "
    "O(n) time and O(1) space."
)
KPS = [
    "two pointers slow and fast",
    "fast moves two steps",
    "they meet if a cycle exists",
    "O(n) time and O(1) space",
]


def _wav(seconds_voiced: float, seconds_silent: float, rate: int = 16000) -> bytes:
    t = np.arange(int(rate * seconds_voiced)) / rate
    f0 = 140 + 40 * np.sin(2 * np.pi * 0.5 * t)  # varying pitch
    voiced = 0.4 * np.sin(2 * np.pi * np.cumsum(f0) / rate)
    signal = np.concatenate([voiced, np.zeros(int(rate * seconds_silent))])
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes((signal * 32767).astype(np.int16).tobytes())
    return buf.getvalue()


def test_prosody_features() -> None:
    p = prosody(_wav(6, 4))
    assert abs(p.duration_s - 10) < 0.1
    assert 0.3 < p.pause_ratio < 0.5
    assert p.pitch_mean_hz is not None and 100 < p.pitch_mean_hz < 200
    assert p.pitch_variability is not None and p.pitch_variability > 0.05


def test_good_answer_outscores_poor_answer() -> None:
    good = (
        "First, I would use two pointers, a slow one and a fast one. The fast pointer moves "
        "two steps while the slow moves one step. Then, if there is a cycle, they meet; "
        "if fast reaches null there is no cycle. As a result it runs in O(n) time and O(1) "
        "space, because we store nothing extra. For example, on a list of five nodes with "
        "a loop back to the second node, they meet inside the loop."
    )
    poor = "Um, I think maybe you like, basically check the list, I guess. Not sure."
    g, _ = score_answer(good, REF, KPS)
    p, feedback = score_answer(poor, REF, KPS)
    assert g["content"] > p["content"] + 30
    assert g["communication"] > p["communication"]
    assert g["delivery"] > p["delivery"]
    assert any("filler" in f.lower() for f in feedback)
    assert any("hedging" in f.lower() for f in feedback)


def test_session_flow_end_to_end(client: TestClient, make_student: Callable[..., Headers]) -> None:
    h = make_student()
    s = client.post(
        "/api/v1/interviews/sessions",
        headers=h,
        json={"role": "Software Engineer", "company_type": "product"},
    )
    assert s.status_code == 201
    session = s.json()
    assert len(session["questions"]) == 4
    assert {q["category"] for q in session["questions"]} == {"hr", "behavioral", "technical", "dsa"}

    q = session["questions"][0]
    r = client.post(
        f"/api/v1/interviews/sessions/{session['id']}/answers",
        headers=h,
        data={
            "question_id": str(q["id"]),
            "transcript": "I am a final year student. First I built an API.",
        },
        files={"audio": ("a.wav", _wav(5, 1), "audio/wav")},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert {"content", "communication", "delivery", "overall"} <= set(body["scores"])
    assert body["scores"]["details"]["audio_analyzed"] is True
    assert body["feedback"]


def test_audio_needs_recording_consent(
    client: TestClient, make_student: Callable[..., Headers]
) -> None:
    h = make_student(consents=("analytics",))
    session = client.post("/api/v1/interviews/sessions", headers=h, json={}).json()
    q = session["questions"][0]
    r = client.post(
        f"/api/v1/interviews/sessions/{session['id']}/answers",
        headers=h,
        data={"question_id": str(q["id"]), "transcript": "hello"},
        files={"audio": ("a.wav", _wav(2, 0), "audio/wav")},
    )
    assert r.status_code == 403
    text_only = client.post(
        f"/api/v1/interviews/sessions/{session['id']}/answers",
        headers=h,
        data={"question_id": str(q["id"]), "transcript": "hello there"},
    )
    assert text_only.status_code == 201
