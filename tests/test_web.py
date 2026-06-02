import json

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from arxiv_marker import web  # noqa: E402

_RECORDS = [
    {"item_key": "K1", "title": "Paper One", "target_item_type": "conferencePaper",
     "fields": {"proceedingsTitle": "ICLR"}, "confidence": 0.9, "acceptance": "accepted",
     "current_item_type": "preprint", "canonical": "ICLR", "core_tier": "A*",
     "citation_count": 100, "arxiv_id": "2106.00001", "year": 2021},
    {"item_key": "K2", "title": "Paper Two", "target_item_type": "conferencePaper",
     "fields": {"proceedingsTitle": "X"}, "confidence": 0.5, "acceptance": "accepted",
     "current_item_type": "preprint", "canonical": "X", "core_tier": None,
     "citation_count": 1, "arxiv_id": "2106.00002", "year": 2021},
    {"item_key": "K3", "title": "Paper Three", "target_item_type": None, "fields": {},
     "confidence": 0.0, "acceptance": "unknown", "current_item_type": "preprint",
     "canonical": None, "core_tier": None, "citation_count": None,
     "arxiv_id": "2106.00003", "year": None},
]


@pytest.fixture
def client(tmp_path, monkeypatch):
    (tmp_path / "resolutions.json").write_text(json.dumps(_RECORDS), encoding="utf-8")
    monkeypatch.setattr(web.config, "OUT_DIR", tmp_path)
    return TestClient(web.create_app())


def test_index_serves_html(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "arxiv-marker" in r.text
    assert "Write selected" in r.text


def test_resolutions_endpoint(client):
    r = client.get("/api/resolutions")
    assert r.status_code == 200
    assert [x["item_key"] for x in r.json()] == ["K1", "K2", "K3"]


def test_write_requires_api_key(client, monkeypatch):
    monkeypatch.setattr(web.config, "ZOTERO_API_KEY", "")
    r = client.post("/api/write", json={"keys": ["K1"]})
    assert r.status_code == 400


def test_write_applies_only_eligible(client, monkeypatch):
    monkeypatch.setattr(web.config, "ZOTERO_API_KEY", "KEY")

    class _FakeZot:
        def __init__(self, *a, **k):
            pass

        def get_item(self, key):
            return {"version": 5}

        def apply_changes(self, key, version, itype, fields):
            return None

    monkeypatch.setattr(web, "ZoteroClient", _FakeZot)
    r = client.post("/api/write", json={"keys": ["K1", "K2", "K3"]})
    assert r.status_code == 200
    res = {x["key"]: x for x in r.json()["results"]}
    assert res["K1"]["ok"] is True
    assert res["K2"]["ok"] is False and "threshold" in res["K2"]["error"]
    assert res["K3"]["ok"] is False                      # no target_item_type


def test_write_persists_applied_change_to_cache(client, monkeypatch):
    """Regression: after a successful write, a page refresh (re-read of the cache file)
    must NOT resurrect the row as an unwritten preprint."""
    monkeypatch.setattr(web.config, "ZOTERO_API_KEY", "KEY")

    class _Resp:
        headers = {"Last-Modified-Version": "777"}

    class _FakeZot:
        def __init__(self, *a, **k):
            pass

        def apply_changes(self, key, version, itype, fields):
            return _Resp()

    monkeypatch.setattr(web, "ZoteroClient", _FakeZot)
    assert client.post("/api/write", json={"keys": ["K1"]}).status_code == 200

    recs = {r["item_key"]: r for r in client.get("/api/resolutions").json()}
    assert recs["K1"]["target_item_type"] is None        # proposal cleared
    assert recs["K1"]["fields"] == {}
    assert recs["K1"]["current_item_type"] == "conferencePaper"   # now matches Zotero
    assert recs["K1"]["version"] == 777                  # advanced to the new server version
    assert recs["K2"]["target_item_type"] == "conferencePaper"    # untouched rows stay pending
