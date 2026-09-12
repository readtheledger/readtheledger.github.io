# Recurring static standby publishing

The public address remains **https://readtheledger.github.io/**. The owner is still choosing a future name; naming is not a prerequisite for launch/setup work. This change updates the existing `ledger-static-preview` standby, retaining `X-Robots-Tag: noindex, nofollow`. It does not migrate the public site.

## Delivery contract

The existing `pages.yml` push/manual/half-hour schedule gathers once, builds once, checks the site, uploads `github-pages`, and deploys GitHub Pages. Its follow-on job consumes the exact artifact ID from that successful producer job. It does not gather, rebuild, or add another schedule. Workflow-wide `pages` concurrency serializes both jobs. GitHub schedules remain best effort, not an exact freshness guarantee.

Before deployment, `publish.py` validates the canonical repository name and numeric ID, main branch and commit, trusted event, workflow, run/attempt, successful producer job, artifact origin/time/digest, and current main/latest run. Older runs and older reruns are skipped once a later main run exists, even if the later run failed. Run/attempt and main checks are repeated immediately before deployment. A run issued during an upload can cause a brief older standby edition; the shared queue prevents that upload completing after a newer workflow deployment. Do not manually deploy this target concurrently outside that queue.

The archive digest is checked before extracting regular static files. Links, path escapes, duplicate names, private build files, embedded Cloudflare configuration, and oversized archives/assets are rejected. Every source byte is preserved; only the reviewed `_headers` is added. A fresh gathered feed, unchanged story canonicals, stamped service worker and collection-off setting are required. Missing or stale feed evidence fails closed for Cloudflare; GitHub Pages has already deployed under its existing fallback policy.

The prepared file hashes and static-only configuration are checked again before Wrangler. Wrangler 4.131.1 and its dependency lock are committed; Actions are pinned by SHA. Only the final deploy step receives Cloudflare secrets. Wrangler receives no GitHub read token. Raw provider output is withheld. The receipt must identify one version serving 100%, whose version annotation matches the Pages run, attempt, artifact and feed time. This verifies provider deployment evidence; it does not establish public browser behavior.

If an upload/receipt request times out, treat delivery as **uncertain**, inspect the provider receipt, and avoid a blind older-run retry. A newer successful main workflow supplies the next edition. Rerunning only failed jobs can retain an artifact from an earlier attempt; this is intentionally refused. If a rerun is needed, rerun all jobs on current main.

## Secure activation handoff

Review and merge the PR before enabling standby publishing. GitHub Pages continues normally while `CLOUDFLARE_PREVIEW_ENABLED` is absent or false.

1. In the existing Cloudflare account, create a custom API token named `Ledger GitHub static standby`. Grant **Account → Workers Scripts → Edit**, restricted to the single account containing `ledger-static-preview`. This is account-wide Workers permission, not a worker-name restriction. Do not add DNS, zone, KV, R2, AI, billing or all-account access. If that exact scope fails, retain the failure and request review of the specific missing API permission; do not broaden automatically. Configure an appropriate expiry and rotation reminder with the owner.
2. In the canonical repository's [Actions secrets settings](https://github.com/readtheledger/readtheledger.github.io/settings/secrets/actions), install `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` directly through the secure UI. Keep values out of chats, files, terminal output, PRs and logs. Existing local Wrangler OAuth stays local. Never upload its credential file.
3. Read back secret **names only**. Then set repository Actions variable `CLOUDFLARE_PREVIEW_ENABLED` to `true`. That explicit switch separates a merged implementation from an activated integration.
4. Dispatch **Deploy to GitHub Pages** on current main (or observe its next normal run). Verify the successful producer and standby jobs, exact run/artifact digest, feed timestamp, and matching provider version at 100%. Retain the workflow receipt.
5. Independently verify the deployed version's headers, feed, story links, 404 and service-worker update using an authorized public browser path. The earlier preview tests do not validate this publisher. If a reader blocks the preview URL, report the runtime gap; do not bypass that block with another fetch path.

Cloudflare documents [CI token/account-ID authentication](https://developers.cloudflare.com/workers/ci-cd/external-cicd/github-actions/) and [custom token permissions/resource scoping](https://developers.cloudflare.com/fundamentals/api/get-started/create-token/). Actual token-scope sufficiency and end-to-end CI publication remain unproven until the authorized activation run succeeds.

## Tests and rollback

Run `python3 -m unittest discover -s .github/cloudflare -p test_publish.py -v`. The PR workflow has read-only repository permissions and no deployment secrets. The same tests run in the main consumer before artifact preparation. A locked install uses `npm ci --prefix .github/cloudflare --no-audit --no-fund`.

Disable `CLOUDFLARE_PREVIEW_ENABLED` to stop subsequent standby jobs; let any active publisher finish or cancel it and inspect its receipt before recovery. GitHub Pages and its existing news schedule continue. To repair the standby, normally publish a new validated main edition. For an intentional rollback, keep the switch disabled, have root approve a known-good Cloudflare version, record its previous/new version IDs and retained noindex headers, then re-enable after a fresh validation. An old workflow rerun is deliberately not a rollback mechanism. Revert this PR if its workflow changes affect the producer; use the pre-change main commit recorded in the PR as the recovery reference.

## Future address change: requirements only

There is no destination selection, DNS change, redirect release or purchase in this PR. Before any later move, record a reviewed `destination_origin` (HTTPS origin only, no credentials/path/query/fragment), old origin, source commit, artifact, route map and rollback owner. Keep the existing story IDs and paths.

| Surface | Required destination mapping and proof |
| --- | --- |
| Home, sections, `/about/`, `/story/<id>/` | Map each old path to the identical destination path. Test direct visits, trailing slashes, history, share links and the legacy root article hash. Unknown routes keep a real 404. |
| Build metadata | Parameterize `SITE` in `build.mjs` and runtime `index.html` together; verify canonicals, Open Graph, JSON-LD organization/article URLs, sitemap, news sitemap, robots sitemap URLs, Atom IDs/links and share images. Default remains the GitHub origin until release approval. |
| Feed continuity | The existing gatherer already supports `--previous`. After a verified destination edition exists, use `destination_origin + /data/feed.json` for fallback. Keep one gather/schedule and one validated artifact. Test failed-source stale-item retention. |
| GitHub redirect fallback | Prepare an immediate meta-refresh, canonical link and visible continue link for every known HTML page. Preserve query/hash through reviewed JavaScript without creating an open redirect. This is **not HTTP 301**. Do not redirect all stories to the home page. Plan machine-readable feed/sitemap continuity separately. |
| Saved state and installed app | Browser storage is origin-bound. Saved items, read state, theme/size, audio preferences and `ledger-audio` will not transfer automatically. Implement/test a user-controlled export/import or recovery path before a move; exclude `ledger.apikey` and all credentials. Account for an old service worker serving cached pages before redirects, offline readers and installed-app updates. |
| Discovery and indexing | Remove noindex only from an approved production destination. Verify ownership, crawler access, sitemap submission, per-page canonicals and actual response headers. Keep standby noindex. Platform/domain syntax eligibility does not guarantee advertising or search approval. |
| Rollback | Retain the pre-move artifact/version and old route manifest. Define how to restore old-origin content, runtime origin, canonicals, gather fallback and service-worker update behavior. Test reverse redirects for loops before any DNS/redirect release. Preserve old-origin recovery long enough for returning readers. |

Google documents [immediate meta-refresh as a permanent-redirect signal](https://developers.google.com/search/docs/crawling-indexing/301-redirects); GitHub's static fallback must not be described as a server-issued redirect. A future address move is independent of completing current setup at the existing public address.
