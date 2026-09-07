"""Third QA pass: the pages. Builds the site with build.mjs, serves the output the
way GitHub Pages does (directories to index.html, unknown paths to 404.html with
a 404 status), and checks that every Ledger story and section has an address of
its own that works in a fresh browser, after a refresh, and with JavaScript off;
that sharing, bookmarks, audio and back navigation still work from those
addresses with JavaScript on; that the service worker caches pages by their
addresses, lets a real 404 through while online, and upgrades cleanly from the
previously released service worker (the one installed readers have now)."""
import asyncio, http.server, socketserver, threading, os, sys, json, subprocess, shutil, re, urllib.parse
from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(ROOT, "_site")
OLD  = os.path.join(ROOT, "_old")
PORT = 8933
PREVIOUS_RELEASE = "e4aaf95"   # the last main with the v3 service worker

# ---------------------------------------------------------------- the server
STATE = {"root": SITE, "down": False}   # down: drop every connection, the way a lost signal does
TYPES = {".html":"text/html; charset=utf-8", ".js":"text/javascript; charset=utf-8", ".json":"application/json",
         ".webmanifest":"application/manifest+json", ".png":"image/png", ".xml":"application/xml; charset=utf-8",
         ".txt":"text/plain; charset=utf-8", ".ico":"image/x-icon"}

class Pages(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if STATE["down"]:
            # no reply at all: the browser sees a dead connection, and so does the
            # service worker (Playwright's offline emulation does not reach a worker's
            # own fetches, so a real outage has to come from the server)
            self.close_connection = True
            return
        root = STATE["root"]
        p = urllib.parse.urlparse(self.path).path
        fp = os.path.normpath(os.path.join(root, p.lstrip("/")))
        if not fp.startswith(root):
            self.send_error(403); return
        if os.path.isdir(fp):
            if not p.endswith("/"):
                self.send_response(301); self.send_header("Location", p + "/"); self.end_headers(); return
            fp = os.path.join(fp, "index.html")
        if not os.path.isfile(fp):
            nf = os.path.join(root, "404.html")
            body = open(nf, "rb").read() if os.path.isfile(nf) else b"<h1>Not found</h1>"
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers(); self.wfile.write(body); return
        body = open(fp, "rb").read()
        self.send_response(200)
        self.send_header("Content-Type", TYPES.get(os.path.splitext(fp)[1], "application/octet-stream"))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers(); self.wfile.write(body)

def serve():
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("127.0.0.1", PORT), Pages) as s:
        s.serve_forever()

# ------------------------------------------------------------------ the build
def build():
    r = subprocess.run(["node", os.path.join(ROOT, "build.mjs"), SITE], capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout); print(r.stderr); sys.exit("build failed")
    print(r.stdout.strip())

def previous_release():
    """The last released app, so the upgrade check starts from what readers have installed."""
    shutil.rmtree(OLD, ignore_errors=True); os.makedirs(OLD)
    for f in ["index.html", "content.js", "sw.js", "manifest.webmanifest"]:
        src = subprocess.run(["git", "-C", ROOT, "show", f"{PREVIOUS_RELEASE}:{f}"], capture_output=True).stdout
        open(os.path.join(OLD, f), "wb").write(src)
    for f in ["icon-180.png", "icon-192.png", "icon-512.png", "icon-maskable-512.png"]:
        shutil.copy(os.path.join(ROOT, f), OLD)

def edition():
    js = ('const vm=require("vm"),fs=require("fs");const c={window:{}};'
          'vm.runInNewContext(fs.readFileSync(process.argv[1],"utf8"),c);'
          'console.log(JSON.stringify(c.window.LEDGER_CONTENT))')
    return json.loads(subprocess.run(["node", "-e", js, os.path.join(ROOT, "content.js")], capture_output=True, text=True).stdout)

def slug(s): return re.sub(r"^-|-$", "", re.sub(r"[^a-z0-9]+", "-", s.lower().replace("&", "and")))
PAGE_SECTIONS = ["Markets","Companies","Economics","Central Banks","Opinion","Tech & Finance","Personal Finance"]

# ------------------------------------------------------------------- checks
async def main():
    build(); previous_release()
    ed = edition(); arts = ed["articles"]
    base = f"http://127.0.0.1:{PORT}"
    results = []
    def ok(name, cond, extra=""):
        results.append((("PASS" if cond else "FAIL"), name, str(extra)))

    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--no-sandbox"])
        errors = []
        def watch(page):
            page.on("pageerror", lambda e: errors.append(str(e)))

        # ============ 1. the pages, with JavaScript off ============
        ctx = await b.new_context(java_script_enabled=False, viewport={"width":440,"height":956})
        page = await ctx.new_page(); watch(page)
        for a in arts:
            path = f"/story/{a['id']}/"
            r = await page.goto(base + path, wait_until="load")
            h1 = (await page.locator("#static h1").inner_text()).strip()
            paras = await page.locator("#static .rbody p").count()
            srcs = await page.locator("#static .sourcesbox a").count()
            title = await page.title()
            canon = await page.locator('link[rel="canonical"]').get_attribute("href")
            ogurl = await page.locator('meta[property="og:url"]').get_attribute("content")
            ogtype = await page.locator('meta[property="og:type"]').get_attribute("content")
            pub = await page.locator('meta[property="article:published_time"]').get_attribute("content")
            ld = json.loads(await page.locator('script[type="application/ld+json"]').first.inner_text())
            visible = await page.locator("#static").is_visible()
            home = await page.locator('#static a[href="/"]').count()
            kick = await page.locator("#static .kicker a").get_attribute("href")
            ok(f"{a['id']}: 200, readable without JavaScript",
               r.status == 200 and visible and h1 == a["title"] and paras >= 2 and srcs == len(a["sources"]),
               f"status={r.status} paras={paras} sources={srcs}/{len(a['sources'])}")
            ok(f"{a['id']}: own title, canonical and sharing metadata",
               title == a["title"] + " — The Ledger"
               and canon == "https://readtheledger.github.io" + path and ogurl == canon and ogtype == "article",
               f"title={title[:40]!r} canonical={canon}")
            ok(f"{a['id']}: publication date preserved",
               pub == a["date"] and ld.get("datePublished") == a["date"] and ld.get("headline") == a["title"]
               and ld.get("@type") == "NewsArticle", f"published={pub} ld={ld.get('datePublished')}")
            ok(f"{a['id']}: links home and to its section", home >= 1 and kick == f"/{slug(a['section'])}/", f"kicker={kick}")

        # every asset the page asks for is rooted at /, so it resolves from /story/<id>/
        rel = await page.evaluate("""() => [...document.querySelectorAll('script[src],link[href]')]
              .map(e => e.getAttribute('src') || e.getAttribute('href'))
              .filter(u => !/^(https?:|\\/)/.test(u))""")
        ok("story pages reference assets by absolute path", not rel, ", ".join(rel))

        # sections list their stories; the front page lists all of them
        for s in PAGE_SECTIONS:
            r = await page.goto(f"{base}/{slug(s)}/", wait_until="load")
            links = await page.evaluate("() => [...document.querySelectorAll('#static article.card .hl a')].map(a=>a.getAttribute('href'))")
            want = sorted(f"/story/{a['id']}/" for a in arts if a["section"] == s)
            ok(f"section /{slug(s)}/ lists its stories", r.status == 200 and sorted(links) == want, f"{len(links)} links")
        r = await page.goto(base + "/", wait_until="load")
        links = await page.evaluate("() => [...document.querySelectorAll('#static article.card .hl a')].map(a=>a.getAttribute('href'))")
        ok("front page links to every story without JavaScript",
           r.status == 200 and sorted(links) == sorted(f"/story/{a['id']}/" for a in arts), f"{len(links)} links")
        secnav = await page.evaluate("() => [...document.querySelectorAll('#static .static-nav a')].map(a=>a.getAttribute('href'))")
        ok("static section navigation present", secnav == ["/"] + [f"/{slug(s)}/" for s in PAGE_SECTIONS], secnav)

        # sitemap, robots, 404
        sm = await (await ctx.request.get(base + "/sitemap.xml")).text()
        locs = re.findall(r"<loc>([^<]+)</loc>", sm)
        ok("sitemap lists the front page, sections with content and every story",
           "https://readtheledger.github.io/" in locs
           and all(f"https://readtheledger.github.io/story/{a['id']}/" in locs for a in arts)
           and all(("https://readtheledger.github.io/%s/" % slug(s) in locs) == any(a["section"] == s for a in arts) for s in PAGE_SECTIONS),
           f"{len(locs)} urls")
        ok("sitemap lastmod carries the publication dates",
           all(f"<lastmod>{a['date']}</lastmod>" in sm for a in arts))
        rb = await (await ctx.request.get(base + "/robots.txt")).text()
        ok("robots.txt allows crawling and names the sitemap", "Allow: /" in rb and "Sitemap: https://readtheledger.github.io/sitemap.xml" in rb)
        r = await page.goto(base + "/story/no-such-story/", wait_until="load")
        ok("unknown story is a real 404", r.status == 404 and await page.locator("#static").count() == 0
           and "isn't in this edition" in await page.content(), f"status={r.status}")
        await ctx.close()

        # ============ 2. the app, from a story's own address ============
        ctx = await b.new_context(viewport={"width":440,"height":956}, is_mobile=True, has_touch=True, locale="en-GB")
        await ctx.grant_permissions(["clipboard-read", "clipboard-write"])
        page = await ctx.new_page(); watch(page)
        a0 = arts[0]; p0 = f"/story/{a0['id']}/"

        await page.goto(base + p0, wait_until="load")
        await page.wait_for_selector("#reader.on", timeout=8000)
        await page.wait_for_timeout(500)
        ok("fresh visit to a story address opens that story",
           (await page.locator("#rwrap h1").inner_text()).strip() == a0["title"]
           and await page.evaluate("location.pathname") == p0
           and await page.locator("#static").count() == 0
           and a0["title"] in await page.title(), await page.evaluate("location.pathname"))

        await page.reload(wait_until="load")
        await page.wait_for_selector("#reader.on", timeout=8000)
        ok("refresh keeps the story open at the same address",
           (await page.locator("#rwrap h1").inner_text()).strip() == a0["title"] and await page.evaluate("location.pathname") == p0)

        # back from a story landed on directly reaches the front page, in the app
        await page.go_back()
        await page.wait_for_function("location.pathname === '/'", timeout=5000)
        await page.wait_for_timeout(400)
        ok("browser back from a direct landing shows the front page",
           await page.locator("#reader.on").count() == 0 and await page.locator("article.card").count() >= 1
           and await page.evaluate("document.title") == "The Ledger — Finance, read properly")
        await page.go_forward()
        await page.wait_for_function(f"location.pathname === '{p0}'", timeout=5000)
        await page.wait_for_timeout(400)
        ok("browser forward re-opens the story", await page.locator("#reader.on").count() == 1
           and (await page.locator("#rwrap h1").inner_text()).strip() == a0["title"])
        await page.go_back()
        await page.wait_for_function("location.pathname === '/'", timeout=5000)

        # a headline on the front page is a real link, opened in place
        card = page.locator("article.card").first
        href = await card.locator(".hl a").get_attribute("href")
        await card.locator(".hl a").click()
        await page.wait_for_selector("#reader.on", timeout=5000)
        ok("front-page headline links to the story's address and opens the reader",
           href.startswith("/story/") and await page.evaluate("location.pathname") == href, f"href={href}")
        await page.locator("#rBack").click()
        await page.wait_for_function("location.pathname === '/'", timeout=5000)
        ok("back button returns to the front page address", await page.locator("#reader.on").count() == 0)

        # the escape key leaves through history the same way
        await card.locator(".hl a").click()
        await page.wait_for_selector("#reader.on", timeout=5000)
        await page.keyboard.press("Escape")
        await page.wait_for_function("location.pathname === '/'", timeout=5000)
        ok("escape closes the story and restores the address", await page.locator("#reader.on").count() == 0)

        # section tabs are links; switching updates the address and survives a refresh
        await page.locator('#secnav a[data-sec="Markets"]').click()
        await page.wait_for_function("location.pathname === '/markets/'", timeout=5000)
        kickers = await page.evaluate("() => [...document.querySelectorAll('#feed article.card .kicker')].map(k=>k.textContent)")
        ok("section tab is a link that updates the address", kickers and all(k == "Markets" for k in kickers), kickers)
        await page.reload(wait_until="load")
        await page.wait_for_timeout(600)
        cur = await page.locator('#secnav [aria-current="page"]').get_attribute("data-sec")
        ok("refreshing a section address lands on that section", cur == "Markets" and await page.locator("#static").count() == 0, f"current={cur}")
        tabs = await page.evaluate("() => [...document.querySelectorAll('#secnav .seclink')].map(e=>e.tagName+':'+(e.getAttribute('href')||''))")
        ok("editorial sections are anchors, Newsstand and Saved stay buttons",
           tabs[0] == "A:/" and "A:/markets/" in tabs and "BUTTON:" in tabs and tabs.count("BUTTON:") == 2, tabs)

        # sharing: a Ledger story shares its own address; a feed item shares the publisher's
        await page.goto(base + p0, wait_until="load")
        await page.wait_for_selector("#reader.on", timeout=8000)
        await page.evaluate("Object.defineProperty(navigator, 'share', {configurable:true, value: d => { window.__shared = d; return Promise.resolve(); }})")
        await page.locator("#rShare").click(); await page.wait_for_timeout(300)
        shared = await page.evaluate("window.__shared")
        ok("share hands the system the story's own address",
           shared and shared["url"] == base + p0 and shared["title"] == a0["title"], shared and shared["url"])
        await page.evaluate("Object.defineProperty(navigator, 'share', {configurable:true, value: undefined})")
        await page.locator("#rShare").click(); await page.wait_for_timeout(400)
        clip = await page.evaluate("navigator.clipboard.readText()")
        ok("share falls back to copying the story's address", clip.startswith(base + p0), clip[:60])
        feed_share = await page.evaluate("""() => {
          const it = makeItem({title:'Wire story', link:'https://example.com/wire', rawHtml:'<p>'+'word '.repeat(300)+'</p>',
                               author:'A', date:new Date().toISOString(), source:'Newswire', hintSection:'Markets'});
          openReader(it);
          const own = storyPath(it);
          const url = own ? location.origin+own : (safeUrl(it.link)||location.href);
          const path = location.pathname; closeReader(); history.back(); return {own, url, path};
        }""")
        ok("a feed item shares the publisher's link and keeps the page address",
           feed_share["own"] == "" and feed_share["url"] == "https://example.com/wire" and feed_share["path"] == p0, feed_share)

        # bookmarks from a story address, surviving a refresh, and reachable from Saved
        await page.goto(base + p0, wait_until="load")
        await page.wait_for_selector("#reader.on", timeout=8000)
        await page.locator("#rSave").click(); await page.wait_for_timeout(300)
        await page.reload(wait_until="load")
        await page.wait_for_selector("#reader.on", timeout=8000)
        ok("bookmark made at a story address survives a refresh",
           await page.locator('#rSave[aria-pressed="true"]').count() == 1)
        await page.go_back()
        await page.wait_for_function("location.pathname === '/'", timeout=5000)
        await page.locator("#btnSaved").click(); await page.wait_for_timeout(400)
        saved_href = await page.locator("#feed article.card .hl a").first.get_attribute("href")
        await page.locator("#feed article.card .hl a").first.click()
        await page.wait_for_selector("#reader.on", timeout=5000)
        ok("saved list links the story to its address and opens it",
           saved_href == p0 and await page.evaluate("location.pathname") == p0
           and (await page.locator("#rwrap h1").inner_text()).strip() == a0["title"], saved_href)

        # audio from a story address: the dock opens and the device voice is used
        await page.locator("#rListen").click(); await page.wait_for_timeout(1000)
        sub = await page.locator("#dSub").inner_text()
        ok("listen works from a story address",
           await page.locator("#dock.on").count() == 1 and "Device voice" in sub
           and (await page.locator("#dTitle").inner_text()).strip() == a0["title"], sub)
        await page.locator("#dClose").click()

        # copy still carries the article
        await page.locator("#rCopy").click(); await page.wait_for_timeout(400)
        clip = await page.evaluate("navigator.clipboard.readText()")
        ok("copy carries the article from a story address", a0["title"] in clip and len(clip) > 500, f"{len(clip)} chars")

        # ============ 3. the service worker ============
        await page.wait_for_function("navigator.serviceWorker && navigator.serviceWorker.controller !== null", timeout=15000)
        names = await page.evaluate("caches.keys()")
        ok("service worker installs a stamped v4 shell", any(re.match(r"ledger-shell-v4-[0-9a-f]{8}$", n) for n in names), names)

        # a real 404 comes through the worker unchanged while online
        r = await page.goto(base + "/story/no-such-story/", wait_until="load")
        ok("online, a missing page is still a 404 through the service worker",
           r.status == 404 and "isn't in this edition" in await page.content() and await page.locator("#reader").count() == 0,
           f"status={r.status}")

        # pages are cached under their own addresses: a visited story reads offline...
        a1 = arts[1]; p1 = f"/story/{a1['id']}/"
        await page.goto(base + p1, wait_until="load"); await page.wait_for_selector("#reader.on", timeout=8000)
        await page.wait_for_timeout(500)
        cached = await page.evaluate("name => caches.open(name).then(c=>c.keys()).then(ks=>ks.map(k=>new URL(k.url).pathname))",
                                     next(n for n in names if n.startswith("ledger-shell-v4-")))
        ok("visited pages are cached by their own path", p0 in cached and p1 in cached, cached)
        STATE["down"] = True
        r = await page.goto(base + p1, wait_until="load")
        await page.wait_for_selector("#reader.on", timeout=8000)
        ok("offline, a visited story loads from its own cached page",
           r.status == 200 and (await page.locator("#rwrap h1").inner_text()).strip() == a1["title"]
           and await page.evaluate("document.querySelector('link[rel=canonical]').href") == "https://readtheledger.github.io" + p1, f"status={r.status}")
        # ...and an unvisited story falls back to the shell, which renders it from content.js
        a2 = arts[2]; p2 = f"/story/{a2['id']}/"
        r = await page.goto(base + p2, wait_until="load")
        await page.wait_for_selector("#reader.on", timeout=8000)
        ok("offline, an unvisited story is rendered by the app shell",
           r.status == 200 and (await page.locator("#rwrap h1").inner_text()).strip() == a2["title"], f"status={r.status}")
        r = await page.goto(base + "/sitemap.xml", wait_until="load")
        ok("offline, a page the app cannot render does not pretend to exist", r.status == 503, f"status={r.status}")
        STATE["down"] = False
        await ctx.close()

        # ============ 4. upgrading the installed app ============
        # what readers have now: the previous release with its v3 worker, served at the same origin
        STATE["root"] = OLD
        ctx = await b.new_context(viewport={"width":440,"height":956})
        page = await ctx.new_page(); watch(page)
        await page.goto(base + "/", wait_until="load")
        await page.wait_for_function("navigator.serviceWorker && navigator.serviceWorker.controller !== null", timeout=15000)
        old_names = await page.evaluate("caches.keys()")
        ok("previous release installs its v3 worker", "ledger-shell-v3" in old_names, old_names)
        # the release lands; the next launch finds the new worker, installs it and
        # throws the old caches away (polled, because evaluate awaits the promise
        # and wait_for_function would not)
        STATE["root"] = SITE
        await page.reload(wait_until="load")
        new_names, upgraded = [], False
        for _ in range(40):
            new_names = await page.evaluate("caches.keys()")
            if any(re.match(r"ledger-shell-v4-", n) for n in new_names) and not any(n.endswith("-v3") for n in new_names):
                upgraded = True; break
            await page.wait_for_timeout(500)
        ok("upgrade replaces the v3 caches with the v4 shell", upgraded, new_names)
        # the v3 worker turned every server error into the cached shell; the v4 worker
        # lets a 404 through, so a 404 is the proof of which one is in control
        await page.reload(wait_until="load")
        r = await page.goto(base + "/story/no-such-story/", wait_until="load")
        ok("after the upgrade the new worker is in control (a 404 passes through)", r.status == 404, f"status={r.status}")
        ctl = await page.evaluate("navigator.serviceWorker.controller && navigator.serviceWorker.controller.scriptURL")
        await page.goto(base + p0, wait_until="load")
        await page.wait_for_selector("#reader.on", timeout=8000)
        ok("after the upgrade a story address opens through the new worker",
           ctl and ctl.endswith("/sw.js") and (await page.locator("#rwrap h1").inner_text()).strip() == a0["title"], ctl)
        # and the pages an upgraded reader opens are cached under their addresses
        await page.wait_for_timeout(500)
        cached = await page.evaluate("caches.keys().then(ks => caches.open(ks.find(k => /^ledger-shell-v4-/.test(k))).then(c => c.keys()).then(rs => rs.map(r => new URL(r.url).pathname)))")
        ok("after the upgrade visited pages are cached by their addresses", p0 in cached, cached)
        await ctx.close()

        await b.close()

    ok("no uncaught JS errors across every page", not errors, "; ".join(errors[:3]))

    width = max(len(n) for _, n, _ in results)
    fails = sum(1 for s, _, _ in results if s == "FAIL")
    for s, n, e in results: print(f"{s}  {n.ljust(width)}  {e}")
    print(f"\n{len(results)-fails}/{len(results)} page checks passed")
    sys.exit(1 if fails else 0)

threading.Thread(target=serve, daemon=True).start()
asyncio.run(main())
