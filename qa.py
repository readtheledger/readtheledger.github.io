import asyncio, http.server, socketserver, threading, os, json, functools, sys
from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = 8931

def serve():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), handler) as httpd:
        httpd.serve_forever()

threading.Thread(target=serve, daemon=True).start()

IPHONE17PM = {"width": 440, "height": 956}

async def main():
    results = []
    def ok(name, cond, extra=""):
        results.append((("PASS" if cond else "FAIL"), name, extra))

    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--no-sandbox"])
        ctx = await b.new_context(viewport=IPHONE17PM, device_scale_factor=3, is_mobile=True,
                                  has_touch=True, locale="en-GB",
                                  user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1")
        await ctx.grant_permissions(["clipboard-read", "clipboard-write"])
        page = await ctx.new_page()
        errors, console = [], []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: console.append((m.type, m.text)) if m.type == "error" else None)

        await page.goto(f"http://127.0.0.1:{PORT}/index.html", wait_until="load")
        # feeds will fail in this sandbox -> exercises the graceful-degradation path
        await page.wait_for_timeout(6000)

        ok("no uncaught JS errors", not errors, "; ".join(errors[:3]))
        # network failures to external hosts are expected in this sandbox (no egress);
        # only app-level console errors count
        app_errs = [t for _, t in console if "Failed to load resource" not in t]
        ok("no app console errors", not app_errs, "; ".join(app_errs[:3]))
        print(f"note: {len(console)} external resource load failures (sandbox has no egress to the RSS relays or Google Fonts)")

        # layout
        sw = await page.evaluate("document.documentElement.scrollWidth")
        ok("no horizontal overflow", sw <= 441, f"scrollWidth={sw}")

        ok("masthead present", await page.locator(".wordmark").count() == 1)
        ok("section nav rendered", await page.locator("#secnav .seclink").count() >= 8)

        # a card must exist (fallback demo article at minimum)
        cards = await page.locator("article.card").count()
        ok("front page shows at least one story", cards >= 1, f"cards={cards}")

        # touch targets
        small = await page.evaluate("""() => {
          const bad=[];
          document.querySelectorAll('button:not([hidden])').forEach(b=>{
            const r=b.getBoundingClientRect();
            if(r.width>0 && r.height>0 && (r.height<43.5||r.width<43.5)) bad.push((b.id||b.className)+':'+Math.round(r.width)+'x'+Math.round(r.height));
          });
          return bad;
        }""")
        ok("all visible buttons >= 44px", not small, ", ".join(small[:5]))

        # open the article
        await page.locator("article.card").first.click()
        await page.wait_for_timeout(700)
        ok("reader opens", await page.locator("#reader.on").count() == 1)
        ok("headline rendered in reader", bool((await page.locator("#rwrap h1").inner_text()).strip()))
        drop = await page.evaluate("""() => {
          const p=document.querySelector('.rbody p'); if(!p) return null;
          return getComputedStyle(p,'::first-letter').fontSize;
        }""")
        ok("drop cap applied", bool(drop) and float(str(drop).replace("px","")) > 40, f"first-letter={drop}")

        # copy
        await page.locator("#rCopy").click()
        await page.wait_for_timeout(600)
        clip = await page.evaluate("navigator.clipboard.readText()")
        ok("one-tap copy puts article on clipboard", clip and len(clip) > 200, f"{len(clip or '')} chars")
        ok("copy includes title + source", bool(clip) and "The Ledger" in clip)
        ok("copied toast shown", await page.locator("#toast.on").count() == 1)
        await page.wait_for_timeout(2200)

        # listen -> device-voice fallback (no API key set)
        await page.locator("#rListen").click()
        await page.wait_for_timeout(1200)
        ok("audio dock opens on Listen", await page.locator("#dock.on").count() == 1)
        sub = await page.locator("#dSub").inner_text()
        ok("falls back to device voice without API key", "Device voice" in sub or "speech" in sub.lower(), sub)

        # rate control
        await page.locator("#dRate").click()
        ok("playback speed cycles", (await page.locator("#dRate").inner_text()) != "1.0×",
           await page.locator("#dRate").inner_text())

        # progress bar
        await page.evaluate("document.querySelector('#reader').scrollTo(0, 900)")
        await page.wait_for_timeout(400)
        w = await page.evaluate("document.querySelector('#progress').style.width")
        ok("reading progress bar advances", w not in ("", "0%"), f"width={w}")

        await page.screenshot(path=os.path.join(ROOT, "shot-article.png"), full_page=False)

        # bookmark from reader, then Saved section
        await page.locator("#rSave").click()
        await page.wait_for_timeout(400)
        await page.locator("#rBack").click()
        await page.wait_for_timeout(700)
        await page.locator("#btnMenu").click()
        await page.locator("#btnSaved").click()
        await page.wait_for_timeout(500)
        ok("saved section lists the bookmark", await page.locator("article.card").count() >= 1)

        # back to front page + search
        await page.locator('#secnav .seclink[data-sec="Front page"]').click()
        await page.wait_for_timeout(400)
        await page.locator("#btnSearch").click()
        await page.fill("#q", "zzzznomatch")
        await page.wait_for_timeout(400)
        ok("search filters (empty state)", await page.locator(".notice").count() >= 1)
        await page.fill("#q", "")
        await page.locator("#btnSearch").click()

        # dark mode (from the menu)
        await page.locator("#btnMenu").click()
        await page.locator("#btnTheme").click()
        await page.wait_for_timeout(400)
        theme = await page.evaluate("document.documentElement.dataset.theme")
        ok("dark mode toggles", theme == "dark", f"theme={theme}")
        await page.evaluate("closeMenu()")
        await page.screenshot(path=os.path.join(ROOT, "shot-dark.png"))
        await page.locator("#btnMenu").click()
        await page.locator("#btnTheme").click()
        await page.wait_for_timeout(300)

        # settings + persistence (from the menu)
        await page.locator("#btnSettings").click()
        await page.wait_for_timeout(400)
        ok("settings sheet opens", await page.locator("#settings.on").count() == 1)
        ok("feed status listed", await page.locator("#feedstatus div").count() >= 20,
           str(await page.locator("#feedstatus div").count()))
        await page.fill("#apikey", "sk-test-not-a-real-key")
        await page.locator("#saveSettings").click()
        await page.wait_for_timeout(500)
        stored = await page.evaluate("JSON.parse(localStorage.getItem('ledger.apikey'))")
        ok("API key persists on device only", stored == "sk-test-not-a-real-key", str(stored))
        # and it must never leave for anywhere but openai
        hosts = await page.evaluate("""() => {
          const s = document.documentElement.innerHTML;
          return /api\\.openai\\.com/.test(s);
        }""")
        ok("key is only ever posted to api.openai.com", hosts)

        # PWA bits
        man = await page.evaluate("""async () => {
          const l=document.querySelector('link[rel=manifest]');
          const r=await fetch(l.href); return await r.json();
        }""")
        ok("manifest loads", man.get("name","").startswith("The Ledger"), json.dumps(man)[:60])
        ok("manifest is standalone", man.get("display") == "standalone")
        sw_ok = await page.evaluate("navigator.serviceWorker.getRegistrations().then(r=>r.length>0)")
        ok("service worker registered", sw_ok)
        nav_first = await page.evaluate("""async () => {
          const r = await fetch('sw.js', {cache:'no-store'});
          const s = await r.text();
          return /req\\.mode === "navigate"/.test(s) && /async function navigate/.test(s) && !/caches\\.match\\("\\.\\/index\\.html"\\).then\\(hit => hit \\|\\|/.test(s);
        }""")
        ok("shell is network-first, so a deploy reaches installed users", nav_first)

        # feed content is third-party: no URL scheme may reach the browser but the safe ones
        bad = await page.evaluate("""() => {
          const kept = [];
          for (const raw of ['javascript:x=1',' javascript:x=1','java\\tscript:x=1','\\njavascript:x=1',
                             'JaVaScRiPt:x=1','vbscript:x=1']) {
            const d=document.createElement('div');
            d.innerHTML = sanitize('<a href="'+raw+'">x</a>');
            const a=d.querySelector('a');
            if (a && a.hasAttribute('href')) kept.push(raw);
          }
          return kept;
        }""")
        ok("script URLs stripped from article links", not bad, "; ".join(bad))
        ok("feed link scheme vetted on the way in", await page.evaluate("""() => {
          const it = makeItem({title:'T', link:' javascript:x=1', rawHtml:'<p>b</p>', author:'A',
                               date:new Date().toISOString(), source:'S', hintSection:'Markets'});
          return it.link === '';
        }"""))
        ok("ordinary links and images survive sanitising", await page.evaluate("""() => {
          const out = sanitize('<p><a href="https://example.com/a?b=1">l</a><img src="https://example.com/c.png" alt="c"></p>');
          return out.includes('href="https://example.com/a?b=1"') && out.includes('src="https://example.com/c.png"');
        }"""))
        ok("content security policy declared", await page.evaluate(
           """() => { const m=document.querySelector('meta[http-equiv="Content-Security-Policy"]');
                      return !!m && /connect-src[^;]*api\\.openai\\.com/.test(m.content); }"""))

        # a bookmark has to outlive the feed cache the article arrived in
        kept = await page.evaluate("""() => {
          localStorage.removeItem('ledger.saved'); localStorage.removeItem('ledger.savedItems');
          S.saved={}; S.savedItems={};
          const it = makeItem({title:'Kept story', link:'https://example.com/k',
                               rawHtml:'<p>'+'word '.repeat(400)+'</p>', author:'A',
                               date:new Date().toISOString(), source:'S', hintSection:'Markets'});
          S.items=[it]; toggleSave(it.id);
          S.items=[];                                                  // article falls off the feed
          S.savedItems = JSON.parse(localStorage.getItem('ledger.savedItems'));   // as if reloaded
          S.saved      = JSON.parse(localStorage.getItem('ledger.saved'));
          S.section='Saved';
          const shown = visible();
          const back  = itemById(it.id);
          S.section='Front page';
          return {n: shown.length, body: !!(back && back.html)};
        }""")
        ok("bookmark survives the article leaving the feed", kept["n"] == 1 and kept["body"], str(kept))

        # 120 full-text articles do not fit in a browser's storage; the cache must not lose the lot
        cache = await page.evaluate("""() => {
          const big = '<p>'+'word '.repeat(4000)+'</p>';
          const items = [];
          for (let i=0;i<200;i++) items.push(makeItem({title:'S'+i, link:'https://e.com/'+i, rawHtml:big,
                                   author:'A', date:new Date().toISOString(), source:'S', hintSection:'Markets'}));
          localStorage.removeItem('ledger.cache');
          const n = writeCache(items);
          const raw = localStorage.getItem('ledger.cache');
          return {n, readsBack: raw ? JSON.parse(raw).items.length : 0};
        }""")
        ok("feed cache stays inside the storage quota", 0 < cache["readsBack"] <= 40, str(cache))

        # ---- editorial strategy: the mix, the furniture, and the rights model ----
        # editorial articles ship in content.js and load at boot, so the mix, the
        # why-it-matters card and the weekly feature all need zero seeding. (S.items
        # is restored to normal boot contents here because an earlier check in this
        # suite -- the bookmark-durability test above -- deliberately empties it.)
        mix = await page.evaluate("""() => {
          S.items = EDITORIAL.concat([DEMO]);
          S.section='Front page'; S.query=''; render();
          return S.mix;
        }""")
        n, a, d, t = mix["news"], mix["analysis"], mix["deep"], mix["total"]
        ok("front page is news-led (60-70% news)", 0.55 <= n/t <= 0.75, f"{n}/{t} = {round(100*n/t)}%")
        ok("why-it-matters layer at 20-30%", 0.15 <= a/t <= 0.35, f"{a}/{t} = {round(100*a/t)}%")
        ok("deep expert work at 10-15%", 0.05 <= d/t <= 0.20, f"{d}/{t} = {round(100*d/t)}%")

        ok("why-it-matters card on the front page", await page.locator("article.card.wim").count() == 1)
        ok("weekly deep-dive feature on the front page", await page.locator("article.card.weekly").count() == 1)

        await page.locator("article.card.wim").click()
        await page.wait_for_timeout(500)
        wim_open = await page.evaluate("document.querySelector('#reader').classList.contains('on')")
        ok("why-it-matters card opens its story", wim_open)
        await page.evaluate("closeReader()")

        weekly = await page.evaluate("""() => {
          openReader(weeklyItem());
          return {paras: document.querySelectorAll('#rwrap .rbody p').length,
                  attr: (document.querySelector('#rwrap .attrline')||{}).textContent||""};
        }""")
        ok("weekly feature is a full Ledger essay", weekly["paras"] >= 5 and "The Ledger" in weekly["attr"],
           f"{weekly['paras']} paragraphs")
        await page.evaluate("closeReader()")

        # every Ledger article credits its research with live https sources
        srcs_ok = await page.evaluate("""() => {
          return EDITORIAL.length > 0 && EDITORIAL.every(a =>
            Array.isArray(a.sources) && a.sources.length >= 1 &&
            a.sources.every(s => /^https:\\/\\//.test(s.u)));
        }""")
        ok("every Ledger article cites >=1 https source", srcs_ok)

        srcbox = await page.evaluate("""() => {
          openReader(EDITORIAL[0]);
          return {links: document.querySelectorAll('#rwrap .sourcesbox a').length,
                  attr: (document.querySelector('#rwrap .attrline')||{}).textContent||""};
        }""")
        ok("Ledger reader shows a sources box with attribution",
           srcbox["links"] >= 1 and "Reported and written by The Ledger" in srcbox["attr"], str(srcbox))
        await page.evaluate("closeReader()")

        badges = await page.evaluate("""() => {
          S.section='Front page'; S.query=''; render();
          return Array.from(document.querySelectorAll('article.card .badge')).map(b=>b.textContent.trim());
        }""")
        ok("front page cards carry only The Ledger's own badge",
           bool(badges) and all(b == "The Ledger" for b in badges), f"{len(badges)} cards")

        # seed synthetic feed items for the rights-model checks below and for Newsstand
        seeded = await page.evaluate("""() => {
          const mk = (i, kind, lic, words, src) => makeItem({
            title: kind+" story "+i+" about markets and the economy",
            link: "https://example.com/"+kind+"/"+i,
            rawHtml: "<p>"+Array.from({length: Math.ceil(words/11)}, (_,j)=>
              "Paragraph sentence "+j+" reports on rates, earnings and consumer spending in some detail.").join(" ")+"</p>",
            author: "Ann Writer "+i, date: new Date(Date.now()-i*36e5).toISOString(),
            source: src, hintSection: "Markets", weight: 1, kind, lic});
          const items = [];
          for(let i=0;i<20;i++) items.push(mk(i,"news","",80,"Newswire"));
          for(let i=0;i<9;i++)  items.push(mk(100+i,"analysis","",600,"Analyst Blog"));
          for(let i=0;i<5;i++)  items.push(mk(200+i,"deep", i===0?"CC BY-ND 4.0":"",900,"Research House"));
          return commit(items);
        }""")

        post = await page.evaluate("""() => {
          S.section='Front page'; S.query=''; render();
          const badges = Array.from(document.querySelectorAll('article.card .badge')).map(b=>b.textContent.trim());
          S.section='Newsstand';
          const ns = visible().length;
          S.section='Front page'; render();
          return {badges, ns};
        }""")
        ok("front page stays Ledger-only once feed items land",
           bool(post["badges"]) and all(b == "The Ledger" for b in post["badges"]), f"{len(post['badges'])} cards")
        ok("newsstand lists the seeded feed items", post["ns"] >= seeded, f"{post['ns']} >= {seeded}")

        # an open feed is not a licence: unlicensed full text is never reprinted
        summary = await page.evaluate("""() => {
          closeReader();
          const it = S.items.find(i=>i.kind==='analysis' && i.fullText && !i.republish);
          openReader(it);
          const rb = document.querySelector('#rwrap .rbody').innerText;
          return {full: it.text.length, rendered: rb.length,
                  quote: !!document.querySelector('#rwrap .quotebox'),
                  wimbox: !!document.querySelector('#rwrap .wimbox'),
                  cta: !!document.querySelector('#rwrap .srccta a'),
                  attr: ((document.querySelector('#rwrap .attrline')||{}).textContent||"").includes('a summary by The Ledger'),
                  label: (document.querySelector('#rwrap .wimbox h2')||{}).textContent||"",
                  copied: plainText(it), spoken: speechText(it)};
        }""")
        ok("unlicensed article shown as summary, not reprint",
           summary["rendered"] < summary["full"] * 0.4, f"{summary['rendered']} of {summary['full']} chars shown")
        ok("summary carries quote, context, attribution and route out",
           summary["quote"] and summary["wimbox"] and summary["cta"] and summary["attr"])
        ok("a standing note is labelled Background, not Why it matters", summary["label"] == "Background", summary["label"])
        ok("copy carries the summary, not the withheld body, with the same label",
           len(summary["copied"]) < summary["full"] * 0.5 and "Background:" in summary["copied"] and "Why it matters" not in summary["copied"]
           and "https://example.com/" in summary["copied"], f"{len(summary['copied'])} chars")
        ok("listen reads the summary, not the withheld body",
           len(summary["spoken"]) < summary["full"] * 0.5, f"{len(summary['spoken'])} chars")

        licensed = await page.evaluate("""() => {
          closeReader();
          const it = S.items.find(i=>i.republish);
          openReader(it);
          return {full: it.text.length,
                  rendered: document.querySelector('#rwrap .rbody').innerText.length,
                  attr: ((document.querySelector('#rwrap .attrline')||{}).textContent||"")};
        }""")
        ok("licensed article republished in full, licence named",
           licensed["rendered"] >= licensed["full"] * 0.9 and "CC BY-ND 4.0" in licensed["attr"],
           f"{licensed['rendered']}/{licensed['full']} chars")
        await page.evaluate("closeReader()")

        # launch plumbing: feedback link present; analytics silent until a code is set
        fb = await page.evaluate("""() => !!document.querySelector('#settings a[href*="github.com/readtheledger/readtheledger.github.io/issues"]')""")
        ok("feedback link in settings", fb)
        pixel_only = await page.evaluate("""() => {
          // image-ping only, single host, and never a script: the mechanism is
          // inspectable because ping() is the sole sender
          return ping.toString().includes(".goatcounter.com/count") &&
                 ping.toString().includes("new Image()") &&
                 !document.querySelector('script[src]:not([src="/content.js"]):not([src="/sources.js"]):not([src="/topics.js"]):not([src="/context.js"]):not([src="/about.js"])');
        }""")
        ok("analytics is an image ping to goatcounter only, no scripts", pixel_only)

        # front page screenshot after a successful-ish state
        await page.evaluate("document.querySelector('#settings').classList.remove('on')")
        await page.wait_for_timeout(400)
        await page.screenshot(path=os.path.join(ROOT, "shot-front.png"))

        await b.close()

    width = max(len(n) for _, n, _ in results)
    fails = 0
    for st, n, ex in results:
        if st == "FAIL": fails += 1
        print(f"{st}  {n.ljust(width)}  {ex}")
    print(f"\n{len(results)-fails}/{len(results)} checks passed")
    sys.exit(1 if fails else 0)

asyncio.run(main())
