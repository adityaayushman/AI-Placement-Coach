"""Skill extraction: exact alias matching over the taxonomy, plus a fuzzy fallback for
near-miss spellings ("reactjs", "postgress") inside the skills section."""

import difflib
import re
from functools import lru_cache

from app.ml.resume.taxonomy import TAXONOMY


@lru_cache
def _patterns() -> list[tuple[str, re.Pattern[str]]]:
    out = []
    for name, (_, aliases, _) in TAXONOMY.items():
        for term in sorted({name, *aliases}, key=len, reverse=True):
            # Word boundaries that also work for terms like "c++", "ci/cd", "node.js".
            pat = re.compile(r"(?<![a-z0-9+#])" + re.escape(term) + r"(?![a-z0-9+#])")
            out.append((name, pat))
    return out


@lru_cache
def _vocab() -> dict[str, str]:
    return {t: n for n, (_, aliases, _) in TAXONOMY.items() for t in (n, *aliases) if len(t) > 3}


def extract_skills(text: str, skills_section: str = "") -> dict[str, str]:
    """Return {canonical_skill: how_it_matched} where how is 'exact' or 'fuzzy:<token>'."""
    lowered = text.lower()
    found: dict[str, str] = {}
    for name, pat in _patterns():
        # A bare "c" or "go" is too ambiguous outside the skills section.
        haystack = skills_section.lower() if name in {"c", "go"} else lowered
        if name not in found and pat.search(haystack):
            found[name] = "exact"
    vocab = _vocab()
    for token in re.split(r"[,;|/\n•·]+", skills_section.lower()):
        token = token.strip(" .-:")
        if len(token) < 4 or token in vocab:
            continue
        match = difflib.get_close_matches(token, vocab.keys(), n=1, cutoff=0.86)
        if match and vocab[match[0]] not in found:
            found[vocab[match[0]]] = f"fuzzy:{token}"
    return found
