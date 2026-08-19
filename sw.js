/* The Ledger — offline shell.
   Caches the app itself and the last pages you opened, so a dropped signal
   doesn't cost you your reading. Feeds and audio are cached separately
   (localStorage / IndexedDB) by the app. */

const VERSION = "3";
const SHELL = "ledger-shell-v" + VERSION;
const RUNTIME = "ledger-runtime-v" + VERSION;
const FILES = [
  "./",
  "./index.html",
  "./content.js",
  "./manifest.webmanifest",
  "./icon-192.png",
  "./icon-512.png",
  "./icon-180.png"
];

/* How long a launch waits for a fresh copy of the app before falling back to the
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

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys()
      .then(ks => Promise.all(ks.filter(k => k !== SHELL && k !== RUNTIME).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

/* The whole app is index.html, so a cache-first shell means a deploy never reaches
   anyone who has already installed it. Navigations go to the network first and only
   fall back to the cached copy when the network is slow or gone — an update lands on
   the next launch, offline still works, and no cache name has to be bumped by hand. */
async function navigate(req) {
  const cache = await caches.open(SHELL);
  try {
    const ctl = new AbortController();
    const timer = setTimeout(() => ctl.abort(), NAV_TIMEOUT);
    let res;
    try { res = await fetch(req, {signal:ctl.signal, cache:"no-cache"}); }
    finally { clearTimeout(timer); }
    if (!res || !res.ok) throw new Error("HTTP " + (res && res.status));
    cache.put("./index.html", res.clone());
    return res;
  } catch (e) {
    return (await cache.match("./index.html")) || (await cache.match("./")) || Response.error();
  }
}

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;

  const url = new URL(req.url);

  // never touch the speech API or the CORS relays — always live
  if (/api\.openai\.com|allorigins|corsproxy|codetabs/.test(url.hostname)) return;

  if (req.mode === "navigate") {
    e.respondWith(navigate(req));
    return;
  }

  // fonts, icons, same-origin assets: cache first, refresh in background
  e.respondWith(
    caches.match(req).then(hit => {
      const live = fetch(req).then(res => {
        if (res && res.ok && (url.origin === location.origin || /fonts\.(googleapis|gstatic)\.com/.test(url.hostname))) {
          caches.open(RUNTIME).then(c => c.put(req, res.clone()));
        }
        return res;
      }).catch(() => hit);
      return hit || live;
    })
  );
});
