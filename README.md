# The Ledger

A quiet reader for high-quality, free-to-read financial journalism, built to look and feel like a broadsheet business paper on an iPhone 17 Pro Max. No adverts, no trackers, no paywall circumvention. Every article keeps its byline, its publication and a link home.

## The editorial model

The Ledger is news-led. The front page is composed to a deliberate mix: roughly **60–70% timely news** across finance, startups and AI, built to be read and shared quickly; **20–30% "Why it matters"** — The Ledger's own short analysis of what a story means financially; and **10–15% deep, expert-quality work**, anchored by one weekly Ledger-written feature on the overlap of finance and AI. The composer in `index.html` enforces this mix whatever the feeds delivered today, and the test suite holds it to those bands.

The front page carries only The Ledger's own journalism. Every article there is a complete, self-contained piece written in The Ledger's own voice from credited research — not a summary of someone else's story. Every material source behind an article is credited and linked in a **Sources & further reading** box at the foot of the piece; those links support the reporting, they do not replace it. The wider public-feed layer lives one tab over, in a clearly labelled **Newsstand** — what the desk is reading, not what The Ledger has written — where a third-party story appears only as a brief summary with attribution and a link to the original, never dressed up as a Ledger article. The publication rule there is strict and simple: **a public feed is an invitation to read, not a licence to republish.** Full third-party text renders only under an explicit reuse licence — Creative Commons work, US government material, and publishers whose terms allow reproduction with acknowledgement — and that licence is named beside the piece; everything else in the Newsstand stays a summary, at most one short attributed quote, and a prominent route to the source. Listen and Copy carry only what's actually rendered, never a withheld body.

## What it does

The front page is arranged like a newspaper, entirely from The Ledger's own articles: one bold lead story, short news stories underneath, a claret-edged **Why it matters** card carrying the day's best analysis with The Ledger's context, **The Ledger Weekly** deep dive, and a *Long reads* rail beside it on wider screens. Section tabs across the top cover Markets, Companies, Economics, Central Banks, Opinion, Tech & Finance and Personal Finance, plus a **Newsstand** tab for the public-feed stories and your saved articles. Search, bookmarking, mark-as-read, pull-to-refresh and a reading-progress bar are all there, and there is a full dark reading mode.

Every article has two buttons that matter. **Listen** reads the piece aloud — with your own OpenAI API key it uses OpenAI's speech models and sounds close to a human presenter, and without a key it falls back to the voice built into your phone, so the button always works. **Copy** puts the whole article on your clipboard as clean plain text: headline, publication, author, date, original link, then the body.

## Every story has an address

Each Ledger article is published at `/story/<id>/` and each editorial section at its own path (`/markets/`, `/central-banks/`, `/tech-and-finance/` and so on). Those pages are written by `build.mjs`: each one is the app, with that page's title, description, canonical URL, Open Graph and Twitter Card metadata and `NewsArticle` structured data in its head, and a static copy of the content inside `<main>` so the story reads in full — headline, standfirst, body, sources, date — with JavaScript off. When the app boots on one of those pages it removes the static copy and opens the same story in the reader, so the address keeps meaning what it meant; a refresh, a bookmark or a shared link all come back to the story. Headlines on the front page are ordinary links to those addresses, section tabs are links to the section pages, and Share hands the system a Ledger story's own URL (a Newsstand item still shares the publisher's original). The build also writes `sitemap.xml`, `robots.txt` and a real `404.html`.

```
node build.mjs            # writes the site into ./_site
```

## Getting it onto your iPhone

The site is a folder of static files. It needs to be served over HTTPS at the root of a domain for the service worker, Add-to-Home-Screen and clipboard access to work, so opening `index.html` straight off the filesystem will only give you a partial experience.

Run `node build.mjs` and publish the `_site` folder. The quickest route is **Netlify Drop**: go to `app.netlify.com/drop` on your laptop and drag `_site` onto the page. You get an HTTPS URL in a few seconds, with no account needed to start. Open that URL in Safari on your phone, tap the share icon, then *Add to Home Screen*.

For **GitHub Pages**, the workflow in `.github/workflows/pages.yml` runs the build and deploys `_site` on every push to `main`; in Settings → Pages the source should be *GitHub Actions* so that only that workflow publishes. The pages are written for the root of a domain (`https://<user>.github.io/`), not a repository sub-path. **Cloudflare Pages** and **Vercel** work the same way — build command `node build.mjs`, output directory `_site`.

Once installed to the home screen the app runs full-screen with the salmon status bar, and the service worker keeps the shell and your last-read articles available when you lose signal.

Redeploying is just replacing the files: the service worker asks the network for every page first and only falls back to its cached copy — the page itself, cached under its own address, or the app shell for a story it has never fetched — when the network is slow or absent, so a change reaches everyone who has installed the app on their next launch. A 404 from the server stays a 404. The build stamps the service worker with a hash of the app and the edition, so a new article installs a fresh shell without anything being version-stamped by hand.

## Adding your OpenAI key

Open Settings (the gear in the masthead), paste a key that starts with `sk-`, choose a model and a voice, and save. The key is written to this browser's `localStorage` and is sent to exactly one place: `https://api.openai.com/v1/audio/speech`. It is never transmitted anywhere else, there is no server in this app to send it to, and you can clear it by emptying the field and saving again.

`gpt-4o-mini-tts` is the default and the best value; `tts-1-hd` is the higher-fidelity older model. Long articles are split into sentence-aware chunks of roughly 3,800 characters, queued so playback is seamless, and each generated chunk is cached in IndexedDB — so re-listening to an article costs nothing. *Clear audio cache* in Settings empties that store.

Lock-screen and background playback use the Media Session API, so the title, skip-back-15 and skip-forward-15 controls appear on your lock screen and in AirPods gestures.

## Changing the sources

Open `index.html` and find the `SOURCES` array near the top of the script. Each entry looks like this:

```js
{n:"Calculated Risk", u:"https://calculatedrisk.substack.com/feed", s:"Economics", h:true, q:1.25, k:"analysis"}
```

`n` is the display name, `u` is the RSS or Atom URL, `s` is the fallback section when the text gives no clearer signal, `h:true` marks a heavy full-text feed (fetched in a second wave so the front page paints fast), and `q` is a quality weight used when choosing the lead story — analysts and central banks sit above 1.0, wire filler below. `k` is the editorial kind — `"news"`, `"analysis"` or `"deep"` — which decides where the source's stories sit in the front-page mix. `lic` names a reuse licence and exists only where one genuinely does (The Conversation's CC BY-ND, Federal Reserve Board material, the ECB's reproduction-with-acknowledgement terms); a source without `lic` is never republished in full, no matter what its feed carries. Delete a line to remove a source; add a line to add one. Nothing else needs to change.

The Ledger's own articles live in `content.js`, not in `index.html`: each entry carries its `kind` (`"news"`, `"analysis"` or `"deep"`), section, headline, body and a `sources` array crediting every piece of research behind it — replace or add an entry and redeploy to publish. Mark the current deep-dive feature with `weekly:true`. `index.html` still holds `WIM_NOTES`, the short "Why it matters" context notes shown on the front-page card, by desk.

Every feed shipped here was checked by hand: public, free, no login and no paywall. The Financial Times, WSJ, Bloomberg and The Economist are deliberately absent. Settings shows a live list of which feeds answered on the last refresh and how many items each returned.

## How it handles article text

Browsers cannot read cross-origin RSS directly, so feeds are fetched through public CORS relays with a fallback chain (`api.allorigins.win`, then `corsproxy.io`, then `api.codetabs.com`). If all of them fail, the app shows whatever is already cached on your device rather than an empty screen.

What renders is decided by rights, not by what the feed happened to carry. A source with a named reuse licence renders in full — sanitised of scripts, iframes and inline handlers, with the licence stated in the attribution line and a link to the original. Every other story, including the many whose feeds carry complete articles, is presented as The Ledger's page: the summary as the lede, at most one short quote attributed to the publisher, the Ledger's "Why it matters" analysis in its own box, an attribution line, and a solid *Read the full story* button out to the source. Links and images are kept only if the browser resolves them to `http`, `https` or `mailto`, which is stricter than it sounds: a leading space or tab makes `javascript:` look harmless to a naive check but not to the URL parser. A content security policy sits behind that, so no script can be loaded from another host and the page can only talk to the speech API and the feed relays — the API key in local storage has nowhere to be sent even if something did slip through. The app never scrapes past a paywall and never fetches anything a feed did not publish.

A note on the *Long reads* rail: it is ranked by depth and source quality, not by readership, because a static client has no way to know what other people are reading. It is labelled honestly rather than called "most read".

## Files

`index.html` is the entire application — markup, styles and logic in one file. `content.js` is the publication: The Ledger's own articles, loaded at boot. `sw.js` is the offline shell. `manifest.webmanifest` plus the PNG icons make it installable. `build.mjs` writes the story and section pages, the sitemap, `robots.txt` and the 404 page into `_site`. `qa.py`, `qa_live.py` and `qa_pages.py` are the test suites, and `fetch_fixtures.sh` captures the feeds the live suite reads.

Only `_site` is deployed — the workflow in `.github/workflows/pages.yml` runs the build and publishes that folder, and the build fails if anything a page references is missing from the output. The tests and this README stay behind.

## Tests

Both suites drive headless Chromium at a 440 × 956 viewport with touch and mobile emulation.

```
pip install playwright && playwright install chromium

python3 qa.py            # 53 checks: layout, touch targets, copy, listen fallback,
                         # dark mode, settings persistence, manifest, service worker,
                         # URL sanitising, bookmark durability, cache limits, the
                         # editorial mix, Ledger sourcing and the licence model
python3 qa_pages.py      # 75 checks: builds the site, then every story and section
                         # page in a fresh browser with JavaScript off (content,
                         # metadata, dates, links), the same addresses with it on
                         # (refresh, back and forward, sharing, bookmarks, audio,
                         # copy), the sitemap, robots.txt and 404, the service
                         # worker caching pages by address, letting a 404 through
                         # and serving offline, and an upgrade from the previously
                         # released worker
./fetch_fixtures.sh      # capture eight real feeds (not committed — see .gitignore)
python3 qa_live.py       # 23 checks: sectioning, dedupe, bylines, sanitisation, the
                         # mix and licence model, the Newsstand, copy fidelity,
                         # TTS chunking against real publisher output
```

The page suite serves the built site the way GitHub Pages does — directories to `index.html`, unknown paths to `404.html` with a 404 status — and simulates an outage by dropping connections at the server, because a browser's offline emulation does not reach a service worker's own fetches. The live suite intercepts the relay request and answers with the captured feeds, so it exercises the real fetch-and-parse path without depending on the network being up. Publisher feed content is deliberately not committed to this repository.

## Known limits

A browser gives a site something like five megabytes of local storage, which is a few dozen full-text articles and no more, so the offline cache keeps the most recent forty. Bookmarks are exempt: saving an article keeps your own copy of it, so it stays readable — and listenable, and copyable — long after it has dropped off the feed. If storage does fill up, the oldest bookmarks give up their formatting before any bookmark is dropped.

Clipboard writes and the service worker need HTTPS or `localhost`. Background audio on iOS keeps playing while the screen is locked once playback has started, but Safari will not start playback without a tap. The device-voice fallback has no seek bar — the skip buttons move between chunks instead. Feed relays are free public services and occasionally rate-limit; the app degrades to cached content when that happens rather than failing.
