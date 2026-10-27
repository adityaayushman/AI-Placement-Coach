"""SYNTHETIC study simulation for the "skill-gap tracking gain" metric.

Simulated learners hold a hidden known/unknown state per skill. Each session a policy picks one
skill to study; studying teaches it with probability LEARN_READY when its prerequisites are known
(LEARN_BLOCKED otherwise), and a quiz answer on that skill is observed (slip/guess noise).

Gain = weighted share of target skills mastered under the recommender vs a baseline policy.
The simulator shares the recommender's assumptions (prerequisite graph, company weights), so the
result shows the loop works as designed; it is not evidence about real students."""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from app.ml.knowledge import bkt
from app.ml.knowledge.recommender import rank
from app.ml.resume.taxonomy import prerequisites_of, skill_weight

LEARN_READY = 0.3
LEARN_BLOCKED = 0.08

Policy = Callable[[dict[str, float], list[str], int, np.random.Generator], str]


@dataclass
class Result:
    policy: str
    gap_closed: float  # weighted share of target skills truly known at the end
    std: float


def _recommender(company_type: str) -> Policy:
    def pick(est: dict[str, float], skills: list[str], _t: int, _r: np.random.Generator) -> str:
        top = rank(est, skills, company_type, limit=1)
        return top[0].skill if top else skills[0]

    return pick


def _random(est: dict[str, float], skills: list[str], _t: int, rng: np.random.Generator) -> str:
    return skills[int(rng.integers(len(skills)))]


def _syllabus(est: dict[str, float], skills: list[str], t: int, _r: np.random.Generator) -> str:
    return skills[t % len(skills)]


def _learner_skills(skills: list[str]) -> list[str]:
    """Target skills plus any prerequisites, so blocked skills can be unblocked."""
    out = list(skills)
    for s in skills:
        out += [p for p in prerequisites_of(s) if p not in out]
    return out


def run(
    skills: list[str],
    company_type: str,
    sessions: int = 30,
    learners: int = 400,
    seed: int = 7,
) -> list[Result]:
    pool = _learner_skills(skills)
    weights = {s: skill_weight(s, company_type) for s in skills}
    policies: dict[str, Policy] = {
        "recommender (BKT + ranking)": _recommender(company_type),
        "random topic": _random,
        "fixed syllabus order": _syllabus,
    }
    results = []
    for name, policy in policies.items():
        rng = np.random.default_rng(seed)  # same learners for every policy
        closed = []
        for _ in range(learners):
            known = {s: rng.random() < 0.25 for s in pool}
            est = {s: bkt.DEFAULT.p_init for s in pool}
            for t in range(sessions):
                s = policy(est, pool, t, rng)
                ready = all(known.get(p, True) for p in prerequisites_of(s))
                if not known[s] and rng.random() < (LEARN_READY if ready else LEARN_BLOCKED):
                    known[s] = True
                p_correct = (1 - bkt.DEFAULT.p_slip) if known[s] else bkt.DEFAULT.p_guess
                est[s] = bkt.update(est[s], bool(rng.random() < p_correct))
            total = sum(weights.values())
            closed.append(sum(weights[s] for s in skills if known[s]) / total)
        arr = np.array(closed)
        results.append(Result(name, round(float(arr.mean()), 4), round(float(arr.std()), 4)))
    return results


def gain(results: list[Result], baseline: str) -> float:
    rec = results[0].gap_closed
    base = next(r.gap_closed for r in results if r.policy == baseline)
    return round((rec - base) / base, 4) if base else float("inf")
