# Search audit and implementation pass

An audit of what The Ledger serves to a crawler and to a reader, measured
against Google Search Central's current guidance, followed by the fixes that
audit supported. Baseline: the site as released in Package 1 (`main` at
`5f5f78c`, live at https://readtheledger.github.io/ on 12 September 2026).

Two things are kept apart throughout. **The Ledger's own reporting** — the
eight pieces in `content.js`, each with an address, a date and credited
sources — is what this pass works on. **The Newsstand** — third-party feed
summaries the desk is reading, gathered every half hour — is a separate,
labelled, app-only view, and is deliberately *not* made indexable: a page of
other publishers' RSS summaries is not content of The Ledger's own, and a
generic feed summary is a real content-quality limitation rather than
something to dress up as a page. The Newsstand keeps `noindex`.

Rankings and indexing are Google's decisions. Nothing below is a claim about
either; a Lighthouse score is a lab measurement of a page, not evidence of
ranking.

## Guidance this was measured against

- Robots: https://developers.google.com/search/docs/crawling-indexing/robots/intro —
  `robots.txt` is not a way to keep a page out of results; a blocked URL can
  still be indexed without its content, and a crawler that may not fetch a
  page cannot see its `noindex`.
- Indexing control: https://developers.google.com/search/docs/crawling-indexing/block-indexing
- Canonicals and duplicates: https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls
- Article structured data: https://developers.google.com/search/docs/appearance/structured-data/article
- Breadcrumbs: https://developers.google.com/search/docs/appearance/structured-data/breadcrumb
- Organization: https://developers.google.com/search/docs/appearance/structured-data/organization
- News sitemaps: https://developers.google.com/search/docs/crawling-indexing/sitemaps/news-sitemap —
  only articles from the last two days; an empty file is allowed and
  expected between publications.
- Helpful content and titles/snippets: https://developers.google.com/search/docs/fundamentals/creating-helpful-content,
  https://developers.google.com/search/docs/appearance/title-link,
  https://developers.google.com/search/docs/appearance/snippet

## Baseline evidence (before)

Read from the built pages of `main` at `5f5f78c` and from the live site
(fetched through a rendering proxy, since this sandbox cannot reach the
domain directly; the live `robots.txt`, `sitemap.xml` and page heads matched
the local build).

| Area | Finding | Guidance says |
|---|---|---|
| Crawlable content | Every story and section page carries a full static copy of its content inside `<main>`; JS off, a story reads in full (504 words on the sample story, 14 real links). Good. | — |
| Indexability | `robots.txt` disallowed `/*?view=` and `/*?q=`, while the app set `noindex` on those same views *and* every page kept `<link rel="canonical">` pointing at `/`. Those addresses are linked from every page. | A blocked URL can be indexed URL-only; the `noindex` behind the block is invisible; a `noindex` page should not name another page as canonical. |
| Empty sections | `/companies/` and `/opinion/` were served, linked from the navigation, indexable, with 31 words ("Nothing here yet"). Excluded from the sitemap, but nothing told a crawler not to index them. | Thin pages: mark `noindex` or give them content. |
| Headings | The front page and the section pages had no `h1` in the static copy; a story page had `h1` then `h3` (sources box); notices were `h3` under an `h1`. | Headings that describe the structure. |
| Titles / descriptions | Front page: "The Ledger — Finance, read properly" with a one-line generic description. Section pages: a boilerplate description ("original reporting and analysis…") even for the empty sections. Story: headline + standfirst (good). | Titles and descriptions specific to the page. |
| Internal links | A story page's only links were its sources (outbound) and the section nav; no links between pieces. No About page existed on the site — only a card inside the app with no address. | Real links; a page for who publishes this. |
| Structured data | `WebSite` (front), `CollectionPage` (sections), `NewsArticle` (stories, author = Organization "The Ledger", image = the 512 px icon). No `BreadcrumbList`, no `Organization` node on the front page. | Breadcrumb and Organization are supported types; author as an organisation is truthful here, since no person is stated. |
| Sitemaps | `sitemap.xml`: 14 URLs, `lastmod` from publication dates (good). No news sitemap. | News sitemap only for the last two days. Nothing published in the last two days as of this audit, so it would be empty. |
| Feeds | No feed of The Ledger's own pieces. | — |
| 404 | `404.html` real, `noindex`, links out. Good. | — |
| Asset loading | Google Fonts stylesheet render-blocking; it requested Playfair 500 and Inter 500, which no rule uses. Four same-origin scripts before the app script, also flagged as render-blocking by Lighthouse. | — |
| Accessibility | Lighthouse: badge text at 4.33:1 on the card background; a read story's dimmed standfirst at 3.19:1; heading order. No skip link. | 4.5:1 for body text. |
| Freshness | All eight pieces dated 17 August 2026. | Not a technical problem; a content one (see opportunities). |

## What changed

| Finding | Fix | Checked by |
|---|---|---|
| `robots.txt` blocks contradicted `noindex` + canonical | `robots.txt` allows everything. The app-only views are `noindex,follow` with a canonical of their own (`location.origin + address`); a built page keeps the values the build wrote. | `qa_seo.py`: Newsstand, search, front page, empty section |
| Empty sections indexable | The build writes `noindex,follow` for a section with no stories; it flips to `index,follow` the moment one is published. Still served and linked. | `qa_seo.py` |
| No `h1` / heading order | Front page: `<h1 class="sr">` with the site title (the wordmark stays the visible title). Section: `<h1>` + count, as the app shows. Sources box, context box and notices are `h2`. | `qa_seo.py` (JS off), Lighthouse `heading-order` |
| Generic descriptions | Front: names the desks and the sourcing rule. Section: count + latest piece and its date. Empty section: says it is empty. | `qa_seo.py` |
| No links between pieces; no About page | *More from The Ledger* on every story page (four pieces, same desk first, never itself). `/about/` from `about.js`, shared with the app; About in every static nav and in the menu. | `qa_seo.py`, `qa_pages.py` |
| No breadcrumbs / Organization | `BreadcrumbList` on section, story and About pages; `Organization` (logo, repository as `sameAs`) on the front page; `CollectionPage.hasPart`; `AboutPage` with the organisation as `mainEntity`. `dateModified` honours an article's `updated` field (the build refuses one earlier than `date`). | `qa_seo.py` parses every JSON-LD block |
| `NewsArticle.image` was the 512 px site icon | Removed. Google's Article guidance asks for an image that represents the article, not a logo, and has no required properties, so a piece without an image of its own carries none. A piece may now declare `image: {u, alt, w, h, caption}` in `content.js`; the build validates it (https, alt text, size; the icon is refused), writes it as `ImageObject`, shows it on the static page and in the reader, and uses it for the sharing preview. Without one, `og:image` stays the icon — a sharing preview, not an article image claim. No piece has an image today; no rich-result eligibility is claimed. | `qa_seo.py`: a fixture piece with an image, one without, and the icon refused |
| No news sitemap / feed | `sitemap-news.xml` with a 48-hour window (empty otherwise, which Google documents as acceptable); `feed.xml` (Atom, own pieces in full); both linked from `robots.txt` / every page. `/about/` in `sitemap.xml` without `lastmod`. | `qa_seo.py` builds as of two clocks to prove the window |
| Fonts render-blocking, unused weights | Stylesheet loaded with `media="print" onload="this.media='all'"` plus a `<noscript>` fallback; unused weights dropped. | Lighthouse `render-blocking-insight`; `qa_seo.py` |
| Contrast, skip link | Teal `#0A626B` (6.4:1 on paper); read-state dimming 75 %; a skip link to `<main id="main">`. | Lighthouse `color-contrast`; `qa_seo.py` |

Not changed, on purpose:

- **The Newsstand stays out of the index.** Its summaries are other
  publishers' feed text with a link out; that is the content-quality limitation
  the audit was asked to treat as real, and it is.
- **No author is invented.** `author` stays the organisation. A byline, a
  contact address and a corrections policy beyond "open an issue" need facts
  the owner has not stated (see below).
- **The About page claims only what the repository evidences.** The eight
  published pieces carry the default production label and predate any kept
  review record (`REVIEW.md` is the policy; no review record exists for them),
  so the page describes the labels as the intended editorial standard, not as
  completed human review. It gives the half-hour gathering as a target that
  scheduled runs have missed by hours, and names the destinations the app
  actually requests: GoatCounter, Google Fonts, this site's gathered edition,
  the feed relays as a fallback, publishers' image hosts for Newsstand images,
  and OpenAI only when the optional authenticated speech is used (the locally
  stored key goes with that request). It makes no "nothing else is sent" or
  "offline" promise.
- **The four same-origin scripts stay parser-blocking.** Deferring them would
  mean turning the inline app into a module (or a separate file), which the
  test suites drive through page globals; that is a larger change than this
  pass should carry, and the scripts are small (about 50 KB, one origin).
- **No article images exist yet.** The eight pieces have none, so their
  `NewsArticle` markup carries no `image`; adding real ones is a content
  opportunity, and the build now supports them.

## Measurements

All numbers here are **lab data**: Lighthouse 13.4.1, mobile emulation
(Moto G class, slow 4G throttling), run against the built site served from
this sandbox, three runs per page, medians reported. There is **no field
data**: this sandbox has no Chrome UX Report or Search Console access for the
origin, and the site is too small to have a CrUX entry in any case. A
Lighthouse score is a property of a page under emulation, not evidence of
ranking or indexing.

Conditions were made identical for the two builds: a stub gathered edition in
`data/feed.json` (production has one, so the app does not call the relays),
and every external host this sandbox cannot reach — Google Fonts, GoatCounter,
the relays — blocked outright so a request fails at once instead of hanging.
Two consequences: the fonts-stylesheet change **cannot be measured here** (the
stylesheet is blocked in both runs), and the first, uncontrolled baseline run
without that blocking (performance 77/76/76, LCP 3.9 s, Speed Index 20 s) was
an artefact of requests hanging until the proxy reset them, not a property of
the site; it is recorded here so it is not mistaken for one.

"Before" is `main` at `5f5f78c`; "after" is the merged pass, `a270ce2`.

| Page | Build | Perf | A11y | Best pr. | SEO | FCP ms | LCP ms | SI ms | TBT ms | CLS | KB |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `/` | before | 97 | 96 | 100 | 100 | 1981 | 1981 | 1981 | 0 | 0.065 | 170 |
| `/` | after | 97 | **100** | 100 | 100 | 1801 | 2101 | 1801 | 0 | 0.065 | 178 |
| `/markets/` | before | 97 | 98 | 100 | 100 | 1980 | 2101 | 1980 | 0 | 0.065 | 167 |
| `/markets/` | after | 98 | **100** | 100 | 100 | 1527 | 1981 | 1527 | 0 | 0.065 | 175 |
| `/story/led-20260817-fed/` | before | 97 | 94 | 100 | 100 | 1981 | 1981 | 1981 | 0 | 0.065 | 171 |
| `/story/led-20260817-fed/` | after | 98 | **100** | 100 | 100 | 1535 | 2176 | 1535 | 0 | 0.065 | 179 |

What the numbers do and do not show:

- **Accessibility 94–98 → 100** on all three pages: the `color-contrast` audit
  (badge text, read-state standfirst) and `heading-order` (sources box,
  notices) went from failing to passing. This is the one change the lab
  measures cleanly.
- **Performance and SEO categories did not move** (97–98 and 100 before and
  after). Lighthouse's SEO category never saw the `robots.txt`/`noindex`/
  canonical contradiction, the missing `h1`s or the thin sections — it checks
  a page's own tags for syntax, not the site's signals for sense — which is
  why `qa_seo.py` exists. Do not read 100 as "nothing was wrong".
- **Paint timings** (FCP, Speed Index) came in 180–450 ms lower after, LCP
  within ±200 ms either way; with three runs per page and ~200 ms
  run-to-run variance this is at most suggestive, not a measured gain. The
  render-blocking audit still names the same-origin scripts (now including
  `about.js`, +8 KB), as expected from the decision not to defer them.
- **Weight** rose 7–8 KB per page: `about.js` and the extra static content
  (About card, related links, breadcrumb data). Every page is still under
  180 KB transferred, uncompressed in this sandbox (GitHub Pages gzips).

## Original reporting versus the Newsstand

| | The Ledger's own pieces | Newsstand items |
|---|---|---|
| Where | `/story/<id>/`, section pages, front page, `feed.xml` | `/?view=newsstand` only, inside the app |
| Indexable | Yes (`index,follow`, own canonical, in `sitemap.xml`) | No (`noindex,follow`, own canonical, not in any sitemap) |
| Structured data | `NewsArticle` + `BreadcrumbList` | None |
| Content | Full text, static, credited sources | Publisher summary + link; full text only under a named licence |
| Freshness signal | `datePublished`, `lastmod`, the news sitemap when within 48 h | The gathering time, shown on the view |

## Remaining opportunities (content, not code)

1. **Publish.** Every piece is dated 17 August 2026. The news sitemap is
   empty and will stay empty until something is published; the archive
   labels are honest about the age. Nothing technical fixes this.
2. **Who writes it.** `author` is the organisation because no person has been
   named. A byline, an author page and a stated editor would be supported
   `Person` data — only once the owner states them.
3. **Contact and corrections.** The About page says corrections go to the
   repository's issues, which is true. An email address or a corrections
   log would be better; both are owner facts.
4. **Images.** A representative image per piece (1200 px wide or more, in
   more than one aspect ratio) would complete the article markup and make
   sharing previews real; `content.js` accepts `image: {u, alt, w, h, caption}`
   per piece and the build does the rest. None exists today.
5. **Newsstand summaries.** They are what the feeds give. Any Newsstand item
   The Ledger wants in search needs a Ledger piece written about it, with the
   review loop in `REVIEW.md`.
6. **Script loading.** A deferred app (module or separate file) would take
   the four scripts off the parser's path; it needs the test suites' globals
   rethought first.

## Blockers that need the owner

- **Search Console.** No property is verified for this session, so
  indexing status was not inspected and no sitemap was submitted. Owner
  action: verify `readtheledger.github.io` (the HTML-file or meta-tag method
  works on Pages) and submit `sitemap.xml`; submit `sitemap-news.xml` only if
  the publication intends to publish within two-day windows — otherwise it
  will simply report as empty.
- **Pages source.** The repository still publishes through GitHub's built-in
  branch build as well as the workflow; the workflow waits for it. Owner
  action: Settings → Pages → Source → GitHub Actions.
- **Field data.** There is no Chrome UX Report data for this origin available
  from here; every number above is lab data.

## Live verification

Deploy: workflow run 49 (`34701806904`) for `a270ce2`, every step
successful, "Reported success" at 15:18:40 UTC — 11:18 a.m. Toronto (EDT),
12 September 2026. The job log lists the deployed artifact, which includes
`about/index.html`, `about.js`, `sitemap.xml`, `sitemap-news.xml`, `feed.xml`,
`robots.txt`, `404.html`, every section and story page, and the gathered
`data/feed.json`.

Fetched live after the deploy (this sandbox cannot reach the domain directly;
two fetch proxies were used, which return rendered text and honour robots
directives, and one of which reports the served `Last-Modified`):

| Address | Verified live |
|---|---|
| `/robots.txt` | Verbatim: `User-agent: *`, `Allow: /`, no `Disallow`, `Sitemap:` lines for `sitemap.xml` and `sitemap-news.xml`. |
| `/sitemap.xml` | 15 `<loc>` entries: `/`, five sections with stories, eight stories with their publication dates as `lastmod`, and `/about/` with no `lastmod`. Served `Last-Modified: Sat, 12 Sep 2026 15:18:36 GMT` — this deploy. |
| `/about/` | The full new About text, including the corrected paragraphs: production labels as the intended editorial standard, the half-hour gathering as a target that runs have missed by hours, "What leaves your device" naming GoatCounter, Google Fonts, the relays, image hosts and OpenAI-only-with-a-key. |
| `/companies/` | The fetch proxy refused the page with `CRAWL_NOINDEX`: the live page carries the `noindex` the build wrote for an empty section. |
| `/story/led-20260817-fed/` | `h1` headline, standfirst, "17 August 2026, 08:30 UTC", full body, *Sources & further reading*, the "Reported and written by The Ledger" line. (The proxy strips `<nav>`, so the related-links block is verified in the artifact and by `qa_seo.py`, not in this fetch.) |
| `/feed.xml` | Served, titled "The Ledger", same `Last-Modified` as the sitemap; the proxy does not render Atom entries, so the entry list is verified in the artifact and by `qa_seo.py`. |
| `/sitemap-news.xml` | In the deployed artifact and named by the live `robots.txt`; the fetch proxies could not render the (empty) XML, so its live content is not separately verified. It is empty by design until something is published within 48 hours. |

Not verified from here: HTTP status codes (the proxies do not expose them;
the 404 behaviour is unchanged from Package 1 and covered by `qa_pages.py`
against a server that behaves as Pages does), the `<head>` metadata and
JSON-LD of the live pages (the proxies strip them; they are byte-identical to
the local build of `a270ce2`, which `qa_seo.py` and `qa_pages.py` check), and
anything in Search Console (no verified property is available to this
session; nothing was submitted).
