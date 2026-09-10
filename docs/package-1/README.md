# Package 1 — freshness, topics, labels, mobile navigation, sharing

Roadmap package 1 for The Ledger, delivered as a reviewable pull request.
Nothing here is merged or published; the production step is a separate approval.

## What changed, in one screen

| Area | Before | After |
|---|---|---|
| Masthead date | Today's date from the visitor's clock | *Latest edition 17 August 2026* — the newest date in `content.js`, written by the build; plus *Newsstand gathered 10 Sep, 01:25 (3 hours ago)* once known |
| About page | "just now", inside the news chronology | A labelled *About* card at the foot of the front page, no date; the reader says it is part of the app |
| Older news | Bare relative date | *From the archive · Markets* on cards and in the reader for news past a week; analysis and deep work keep their date and are not expired |
| Missing/invalid dates | Fell back to "now" | *date unknown* / *Publication date unknown*; sorted last; never scored as fresh |
| Refresh | "N stories · gathered …" or a browser re-gather | Three outcomes in words: newer edition loaded / no newer edition / couldn't reach — previous edition kept with its true time. Offline copy carries the edition's time |
| Filing | Feed category unless ≥2 keyword hits | `topics.js`: headline-weighted subject scoring, economic-relevance gate, publisher category as evidence, General fallback, `fixed` sources, headline overrides; the edition carries section + confidence + reason + desk |
| Context box | Every Newsstand item: "Why it matters" from a per-desk stock note | *Background* with an honest signature; *Why it matters* only for a reviewed note in `context.js` (with sources and reviewer). Reader, Copy and Listen agree |
| Masthead (phone) | Wordmark + 5 icon buttons; logo wrapped at 390 | Wordmark (one line, link home) + labelled **Search** and **Menu**; secondary actions grouped in the menu |
| Topic strip | Clipped, no cue | Fade + chevron while more is to the right; current topic scrolled into view |
| Views | No headings; Newsstand/Saved unaddressed; tabs were buttons | Each view has an h1 + state line; `/?view=newsstand`, `/?view=saved`, `?q=term` restore; titles match; `noindex` + `robots.txt` disallow; every topic is a link |
| Reader actions | Icon-only | Icon + visible label; *Share original* / *Read the original* for Newsstand previews |
| Share | Silent on success/cancel | Completed / cancelled / copied-instead reported in the live-region toast; never claims a post |

Full detail: `CHANGELOG.md` (Unreleased → Package 1), `navigation-behaviour.md`
(the documented contract), `classification-evaluation.md` (the sample and score).

## Files

- `topics.js` (new) — the shared classifier; `eval_topics.mjs` (new) — its evaluation; `topic-sample.json` — the labelled sample.
- `context.js` (new) — reviewed per-story context; empty by default.
- `index.html` — freshness model, labels, masthead/menu, view headings, restorable state, share feedback.
- `fetch_feeds.mjs` — files each item at gather time (also items kept from older editions); `sources.js` — `fixed` flag on 8 single-subject feeds.
- `build.mjs` — copies the new files, writes the edition line for JS-off readers, `robots.txt` disallows the app-only addresses; `sw.js`, `check_site.sh` — precache/verify the new files.
- `qa_package1.py` (new suite); `qa.py`, `qa_pages.py`, `qa_feed.py` updated for the menu, topic links, wording and the new edition fields.

## Verification

### Checks I ran (headless Chromium in the build container; a simulation, not a phone)

| Check | Result | Where |
|---|---|---|
| `qa_package1.py` — package 1 at 360/390/768/1440 (freshness, filing, labels, masthead/menu, restorable views, share outcomes, refresh outcomes) | **114/114** | new suite |
| Smoke run against the **real edition** of 10 Sep (347 items) at the same four widths, incl. share success/cancel/fallback and search/Saved restore | **89/89** | `docs/package-1/shots/` came from this run |
| `qa.py` — layout, touch targets, copy, listen fallback, dark mode, settings, manifest, worker, sanitising, bookmarks, cache, editorial mix, rights model | **54/54** (was 53; one check added for the Background label in Copy) | existing suite, updated |
| `qa_pages.py` — built pages JS-off/on, metadata, dates, links, sharing, bookmarks, audio, worker caching, 404, offline, upgrade from v3 | **90/90** | existing suite, updated for the menu and topic links |
| `qa_feed.py` — gatherer against synthetic feeds, now incl. `section`/`topic`/`desk` and filing of items kept from older editions | **26/26** (was 21) | existing suite, extended |
| `eval_topics.mjs` — 86-story labelled sample, 26 publishers | **86/86 with excerpts; 83/86 (96.5%) headlines only** | `classification-evaluation.md` |
| `check_site.sh` on the build | ok | run by `qa_pages.py` and the workflow |

Regression coverage the package asked for: story links (`qa_pages`: headline links, direct landing, reload, back/forward), search (`qa_package1`: heading, address, restore; `qa.py`: empty state), bookmarks (`qa_pages`: from a story address, Saved list; `qa.py`: durability), dark mode (`qa.py`; `qa_package1` screenshot), reader controls (`qa.py`: copy, listen fallback, rate, progress; `qa_pages`: audio and copy from a story address), failed-feed/freshness (`qa_package1`: 503 from the server keeps the edition with its time; no-newer and newer outcomes; unknown date; edition line; archive label; About card), keyboard/focus (`qa_package1`: menu takes focus and returns it on Escape; Escape closes a story through history; `qa.py`: Enter opens a focused card), share paths (`qa_package1` and the smoke run: completed / cancelled / copied-instead for both a Ledger story and a Newsstand preview).

Screenshots in `shots/` were captured by the smoke run against the real edition
of 10 September (recovered from the live site; not committed), at 360, 390, 768
and 1440 px: front page, menu, Newsstand, a Newsstand preview in the reader, a
Ledger story in the reader, and the front page in dark mode at 390.

### What I could not do here

- **No real phone.** All width checks are Chromium viewport simulations with
  touch and mobile emulation. Safari on iOS, Add-to-Home-Screen, the real share
  sheet and lock-screen audio were not exercised.
- **No live feeds.** The sandbox's egress policy blocks the publisher hosts, so
  `fetch_feeds.mjs` was exercised only by `qa_feed.py`'s synthetic feeds; the
  classifier was evaluated against the real edition of 10 September.
- **`qa_live.py`** (real feed fixtures) could not run for the same reason.

### Classification

86-story sample from 26 publishers, labels **agent-reviewed** (not
human-reviewed): 86/86 (100%) placed appropriately with excerpts; 83/86 (96.5%)
from headlines alone (what CI runs). 69 exactly as expected; the rest landed on
an accepted alternative. Ambiguities and misplacements are listed in
`classification-evaluation.md`. Target was 90%.

## Rollback

The package is one squash-mergeable branch. To roll back after a merge, revert
the merge commit: the build re-stamps the service worker, so installed readers
pick up the previous shell on their next launch; `topics.js` and `context.js`
simply stop being referenced. The gathered edition format is backward-compatible
in both directions — the app files items itself when `topic` is absent, and the
gatherer files items kept from an older edition.

## Decisions for the owner

1. **Labels are agent-reviewed.** A human pass over `topic-sample.json` would
   turn the evaluation into a human-reviewed one; disagreements are cheap to
   record (edit the file, re-run `node eval_topics.mjs`).
2. **Archive threshold.** News older than 7 days is labelled *From the archive*.
   Today every original is from 17 August, so the whole front page carries the
   label — honest, but it makes the case for a newer edition.
3. **"General" in the Newsstand.** Stories with no economic case now show under
   no topic (kicker *Newsstand*). If a desk would rather they not appear at all,
   that is a one-line filter.
4. **`context.js` is empty.** The *Why it matters* path exists and is tested,
   but no reviewed notes have been written; `REVIEW.md`'s rules apply to them.
5. **Pages source setting** (unchanged from before): Settings → Pages → Source
   should be *GitHub Actions* so only the workflow publishes.

## Out of scope (later packages)

Automated article generation, paid audio/services, newsletters, social posting,
clustering, calculators, article chat, redesign.
