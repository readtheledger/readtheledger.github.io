#!/bin/sh
# Checks a built site (the _site folder build.mjs writes) is complete enough to
# publish. The Pages workflow runs this on the artifact it is about to deploy,
# and qa_pages.py runs the very same script on its own build — so the check the
# deploy relies on is the check the tests exercise.
#
#   sh check_site.sh _site
#
# Exit status 0 when everything is present, 1 with a MISSING line per problem.

dir="${1:-_site}"
missing=0
say() { echo "$1"; missing=1; }

[ -d "$dir" ] || { echo "MISSING: $dir is not a directory"; exit 1; }

# the files the installed app precaches, and the files this release publishes
for f in index.html content.js sources.js topics.js context.js about.js analytics.js media.js production.js sw.js manifest.webmanifest \
         icon-180.png icon-192.png icon-512.png icon-maskable-512.png \
         sitemap.xml sitemap-news.xml feed.xml robots.txt 404.html about/index.html .nojekyll; do
  [ -f "$dir/$f" ] || say "MISSING from $dir: $f"
done

# at least one story page, and every story page has its own canonical address
stories=$(find "$dir/story" -name index.html 2>/dev/null | wc -l | tr -d ' ')
echo "story pages: $stories"
[ "$stories" -ge 1 ] || say "MISSING: no story pages were generated"
for p in $(find "$dir/story" -name index.html 2>/dev/null); do
  id=$(basename "$(dirname "$p")")
  grep -q "<link rel=\"canonical\" href=\"https://readtheledger.github.io/story/$id/\">" "$p" \
    || say "MISSING: canonical address in story/$id/index.html"
done

# the service worker must carry the build's stamp — the cache name itself is
# assembled at runtime, so the stamped declaration is what can be checked — and
# the list of addresses the app can render offline
grep -Eq '^const BUILD = "[0-9a-f]{8}";' "$dir/sw.js" \
  || say "MISSING: sw.js was not stamped by the build (const BUILD)"
grep -Eq '^const ROUTES = \[.*"/story/[^"]+/".*\];' "$dir/sw.js" \
  || say "MISSING: sw.js does not carry the build's route list (const ROUTES)"

# the gathered Newsstand, when there is one, must be an edition the app can read
if [ -f "$dir/data/feed.json" ]; then
  python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert d["fetched"] and isinstance(d["items"],list) and isinstance(d["sources"],list); print("newsstand: %d items, gathered %s" % (len(d["items"]), d["fetched"]))' "$dir/data/feed.json" \
    || say "MISSING: data/feed.json is not an edition the app can read"
else
  echo "newsstand: no data/feed.json in $dir (the app will gather in the browser)"
fi

# every page in the sitemap exists in the output
for loc in $(grep -o '<loc>[^<]*</loc>' "$dir/sitemap.xml" 2>/dev/null | sed 's|<loc>https://readtheledger.github.io||; s|</loc>||'); do
  [ -f "$dir${loc}index.html" ] || say "MISSING: sitemap names $loc but $dir${loc}index.html does not exist"
done

[ "$missing" -eq 0 ] && echo "artifact check: ok ($dir)"
exit "$missing"
