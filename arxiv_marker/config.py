"""Configuration + minimal .env loading (no external deps)."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv(p: Path) -> None:
    """Read KEY=VALUE lines from a .env file into os.environ (without overriding)."""
    if not p.exists():
        return
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


_load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "out"

# Zotero local API by default (Zotero 7+ desktop running). No key needed locally.
ZOTERO_API_BASE = os.environ.get("ZOTERO_API_BASE", "http://localhost:23119/api")
ZOTERO_LIBRARY_ID = os.environ.get("ZOTERO_LIBRARY_ID", "")  # set in .env; no default (don't target a stranger's library)
ZOTERO_LIBRARY_TYPE = os.environ.get("ZOTERO_LIBRARY_TYPE", "users")  # users | groups
ZOTERO_API_KEY = os.environ.get("ZOTERO_API_KEY", "")  # required for WRITES (web API)
# Reads use the local API (read-only). Writes must go through the web API, which the
# local API rejects with 501. ZOTERO_WRITE_BASE is the web endpoint used for writes.
ZOTERO_WRITE_BASE = os.environ.get("ZOTERO_WRITE_BASE", "https://api.zotero.org")

SEMANTIC_SCHOLAR_KEY = os.environ.get("S2_API_KEY", "")
CONTACT_EMAIL = os.environ.get("CONTACT_EMAIL", "anonymous@example.com")
