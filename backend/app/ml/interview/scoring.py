"""Answer scoring: content correctness, communication, confidence/delivery (each 0-100).

All rules are transparent heuristics; every point lost produces a feedback line. Automated scores
are not validated against human raters yet (see docs/EVALUATION.md)."""

import re
from typing import Any

from app.ml.embeddings import get_embedder
from app.ml.interview.audio import Prosody

FILLERS = [
    "um",
    "uh",
    "erm",
    "like",
    "you know",
    "basically",
    "actually",
    "literally",
    "sort of",
    "kind of",
    "i mean",
]
HEDGES = ["i think", "maybe", "probably", "i guess", "not sure", "i don't know"]
STRUCTURE = [
    "first",
    "second",
    "then",
    "finally",
    "for example",
    "for instance",
    "because",
    "as a result",
    "situation",
    "task",
    "action",
    "result",
    "in summary",
    "overall",
]


def _count(text: str, phrases: list[str]) -> int:
    return sum(len(re.findall(rf"\b{re.escape(p)}\b", text)) for p in phrases)


def _clip(x: float) -> float:
    return round(max(0.0, min(100.0, x)), 1)


def score_answer(
    transcript: str,
    reference: str,
    key_points: list[str],
    prosody: Prosody | None = None,
) -> tuple[dict[str, Any], list[str]]:
    text = transcript.lower().strip()
    words = re.findall(r"[a-z']+", text)
    n = len(words)
    feedback: list[str] = []

    # Content: key-point coverage (exact or semantically close) + similarity to reference.
    embedder = get_embedder()
    sentences = [s for s in re.split(r"[.!?\n]+", text) if s.strip()] or [text or " "]
    covered: list[str] = []
    if key_points:
        sims = embedder.similarity(key_points, sentences)
        for i, kp in enumerate(key_points):
            if kp.lower() in text or float(sims[i].max()) >= 0.3:
                covered.append(kp)
    coverage = len(covered) / len(key_points) if key_points else 0.0
    ref_sim = float(embedder.similarity([text or " "], [reference])[0, 0]) if reference else 0.0
    content = _clip(100 * (0.7 * coverage + 0.3 * min(ref_sim / 0.5, 1.0)))
    missed = [kp for kp in key_points if kp not in covered]
    if missed:
        feedback.append("Cover these points: " + "; ".join(missed[:3]) + ".")

    # Communication: length, structure markers, filler and hedge rate.
    fillers = _count(text, FILLERS)
    hedges = _count(text, HEDGES)
    structure = _count(text, STRUCTURE)
    filler_rate = fillers / n if n else 0.0
    comm = 100.0
    if n < 40:
        comm -= 35
        feedback.append(f"Your answer was {n} words; aim for 80-200 with an example.")
    elif n > 300:
        comm -= 15
        feedback.append("Tighten the answer; keep it under about two minutes.")
    if structure == 0:
        comm -= 20
        feedback.append("Signpost your answer (first, then, for example, as a result).")
    if filler_rate > 0.03:
        comm -= min(30, filler_rate * 600)
        feedback.append(f"Cut filler words ({fillers} found, e.g. 'um', 'like', 'basically').")
    communication = _clip(comm)

    # Delivery/confidence: hedging always; pace, pauses and pitch when audio is available.
    conf = 100.0 - min(30, hedges * 10)
    if hedges:
        feedback.append("State conclusions directly instead of hedging ('I think', 'maybe').")
    wpm = None
    if prosody and prosody.duration_s > 3:
        wpm = round(n / (prosody.duration_s / 60), 1)
        if wpm < 100:
            conf -= 15
            feedback.append(f"Pace was {wpm} words/min; aim for roughly 120-160.")
        elif wpm > 185:
            conf -= 15
            feedback.append(f"Pace was {wpm} words/min; slow down slightly.")
        if prosody.pause_ratio > 0.45:
            conf -= 15
            feedback.append("Long silences; pause briefly to think, then keep going.")
        if prosody.pitch_variability is not None and prosody.pitch_variability < 0.08:
            conf -= 10
            feedback.append("Delivery sounded flat; vary your tone to stress key points.")
    delivery = _clip(conf)

    scores = {
        "content": content,
        "communication": communication,
        "delivery": delivery,
        "overall": round(0.5 * content + 0.3 * communication + 0.2 * delivery, 1),
        "details": {
            "words": n,
            "key_points_covered": covered,
            "reference_similarity": round(ref_sim, 3),
            "filler_count": fillers,
            "hedge_count": hedges,
            "wpm": wpm,
            "pause_ratio": round(prosody.pause_ratio, 3) if prosody else None,
            "pitch_variability": (
                round(prosody.pitch_variability, 3)
                if prosody and prosody.pitch_variability is not None
                else None
            ),
            "audio_analyzed": prosody is not None,
        },
    }
    if not feedback:
        feedback.append("Strong answer: clear, structured and on point.")
    return scores, feedback
