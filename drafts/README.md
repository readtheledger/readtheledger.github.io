# Drafts

Pieces waiting for review live here, one file each, named
`YYYY-MM-DD-<slug>.js`. A draft is a `content.js`-shaped entry:

```js
// drafts/2026-09-09-briefing.js
({
  id: "led-20260909-briefing",
  kind: "news", section: "Markets",
  produced: "assisted",
  date: "2026-09-09T06:00:00Z",
  title: "…",
  standfirst: "…",
  html: `<p>…</p>`,
  sources: [ {t: "…", u: "https://…", p: "Publisher"} ]
})
```

Nothing in this folder is published. The build reads only `content.js`. A draft
moves into `content.js` when it has passed the checklist in `REVIEW.md`, and the
pull request that moves it records the outcome of every item on that checklist.
