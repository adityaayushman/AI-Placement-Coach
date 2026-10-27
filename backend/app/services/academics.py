"""Academic record import: a student's own CSV, or an institutional export uploaded by staff.

The staff path stands in for the ERP/LMS sync in the methodology: institutions export a CSV and a
coordinator uploads it, so no live connection to institutional systems is needed."""

import csv
import io
from collections import defaultdict

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AcademicRecord, StudentProfile, User
from app.schemas.common import AcademicIn

MAX_BYTES = 1024 * 1024


async def read_csv(file: UploadFile) -> list[dict[str, str]]:
    raw = await file.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "CSV larger than 1 MB")
    try:
        return list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    except (UnicodeDecodeError, csv.Error) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Bad CSV: {exc}") from None


def parse_row(row: dict[str, str], line: int) -> AcademicIn:
    try:
        return AcademicIn(
            term=row["term"], gpa=float(row["gpa"]), backlogs=int(row.get("backlogs") or 0)
        )
    except (KeyError, ValueError) as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, f"Bad CSV row {line}: {exc}"
        ) from None


def apply(db: Session, user_id: int, items: list[AcademicIn]) -> list[AcademicRecord]:
    """Replace terms present in the import, then derive CGPA (mean term GPA) and current
    backlogs (latest term in file order) onto the profile used by the predictor."""
    terms = {i.term for i in items}
    for old in db.scalars(
        select(AcademicRecord).where(
            AcademicRecord.user_id == user_id, AcademicRecord.term.in_(terms)
        )
    ):
        db.delete(old)
    rows = [AcademicRecord(user_id=user_id, **i.model_dump()) for i in items]
    db.add_all(rows)
    db.flush()
    all_rows = list(
        db.scalars(
            select(AcademicRecord)
            .where(AcademicRecord.user_id == user_id)
            .order_by(AcademicRecord.id)
        )
    )
    profile = db.scalar(select(StudentProfile).where(StudentProfile.user_id == user_id))
    if profile is None:
        profile = StudentProfile(user_id=user_id)
        db.add(profile)
    profile.cgpa = round(sum(r.gpa for r in all_rows) / len(all_rows), 2)
    profile.backlogs = all_rows[-1].backlogs
    return rows


def import_institutional(db: Session, rows: list[dict[str, str]]) -> tuple[list[int], list[str]]:
    """CSV columns: email,term,gpa[,backlogs]. Returns (updated user ids, unknown emails);
    unknown emails are reported, never created."""
    by_email: dict[str, list[AcademicIn]] = defaultdict(list)
    for line, row in enumerate(rows, start=2):
        email = (row.get("email") or "").strip().lower()
        if not email:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Row {line}: no email")
        by_email[email].append(parse_row(row, line))
    users = {
        u.email: u
        for u in db.scalars(
            select(User).where(User.email.in_(list(by_email)), User.role == "student")
        )
    }
    updated: list[int] = []
    for email, items in by_email.items():
        if email in users:
            apply(db, users[email].id, items)
            updated.append(users[email].id)
    return updated, sorted(set(by_email) - set(users))
