"""Build the metadata write-back proposal so easyScholar / zotero-style / 小绿蛙 light up.

Those plugins read the VENUE FIELD (publicationTitle for journals; proceedingsTitle /
conferenceName for conferences) and match easyScholar by venue name (+ DOI), NOT tags.
A preprint has no venue field, so we must convert itemType too. We preserve the arXiv
id + citation count in Extra and never invent a publisher where the type has no such field.
"""
from __future__ import annotations

import re
from datetime import datetime

from . import rankings

# Lines THIS tool authored (rewritten each run for idempotency). Scoped to our own
# Semantic Scholar source + our stamp, so a user's citation line from another source
# (e.g. Citation Tally's default "Citations: N (Crossref)") is never stripped.
_TOOL_LINE = re.compile(
    r"^\s*(?:"
    r"\d+\s+citations\s*\(semantic\s*scholar\)"      # legacy: "N citations (Semantic Scholar)"
    r"|citations:\s*\d+\s*\(semanticscholar\)"        # current: "Citations: N (SemanticScholar)"
    r"|(?:zotero|arxiv)-marker:"                                 # our resolved stamp
    r")",
    re.I,
)

# Publisher is a completeness field (NOT needed for IF matching) and only exists on
# conferencePaper, not journalArticle. Best-effort by canonical venue; user-editable.
_PUBLISHER = {
    "CVPR": "IEEE", "ICCV": "IEEE", "WACV": "IEEE", "ICRA": "IEEE", "IROS": "IEEE",
    "ECCV": "Springer",
    "ICML": "PMLR", "AISTATS": "PMLR", "COLT": "PMLR", "UAI": "PMLR",
    "ACL": "ACL", "EMNLP": "ACL", "NAACL": "ACL",
    "KDD": "ACM", "WWW": "ACM", "SIGIR": "ACM", "SIGGRAPH": "ACM", "ACM MM": "ACM",
    "AAAI": "AAAI Press", "IJCAI": "IJCAI", "USENIX Security": "USENIX",
}


def is_arxiv_doi(doi: str | None) -> bool:
    return bool(doi) and "arxiv" in doi.lower()


_TITLE_STOPWORDS = {"a", "an", "the", "of", "for", "and", "in", "on", "to", "at", "via"}


def _smart_title(s: str) -> str:
    """Title-case a lowercased venue name WITHOUT upcasing interior stopwords, so the
    written string ('Advances in Neural Information Processing Systems') matches how the
    venue is actually written — `str.title()` would mangle it to 'Advances In ... Of The'."""
    words = s.split()
    return " ".join(
        w.lower() if (i and w.lower() in _TITLE_STOPWORDS) else w[:1].upper() + w[1:]
        for i, w in enumerate(words)
    )


def _full_name(canonical: str | None, raw: str | None) -> str:
    """Full venue name to write (easyScholar matches on the full venue string).

    Semantic Scholar's venue name and easyScholar's match value can differ — e.g. S2
    returns 'IEEE International Conference on Computer Vision', but easyScholar's ICCV
    (CCF A) entry has no 'IEEE' prefix, so writing S2's string leaves the CCF tag blank.
    `write_as` in venue_rankings.csv pins the exact easyScholar-matching string for such
    venues (decoupled from the lookup aliases). Otherwise S2's multi-word raw is already
    the full name; single-token raws fall back to the longest table alias.
    """
    row = rankings.lookup(canonical or raw or "")
    if row and row.get("write_as"):
        return row["write_as"]                 # S2 name != easyScholar match value
    if raw and len(raw.split()) >= 2:          # S2 'venue_raw' is already the full name
        return raw
    if row:
        longest = max([row["canonical"], *row["aliases"]], key=len)
        if len(longest.split()) >= 2:
            return _smart_title(longest)
    return raw or canonical or ""


def build(res, s2_hit, arxiv_id: str | None, data: dict) -> tuple[str | None, dict]:
    """Return (target_itemType, field_changes). Empty when nothing should be written."""
    if res.acceptance != "accepted" or not res.canonical:
        return None, {}

    name = _full_name(res.canonical, res.venue_raw)
    doi = None
    issn = None
    abbrev = res.canonical
    if s2_hit:
        if s2_hit.external_doi and not is_arxiv_doi(s2_hit.external_doi):
            doi = s2_hit.external_doi
        issn = s2_hit.issn
        abbrev = s2_hit.abbrev or res.canonical

    fields: dict[str, str] = {}
    if (res.kind or "conference") == "journal":
        itype = "journalArticle"
        fields["publicationTitle"] = name
        if abbrev:
            fields["journalAbbreviation"] = abbrev
        if issn:
            fields["ISSN"] = issn
    else:
        itype = "conferencePaper"
        fields["proceedingsTitle"] = name
        fields["conferenceName"] = name
        pub = _PUBLISHER.get(res.canonical)
        if pub:
            fields["publisher"] = pub

    if doi:
        fields["DOI"] = doi

    # Preserve arXiv provenance + citation count + a dated tool stamp in Extra
    # (preprint-only fields are dropped on type change, so the arXiv id must survive
    # here). Tool-managed lines are rewritten idempotently so re-runs never duplicate.
    today = datetime.now().strftime("%Y-%m-%d")
    kept = [ln for ln in (data.get("extra") or "").splitlines() if not _TOOL_LINE.match(ln)]
    if arxiv_id and not any("arxiv" in ln.lower() for ln in kept):
        kept.append(f"arXiv:{arxiv_id}")
    if res.citation_count is not None:
        # Exact format read by the Citation Tally column plugin (daeh/zotero-citation-tally).
        # Its column regex is /^Citations: *(\d+) *\(<source>\)( \[date\])?/i where <source>
        # is the plugin's *localized* DB name. For Semantic Scholar that is the ONE-WORD
        # "SemanticScholar" (verified in addon/locale/{en-US,zh-CN}/addon.ftl:
        # `database-semanticscholar = SemanticScholar`) — a space would NOT match, showing "-".
        # NOTE: the user must add Semantic Scholar to Citation Tally's database order, else
        # its column only scans for "(Crossref)" (the default) and won't find this line.
        kept.append(f"Citations: {res.citation_count} (SemanticScholar) [{today}]")
    kept.append(f"arxiv-marker: resolved {today}")
    fields["extra"] = "\n".join(kept).strip()

    # Idempotency: if the item is ALREADY the target type with its venue field already
    # written, there's no STRUCTURAL change left to propose — return empty so the review
    # UI shows "no change" instead of perpetually re-listing a resolved item (and
    # auto-selecting it for a redundant re-write). Compare the venue field only, NOT
    # extra: the citation line + dated stamp legitimately change every run, and we won't
    # re-list an already-converted item just to refresh those.
    venue_field = "publicationTitle" if itype == "journalArticle" else "proceedingsTitle"
    if data.get("itemType") == itype and (data.get(venue_field) or "") == fields.get(venue_field, ""):
        return None, {}

    return itype, fields
