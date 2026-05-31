"""Shared pytest fixtures: factory builders for Zotero items, Resolutions, VenueHits."""
from __future__ import annotations

import pytest

from zotero_marker.pipeline import Resolution
from zotero_marker.resolvers import VenueHit


@pytest.fixture(autouse=True)
def _isolate_overrides(monkeypatch):
    """Don't let the real data/overrides.csv influence tests; a test can set its own."""
    monkeypatch.setattr("zotero_marker.pipeline.overrides.get", lambda aid: None)


@pytest.fixture
def make_item():
    """Build a raw Zotero item dict ({"key","version","data":{...}})."""
    def _make(key="ABC123", version=100, **data):
        d = {
            "key": key, "version": version, "itemType": "preprint",
            "title": "A Great Paper",
            "creators": [{"creatorType": "author", "firstName": "Ada", "lastName": "Smith"}],
            "date": "2021", "DOI": "", "url": "", "extra": "", "archiveID": "", "tags": [],
        }
        d.update(data)
        return {"key": key, "version": version, "data": d}
    return _make


@pytest.fixture
def make_resolution():
    """Build a Resolution with sensible accepted-conference defaults."""
    def _make(**kw):
        base = {
            "item_key": "ABC123", "version": 1, "title": "A Great Paper",
            "arxiv_id": "2106.09685",
            "venue_raw": "International Conference on Learning Representations",
            "canonical": "ICLR", "kind": "conference", "year": 2021,
            "core_tier": "A*", "acceptance": "accepted",
            "confidence": 0.85, "citation_count": 100, "influential_citations": 10,
        }
        base.update(kw)
        return Resolution(**base)
    return _make


@pytest.fixture
def make_hit():
    """Build a VenueHit."""
    def _make(**kw):
        base = {"source": "semantic_scholar", "venue_raw": None}
        base.update(kw)
        return VenueHit(**base)
    return _make
