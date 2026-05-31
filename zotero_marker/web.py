"""Optional local web UI (needs the `web` extra: fastapi + uvicorn).

A thin browser front-end over the same resolve/write pipeline: review the proposed
changes in a table, then write the ones you tick — without leaving the browser.

Safety: binds to 127.0.0.1 only; the /api/write endpoint requires ZOTERO_API_KEY,
an explicit click + confirm, and only writes rows at/above the confidence bar.
Launch with `python run.py web` (or `uv run python run.py web`).
"""
# NB: no `from __future__ import annotations` here — FastAPI must see the real
# (non-stringized) Pydantic model annotation on the closure-local request body,
# otherwise it can't resolve it and treats the body as a query param.
import json

from . import config
from .pipeline import resolve_items
from .report import _CSS, write_reports
from .resolvers import DBLP, SemanticScholar
from .zotero_api import ZoteroClient


def _load_records() -> list[dict]:
    p = config.OUT_DIR / "resolutions.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return []


def create_app():
    """Build the FastAPI app. Imports fastapi lazily so the core CLI needs no web deps."""
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.responses import HTMLResponse
        from pydantic import BaseModel
    except ModuleNotFoundError as e:  # pragma: no cover - exercised via the CLI message
        raise SystemExit(
            "The web UI needs the 'web' extra. Install it with:  uv sync --extra web"
        ) from e

    app = FastAPI(title="zotero-marker", docs_url=None, redoc_url=None)

    class WriteReq(BaseModel):
        keys: list[str]
        threshold: float = 0.85

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return _PAGE

    @app.get("/api/resolutions")
    def api_resolutions() -> list[dict]:
        """The most recent dry-run results (from out/resolutions.json)."""
        return _load_records()

    @app.post("/api/resolve")
    def api_resolve() -> list[dict]:
        """Re-run the read-only resolve cascade against the live Zotero library."""
        from .cli import _gather  # local import avoids any import-order coupling

        zot = ZoteroClient()
        if not zot.ping():
            raise HTTPException(503, "Zotero desktop not reachable at localhost:23119.")
        items = _gather(zot, None, None)
        results = resolve_items(items, SemanticScholar(), DBLP())
        write_reports(results)
        return [r.to_dict() for r in results]

    @app.post("/api/write")
    def api_write(req: WriteReq) -> dict:
        """Apply the proposed field changes for the picked keys (the only mutating call)."""
        if not config.ZOTERO_API_KEY:
            raise HTTPException(400, "Writing needs ZOTERO_API_KEY in .env (the local API is read-only).")
        records = {r["item_key"]: r for r in _load_records()}
        zot = ZoteroClient(base=config.ZOTERO_WRITE_BASE, api_key=config.ZOTERO_API_KEY)
        results = []
        for key in req.keys:
            r = records.get(key)
            if not r or not r.get("target_item_type") or not r.get("fields"):
                results.append({"key": key, "ok": False, "error": "no proposal / not eligible"})
                continue
            if float(r.get("confidence") or 0) < req.threshold:
                results.append({"key": key, "ok": False, "error": "below confidence threshold"})
                continue
            try:
                # guard on the resolve-time version (see the CLI note); 412 if it changed
                zot.apply_changes(key, int(r.get("version") or 0), r["target_item_type"], r["fields"])
                results.append({"key": key, "ok": True, "venue": r.get("canonical")})
            except Exception as e:  # noqa: BLE001 - report per-item, never abort the batch
                msg = "item changed since resolve — re-resolve" if "412" in str(e) else str(e)
                results.append({"key": key, "ok": False, "error": msg})
        return {"results": results}

    return app


def main(host: str = "127.0.0.1", port: int = 8000) -> None:
    import uvicorn

    print(f"zotero-marker web UI → http://{host}:{port}  (Ctrl+C to stop)")
    uvicorn.run(create_app(), host=host, port=port, log_level="warning")


_JS = r"""
const E=(s,p=document)=>p.querySelector(s);
let RECS=[];
const fmt=n=>n==null?'-':(''+n).replace(/\B(?=(\d{3})+(?!\d))/g,',');
function esc(s){const d=document.createElement('div');d.textContent=(s==null?'':s);return d.innerHTML;}
function setStatus(t){E('#status').textContent=t;}
function render(){
  const q=(E('#q').value||'').toLowerCase();
  const acc=RECS.filter(r=>r.acceptance==='accepted').length;
  E('#sub').textContent=`${RECS.length} items · ${acc} resolved · ${RECS.length-acc} unknown · dry-run until you click Write`;
  E('#thead').innerHTML='<tr><th>✓</th><th>Title / arXiv</th><th>Type change</th><th>Venue</th><th>CORE</th><th>Cites</th><th>Conf.</th><th>Fields to write</th><th>Status</th></tr>';
  const tb=E('#tbody'); tb.innerHTML='';
  for(const r of RECS){
    if(q && !(r.title||'').toLowerCase().includes(q)) continue;
    const elig = r.acceptance==='accepted' && r.target_item_type && (r.confidence>=0.85);
    const tr=document.createElement('tr'); tr.dataset.key=r.item_key;
    const chg = r.target_item_type ? `${esc(r.current_item_type)} → ${esc(r.target_item_type)}` : '<span class=mut>no change</span>';
    const fields = (r.fields && Object.keys(r.fields).length)
      ? Object.entries(r.fields).map(([k,v])=>`${k}=${(''+v).replace(/\n/g,' / ')}`).join(' ; ') : '—';
    tr.innerHTML =
      `<td><input type=checkbox ${elig?'checked':''} ${r.target_item_type?'':'disabled'}></td>`+
      `<td class=t>${esc(r.title)}<div class=mut>${esc(r.arxiv_id||'')}</div></td>`+
      `<td class=type>${chg}</td>`+
      `<td>${esc(r.canonical||'-')}<div class=mut>${esc(''+(r.year||''))}</div></td>`+
      `<td class=tier>${esc(r.core_tier||'-')}</td>`+
      `<td>${fmt(r.citation_count)}</td>`+
      `<td class="${r.confidence>=0.85?'ok':'warn'}">${(r.confidence||0).toFixed(2)}</td>`+
      `<td class=changes>${esc(fields)}</td>`+
      `<td class=stat></td>`;
    tb.appendChild(tr);
  }
}
async function load(){ try{ RECS=await (await fetch('/api/resolutions')).json(); render(); }catch(e){ setStatus('load failed: '+e.message);} }
E('#q').oninput=render;
E('#resolve').onclick=async()=>{
  setStatus('resolving… (querying Semantic Scholar / DBLP)'); E('#resolve').disabled=true;
  try{ const r=await fetch('/api/resolve',{method:'POST'}); const d=await r.json(); if(!r.ok)throw new Error(d.detail||r.status); RECS=d; render(); setStatus('resolved '+RECS.length+' items'); }
  catch(e){ setStatus('resolve failed: '+e.message); }
  finally{ E('#resolve').disabled=false; }
};
E('#write').onclick=async()=>{
  const keys=[...document.querySelectorAll('#tbody tr')]
    .filter(tr=>tr.style.display!=='none')
    .map(tr=>[tr,tr.querySelector('input')])
    .filter(([_,c])=>c && c.checked && !c.disabled)
    .map(([tr])=>tr.dataset.key);
  if(!keys.length){ setStatus('nothing selected'); return; }
  if(!confirm(`Write venue metadata to ${keys.length} item(s) in Zotero?\nThis changes their itemType + fields.`)) return;
  setStatus('writing '+keys.length+'…'); E('#write').disabled=true;
  try{
    const r=await fetch('/api/write',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({keys})});
    const data=await r.json(); if(!r.ok)throw new Error(data.detail||r.status);
    let ok=0;
    for(const res of data.results){
      const tr=document.querySelector(`#tbody tr[data-key="${res.key}"]`); if(!tr)continue;
      const cell=tr.querySelector('.stat');
      cell.textContent=res.ok?'✓ written':('✗ '+res.error); cell.className='stat '+(res.ok?'st-ok':'st-err');
      if(res.ok)ok++;
    }
    setStatus(`wrote ${ok}/${data.results.length}`);
  }catch(e){ setStatus('write failed: '+e.message); }
  finally{ E('#write').disabled=false; }
};
load();
"""

_PAGE = ("""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>zotero-marker</title>
<style>__CSS__
.toolbar{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
button.act{cursor:pointer}button.act:disabled{opacity:.5;cursor:default}
.st-ok{color:var(--ok)}.st-err{color:#f85149}.stat{font-size:11px;white-space:nowrap}
#status{margin-left:auto;color:var(--mut)}
</style></head><body>
<header>
  <h1>zotero-marker · web</h1>
  <div class="sub" id="sub">loading…</div>
  <div class="bar toolbar">
    <input id="q" type="search" placeholder="search title…">
    <button class="act" id="resolve">Re-resolve from Zotero</button>
    <button class="act" id="write">Write selected →</button>
    <span id="status"></span>
  </div>
</header>
<table><thead id="thead"></thead><tbody id="tbody"></tbody></table>
<footer>Reads the local Zotero API; writes go through the Zotero Web API and need
<code>ZOTERO_API_KEY</code>. Only ticked rows at/above the confidence bar are written.
Bound to 127.0.0.1.</footer>
<script>__JS__</script></body></html>"""
         .replace("__CSS__", _CSS).replace("__JS__", _JS))
