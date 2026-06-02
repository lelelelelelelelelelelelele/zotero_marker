# Packages the runtime files into build/arxiv-marker-<version>.xpi (a ZIP with the
# manifest at the root and forward-slash entry paths, as Zotero/Gecko require). Dev-only
# dirs (tools/, test/, build/, node_modules/) are excluded.
# Run from the plugin/ dir:  powershell -ExecutionPolicy Bypass -File tools/build-xpi.ps1
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$pluginDir = Split-Path -Parent $PSScriptRoot   # tools/ -> plugin/
$manifest = Get-Content (Join-Path $pluginDir "manifest.json") -Raw | ConvertFrom-Json
$version = $manifest.version
$buildDir = Join-Path $pluginDir "build"
if (-not (Test-Path $buildDir)) { New-Item -ItemType Directory -Path $buildDir | Out-Null }
$xpi = Join-Path $buildDir "arxiv-marker-$version.xpi"
if (Test-Path $xpi) { Remove-Item $xpi -Force }

# Runtime files: top-level entry points + everything under content/.
$files = @()
foreach ($f in @("manifest.json", "bootstrap.js", "prefs.js")) {
  $p = Join-Path $pluginDir $f
  if (Test-Path $p) { $files += [PSCustomObject]@{ Path = $p; Entry = $f } }
}
$contentDir = Join-Path $pluginDir "content"
Get-ChildItem $contentDir -Recurse -File | ForEach-Object {
  $rel = $_.FullName.Substring($pluginDir.Length + 1) -replace '\\', '/'
  $files += [PSCustomObject]@{ Path = $_.FullName; Entry = $rel }
}

$zip = [System.IO.Compression.ZipFile]::Open($xpi, [System.IO.Compression.ZipArchiveMode]::Create)
try {
  foreach ($item in $files) {
    [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
      $zip, $item.Path, $item.Entry, [System.IO.Compression.CompressionLevel]::Optimal) | Out-Null
  }
} finally { $zip.Dispose() }

Write-Output "built: $xpi"
Write-Output "entries:"
$z = [System.IO.Compression.ZipFile]::OpenRead($xpi)
try { $z.Entries | ForEach-Object { Write-Output ("  " + $_.FullName) } } finally { $z.Dispose() }
