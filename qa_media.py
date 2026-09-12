"""Editorial media: a piece's own picture, rendered once by media.js for the static
page and the reader, with its caption, credit and disclosure; the card variants
(lead, compact with a thumbnail, feature); the text-led state for a piece with no
picture; the handover from the static page to the reader without a second
fetch or a duplicate figure; lazy loading below the fold; typography at 390px
and under the reader's text-size setting; the Listen dock's reserved space; no
horizontal overflow from 320 to 1440px; Save, Copy and Share unchanged; and
the worker's bounded image cache. Two builds: the real content.js as
published, for everything about the production pages and their pace; and a
fixture with one piece's picture removed (the AI-trade story, a text-led row on
the front page either way), served on a second port, for the text-led state.

    python3 qa_media.py            # needs playwright (chromium) and node
"""
import asyncio, http.server, socketserver, threading, os, sys, json, subprocess, re, urllib.parse, tempfile, shutil, collections
from playwright.async_api import async_playwright
from qa_worker_helpers import update_and_wait_for_controller, wait_for_active_controller, wait_for_cached_response

ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = 8943          # the publication as it is
PORT2 = 8944         # the fixture with one picture removed
SITE_URL = "https://readtheledger.github.io"
STATE = {"root": None, "root2": None, "hits": collections.Counter()}
TYPES = {".html":"text/html; charset=utf-8", ".js":"text/javascript; charset=utf-8", ".json":"application/json", ".webp":"image/webp", ".jpg":"image/jpeg",
         ".webmanifest":"application/manifest+json", ".png":"image/png", ".xml":"application/xml; charset=utf-8", ".txt":"text/plain; charset=utf-8"}
class Pages(http.server.BaseHTTPRequestHandler):
    rootkey = "root"
    def log_message(self, *a): pass
    def do_GET(self):
        root = STATE[self.rootkey]; p = urllib.parse.urlparse(self.path).path
        STATE["hits"][p] += 1
        fp = os.path.normpath(os.path.join(root, p.lstrip("/")))
        if os.path.isdir(fp):
            if not p.endswith("/"): self.send_response(301); self.send_header("Location", p + "/"); self.end_headers(); return
            fp = os.path.join(fp, "index.html")
        if not fp.startswith(root) or not os.path.isfile(fp):
            body = open(os.path.join(root, "404.html"), "rb").read()
            self.send_response(404); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body); return
        body = open(fp, "rb").read()
        self.send_response(200); self.send_header("Content-Type", TYPES.get(os.path.splitext(fp)[1], "application/octet-stream"))
        self.send_header("Cache-Control", "max-age=600" if p.startswith("/assets/") else "no-store")   # as GitHub Pages serves them
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
class Pages2(Pages): rootkey = "root2"
def serve(port, handler):
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("127.0.0.1", port), handler) as s: s.serve_forever()

R = []
def ok(name, cond, note=""):
    R.append(("PASS" if cond else "FAIL", name, note)); print(("PASS " if cond else "FAIL ") + name + (("  — " + str(note)) if (note and not cond) else ""))
def lds(html): return [json.loads(m) for m in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)]
def hits(prefix): return {k: v for k, v in STATE["hits"].items() if k.startswith(prefix)}

# the fixture removes the picture from a piece that is a text-led row on the front
# page in both orders — the static page's (by date) and the app's composed one
WITH = "led-20260817-savers"; FEATURE = "led-20260817-weekly"; WITHOUT = "led-20260817-aitrade"

async def main():
    work = tempfile.mkdtemp(prefix="ledger-media-"); site = os.path.join(work, "site"); site2 = os.path.join(work, "site-noimage")
    stub = '{"fetched":"2026-09-12T14:00:00Z","sources":[],"items":[]}'
    # the publication as it is
    r = subprocess.run(["node", os.path.join(ROOT, "build.mjs"), site], capture_output=True, text=True)
    if r.returncode: print(r.stdout, r.stderr); sys.exit("build failed")
    print(r.stdout.strip().splitlines()[-1])
    # and the same with one piece's picture taken away, for the text-led state
    src = open(os.path.join(ROOT, "content.js"), encoding="utf-8").read()
    stripped = re.sub(r'(id:\s*"%s",\n(?:\s*produced:[^\n]+\n)?\s*)image:\{[^\n]*\},\n' % WITHOUT, r"\1", src)
    assert stripped != src, "fixture: could not remove the picture from " + WITHOUT
    cf = os.path.join(work, "content.js"); open(cf, "w", encoding="utf-8").write(stripped)
    r = subprocess.run(["node", os.path.join(ROOT, "build.mjs"), site2, "--content", cf], capture_output=True, text=True)
    if r.returncode: print(r.stdout, r.stderr); sys.exit("fixture build failed")
    for d in (site, site2):
        os.makedirs(os.path.join(d, "data")); open(os.path.join(d, "data", "feed.json"), "w").write(stub)
    STATE["root"] = site; STATE["root2"] = site2
    threading.Thread(target=serve, args=(PORT, Pages), daemon=True).start()
    threading.Thread(target=serve, args=(PORT2, Pages2), daemon=True).start()
    base = f"http://127.0.0.1:{PORT}"; base2 = f"http://127.0.0.1:{PORT2}"
    rd = lambda *p: open(os.path.join(site, *p), encoding="utf-8").read()
    rd2 = lambda *p: open(os.path.join(site2, *p), encoding="utf-8").read()

    # ---- the built pages
    sw = rd("sw.js")
    ok("worker: media.js precached, pictures never precached, bounded image cache of its own, scoped to the build",
       '"/media.js"' in sw and "assets/editorial" not in re.search(r"const FILES = \[(.*?)\];", sw, re.S).group(1) and "IMAGE_KEEP" in sw and 'startsWith("/assets/editorial/")' in sw
       and 'const IMAGES  = "ledger-images-v" + VERSION + "-" + BUILD' in sw and "e.waitUntil(c.put(" in sw)
    ok("archive label on static pages: a news story past a week says so, analysis carries only its date",
       '<span class="arch">From the archive · </span>' in re.search(r'<div id="static">[\s\S]*?<h1>', rd("story", "led-20260817-record", "index.html")).group(0)
       and '<span class="arch">' not in re.search(r'<div id="static">[\s\S]*?<h1>', rd("story", WITH, "index.html")).group(0)
       and rd("index.html").count('<span class="arch">From the archive · </span>') >= 5)
    html = rd("story", WITH, "index.html"); L = lds(html)
    im = L[0]["image"][0]
    ok("story with a picture: NewsArticle.image is the piece's own derivative with size, credit and AI source type",
       im["url"] == f"{SITE_URL}/assets/editorial/{WITH}/hero-1200.jpg" and im["width"] == 1200 and im["creditText"] == "The Ledger" and "trainedAlgorithmicMedia" in im["digitalSourceType"])
    ok("story with a picture: sharing preview is the piece's own picture, large card",
       f'property="og:image" content="{SITE_URL}/assets/editorial/{WITH}/hero-1200.jpg"' in html and 'twitter:card" content="summary_large_image"' in html and 'og:image:alt' in html)
    ok("as published, every piece carries a picture",
       all("image" in lds(rd("story", a, "index.html"))[0] for a in [WITH, FEATURE, WITHOUT, "led-20260817-record", "led-20260817-fed"]))
    html2 = rd2("story", WITHOUT, "index.html"); L2 = lds(html2)
    ok("fixture, story without a picture: no NewsArticle.image, icon only as the sharing preview, no figure",
       "image" not in L2[0] and f'property="og:image" content="{SITE_URL}/icon-512.png"' in html2 and '<figure class="fig' not in re.search(r'<div id="static">[\s\S]*?</div>\s*</main>', html2).group(0))
    ok("every derivative a piece names is served", all(
        subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", base + u], capture_output=True, text=True).stdout == "200"
        for u in [f"/assets/editorial/{WITH}/hero-{w}.webp" for w in (480, 768, 1200)] + [f"/assets/editorial/{WITH}/hero-1200.jpg", f"/assets/editorial/{FEATURE}/hero-1200.jpg"]))
    ok("no master is shipped: every editorial file under 600 KB, provenance carries the master's hash only",
       all(os.path.getsize(os.path.join(dp, f)) < 600 * 1024 for dp, _, fs in os.walk(os.path.join(site, "assets", "editorial")) for f in fs)
       and json.load(open(os.path.join(site, "assets", "editorial", WITH, "manifest.json")))["master"]["committed"] is False)

    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        # ---- JavaScript off: what a crawler and a reader without scripts get
        ctx = await b.new_context(java_script_enabled=False, viewport={"width":390,"height":844}, is_mobile=True, device_scale_factor=2)
        page = await ctx.new_page()
        await page.goto(base + f"/story/{WITH}/")
        info = await page.evaluate("""() => {
          const s=document.querySelector('#static'); const f=s.querySelector('figure.fig-hero'); const img=f&&f.querySelector('img');
          const order=[...s.querySelectorAll('.kicker,h1,.rstand,figure.fig-hero,.rmeta,.rbody')].map(e=>e.matches('figure')?'figure':e.className||e.tagName.toLowerCase());
          return {order, alt:img&&img.alt, w:img&&img.getAttribute('width'), h:img&&img.getAttribute('height'), srcset:img&&img.getAttribute('srcset'), sizes:img&&img.getAttribute('sizes'),
                  loading:img&&img.getAttribute('loading'), prio:img&&img.getAttribute('fetchpriority'), cap:f&&(f.querySelector('.fig-cap')||{}).textContent, credit:f&&(f.querySelector('.fig-credit')||{}).textContent,
                  ai:!!(f&&f.querySelector('.fig-ai')), rendered:img&&Math.round(img.getBoundingClientRect().width), chosen:img&&(img.currentSrc||'').split('/').pop(), figs:s.querySelectorAll('figure.fig').length};
        }""")
        ok("static story: kicker, headline, deck, picture, byline/date, body — in that order",
           info["order"] == ["kicker", "h1", "rstand", "figure", "rmeta", "rbody"], info["order"])
        ok("static story: one figure with alt text, reserved size, three WebP candidates, sizes, eager and high priority",
           info["figs"] == 1 and info["alt"].startswith("A stack of coins") and info["w"] == "1200" and info["h"] == "800" and info["srcset"].count("w,") == 2 and "100vw" in info["sizes"] and info["loading"] == "eager" and info["prio"] == "high", info)
        ok("static story: caption is editorial, credit names the maker, disclosure says AI-generated",
           info["cap"].startswith("Cash savings") and "AI-generated" not in info["cap"] and "The Ledger" in info["credit"] and info["ai"])
        ok("static story at 390px, 2x: the picture fills the viewport and the 1200px derivative is chosen", info["rendered"] == 390 and info["chosen"] == "hero-1200.webp", info)
        await page.goto(base2 + f"/story/{WITHOUT}/")
        order = await page.evaluate("[...document.querySelectorAll('#static .kicker, #static h1, #static .rstand, #static figure, #static .rmeta, #static .rbody')].map(e=>e.matches('figure')?'figure':e.className||e.tagName.toLowerCase())")
        ok("fixture, static story without a picture: text-led, same order, nothing left empty", order == ["kicker", "h1", "rstand", "rmeta", "rbody"], order)
        await page.goto(base2 + "/")
        ok("fixture, front page: the row whose story lost its picture stays text-led; lead, two thumbnails and the feature are unchanged",
           await page.evaluate("[...document.querySelectorAll('#static article.card figure.fig')].map(f=>f.className.replace('fig ',''))") == ["fig-lead", "fig-thumb", "fig-thumb", "fig-feature"])
        os.makedirs(os.path.join(ROOT, "docs", "design", "shots"), exist_ok=True)
        await page.screenshot(path=os.path.join(ROOT, "docs", "design", "shots", "no-image-390-nojs.png"), full_page=False)
        await page.goto(base + "/")
        cards = await page.evaluate("""() => [...document.querySelectorAll('#static article.card')].map(c=>({cls:c.className, fig:(c.querySelector('figure.fig')||{}).className||'', cap:!!c.querySelector('figcaption'), lazy:(c.querySelector('img')||{}).getAttribute?c.querySelector('img').getAttribute('loading'):null, below:!!c.querySelector('.cardbelow'), italic:!!c.querySelector('.feature-hl')}))""")
        lead, comp, feat = cards[0], next(c for c in cards if "compact" in c["cls"] and "has-image" in c["cls"]), next(c for c in cards if "feature" in c["cls"])
        ok("static front: the lead keeps editorial order and carries its own picture above the words, eager",
           "lead" in lead["cls"] and lead["fig"] == "fig fig-lead" and lead["lazy"] == "eager" and not lead["cap"])
        thumbs = [i for i, c in enumerate(cards) if "fig-thumb" in c["fig"]]
        ok("static front: thumbnails on the two stories after the lead only; the rows after are text-led although their stories have pictures",
           thumbs == [1, 2] and all(c["fig"] == "" for c in cards[3:] if "compact" in c["cls"]), thumbs)
        ok("static front: a compact story shows a lazy 3:2 thumbnail with no caption, summary and meta below at full width",
           comp["fig"] == "fig fig-thumb" and not comp["cap"] and comp["lazy"] == "lazy" and comp["below"])
        ok("static front: the weekly feature shows its picture above an italic headline", feat["fig"] == "fig fig-feature" and feat["italic"] and feat["lazy"] == "lazy")
        await ctx.close()

        # ---- JavaScript on: the handover, navigation, loading, reading tools
        ctx = await b.new_context(viewport={"width":390,"height":844}, is_mobile=True, has_touch=True, device_scale_factor=2)
        await ctx.grant_permissions(["clipboard-read", "clipboard-write"])
        page = await ctx.new_page()
        STATE["hits"].clear()
        await page.goto(base + f"/story/{WITH}/", wait_until="load"); await page.wait_for_selector("#reader.on"); await page.wait_for_timeout(800)
        h = hits(f"/assets/editorial/{WITH}/")
        ok("direct navigation: the reader opens on the story, the static copy is gone once the picture has loaded, exactly one hero figure is visible",
           await page.locator("#static").count() == 0 and await page.locator("figure.fig-hero").count() == 1 and await page.evaluate("location.pathname") == f"/story/{WITH}/")
        ok("handover: the hero is fetched from the server once, one derivative, for the static page and the reader together", sum(h.values()) == 1 and list(h)[0].endswith("hero-1200.webp"), h)
        await page.goto(base + "/story/led-20260817-record/", wait_until="load"); await page.wait_for_selector("#reader.on"); await page.wait_for_timeout(300)
        meta = await page.locator("#rwrap .rmeta").text_content()
        ok("reader: the archive label sits above a news headline past a week, and the true date is shown",
           "From the archive" in await page.locator("#rwrap .kicker").text_content() and re.search(r"August 17, 2026|17 August 2026", meta) is not None, meta)
        await page.goto(base + f"/story/{WITH}/", wait_until="load"); await page.wait_for_selector("#reader.on"); await page.wait_for_timeout(300)
        ok("reader: the figure follows the deck and precedes the byline; caption, credit and disclosure present",
           await page.evaluate("(()=>{const w=document.querySelector('#rwrap');const o=[...w.querySelectorAll('h1,.rstand,figure.fig-hero,.rmeta,.rbody')].map(e=>e.matches('figure')?'figure':e.className||'h1');return JSON.stringify(o)})()") == '["h1","rstand","figure","rmeta","rbody"]'
           and await page.locator("#rwrap .fig-ai").count() == 1 and "The Ledger" in await page.locator("#rwrap .fig-credit").text_content())
        t = await page.evaluate("(()=>{const px=e=>parseFloat(getComputedStyle(e).fontSize);return {h1:px(document.querySelector('#rwrap h1')),deck:px(document.querySelector('.rstand')),body:px(document.querySelector('.rbody')),lh:parseFloat(getComputedStyle(document.querySelector('.rbody')).lineHeight),italic:getComputedStyle(document.querySelector('#rwrap h1')).fontStyle}})()")
        ok("typography at 390px, regular size: headline 30–34px upright, deck 18–19.5px, body 20–21px with comfortable leading",
           30 <= t["h1"] <= 34 and 18 <= t["deck"] <= 19.5 and 20 <= t["body"] <= 21 and t["lh"] >= 30 and t["italic"] == "normal", t)
        await page.evaluate("localStorage.setItem('ledger.size','1.2')"); await page.reload(wait_until="load"); await page.wait_for_selector("#reader.on"); await page.wait_for_timeout(500)
        t2 = await page.evaluate("(()=>{const px=e=>parseFloat(getComputedStyle(e).fontSize);return {h1:px(document.querySelector('#rwrap h1')),deck:px(document.querySelector('.rstand')),body:px(document.querySelector('.rbody'))}})()")
        ok("the reader's text-size setting still scales headline, deck and body", t2["body"] > t["body"] and t2["deck"] > t["deck"] and t2["h1"] >= t["h1"], (t, t2))
        await page.evaluate("localStorage.removeItem('ledger.size')")
        await page.goto(base + f"/story/{FEATURE}/", wait_until="load"); await page.wait_for_selector("#reader.on"); await page.wait_for_timeout(400)
        ok("the weekly feature's headline is the italic display face, with the drop cap reserved for it",
           await page.evaluate("getComputedStyle(document.querySelector('#rwrap h1')).fontStyle") == "italic"
           and await page.evaluate("parseFloat(getComputedStyle(document.querySelector('#rwrap .rbody>p:first-of-type'),'::first-letter').fontSize) > 40"))
        await page.goto(base2 + f"/story/{WITHOUT}/", wait_until="load"); await page.wait_for_selector("#reader.on"); await page.wait_for_timeout(400)
        await page.screenshot(path=os.path.join(ROOT, "docs", "design", "shots", "no-image-390.png"), full_page=False)
        ok("fixture: a story without a picture reads text-led in the reader, no figure, no drop cap, byline after the deck",
           await page.locator("#rwrap figure").count() == 0 and await page.evaluate("parseFloat(getComputedStyle(document.querySelector('#rwrap .rbody>p:first-of-type'),'::first-letter').fontSize) < 40"))
        # Listen dock leaves the article's end readable
        await page.click("#rListen"); await page.wait_for_timeout(1200)
        ok("Listen: the reader reserves more than the dock's height below the article",
           await page.evaluate("document.querySelector('#dock').classList.contains('on') && parseFloat(getComputedStyle(document.querySelector('#rwrap')).paddingBottom) >= document.querySelector('#dock').offsetHeight"))
        await page.click("#dClose"); await page.wait_for_timeout(300)
        # back and forward from a direct story load
        await page.goto(base + f"/story/{WITH}/", wait_until="load"); await page.wait_for_selector("#reader.on"); await page.wait_for_timeout(300)
        await page.go_back(); await page.wait_for_timeout(500)
        ok("Back from a directly opened story lands on the front page with the reader closed",
           await page.evaluate("location.pathname") == "/" and not await page.evaluate("document.querySelector('#reader').classList.contains('on')"))
        await page.go_forward(); await page.wait_for_timeout(600)
        ok("Forward reopens the story with its picture", await page.evaluate("location.pathname") == f"/story/{WITH}/" and await page.locator("#reader.on figure.fig-hero img").count() == 1)
        # Save, Copy, Share on a story with a picture
        await page.click("#rSave"); await page.wait_for_timeout(300)
        saved = await page.get_attribute("#rSave", "aria-pressed")
        await page.click("#rCopy"); await page.wait_for_timeout(600)
        clip = await page.evaluate("navigator.clipboard.readText()")
        ok("Save, Copy and Share are unchanged on a story with a picture",
           saved == "true" and "What 4.3% expected inflation" in clip and await page.locator("#rShareLbl").text_content() == "Share")
        await page.click("#rSave"); await page.wait_for_timeout(200)
        # the front page: lazy feature picture loads once scrolled to
        await page.goto(base + "/", wait_until="load"); await page.wait_for_selector("#feed article.card"); await page.wait_for_timeout(500)
        loaded = await page.evaluate("(()=>{const i=document.querySelector('#feed article.weekly img');return i && i.complete && i.naturalWidth>0})()")
        await page.evaluate("document.querySelector('#feed article.weekly').scrollIntoView()"); await page.wait_for_timeout(1200)
        ok("front page: the feature picture is a real image that has loaded once scrolled into view",
           await page.evaluate("(()=>{const i=document.querySelector('#feed article.weekly img');return i && i.complete && i.naturalWidth>0 && Math.round(i.getBoundingClientRect().width)>300})()"))
        ok("front page: the compact thumbnail is 112px wide, 3:2, and the 480px derivative is chosen",
           await page.evaluate("(()=>{const i=document.querySelector('#feed article.compact.has-image img');const r=i.getBoundingClientRect();return Math.round(r.width)===112 && Math.abs(r.width/r.height-1.5)<0.05 && (i.currentSrc||'').endsWith('hero-480.webp')})()"))
        clamp = await page.evaluate("(()=>{const m=e=>{const cs=getComputedStyle(e);return [e.clientHeight, parseFloat(cs.lineHeight), e.scrollHeight]};return {lead:m(document.querySelector('#feed article.lead .standfirst')), comp:m(document.querySelector('#feed article.compact .standfirst'))}})()")
        ok("front page on a phone: the lead's summary shows at most four lines and a supporting story's three, the rest clipped",
           clamp["lead"][0] <= clamp["lead"][1] * 4 + 2 and clamp["lead"][2] > clamp["lead"][0] and clamp["comp"][0] <= clamp["comp"][1] * 3 + 2, clamp)
        ok("front page in the app: one lead picture, two thumbnails, one feature picture — and no more",
           await page.evaluate("[...document.querySelectorAll('#feed article.card figure.fig')].map(f=>f.className.replace('fig ',''))") == ["fig-lead", "fig-thumb", "fig-thumb", "fig-feature"])
        await ctx.close()

        # ---- the worker's picture cache: scoped to the build, bounded, refreshed by a replaced picture
        HERO = f"/assets/editorial/{WITH}/hero-1200.webp"
        ctx = await b.new_context(viewport={"width":390,"height":844}, is_mobile=True, has_touch=True, device_scale_factor=2)
        page = await ctx.new_page()
        await page.goto(base + f"/story/{WITH}/", wait_until="load")
        await wait_for_active_controller(page, timeout=20000)
        await page.reload(wait_until="load"); await page.wait_for_selector("#reader.on")
        # the 1200px derivative, requested through the worker in this very context, is the one the test follows
        await page.evaluate("u => fetch(u).then(r => r.arrayBuffer())", HERO)
        stampA = re.search(r'const BUILD = "([0-9a-f]{8})"', rd("sw.js")).group(1)
        await wait_for_cached_response(page, "ledger-images-v4-" + stampA, HERO)
        img_caches = [k for k in await page.evaluate("caches.keys()") if k.startswith("ledger-images-v")]
        held = await page.evaluate("async k => (await (await caches.open(k)).keys()).map(r=>new URL(r.url).pathname)", img_caches[0]) if img_caches else []
        ok("worker: one image cache, named for this build, holding the 1200px hero after a controlled load",
           len(img_caches) == 1 and stampA in img_caches[0] and HERO in held, (img_caches, held))
        os.makedirs(os.path.join(site, "assets", "editorial", "limit"))
        small = open(os.path.join(site, "assets", "editorial", WITH, "hero-480.webp"), "rb").read()
        for i in range(45): open(os.path.join(site, "assets", "editorial", "limit", f"hero-{i}.webp"), "wb").write(small)
        await page.evaluate("async () => { for (let i=0;i<45;i++) await fetch('/assets/editorial/limit/hero-'+i+'.webp'); }")
        await page.wait_for_timeout(1500)
        n = await page.evaluate("async k => (await (await caches.open(k)).keys()).length", img_caches[0])
        ok("worker: after 45 pictures through it the cache holds at most 40, the oldest gone", 35 <= n <= 40, n)
        # a new build in which this piece's picture was replaced, and nothing else changed
        alt = os.path.join(work, "assets-b"); shutil.copytree(os.path.join(ROOT, "assets", "editorial"), alt)
        for f in ["hero-1200.webp", "hero-768.webp", "hero-480.webp", "hero-1200.jpg"]:
            shutil.copy(os.path.join(alt, FEATURE, f), os.path.join(alt, WITH, f))
        siteb = os.path.join(work, "site-b")
        rb = subprocess.run(["node", os.path.join(ROOT, "build.mjs"), siteb, "--assets", alt], capture_output=True, text=True)
        os.makedirs(os.path.join(siteb, "data")); open(os.path.join(siteb, "data", "feed.json"), "w").write(stub)
        stampB = re.search(r'const BUILD = "([0-9a-f]{8})"', open(os.path.join(siteb, "sw.js")).read()).group(1) if rb.returncode == 0 else ""
        ok("a replaced picture alone gives the build a new stamp", rb.returncode == 0 and stampB and stampB != stampA, (stampA, stampB, rb.stderr[-200:]))
        before_hits = STATE["hits"][HERO]
        STATE["root"] = siteb
        # the app asks for a worker update on every return to the page and hourly; the
        # simulated deployment asks for one now, so the new worker is fetched at once
        # Wait for the different worker itself to activate and control this client.
        # A Promise-returning wait_for_function predicate could resolve false once
        # and still be mistaken for success. Cleanup is checked separately below.
        update = await update_and_wait_for_controller(page)
        activated = update["changed"] and update["state"] == "activated"
        await page.reload(wait_until="load"); await page.wait_for_selector("#reader.on")
        newlen = os.path.getsize(os.path.join(siteb, "assets", "editorial", WITH, "hero-1200.webp"))
        got = await page.evaluate("u => fetch(u).then(r=>r.arrayBuffer()).then(b=>b.byteLength)", HERO)
        keys2 = await page.evaluate("caches.keys()")
        after_hits = STATE["hits"][HERO]
        ok("after the new build, the worker activates and drops every old cache; the same 1200px address then yields the replaced picture, fetched from the server past the HTTP cache's max-age",
           activated and got == newlen and after_hits > before_hits and not any(stampA in k for k in keys2) and all(stampB in k for k in keys2 if k.startswith("ledger-")), (activated, got, newlen, before_hits, after_hits, keys2))
        STATE["root"] = site
        await ctx.close()

        # ---- no horizontal overflow, JS on, at every width
        bad = []
        for w in [320, 360, 390, 430, 768, 1440]:
            ctx = await b.new_context(viewport={"width":w,"height":800}, is_mobile=w < 700, has_touch=w < 700)
            page = await ctx.new_page()
            for p in ["/", f"/story/{WITH}/", f"/story/{FEATURE}/", f"/story/{WITHOUT}/"]:
                await page.goto(base + p, wait_until="load"); await page.wait_for_timeout(500)
                sw_ = await page.evaluate("Math.max(document.documentElement.scrollWidth, (document.querySelector('#reader')||{scrollWidth:0}).scrollWidth)")
                if sw_ > w: bad.append((w, p, sw_))
            await ctx.close()
        ok("no horizontal overflow at 320, 360, 390, 430, 768 and 1440px on the front page and the three pilot stories", not bad, bad)
        await b.close()
    shutil.rmtree(work, ignore_errors=True)

asyncio.run(main())
fails = [r for r in R if r[0] == "FAIL"]
print(f"\n{len(R) - len(fails)}/{len(R)} passed")
sys.exit(1 if fails else 0)
