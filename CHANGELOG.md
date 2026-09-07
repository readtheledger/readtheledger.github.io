# Changelog

All notable changes to The Ledger. Dates are UTC.

## Unreleased

### Added
- **Every story has an address.** `build.mjs` writes a page for each Ledger
  article (`/story/<id>/`) and each editorial section (`/markets/`,
  `/central-banks/`, …): the app, with that page's title, description, canonical
  URL, Open Graph and Twitter Card metadata and `NewsArticle` structured data in
  its head, and a static copy of the content inside `<main>` so the story reads
  in full with JavaScript off. Article text and publication dates are carried
  through unchanged from `content.js`.
- Headlines on the front page and in sections are ordinary links to those pages;
  section tabs are links to the section pages (Newsstand and Saved stay buttons —
  they exist only inside the app). Opening a story updates the address bar; a
  refresh, browser back and forward, bookmarks and Escape all work from it.
- Share hands the system a Ledger story's own URL. A Newsstand item still shares
  the publisher's original.
- `sitemap.xml`, `robots.txt` and a real `404.html`.
- `qa_pages.py`: 75 checks covering the built pages with JavaScript off and on,
  the service worker, and an upgrade from the previously released worker.

### Changed
- **Service worker v4.** Pages are cached under their own addresses (query
  strings ignored). Navigations stay network-first; a 404 or any other answer
  from the server is passed through unchanged rather than replaced by the cached
  shell. Offline, a visited page is served from its own cached copy; a page the
  app can render itself — the front page, a section or a story that exists in
  this edition, from a route list the build stamps into the worker — falls back
  to the shell; anything else, including an unknown story or section, is an
  honest 503. The build stamps the worker with a hash of the app and the
  edition, so a new article installs a fresh shell. Upgrading from v3 removes
  the old caches.
- The Pages workflow's artifact check is `check_site.sh`, and `qa_pages.py` runs
  the same script on its own build (and on a copy with an unstamped worker,
  which it must reject).
- Asset references (`content.js`, `sw.js`, the manifest and icons) are rooted at
  `/`, so they resolve from every page; the manifest's `start_url` and `scope`
  are `/`. The pages are written for the root of a domain.
- The Pages workflow now runs `node build.mjs` and publishes `_site`; the build
  fails if any file a page references is missing from the output.

## 2026-08-19

### Fixed
- **The publication now actually deploys.** The Pages workflow assembled the site
  without `content.js` — the file that carries every Ledger article — so the live
  front page fell back to the built-in demo page alone. `content.js` is now copied
  into the artifact, and a new workflow step fails the build if any file referenced
  by `index.html`, `sw.js` or the manifest is missing from `_site`, so this class of
  bug cannot ship silently again.
- Playback-speed button label rendered `2.×` and `1.×` at whole-number rates; it now
  shows `2.0×` / `1.0×`.
- Pressing Escape in the reader now leaves through history exactly like the back
  button, so the reader's history entry no longer lingers after the panel closes.

### Improved
- **Keyboard accessibility:** article cards and the long-reads rail are focusable
  and open with Enter or Space; a visible `:focus-visible` outline was added; the
  active section tab is now marked with `aria-current="page"`; the search input
  gained an accessible label.
- The `theme-color` status-bar colour now follows the in-app light/dark toggle,
  not just the system preference.
- Added canonical URL and Open Graph / Twitter card metadata so shared links
  preview properly.
- Service worker cache version bumped to 3 so installed clients re-precache the
  full shell (including `content.js`).

## 2026-08-18

- First deployment of the site to https://readtheledger.github.io/ (mirror of the
  tested build, commit `d733a6f`).
