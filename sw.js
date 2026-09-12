/* The Ledger — offline shell.
   Caches the app itself and the pages you have opened, so a dropped signal
   doesn't cost you your reading. Feeds and audio are cached separately
   (localStorage / IndexedDB) by the app.

   Every story and section has an address of its own, and each one is cached
   under that address. A page the server answers for — a story, a section, a
   real 404 — is always what the reader gets while the network is up; the cache
   only speaks when the network cannot. */

const VERSION = "4";
const BUILD = "dev";   // build.mjs stamps a hash of the app and the edition here,
                       // so a new article or a changed page installs a fresh shell
const SHELL   = "ledger-shell-v"   + VERSION + "-" + BUILD;
const RUNTIME = "ledger-runtime-v" + VERSION + "-" + BUILD;
const FILES = [
  "/",
  "/index.html",
  "/sources.js",
  "/topics.js",
  "/context.js",
  "/about.js",
  "/content.js",
  "/manifest.webmanifest",
  "/icon-192.png",
  "/icon-512.png",
  "/icon-180.png"
];

/* The addresses the app can render from content.js when a page has never been
   fetched: the front page, every story and every section that actually exists
   in this edition. build.mjs stamps the full list; offline, only these fall
   back to the shell, and an address that is not on it does not pretend to exist. */
const ROUTES = ["/", "/index.html"];

function appRoute(pathname) {
  return ROUTES.includes(pathname) || (!pathname.endsWith("/") && ROUTES.includes(pathname + "/"));
}

/* How long a launch waits for a fresh copy of the page before falling back to the
   cached one. Long enough for a slow train connection, short enough not to feel
   like a hang. */
const NAV_TIMEOUT = 3500;

self.addEventListener("install", e => {
  e.waitUntil(
    caches.open(SHELL)
      .then(c => Promise.allSettled(FILES.map(f => c.add(new Request(f, {cache:"reload"})))))
      .then(() => self.skipWaiting())
  );
});

/* Every earlier cache goes — including the v3 shell that kept a single index.html
   under a relative key — so an upgrade from the installed app starts clean. */
self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys()
      .then(ks => Promise.all(ks.filter(k => k !== SHELL && k !== RUNTIME).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

/* A page is cached by its path, never its query string, so /story/x/?utm=… and a
   cache-busting refresh both find the same copy. */
function pageKey(url) {
  return url.origin + url.pathname;
}

/* Network first: a deploy reaches an installed reader on the next launch, and a
   404 from the server stays a 404. The cache answers only when the network is
   slow or gone — first with the very page that was asked for, then, for an
   address on the build's route list, with the shell; for anything else, an
   honest 503, because a page that does not exist must not come back as the
   front page with a 200. */
async function navigate(req) {
  const url = new URL(req.url);
  const key = pageKey(url);
  const cache = await caches.open(SHELL);
  try {
    const ctl = new AbortController();
    const timer = setTimeout(() => ctl.abort(), NAV_TIMEOUT);
    let res;
    try { res = await fetch(req, {signal:ctl.signal, cache:"no-cache"}); }
    finally { clearTimeout(timer); }
    if (res.ok && !res.redirected && res.type === "basic") cache.put(key, res.clone());
    return res;                       // 200 cached and served; 404, 500, redirects served as they are
  } catch (e) {
    const own = await cache.match(key);
    if (own) return own;
    if (appRoute(url.pathname)) {
      const shell = (await cache.match("/index.html")) || (await cache.match("/"));
      if (shell) return shell;
    }
    return new Response(
      "<!doctype html><meta charset=\"utf-8\"><title>Offline — The Ledger</title>" +
      "<p style=\"font-family:Georgia,serif;padding:2em\">You're offline and this page hasn't been saved on this device.</p>",
      {status:503, headers:{"Content-Type":"text/html; charset=utf-8"}});
  }
}

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;

  const url = new URL(req.url);

  // never touch the speech API, the analytics ping or the CORS relays — always live
  if (/api\.openai\.com|goatcounter\.com|allorigins|corsproxy|codetabs/.test(url.hostname)) return;

  if (req.mode === "navigate") {
    e.respondWith(navigate(req));
    return;
  }

  // the gathered Newsstand is the edition of the moment: network first, so a
  // fresh gathering is seen on the next launch, and the cached copy only when
  // the network is gone
  if (url.origin === location.origin && url.pathname.startsWith("/data/")) {
    e.respondWith(
      fetch(req).then(res => {
        // clone before the page starts reading the body, or there is nothing left to keep
        if (res && res.ok) { const copy = res.clone(); caches.open(RUNTIME).then(c => c.put(req, copy)); }
        return res;
      }).catch(() => caches.match(req).then(hit => hit || Response.error()))
    );
    return;
  }

  // fonts, icons, same-origin assets: cache first, refresh in background
  e.respondWith(
    caches.match(req).then(hit => {
      const live = fetch(req).then(res => {
        if (res && res.ok && (url.origin === location.origin || /fonts\.(googleapis|gstatic)\.com/.test(url.hostname))) {
          const copy = res.clone();
          caches.open(RUNTIME).then(c => c.put(req, copy));
        }
        return res;
      }).catch(() => hit);
      return hit || live;
    })
  );
});
