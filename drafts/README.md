# Drafts

Pieces waiting for review live here, one file each, named
`YYYY-MM-DD-<slug>.js`. A draft is a `content.js`-shaped entry:

```js
// drafts/2026-09-09-briefing.js
({
  id: "led-20260909-briefing",
  kind: "news", section: "Markets",
  produced: "assisted",
  date: null,
  title: "…",
  standfirst: "…",
  html: `<p>…</p>`,
  sources: [ {t: "…", u: "https://…", p: "Publisher"} ]
})
```

Nothing in this folder is published. The build reads only `content.js`. A draft
moves into `content.js` when it has passed the checklist in `REVIEW.md`, and the
pull request that moves it records the outcome of every item on that checklist.

Keep `date: null` while a draft is private. Replace it with the actual UTC
first-publication time only after the final exact text passes its recorded review;
the production build rejects a null date.

Every new entry must explicitly set `produced: "assisted"`, `"reported"`, or
`"ai-source-reviewed"`, matching how it was made. The first two retain their
actual human source-check and read-aloud requirements. The third requires the
recorded root-AI and Claude claim/source checks in `REVIEW.md` and explicitly
claims no human factual review. A category or boolean is not evidence of review.
`legacy-unrecorded` is reserved for the eight pinned August 17 archive articles,
not for new drafts, unreviewed revisions or reused archive IDs. Omitted and
unsupported production values stop the build.
