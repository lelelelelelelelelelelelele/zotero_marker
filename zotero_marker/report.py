"""Reports: CSV (eyeball), JSON (consumed by `write`), and a self-contained HTML console."""
from __future__ import annotations

import csv
import html
import json
from pathlib import Path

from . import config
from .pipeline import Resolution

_COLUMNS = [
    "item_key", "title", "arxiv_id", "canonical", "year", "core_tier",
    "acceptance", "confidence", "citation_count", "current_item_type",
    "target_item_type", "proposed_changes", "sources", "evidence",
]


def _changes_str(fields: dict) -> str:
    return " ; ".join(f"{k}={str(v).replace(chr(10), ' / ')}" for k, v in (fields or {}).items())


def _row(r: Resolution) -> dict:
    d = r.to_dict()
    d["proposed_changes"] = _changes_str(r.fields)
    d["sources"] = ",".join(r.sources)
    d["evidence"] = " ; ".join(r.evidence)
    return {c: d.get(c, "") for c in _COLUMNS}


def write_reports(results: list[Resolution], out_dir: Path | None = None) -> tuple[Path, Path, Path]:
    out = out_dir or config.OUT_DIR
    out.mkdir(parents=True, exist_ok=True)
    csv_path, json_path, html_path = out / "resolutions.csv", out / "resolutions.json", out / "resolutions.html"

    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=_COLUMNS)
        w.writeheader()
        for r in results:
            w.writerow(_row(r))

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump([r.to_dict() for r in results], f, ensure_ascii=False, indent=2)

    html_path.write_text(_render_html(results), encoding="utf-8")
    return csv_path, json_path, html_path


# --------------------------------------------------------------------------- HTML

_CSS = """
:root{--bg:#0f1117;--card:#171a23;--line:#262b38;--fg:#e6e9ef;--mut:#8b93a7;--ok:#3fb950;--warn:#d29922;--a:#388bfd}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.5 ui-sans-serif,system-ui,"Segoe UI",Roboto,"PingFang SC","Microsoft YaHei",sans-serif}
header{padding:18px 22px;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--bg);z-index:5}
h1{font-size:16px;margin:0 0 4px}.sub{color:var(--mut);font-size:12px}
.bar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-top:12px}
.pill{background:var(--card);border:1px solid var(--line);color:var(--fg);border-radius:999px;padding:5px 12px;font-size:12px;cursor:pointer}
.pill.on{border-color:var(--a);color:#fff}
input[type=search]{flex:1;min-width:180px;background:var(--card);border:1px solid var(--line);color:var(--fg);border-radius:8px;padding:7px 12px}
button.act{background:var(--a);border:0;color:#fff;border-radius:8px;padding:7px 14px;cursor:pointer;font-weight:600}
table{width:100%;border-collapse:collapse}
th,td{text-align:left;padding:9px 10px;border-bottom:1px solid var(--line);vertical-align:top}
th{position:sticky;top:96px;background:var(--bg);color:var(--mut);font-weight:600;font-size:12px;cursor:pointer;user-select:none}
tr:hover td{background:#12151d}
.t{font-weight:600;max-width:360px}
.mut{color:var(--mut)}.tier{font-weight:700}.A\\*{color:#a371f7}
.tag{display:inline-block;background:#1f2430;border:1px solid var(--line);border-radius:6px;padding:1px 6px;margin:1px 2px;font-size:11px}
.type{font-size:12px}.arrow{color:var(--a)}
.ok{color:var(--ok)}.warn{color:var(--warn)}
.changes{font-family:ui-monospace,Consolas,monospace;font-size:11px;color:#c9d1d9;max-width:340px;white-space:pre-wrap}
a{color:var(--a)}
footer{padding:14px 22px;color:var(--mut);font-size:12px;border-top:1px solid var(--line)}
"""

_JS = """
const rows=[...document.querySelectorAll('tbody tr')];
function applyFilter(f){document.querySelectorAll('.pill').forEach(p=>p.classList.toggle('on',p.dataset.f===f));
 const q=document.getElementById('q').value.toLowerCase();
 rows.forEach(r=>{const okF=(f==='all')||r.dataset.cls===f||(f==='accepted'&&r.dataset.cls==='accepted')||(f.startsWith('CORE')&&r.dataset.core===f);
  const okQ=!q||r.dataset.title.includes(q);r.style.display=(okF&&okQ)?'':'none';});}
function copyKeys(){const ks=rows.filter(r=>r.style.display!=='none'&&r.querySelector('input').checked).map(r=>r.dataset.key);
 navigator.clipboard.writeText(ks.join(',')).then(()=>{const b=document.getElementById('copy');b.textContent='已复制 '+ks.length+' 个 key';setTimeout(()=>b.textContent='复制选中的 keys',1500);});}
function sortBy(i){const tb=document.querySelector('tbody');const sorted=rows.sort((a,b)=>{
 const x=a.children[i].dataset.s??a.children[i].innerText,y=b.children[i].dataset.s??b.children[i].innerText;
 const nx=parseFloat(x),ny=parseFloat(y);if(!isNaN(nx)&&!isNaN(ny))return ny-nx;return (''+x).localeCompare(''+y);});
 sorted.forEach(r=>tb.appendChild(r));}
document.querySelectorAll('.pill').forEach(p=>p.onclick=()=>applyFilter(p.dataset.f));
document.getElementById('q').oninput=()=>applyFilter(document.querySelector('.pill.on').dataset.f);
"""


def _tier_cell(tier: str | None) -> str:
    if not tier:
        return '<span class="mut">-</span>'
    color = "#a371f7" if tier == "A*" else "inherit"
    return f'<span class="tier" style="color:{color}">{html.escape(tier)}</span>'


def _render_html(results: list[Resolution]) -> str:
    accepted = [r for r in results if r.acceptance == "accepted"]
    a_star = sum(1 for r in accepted if r.core_tier == "A*")
    tr = []
    for r in results:
        cls = "accepted" if r.acceptance == "accepted" else "unknown"
        checked = "checked" if (r.acceptance == "accepted" and r.confidence >= 0.85 and r.fields) else ""
        type_cell = (f'{html.escape(r.current_item_type)} <span class="arrow">→</span> '
                     f'{html.escape(r.target_item_type)}' if r.target_item_type
                     else f'<span class="mut">{html.escape(r.current_item_type)} (no change)</span>')
        cites = "-" if r.citation_count is None else f"{r.citation_count:,}"
        ev = " ".join(f'<a href="{html.escape(u)}" target="_blank">[{i+1}]</a>'
                      for i, u in enumerate(_urls(r)))
        changes = html.escape(_changes_str(r.fields)) or '<span class="mut">—</span>'
        tr.append(
            f'<tr data-cls="{cls}" data-core="CORE {html.escape(r.core_tier or "")}" '
            f'data-key="{html.escape(r.item_key)}" data-title="{html.escape(r.title.lower())}">'
            f'<td><input type="checkbox" {checked}></td>'
            f'<td class="t">{html.escape(r.title)}<div class="mut">{html.escape(r.arxiv_id or "")}</div></td>'
            f'<td class="type">{type_cell}</td>'
            f'<td>{html.escape(r.canonical or "-")}<div class="mut">{html.escape(str(r.year or ""))}</div></td>'
            f'<td data-s="{_tier_sort(r.core_tier)}">{_tier_cell(r.core_tier)}</td>'
            f'<td data-s="{r.citation_count or 0}">{cites}</td>'
            f'<td data-s="{r.confidence}" class="{"ok" if r.confidence>=0.85 else "warn"}">{r.confidence:.2f}</td>'
            f'<td class="changes">{changes}</td>'
            f'<td>{ev or "-"}</td></tr>')

    pills = ('<span class="pill on" data-f="all">全部</span>'
             '<span class="pill" data-f="accepted">已解析</span>'
             '<span class="pill" data-f="unknown">unknown</span>'
             '<span class="pill" data-f="CORE A*">CORE A*</span>')
    head = ("<tr><th>✓</th>"
            "<th onclick='sortBy(1)'>标题 / arXiv</th>"
            "<th onclick='sortBy(2)'>类型变更</th>"
            "<th onclick='sortBy(3)'>Venue</th>"
            "<th onclick='sortBy(4)'>CORE</th>"
            "<th onclick='sortBy(5)'>被引</th><th onclick='sortBy(6)'>置信</th>"
            "<th>将写入的字段</th><th>证据</th></tr>")
    return f"""<!doctype html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>zotero-marker 审核台</title>
<style>{_CSS}</style></head><body>
<header><h1>zotero-marker · 写回审核台</h1>
<div class="sub">{len(results)} 条 · 已解析 {len(accepted)}(CORE A* {a_star}) · unknown {len(results)-len(accepted)} ·
 dry-run,勾选后用 <code>python run.py write --items &lt;keys&gt; --yes</code> 写入</div>
<div class="bar">{pills}<input id="q" type="search" placeholder="搜索标题…">
<button class="act" id="copy" onclick="copyKeys()">复制选中的 keys</button></div></header>
<table><thead>{head}</thead><tbody>{''.join(tr)}</tbody></table>
<footer>勾选要写入的条目 → 点“复制选中的 keys” → 终端运行
 <code>python run.py write --items 粘贴keys --yes</code>。已解析且置信≥0.85 的默认勾选。unknown 不会被写入。</footer>
<script>{_JS}</script></body></html>"""


def _urls(r: Resolution) -> list[str]:
    out = []
    for e in r.evidence:
        i = e.find("http")
        if i >= 0:
            out.append(e[i:].rstrip(") "))
    return out


def _tier_sort(t: str | None) -> int:
    return {"A*": 4, "A": 3, "B": 2, "C": 1}.get(t or "", 0)
