# Contributing

Thanks for your interest! This is a small, deterministic tool — contributions that keep it
simple and well-tested are very welcome.

## Dev setup

```bash
uv sync                 # deps + dev tools (pytest, ruff, fastapi for the web tests)
uv run pytest           # full suite — network is mocked, no Zotero/S2 needed
uv run ruff check .     # lint
```

## Guidelines

- **Keep the deterministic-first design.** Prefer structured sources (Semantic Scholar,
  DBLP) over guesses; the LLM path is a last-resort stub for a reason.
- **Writes to Zotero must stay idempotent and reversible-by-review.** Tool-managed `Extra`
  lines are rewritten, never duplicated; nothing is written without an explicit pick.
- **Add tests for new behavior**, and mock the network — the suite must never hit a live API.
- **Run `ruff check` and `pytest` before opening a PR.** CI runs both on Python 3.10–3.13.
- **The ranking table is data, not code.** PRs extending `data/venue_rankings.csv` are
  welcome — please note the CORE/CCF edition you're following.

## Reporting issues

Include the item's arXiv id, what venue/tier you expected, and what the tool resolved
(the `resolve` HTML console shows the evidence links it used).
