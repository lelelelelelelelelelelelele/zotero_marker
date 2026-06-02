"""User-controlled manual overrides (data/overrides.csv), keyed by arXiv id.

Escape hatch for the long tail the auto-resolver gets 'technically right but not what
you want' — e.g. a paper whose structured record points at a later journal
republication instead of the original conference. Always wins; clearly labelled
source='override' in the report.
"""
from __future__ import annotations

import csv
from functools import lru_cache

from . import config


@lru_cache(maxsize=1)
def _table() -> dict[str, dict]:
    path = config.DATA_DIR / "overrides.csv"
    out: dict[str, dict] = {}
    if not path.exists():
        return out
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            aid = (r.get("arxiv_id") or "").strip()
            if not aid:
                continue
            year = r.get("year", "")
            out[aid] = {
                "canonical": (r.get("canonical") or "").strip(),
                "year": int(year) if str(year).strip().isdigit() else None,
            }
    return out


def get(arxiv_id: str | None) -> dict | None:
    if not arxiv_id:
        return None
    return _table().get(arxiv_id.strip())
