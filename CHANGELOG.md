# Changelog

All notable changes to The Ledger. Dates are UTC.

## Unreleased

### Package 1 — freshness, topics, labels, navigation, sharing

#### Freshness you can trust
- Publication times come from the content, never from the visitor's clock or a
  refresh: the masthead's edition line is the newest date in `content.js`
  ("Latest edition 17 August 2026"), written by the build so it reads without
  JavaScript, and an item whose date is missing or does not parse says "date
  unknown" rather than "just now". The About page leaves the chronology — it
  is a labelled card at the foot of the front page with no date at all.
- A news story more than a week old is labelled **From the archive** on its card
  and in the reader; analysis and deep work are not news and are not expired by
  age. Dates and links are unchanged.
- The Newsstand says when it was actually gathered and how long ago, on the
  view itself, in the masthead line and in Settings; an edition without a
  usable time says "unknown". The half-hour schedule is described as a target.
- A refresh ends in one of three messages: a newer edition loaded, no newer
  edition, or the edition could not be reached and the previous one is kept
  with its true time. The previous edition's time travels with the offline copy.
  Gathering the Newsstand is never presented as new reporting.

#### Topics filed by subject
- `topics.js` files a Newsstand story by its actual subject — headline first,
  then the summary — with the publisher's category as supporting evidence and
  the economic case as the test. Political and human-interest stories carried
  by a business desk stay in the Newsstand under no topic ("General") instead of
  filling Companies. A source can be marked `fixed` in `sources.js` (its
  category is the verdict), and a headline-pattern override table files
  recurring formats. The gatherer writes the section, the confidence and the
  reason into the edition; the app files the same way when it has to gather in
  the browser. Rights, attribution, dates and wire origins are untouched.
- `eval_topics.mjs` scores the classifier against an 86-story sample from 26
  publishers (`docs/package-1/topic-sample.json`); the result and the labels'
  provenance are in `docs/package-1/classification-evaluation.md`.

#### Honest labels
- The desk's standing notes are now labelled **Background** wherever they
  appear — reader, Copy and Listen — with a signature that says they are a
  general note, not a reading of the article. **Why it matters** is reserved
  for a reviewed, story-specific note in `context.js`, with its sources and
  reviewer, and is empty until an editor writes one. Nothing is generated.

#### Navigation on a phone
- A compact masthead: the wordmark (a link home, on one line) and two labelled
  buttons, **Search** and **Menu**. The menu lists every topic as a link and
  groups the secondary actions: Saved, Dark mode, Check Newsstand, Settings,
  Reload app. The topic strip stays, with a fade and chevron while
  there is more to the right. The lead headline is a size that leaves the next
  story visible. Every view opens with a heading and a line about its state
  (Newsstand, Saved, Search, each section). Reader actions carry visible
  labels. Checked at 360, 390, 768 and 1440 px in headless Chromium.

#### Predictable navigation and sharing
- Newsstand, Saved and search are restorable addresses (`/?view=newsstand`,
  `/?view=saved`, `?q=term`), titled to match, marked `noindex` and disallowed
  in `robots.txt`; every topic is an ordinary link. A Newsstand preview keeps
  the address it was opened from, offers **Read the original** and
  **Share original**, and never gets a Ledger address of its own.
- Share reports its outcome in words — completed, cancelled, or copied instead
  when the share sheet is unavailable — and never claims a post was made.
  `docs/package-1/navigation-behaviour.md` is the documented contract.

### Added
- **The Newsstand is gathered by the build.** `fetch_feeds.mjs` reads every
  feed in `sources.js` and writes `data/feed.json` — the items, the time they
  were gathered and the state of every source — which the app loads with one
  request instead of twenty-nine through public relays. The Pages workflow
  gathers on every push and every half hour on a schedule (a target, not a
  promise), and can be run by hand. A feed that does not answer keeps its items
  from the live edition, marked as kept from an earlier gathering with their
  real time; the Newsstand and Settings show when the Newsstand was actually
  gathered. Items are validated on the way in (absolute link, parseable
  non-future date, title) and dropped with a counted reason otherwise;
  duplicates are removed by link and then title; a wire story keeps its origin
  (Reuters, AP, AFP, PA Media) whichever desk carried it.
- `sources.js` holds the feed list for the app and the gatherer, with an
  explicit `rights` value per source ("summary" or "full"); the gatherer refuses
  a source with no rights value, or "full" without a licence, and ships only an
  excerpt and a word count for a "summary" source.
- `qa_feed.py`: 21 checks on the gatherer against synthetic feeds; `qa_pages.py`
  now also checks the app's reading of a gathered edition and the worker's
  caching of it.

- **Production labels, per piece.** An article in `content.js` may carry
  `produced: "reported"` (the default) or `"assisted"`; the attribution line
  under it — in the reader and on the static page — says which, and the build
  refuses any other value. `REVIEW.md` sets out the review loop (fetch → draft →
  check claims against sources → approve → publish) and the per-edition
  checklist; `drafts/` holds pieces waiting for it; `docs/briefing-budget.md`
  is the budget the Daily Briefing is gated on, for the owner to approve.

### Changed
- The service worker serves `/data/` network first, so a fresh gathering is
  seen on the next launch and the cached copy answers only when the network is
  gone. `sources.js` is precached with the shell.
- If the gathered file cannot be read the app gathers in the browser through the
  relays as before, so nothing is lost while the scheduled gathering settles in.

## 2026-09-08

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
  fails if any file a page references is missing from the output. While the
  repository's Pages source is still GitHub's built-in branch build (the job's
  token is not allowed to change it), the workflow waits for that build of the
  same commit to finish before it deploys, so the pages this workflow built are
  the ones that are live; once the source is set to GitHub Actions the wait is
  skipped.

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
