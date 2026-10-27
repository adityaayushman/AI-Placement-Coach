"""Resume report: sections, skills, ATS checks, semantic match and ranked skill gaps."""

from typing import Any

from app.ml.embeddings import get_embedder
from app.ml.resume.ats import ats_score, run_checks
from app.ml.resume.parsing import detect_sections
from app.ml.resume.skills import extract_skills
from app.ml.resume.taxonomy import TAXONOMY, category_of, skill_weight

# A JD skill counts as semantically covered when a resume section is this similar to the
# skill's description terms (taxonomy name + aliases). Tuned on the fixture set in tests/.
SEMANTIC_COVER_THRESHOLD = 0.35
MATCH_SECTIONS = ["summary", "experience", "projects", "skills"]


def _skill_text(skill: str) -> str:
    _, aliases, _ = TAXONOMY.get(skill, ("", [], []))
    return " ".join([skill, *aliases])


def analyze(text: str, jd: dict[str, Any] | None = None) -> dict[str, Any]:
    sections = detect_sections(text)
    skills = extract_skills(text, sections.get("skills", ""))
    report: dict[str, Any] = {
        "sections": sorted(sections),
        "skills_found": sorted(skills),
        "skill_evidence": skills,
        "embedder": get_embedder().name,
    }

    coverage: float | None = None
    if jd:
        report |= _match(text, sections, skills, jd)
        coverage = report["keyword_coverage"]

    checks = run_checks(text, sections, coverage)
    score, check_rows = ats_score(checks)
    report["ats_score"] = score
    report["ats_checks"] = check_rows
    report["fixes"] = [c["fix"] for c in check_rows if c["fix"]]
    return report


def _match(
    text: str, sections: dict[str, str], skills: dict[str, str], jd: dict[str, Any]
) -> dict[str, Any]:
    embedder = get_embedder()
    jd_text = jd.get("text", "")
    names = [s for s in MATCH_SECTIONS if s in sections]
    sims = embedder.similarity([sections[s] for s in names] + [text], [jd_text])
    per_section = {s: round(float(sims[i, 0]), 3) for i, s in enumerate(names)}
    overall = round(float(sims[-1, 0]), 3)

    required = jd.get("required_skills") or []
    company_type = jd.get("type", "product")
    gaps: list[dict[str, Any]] = []
    covered = 0
    req_names = [r["skill"] for r in required]
    evidence = [sections[n] for n in ("projects", "experience") if n in sections] or [text]
    sem = embedder.similarity([_skill_text(s) for s in req_names], evidence) if req_names else None
    for i, req in enumerate(required):
        skill = req["skill"]
        weight = float(req.get("weight", 1.0)) * skill_weight(skill, company_type)
        if skill in skills:
            covered += 1
            continue
        best = float(sem[i].max()) if sem is not None and sem.shape[1] else 0.0
        if best >= SEMANTIC_COVER_THRESHOLD:
            covered += 1
            continue
        gaps.append(
            {
                "skill": skill,
                "category": category_of(skill),
                "importance": round(weight, 3),
                "closest_evidence_similarity": round(best, 3),
                "reason": f"Required by {jd.get('company', 'the role')} but not found in your "
                "resume" + (" (only weakly related text)" if best > 0.15 else "") + ".",
            }
        )
    gaps.sort(key=lambda g: g["importance"], reverse=True)
    return {
        "match_scores": {"overall": overall, "sections": per_section},
        "keyword_coverage": round(covered / len(required), 3) if required else 1.0,
        "skill_gaps": gaps,
    }
