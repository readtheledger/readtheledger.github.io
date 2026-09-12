# Measurement contract

The canonical HTTPS site uses **one Cloudflare Web Analytics collector**. Its
owner-controlled property was created for readtheledger.github.io, with manual
JavaScript snippet installation. The public site token is
`e1563ba6decb4bfcae56ce3d7c2d3366`; it is not an account credential. The unused
`GC_SITE` setting stays empty and no GoatCounter requests are emitted. Ads remain off.

## What is measured

The exact provider module at
`https://static.cloudflareinsights.com/beacon.min.js` loads once per eligible
document. Cloudflare handles its initial page load, browser navigation and
performance reports. The Ledger emits **no manual page events** on top of it.
The app restores a direct story/About route before the module executes, avoiding
an extra home-page count during that internal restoration.

The provider chooses a supported native navigation mechanism. Its documented
fallback uses History API pushState/popstate; some browsers also observe
replaceState through the Navigation API. Reader navigation, Back, Forward and
reload were checked against the actual September 12 provider script. They each
produced one page-load event per tested transition. Performance events are
separate requests, not extra pageviews.

This changes the old, unactivated adapter's proposed count model. There are no
synthetic `/newsstand/reader/` or `/saved/` analytics labels. App-only/query
views can share a reported pathname; native navigation may count query-only
changes while stripping the query from the reported address. Browsers using
the History fallback can miss replaceState-only section changes. Do not treat
these counts as complete click-through, unique-person or returning-reader
measurements. Search, menu and other interaction funnels are not implemented.

## Exclude this browser

Menu → About The Ledger → **Exclude my visits** saves
`ledger.analytics.exclude=1` in local storage. The older `skipgc=t` choice
is also honored. Apply the choice separately in each browser/profile; clearing
site storage clears it.

Before loading the provider, the adapter checks the choice, the exact canonical
origin, HTTPS, frame/prerender state and recognized automation indicators.
Local and alternate preview/standby hosts never load it, even though the same
artifact is deployed there. A noindex meta tag also blocks it. WebDriver and
common automation user agents are excluded, without claiming exhaustive bot
detection. JavaScript-off pages make no analytics requests.

The adapter installs send-time guards before loading Cloudflare. XHR,
sendBeacon and fetch directed to Cloudflare's collector recheck storage before
sending. Other network destinations retain native behavior. Opt-out aborts
tracked pending XHR/fetch requests and reloads the document to tear down
provider listeners; removing a script element alone would not do that.
Unload requests are blocked during that reload. Other tabs observe the saved
choice, and their sends check storage even before their storage event arrives.
Already-sent requests cannot be recalled. A restored cached document rechecks
the exclusion too.

If reading/writing the preference fails, measurement fails closed in that
document. A failed write cannot guarantee persistence across reloads; the UI
says so and keeps the current document blocked without forcing a reload.
Unchecking a saved exclusion does not itself load the beacon; a subsequent
navigation can start it. Re-enabling after a failed write in an already-stopped
document requires a reload to establish a fresh provider lifecycle.
Failure to install the transport guards prevents beacon loading. A failed
provider load is not retried in that document and never blocks reading.

## Data and security boundaries

The provider sends sanitized page/referring addresses, browser information and
loading/performance measurements. Its reviewed code strips query strings,
fragments and URL credentials from its location/referrer fields. Referring
paths are now available to this collector; the old pixel's no-referrer payload
contract no longer applies. The Ledger does not pass search text, saved items,
article text or the user's speech key to the collector. Ordinary connection
metadata is visible to the service. Cloudflare states it uses no tracking
cookies or persistent visitor identity for Web Analytics.

CSP retains its previous restrictions, adding only the exact module URL to
script-src and `https://cloudflareinsights.com/cdn-cgi/rum` to connect-src.
No unsafe-eval, broad wildcard, new advertising script or credential is added.
The external module is provider-managed and can change; it executes in the
page's origin context. Future provider behavior is a trust boundary, not a
guarantee derived from this one script snapshot.

The publisher validates the expected property and inactive GoatCounter setting
on every content head, rejects an unguarded inline beacon installation, and
compares the artifact's adapter to the reviewed checkout. Existing provenance,
archive, artifact digest, gather and static/noindex protections remain in force.

## Verification and measurement start

`python qa_analytics.py --beacon <reviewed-local-beacon.js>` builds the site and
serves both the site and the real provider module through local Playwright
interception. **Every request is locally fulfilled or aborted.** No events
reach the public site, Cloudflare collector or advertisers. The JSON report
records the provider script SHA256. Chromium's native-navigation and History
fallback paths are both checked, along with exclusions, storage errors,
cross-tab choice, provider failure and protected transports. Prerender is a
simulated lifecycle check; this is not physical-device certification.

Deployment and locally observed requests are not proof of dashboard receipt.
The owner must verify the property's receipt, displayed units, time window
and test traffic before setting a clean measurement start. No synthetic test
traffic is growth, earnings or a real readership baseline.

Sources checked September 12, 2026:
[setup](https://developers.cloudflare.com/web-analytics/get-started/),
[SPA navigation](https://developers.cloudflare.com/web-analytics/get-started/web-analytics-spa/),
[service description](https://developers.cloudflare.com/web-analytics/about/),
[CSP destinations](https://developers.cloudflare.com/fundamentals/reference/policies-compliances/content-security-policies/),
[data and query-string limits](https://developers.cloudflare.com/web-analytics/faq/).
