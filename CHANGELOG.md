# Changelog

All notable changes are documented here. Format based on
[Keep a Changelog](https://keepachangelog.com/); versioning aims for
[SemVer](https://semver.org/).

## [Unreleased]

### Fixed
- ICCV items got no easyScholar CCF tag. Semantic Scholar returns the venue as
  `IEEE International Conference on Computer Vision`, but easyScholar's ICCV (CCF A) entry
  has no `IEEE` prefix — so the venue string written didn't match and the tag stayed blank
  (venue + citation count were unaffected). Added an optional `write_as` column to
  `data/venue_rankings.csv` that pins the exact easyScholar-matching string to write,
  decoupled from the lookup aliases; ICCV now writes `International Conference on Computer
  Vision`. CVPR/ECCV were already correct (S2 returns their prefix-less names).

## [0.1.0] — 2026-05-31

### Added
- Deterministic venue resolver: Semantic Scholar (batch by arXiv id) → DBLP (by title)
  cascade, with an LLM fallback left as a stub.
- CORE/CCF ranking lookup table (`data/venue_rankings.csv`) with alias + substring matching.
- Write-back proposal: `preprint` → `journalArticle`/`conferencePaper` plus
  venue / DOI / ISSN / journalAbbreviation / publisher, preserving the arXiv id and
  citation count in `Extra` (idempotent; Citation-Tally display format).
- Manual overrides (`data/overrides.csv`) keyed by arXiv id; always win, clearly labelled.
- Three review surfaces: CSV, JSON, and a self-contained HTML console.
- Optional local web UI (`web` extra, FastAPI): review + write from the browser.
- CLI: `resolve`, `write`, `web`, and `--version`.
- Duplicate-arXiv detection surfaced in the resolve summary.
- Test suite (pytest, network mocked), ruff lint config, GitHub Actions CI (3.10–3.13),
  MIT license, uv packaging.

### Fixed
- `_confidence` now returns 0.95 when ≥2 sources actually **agree** on a venue. The previous
  set-based `len(canons) >= 2` check only fired when sources *disagreed*, so the documented
  high-confidence tier was effectively unreachable.
