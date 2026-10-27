"""ORM models. PII (email, name) lives only on `users`; everything used for modelling hangs off
`user_id` and is exported/trained under `student_profiles.pseudonym_id`."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, JSONType, TimestampMixin, utcnow

USER_FK = "users.id"


def _uid() -> str:
    return uuid.uuid4().hex


class User(TimestampMixin, Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(200), default="")
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="student")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class StudentProfile(TimestampMixin, Base):
    __tablename__ = "student_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey(USER_FK, ondelete="CASCADE"), unique=True)
    pseudonym_id: Mapped[str] = mapped_column(String(32), default=_uid, unique=True)
    department: Mapped[str] = mapped_column(String(100), default="")
    graduation_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(30), nullable=True)
    target_company_type: Mapped[str] = mapped_column(String(20), default="product")
    target_role: Mapped[str] = mapped_column(String(100), default="Software Engineer")
    cgpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    backlogs: Mapped[int] = mapped_column(Integer, default=0)
    tenth_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    twelfth_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    internships: Mapped[int] = mapped_column(Integer, default=0)


class Consent(TimestampMixin, Base):
    """Append-only: the latest row per (user, scope) is the current state."""

    __tablename__ = "consents"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey(USER_FK, ondelete="CASCADE"), index=True)
    scope: Mapped[str] = mapped_column(String(40))
    granted: Mapped[bool] = mapped_column(Boolean)
    version: Mapped[str] = mapped_column(String(20))


class AcademicRecord(TimestampMixin, Base):
    __tablename__ = "academic_records"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey(USER_FK, ondelete="CASCADE"), index=True)
    term: Mapped[str] = mapped_column(String(40))
    gpa: Mapped[float] = mapped_column(Float)
    backlogs: Mapped[int] = mapped_column(Integer, default=0)


class CodingActivity(TimestampMixin, Base):
    __tablename__ = "coding_activities"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey(USER_FK, ondelete="CASCADE"), index=True)
    platform: Mapped[str] = mapped_column(String(60))
    problems_solved: Mapped[int] = mapped_column(Integer, default=0)
    contest_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Project(TimestampMixin, Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey(USER_FK, ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    tech: Mapped[list[str]] = mapped_column(JSONType, default=list)
    complexity: Mapped[int] = mapped_column(Integer, default=1)


class Certification(TimestampMixin, Base):
    __tablename__ = "certifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey(USER_FK, ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    issuer: Mapped[str] = mapped_column(String(200), default="")
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Resume(TimestampMixin, Base):
    __tablename__ = "resumes"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey(USER_FK, ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    storage_path: Mapped[str] = mapped_column(String(500))
    parsed_text: Mapped[str] = mapped_column(Text, default="")
    sections: Mapped[dict[str, str]] = mapped_column(JSONType, default=dict)
    version: Mapped[int] = mapped_column(Integer, default=1)


class Company(TimestampMixin, Base):
    __tablename__ = "companies"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    type: Mapped[str] = mapped_column(String(20), default="product")


class JobDescription(TimestampMixin, Base):
    __tablename__ = "job_descriptions"
    id: Mapped[int] = mapped_column(primary_key=True)
    company: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(200))
    type: Mapped[str] = mapped_column(String(20), default="product")
    text: Mapped[str] = mapped_column(Text)
    # [{"skill": "python", "weight": 1.0}, ...]
    required_skills: Mapped[list[dict[str, Any]]] = mapped_column(JSONType, default=list)


class ResumeAnalysis(TimestampMixin, Base):
    __tablename__ = "resume_analyses"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey(USER_FK, ondelete="CASCADE"), index=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"))
    jd_id: Mapped[int | None] = mapped_column(
        ForeignKey("job_descriptions.id", ondelete="SET NULL"), nullable=True
    )
    ats_score: Mapped[float] = mapped_column(Float)
    ats_report: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    match_scores: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    skill_gaps: Mapped[list[dict[str, Any]]] = mapped_column(JSONType, default=list)
    skills_found: Mapped[list[str]] = mapped_column(JSONType, default=list)


class Skill(Base):
    __tablename__ = "skills"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    category: Mapped[str] = mapped_column(String(60), default="general")
    aliases: Mapped[list[str]] = mapped_column(JSONType, default=list)
    prerequisites: Mapped[list[str]] = mapped_column(JSONType, default=list)


class SkillMastery(Base):
    __tablename__ = "skill_mastery"
    __table_args__ = (UniqueConstraint("user_id", "skill"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey(USER_FK, ondelete="CASCADE"), index=True)
    skill: Mapped[str] = mapped_column(String(100))
    p_known: Mapped[float] = mapped_column(Float)
    n_obs: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class QuestionBank(TimestampMixin, Base):
    __tablename__ = "question_bank"
    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(20))  # quiz | interview
    skill: Mapped[str] = mapped_column(String(100), default="")
    category: Mapped[str] = mapped_column(String(40), default="technical")
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    role: Mapped[str] = mapped_column(String(100), default="Software Engineer")
    company_type: Mapped[str] = mapped_column(String(20), default="any")
    prompt: Mapped[str] = mapped_column(Text)
    options: Mapped[list[str]] = mapped_column(JSONType, default=list)
    answer_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    key_points: Mapped[list[str]] = mapped_column(JSONType, default=list)
    reference_answer: Mapped[str] = mapped_column(Text, default="")


class Assessment(TimestampMixin, Base):
    __tablename__ = "assessments"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    skill: Mapped[str] = mapped_column(String(100))
    question_ids: Mapped[list[int]] = mapped_column(JSONType, default=list)


class AssessmentAttempt(TimestampMixin, Base):
    __tablename__ = "assessment_attempts"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey(USER_FK, ondelete="CASCADE"), index=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessments.id", ondelete="CASCADE"))
    answers: Mapped[dict[str, int]] = mapped_column(JSONType, default=dict)
    correct: Mapped[dict[str, bool]] = mapped_column(JSONType, default=dict)
    score: Mapped[float] = mapped_column(Float)


class InterviewSession(TimestampMixin, Base):
    __tablename__ = "interview_sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey(USER_FK, ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(100))
    company_type: Mapped[str] = mapped_column(String(20))
    question_ids: Mapped[list[int]] = mapped_column(JSONType, default=list)
    status: Mapped[str] = mapped_column(String(20), default="active")


class InterviewAnswer(TimestampMixin, Base):
    __tablename__ = "interview_answers"
    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("interview_sessions.id", ondelete="CASCADE"), index=True
    )
    question_id: Mapped[int] = mapped_column(ForeignKey("question_bank.id", ondelete="CASCADE"))
    transcript: Mapped[str] = mapped_column(Text, default="")
    audio_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    duration_s: Mapped[float | None] = mapped_column(Float, nullable=True)
    scores: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    feedback: Mapped[list[str]] = mapped_column(JSONType, default=list)


class ReadinessScore(TimestampMixin, Base):
    __tablename__ = "readiness_scores"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey(USER_FK, ondelete="CASCADE"), index=True)
    score: Mapped[float] = mapped_column(Float)
    probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    components: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    weights: Mapped[dict[str, float]] = mapped_column(JSONType, default=dict)
    model_version: Mapped[str] = mapped_column(String(60), default="")
    attributions: Mapped[list[dict[str, Any]]] = mapped_column(JSONType, default=list)


class LearningResource(TimestampMixin, Base):
    __tablename__ = "learning_resources"
    id: Mapped[int] = mapped_column(primary_key=True)
    skill: Mapped[str] = mapped_column(String(100), index=True)
    title: Mapped[str] = mapped_column(String(300))
    url: Mapped[str] = mapped_column(String(500))
    kind: Mapped[str] = mapped_column(String(30), default="article")
    minutes: Mapped[int] = mapped_column(Integer, default=30)


class Recommendation(TimestampMixin, Base):
    __tablename__ = "recommendations"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey(USER_FK, ondelete="CASCADE"), index=True)
    skill: Mapped[str] = mapped_column(String(100))
    resource_id: Mapped[int | None] = mapped_column(
        ForeignKey("learning_resources.id", ondelete="SET NULL"), nullable=True
    )
    reason: Mapped[str] = mapped_column(Text)
    priority: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), default="open")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Event(TimestampMixin, Base):
    """Append-only interaction log."""

    __tablename__ = "events"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey(USER_FK, ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(60), index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)


class AuditLog(TimestampMixin, Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    # No FK: audit rows must survive the deletion of the actor.
    actor_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    action: Mapped[str] = mapped_column(String(80))
    target: Mapped[str] = mapped_column(String(200), default="")
    meta: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)


class ModelVersion(TimestampMixin, Base):
    __tablename__ = "model_versions"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60))
    version: Mapped[str] = mapped_column(String(60), unique=True)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    data_hash: Mapped[str] = mapped_column(String(64), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)


class Announcement(TimestampMixin, Base):
    __tablename__ = "announcements"
    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)


# Tables keyed by user_id, in delete order (children first). Used by "delete all my data".
USER_OWNED = [
    ReadinessScore,
    Recommendation,
    Event,
    SkillMastery,
    AssessmentAttempt,
    ResumeAnalysis,
    Resume,
    InterviewSession,
    Certification,
    Project,
    CodingActivity,
    AcademicRecord,
    Consent,
    StudentProfile,
]
