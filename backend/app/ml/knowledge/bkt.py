"""Bayesian Knowledge Tracing (Corbett & Anderson, 1994), one skill at a time.

p_known is P(L_t). After each observation we apply Bayes' rule with slip/guess, then the learning
transition. Default parameters are common textbook values, not fitted to our data."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BKTParams:
    p_init: float = 0.2
    p_learn: float = 0.15
    p_slip: float = 0.1
    p_guess: float = 0.2


DEFAULT = BKTParams()


def update(p_known: float, correct: bool, params: BKTParams = DEFAULT) -> float:
    s, g = params.p_slip, params.p_guess
    if correct:
        posterior = p_known * (1 - s) / (p_known * (1 - s) + (1 - p_known) * g)
    else:
        posterior = p_known * s / (p_known * s + (1 - p_known) * (1 - g))
    return posterior + (1 - posterior) * params.p_learn


def predict_correct(p_known: float, params: BKTParams = DEFAULT) -> float:
    return p_known * (1 - params.p_slip) + (1 - p_known) * params.p_guess


def learn_only(p_known: float, params: BKTParams = DEFAULT) -> float:
    """Transition without evidence (e.g. completing a study resource)."""
    return p_known + (1 - p_known) * params.p_learn * 0.5
