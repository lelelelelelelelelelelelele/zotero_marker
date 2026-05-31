# zotero-marker

![python](https://img.shields.io/badge/python-3.10%2B-blue)
![license](https://img.shields.io/badge/license-MIT-green)
![lint](https://img.shields.io/badge/lint-ruff-261230)
![tests](https://img.shields.io/badge/tests-pytest-0a9edc)

Resolve the **real publication venue** of the arXiv preprints sitting in your Zotero
library, then write it back as proper metadata — so impact-factor / 分区 / CCF plugins
(easyScholar, [zotero-style](https://github.com/MuiseDestiny/zotero-style) / Ethereal
Style) and citation-count columns ([Citation Tally](https://github.com/daeh/zotero-citation-tally))
light up natively.

A `preprint` in Zotero has no venue field, so those plugins show nothing for it. They read
the **venue field** (`publicationTitle` for journals; `proceedingsTitle`/`conferenceName`
for conferences) and match easyScholar by venue name + DOI — they do **not** read tags. So
zotero-marker **converts the itemType** and fills the venue + identifiers, keeping the arXiv
id and citation count in `Extra`.

It is deliberately **deterministic-first**: venues are resolved for free via Semantic
Scholar (keyed on the arXiv id) and DBLP, with ~zero hallucination. An LLM + web-search
fallback is left as a stub (`resolvers.resolve_llm`) for the hard residual only.

> **Why not the existing arXiv plugins?** They merge on the *published DOI* the author
> registered on the arXiv page. NeurIPS / ICLR / older CVPR have **no Crossref DOI** (they
> live on proceedings sites / OpenReview), so DOI-first tools miss exactly the famous
> papers. Keying on the **arXiv id → Semantic Scholar** (which dedupes preprint + published
> into one record) fixes that.

## Install

Uses [uv](https://docs.astral.sh/uv/). Clone, then:

```bash
uv sync                       # creates .venv, installs deps (+ dev tools)
cp .env.example .env          # then edit (see below)
```

- **Zotero 7+ desktop must be running** — the tool talks to its local API at
  `localhost:23119`. Set `ZOTERO_LIBRARY_ID` in `.env` to your user/library id.
- A **Semantic Scholar API key** is optional but recommended (removes 429 rate limits):
  get one at <https://www.semanticscholar.org/product/api> and set `S2_API_KEY=...`.
- Writing back uses the **Zotero Web API** (the local API is read-only), so it needs a
  `ZOTERO_API_KEY` with write scope — create one at
  <https://www.zotero.org/settings/keys>.

## Use — CLI

**1. Resolve (dry-run, writes nothing to Zotero):**

```bash
uv run python run.py resolve                 # all preprints in the library
uv run python run.py resolve --limit 12      # first 12
uv run python run.py resolve --items GD5PM7VD,BW3RIHJ2   # specific items
```

This produces `out/resolutions.csv`, `out/resolutions.json`, and **`out/resolutions.html`** —
a self-contained review console: sortable/filterable table of every item, the exact field
changes that will be written, citations, and evidence links. Tick the rows you want and
click **复制选中的 keys**.

**2. Write (converts itemType + fills venue fields):**

```bash
uv run python run.py write                              # dry-run: prints every proposed change
uv run python run.py write --items GD5PM7VD,2I966U5R --yes   # write only the keys you picked
uv run python run.py write --threshold 0.9 --yes        # write everything above a confidence bar
```

Only items with a resolved venue and `confidence >= threshold` are written; `unknown` items
are never touched.

## Use — web UI (optional)

A browser front-end over the same pipeline (review → tick → write, no terminal):

```bash
uv sync --extra web
uv run python run.py web        # serves http://127.0.0.1:8000
```

Bound to `127.0.0.1` only; the write action needs `ZOTERO_API_KEY` and an explicit confirm.

## The payoff — what shows up in Zotero

After writing, your community plugins recognise the venue and citation count:

- **Venue / IF / 分区 / CCF** — via **easyScholar + zotero-style**. easyScholar matches by
  the venue string we wrote, so CCF-listed venues (NeurIPS, CVPR, …) get their tag, and
  journals get their impact factor.
- **Citation count column** — via **Citation Tally**. We write the citation line in its exact
  format `Citations: <N> (SemanticScholar) [date]`, and Semantic Scholar is on by default in
  its database order, so the count appears with no re-fetch.

### Honest limitations

- **Impact factor is journal-only** — conference papers (ICLR, NeurIPS) correctly show no IF.
- **ICLR's CCF tag may not appear** — CCF added ICLR only in its 2026 (7th) edition, which
  easyScholar's dataset still lags; add it via an easyScholar custom dataset if you need it.
- **arXiv-only / workshop papers stay `unknown`** — if a paper was never formally published
  (or only as a workshop paper), there's no venue to resolve, even with thousands of citations.

## How confidence is computed

Rule-based, **not** an LLM's self-reported number:

| confidence | meaning |
|---|---|
| 0.95 | ≥2 independent sources (S2 + DBLP) agree on a known venue |
| 0.85 | one source, venue recognized in the ranking table |
| 0.60 | a venue string was found, but it's not in the ranking table |
| 0.00 | no venue found → `acceptance=unknown` |

## Ranking table & overrides

`data/venue_rankings.csv` is an **editable starter** set (CORE A*/A/B/C) — extend it
freely. `data/overrides.csv` (optional, keyed by arXiv id) is the escape hatch for the long
tail the auto-resolver gets "technically right but not what you want" (e.g. a paper whose
record points at a later journal republication instead of the original conference). Overrides
always win and are labelled `source=override` in the report.

> Rankings disagree below the top tier and lag reality by years — treat any single tier as
> "source X says Y", not ground truth.

## FAQ

**Is it free?**
Yes. DBLP is free and needs no key; the Zotero local + Web APIs are free; a Semantic
Scholar key is optional (it only lifts rate limits). The tool has one runtime dependency
(`requests`).

**What is DBLP, and why use it alongside Semantic Scholar?**
[DBLP](https://dblp.org) is a free, open computer-science bibliography (maintained by
Schloss Dagstuhl). It has the best coverage of CS *conferences* — exactly where Crossref
and Semantic Scholar are weakest. zotero-marker uses it as a fallback: when S2 returns no
venue, or a later journal reprint, DBLP recovers the original conference by title + author
+ year (e.g. *Generative Adversarial Networks*: S2 says CACM, DBLP finds NeurIPS 2014).

**Does it only work on arXiv papers?**
It processes Zotero `preprint` items only — your already-published entries are never
touched. arXiv preprints get the full result (venue **and** citation count). A preprint
*without* an arXiv id can still get a venue via DBLP's title search, but no citation count
(citations come from Semantic Scholar, keyed on the arXiv id).

**Will it create duplicates or clobber my data?**
No. It never creates items — it edits existing ones in place. The `Extra` rewrite is
idempotent (it only ever rewrites lines this tool authored, so re-runs don't pile up), and
each write is guarded by the item's resolve-time version (a 412 aborts rather than
overwrite your newer edits). Nothing is written until you review and pick it. Separately,
`resolve` *flags* duplicate arXiv ids already in your library so you can merge them.

**What do the confidence numbers mean?**

| confidence | meaning | written by default? |
|---|---|---|
| 0.95 | two independent sources (S2 + DBLP) agree on a known venue | ✓ |
| 0.85 | one source, venue recognized in the ranking table | ✓ |
| 0.60 | a venue string was found, but it isn't in the ranking table | ✗ |
| 0.00 | no venue found → `unknown` | ✗ |

`write` only applies items at or above `--threshold` (default `0.85`). Lower it
(`--threshold 0.6`) to include shakier matches, or raise it to be stricter. The score is a
rule (how many databases agree), not a model's self-reported guess.

**Why does a conference paper show no impact factor?**
Impact factor is a journal-only metric (JCR). Conferences are ranked by CORE / CCF, not IF
— so a blank IF on a conference paper is correct, not a bug.

**Why doesn't my ICLR paper get a CCF tag?**
CCF only added ICLR in its 2026 (7th) edition, which easyScholar's dataset still lags.
That's a data-source delay on easyScholar's side, not something this tool controls.

**Why is a paper with thousands of citations marked `unknown`?**
Because it was never formally published — arXiv-only or workshop-only papers (e.g. *Scaling
Laws for Neural Language Models*) have no venue to resolve, however many citations they have.

**Why a CLI and not a Zotero plugin?**
Zotero now ships a major version roughly every 8 weeks, and plugins break on each bump
(JSM→ESM, bootstrap changes, `strict_max_version`). The resolution logic is far more
durable as a Python CLI on stable APIs. A thin Zotero plugin that *calls* this resolver is
a sensible later layer (see the Roadmap) — but the brain stays decoupled from Zotero's churn.

## Development

```bash
uv run pytest              # full suite (network is mocked; no Zotero/S2 needed)
uv run ruff check .        # lint
```

CI (GitHub Actions) runs ruff + pytest on Python 3.10–3.13. See
[CONTRIBUTING.md](CONTRIBUTING.md).

## Roadmap

The deterministic cascade handles the bulk for free, with ~zero hallucination. Planned
next steps:

- **Citation refresh (`refresh` mode)** — the tool really has two jobs: *preprint match*
  (incremental — `resolve` / `write` resolve the as-yet-unmatched preprints) and *citation
  update* (a full sweep that re-fetches citation counts for already-matched items by arXiv id
  and rewrites only the `Citations:` line + date, leaving venue/type untouched). The second
  is **not built yet** — once an item is written it leaves the preprint scan, so its count
  freezes; the dated `Extra` stamp is the hook a `refresh` mode would use.
- **LLM + web-search fallback** for the residual that Semantic Scholar and DBLP both
  miss — fuse OpenReview / CVF Open Access / author pages to read "Accepted at NeurIPS
  2024"-style evidence, with forced abstention and snippet-constrained evidence URLs.
- **Expose the resolver as an MCP server** so other clients (editors, agents) can use it.
- **A thin Zotero plugin** that calls the resolver from a right-click menu.

## Layout

```
run.py                      entry point: python run.py resolve|write|web
pyproject.toml              uv project + ruff/pytest config
zotero_marker/
  config.py                 .env loading + settings
  util.py                   arXiv-id extraction + title matching
  resolvers.py              Semantic Scholar (batch by arXiv id) + DBLP + LLM stub
  rankings.py               venue string -> canonical + CORE tier
  overrides.py              manual per-arXiv overrides
  pipeline.py               resolve cascade, venue choice, confidence, tags, dup detection
  proposal.py               itemType + field write-back (idempotent Extra)
  report.py                 CSV + JSON + HTML review console
  cli.py                    resolve / write / web commands
  web.py                    optional FastAPI web UI (the `web` extra)
  zotero_api.py             local (read) + web (write) Zotero client
data/
  venue_rankings.csv        editable CORE ranking table
  overrides.csv             optional manual overrides
tests/                      pytest suite (network mocked)
```

## License

[MIT](LICENSE).
