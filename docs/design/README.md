# Editorial design: pictures, hierarchy and the phone page

The first design release for The Ledger, built on the search pass
(`da56f78`). The brief was an NYT-inspired editorial feel with The Ledger's
own identity: expressive headlines, relevant original images, clear
attribution, comfortable prose and a visible hierarchy between the lead and
the supporting stories, readable on an iPhone. The two reference screenshots
supplied by the owner were used for composition only; nothing from them is an
asset here.

## Decisions taken at the design checkpoint

- **One renderer.** `media.js` is the single contract and renderer for a
  piece's picture, loaded by the app and run by the build, so the static page
  and the reader produce the same markup and the browser fetches the picture
  once.
- **Caption, credit and disclosure are three fields.** The caption is the
  editorial line and adds no factual claim. The credit names the maker. `ai:
  true` renders a visible **AI-generated illustration** label. The story's
  production label (reported / assisted) is unrelated and unchanged.
- **No crops.** Every picture is its full 3:2 composition at every size,
  including the 112 px thumbnail. Focal points are recorded in the
  manifests and not used.
- **Warm paper stays.** The illustrations were generated on warm ivory; on
  the existing paper their edges dissolve. The near-white surface proposed in
  the plan is deferred to its own decision.
- **Editorial order is untouched.** The lead is still the lead. Pictures
  follow the order; the order does not follow the pictures.

## The image contract

```
image: {
  u: "/assets/editorial/<id>/hero-1200.jpg",   // the JPEG fallback; https or root-relative
  alt: "what is visible",                       // required
  w: 1200, h: 800,                              // the fallback's pixels; required
  caption: "the editorial line",                // optional
  credit: "The Ledger",                         // optional
  ai: true,                                     // optional; renders the disclosure
  widths: [480, 768, 1200]                      // WebP derivatives beside u, hero-<w>.webp
}
```

`media.js` validates it (the build refuses a piece that fails, the app renders
that piece text-led), builds the `srcset`, and sets `sizes` per placement so
the browser downloads what the slot actually renders:

| Placement | `sizes` | Loading |
|---|---|---|
| Story hero (static page and reader) | 684 px in the column, else 100vw | eager, high priority |
| Lead card | the feed column (738 px at 1440, minus the rail at 820 and above, full width below) | eager |
| Feature card (weekly) | as the lead card | lazy |
| Compact thumbnail | 112 px | lazy |

Derivatives are made by `make_derivatives.py` from a master that stays
outside the repository; only the derivatives and a `manifest.json` with the
master's sha256, size, prompt, method and date are committed. Nothing in the
output is larger than 600 KB and the build refuses anything that is.

| Piece | 480 WebP | 768 WebP | 1200 WebP | 1200 JPEG |
|---|---|---|---|---|
| aitrade | 27 KB | 77 KB | 216 KB | 242 KB |
| badnews | 18 KB | 51 KB | 137 KB | 187 KB |
| consumer | 13 KB | 31 KB | 77 KB | 131 KB |
| fed | 32 KB | 92 KB | 251 KB | 275 KB |
| record | 19 KB | 51 KB | 129 KB | 181 KB |
| river | 40 KB | 107 KB | 266 KB | 294 KB |
| savers | 15 KB | 33 KB | 80 KB | 134 KB |
| weekly | 29 KB | 72 KB | 173 KB | 225 KB |

A phone at 2x picks the 1200 px WebP for a hero (80–173 KB for the two
pilot pieces), the 768 for a feature card and the 480 for a thumbnail.

## The article page

Order, on every story: section label (with *From the archive* when the story
is news past a week), headline, deck, picture with its caption and credit,
byline and date and reading time, body, sources, related pieces. Standard
stories keep an upright bold headline; the weekly feature uses the italic
display face and keeps the drop cap. A story without a picture renders the
same order without the figure and is tested that way.

Type at 390 px, regular size: headline 32 px (30–34 across the phone
widths), deck 18.4 px, body 20 px on 32 px leading. All three scale with the
reader's text-size setting. The hero bleeds to the viewport edge on a phone
with the caption on the 18 px gutter; on a desktop it sits in the 684 px
column. The reader reserves more than the Listen dock's height below the
article.

## The front page

Pace, not uniformity: the lead carries its picture above the words on a phone
and beside them from 820 px up, so the headline is on the first screen; the
two stories after it carry a 112 px thumbnail with the summary and meta below
at full width; the rows after that are text-led even though every piece now
has a picture; the *Why it matters* card is unchanged; the weekly feature
carries its picture above an italic headline. Section pages use the same rule.
Saved and search stay as they were.

On a phone a front-page summary is a glimpse, not the deck: the lead's shows
four lines and a supporting story's three, clipped; the headline link and the
article's own deck are whole. Above 820 px the summaries are not clipped.

The archive label the app shows — *From the archive* on a news story more than
a week old, never on analysis or deep work, which carry their date and are not
expired by age — is now written by the build on the static pages too, as of
build time, so the static story and the reader agree. The true dates are
unchanged and shown under the picture.

## The worker's picture cache

Pictures are never precached, so offline text never depends on them. They are
cached on first view in a cache of their own, bounded to 40 (oldest out), and
that cache is scoped to the build like the shell: the build stamp covers the
pictures' bytes, so a replaced picture arrives with a new stamp and the old
cache is dropped on activation. An installed reader cannot keep old artwork
for a piece whose picture changed. The write is attached to the fetch event so
a stopped worker cannot lose it. `qa_media.py` proves the three properties:
the cache is named for the build and holds the hero; 45 pictures leave at most
40; a build in which one picture was replaced gets a new stamp, installs, and
serves the replaced bytes with the old cache gone.

## Evidence

Screenshots in `shots/` (headless Chromium, not a physical phone; the fonts
do not load in the build sandbox, so the fallback serif shows in place of
Playfair and Source Serif): `front-390`, `front-1440`, `record-390`,
`savers-390`, `savers-1440`, `weekly-390`, `weekly-1440`, `markets-390`,
`savers-390-nojs` (JavaScript off), `no-image-390` and `no-image-390-nojs`
(the text-led state, from the test fixture).

`qa_media.py` checks the contract end to end: order of the static and
interactive pages, one figure, one server fetch of the hero across the
handover, caption/credit/disclosure, the lead/thumbnail/feature pace on the
front page, lazy pictures loading on scroll, typography at 390 px and under
the text-size setting, the Listen dock's space, Back and Forward from a
direct story load, Save/Copy/Share, no overflow from 320 to 1440 px, no
master shipped, and the worker's bounded image cache.

Not done here: a physical iPhone Safari check (outstanding; the owner can do
it on the deployed page), and field performance data (none exists for this
origin; lab measurements are in the pull request). The section-page
screenshot shows a *Live feeds unreachable* notice: the build sandbox serves a
stub Newsstand edition with no items and cannot reach the relays; production
serves a gathered edition and the notice does not appear.

## The art

Eight conceptual illustrations, one per piece, generated by Codex with the
prompts recorded in each manifest, reviewed as full compositions. Notes from
inspection before integration: coins appear in three of the eight (savers,
river, aitrade) and a receipt in two (consumer, aitrade), which is worth
varying in the next round; the aitrade chip carries a small engraved brain
motif, which the brief had asked to avoid but is restrained here; nothing
depicts an actual place, person or facility, and no picture carries text.
