"""Thin Zotero API client. Defaults to the local API (no key); supports the web API."""
from __future__ import annotations

import requests

from . import config


class ZoteroClient:
    def __init__(self, base=None, library_id=None, library_type=None,
                 api_key=None, timeout=20):
        self.base = (base or config.ZOTERO_API_BASE).rstrip("/")
        self.library_id = library_id or config.ZOTERO_LIBRARY_ID
        self.library_type = library_type or config.ZOTERO_LIBRARY_TYPE
        self.api_key = api_key if api_key is not None else config.ZOTERO_API_KEY
        self.timeout = timeout
        self.s = requests.Session()
        if self.api_key:
            self.s.headers["Zotero-API-Key"] = self.api_key

    @property
    def _prefix(self) -> str:
        return f"{self.base}/{self.library_type}/{self.library_id}"

    def ping(self) -> bool:
        try:
            r = self.s.get(f"{self._prefix}/items",
                           params={"limit": 1, "format": "json"}, timeout=self.timeout)
            return r.status_code == 200
        except requests.RequestException:
            return False

    def iter_items(self, item_type="preprint", limit=100):
        """Yield raw item dicts of a given itemType (paginated)."""
        start = 0
        while True:
            r = self.s.get(f"{self._prefix}/items",
                           params={"itemType": item_type, "limit": limit,
                                   "start": start, "format": "json"},
                           timeout=self.timeout)
            r.raise_for_status()
            batch = r.json()
            if not batch:
                return
            yield from batch
            if len(batch) < limit:
                return
            start += limit

    def get_item(self, key: str) -> dict:
        r = self.s.get(f"{self._prefix}/items/{key}",
                       params={"format": "json"}, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def patch_tags(self, key: str, version: int, tags: list[dict]) -> requests.Response:
        """Replace the item's tag list (caller must pass the full, merged list)."""
        return self._patch(key, version, {"tags": tags})

    def apply_changes(self, key: str, version: int, item_type: str | None,
                      fields: dict) -> requests.Response:
        """Change itemType (optional) and set venue/metadata fields in one PATCH.
        Zotero keeps valid fields and drops fields invalid for the new type."""
        payload = dict(fields)
        if item_type:
            payload["itemType"] = item_type
        return self._patch(key, version, payload)

    def _patch(self, key: str, version: int, payload: dict) -> requests.Response:
        r = self.s.patch(
            f"{self._prefix}/items/{key}",
            json=payload,
            headers={"If-Unmodified-Since-Version": str(version),
                     "Content-Type": "application/json"},
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r
