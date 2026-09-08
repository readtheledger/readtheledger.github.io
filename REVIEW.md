# Editorial review

The Ledger publishes two kinds of piece, and the attribution line on each says
which it is. That line has to be true, so this is the process that makes it true.

| `produced` | Attribution line | Meaning |
|---|---|---|
| `"reported"` (the default) | Reported and written by The Ledger. | A person wrote it from the credited sources. |
| `"assisted"` | Drafted with AI assistance from the credited sources and reviewed by The Ledger's editor before publication. | A model drafted it from the credited sources; a person checked every claim before it went out. |

The label is set per piece in `content.js`, never by default. `build.mjs` refuses
any other value.

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

Until a draft passes the check, the previously approved edition stays visible
with its original date. Nothing publishes straight from a model to the page.

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

A piece a person wrote from the sources keeps `produced: "reported"` (or omits
it). It goes through the same checklist; the label simply says how it was made.
