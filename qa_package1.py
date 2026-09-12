"""Fifth QA pass: package 1 — freshness, filing, labels, the masthead and menu,
restorable views and sharing. Builds the site, writes a small gathered edition
into it (a political story a business desk carried, a Companies story, an item
with no usable date, a source kept from an earlier gathering), serves it the way
GitHub Pages does, and checks in headless Chromium at 360, 390, 768 and 1440 px:

  - every time on show comes from the content: the edition line is the newest
    date in content.js, the About card has no date and sits last, a news story
    past its week is labelled archive, an undated item says "date unknown";
  - the Newsstand says when it was gathered and how long ago; a refresh reports
    a newer edition, no newer edition, or the previous one kept after a failure;
  - a story with no economic case is filed under no topic; the reader shows the
    publisher's own filing beside The Ledger's when they differ;
  - a standing note is labelled Background in the reader, in Copy and in Listen;
    a reviewed note from context.js is labelled Why it matters, with its sources;
  - the masthead's two labelled buttons, the menu, the topic strip's scroll cue,
    one h1 per view, 44 px targets and no sideways overflow at every width;
  - Newsstand, Saved and search restore from their addresses with matching
    titles and noindex; every topic is a link; Escape and Back close a story;
  - Share reports completed, cancelled, or copied instead, and never claims
    a post was made.

This is a simulation in headless Chromium at phone and desktop widths, not a
test on a phone."""
import asyncio, http.server, socketserver, threading, os, sys, json, subprocess, re, urllib.parse
from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(ROOT, "_site")
PORT = 8935
SHOTS = os.environ.get("LEDGER_SHOTS", "")   # a directory: write screenshots there

TYPES = {".html":"text/html; charset=utf-8", ".js":"text/javascript; charset=utf-8", ".json":"application/json",
         ".webmanifest":"application/manifest+json", ".png":"image/png", ".xml":"application/xml; charset=utf-8", ".txt":"text/plain; charset=utf-8"}
STATE = {"feed_down": False, "feed": None}   # feed_down: answer 503 for the edition; feed: serve this JSON body instead
class Pages(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        p = urllib.parse.urlparse(self.path).path
        if p == "/data/feed.json" and (STATE["feed_down"] or STATE["feed"] is not None):
            if STATE["feed_down"]:
                self.send_response(503); self.send_header("Content-Length", "0"); self.end_headers(); return
            body = json.dumps(STATE["feed"]).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body); return
        fp = os.path.normpath(os.path.join(SITE, p.lstrip("/")))
        if os.path.isdir(fp): fp = os.path.join(fp, "index.html")
        if not fp.startswith(SITE) or not os.path.isfile(fp):
            body = open(os.path.join(SITE, "404.html"), "rb").read()
            self.send_response(404); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body); return
        body = open(fp, "rb").read()
        self.send_response(200); self.send_header("Content-Type", TYPES.get(os.path.splitext(fp)[1], "application/octet-stream"))
        self.send_header("Cache-Control", "no-store"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
def serve():
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("127.0.0.1", PORT), Pages) as s: s.serve_forever()

def build():
    r = subprocess.run(["node", os.path.join(ROOT, "build.mjs"), SITE], capture_output=True, text=True)
    if r.returncode != 0: print(r.stdout, r.stderr); sys.exit("build failed")

GATHERED = "2026-09-10T01:25:46.000Z"
LONG = " ".join(f"Sentence {i} of a report on rates, earnings and consumer spending, in some detail." for i in range(1, 30))
def item(i, title, source, desk, date, section, conf, **kw):
    d = {"id": f"p{i}", "source": source, "origin": source, "title": title, "link": f"https://example.com/{source.lower().replace(' ', '-')}/{i}",
         "author": source, "date": date, "html": "<p>" + LONG[:900] + "</p>", "words": 400,
         "section": section, "topic": {"confidence": conf, "reason": "test"}, "desk": desk,
         "kind": "news", "weight": 1, "lic": "", "rights": "summary"}
    d.update(kw); return d
EDITION = {"schema": 1, "fetched": GATHERED, "duplicates": 0,
  "sources": [{"n": "Wire Desk", "ok": True, "stale": False, "count": 3, "fetchedAt": GATHERED},
              {"n": "Business Desk", "ok": False, "stale": True, "count": 2, "fetchedAt": "2026-09-09T20:00:00Z", "error": "HTTP 503"}],
  "items": [
    item(1, "Oil prices climb above $100 as supply worries return", "Wire Desk", "Markets", "2026-09-10T01:00:00Z", "Markets", "high"),
    item(2, "Automaker announces third quarter results and a share buyback", "Wire Desk", "Markets", "2026-09-10T00:30:00Z", "Companies", "high"),
    item(3, "Prime minister denies ignoring warning ahead of the attacks", "Business Desk", "Companies", "2026-09-09T19:00:00Z", "", "none"),
    item(4, "Central bank holds rates steady and signals a pause", "Business Desk", "Companies", "2026-09-09T18:00:00Z", "Central Banks", "high"),
    item(5, "A story the feed gave no date for", "Wire Desk", "Markets", "", "Markets", "medium"),
  ]}
CONTEXT_JS = '''window.LEDGER_CONTEXT = {
  "https://example.com/wire-desk/1?utm_source=rss": {
    why: "Brent above $100 with inventories this low means the next move is in the physical market, not the futures curve.",
    sources: [{t: "Weekly petroleum status report", u: "https://example.org/eia", p: "EIA"}],
    reviewed: "2026-09-10", by: "the editor"
  }
};'''

async def main():
    build()
    os.makedirs(os.path.join(SITE, "data"), exist_ok=True)
    json.dump(EDITION, open(os.path.join(SITE, "data", "feed.json"), "w"))
    open(os.path.join(SITE, "context.js"), "w").write(CONTEXT_JS)   # a reviewed note, for this run only
    content = json.loads(subprocess.run(["node", "-e", 'const vm=require("vm"),fs=require("fs");const c={window:{}};vm.runInNewContext(fs.readFileSync(process.argv[1],"utf8"),c);console.log(JSON.stringify(c.window.LEDGER_CONTENT))', os.path.join(ROOT, "content.js")], capture_output=True, text=True).stdout)
    arts = content["articles"]
    newest = max(a["date"] for a in arts)
    news_old = sum(1 for a in arts if a["kind"] == "news")   # every current piece is well past a week
    base = f"http://127.0.0.1:{PORT}"
    results, errors = [], []
    def ok(n, c, x=""): results.append(("PASS" if c else "FAIL", n, str(x)))
    def shot(page, name):
        return page.screenshot(path=os.path.join(SHOTS, name + ".png")) if SHOTS else asyncio.sleep(0)
    # the app keys a card by a hash of the item's link, so cards are found by link
    async def cid(page, link_suffix):
        return await page.evaluate("suf => (S.items.find(i => i.link && i.link.endsWith(suf)) || {}).id || ''", link_suffix)
    async def txt(page, sel):
        return await page.evaluate("s => (document.querySelector(s) || {textContent: ''}).textContent.trim().replace(/\\s+/g, ' ')", sel)

    # the classifier, on the labelled sample, from headlines alone (the edition
    # with the publishers' excerpts is not committed; see the evaluation document)
    r = subprocess.run(["node", os.path.join(ROOT, "eval_topics.mjs"), "--edition", os.path.join(ROOT, "no-such-edition.json"), "--target", "0.9"], capture_output=True, text=True)
    last = [l for l in r.stdout.splitlines() if "placed appropriately" in l]
    ok("classifier places >= 90% of the labelled sample appropriately from headlines alone", r.returncode == 0, last[-1] if last else r.stderr[-200:])

    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--no-sandbox"])
        for W in (360, 390, 768, 1440):
            ctx = await b.new_context(viewport={"width": W, "height": 844 if W < 800 else 900}, is_mobile=W < 800, has_touch=W < 800, locale="en-GB")
            await ctx.grant_permissions(["clipboard-read", "clipboard-write"])
            page = await ctx.new_page(); page.on("pageerror", lambda e: errors.append(f"{W}: {e}"))
            await page.goto(base + "/", wait_until="load")
            await page.wait_for_function("S.edition && S.edition.fetched", timeout=15000); await page.wait_for_timeout(400)
            # ---- layout and masthead
            sw = await page.evaluate("document.documentElement.scrollWidth")
            ok(f"{W}: no sideways overflow", sw <= W, sw)
            ok(f"{W}: wordmark on one line and a link home", await page.evaluate("document.querySelector('.wordmark').getBoundingClientRect().height") < 40
               and await page.evaluate("document.querySelector('.wordmark').getAttribute('href')") == "/")
            ok(f"{W}: masthead buttons are labelled Search and Menu", await page.evaluate("[...document.querySelectorAll('.mastbtn span')].map(e=>e.textContent)") == ["Search", "Menu"])
            small = await page.evaluate("""() => { const bad=[]; document.querySelectorAll('button, a.seclink').forEach(b => { const r=b.getBoundingClientRect(); if (r.width>0 && r.height>0 && (r.height<43.5 || r.width<43.5)) bad.push((b.id||b.className)+':'+Math.round(r.width)+'x'+Math.round(r.height)); }); return bad; }""")
            ok(f"{W}: every visible control is a 44 px target", not small, small[:4])
            ok(f"{W}: scroll cue shown exactly when the topic strip overflows",
               await page.evaluate("document.querySelector('#secwrap').classList.contains('scrollable') === (document.querySelector('#secscroll').scrollWidth > document.querySelector('#secscroll').clientWidth + 4)"))
            ok(f"{W}: one h1 on the front page", await page.evaluate("document.querySelectorAll('h1').length") == 1)
            lead = await page.evaluate("parseFloat(getComputedStyle(document.querySelector('article.card.lead .hl')).fontSize)")
            ok(f"{W}: lead headline between 24 and 42 px", 24 <= lead <= 42, lead)
            # ---- freshness on the front page
            ds = await txt(page, "#datestrip")
            want = "Latest edition " + subprocess.run(["node", "-e", f'console.log(new Date("{newest}").toLocaleDateString("en-GB",{{day:"numeric",month:"long",year:"numeric",timeZone:"UTC"}}))'], capture_output=True, text=True).stdout.strip()
            ok(f"{W}: edition line is the publication's newest date plus the gathering time and age",
               ds.startswith(want) and "Newsstand gathered" in ds and "ago)" in ds, ds)
            ok(f"{W}: the About card is last, labelled About, with no date",
               await page.evaluate("(()=>{const c=[...document.querySelectorAll('#feed article.card')];const l=c[c.length-1];return l.classList.contains('about') && l.querySelector('.kicker').textContent==='About' && /no date/.test(l.querySelector('.meta').textContent)})()"))
            ok(f"{W}: every news story older than a week is labelled archive, analysis is not",
               await page.evaluate("document.querySelectorAll('#feed article.card:not(.about) .kicker .arch').length") == news_old
               and await page.evaluate("[...document.querySelectorAll('#feed article.card')].filter(c=>c.querySelector('.kicker .arch')).every(c=>{const it=itemById(c.dataset.id);return it.kind==='news'})"), news_old)
            await shot(page, f"front-{W}")
            # ---- the menu
            await page.locator("#btnMenu").click(); await page.wait_for_timeout(250)
            ok(f"{W}: menu opens, lists ten topic links and the secondary actions, and takes focus",
               await page.locator("#menu.on").count() == 1 and await page.locator("#menuTopics a").count() == 10
               and await page.evaluate("['btnSaved','btnTheme','btnRefresh','btnSettings','btnReload'].every(id=>document.getElementById(id).offsetParent!==null)")
               and await page.evaluate("document.activeElement && document.activeElement.closest('#menu') !== null"))
            await shot(page, f"menu-{W}")
            await page.keyboard.press("Escape"); await page.wait_for_timeout(200)
            ok(f"{W}: Escape closes the menu and returns focus to the Menu button", await page.locator("#menu.on").count() == 0 and await page.evaluate("document.activeElement.id") == "btnMenu")
            # ---- the Newsstand view
            await page.locator('#secnav a[data-sec="Newsstand"]').click(); await page.wait_for_timeout(400)
            g = await txt(page, "#gathered")
            ok(f"{W}: Newsstand heading, gathered time and age, kept source, address, title, noindex",
               (await txt(page, ".viewhead h1")) == "Newsstand" and g.startswith("Newsstand gathered") and "ago)" in g and "1 source kept from an earlier gathering" in g
               and await page.evaluate("location.pathname + location.search") == "/?view=newsstand" and await page.title() == "Newsstand — The Ledger"
               and await page.evaluate("document.querySelector('#robotsMeta').content") == "noindex,follow", g)
            P = {n: await cid(page, suf) for n, suf in [("p1", "/wire-desk/1"), ("p2", "/wire-desk/2"), ("p3", "/business-desk/3"), ("p4", "/business-desk/4"), ("p5", "/wire-desk/5")]}
            kick = dict(await page.evaluate("[...document.querySelectorAll('#feed article.card')].map(c=>[c.dataset.id, c.querySelector('.kicker').textContent])"))
            ok(f"{W}: a story with no economic case shows a Newsstand kicker, not the desk's Companies", kick.get(P["p3"]) == "Newsstand" and kick.get(P["p4"]) == "Central Banks", kick)
            ok(f"{W}: an undated item says date unknown", "date unknown" in await txt(page, f'#feed article.card[data-id="{P["p5"]}"] .meta'))
            await shot(page, f"newsstand-{W}")
            # ---- the Companies tab does not carry the political story
            await page.locator('#secnav a[data-sec="Companies"]').click(); await page.wait_for_timeout(300)
            ids = await page.evaluate("[...document.querySelectorAll('#feed article.card')].map(c=>c.dataset.id)")
            ok(f"{W}: Companies tab carries the Companies story and not the political one", P["p2"] in ids and P["p3"] not in ids and await page.evaluate("location.pathname") == "/companies/", ids)
            # ---- reader of a Newsstand item: Background, publisher's filing, Read/Share original
            await page.locator('#secnav a[data-sec="Newsstand"]').click(); await page.wait_for_timeout(300)
            await page.locator(f'#feed article.card[data-id="{P["p4"]}"]').click(); await page.wait_for_selector("#reader.on"); await page.wait_for_timeout(300)
            ok(f"{W}: standing note is labelled Background with an honest signature, and the publisher's own filing is shown",
               (await txt(page, "#rwrap .wimbox h3")) == "Background" and "standing note" in await txt(page, "#rwrap .wimsig")
               and "filed by Business Desk under Companies" in await txt(page, "#rwrap .rmeta"))
            ok(f"{W}: preview tag, Read the original, Share original, labelled reader actions",
               await page.locator("#rwrap .preview-tag").count() == 1 and "Read the original at" in await txt(page, "#rwrap .srccta a")
               and await page.evaluate("[...document.querySelectorAll('.rbar-in .rbtn .lbl')].map(e=>e.textContent)") == ["Back", "Listen", "Copy", "Share original", "Save"])
            copied = await page.evaluate("plainText(S.current)"); spoken = await page.evaluate("speechText(S.current)")
            ok(f"{W}: Copy and Listen carry the Background label, not Why it matters",
               "Background:" in copied and "Why it matters" not in copied and "Background." in spoken and "Why it matters" not in spoken)
            await page.evaluate("history.back()"); await page.wait_for_timeout(300)
            ok(f"{W}: Newsstand preview keeps the page address and Back closes it", await page.locator("#reader.on").count() == 0 and await page.evaluate("location.search") == "?view=newsstand")
            # ---- a reviewed note is Why it matters, with its sources
            await page.locator(f'#feed article.card[data-id="{P["p1"]}"]').click(); await page.wait_for_selector("#reader.on"); await page.wait_for_timeout(300)
            ok(f"{W}: a reviewed note from context.js is Why it matters with its source and reviewer",
               (await txt(page, "#rwrap .wimbox h3")) == "Why it matters" and await page.locator("#rwrap .wimbox ul a").count() == 1
               and "reviewed 2026-09-10" in await txt(page, "#rwrap .wimsig") and "Why it matters:" in await page.evaluate("plainText(S.current)"))
            await shot(page, f"reader-newsstand-{W}")
            # ---- share outcomes
            await page.evaluate("Object.defineProperty(navigator,'share',{configurable:true,value:d=>{window.__s=d;return Promise.resolve()}})")
            await page.locator("#rShare").click(); await page.wait_for_timeout(200); t1 = await txt(page, "#toast"); u1 = await page.evaluate("window.__s.url")
            await page.evaluate("Object.defineProperty(navigator,'share',{configurable:true,value:()=>Promise.reject(Object.assign(new Error('x'),{name:'AbortError'}))})")
            await page.locator("#rShare").click(); await page.wait_for_timeout(200); t2 = await txt(page, "#toast")
            await page.evaluate("Object.defineProperty(navigator,'share',{configurable:true,value:undefined})")
            await page.locator("#rShare").click(); await page.wait_for_timeout(300); t3 = await txt(page, "#toast"); clip = await page.evaluate("navigator.clipboard.readText()")
            ok(f"{W}: Share original: completed, cancelled and copied-instead each reported, sharing the publisher's link",
               t1.startswith("Shared the original article's link") and u1.startswith("https://example.com/wire-desk/1") and t2 == "Share cancelled"
               and "copied the original article's link" in t3 and clip == u1 and "posted" not in (t1 + t2 + t3).lower(), f"{t1} | {t2} | {t3}")
            await page.keyboard.press("Escape"); await page.wait_for_timeout(300)
            # ---- search: heading, address, restore
            await page.locator("#btnSearch").click(); await page.fill("#q", "oil"); await page.wait_for_timeout(600)
            ok(f"{W}: search view names the term and count, is addressed and titled, and is noindex",
               (await txt(page, ".viewhead h1")) == "Search" and "“oil”" in await txt(page, ".viewnote")
               and "q=oil" in await page.evaluate("location.search") and await page.title() == "Search: oil — The Ledger"
               and await page.evaluate("document.querySelector('#robotsMeta').content") == "noindex,follow")
            await page.reload(wait_until="load"); await page.wait_for_timeout(700)
            ok(f"{W}: a search restores after reload with the box open", await page.evaluate("S.query") == "oil" and await page.evaluate("document.querySelector('#q').value") == "oil" and await page.locator("#searchwrap.on").count() == 1)
            await page.goto(base + "/?view=saved", wait_until="load"); await page.wait_for_timeout(400)
            ok(f"{W}: /?view=saved in a new tab shows the Saved view with its heading and title", (await txt(page, ".viewhead h1")) == "Saved articles" and await page.title() == "Saved articles — The Ledger")
            # ---- a Ledger story: archive label in the reader, plain Share, Escape through history
            a0 = arts[0]; await page.goto(base + f"/story/{a0['id']}/", wait_until="load"); await page.wait_for_selector("#reader.on"); await page.wait_for_timeout(300)
            k = await txt(page, "#rwrap .kicker")
            ok(f"{W}: a Ledger news story past its week is labelled archive in the reader, with its real date",
               k.startswith("From the archive") and re.search(r"\b2026\b", await txt(page, "#rwrap .rmeta")) is not None, k)
            ok(f"{W}: a Ledger story's Share is plain Share", (await txt(page, "#rShareLbl")) == "Share")
            await shot(page, f"reader-ledger-{W}")
            if W == 390:
                await page.evaluate("store.set(LS.theme,'dark'); applyTheme()"); await page.keyboard.press("Escape"); await page.wait_for_timeout(300)
                await shot(page, "front-dark-390"); await page.evaluate("store.set(LS.theme,'light'); applyTheme()")
            await ctx.close()

        # ---- refresh outcomes, once
        ctx = await b.new_context(viewport={"width": 390, "height": 844}); page = await ctx.new_page(); page.on("pageerror", lambda e: errors.append(str(e)))
        await page.goto(base + "/", wait_until="load"); await page.wait_for_function("S.edition && S.edition.fetched", timeout=15000)
        first = await page.evaluate("S.edition.fetched")
        STATE["feed_down"] = True
        await page.evaluate("loadFeeds({manual:true})"); await page.wait_for_timeout(1200)
        t = await txt(page, "#toast")
        ok("a failed refresh keeps the previous edition, with its true gathering time",
           t.startswith("Couldn't reach the Newsstand — keeping the edition gathered") and await page.evaluate("S.edition.fetched") == first
           and await page.evaluate("S.items.filter(i=>!i.demo && !i.ledger).length") == 5, t)
        STATE["feed_down"] = False
        await page.evaluate("loadFeeds({manual:true})"); await page.wait_for_timeout(1200)
        t = await txt(page, "#toast")
        ok("a refresh with nothing newer says so", t.startswith("No newer Newsstand edition"), t)
        newer = dict(EDITION); newer["fetched"] = "2026-09-10T09:00:00.000Z"
        STATE["feed"] = newer
        await page.evaluate("loadFeeds({manual:true})"); await page.wait_for_timeout(1200)
        t = await txt(page, "#toast")
        ok("a refresh with a newer edition says so, and the masthead line follows", t.startswith("Newer Newsstand edition loaded") and "Newsstand gathered" in await txt(page, "#datestrip"), t)
        STATE["feed"] = None
        # the offline copy keeps the edition's own time
        cached = await page.evaluate("JSON.parse(localStorage.getItem('ledger.cache')).fetched")
        ok("the device's cached copy carries the edition's gathering time", cached == "2026-09-10T09:00:00.000Z", cached)
        await ctx.close(); await b.close()

    ok("no uncaught JS errors", not errors, "; ".join(errors[:3]))
    w = max(len(n) for _, n, _ in results); fails = sum(1 for s, _, _ in results if s == "FAIL")
    for s, n, x in results: print(f"{s}  {n.ljust(w)}  {x}")
    print(f"\n{len(results)-fails}/{len(results)} package-1 checks passed  (headless Chromium simulation at 360/390/768/1440 px, not a phone)")
    sys.exit(1 if fails else 0)

threading.Thread(target=serve, daemon=True).start()
asyncio.run(main())
