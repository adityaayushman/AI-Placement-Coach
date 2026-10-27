"""Rank next skills to work on: gap_size x skill_weight x prerequisite_readiness.

Pure function over plain data so it can be replay-tested offline."""

from dataclasses import dataclass

from app.ml.knowledge.bkt import DEFAULT
from app.ml.resume.taxonomy import category_of, prerequisites_of, skill_weight

MASTERED = 0.85
IGNORE_PENALTY = 0.5  # each recent "ignore" halves an item's priority
# Unassessed prerequisites are assumed partly known so they shape, but do not block, ranking.
UNASSESSED_PREREQ = 0.7


@dataclass
class Ranked:
    skill: str
    priority: float
    reason: str


def rank(
    mastery: dict[str, float],
    target_skills: list[str],
    company_type: str,
    resume_gaps: set[str] | None = None,
    ignored: dict[str, int] | None = None,
    limit: int = 5,
) -> list[Ranked]:
    resume_gaps = resume_gaps or set()
    ignored = ignored or {}
    candidates: list[Ranked] = []
    for skill in dict.fromkeys(target_skills):
        p = mastery.get(skill, DEFAULT.p_init)
        if p >= MASTERED:
            continue
        gap = 1 - p
        weight = skill_weight(skill, company_type)
        prereqs = prerequisites_of(skill)
        readiness = (
            min(mastery.get(pr, UNASSESSED_PREREQ) for pr in prereqs) / MASTERED if prereqs else 1.0
        )
        readiness = min(1.0, max(readiness, 0.1))
        boost = 1.25 if skill in resume_gaps else 1.0
        priority = gap * weight * readiness * boost * IGNORE_PENALTY ** ignored.get(skill, 0)
        candidates.append(
            Ranked(
                skill,
                priority,
                _reason(skill, p, weight, prereqs, mastery, company_type, skill in resume_gaps),
            )
        )

    candidates.sort(key=lambda r: r.priority, reverse=True)
    # Diversity: at most two picks per category.
    picked: list[Ranked] = []
    per_cat: dict[str, int] = {}
    for r in candidates:
        cat = category_of(r.skill)
        if per_cat.get(cat, 0) >= 2:
            continue
        per_cat[cat] = per_cat.get(cat, 0) + 1
        picked.append(r)
        if len(picked) == limit:
            break
    return picked


def _reason(
    skill: str,
    p: float,
    weight: float,
    prereqs: list[str],
    mastery: dict[str, float],
    company_type: str,
    in_resume_gap: bool,
) -> str:
    parts = [f"Estimated mastery {round(p * 100)}%"]
    if weight >= 0.8:
        parts.append(f"weighted highly by {company_type}-based companies")
    weak = [pr for pr in prereqs if mastery.get(pr, UNASSESSED_PREREQ) < 0.5]
    if weak:
        parts.append(f"shore up {', '.join(weak)} alongside it")
    elif prereqs:
        parts.append("prerequisites are in place")
    if in_resume_gap:
        parts.append("missing from your resume for your target role")
    return "; ".join(parts) + "."
