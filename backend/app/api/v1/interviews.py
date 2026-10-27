import json
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select

from app.db.models import InterviewAnswer, InterviewSession, QuestionBank
from app.deps import DB, Student
from app.ml.interview import stt
from app.ml.interview.audio import prosody
from app.ml.interview.scoring import FaceSignals, score_answer
from app.schemas.common import ORM, CompanyType
from app.services.governance import log_event, require_consent
from app.services.knowledge import observe
from app.services.rescoring import request_rescore
from app.services.storage import get_storage

router = APIRouter(prefix="/interviews", tags=["interviews"])
QUESTIONS_PER_SESSION = 4


class SessionIn(BaseModel):
    role: str = "Software Engineer"
    company_type: CompanyType = "product"


class InterviewQuestion(ORM):
    id: int
    category: str
    difficulty: int
    prompt: str


class SessionOut(ORM):
    id: int
    role: str
    company_type: str
    status: str
    questions: list[InterviewQuestion]


class AnswerOut(ORM):
    id: int
    question_id: int
    transcript: str
    scores: dict[str, Any]
    feedback: list[str]


@router.get("/stt")
def stt_status() -> dict[str, bool]:
    return {"server_stt": stt.available()}


@router.post("/sessions", response_model=SessionOut, status_code=201)
def start_session(body: SessionIn, user: Student, db: DB) -> SessionOut:
    qs = list(
        db.scalars(
            select(QuestionBank)
            .where(
                QuestionBank.kind == "interview",
                QuestionBank.company_type.in_([body.company_type, "any"]),
            )
            .order_by(QuestionBank.difficulty, QuestionBank.id)
        )
    )
    # One per category first (HR, behavioural, technical, DSA), then fill.
    picked: list[QuestionBank] = []
    for cat in ("hr", "behavioral", "technical", "dsa"):
        picked += [q for q in qs if q.category == cat][:1]
    picked += [q for q in qs if q not in picked]
    picked = picked[:QUESTIONS_PER_SESSION]
    if not picked:
        raise HTTPException(status.HTTP_409_CONFLICT, "Question bank is empty")
    session = InterviewSession(
        user_id=user.id,
        role=body.role,
        company_type=body.company_type,
        question_ids=[q.id for q in picked],
    )
    db.add(session)
    db.commit()
    return SessionOut(
        id=session.id,
        role=session.role,
        company_type=session.company_type,
        status=session.status,
        questions=[InterviewQuestion.model_validate(q) for q in picked],
    )


@router.post("/sessions/{sid}/answers", response_model=AnswerOut, status_code=201)
async def submit_answer(
    sid: int,
    user: Student,
    db: DB,
    question_id: int = Form(),
    transcript: str = Form(default="", max_length=10000),
    audio: UploadFile | None = File(default=None),
    face_metrics: str = Form(default="", max_length=2000),
) -> InterviewAnswer:
    session = db.get(InterviewSession, sid)
    if session is None or session.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    if question_id not in session.question_ids:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Question not in session")
    question = db.get(QuestionBank, question_id)
    assert question is not None

    pros, audio_path = None, None
    if audio is not None:
        require_consent(db, user.id, "interview_recording")
        data = await audio.read(15 * 1024 * 1024 + 1)
        if len(data) > 15 * 1024 * 1024 or not data.startswith(b"RIFF"):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Send WAV audio up to 15 MB")
        try:
            pros = prosody(data)
        except (ValueError, EOFError) as exc:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from None
        audio_path = get_storage().save(data, ".wav")
        if not transcript.strip():
            transcript = stt.transcribe(data) or ""
    if not transcript.strip():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "No transcript available")

    face = None
    if face_metrics.strip():
        require_consent(db, user.id, "face_analysis")
        try:
            face = FaceSignals.parse(json.loads(face_metrics))
        except (ValueError, KeyError, TypeError):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Bad face_metrics") from None

    scores, feedback = score_answer(
        transcript, question.reference_answer, question.key_points, pros, face
    )
    answer = InterviewAnswer(
        session_id=sid,
        question_id=question_id,
        transcript=transcript,
        audio_path=audio_path,
        duration_s=pros.duration_s if pros else None,
        scores=scores,
        feedback=feedback,
    )
    db.add(answer)
    if question.skill:
        observe(db, user.id, question.skill, scores["content"] >= 60)
    observe(db, user.id, "communication", scores["communication"] >= 60)
    answered = {
        a.question_id
        for a in db.scalars(select(InterviewAnswer).where(InterviewAnswer.session_id == sid))
    } | {question_id}
    if answered >= set(session.question_ids):
        session.status = "completed"
    log_event(db, user.id, "interview_answered", session_id=sid, overall=scores["overall"])
    db.commit()
    request_rescore(user.id)
    return answer


@router.get("/sessions/{sid}/answers", response_model=list[AnswerOut])
def list_answers(sid: int, user: Student, db: DB) -> list[InterviewAnswer]:
    session = db.get(InterviewSession, sid)
    if session is None or session.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    return list(db.scalars(select(InterviewAnswer).where(InterviewAnswer.session_id == sid)))
