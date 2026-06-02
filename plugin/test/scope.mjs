// Simulates Zotero's loadSubScript loading: zm-data.js then resolver.js are evaluated as
// classic scripts in ONE shared scope with NO `require`/`module` (exactly the Zotero
// sandbox). Verifies the free-variable wiring (resolver reads ZM_RANKINGS/ZM_OVERRIDES
// from zm-data, exposes ZMResolver) and that a resolve runs end-to-end in that scope —
// the one part of the Zotero load path otherwise only testable inside Zotero.
import vm from "node:vm";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const scripts = resolve(here, "..", "content", "scripts");

// A sandbox WITHOUT require/module (like the Zotero scope). Inject only non-intrinsic globals.
const sandbox = { console, setTimeout, clearTimeout };
vm.createContext(sandbox);

for (const f of ["zm-data.js", "resolver.js"]) {
  vm.runInContext(readFileSync(resolve(scripts, f), "utf8"), sandbox, { filename: f });
}

let pass = 0,
  fail = 0;
const ok = (c, m) => (c ? pass++ : (fail++, console.log("  ✗ " + m)));

ok(sandbox.ZM_RANKINGS && sandbox.ZM_RANKINGS.length >= 30, "zm-data defined ZM_RANKINGS in scope");
ok(typeof sandbox.ZMResolver === "object", "resolver defined ZMResolver in scope");
ok(typeof sandbox.ZMResolver.resolveItems === "function", "ZMResolver.resolveItems is a function");
ok(typeof sandbox.require === "undefined", "no require in scope (true Zotero-like sandbox)");
ok(typeof sandbox.module === "undefined", "no module in scope");

const row = sandbox.ZMResolver.lookupRanking("NeurIPS");
ok(row && row.canonical === "NeurIPS" && row.core === "A*", "lookupRanking wired to ZM_RANKINGS from zm-data");

// end-to-end resolve in the simulated scope, with a fake injected request
const fakeRequest = async (method, url, opts) => {
  if (url.includes("/paper/batch")) {
    const ids = JSON.parse(opts.body).ids; // ["ARXIV:2106.09685"]
    const data = ids.map(() => ({
      publicationVenue: { name: "International Conference on Learning Representations", type: "conference" },
      year: 2021,
      citationCount: 100,
      externalIds: {},
    }));
    return { status: 200, data };
  }
  return { status: 404, data: null };
};

const items = [{ key: "K", version: 1, data: { title: "Some ICLR Paper", archiveID: "arXiv:2106.09685", itemType: "preprint", creators: [], extra: "", tags: [] } }];
const [res] = await sandbox.ZMResolver.resolveItems(items, { request: fakeRequest, today: "2026-06-02" });
ok(res.canonical === "ICLR", "scope resolve -> ICLR");
ok(res.core_tier === "A*", "scope resolve -> A* tier");
ok(res.target_item_type === "conferencePaper", "scope resolve -> conferencePaper");
ok(res.fields.proceedingsTitle === "International Conference on Learning Representations", "scope resolve -> proceedingsTitle written");

console.log(`\nscope: ${pass} passed, ${fail} failed`);
if (fail) process.exit(1);
