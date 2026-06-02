"""Reports: CSV (eyeball), JSON (consumed by `write`), and a self-contained HTML console.

The HTML console shares the live web UI's "Highlighter Desk" look (arxiv_marker/web.py)
but stays fully self-contained — no font CDN, no network — so it works offline as a file.
"""
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
    "target_item_type", "proposed_changes", "collections", "sources", "evidence",
]


def _changes_str(fields: dict) -> str:
    return " ; ".join(f"{k}={str(v).replace(chr(10), ' / ')}" for k, v in (fields or {}).items())


def _row(r: Resolution) -> dict:
    d = r.to_dict()
    d["proposed_changes"] = _changes_str(r.fields)
    d["collections"] = ", ".join(r.collections or [])
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
:root{
  --bg:#0b0d0c;--bg2:#0f1211;--panel:#131715;--panel2:#181d1a;
  --line:#242b27;--line2:#323a35;--fg:#eef1ea;--fg2:#c2c9bf;--mut:#7b847b;
  --mark:#c9f24a;--mark-dim:#aad23c;--mark-soft:rgba(201,242,74,.13);
  --violet:#b896ff;--blue:#76b6ff;--warn:#e9bb4f;
  --mono:ui-monospace,"SFMono-Regular",Consolas,"Cascadia Mono",monospace;
  --sans:ui-sans-serif,system-ui,"Segoe UI",Roboto,"PingFang SC","Microsoft YaHei",sans-serif;
  --serif:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,"Songti SC","SimSun",serif;
  --hh:150px;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.55 var(--sans);letter-spacing:.005em;min-height:100vh;
  background-image:radial-gradient(1100px 460px at 12% -8%,rgba(201,242,74,.06),transparent 60%),
    radial-gradient(900px 520px at 100% 0%,rgba(118,182,255,.045),transparent 55%);background-attachment:fixed}
body::before{content:"";position:fixed;inset:0;z-index:0;pointer-events:none;opacity:.04;
  background:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")}
a{color:var(--fg);text-decoration:none}
code{font-family:var(--mono);font-size:.84em;background:var(--panel2);border:1px solid var(--line);border-radius:5px;padding:1px 5px;color:var(--fg2)}

header{position:sticky;top:0;z-index:20;padding:18px 26px 14px;border-bottom:1px solid var(--line);
  backdrop-filter:blur(12px);background:linear-gradient(180deg,rgba(11,13,12,.94),rgba(11,13,12,.80))}
.brand-row{display:flex;align-items:baseline;gap:16px;flex-wrap:wrap}
.brand{font-family:var(--serif);font-weight:600;font-size:26px;line-height:1;letter-spacing:-.012em;display:inline-flex;align-items:baseline}
.brand .dot{color:var(--mark);padding:0 .05em}
.brand .sep{color:var(--mut);font-weight:400;margin:0 .35em;font-size:.7em}
.brand .m{position:relative;z-index:0}
.brand .m .swipe{position:absolute;left:-.05em;right:-.09em;bottom:.06em;height:.4em;z-index:-1;border-radius:2px;
  background:var(--mark);opacity:.85;transform:skewX(-12deg);transform-origin:left;animation:swipe .6s .15s both cubic-bezier(.2,.85,.2,1)}
@keyframes swipe{from{transform:skewX(-12deg) scaleX(0)}to{transform:skewX(-12deg) scaleX(1)}}
.tagline{color:var(--mut);font-size:12.5px}.tagline b{color:var(--fg2);font-weight:600}

.stats{display:flex;gap:10px;margin:16px 0 2px;flex-wrap:wrap}
.chip{appearance:none;cursor:pointer;display:flex;flex-direction:column;gap:2px;align-items:flex-start;color:var(--fg);
  background:var(--panel);border:1px solid var(--line);border-radius:13px;padding:8px 15px;min-width:74px;transition:transform .14s,border-color .14s,background .14s}
.chip:hover{transform:translateY(-1px);border-color:var(--line2)}
.chip .chip-n{font-family:var(--serif);font-weight:600;font-size:21px;line-height:1}
.chip .chip-l{font:600 10.5px var(--mono);letter-spacing:.06em;text-transform:uppercase;color:var(--mut)}
.chip.on{border-color:var(--fg2)}.chip.on .chip-l{color:var(--fg2)}
.chip-mark .chip-n{color:var(--mark)}
.chip-mark.on{border-color:var(--mark);background:var(--mark-soft)}

.toolbar{display:flex;gap:12px;align-items:center;margin-top:14px;flex-wrap:wrap}
.search{position:relative;flex:1;min-width:200px;max-width:380px}
.search input{width:100%;background:var(--panel);border:1px solid var(--line);color:var(--fg);border-radius:10px;padding:9px 12px 9px 33px;font:14px var(--sans)}
.search input:focus{outline:none;border-color:var(--mark);box-shadow:0 0 0 3px var(--mark-soft)}
.search .mag{position:absolute;left:11px;top:50%;transform:translateY(-50%);color:var(--mut);font-size:15px}
.coll{max-width:300px;background:var(--panel);border:1px solid var(--line);color:var(--fg);border-radius:10px;padding:9px 30px 9px 12px;font:13px var(--sans);cursor:pointer;
  appearance:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6' fill='none' stroke='%237b847b' stroke-width='1.6'%3E%3Cpath d='M1 1l4 4 4-4'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 12px center}
.coll:focus{outline:none;border-color:var(--mark);box-shadow:0 0 0 3px var(--mark-soft)}
.coll option{background:var(--panel);color:var(--fg)}
.spacer{flex:1 1 auto}
.btn{cursor:pointer;font:600 13.5px var(--sans);border-radius:10px;padding:9px 16px;border:1px solid var(--line2);background:var(--panel);color:var(--fg);transition:border-color .14s,background .14s}
.btn.mark{background:var(--mark);color:#0b0d0c;border-color:var(--mark);box-shadow:0 8px 22px -10px rgba(201,242,74,.55)}
.btn.mark:hover{background:#d7ff5e;border-color:#d7ff5e}

.wrap{padding:6px 16px 48px;position:relative;z-index:1;animation:fade .45s ease both}
@keyframes fade{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
table{width:100%;border-collapse:separate;border-spacing:0}
thead th{position:sticky;top:var(--hh);z-index:6;background:var(--bg);font:600 10.5px var(--mono);letter-spacing:.06em;
  text-transform:uppercase;color:var(--mut);text-align:left;padding:10px 12px;border-bottom:1px solid var(--line);white-space:nowrap;user-select:none}
th[data-col]{cursor:pointer}th[data-col]:hover{color:var(--fg2)}
th.asc::after{content:" ↑";color:var(--mark)}th.desc::after{content:" ↓";color:var(--mark)}
td{padding:11px 12px;border-bottom:1px solid var(--line);vertical-align:top}
tr.row:hover td{background:rgba(255,255,255,.018)}
tr.row.will{box-shadow:inset 3px 0 0 var(--mark)}
tr.row.will td{background:linear-gradient(90deg,var(--mark-soft),transparent 46%)}
tr.row.dim td{opacity:.5}
.mut{color:var(--mut)}
.c-check{width:36px}.c-check input{width:16px;height:16px;accent-color:var(--mark);cursor:pointer;margin-top:2px}
.c-check input:disabled{cursor:default;opacity:.4}
.c-title{max-width:340px}
.title{font-weight:600;line-height:1.34;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.sub{font:11.5px var(--mono);color:var(--mut);margin-top:3px}
.ax{color:var(--mut)}.ax:hover{color:var(--mark)}
.chg{display:inline-flex;align-items:center;gap:6px;font:12px var(--mono);white-space:nowrap}
.chg .from{color:var(--mut)}.chg .ar{color:var(--mark)}
.chg .to{color:var(--fg);background:var(--mark-soft);border:1px solid rgba(201,242,74,.26);border-radius:5px;padding:1px 6px}
.c-venue{max-width:200px}.ven{font-weight:500}
.tier{font:700 12px var(--mono);border-radius:6px;padding:2px 8px;display:inline-block}
.t-As{color:var(--violet);background:rgba(184,150,255,.12);border:1px solid rgba(184,150,255,.32)}
.t-A{color:var(--blue);background:rgba(118,182,255,.10);border:1px solid rgba(118,182,255,.28)}
.t-B,.t-C{color:var(--fg2);background:var(--panel2);border:1px solid var(--line)}
.c-cites{font-family:var(--mono);white-space:nowrap}
.cn{font-size:13.5px}.ci{display:block;font-size:10.5px;color:var(--mut);margin-top:2px}
.c-conf{width:98px}
.meter{height:5px;border-radius:3px;background:var(--panel2);overflow:hidden;margin-bottom:4px}
.meter span{display:block;height:100%;border-radius:3px}
.meter.ok span{background:var(--mark)}.meter.warn span{background:var(--warn)}.meter.zero span{background:var(--line2)}
.cval{font:600 12px var(--mono)}.cval.ok{color:var(--mark)}.cval.warn{color:var(--warn)}.cval.zero{color:var(--mut)}
.c-fields{max-width:420px}
.fwrap{display:flex;flex-wrap:wrap;gap:4px}
.fchip{font:11px var(--mono);background:var(--panel2);border:1px solid var(--line);border-radius:5px;padding:1px 6px;max-width:182px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--mut);display:inline-block}
.fchip b{color:var(--fg2);font-weight:600;margin-right:5px}
.c-coll{max-width:200px}
.src{font:11px var(--mono);background:var(--panel2);border:1px solid var(--line);border-radius:5px;padding:1px 7px;margin:0 4px 4px 0;color:var(--fg2);display:inline-block}
.c-ev a{color:var(--blue);margin-right:6px;font-size:12px}.c-ev a:hover{color:var(--mark)}
footer{position:relative;z-index:1;padding:18px 26px 42px;color:var(--mut);font-size:12px;border-top:1px solid var(--line)}
footer b{color:var(--fg2)}
@media (max-width:980px){.c-cites,.c-coll{display:none}}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
"""

_JS = """
const rows=[...document.querySelectorAll('#tbody tr.row')];
let F='all',C='',Q='';
function vis(r){
  const acc=r.dataset.acc;
  const okF=(F==='all')||(F==='accepted'&&acc==='accepted')||(F==='unknown'&&acc==='unknown')
    ||(F==='astar'&&r.dataset.tier==='A*')||(F==='will'&&r.dataset.will==='1');
  let okC=!C; if(C){try{okC=JSON.parse(r.dataset.colls||'[]').includes(C);}catch(e){okC=false;}}
  const okQ=!Q||r.dataset.title.includes(Q);
  return okF&&okC&&okQ;
}
function apply(){rows.forEach(r=>{r.style.display=vis(r)?'':'none';});}
document.querySelectorAll('.chip').forEach(c=>c.onclick=()=>{F=c.dataset.f;
  document.querySelectorAll('.chip').forEach(x=>x.classList.toggle('on',x.dataset.f===F));apply();});
const q=document.getElementById('q');q.oninput=()=>{Q=q.value.trim().toLowerCase();apply();};
const coll=document.getElementById('coll');if(coll)coll.onchange=()=>{C=coll.value;apply();};
function sortBy(i,th){
  const tb=document.querySelector('tbody');
  const dir=th.classList.contains('asc')?-1:1;
  document.querySelectorAll('th[data-col]').forEach(h=>h.classList.remove('asc','desc'));
  th.classList.add(dir>0?'asc':'desc');
  rows.sort((a,b)=>{const x=a.children[i].dataset.s??a.children[i].innerText,y=b.children[i].dataset.s??b.children[i].innerText;
    const nx=parseFloat(x),ny=parseFloat(y);if(!isNaN(nx)&&!isNaN(ny))return (nx-ny)*dir;return (''+x).localeCompare(''+y)*dir;});
  rows.forEach(r=>tb.appendChild(r));
}
function copyKeys(){const ks=rows.filter(r=>r.style.display!=='none'&&r.querySelector('input').checked).map(r=>r.dataset.key);
  navigator.clipboard.writeText(ks.join(',')).then(()=>{const b=document.getElementById('copy');const t=b.textContent;
    b.textContent='已复制 '+ks.length+' 个 key';setTimeout(()=>b.textContent=t,1500);});}
addEventListener('keydown',e=>{if(e.key==='/'&&document.activeElement!==q){e.preventDefault();q.focus();}});
"""


def _e(s) -> str:
    return html.escape("" if s is None else str(s))


def _tier_badge(t: str | None) -> str:
    if not t:
        return '<span class="mut">—</span>'
    return f'<span class="tier t-{"As" if t == "A*" else _e(t)}">{_e(t)}</span>'


def _conf_html(c: float) -> str:
    pct = round((c or 0) * 100)
    k = "ok" if c >= 0.85 else ("warn" if c > 0 else "zero")
    return f'<div class="meter {k}"><span style="width:{pct}%"></span></div><span class="cval {k}">{c:.2f}</span>'


def _field_chips(fields: dict) -> str:
    if not fields:
        return '<span class="mut">—</span>'
    chips = []
    for k, v in fields.items():
        val = _e(str(v).replace("\n", " · "))
        chips.append(f'<span class="fchip" title="{_e(k + " = " + str(v))}"><b>{_e(k)}</b>{val}</span>')
    return f'<div class="fwrap">{"".join(chips)}</div>'


def _eligible(r: Resolution) -> bool:
    return r.acceptance == "accepted" and r.confidence >= 0.85 and bool(r.fields)


def _render_html(results: list[Resolution]) -> str:
    accepted = [r for r in results if r.acceptance == "accepted"]
    a_star = sum(1 for r in accepted if r.core_tier == "A*")
    will = sum(1 for r in results if _eligible(r))

    # open with the actionable rows on top (eligible, then high confidence, then high cites)
    disp = sorted(results, key=lambda r: (0 if _eligible(r) else 1,
                                          -(r.confidence or 0), -(r.citation_count or 0)))

    coll_counts: dict[str, int] = {}
    for r in results:
        for c in (r.collections or []):
            coll_counts[c] = coll_counts.get(c, 0) + 1

    tr = []
    for r in disp:
        acc = "accepted" if r.acceptance == "accepted" else "unknown"
        cls = "row" + (" will" if _eligible(r) else (" dim" if acc == "unknown" else ""))
        checked = "checked" if _eligible(r) else ""
        dis = "" if (r.target_item_type and r.fields) else "disabled"
        colls_json = html.escape(json.dumps(r.collections or [], ensure_ascii=False), quote=True)

        type_cell = (f'<span class="chg"><span class="from">{_e(r.current_item_type)}</span>'
                     f'<span class="ar">→</span><span class="to">{_e(r.target_item_type)}</span></span>'
                     if r.target_item_type else '<span class="mut">no change</span>')
        ax = (f'<a class="ax" href="https://arxiv.org/abs/{_e(r.arxiv_id)}" target="_blank" '
              f'rel="noopener">{_e(r.arxiv_id)} ↗</a>' if r.arxiv_id else "")
        venue_sub = " · ".join(str(x) for x in [r.year, r.kind] if x)
        cites = ('<span class="mut">—</span>' if r.citation_count is None
                 else f'<span class="cn">{r.citation_count:,}</span>'
                 + (f'<span class="ci">{r.influential_citations:,} infl</span>' if r.influential_citations else ""))
        colls_cell = ("".join(f'<span class="src">{_e(c)}</span>' for c in (r.collections or []))
                      or '<span class="mut">—</span>')
        ev = " ".join(f'<a href="{_e(u)}" target="_blank" rel="noopener">[{i + 1}]</a>'
                      for i, u in enumerate(_urls(r))) or '<span class="mut">—</span>'

        tr.append(
            f'<tr class="{cls}" data-key="{_e(r.item_key)}" data-acc="{acc}" '
            f'data-tier="{_e(r.core_tier or "")}" data-will="{"1" if _eligible(r) else "0"}" '
            f'data-title="{_e((r.title or "").lower())}" data-colls="{colls_json}">'
            f'<td class="c-check"><input type="checkbox" {checked} {dis}></td>'
            f'<td class="c-title"><div class="title" title="{_e(r.title)}">{_e(r.title)}</div>'
            f'<div class="sub">{ax}</div></td>'
            f'<td class="c-chg">{type_cell}</td>'
            f'<td class="c-venue"><div class="ven">{_e(r.canonical or "—")}</div>'
            f'<div class="sub mut">{_e(venue_sub)}</div></td>'
            f'<td class="c-core" data-s="{_tier_sort(r.core_tier)}">{_tier_badge(r.core_tier)}</td>'
            f'<td class="c-cites" data-s="{r.citation_count or 0}">{cites}</td>'
            f'<td class="c-conf" data-s="{r.confidence}">{_conf_html(r.confidence)}</td>'
            f'<td class="c-fields">{_field_chips(r.fields)}</td>'
            f'<td class="c-coll">{colls_cell}</td>'
            f'<td class="c-ev">{ev}</td></tr>')

    chips = (
        f'<button class="chip on" data-f="all"><span class="chip-n">{len(results)}</span><span class="chip-l">全部</span></button>'
        f'<button class="chip" data-f="accepted"><span class="chip-n">{len(accepted)}</span><span class="chip-l">已解析</span></button>'
        f'<button class="chip" data-f="unknown"><span class="chip-n">{len(results) - len(accepted)}</span><span class="chip-l">unknown</span></button>'
        f'<button class="chip" data-f="astar"><span class="chip-n">{a_star}</span><span class="chip-l">CORE A*</span></button>'
        f'<button class="chip chip-mark" data-f="will"><span class="chip-n">{will}</span><span class="chip-l">可写入</span></button>'
    )
    coll_html = ""
    if coll_counts:
        opts = f'<option value="">全部分类 ({len(results)})</option>' + "".join(
            f'<option value="{_e(c)}">{_e(c)} ({n})</option>'
            for c, n in sorted(coll_counts.items(), key=lambda kv: kv[0]))
        coll_html = f'<select id="coll" class="coll" aria-label="按 Zotero 分类筛选">{opts}</select>'

    head = ('<tr><th class="c-check"></th>'
            '<th data-col onclick="sortBy(1,this)">标题 / arXiv</th>'
            '<th>类型变更</th>'
            '<th data-col onclick="sortBy(3,this)">Venue</th>'
            '<th data-col onclick="sortBy(4,this)">CORE</th>'
            '<th data-col onclick="sortBy(5,this)">被引</th>'
            '<th data-col onclick="sortBy(6,this)">置信</th>'
            '<th>将写入的字段</th>'
            '<th data-col onclick="sortBy(8,this)">分类</th>'
            '<th>证据</th></tr>')

    return f"""<!doctype html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>arxiv-marker · 写回审核台</title>
<style>{_CSS}</style></head><body>
<header>
  <div class="brand-row">
    <div class="brand">arxiv<span class="dot">·</span><span class="m">marker<span class="swipe"></span></span><span class="sep">写回审核台</span></div>
    <div class="tagline">{len(results)} 条 · 已解析 {len(accepted)}(CORE A* {a_star}) · unknown {len(results) - len(accepted)} ·
      <b>dry-run,勾选后复制 keys 写入</b></div>
  </div>
  <div class="stats">{chips}</div>
  <div class="toolbar">
    <div class="search"><span class="mag">⌕</span><input id="q" type="search" placeholder="搜索标题…" autocomplete="off"></div>
    {coll_html}
    <span class="spacer"></span>
    <button class="btn mark" id="copy" onclick="copyKeys()">复制选中的 keys</button>
  </div>
</header>
<div class="wrap"><table><thead>{head}</thead><tbody id="tbody">{''.join(tr)}</tbody></table></div>
<footer>勾选要写入的条目 → 点 <b>复制选中的 keys</b> → 终端运行
 <code>python run.py write --items 粘贴keys --yes</code>。已解析且置信≥0.85 的默认已勾选;unknown 不会被写入。
 可按 <b>分类</b> 下拉只看某个 Zotero 收藏夹。</footer>
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
