/**
 * arxiv-marker bootstrap. Structure mirrors Zotero's Make-It-Red example and the
 * Citation Tally plugin (verified loading on the target Zotero 9.x): register a chrome
 * content path from manifest.json, load the plugin scripts into a shared scope via
 * Services.scriptloader.loadSubScript, and expose hooks on Zotero.ZoteroMarker.
 *
 * Load ORDER matters: zm-data.js (defines ZM_RANKINGS / ZM_OVERRIDES as scope vars) ->
 * resolver.js (reads them, defines ZMResolver) -> arxiv-marker.js (uses ZMResolver).
 */

var chromeHandle;

function install() {}

async function startup({ id, version, rootURI }, reason) {
  await Zotero.initializationPromise;

  const aomStartup = Components.classes["@mozilla.org/addons/addon-manager-startup;1"].getService(
    Components.interfaces.amIAddonManagerStartup
  );
  const manifestURI = Services.io.newURI(rootURI + "manifest.json");
  chromeHandle = aomStartup.registerChrome(manifestURI, [["content", "zoteromarker", rootURI + "content/"]]);

  const ctx = { rootURI };
  ctx._globalThis = ctx;
  // charset "UTF-8" is explicit so the bilingual (Chinese) UI strings load intact.
  Services.scriptloader.loadSubScript(`${rootURI}content/scripts/zm-data.js`, ctx, "UTF-8");
  Services.scriptloader.loadSubScript(`${rootURI}content/scripts/resolver.js`, ctx, "UTF-8");
  Services.scriptloader.loadSubScript(`${rootURI}content/scripts/arxiv-marker.js`, ctx, "UTF-8");

  Zotero.ZoteroMarker.rootURI = rootURI;
  Zotero.ZoteroMarker.id = id;
  Zotero.ZoteroMarker.version = version;
  await Zotero.ZoteroMarker.hooks.onStartup();
}

async function onMainWindowLoad({ window }, reason) {
  await Zotero.ZoteroMarker?.hooks.onMainWindowLoad(window);
}

async function onMainWindowUnload({ window }, reason) {
  await Zotero.ZoteroMarker?.hooks.onMainWindowUnload(window);
}

async function shutdown({ id, version, rootURI }, reason) {
  if (reason === APP_SHUTDOWN) return;
  await Zotero.ZoteroMarker?.hooks.onShutdown();
  if (chromeHandle) {
    chromeHandle.destruct();
    chromeHandle = null;
  }
}

function uninstall() {}
