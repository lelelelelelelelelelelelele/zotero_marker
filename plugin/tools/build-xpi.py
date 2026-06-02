"""Package the runtime files into build/arxiv-marker-<version>.xpi using Python's zipfile
(produces a clean, Firefox/Zotero-compatible zip: manifest.json at the root, forward-slash
entry paths, standard deflate). Dev-only dirs (tools/, test/, build/) are excluded.
Run from the plugin/ dir:  python tools/build-xpi.py
"""
import json
import zipfile
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent
manifest = json.loads((PLUGIN_DIR / "manifest.json").read_text(encoding="utf-8"))
version = manifest["version"]
build_dir = PLUGIN_DIR / "build"
build_dir.mkdir(exist_ok=True)
xpi = build_dir / f"arxiv-marker-{version}.xpi"
if xpi.exists():
    xpi.unlink()

# Runtime files: top-level entry points + everything under content/.
files: list[tuple[Path, str]] = []
for top in ("manifest.json", "bootstrap.js", "prefs.js"):
    p = PLUGIN_DIR / top
    if p.exists():
        files.append((p, top))
for p in sorted((PLUGIN_DIR / "content").rglob("*")):
    if p.is_file():
        files.append((p, p.relative_to(PLUGIN_DIR).as_posix()))

with zipfile.ZipFile(xpi, "w", zipfile.ZIP_DEFLATED) as z:
    for path, entry in files:
        z.write(path, entry)

print(f"built: {xpi}")
with zipfile.ZipFile(xpi) as z:
    for name in z.namelist():
        print(f"  {name}")
