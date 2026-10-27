"""Rule-based, explainable ATS checks. Each rule reports points earned, max, and a fix."""

import re
from dataclasses import asdict, dataclass
from typing import Any

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
_PHONE = re.compile(r"(\+?\d[\d\s-]{8,}\d)")
_METRIC = re.compile(r"\d+(\.\d+)?\s*(%|x\b|k\b|ms\b|users|requests|hours|percent)", re.I)
_BULLET = re.compile(r"^\s*([•\-*▪◦]|\d+\.)\s+", re.M)
_ACTION_VERBS = {
    "built",
    "developed",
    "designed",
    "implemented",
    "led",
    "created",
    "improved",
    "reduced",
    "optimized",
    "automated",
    "deployed",
    "analyzed",
    "launched",
    "migrated",
    "integrated",
}


@dataclass
class Check:
    id: str
    label: str
    points: float
    max_points: float
    passed: bool
    detail: str
    fix: str


def run_checks(text: str, sections: dict[str, str], keyword_coverage: float | None) -> list[Check]:
    words = len(text.split())
    checks: list[Check] = []

    core = ["education", "experience", "projects", "skills"]
    present = [s for s in core if s in sections]
    missing = [s for s in core if s not in sections]
    checks.append(
        Check(
            "sections",
            "Standard section headings",
            20 * len(present) / len(core),
            20,
            not missing,
            f"Found: {', '.join(present) or 'none'}.",
            f"Add clearly titled sections: {', '.join(missing)}." if missing else "",
        )
    )

    parseable = words >= 80 and sum(c.isalpha() for c in text) / max(len(text), 1) > 0.5
    checks.append(
        Check(
            "parseable",
            "Text is machine-readable",
            15 if parseable else 0,
            15,
            parseable,
            f"{words} words extracted.",
            ""
            if parseable
            else "Export from a word processor; avoid scanned images and text boxes.",
        )
    )

    has_email, has_phone = bool(_EMAIL.search(text)), bool(_PHONE.search(text))
    contact_pts = 5 * has_email + 5 * has_phone
    checks.append(
        Check(
            "contact",
            "Contact details",
            contact_pts,
            10,
            has_email and has_phone,
            f"Email {'found' if has_email else 'missing'}, "
            f"phone {'found' if has_phone else 'missing'}.",
            "" if has_email and has_phone else "Put email and phone in the header as plain text.",
        )
    )

    good_len = 250 <= words <= 900
    checks.append(
        Check(
            "length",
            "Length (about one page)",
            10 if good_len else 4,
            10,
            good_len,
            f"{words} words.",
            ""
            if good_len
            else (
                "Add detail to projects and experience."
                if words < 250
                else "Trim to the most relevant one to two pages."
            ),
        )
    )

    bullets = len(_BULLET.findall(text))
    checks.append(
        Check(
            "bullets",
            "Bullet points",
            min(bullets, 8) / 8 * 10,
            10,
            bullets >= 6,
            f"{bullets} bullet lines.",
            "" if bullets >= 6 else "Describe experience and projects as short bullet points.",
        )
    )

    metrics = len(_METRIC.findall(text))
    verbs = sum(1 for w in re.findall(r"[a-z]+", text.lower()) if w in _ACTION_VERBS)
    impact = min(metrics, 4) / 4 * 7.5 + min(verbs, 6) / 6 * 7.5
    checks.append(
        Check(
            "impact",
            "Quantified impact and action verbs",
            impact,
            15,
            metrics >= 3 and verbs >= 4,
            f"{metrics} measurable results, {verbs} action verbs.",
            ""
            if metrics >= 3 and verbs >= 4
            else "Start bullets with verbs (built, reduced…) and add numbers "
            "(latency −40%, 2k users).",
        )
    )

    if keyword_coverage is not None:
        checks.append(
            Check(
                "keywords",
                "Job-description keyword coverage",
                20 * keyword_coverage,
                20,
                keyword_coverage >= 0.6,
                f"{round(keyword_coverage * 100)}% of required skills mentioned.",
                ""
                if keyword_coverage >= 0.6
                else "Mention the required skills you genuinely have, "
                "using the job description's wording.",
            )
        )
    return checks


def ats_score(checks: list[Check]) -> tuple[float, list[dict[str, Any]]]:
    earned = sum(c.points for c in checks)
    total = sum(c.max_points for c in checks)
    score = round(100 * earned / total, 1) if total else 0.0
    return score, [asdict(c) | {"points": round(c.points, 1)} for c in checks]
