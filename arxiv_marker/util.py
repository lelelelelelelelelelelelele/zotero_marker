"""Small shared helpers: arXiv-ID extraction and title matching."""
from __future__ import annotations

import re

# Modern arXiv id, e.g. 2106.09685 or 2106.09685v3
_ARXIV_NEW = re.compile(r"(\d{4}\.\d{4,5})(v\d+)?", re.I)
# arXiv embedded in a DOI / text, e.g. 10.48550/arXiv.2106.09685 or "arXiv:2106.09685"
_ARXIV_TAGGED = re.compile(r"arxiv[:.\s/]*?(\d{4}\.\d{4,5})", re.I)


def extract_arxiv_id(data: dict) -> str | None:
    """Best-effort arXiv id from a Zotero item's data fields."""
    # 1) explicit, trustworthy fields
    archive_id = (data.get("archiveID") or "")
    m = _ARXIV_TAGGED.search(archive_id) or _ARXIV_NEW.search(archive_id)
    if m and ("arxiv" in archive_id.lower() or _ARXIV_NEW.fullmatch(archive_id.strip() or "x")):
        return m.group(1)

    doi = (data.get("DOI") or "")
    m = _ARXIV_TAGGED.search(doi)
    if m:
        return m.group(1)

    # 2) url / extra / repository hints
    for field in ("url", "extra"):
        val = data.get(field) or ""
        if "arxiv" in val.lower():
            m = _ARXIV_TAGGED.search(val) or _ARXIV_NEW.search(val)
            if m:
                return m.group(1)
    return None


def norm_title(s: str | None) -> str:
    if not s:
        return ""
    s = re.sub(r"[^a-z0-9 ]+", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def title_jaccard(a: str | None, b: str | None) -> float:
    """Token Jaccard of two normalized titles (1.0 == identical)."""
    na, nb = norm_title(a), norm_title(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    ta, tb = set(na.split()), set(nb.split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def title_match(a: str | None, b: str | None, threshold: float = 0.85) -> bool:
    """True if two titles are the same paper (exact-normalized or high token Jaccard)."""
    return title_jaccard(a, b) >= threshold


def first_author_lastname(data: dict) -> str:
    for c in data.get("creators", []) or []:
        if c.get("creatorType") == "author" and c.get("lastName"):
            return c["lastName"]
    return ""
