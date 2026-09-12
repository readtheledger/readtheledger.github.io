# Changelog

All notable changes to The Ledger. Dates are UTC.

## Unreleased

### Editorial design — pictures, hierarchy and the phone page

The first design release: an editorial feel on a phone — expressive
headlines, a relevant original picture on every piece, clear attribution and
a visible hierarchy — with The Ledger's identity, warm paper and typefaces
unchanged. `docs/design/README.md` has the decisions, the contract and the
evidence.

- **A piece's own picture, rendered once.** `media.js` is the single contract
  and renderer for the optional `image` on a piece in `content.js`, run by the
  build for the static page and loaded by the app for the reader, so both
  produce the same figure and the browser fetches it once. The static copy is
  kept (hidden) until the reader's picture has loaded, so the handover does
  not repeat the request. The build refuses a piece whose picture fails the
  contract; the app renders such a piece text-led.
- **Caption, credit and disclosure are three things.** The caption is the
  editorial line and adds no factual claim; the credit names the maker; a
  picture a model generated carries a visible **AI-generated illustration**
  label and IPTC's `trainedAlgorithmicMedia` source type in the structured
  data. The story's production label is unrelated and unchanged.
- **Eight illustrations, full 3:2 at every size, no crops.** Web derivatives
  (480, 768 and 1200 px WebP with a 1200 px JPEG fallback) are made by
  `make_derivatives.py` from masters that stay outside the repository; each
  `assets/editorial/<id>/manifest.json` records the master's hash, the prompt,
  the method and the date. `sizes` reflect each placement's rendered width.
- **The article page** reads kicker, headline, deck, picture with caption and
  credit, byline and date, body. Headline 30–34 px on a phone, deck 18–19 px,
  body 20 px, all scaling with the reader's text-size setting; the hero bleeds
  to the viewport edge on a phone. The weekly feature uses the italic display
  face and keeps the drop cap; news reports open with an ordinary paragraph.
- **The front page keeps its pace and its order.** The lead carries its
  picture above the words; the two stories after it a 112 px thumbnail with
  the summary and meta below at full width; the rows after are text-led; the
  weekly feature carries its picture above an italic headline. Section pages
  follow the same rule. No story moved.
- The worker caches editorial pictures in a bounded cache of their own (40 at
  most, oldest out), never precached, so offline text never depends on them.
  The cache is scoped to the build, and the build stamp now covers the
  pictures' bytes, so a replaced picture reaches installed readers with the
  next build and the old cache is dropped; the write is attached to the fetch
  event so a stopped worker cannot lose it.
- The archive label (*From the archive*, on a news story more than a week old)
  is written by the build on the static pages too, so the static story and
  the reader agree; analysis and deep work carry their date only, as before.
- On a phone a front-page summary shows four lines on the lead and three on a
  supporting story, clipped; the article's own deck is whole. From 820 px the
  lead's picture sits beside its words so the headline is on the first screen.
- `qa_media.py`: 39 checks, including the text-led state from a fixture with
  one piece's picture removed (a second build, served on its own port, so the
  production pace is checked on the publication as it is), one server fetch of
  the hero across the handover with pictures served cacheable as Pages serves
  them, the worker's cache bound and its refresh on a replaced picture, lazy
  pictures loading on scroll, the archive label on both pages, the summary
  clamps, the Listen dock's space, Back and Forward from a direct story load,
  and no overflow from 320 to 1440 px.

### Search — what a crawler is served, and what it is told

Audited against Google Search Central's current guidance (the audit, with
before-and-after evidence, is `docs/seo/README.md`). Nothing about the
publication's identity, dates or labels changed; what changed is what a page
says about itself.

- **Nothing is blocked in `robots.txt` any more.** The app-only views
  (`/?view=newsstand`, `/?view=saved`, `?q=`) were disallowed there and marked
  `noindex` by the app at the same time — a contradiction, since a crawler that
  may not fetch a page cannot read its `noindex`, and Google says a blocked
  address can still be indexed by its URL alone. They are now `noindex` with a
  canonical of their own (a `noindex` page must not name another page as
  canonical), and `robots.txt` allows everything. A section with no stories yet
  is served and linked but written `noindex,follow` by the build until it has one;
  the app keeps whatever value the build wrote.
- **Every page opens with one `h1`** — the site's title on the front page (for
  readers of the structure; the wordmark is the visible one), the section's name
  with its count on a section page, the headline on a story — and the headings
  under it are in order: the sources box, the notices and the context box are
  `h2`. A skip link is the first thing in the body.
- **The About page has an address: `/about/`.** Its text moved to `about.js`,
  shared by the app (the card at the foot of the front page, the menu's About
  link, the reader) and the build (a static page with `AboutPage` structured
  data). It says how pieces are labelled — as the intended editorial standard,
  since the published pieces carry the default label and predate any kept
  review record — what the Newsstand is (a half-hour target that scheduled
  runs have missed by hours, with the real gathering time shown), where
  corrections go (an issue on the public repository), and the destinations
  the app actually requests (GoatCounter, Google Fonts, the feed relays as a
  fallback, publishers' image hosts, and OpenAI — with the locally stored key —
  only when the optional authenticated speech is used). It names no person,
  because the publication has not stated one, and still carries no date.
- **Structured data:** `BreadcrumbList` on every section, story and About page
  (Home › Section › Story); `Organization` on the front page with the logo and
  the repository as `sameAs`; a section's `CollectionPage` lists its pieces.
  `NewsArticle` no longer names the site icon as its `image`: Google's Article
  guidance asks for an image of the article, not a logo, and requires no
  properties, so a piece without an image of its own carries none. A piece may
  declare `image: {u, alt, w, h, caption}` in `content.js`; the build validates
  it (https, alt text, size; the icon is refused), writes it as `ImageObject`,
  shows it on the static page and in the reader, and uses it for the sharing
  preview (otherwise the preview stays the icon). `dateModified` reads an
  article's `updated` field when one is set (the build refuses one earlier
  than `date`).
- **Titles and descriptions say what is on the page.** The front page's
  description names the desks and the sourcing rule; a section's gives its
  count and latest piece; an empty section's says it is empty.
- **Real links between pages.** A story page links to four other pieces (the
  same desk first) under *More from The Ledger*, and the section navigation on
  every static page ends with About.
- **Sitemaps and a feed.** `sitemap.xml` includes `/about/` (no `lastmod`, since
  it has no date). `sitemap-news.xml` lists only what was published in the last
  48 hours — what Google reads a news sitemap for — and is empty otherwise; an
  archive does not qualify, and the build does not pretend it does. `feed.xml`
  is an Atom feed of The Ledger's own pieces in full, linked from every page.
- **Loading and accessibility.** The Google Fonts stylesheet no longer blocks
  the first paint (text shows in the fallback face and swaps) and asks only for
  the weights the stylesheet uses; the teal badge text and a read story's
  dimmed standfirst now meet 4.5:1 contrast.
- `qa_seo.py`: 45 checks on all of the above, from a fixture edition with one
  piece inside the 48-hour window and four desks with nothing yet.

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
  `/?view=saved`, `?q=term`), titled to match and marked `noindex` (the
  `robots.txt` disallow that went with it was removed in the search pass
  above); every topic is an ordinary link. A Newsstand preview keeps
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
