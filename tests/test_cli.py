import argparse
import json

import pytest

from zotero_marker import cli


def test_version_flag(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.build_parser().parse_args(["--version"])
    assert exc.value.code == 0
    assert "zotero-marker" in capsys.readouterr().out


def test_parser_resolve_defaults():
    args = cli.build_parser().parse_args(["resolve"])
    assert args.cmd == "resolve"
    assert args.limit is None
    assert args.items is None


def test_parser_write_flags():
    args = cli.build_parser().parse_args(
        ["write", "--items", "A,B", "--threshold", "0.9", "--yes"])
    assert args.cmd == "write"
    assert args.items == "A,B"
    assert args.threshold == 0.9
    assert args.yes is True


def test_cmd_write_dry_run_counts_eligible(tmp_path, monkeypatch, capsys):
    records = [
        {"item_key": "K1", "target_item_type": "conferencePaper", "fields": {"x": 1},
         "confidence": 0.9, "current_item_type": "preprint", "canonical": "ICLR"},
        {"item_key": "K2", "target_item_type": "conferencePaper", "fields": {"x": 1},
         "confidence": 0.5, "current_item_type": "preprint", "canonical": "X"},      # below bar
        {"item_key": "K3", "target_item_type": None, "fields": {},
         "confidence": 0.99, "current_item_type": "preprint", "canonical": None},    # unknown
    ]
    p = tmp_path / "resolutions.json"
    p.write_text(json.dumps(records), encoding="utf-8")
    monkeypatch.setattr(cli.config, "ZOTERO_API_KEY", "KEY")
    monkeypatch.setattr(cli.config, "ZOTERO_LIBRARY_ID", "123")

    class _FakeClient:
        def __init__(self, *a, **k):
            pass

        def ping(self):
            return True

    monkeypatch.setattr(cli, "ZoteroClient", _FakeClient)
    ns = argparse.Namespace(from_json=str(p), threshold=0.85, items=None, yes=False)
    rc = cli.cmd_write(ns)
    out = capsys.readouterr().out
    assert rc == 0
    assert "1 item(s) eligible" in out      # only K1 clears the bar + has a target
    assert "DRY-RUN" in out


def test_cmd_write_missing_json(tmp_path, capsys):
    ns = argparse.Namespace(from_json=str(tmp_path / "nope.json"),
                            threshold=0.85, items=None, yes=False)
    assert cli.cmd_write(ns) == 2
    assert "not found" in capsys.readouterr().err


def test_cmd_write_requires_library_id(tmp_path, monkeypatch, capsys):
    p = tmp_path / "resolutions.json"
    p.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(cli.config, "ZOTERO_API_KEY", "KEY")
    monkeypatch.setattr(cli.config, "ZOTERO_LIBRARY_ID", "")
    ns = argparse.Namespace(from_json=str(p), threshold=0.85, items=None, yes=False)
    assert cli.cmd_write(ns) == 2
    assert "ZOTERO_LIBRARY_ID" in capsys.readouterr().err
