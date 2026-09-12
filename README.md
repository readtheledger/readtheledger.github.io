# The Ledger

A quiet reader for high-quality, free-to-read financial journalism, built to look and feel like a broadsheet business paper on an iPhone 17 Pro Max. No adverts, no trackers, no paywall circumvention. Every article keeps its byline, its publication and a link home.

## The editorial model

The Ledger is news-led. The front page is composed to a deliberate mix: roughly **60–70% timely news** across finance, startups and AI, built to be read and shared quickly; **20–30% "Why it matters"** — The Ledger's own short analysis of what a story means financially; and **10–15% deep, expert-quality work**, anchored by one weekly Ledger-written feature on the overlap of finance and AI. The composer in `index.html` enforces this mix whatever the feeds delivered today, and the test suite holds it to those bands.

The front page carries only The Ledger's own journalism. Every article there is a complete, self-contained piece written in The Ledger's own voice from credited research — not a summary of someone else's story. Every material source behind an article is credited and linked in a **Sources & further reading** box at the foot of the piece; those links support the reporting, they do not replace it. The wider public-feed layer lives one tab over, in a clearly labelled **Newsstand** — what the desk is reading, not what The Ledger has written — where a third-party story appears only as a brief summary with attribution and a link to the original, never dressed up as a Ledger article. The publication rule there is strict and simple: **a public feed is an invitation to read, not a licence to republish.** Full third-party text renders only under an explicit reuse licence — Creative Commons work, US government material, and publishers whose terms allow reproduction with acknowledgement — and that licence is named beside the piece; everything else in the Newsstand stays a summary, at most one short attributed quote, and a prominent route to the source. Listen and Copy carry only what's actually rendered, never a withheld body.

## What it does

The front page is arranged like a newspaper, entirely from The Ledger's own articles: one bold lead story, short news stories underneath, a claret-edged **Why it matters** card carrying the day's best analysis with The Ledger's context, **The Ledger Weekly** deep dive, and a *Long reads* rail beside it on wider screens. The masthead carries the wordmark, **Search** and **Menu**; the topic strip beneath covers Markets, Companies, Economics, Central Banks, Opinion, Tech & Finance and Personal Finance, plus **Newsstand** for the public-feed stories and **Saved** for your bookmarks (the menu lists the same topics and groups the secondary actions — dark mode, settings, checking for a newer Newsstand, reloading the app). Search, bookmarking, mark-as-read, pull-to-refresh and a reading-progress bar are all there, and there is a full dark reading mode.

## Dates you can trust

Every time on show comes from the content. The masthead's edition line is the newest publication date in `content.js` — "Latest edition 17 August 2026" — and it is written by the build, so it reads without JavaScript and never becomes today's date. A news story more than a week old is labelled *From the archive*; analysis and deep work carry their date and are not expired by age. A Newsstand item whose feed gave no usable date says *date unknown* rather than *just now*. The About page is part of the app, not an article: it sits at the foot of the front page and carries no date. The Newsstand says when it was actually gathered and how long ago, and a refresh reports one of three outcomes — a newer edition loaded, no newer edition, or the edition could not be reached and the previous one is kept with its true time. `docs/package-1/navigation-behaviour.md` sets out the addresses, the history behaviour and the sharing messages.

Every article has two buttons that matter. **Listen** reads the piece aloud — with your own OpenAI API key it uses OpenAI's speech models and sounds close to a human presenter, and without a key it falls back to the voice built into your phone, so the button always works. **Copy** puts the whole article on your clipboard as clean plain text: headline, publication, author, date, original link, then the body.

## Every story has an address

Each Ledger article is published at `/story/<id>/` and each editorial section at its own path (`/markets/`, `/central-banks/`, `/tech-and-finance/` and so on). Those pages are written by `build.mjs`: each one is the app, with that page's title, description, canonical URL, Open Graph and Twitter Card metadata and `NewsArticle` structured data in its head, and a static copy of the content inside `<main>` so the story reads in full — headline, standfirst, body, sources, date — with JavaScript off. When the app boots on one of those pages it removes the static copy and opens the same story in the reader, so the address keeps meaning what it meant; a refresh, a bookmark or a shared link all come back to the story. Headlines on the front page are ordinary links to those addresses, section tabs are links to the section pages, and Share hands the system a Ledger story's own URL (a Newsstand item still shares the publisher's original). The About page is `/about/`, written from `about.js`, which the app and the build share. The build also writes `sitemap.xml`, a news sitemap (`sitemap-news.xml`, listing only what was published in the last 48 hours — empty otherwise), an Atom feed of The Ledger's own pieces (`feed.xml`), `robots.txt` and a real `404.html`.

Every page opens with one `h1` and has a skip link; a section with no stories yet is served and linked but marked `noindex` until it has one; a story page carries `NewsArticle` and `BreadcrumbList` structured data, with The Ledger (the organisation) as author — no person is named because none has been stated — and links to four other pieces. The app-only views (`/?view=newsstand`, `/?view=saved`, `?q=`) are `noindex` with a canonical of their own, and nothing is blocked in `robots.txt`, so a crawler can read that instruction. `docs/seo/README.md` is the audit behind this, with the before-and-after evidence.

```
node build.mjs            # writes the site into ./_site
```

## Getting it onto your iPhone

The site is a folder of static files. It needs to be served over HTTPS at the root of a domain for the service worker, Add-to-Home-Screen and clipboard access to work, so opening `index.html` straight off the filesystem will only give you a partial experience.

Run `node build.mjs` and publish the `_site` folder. The quickest route is **Netlify Drop**: go to `app.netlify.com/drop` on your laptop and drag `_site` onto the page. You get an HTTPS URL in a few seconds, with no account needed to start. Open that URL in Safari on your phone, tap the share icon, then *Add to Home Screen*.

For **GitHub Pages**, the workflow in `.github/workflows/pages.yml` runs the build and deploys `_site` on every push to `main`; in Settings → Pages the source should be *GitHub Actions* so that only that workflow publishes. The pages are written for the root of a domain (`https://<user>.github.io/`), not a repository sub-path. **Cloudflare Pages** and **Vercel** work the same way — build command `node build.mjs`, output directory `_site`.

Once installed to the home screen the app runs full-screen with the salmon status bar, and the service worker keeps the shell and your last-read articles available when you lose signal.

Redeploying is just replacing the files: the service worker asks the network for every page first and only falls back to its cached copy — the page itself, cached under its own address, or the app shell for a story or section that exists in this edition (the build stamps that list into the worker) — when the network is slow or absent, so a change reaches everyone who has installed the app on their next launch. A 404 from the server stays a 404, and offline, an address that is not in the edition is a 503 rather than the front page. The build stamps the service worker with a hash of the app and the edition, so a new article installs a fresh shell without anything being version-stamped by hand.

## Adding your OpenAI key

Open Settings (the gear in the masthead), paste a key that starts with `sk-`, choose a model and a voice, and save. The key is written to this browser's `localStorage` and is sent to exactly one place: `https://api.openai.com/v1/audio/speech`. It is never transmitted anywhere else, there is no server in this app to send it to, and you can clear it by emptying the field and saving again.

`gpt-4o-mini-tts` is the default and the best value; `tts-1-hd` is the higher-fidelity older model. Long articles are split into sentence-aware chunks of roughly 3,800 characters, queued so playback is seamless, and each generated chunk is cached in IndexedDB — so re-listening to an article costs nothing. *Clear audio cache* in Settings empties that store.

Lock-screen and background playback use the Media Session API, so the title, skip-back-15 and skip-forward-15 controls appear on your lock screen and in AirPods gestures.

## Changing the sources

Open `sources.js`. Each entry looks like this:

```js
{n:"Calculated Risk", u:"https://calculatedrisk.substack.com/feed", s:"Economics", h:true, q:1.25, k:"analysis", rights:"summary"}
```

`n` is the display name, `u` is the RSS or Atom URL, `s` is the fallback section when the text gives no clearer signal, `h:true` marks a heavy full-text feed (fetched in a second wave when the app has to gather in the browser), and `q` is a quality weight used when choosing the lead story — analysts and central banks sit above 1.0, wire filler below. `k` is the editorial kind — `"news"`, `"analysis"` or `"deep"` — which decides where the source's stories sit in the front-page mix. `rights` records what The Ledger may carry from the feed: `"summary"` (a summary, one short attributed quote and a link out) or `"full"` (the whole article), and `"full"` needs `lic` to name the licence — The Conversation's CC BY-ND, Federal Reserve Board material, the ECB's reproduction-with-acknowledgement terms. The gatherer refuses to run for a source with no rights value, so nothing ships without a recorded permission. Delete a line to remove a source; add a line to add one. The app and the gatherer both read this file, so nothing else needs to change.

## How the Newsstand is gathered

`fetch_feeds.mjs` reads every feed in `sources.js` and writes one file, `data/feed.json`, that the app loads with a single request: the items, the time they were gathered, and the state of every source. The Pages workflow runs it before each build — on every push and every half hour on a schedule, which is a target rather than a promise, since GitHub may delay or drop scheduled runs; that is why the app shows the time the Newsstand was *actually* gathered, in Settings and at the top of the Newsstand, and why the workflow can also be run by hand. A feed that does not answer keeps its items from the edition that is live, marked as kept from an earlier gathering with their real time, so the page is never emptied by one bad feed. Every item is checked on the way in — an absolute link, a publication date that parses and is not in the future, a title — and anything else is dropped and counted. The same story is carried once (duplicates removed by link, then by title), and a story credited to Reuters, AP or another wire keeps that origin whichever desk carried it, so copies of one syndicated report can never pass for independent confirmations. A `"summary"` source ships an excerpt and a word count, never the article, so the rights rule is enforced in the data as well as on the page.

If the gathered file cannot be read, the app gathers in the browser as it always did, through public CORS relays, so an installed reader is never left with nothing.

The Ledger's own articles live in `content.js`, not in `index.html`: each entry carries its `kind` (`"news"`, `"analysis"` or `"deep"`), section, headline, body and a `sources` array crediting every piece of research behind it. Follow `REVIEW.md` before publishing an addition or substantive revision. Mark the current deep-dive feature with `weekly:true`. Each entry may carry an `image` — its own picture, with alt text, size, caption, credit, an `ai` flag and the derivative widths; `media.js` documents the contract and `docs/design/README.md` the policy (full 3:2 compositions, no crops, the caption adds no claim).

Every entry must explicitly set `produced`: `"reported"` (a person wrote it) or `"assisted"` (a model drafted it from credited sources and a person checked every claim before publication). Both require the human factual-source and read-aloud checklist, recorded in the publication pull request. The eight original August 17 articles instead carry `"legacy-unrecorded"`: their retained evidence does not establish their production history or a recorded factual review. `production.js` limits that category to their pinned IDs and original dates and shares the attribution with the build and reader. Omitted, unsupported or new-article legacy values fail the build. Validation checks metadata, not whether a person really performed a review. The archive status also accompanies Listen and Copy. `drafts/` is where new work waits for actual review. `index.html` holds `WIM_NOTES`, the standing background notes by desk.

Every feed shipped here was checked by hand: public, free, no login and no paywall. The Financial Times, WSJ, Bloomberg and The Economist are deliberately absent. Settings shows a live list of which feeds answered on the last gathering and how many items each returned.

## How a Newsstand story is filed

`topics.js` files each story by its actual subject — the headline first, then the opening of the summary, then the rest — and by its economic relevance. The publisher's category (`s` in `sources.js`) is supporting evidence, never the verdict: a business desk's feed carries politics and human interest, and a story with no economic case of its own stays in the Newsstand under no topic rather than filling Companies. A source marked `fixed:true` is always filed under its own section (a central bank's press feed is Central Banks whatever a headline says), and a table of headline patterns files recurring formats. The gatherer writes the section, its confidence and its reason into the edition, and the reader shows the publisher's own filing beside The Ledger's when they differ. `node eval_topics.mjs --edition data/feed.json` scores the classifier against the labelled sample in `docs/package-1/topic-sample.json`.

A Newsstand story's context box is labelled honestly. The desk's standing note is **Background** — a general note on that kind of story, and the box says so. **Why it matters** appears only for a note an editor wrote about that story and checked against the sources it names, kept in `context.js`; it is empty until someone writes one, and nothing is generated to fill it.

## How it handles article text

The Newsstand normally arrives as the gathered file described above. When it cannot be read, browsers cannot read cross-origin RSS directly, so feeds are fetched through public CORS relays with a fallback chain (`api.allorigins.win`, then `corsproxy.io`, then `api.codetabs.com`). If all of them fail, the app shows whatever is already cached on your device rather than an empty screen.

What renders is decided by rights, not by what the feed happened to carry. A source with a named reuse licence renders in full — sanitised of scripts, iframes and inline handlers, with the licence stated in the attribution line and a link to the original. Every other story, including the many whose feeds carry complete articles, is presented as The Ledger's page: the summary as the lede, at most one short quote attributed to the publisher, the Ledger's "Why it matters" analysis in its own box, an attribution line, and a solid *Read the full story* button out to the source. Links and images are kept only if the browser resolves them to `http`, `https` or `mailto`, which is stricter than it sounds: a leading space or tab makes `javascript:` look harmless to a naive check but not to the URL parser. A content security policy sits behind that, limiting scripts to this site and the Cloudflare analytics beacon, and connections to this site, speech, feed relays and the analytics endpoint. The integration does not read or transmit the speech key; changes to the third-party script remain a trust boundary. The app never scrapes past a paywall and never fetches anything a feed did not publish.

A note on the *Long reads* rail: it is ranked by depth and source quality, not by readership, because a static client has no way to know what other people are reading. It is labelled honestly rather than called "most read".

## Files

The canonical public site uses one Cloudflare Web Analytics property. The adapter
in `analytics.js` guards loading and outgoing requests with the persistent
**Exclude my visits** choice, canonical-host and automation checks. GoatCounter
remains inactive. `docs/measurement.md` describes native navigation measurement,
opt-out reloads, privacy boundaries and the separate dashboard receipt check.
`python qa_analytics.py --beacon <reviewed-local-beacon.js>` tests the actual
provider script with all page and collection traffic intercepted locally.

`index.html` is the entire application — markup, styles and logic in one file. `content.js` is the publication: The Ledger's own articles, loaded at boot. `about.js` is the About page, shared by the app and the build. `media.js` is the contract and renderer for a piece's picture, shared the same way; `assets/editorial/<id>/` holds each picture's web derivatives and provenance (masters stay outside the repository; `make_derivatives.py` makes the derivatives). `sw.js` is the offline shell. `manifest.webmanifest` plus the PNG icons make it installable. `sources.js` is the list of public feeds, read by the app and the gatherer alike; `topics.js` is the filing rule they share; `context.js` holds reviewed story-specific context. `fetch_feeds.mjs` gathers those feeds into `data/feed.json`. `build.mjs` writes the story, section and About pages, the sitemaps, the Atom feed, `robots.txt` and the 404 page into `_site` and copies the gathered Newsstand in; `check_site.sh` is the artifact check the deploy runs on that folder. `qa.py`, `qa_live.py`, `qa_pages.py`, `qa_feed.py`, `qa_package1.py` and `qa_seo.py` are the test suites, and `fetch_fixtures.sh` captures the feeds the live suite reads.

Only `_site` is deployed — the workflow in `.github/workflows/pages.yml` runs the build and publishes that folder, and the build fails if anything a page references is missing from the output. The tests and this README stay behind.

## Tests

Both suites drive headless Chromium at a 440 × 956 viewport with touch and mobile emulation.

```
pip install playwright && playwright install chromium

python3 qa.py            # 53 checks: layout, touch targets, copy, listen fallback,
                         # dark mode, settings persistence, manifest, service worker,
                         # URL sanitising, bookmark durability, cache limits, the
                         # editorial mix, Ledger sourcing and the licence model
python3 qa_pages.py      # 90 checks: builds the site, runs the deploy's own artifact
                         # check on it (and on an unstamped copy it must reject), the
                         # app's reading of a gathered Newsstand, then every story and section
                         # page in a fresh browser with JavaScript off (content,
                         # metadata, dates, links), the same addresses with it on
                         # (refresh, back and forward, sharing, bookmarks, audio,
                         # copy), the sitemap, robots.txt and 404, the service
                         # worker caching pages by address, letting a 404 through
                         # and serving offline, and an upgrade from the previously
                         # released worker
python3 qa_package1.py   # package 1: freshness, filing, labels, the masthead and
                         # menu at 360/390/768/1440, restorable views, sharing outcomes
python3 qa_media.py      # 29 checks: a piece's picture on the static page and in the
                         # reader (one figure, one fetch), caption/credit/disclosure,
                         # the front page's pace, the text-led state, typography,
                         # the Listen dock, Back/Forward, no overflow 320–1440px
python3 qa_seo.py        # 45 checks: what a crawler is served — headings, titles,
                         # descriptions, canonicals, robots, both sitemaps, the Atom
                         # feed, structured data, the About page, related links, the
                         # skip link — and that the app keeps those signals honest
python3 qa_production.py # archive attribution on all eight static/reader pages,
                         # explicit production categories and rejection cases;
                         # every browser request is served locally or blocked
python3 qa_cache_update.py # gated worker installation, old-client request, image
                           # replacement, scoped cleanup, saved state and offline
                           # reading across two updates; local disposable browser
node eval_topics.mjs --edition data/feed.json   # the classifier against the labelled sample
python3 qa_feed.py       # 21 checks: the gatherer against synthetic RSS and Atom
                         # feeds — validation and dropped-item reasons, excerpts
                         # versus licensed markup, duplicates, wire origins, a
                         # feed answering 500 kept stale from the previous
                         # edition, a feed that never answers, rights enforcement
./fetch_fixtures.sh      # capture eight real feeds (not committed — see .gitignore)
python3 qa_live.py       # 23 checks: sectioning, dedupe, bylines, sanitisation, the
                         # mix and licence model, the Newsstand, copy fidelity,
                         # TTS chunking against real publisher output
```

The page suite serves the built site the way GitHub Pages does — directories to `index.html`, unknown paths to `404.html` with a 404 status — and simulates an outage by dropping connections at the server, because a browser's offline emulation does not reach a service worker's own fetches. The live suite intercepts the relay request and answers with the captured feeds, so it exercises the real fetch-and-parse path without depending on the network being up. Publisher feed content is deliberately not committed to this repository.

## Known limits

A browser gives a site something like five megabytes of local storage, which is a few dozen full-text articles and no more, so the offline cache keeps the most recent forty. Bookmarks are exempt: saving an article keeps your own copy of it, so it stays readable — and listenable, and copyable — long after it has dropped off the feed. If storage does fill up, the oldest bookmarks give up their formatting before any bookmark is dropped.

Clipboard writes and the service worker need HTTPS or `localhost`. Background audio on iOS keeps playing while the screen is locked once playback has started, but Safari will not start playback without a tap. The device-voice fallback has no seek bar — the skip buttons move between chunks instead. Feed relays are free public services and occasionally rate-limit; the app degrades to cached content when that happens rather than failing.
