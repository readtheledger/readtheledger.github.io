"""Editorial media: a piece's own picture, rendered once by media.js for the static
page and the reader, with its caption, credit and disclosure; the card variants
(lead, compact with a thumbnail, feature); the text-led state for a piece with no
picture; the handover from the static page to the reader without a second
fetch or a duplicate figure; lazy loading below the fold; typography at 390px
and under the reader's text-size setting; the Listen dock's reserved space; no
horizontal overflow from 320 to 1440px; Save, Copy and Share unchanged; and
the worker's bounded image cache. Builds from the real content.js.

    python3 qa_media.py            # needs playwright (chromium) and node
"""
import asyncio, http.server, socketserver, threading, os, sys, json, subprocess, re, urllib.parse, tempfile, shutil, collections
from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = 8943
SITE_URL = "https://readtheledger.github.io"
STATE = {"root": None, "hits": collections.Counter()}
TYPES = {".html":"text/html; charset=utf-8", ".js":"text/javascript; charset=utf-8", ".json":"application/json", ".webp":"image/webp", ".jpg":"image/jpeg",
         ".webmanifest":"application/manifest+json", ".png":"image/png", ".xml":"application/xml; charset=utf-8", ".txt":"text/plain; charset=utf-8"}
class Pages(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        root = STATE["root"]; p = urllib.parse.urlparse(self.path).path
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
        self.send_header("Cache-Control", "no-store"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
def serve():
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("127.0.0.1", PORT), Pages) as s: s.serve_forever()

R = []
def ok(name, cond, note=""):
    R.append(("PASS" if cond else "FAIL", name, note)); print(("PASS " if cond else "FAIL ") + name + (("  — " + str(note)) if (note and not cond) else ""))
def lds(html): return [json.loads(m) for m in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)]
def hits(prefix): return {k: v for k, v in STATE["hits"].items() if k.startswith(prefix)}

WITH = "led-20260817-savers"; FEATURE = "led-20260817-weekly"; WITHOUT = "led-20260817-fed"

async def main():
    work = tempfile.mkdtemp(prefix="ledger-media-"); site = os.path.join(work, "site")
    # the real publication, with one piece's picture taken away for the text-led state
    src = open(os.path.join(ROOT, "content.js"), encoding="utf-8").read()
    stripped = re.sub(r'(id:\s*"%s",\n\s*)image:\{[^\n]*\},\n' % WITHOUT, r"\1", src)
    assert stripped != src, "fixture: could not remove the picture from " + WITHOUT
    cf = os.path.join(work, "content.js"); open(cf, "w", encoding="utf-8").write(stripped)
    r = subprocess.run(["node", os.path.join(ROOT, "build.mjs"), site, "--content", cf], capture_output=True, text=True)
    if r.returncode: print(r.stdout, r.stderr); sys.exit("build failed")
    print(r.stdout.strip().splitlines()[-1])
    os.makedirs(os.path.join(site, "data")); open(os.path.join(site, "data", "feed.json"), "w").write('{"fetched":"2026-09-12T14:00:00Z","sources":[],"items":[]}')
    STATE["root"] = site
    threading.Thread(target=serve, daemon=True).start()
    base = f"http://127.0.0.1:{PORT}"
    rd = lambda *p: open(os.path.join(site, *p), encoding="utf-8").read()

    # ---- the built pages
    sw = rd("sw.js")
    ok("worker: media.js precached, pictures never precached, bounded image cache of its own",
       '"/media.js"' in sw and "assets/editorial" not in re.search(r"const FILES = \[(.*?)\];", sw, re.S).group(1) and "IMAGE_KEEP" in sw and 'startsWith("/assets/editorial/")' in sw)
    html = rd("story", WITH, "index.html"); L = lds(html)
    im = L[0]["image"][0]
    ok("story with a picture: NewsArticle.image is the piece's own derivative with size, credit and AI source type",
       im["url"] == f"{SITE_URL}/assets/editorial/{WITH}/hero-1200.jpg" and im["width"] == 1200 and im["creditText"] == "The Ledger" and "trainedAlgorithmicMedia" in im["digitalSourceType"])
    ok("story with a picture: sharing preview is the piece's own picture, large card",
       f'property="og:image" content="{SITE_URL}/assets/editorial/{WITH}/hero-1200.jpg"' in html and 'twitter:card" content="summary_large_image"' in html and 'og:image:alt' in html)
    html2 = rd("story", WITHOUT, "index.html"); L2 = lds(html2)
    ok("story without a picture: no NewsArticle.image, icon only as the sharing preview, no figure",
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
        await page.goto(base + f"/story/{WITHOUT}/")
        order = await page.evaluate("[...document.querySelectorAll('#static .kicker, #static h1, #static .rstand, #static figure, #static .rmeta, #static .rbody')].map(e=>e.matches('figure')?'figure':e.className||e.tagName.toLowerCase())")
        ok("static story without a picture: text-led, same order, nothing left empty", order == ["kicker", "h1", "rstand", "rmeta", "rbody"], order)
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
        await page.goto(base + f"/story/{WITHOUT}/", wait_until="load"); await page.wait_for_selector("#reader.on"); await page.wait_for_timeout(400)
        await page.screenshot(path=os.path.join(ROOT, "docs", "design", "shots", "no-image-390.png"), full_page=False)
        ok("a story without a picture reads text-led in the reader, no figure, no drop cap, byline after the deck",
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
        ok("front page in the app: one lead picture, two thumbnails, one feature picture — and no more",
           await page.evaluate("[...document.querySelectorAll('#feed article.card figure.fig')].map(f=>f.className.replace('fig ',''))") == ["fig-lead", "fig-thumb", "fig-thumb", "fig-feature"])
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
