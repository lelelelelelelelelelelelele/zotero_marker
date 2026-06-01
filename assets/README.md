# assets/

Static media referenced by the project README.

- **`demo.gif`** (English captions) — the before→after demo shown at the top of the README.
- **`demo_zh.gif`** (Chinese captions) — same animation for the 小红书 / 知乎 posts.
- **`zotero-before.png`** — a **real** Zotero screenshot: arXiv preprints with the
  easyScholar 影响因子/期刊标签 and Citation Tally 引用 columns blank. The authenticity
  ("proof") counterpart to the illustration GIF.
- **`zotero-review.webp`** — a **real** screenshot of the web review console: resolved
  venues (ICCV/CVPR/ECCV), citations, CORE tier, the exact **FIELDS TO WRITE**, and the
  6/8 selection (the two 0.60 workshop/WACV rows correctly unchecked = honest abstention).
  Embedded in the README "web UI" section, and reused as panel 02 of `zotero-story.webp`.
  Cropped to content + WebP q90 (~180 KB).
- **`zotero-after.png`** — the **same** items/columns/window after `write`: 出版物 (venue),
  期刊标签 (`CCF A`/`CCF B`), and 引用 (citation count) now filled — the blank→filled
  counterpart to `zotero-before.png` (影响因子 stays blank: conferences have no impact factor).
- **`zotero-story.webp`** / **`zotero-story-zh.webp`** — the three shots above composited
  into one **before → review → after** narrative; the README hero. English chrome →
  `zotero-story.webp` (used by `README.md`), Chinese chrome → `zotero-story-zh.webp` (used
  by `README_zh.md`). The embedded Zotero screenshots stay in the real (Chinese) UI either
  way. WebP keeps each ~340 KB at full resolution (vs ~3 MB PNG). Rebuild: open
  `../out/build_story.html?lang=en` (or `?lang=zh`), screenshot its `#card` at 1280px,
  save as WebP q90.

Both are **illustration animations**, built by `../out/build_demo.py` (Pillow) from the
**real** resolved values in `../out/resolutions.json` (real papers, real venues, real
Semantic Scholar citation counts — *Attention Is All You Need* 178,362, etc.). They are
stylised explainers, **not** literal screen captures, and say so in the footer.

To regenerate after editing the script:

```bash
python out/build_demo.py en   # -> assets/demo.gif
python out/build_demo.py zh   # -> assets/demo_zh.gif
```

**Optional upgrade:** for the launch you can replace `demo.gif` with a true screen
recording of real Zotero (the blank→lit contrast in the actual UI is the strongest
version). Follow [`../docs/DEMO_SCRIPT.md`](../docs/DEMO_SCRIPT.md) and overwrite
`demo.gif`. Keep it < 5 MB (12–15 fps, ~900 px wide); ScreenToGif handles this on export.
