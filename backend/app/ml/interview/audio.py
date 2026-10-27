"""Prosody features from 16-bit PCM WAV using numpy only (librosa-free).

Pause ratio: share of 30 ms frames whose RMS energy is below an adaptive threshold.
Pitch: autocorrelation F0 estimate on voiced frames (75-400 Hz); we report its coefficient of
variation as "pitch variability". These are coarse signals; treat them as indicative."""

import io
import wave
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass
class Prosody:
    duration_s: float
    pause_ratio: float
    pitch_mean_hz: float | None
    pitch_variability: float | None


def read_wav(data: bytes) -> tuple[NDArray[np.float64], int]:
    with wave.open(io.BytesIO(data)) as wf:
        if wf.getsampwidth() != 2:
            raise ValueError("Expected 16-bit PCM WAV")
        rate, channels = wf.getframerate(), wf.getnchannels()
        frames = wf.readframes(min(wf.getnframes(), rate * 600))  # cap at 10 minutes
    samples = np.frombuffer(frames, dtype=np.int16).astype(np.float64) / 32768.0
    if channels > 1:
        samples = samples.reshape(-1, channels).mean(axis=1)
    return samples, rate


def _f0(frame: NDArray[np.float64], rate: int) -> float | None:
    frame = frame - frame.mean()
    corr = np.correlate(frame, frame, mode="full")[len(frame) - 1 :]
    lo, hi = int(rate / 400), int(rate / 75)
    if hi >= len(corr) or corr[0] <= 0:
        return None
    lag = lo + int(np.argmax(corr[lo:hi]))
    return rate / lag if corr[lag] / corr[0] > 0.3 else None


def prosody(data: bytes) -> Prosody:
    samples, rate = read_wav(data)
    duration = len(samples) / rate if rate else 0.0
    size = int(0.03 * rate)
    if size == 0 or len(samples) < size:
        return Prosody(duration, 1.0, None, None)
    n = len(samples) // size
    frames = samples[: n * size].reshape(n, size)
    rms = np.sqrt((frames**2).mean(axis=1))
    threshold = max(0.02, 0.3 * float(np.percentile(rms, 90)))
    voiced = rms >= threshold
    pause_ratio = float(1 - voiced.mean())
    pitches = [p for f in frames[voiced][::3] if (p := _f0(f, rate))]
    if len(pitches) < 5:
        return Prosody(duration, pause_ratio, None, None)
    arr = np.array(pitches)
    return Prosody(duration, pause_ratio, float(arr.mean()), float(arr.std() / arr.mean()))
