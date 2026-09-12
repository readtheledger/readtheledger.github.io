# Editorial review

New Ledger pieces use one of two explicit production categories. The existing
archive has a separate, limited status for missing records. The attribution
line must describe the evidence honestly; this process makes new labels true.

| `produced` | Attribution line | Meaning |
|---|---|---|
| `"reported"` | Reported and written by The Ledger. | A person wrote it from the credited sources. |
| `"assisted"` | Drafted with AI assistance from the credited sources and reviewed by The Ledger's editor before publication. | A model drafted it from the credited sources; a person checked every claim before it went out. |
| `"legacy-unrecorded"` | From The Ledger archive. A factual review record is not available for this article. | The eight original August 17, 2026 articles lack retained factual-review records and have incomplete production evidence. |

The label is set explicitly per piece in `content.js`, never by default.
`production.js` shares validation and attribution between the build and reader.
The build rejects omitted or unsupported values. It also rejects the legacy
category for an ID/date outside the eight pinned originals, or for a new edition
date. This validation cannot verify that a person performed a factual review:
the actual source checks and pull-request record below are still required.

## Existing archive

The legacy inventory is `led-20260817-record`, `led-20260817-fed`,
`led-20260817-consumer`, `led-20260817-river`, `led-20260817-aitrade`,
`led-20260817-badnews`, `led-20260817-savers` and `led-20260817-weekly`, with
their original timestamps pinned in `production.js`. Do not add new articles to
that inventory or reuse its IDs/dates to bypass review. The status is an honest
record limitation, not evidence that nobody reviewed a piece or that it is false.
These editions must not be described as previously approved without evidence.
The attribution correction preserves their reporting, sources and article dates.
A substantive revision follows the full checklist and records its actual review;
the archive status is not a review exemption for new reporting or revisions.

## The loop for an assisted piece

**Fetch → draft → check claims against sources → approve → publish text and audio.**

1. **Fetch.** The day's items come from the gathered Newsstand (`data/feed.json`).
   Each carries its source, its origin (a wire story keeps its wire), an excerpt
   and a link.
2. **Draft.** The model writes the piece into `drafts/YYYY-MM-DD-<slug>.js` as a
   `content.js`-shaped entry with `produced: "assisted"`, and with **every claim
   tied to the item it came from** in the `sources` array. A draft with a claim
   that has no source is not ready for review; send it back.
3. **Check.** A person works through the checklist below, against the sources,
   not against the draft. This is the step that makes the label true. A source
   link and an AI-assistance label are not evidence a claim was checked; the
   record of this step is.
4. **Approve.** The entry moves from `drafts/` into `content.js`. `updated` in
   `content.js` moves to today. The draft file is deleted.
5. **Publish.** The push builds and deploys the page and, when audio is
   enabled, the recording.

Until a draft passes the check, the existing published edition stays visible
with its original date and truthful attribution status. Nothing publishes
straight from a model to the page.

## The checklist

Record the outcome per item in the pull request that moves the piece into
`content.js`. Every box, every edition.

- [ ] **Every factual claim is in a credited source.** Numbers, names, dates,
      quotations, and who-said-what. Open each source; do not take the draft's
      word for it.
- [ ] **Quotations are brief, verbatim and attributed** to the outlet that
      reported them.
- [ ] **Nothing is presented as independently confirmed** when the sources are
      copies of one wire report. Check `origin` on the items used.
- [ ] **No source's article is reproduced.** Summary, at most one short quote,
      and a link out, unless the source's `rights` is `"full"` and the licence
      is named.
- [ ] **Dates are right:** the piece's `date` is today's publication time; the
      events it describes are dated as the sources date them.
- [ ] **`produced` is `"assisted"`** and the attribution line the build prints
      says so (check the built page).
- [ ] **Section and kind** are correct for the front-page mix.
- [ ] **The standfirst and headline match the body** and do not overstate it.
- [ ] **Read the whole thing aloud once** (Listen). Anything that sounds wrong
      usually is.

## When a check fails

Fix the claim from the source, or cut it. If the piece cannot stand without it,
it does not publish today; the previous edition stays up. Note what failed in
the draft's pull request so the drafting instructions can be improved.

## Human-written pieces

A piece a person wrote from the sources explicitly sets `produced: "reported"`.
It goes through the same checklist, with the production-label item checked
against `reported` rather than `assisted`; the label says how it was made.
