import io
import zipfile
from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from app.ml.resume.analyzer import analyze
from app.ml.resume.parsing import ParseError, detect_sections, extract_text
from app.ml.resume.skills import extract_skills
from app.seed import SAMPLE_JDS
from tests.conftest import Headers
from tests.fixtures import GAP_CASES, STRONG_RESUME, WEAK_RESUME


def _docx(text: str) -> bytes:
    ns = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    paras = "".join(f"<w:p><w:r><w:t>{line}</w:t></w:r></w:p>" for line in text.splitlines())
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(
            "word/document.xml", f'<w:document xmlns:w="{ns}"><w:body>{paras}</w:body></w:document>'
        )
    return buf.getvalue()


def test_docx_and_txt_extraction() -> None:
    assert "Asha Rao" in extract_text(".docx", _docx(STRONG_RESUME))
    assert "Asha Rao" in extract_text(".txt", STRONG_RESUME.encode())


def test_rejects_mismatched_magic_bytes() -> None:
    with pytest.raises(ParseError):
        extract_text(".pdf", b"not a pdf at all")
    with pytest.raises(ParseError):
        extract_text(".exe", b"MZ")


def test_section_detection() -> None:
    sections = detect_sections(STRONG_RESUME)
    assert {"education", "experience", "projects", "skills", "certifications"} <= set(sections)


def test_skill_extraction_exact_and_fuzzy() -> None:
    found = extract_skills("Built APIs in python with reactjs", "Skills\nPostgress, Kubernetis")
    assert found["python"] == "exact"
    assert found["react"] == "exact"  # alias
    assert found["sql"].startswith("fuzzy")
    assert found["kubernetes"].startswith("fuzzy")


def test_ats_strong_beats_weak_and_explains() -> None:
    strong, weak = analyze(STRONG_RESUME), analyze(WEAK_RESUME)
    assert strong["ats_score"] > weak["ats_score"] + 20
    assert weak["fixes"], "weak resume must get fix-it suggestions"
    assert all({"label", "points", "max_points", "detail"} <= set(c) for c in weak["ats_checks"])


@pytest.mark.parametrize(("resume", "jd_idx", "expected"), GAP_CASES)
def test_skill_gaps_on_constructed_fixtures(resume: str, jd_idx: int, expected: set[str]) -> None:
    report = analyze(resume, SAMPLE_JDS[jd_idx])
    gaps = {g["skill"] for g in report["skill_gaps"]}
    assert gaps == expected
    importances = [g["importance"] for g in report["skill_gaps"]]
    assert importances == sorted(importances, reverse=True)


def test_report_is_deterministic() -> None:
    assert analyze(STRONG_RESUME, SAMPLE_JDS[0]) == analyze(STRONG_RESUME, SAMPLE_JDS[0])


def test_upload_and_report_via_api(
    client: TestClient, make_student: Callable[..., Headers]
) -> None:
    h = make_student()
    jobs = client.get("/api/v1/jobs", headers=h).json()
    jd_id = next(j["id"] for j in jobs if j["type"] == "service")
    r = client.post(
        "/api/v1/resumes",
        headers=h,
        data={"jd_id": str(jd_id)},
        files={"file": ("cv.docx", _docx(STRONG_RESUME), "application/octet-stream")},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["jd_id"] == jd_id
    assert "aptitude" in {g["skill"] for g in body["skill_gaps"]}
    assert body["match_scores"]["overall"] > 0

    bad = client.post(
        "/api/v1/resumes",
        headers=h,
        files={"file": ("cv.exe", b"MZ....", "application/octet-stream")},
    )
    assert bad.status_code == 415
