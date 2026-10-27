"""Text extraction and section detection for PDF / DOCX / TXT resumes."""

import io
import re
import zipfile
from xml.etree import ElementTree

ALLOWED = {".pdf", ".docx", ".txt"}
_MAGIC = {".pdf": b"%PDF-", ".docx": b"PK\x03\x04"}
_MAX_DOCX_UNCOMPRESSED = 20 * 1024 * 1024  # zip-bomb guard
_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


class ParseError(ValueError):
    pass


def check_magic(suffix: str, data: bytes) -> None:
    """Reject files whose content does not match their extension."""
    if suffix not in ALLOWED:
        raise ParseError(f"Unsupported file type {suffix}; use PDF, DOCX or TXT")
    magic = _MAGIC.get(suffix)
    if magic and not data.startswith(magic):
        raise ParseError("File content does not match its extension")


def _docx_text(data: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        info = zf.getinfo("word/document.xml")
        if info.file_size > _MAX_DOCX_UNCOMPRESSED:
            raise ParseError("DOCX too large when uncompressed")
        root = ElementTree.fromstring(zf.read(info))
    lines = []
    for para in root.iter(f"{_W}p"):
        lines.append("".join(t.text or "" for t in para.iter(f"{_W}t")))
    return "\n".join(lines)


def _pdf_text(data: bytes) -> str:
    try:
        import pdfplumber

        with pdfplumber.open(io.BytesIO(data)) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages[:10])
    except ImportError:
        pass
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ParseError("PDF support is not installed on this server; upload DOCX") from exc
    reader = PdfReader(io.BytesIO(data))
    return "\n".join(page.extract_text() or "" for page in reader.pages[:10])


def extract_text(suffix: str, data: bytes) -> str:
    check_magic(suffix, data)
    try:
        if suffix == ".docx":
            text = _docx_text(data)
        elif suffix == ".pdf":
            text = _pdf_text(data)
        else:
            text = data.decode("utf-8", errors="replace")
    except (zipfile.BadZipFile, KeyError, ElementTree.ParseError) as exc:
        raise ParseError("Could not read the document") from exc
    return clean(text)


def clean(text: str) -> str:
    text = text.replace("\r", "\n").replace("•", "\n• ").replace("\t", " ")
    text = re.sub(r"[  ]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


SECTION_HEADINGS: dict[str, list[str]] = {
    "summary": ["summary", "profile", "objective", "about me", "career objective"],
    "education": ["education", "academics", "academic background", "qualifications"],
    "experience": [
        "experience",
        "work experience",
        "internships",
        "internship",
        "employment",
        "professional experience",
    ],
    "projects": ["projects", "academic projects", "personal projects", "key projects"],
    "skills": ["skills", "technical skills", "core competencies", "technologies", "tech stack"],
    "certifications": ["certifications", "certificates", "courses", "licenses"],
    "achievements": ["achievements", "awards", "accomplishments", "honors"],
}
_HEADING_LOOKUP = {h: sec for sec, hs in SECTION_HEADINGS.items() for h in hs}


def detect_sections(text: str) -> dict[str, str]:
    """Split on lines that are just a known heading (optionally followed by ':')."""
    sections: dict[str, list[str]] = {"header": []}
    current = "header"
    for line in text.splitlines():
        key = re.sub(r"[^a-z ]", "", line.lower()).strip()
        if len(key) <= 40 and key in _HEADING_LOOKUP:
            current = _HEADING_LOOKUP[key]
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return {k: "\n".join(v).strip() for k, v in sections.items() if "\n".join(v).strip()}
