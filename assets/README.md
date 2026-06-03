# assets/

Static media referenced by the project README. The current set are **real screen captures
of the native Zotero plugin** (no synthetic illustration).

## Current (plugin)

- **`plugin-story.webp`** (EN) / **`plugin-story-zh.webp`** (中文) — the README hero: the
  three shots below composited into one **before → review → after** narrative, styled to match
  `social-card.png` (lime accent, dark gradient, flow chips). `README.md` uses the EN one,
  `README_zh.md` the 中文 one.
- **`library-before.png`** — a **real** Zotero library: arXiv preprints with the Publication,
  IF, easyScholar CCF and Citations columns blank (the "proof" before-state).
- **`library-after.png`** — the **same** items after **Resolve venue → Write selected**:
  Publication filled, `CCF A` / `CCF B` tags, and citation counts now showing. Two rows stay
  `preprint` (honest abstention: no recognized venue).
- **`plugin-review.png`** (EN) / **`plugin-review-zh.png`** (中文) — a **real** shot of the
  plugin's review dialog: every item, resolved venue + tier + citations, the exact fields to
  write, and low-confidence rows left unchecked.
- **`social-card.png`** — 1280×640 GitHub Social-preview card (gitignored; uploaded via repo
  Settings, not referenced in the README).

The three input PNGs are literal screenshots taken in Zotero 7. The `plugin-story*` composite
is an HTML layout, `../out/build_plugin_story.html`: open it in a browser at `?lang=en` (or
`?lang=zh`), size the viewport to 1200px wide, full-page-screenshot the `#card`, and save as
WebP. To refresh after re-capturing the screenshots, just drop the new PNGs in here and
re-render.

> Note: the `library-*` screenshots show Zotero's English column headers. The 中文 story reuses
> them with Chinese captions + the Chinese review dialog; re-capture the library in a Chinese
> Zotero UI if a fully-localized hero is wanted.

The legacy CLI/web-era assets (`demo*.gif`, `zotero-story*.webp`, `zotero-review.webp`,
`zotero-before/after.png`) were removed in the plugin rewrite (2026-06-04).
