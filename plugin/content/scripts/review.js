// Review dialog logic for arxiv-marker. Runs in the modal dialog window's scope.
// window.arguments[0] = { resolutions, minConfidence, zh, accepted, selectedKeys }.
// "Write selected" fills selectedKeys + accepted=true; the opener then writes those items.

const HTML = "http://www.w3.org/1999/xhtml";
var ZM_IO;
var ZM_STR;

function zmTd(text, extra) {
  const e = document.createElementNS(HTML, "td");
  if (text !== undefined && text !== null) e.textContent = String(text);
  e.style.cssText = "padding: 5px 8px; vertical-align: top; border-bottom: 1px solid rgba(0,0,0,0.08);" + (extra || "");
  return e;
}

function zmCheckboxes() {
  return Array.from(document.querySelectorAll('#zm-table input[type="checkbox"]'));
}

function zmUpdateCount() {
  const checked = zmCheckboxes().filter((c) => c.checked).length;
  document.getElementById("zm-count").setAttribute("value", ZM_STR.count(checked));
}

function zmSetAll(val) {
  for (const cb of zmCheckboxes()) if (!cb.disabled) cb.checked = val;
  zmUpdateCount();
}

function zmDoWrite() {
  ZM_IO.selectedKeys = zmCheckboxes()
    .filter((c) => c.checked && !c.disabled)
    .map((c) => c.getAttribute("data-key"));
  ZM_IO.accepted = true;
  window.close();
}

function zmReviewLoad() {
  ZM_IO = window.arguments[0];
  const zh = !!ZM_IO.zh;
  ZM_STR = {
    head: zh
      ? "审核台 — 勾选要写回本地库的条目(低置信项默认不选,你来决定)"
      : "Review — check the items to write back to your library (low-confidence rows left unchecked)",
    all: zh ? "全选合格项" : "Select eligible",
    none: zh ? "全不选" : "Select none",
    cancel: zh ? "取消" : "Cancel",
    write: zh ? "写入所选" : "Write selected",
    cols: zh
      ? ["", "标题", "会议/期刊", "层级", "类型变更", "置信", "引用", "将写入字段"]
      : ["", "Title", "Venue", "Tier", "Type change", "Conf.", "Cites", "Fields to write"],
    nochange: zh ? "无可写入(未解析 / 已是目标)" : "no write (unresolved / already set)",
    count: (n) => (zh ? `已选 ${n} 项` : `${n} selected`),
  };

  document.getElementById("zm-head").setAttribute("value", ZM_STR.head);
  document.getElementById("zm-all").setAttribute("label", ZM_STR.all);
  document.getElementById("zm-none").setAttribute("label", ZM_STR.none);
  document.getElementById("zm-cancel").setAttribute("label", ZM_STR.cancel);
  document.getElementById("zm-write").setAttribute("label", ZM_STR.write);

  const table = document.getElementById("zm-table");

  const headtr = document.createElementNS(HTML, "tr");
  for (const c of ZM_STR.cols) {
    const th = document.createElementNS(HTML, "th");
    th.textContent = c;
    th.style.cssText =
      "padding: 6px 8px; text-align: left; position: sticky; top: 0; background: Field; border-bottom: 1px solid rgba(0,0,0,0.25); white-space: nowrap;";
    headtr.appendChild(th);
  }
  table.appendChild(headtr);

  const resolutions = ZM_IO.resolutions || [];
  for (const res of resolutions) {
    const eligible = !!res.target_item_type;
    const checked = eligible && Number(res.confidence) >= Number(ZM_IO.minConfidence);

    const tr = document.createElementNS(HTML, "tr");
    if (!eligible) tr.style.opacity = "0.55";

    const tdC = zmTd();
    const cb = document.createElementNS(HTML, "input");
    cb.type = "checkbox";
    cb.checked = checked;
    cb.disabled = !eligible;
    cb.setAttribute("data-key", res.item_key);
    cb.addEventListener("change", zmUpdateCount);
    tdC.appendChild(cb);
    tr.appendChild(tdC);

    tr.appendChild(zmTd(res.title || "(no title)", "max-width: 260px; word-break: break-word;"));
    tr.appendChild(zmTd(res.canonical || "—"));
    tr.appendChild(zmTd(res.core_tier || (res.kind === "journal" ? "journal" : "—")));
    tr.appendChild(
      zmTd(eligible ? `${res.current_item_type} → ${res.target_item_type}` : ZM_STR.nochange, "white-space: nowrap;")
    );
    tr.appendChild(zmTd(res.confidence != null ? Number(res.confidence).toFixed(2) : "—"));
    tr.appendChild(zmTd(res.citation_count != null ? String(res.citation_count) : "—"));

    const f = res.fields || {};
    const fstr = Object.keys(f)
      .filter((k) => k !== "extra")
      .map((k) => `${k}=${f[k]}`)
      .join("; ");
    tr.appendChild(zmTd(fstr, "max-width: 320px; word-break: break-word; color: #666;"));

    table.appendChild(tr);
  }

  document.getElementById("zm-all").addEventListener("command", () => zmSetAll(true));
  document.getElementById("zm-none").addEventListener("command", () => zmSetAll(false));
  document.getElementById("zm-cancel").addEventListener("command", () => {
    ZM_IO.accepted = false;
    window.close();
  });
  document.getElementById("zm-write").addEventListener("command", zmDoWrite);

  zmUpdateCount();
}
