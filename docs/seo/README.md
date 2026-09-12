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
- **The four same-origin scripts stay parser-blocking.** Deferring them would
  mean turning the inline app into a module (or a separate file), which the
  test suites drive through page globals; that is a larger change than this
  pass should carry, and the scripts are small (about 50 KB, one origin).
- **The article `image` stays the icon.** There are no article images; a logo
  is a weak `image` but not a false one. Real images are a content opportunity.

## Measurements

MEASUREMENTS_PLACEHOLDER

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
   more than one aspect ratio) would make the article markup complete and
   sharing previews real; the icon is a placeholder.
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

LIVE_PLACEHOLDER
