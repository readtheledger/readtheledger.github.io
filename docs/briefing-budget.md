# Daily Briefing — budget for approval

Release 3 of the roadmap is gated on this document being approved by the owner
before any drafting starts. Nothing here is spent until it is. Every figure is an
estimate from the stated assumptions; the unit prices are list prices as of the
date given and must be re-checked on the day of approval.

## What one edition involves

| Step | What happens | Who or what does it |
|---|---|---|
| Fetch | The gathered Newsstand (`data/feed.json`) supplies the day's items: title, source, origin, excerpt, link | `fetch_feeds.mjs`, already running every half hour |
| Draft | A model writes a short briefing from the top items, with every claim tied to the item it came from | Claude API, one request per edition |
| Check | A person reads the draft against its sources: facts, attribution, dates, labels | Owner or editor, per edition |
| Approve | The draft moves from `drafts/` into `content.js` with `produced: "assisted"` | Owner or editor |
| Publish | The build writes the page and the audio; the deploy puts both live | `build.mjs` and the Pages workflow |

Until a draft passes the check, the previously approved edition stays visible with
its original date.

## Assumptions (change these and the totals change)

| Assumption | Value |
|---|---|
| Editions per month | 30 |
| Items handed to the model per edition | 40 (title, source, origin, ~120-word excerpt, link) |
| Input per request | ~10,000 tokens (≈ 8,000 for the items, ≈ 2,000 for the standing instructions) |
| Output per request | ~1,200 tokens (a 700-word briefing plus a source list) |
| Retry allowance | 1.5× (a second attempt on roughly half of days: a refusal, a bad draft, a re-run after edits) |
| Audio per edition | ~4,200 characters (700 words) |
| Review time per edition | 20–30 minutes |

## Text generation

List prices from the Claude API pricing table cached 2026-06-24 (first-party API;
verify at the Anthropic pricing page before approving).

| Model | Input $/1M | Output $/1M | Per edition (10k in, 1.2k out) | With 1.5× retries | Per month |
|---|---|---|---|---|---|
| Claude Opus 5 (`claude-opus-5`) — recommended | $5.00 | $25.00 | $0.080 | $0.120 | **≈ $3.60** |
| Claude Sonnet 5 (`claude-sonnet-5`) — alternative | $2.00 | $10.00 | $0.032 | $0.048 | ≈ $1.44 |

Opus 5 is the recommended default for the drafting step: the task is judgment
about which items matter and how to state them carefully, and the whole month
costs less than a sandwich either way. Sonnet 5 is listed so the choice is a
decision, not an omission. Prompt caching of the standing instructions would
reduce the input cost further and is not counted.

## Audio

The app already prices OpenAI speech at $0.012 per 1,000 characters for
`gpt-4o-mini-tts` (the figure in `index.html`'s cost hint; verify against
OpenAI's current pricing before approving).

| Item | Characters | Per edition | Per month |
|---|---|---|---|
| Daily briefing audio | ~4,200 | ≈ $0.05 | **≈ $1.50** |
| One-off: recordings for the 8 existing originals | ~8 × 6,000 | — | ≈ $0.60 once |

Audio is generated once in the build from a repository secret and published as a
file; readers are not asked for a key.

## Services and compute

| Item | Cost |
|---|---|
| GitHub Actions minutes | $0 — the repository is public; the half-hourly gathering already runs on that basis. A daily briefing adds one short job. |
| Newsletter (deferred; a later release) | $0 on a free tier while the list is small; check the provider's current tier limits when the time comes |
| Repository secrets | An Anthropic API key and an OpenAI API key, added by the owner in Settings → Secrets → Actions |

## Human review

| Item | Per edition | Per month |
|---|---|---|
| Reading the draft against its sources, checking dates and labels, approving | 20–30 min | 10–15 hours |

This is the largest line by far, and it is the one that cannot be automated
without breaking the plan's rule that a source link and an AI label are not
evidence a claim was checked. If 20–30 minutes a day is not available, the
briefing should run fewer days a week rather than skip the check.

## Totals

| | Per month |
|---|---|
| Text (Opus 5, with retries) | ≈ $3.60 |
| Audio | ≈ $1.50 |
| Services | $0 |
| **Money** | **≈ $5 a month, plus ≈ $0.60 once** |
| **Time** | **10–15 hours a month of review** |

## Approval

- [ ] Assumptions above accepted or amended
- [ ] Model chosen: Opus 5 / Sonnet 5
- [ ] Unit prices re-checked on the day
- [ ] Review time committed (days per week: ___)
- [ ] Secrets added to the repository
- Approved by: ________  Date: ________
