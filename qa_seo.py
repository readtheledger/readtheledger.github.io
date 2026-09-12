"""SEO pass: what a crawler and a reader without JavaScript are served, and what
the app does to those signals once it boots. Builds the site from a fixture
edition (one piece published an hour before the build, one three days before,
one ten days before, four desks with nothing yet) as of a fixed clock, serves it
the way GitHub Pages does, and checks headings, titles and descriptions,
canonicals, robots meta and robots.txt, sitemaps (including the 48-hour news
sitemap), the Atom feed, structured data, the About page, the related links,
the skip link, and that an app-only view is noindex with a canonical of its
own while a built page keeps the values the build wrote.

    python3 qa_seo.py            # needs playwright (chromium) and node
"""
import asyncio, http.server, socketserver, threading, os, sys, json, subprocess, re, urllib.parse, tempfile, shutil
import xml.etree.ElementTree as ET
from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = 8941
NOW = "2026-09-12T12:00:00Z"
SITE_URL = "https://readtheledger.github.io"
PAGE_SECTIONS = ["Markets","Companies","Economics","Central Banks","Opinion","Tech & Finance","Personal Finance"]
def slug(s): return re.sub(r"^-|-$", "", re.sub(r"[^a-z0-9]+", "-", s.lower().replace("&", "and")))

ARTS = [
  {"id":"seo-fresh",  "kind":"news",     "section":"Markets",   "date":"2026-09-12T11:00:00Z", "title":"A fresh piece, an hour old",  "standfirst":"Published within the news window."},
  {"id":"seo-recent", "kind":"analysis", "section":"Economics", "date":"2026-09-09T09:00:00Z", "title":"A recent analysis, three days old", "standfirst":"Outside the news window, inside the archive threshold.",
   "image":{"u":"https://example.com/photos/recent-1600x900.jpg","alt":"A chart of the thing the piece is about","w":1600,"h":900,"caption":"The chart. Source: Example."}},
  {"id":"seo-old",    "kind":"news",     "section":"Markets",   "date":"2026-09-02T09:00:00Z", "title":"An older story, ten days old", "standfirst":"From the archive."},
]
def content_js():
    arts = []
    for a in ARTS:
        arts.append(json.dumps(dict(a, html="<p>First paragraph of %s.</p><h2>A subheading</h2><p>Second paragraph.</p>" % a["id"],
                                     sources=[{"t":"A source","u":"https://example.com/s","p":"Example"}])))
    return "window.LEDGER_CONTENT = {updated:\"2026-09-12\", articles:[" + ",".join(arts) + "]};"

STATE = {"root": None}
TYPES = {".html":"text/html; charset=utf-8", ".js":"text/javascript; charset=utf-8", ".json":"application/json",
         ".webmanifest":"application/manifest+json", ".png":"image/png", ".xml":"application/xml; charset=utf-8", ".txt":"text/plain; charset=utf-8"}
class Pages(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        root = STATE["root"]; p = urllib.parse.urlparse(self.path).path
        fp = os.path.normpath(os.path.join(root, p.lstrip("/")))
        if os.path.isdir(fp):
            if not p.endswith("/"): self.send_response(301); self.send_header("Location", p + "/"); self.end_headers(); return
            fp = os.path.join(fp, "index.html")
        if not fp.startswith(root) or not os.path.isfile(fp):
            body = open(os.path.join(root, "404.html"), "rb").read()
            self.send_response(404); self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body); return
        body = open(fp, "rb").read()
        self.send_response(200); self.send_header("Content-Type", TYPES.get(os.path.splitext(fp)[1], "application/octet-stream"))
        self.send_header("Cache-Control", "no-store"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
def serve():
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("127.0.0.1", PORT), Pages) as s: s.serve_forever()

R = []
def ok(name, cond, note=""):
    R.append(("PASS" if cond else "FAIL", name, note)); print(("PASS " if cond else "FAIL ") + name + (("  — " + str(note)) if (note and not cond) else ""))

def lds(html):
    return [json.loads(m) for m in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)]

async def main():
    work = tempfile.mkdtemp(prefix="ledger-seo-"); site = os.path.join(work, "site")
    cf = os.path.join(work, "content.js"); open(cf, "w").write(content_js())
    r = subprocess.run(["node", os.path.join(ROOT, "build.mjs"), site, "--content", cf, "--now", NOW], capture_output=True, text=True)
    if r.returncode: print(r.stdout, r.stderr); sys.exit("build failed")
    print(r.stdout.strip())
    STATE["root"] = site
    threading.Thread(target=serve, daemon=True).start()
    base = f"http://127.0.0.1:{PORT}"
    rd = lambda *p: open(os.path.join(site, *p), encoding="utf-8").read()

    # ---- files a crawler reads
    robots = rd("robots.txt")
    ok("robots.txt blocks nothing and names both sitemaps",
       "Disallow" not in robots and f"Sitemap: {SITE_URL}/sitemap.xml" in robots and f"Sitemap: {SITE_URL}/sitemap-news.xml" in robots, robots)
    sm = ET.parse(os.path.join(site, "sitemap.xml")).getroot(); ns = {"s":"http://www.sitemaps.org/schemas/sitemap/0.9", "n":"http://www.google.com/schemas/sitemap-news/0.9"}
    locs = [u.find("s:loc", ns).text for u in sm.findall("s:url", ns)]
    ok("sitemap: front page, sections with stories, every story, About; no empty section",
       f"{SITE_URL}/" in locs and f"{SITE_URL}/about/" in locs and all(f"{SITE_URL}/story/{a['id']}/" in locs for a in ARTS)
       and f"{SITE_URL}/markets/" in locs and f"{SITE_URL}/economics/" in locs and f"{SITE_URL}/companies/" not in locs, locs)
    about_url = [u for u in sm.findall("s:url", ns) if u.find("s:loc", ns).text.endswith("/about/")][0]
    ok("sitemap: the About page carries no lastmod (it has no date)", about_url.find("s:lastmod", ns) is None)
    nsm = ET.parse(os.path.join(site, "sitemap-news.xml")).getroot()
    nlocs = [u.find("s:loc", ns).text for u in nsm.findall("s:url", ns)]
    ok("news sitemap lists only the piece published within 48 hours of the build", nlocs == [f"{SITE_URL}/story/seo-fresh/"], nlocs)
    ok("news sitemap names the publication, language, date and title",
       nsm.find(".//n:publication/n:name", ns).text == "The Ledger" and nsm.find(".//n:publication/n:language", ns).text == "en"
       and nsm.find(".//n:publication_date", ns).text == "2026-09-12T11:00:00Z" and nsm.find(".//n:title", ns).text == ARTS[0]["title"])
    r2 = subprocess.run(["node", os.path.join(ROOT, "build.mjs"), site + "-later", "--content", cf, "--now", "2026-09-20T12:00:00Z"], capture_output=True, text=True)
    later = ET.parse(os.path.join(site + "-later", "sitemap-news.xml")).getroot()
    ok("news sitemap is empty once nothing is within 48 hours (an archive does not qualify)", r2.returncode == 0 and later.findall("s:url", ns) == [])
    feed = ET.parse(os.path.join(site, "feed.xml")).getroot(); A = {"a":"http://www.w3.org/2005/Atom"}
    entries = feed.findall("a:entry", A)
    ok("Atom feed carries every piece with its address, dates, section and full text",
       len(entries) == len(ARTS) and [e.find("a:id", A).text for e in entries] == [f"{SITE_URL}/story/{a['id']}/" for a in ARTS]
       and all(e.find("a:published", A).text.startswith(a["date"][:19]) for e, a in zip(entries, ARTS))
       and all("<p>First paragraph" in e.find("a:content", A).text for e in entries)
       and [e.find("a:category", A).get("term") for e in entries] == [a["section"] for a in ARTS])
    ok("feed's own updated time is the newest piece", feed.find("a:updated", A).text.startswith("2026-09-12T11:00:00"))
    sw = rd("sw.js")
    ok("worker precaches about.js and can render /about/ offline", '"/about.js"' in sw and '"/about/"' in re.search(r"^const ROUTES = (.*);$", sw, re.M).group(1))

    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        # ---- with JavaScript off: what a crawler that does not render sees
        ctx = await b.new_context(java_script_enabled=False, viewport={"width":390,"height":844})
        page = await ctx.new_page()
        async def heads(): return await page.evaluate("[...document.querySelectorAll('h1,h2,h3,h4')].filter(h=>h.closest('#static')||h.closest('.masthead')).map(h=>[+h.tagName[1], h.textContent.trim().slice(0,40)])")
        def in_order(hs):
            prev = 0
            for lvl, _ in hs:
                if lvl > prev + 1: return False
                prev = lvl
            return True
        await page.goto(base + "/")
        h1 = await page.evaluate("[...document.querySelectorAll('h1')].map(h=>h.textContent.trim())")
        ok("front page: exactly one h1, the site's title", h1 == ["The Ledger — Finance, read properly"], h1)
        ok("front page: headings in order, stories as h2", in_order(await heads()) and (await page.locator("#static h2.hl").count()) == len(ARTS) + 1, await heads())
        ok("front page: skip link is the first thing in the body and targets main",
           await page.evaluate("document.body.firstElementChild.matches('a.skip[href=\"#main\"]') && !!document.getElementById('main')"))
        ok("front page: About card links to /about/ and says it has no date",
           await page.evaluate("(()=>{const c=document.querySelector('#static article.card.about');return !!c && c.querySelector('h2 a').getAttribute('href')==='/about/' && /no date/.test(c.textContent)})()"))
        html = rd("index.html"); L = lds(html)
        ok("front page: WebSite and Organization structured data, publisher with logo and repository",
           [d["@type"] for d in L] == ["WebSite", "Organization"] and L[1]["logo"]["url"].endswith("/icon-512.png") and any("github.com/readtheledger" in s for s in L[1]["sameAs"]))
        ok("front page: description names what the publication is", 100 < len(re.search(r'name="description" content="([^"]*)"', html).group(1)) < 170)
        ok("every page links the Atom feed", all('type="application/atom+xml"' in rd(*p) for p in [("index.html",), ("markets","index.html"), ("story","seo-fresh","index.html"), ("about","index.html")]))
        ok("fonts stylesheet does not block first paint and has a no-script fallback",
           re.search(r'<link href="https://fonts.googleapis.com[^>]*media="print" onload="this.media=\'all\'">', html) is not None and "<noscript><link href=\"https://fonts.googleapis.com" in html)
        ok("fonts request only the weights the stylesheet uses", "Playfair+Display:ital,wght@0,700;0,800;1,500" in html and "Inter:wght@400;600;700&" in html)

        await page.goto(base + "/markets/")
        hs = await heads()
        ok("section page: h1 is the section, with a count, headings in order", hs[0] == [1, "Markets"] and in_order(hs) and "2 stories" in await page.locator("#static .viewnote").text_content(), hs)
        html = rd("markets", "index.html"); L = lds(html)
        ok("section page: CollectionPage listing its pieces and a two-step breadcrumb",
           L[0]["@type"] == "CollectionPage" and len(L[0]["hasPart"]) == 2 and L[1]["@type"] == "BreadcrumbList"
           and [i["name"] for i in L[1]["itemListElement"]] == ["The Ledger", "Markets"] and L[1]["itemListElement"][1]["item"] == f"{SITE_URL}/markets/")
        desc = re.search(r'name="description" content="([^"]*)"', html).group(1)
        ok("section page: description states the count and the latest piece", desc.startswith("2 original pieces") and ARTS[0]["title"] in desc, desc)
        ok("section page: indexable", 'id="robotsMeta" content="index,follow"' in html)

        await page.goto(base + "/companies/")
        html = rd("companies", "index.html"); hs = await heads()
        ok("empty section: served, noindex,follow, one h1 and an h2 notice, still linked from the nav",
           'id="robotsMeta" content="noindex,follow"' in html and hs[0] == [1, "Companies"] and in_order(hs)
           and await page.locator("#static .notice h2").count() == 1 and await page.locator('#static .static-nav a[href="/companies/"]').count() == 1, hs)
        ok("empty section: description says so, no fabricated content", "has not published in Companies yet" in re.search(r'name="description" content="([^"]*)"', html).group(1))

        await page.goto(base + "/story/seo-fresh/")
        hs = await heads()
        ok("story page: h1 is the headline, body h2, sources and related as h2 — in order", hs[0] == [1, ARTS[0]["title"]] and in_order(hs) and [2, "Sources & further reading"] in hs, hs)
        rel = await page.evaluate("[...document.querySelectorAll('#static nav.related a')].map(a=>a.getAttribute('href'))")
        ok("story page: related links to the other pieces, same desk first, never itself", rel == ["/story/seo-old/", "/story/seo-recent/"], rel)
        html = rd("story", "seo-fresh", "index.html"); L = lds(html)
        ok("story page: NewsArticle with a three-step breadcrumb Home › Section › Story",
           L[0]["@type"] == "NewsArticle" and L[0]["datePublished"] == ARTS[0]["date"] and L[0]["dateModified"] == ARTS[0]["date"]
           and L[0]["author"]["@type"] == "Organization" and L[1]["@type"] == "BreadcrumbList"
           and [i["name"] for i in L[1]["itemListElement"]] == ["The Ledger", "Markets", ARTS[0]["title"]]
           and [i["item"] for i in L[1]["itemListElement"]] == [f"{SITE_URL}/", f"{SITE_URL}/markets/", f"{SITE_URL}/story/seo-fresh/"])
        ok("story page: no author is invented (the organisation is the author, no person named)", "Person" not in json.dumps(L))
        ok("story page without an image of its own carries no NewsArticle image (the logo is not one); sharing preview is the icon",
           "image" not in L[0] and 'property="og:image" content="https://readtheledger.github.io/icon-512.png"' in html and 'twitter:card" content="summary"' in html)
        html2 = rd("story", "seo-recent", "index.html"); L2 = lds(html2)
        await page.goto(base + "/story/seo-recent/")
        ok("story page with an image of its own: NewsArticle.image is that image, with its size; sharing preview uses it; the page shows it",
           L2[0]["image"][0]["url"] == "https://example.com/photos/recent-1600x900.jpg" and L2[0]["image"][0]["width"] == 1600
           and 'property="og:image" content="https://example.com/photos/recent-1600x900.jpg"' in html2 and 'twitter:card" content="summary_large_image"' in html2
           and await page.evaluate("(()=>{const f=document.querySelector('#static figure.fig img');return !!f && f.alt.startsWith('A chart') && f.getAttribute('width')==='1600'})()"))
        bad = os.path.join(work, "bad.js"); open(bad, "w").write(content_js().replace("https://example.com/photos/recent-1600x900.jpg", "https://readtheledger.github.io/icon-512.png"))
        rb = subprocess.run(["node", os.path.join(ROOT, "build.mjs"), site + "-bad", "--content", bad, "--now", NOW], capture_output=True, text=True)
        ok("the build refuses the site icon as a piece's image", rb.returncode == 1 and "the site icon is not a piece's image" in rb.stdout + rb.stderr)

        r = await page.goto(base + "/about/")
        hs = await heads(); html = rd("about", "index.html"); L = lds(html)
        ok("About page: served at /about/, h1 is its title, headings in order", r.status == 200 and hs[0][0] == 1 and hs[0][1].startswith("About The Ledger") and in_order(hs), hs)
        ok("About page: canonical, indexable, AboutPage with the organisation as its subject and a breadcrumb",
           f'<link rel="canonical" href="{SITE_URL}/about/">' in html and 'content="index,follow"' in html
           and L[0]["@type"] == "AboutPage" and L[0]["mainEntity"]["@type"] == "Organization" and L[1]["@type"] == "BreadcrumbList")
        ok("About page: the schedule is a target, the labels are the standard rather than a review record, and every data flow is named",
           await page.evaluate("(()=>{const t=document.querySelector('#static').textContent;return /target is a fresh gathering every half hour/.test(t) && /sometimes delayed by hours/.test(t) && /intended editorial standard/.test(t) && /What leaves your device/.test(t) && /OpenAI/.test(t) && /relay/.test(t) && /GoatCounter/.test(t)})()"))
        ok("About page: says it has no date and where corrections go, names no person",
           await page.evaluate("(()=>{const t=document.querySelector('#static').textContent;return /no date/.test(t) && /Corrections and contact/.test(t) && /github\\.com\\/readtheledger/.test(t)})()")
           and await page.locator('#static .static-nav a[href="/about/"][aria-current="page"]').count() == 1)
        r = await page.goto(base + "/story/no-such-story/")
        ok("unknown story is a 404 that links the front page and About", r.status == 404 and await page.locator('a[href="/about/"]').count() == 1 and await page.locator('a[href="/"]').count() >= 1)
        await ctx.close()

        # ---- with JavaScript on: the app must keep the build's signals honest
        ctx = await b.new_context(viewport={"width":390,"height":844}, is_mobile=True, has_touch=True)
        page = await ctx.new_page()
        await page.goto(base + "/", wait_until="load"); await page.wait_for_selector("#feed article.card")
        robots = lambda: page.evaluate("document.querySelector('#robotsMeta').content")
        canon = lambda: page.evaluate("document.querySelector('link[rel=canonical]').href")
        ok("app on the front page keeps index,follow and the front page canonical", await robots() == "index,follow" and await canon() == f"{SITE_URL}/")
        await page.goto(base + "/?view=newsstand", wait_until="load"); await page.wait_for_selector("#feed")
        ok("Newsstand view is noindex with a canonical of its own, not the front page's",
           await robots() == "noindex,follow" and await canon() == f"{base}/?view=newsstand", (await robots(), await canon()))
        await page.click('#secnav a[data-sec="Front page"]'); await page.wait_for_timeout(300)
        ok("back on the front page the build's values return", await robots() == "index,follow" and await canon() == f"{SITE_URL}/")
        await page.goto(base + "/?q=piece", wait_until="load"); await page.wait_for_timeout(400)
        ok("a search is noindex with its own canonical", await robots() == "noindex,follow" and await canon() == f"{base}/?q=piece", (await robots(), await canon()))
        await page.goto(base + "/companies/", wait_until="load"); await page.wait_for_timeout(400)
        ok("app on an empty section keeps the build's noindex,follow", await robots() == "noindex,follow" and await canon() == f"{SITE_URL}/companies/", (await robots(), await canon()))

        await page.goto(base + "/about/", wait_until="load"); await page.wait_for_selector("#reader.on")
        ok("app on /about/ opens the About page in the reader, at /about/, titled",
           (await page.evaluate("document.querySelector('#rwrap h1').textContent")).startswith("About The Ledger")
           and await page.evaluate("location.pathname") == "/about/" and await page.title() == "About — The Ledger")
        await page.keyboard.press("Escape"); await page.wait_for_timeout(400)
        ok("Escape leaves the About page for the front page", await page.evaluate("location.pathname") == "/" and not await page.evaluate("document.querySelector('#reader').classList.contains('on')"))
        await page.click("#btnMenu"); await page.wait_for_selector("#menu.on")
        ok("the menu has an About link, outside the topic list", await page.locator("#menuTopics a").count() == 10 and await page.get_attribute("#menuAbout", "href") == "/about/")
        await page.click("#menuAbout"); await page.wait_for_selector("#reader.on")
        ok("the menu's About link opens the About page at /about/", await page.evaluate("location.pathname") == "/about/")
        await page.keyboard.press("Escape"); await page.wait_for_timeout(400)
        about_card = page.locator("#feed article.card.about")
        await about_card.click(); await page.wait_for_selector("#reader.on")
        ok("the About card opens the About page at /about/, with no date", await page.evaluate("location.pathname") == "/about/"
           and "no publication date" in await page.evaluate("document.querySelector('#rwrap .attrline').textContent"))
        await page.keyboard.press("Escape"); await page.wait_for_timeout(400)
        await page.goto(base + "/", wait_until="load"); await page.wait_for_selector("#feed article.card")
        await page.keyboard.press("Tab")
        ok("Tab first reaches the skip link, which becomes visible",
           await page.evaluate("document.activeElement.matches('a.skip') && document.activeElement.getBoundingClientRect().top >= 0"))
        await page.keyboard.press("Enter"); await page.wait_for_timeout(200)
        ok("the skip link moves focus into main", await page.evaluate("document.activeElement.id === 'main' || document.activeElement.closest('main') !== null"))
        ok("badge text meets 4.5:1 on paper in light mode",
           await page.evaluate("getComputedStyle(document.querySelector('#feed .badge')).color") == "rgb(10, 98, 107)")
        await ctx.close(); await b.close()
    shutil.rmtree(work, ignore_errors=True)

asyncio.run(main())
fails = [r for r in R if r[0] == "FAIL"]
print(f"\n{len(R) - len(fails)}/{len(R)} passed")
sys.exit(1 if fails else 0)
