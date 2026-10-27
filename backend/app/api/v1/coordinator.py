"""Coordinator views. Cohort aggregates by default; individual rows only for students who
granted `coordinator_visibility`. Groups smaller than MIN_GROUP are suppressed to limit
re-identification."""

import csv
import io
from collections import Counter, defaultdict
from statistics import mean
from typing import Any

from fastapi import APIRouter, Response
from pydantic import BaseModel
from sqlalchemy import select

from app.db.models import Announcement, ReadinessScore, ResumeAnalysis, StudentProfile, User
from app.deps import DB, CurrentUser, Staff
from app.schemas.common import ORM
from app.services.governance import audit, current_consents

router = APIRouter(tags=["coordinator"])
MIN_GROUP = 3
AT_RISK_BELOW = 50.0


def _latest_scores(db: DB) -> dict[int, ReadinessScore]:
    latest: dict[int, ReadinessScore] = {}
    for row in db.scalars(select(ReadinessScore).order_by(ReadinessScore.id)):
        latest[row.user_id] = row
    return latest


def _profiles(db: DB) -> dict[int, StudentProfile]:
    return {p.user_id: p for p in db.scalars(select(StudentProfile))}


@router.get("/coordinator/cohort")
def cohort(_: Staff, db: DB, company_type: str | None = None) -> dict[str, Any]:
    scores = _latest_scores(db)
    profiles = _profiles(db)
    students = [
        uid for uid in profiles if company_type in (None, profiles[uid].target_company_type)
    ]
    scored = [scores[u] for u in students if u in scores]

    buckets = Counter(min(int(s.score // 10) * 10, 90) for s in scored)
    distribution = [
        {"range": f"{b}-{b + 9}", "count": buckets.get(b, 0)} for b in range(0, 100, 10)
    ]

    by_dept: dict[str, list[ReadinessScore]] = defaultdict(list)
    for s in scored:
        by_dept[profiles[s.user_id].department or "Unspecified"].append(s)
    components = ["predictor", "resume", "mastery", "interview", "consistency"]
    heatmap = []
    for dept, rows in sorted(by_dept.items()):
        if len(rows) < MIN_GROUP:
            heatmap.append({"department": dept, "n": len(rows), "suppressed": True})
            continue
        cell: dict[str, Any] = {
            "department": dept,
            "n": len(rows),
            "suppressed": False,
            "score": round(mean(r.score for r in rows), 1),
        }
        for c in components:
            vals = [r.components["values"].get(c) for r in rows]
            vals = [v for v in vals if v is not None]
            cell[c] = round(mean(vals), 1) if len(vals) >= MIN_GROUP else None
        heatmap.append(cell)

    gaps: Counter[str] = Counter()
    seen: set[int] = set()
    for a in db.scalars(select(ResumeAnalysis).order_by(ResumeAnalysis.id.desc())):
        if a.user_id in seen or a.user_id not in students:
            continue
        seen.add(a.user_id)
        gaps.update(g["skill"] for g in a.skill_gaps)

    return {
        "students": len(students),
        "scored": len(scored),
        "mean_score": round(mean(s.score for s in scored), 1) if scored else None,
        "at_risk_count": sum(1 for s in scored if s.score < AT_RISK_BELOW),
        "distribution": distribution,
        "departments": heatmap,
        "top_skill_gaps": [
            {"skill": k, "students": v} for k, v in gaps.most_common(10) if v >= MIN_GROUP
        ],
        "min_group_size": MIN_GROUP,
    }


def _visible_rows(db: DB, actor: User) -> list[dict[str, Any]]:
    scores = _latest_scores(db)
    rows = []
    for uid, profile in _profiles(db).items():
        if not current_consents(db, uid).get("coordinator_visibility"):
            continue
        user = db.get(User, uid)
        s = scores.get(uid)
        rows.append(
            {
                "user_id": uid,
                "name": user.full_name if user else "",
                "email": user.email if user else "",
                "department": profile.department,
                "target": profile.target_company_type,
                "score": s.score if s else None,
                "missing": s.components.get("missing", []) if s else [],
            }
        )
    audit(db, actor.id, "coordinator_viewed_individuals", "cohort", count=len(rows))
    db.commit()
    return rows


@router.get("/coordinator/students")
def consented_students(actor: Staff, db: DB, at_risk: bool = False) -> list[dict[str, Any]]:
    rows = _visible_rows(db, actor)
    if at_risk:
        rows = [r for r in rows if r["score"] is not None and r["score"] < AT_RISK_BELOW]
    return sorted(rows, key=lambda r: (r["score"] is None, r["score"] or 0))


@router.get("/coordinator/students.csv")
def export_csv(actor: Staff, db: DB) -> Response:
    rows = _visible_rows(db, actor)
    buf = io.StringIO()
    writer = csv.DictWriter(
        buf, fieldnames=["name", "email", "department", "target", "score"], extrasaction="ignore"
    )
    writer.writeheader()
    writer.writerows(rows)
    audit(db, actor.id, "coordinator_exported_csv", "cohort", count=len(rows))
    db.commit()
    return Response(
        buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=consented-students.csv"},
    )


class AnnouncementIn(BaseModel):
    title: str
    body: str


class AnnouncementOut(AnnouncementIn, ORM):
    id: int
    created_at: Any


@router.get("/announcements", response_model=list[AnnouncementOut])
def list_announcements(_: CurrentUser, db: DB) -> list[Announcement]:
    return list(db.scalars(select(Announcement).order_by(Announcement.id.desc()).limit(20)))


@router.post("/announcements", response_model=AnnouncementOut, status_code=201)
def create_announcement(body: AnnouncementIn, actor: Staff, db: DB) -> Announcement:
    a = Announcement(author_id=actor.id, **body.model_dump())
    db.add(a)
    db.commit()
    return a
