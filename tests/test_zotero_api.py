from unittest.mock import MagicMock

import requests

from arxiv_marker.zotero_api import ZoteroClient


def _client():
    c = ZoteroClient(base="https://api.zotero.org", api_key="KEY",
                     library_id="123", library_type="users")
    c.s = MagicMock()
    return c


def test_apply_changes_payload_and_version_header():
    c = _client()
    resp = MagicMock()
    c.s.patch.return_value = resp
    c.apply_changes("ITEMKEY", 42, "conferencePaper", {"proceedingsTitle": "ICLR"})
    args, kwargs = c.s.patch.call_args
    assert args[0] == "https://api.zotero.org/users/123/items/ITEMKEY"
    assert kwargs["json"] == {"proceedingsTitle": "ICLR", "itemType": "conferencePaper"}
    assert kwargs["headers"]["If-Unmodified-Since-Version"] == "42"
    resp.raise_for_status.assert_called_once()


def test_apply_changes_without_itemtype():
    c = _client()
    c.s.patch.return_value = MagicMock()
    c.apply_changes("K", 1, None, {"extra": "x"})
    _, kwargs = c.s.patch.call_args
    assert kwargs["json"] == {"extra": "x"}
    assert "itemType" not in kwargs["json"]


def test_patch_tags():
    c = _client()
    c.s.patch.return_value = MagicMock()
    c.patch_tags("K", 7, [{"tag": "x"}])
    _, kwargs = c.s.patch.call_args
    assert kwargs["json"] == {"tags": [{"tag": "x"}]}
    assert kwargs["headers"]["If-Unmodified-Since-Version"] == "7"


def test_api_key_header_set_on_session():
    c = ZoteroClient(base="https://api.zotero.org", api_key="SECRET")
    assert c.s.headers["Zotero-API-Key"] == "SECRET"


def test_ping_true_on_200():
    c = _client()
    c.s.get.return_value = MagicMock(status_code=200)
    assert c.ping() is True


def test_ping_false_on_request_error():
    c = _client()
    c.s.get.side_effect = requests.RequestException("boom")
    assert c.ping() is False


def test_get_collections_builds_parent_paths():
    c = _client()
    resp = MagicMock()
    resp.json.return_value = [
        {"key": "AAA", "data": {"name": "Parent", "parentCollection": False}},
        {"key": "BBB", "data": {"name": "Child", "parentCollection": "AAA"}},
        {"key": "CCC", "data": {"name": "Solo", "parentCollection": False}},
    ]
    c.s.get.return_value = resp
    assert c.get_collections() == {
        "AAA": "Parent", "BBB": "Parent / Child", "CCC": "Solo"}
