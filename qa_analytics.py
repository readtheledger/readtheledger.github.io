"""Analytics contract tests: every browser request is fulfilled or aborted locally.
No request reaches GoatCounter, the live site, publishers or an ad service.
Run after installing Playwright Chromium: python qa_analytics.py
"""
import asyncio, json, mimetypes, os, pathlib, subprocess, urllib.parse
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / ".qa" / "analytics-site"
PUBLIC = "https://readtheledger.github.io"
COLLECTOR = "https://theledger.goatcounter.com"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130.0.0.0 Safari/537.36"
KEY = "ledger.analytics.exclude"
FEED = {"schema": 1, "fetched": "2026-09-12T12:00:00Z", "sources": [], "items": [
    {"id": "fixture-a", "title": "A source report on company earnings", "source": "Fixture",
     "origin": "Fixture", "date": "2026-09-12T10:00:00Z", "link": "https://example.org/private-source",
     "section": "Companies", "kind": "news", "rights": "summary", "html": "<p>Company earnings improved.</p>"},
    {"id": "fixture-b", "title": "A second source report on inflation", "source": "Fixture",
     "origin": "Fixture", "date": "2026-09-12T09:00:00Z", "link": "https://example.org/second",
     "section": "Economics", "kind": "news", "rights": "summary", "html": "<p>Consumer prices changed.</p>"}
]}
checks = []
def ok(name, condition, detail=""):
    checks.append({"name": name, "pass": bool(condition), "detail": detail})
    print(("PASS " if condition else "FAIL ") + name, flush=True)

async def main():
    subprocess.run(["node", str(ROOT / "build.mjs"), str(OUT)], check=True)
    content = json.loads(subprocess.check_output(["node", "-e",
        'global.window={};require(process.argv[1]);console.log(JSON.stringify(window.LEDGER_CONTENT));',
        str(ROOT / "content.js")], text=True))
    a, b = [it["id"] for it in content["articles"][:2]]
    ap, bp = f"/story/{a}/", f"/story/{b}/"
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        async def fixture(*, human=True, origin=PUBLIC, init="", width=390, configured=True):
            context = await browser.new_context(user_agent=UA, service_workers="block",
                                                viewport={"width": width, "height": 844})
            if human:
                await context.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>false});")
            if init:
                await context.add_init_script(init)
            requests, errors = [], []
            async def handle(route):
                req = route.request
                u = urllib.parse.urlsplit(req.url)
                req_origin = f"{u.scheme}://{u.netloc}"
                if req_origin == COLLECTOR:
                    requests.append({"url": req.url, "headers": await req.all_headers(), "type": req.resource_type})
                    await route.abort()
                    return
                if req_origin != origin:
                    await route.abort()
                    return
                if u.path == "/data/feed.json":
                    await route.fulfill(json=FEED)
                    return
                relative = urllib.parse.unquote(u.path).lstrip("/")
                path = (OUT / relative).resolve()
                if path.is_dir():
                    path = path / "index.html"
                if not path.is_relative_to(OUT.resolve()) or not path.is_file():
                    await route.fulfill(status=404, body="Not found")
                    return
                mime = "text/javascript" if path.suffix == ".js" else mimetypes.guess_type(str(path))[0] or "application/octet-stream"
                body = path.read_bytes()
                # Only the locally fulfilled fixture has a configured collector.
                # Production source stays unconfigured; no live traffic can escape.
                if configured and path.suffix == ".html":
                    body = body.replace(b'const GC_SITE = "";', b'const GC_SITE = "theledger";')
                await route.fulfill(body=body, content_type=mime, headers={"Cache-Control": "no-store"})
            await context.route("**/*", handle)
            page = await context.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            return context, page, requests, errors

        def paths(reqs):
            return [urllib.parse.parse_qs(urllib.parse.urlsplit(r["url"]).query)["p"][0] for r in reqs]
        async def settle(page):
            await page.wait_for_timeout(120)
        async def navigate(page, url):
            await page.goto(url)
            await page.wait_for_function("typeof ANALYTICS !== 'undefined' && typeof S !== 'undefined'")
            await settle(page)

        ctx, page, requests, errors = await fixture()
        await navigate(page, PUBLIC + ap + "?q=private-search&token=secret#private-fragment")
        ok("direct original startup emits once, canonical path only", paths(requests) == [ap], paths(requests))
        await page.evaluate("history.back()")
        await page.wait_for_function("!document.querySelector('#reader').classList.contains('on')")
        await settle(page)
        ok("deep-link Back emits home once", paths(requests) == [ap, "/"])
        await page.evaluate("history.forward()")
        await page.wait_for_function("document.querySelector('#reader').classList.contains('on')")
        await settle(page)
        ok("Forward emits the original once", paths(requests) == [ap, "/", ap])
        await page.evaluate("(id)=>openReader(EDITORIAL.find(a=>a.id===id))", b)
        await settle(page)
        ok("story-to-story navigation emits destination once", paths(requests)[-1:] == [bp] and len(requests) == 4)
        await page.evaluate("history.back()")
        await page.wait_for_function("(id)=>S.current.id===id", arg=a)
        await settle(page)
        ok("Back between stories emits destination once", paths(requests)[-1:] == [ap] and len(requests) == 5)
        await page.reload()
        await settle(page)
        ok("reload is a new emission even immediately", paths(requests)[-1:] == [ap] and len(requests) == 6)
        await page.evaluate("window.dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true}))")
        await settle(page)
        ok("bfcache restoration emits one new visible entry", len(requests) == 7 and paths(requests)[-1] == ap)
        ok("all payloads use only existing p and rnd fields", all(set(urllib.parse.parse_qs(urllib.parse.urlsplit(r["url"]).query)) == {"p", "rnd"} for r in requests))
        ok("no title/search/query/fragment or referrer leaks", all("referer" not in r["headers"] and "secret" not in r["url"] and "private" not in r["url"] for r in requests))
        ok("collector transport remains image requests", all(r["type"] == "image" for r in requests))
        ok("deep-link/history run has no uncaught errors", not errors, errors)
        await ctx.close()

        ctx, page, requests, errors = await fixture()
        await page.goto(PUBLIC + "/markets/?q=private-search#private-fragment",
                        referer="https://example.org/private/path?token=secret")
        await settle(page)
        ok("incoming private referrer is not forwarded", len(requests) == 1 and
           "referer" not in requests[0]["headers"] and paths(requests) == ["/markets/"] and
           set(urllib.parse.parse_qs(urllib.parse.urlsplit(requests[0]["url"]).query)) == {"p", "rnd"})
        await page.evaluate("ANALYTICS.visit('bad','/?token=secret'); ANALYTICS.visit('bad2','https://user:pass@example.org/private')")
        await settle(page)
        ok("unapproved paths and arbitrary URLs cannot be emitted", len(requests) == 1)
        await ctx.close()

        ctx, page, requests, errors = await fixture(init="Object.defineProperty(document,'prerendering',{configurable:true,get:()=>true});")
        await navigate(page, PUBLIC + ap)
        ok("prerender does not emit", not requests)
        await page.evaluate("Object.defineProperty(document,'prerendering',{get:()=>false}); document.dispatchEvent(new Event('prerenderingchange'))")
        await settle(page)
        ok("prerender activation emits the visible original once", paths(requests) == [ap])
        await ctx.close()

        ctx, page, requests, errors = await fixture()
        await navigate(page, PUBLIC + "/")
        await page.locator(f'#feed a[href="{ap}"]').first.click()
        await settle(page)
        ok("home-to-story click emits one pageview", paths(requests) == ["/", ap])
        await page.locator("#rBack").click()
        await page.wait_for_function("!document.querySelector('#reader').classList.contains('on')")
        await settle(page)
        await page.locator(f'#feed a[href="{ap}"]').first.click()
        await settle(page)
        ok("legitimate immediate revisit is not time-deduped", paths(requests) == ["/", ap, "/", ap])
        await page.evaluate("closeReader()")
        await page.evaluate("showSection('Markets')")
        await settle(page)
        ok("topic navigation counts its public section path", paths(requests)[-2:] == ["/", "/markets/"])
        n = len(requests)
        await page.evaluate("showSection('Markets'); render(); syncAddress()")
        await settle(page)
        ok("same section and rerender don't emit again", len(requests) == n)
        await page.locator("#btnSearch").click()
        await page.locator("#q").fill("sensitive budget token")
        await page.locator("#q").press("Enter")
        await page.locator("#btnSearch").click()
        await page.locator("#btnMenu").click()
        await page.locator("#btnSettings").click()
        await page.locator("#segSize button").first.click()
        await page.keyboard.press("Escape")
        await settle(page)
        ok("search, overlays and settings do not count", len(requests) == n)
        await page.evaluate("showSection('Newsstand')")
        await page.wait_for_function("()=>S.items.some(i=>i.link==='https://example.org/private-source')")
        await settle(page)
        ok("Newsstand uses fixed aggregate label without query", paths(requests)[-1] == "/newsstand/")
        await page.evaluate("openReader(S.items.find(i=>i.link==='https://example.org/private-source'))")
        await settle(page)
        await page.evaluate("openReader(S.items.find(i=>i.link==='https://example.org/second'))")
        await settle(page)
        ok("distinct Newsstand readers emit aggregate views without IDs/links", paths(requests)[-2:] == ["/newsstand/reader/"] * 2)
        await page.evaluate("history.back()")
        await page.wait_for_function("()=>S.current.link==='https://example.org/private-source'")
        await settle(page)
        ok("Newsstand history emits the restored aggregate reader", paths(requests)[-1] == "/newsstand/reader/")
        await page.evaluate("closeReader(); showSection('Saved')")
        await settle(page)
        ok("Saved counts only its fixed view label", paths(requests)[-1] == "/saved/")
        ok("navigation run has no uncaught errors", not errors, errors)
        await ctx.close()

        ctx, page, requests, errors = await fixture()
        await navigate(page, PUBLIC + "/about/")
        ok("About deep link emits once", paths(requests) == ["/about/"])
        control = page.locator("#rwrap [data-analytics-exclude]")
        await control.check()
        n = len(requests)
        await page.evaluate("(id)=>openReader(EDITORIAL.find(a=>a.id===id))", a)
        await page.reload()
        await settle(page)
        ok("opt-out prevents requests and persists across reload", len(requests) == n and await page.evaluate(f"localStorage.getItem('{KEY}')") == "1")
        await page.evaluate("openReader(DEMO)")
        await settle(page)
        ok("About reports stored exclusion", await control.is_checked() and "excluded" in await page.locator("#rwrap [data-analytics-status]").inner_text())
        await control.uncheck()
        await settle(page)
        ok("re-enabling is not itself a pageview", len(requests) == n)
        await page.evaluate("(id)=>openReader(EDITORIAL.find(a=>a.id===id))", b)
        await settle(page)
        ok("next navigation counts after re-enable", len(requests) == n + 1 and paths(requests)[-1] == bp)
        await page.reload()
        await settle(page)
        ok("re-enabled preference persists after reload", len(requests) == n + 2)
        await page.evaluate("openReader(DEMO)")
        await control.check()
        second = await ctx.new_page()
        await second.goto(PUBLIC + "/about/")
        await settle(second)
        n = len(requests)
        ok("second tab starts excluded", await second.locator("#rwrap [data-analytics-exclude]").is_checked())
        await second.locator("#rwrap [data-analytics-exclude]").uncheck()
        await settle(page)
        ok("cross-tab reversal updates the original control", not await control.is_checked())
        await second.locator("#rwrap [data-analytics-exclude]").check()
        await settle(page)
        await page.evaluate("(id)=>openReader(EDITORIAL.find(a=>a.id===id))", a)
        await settle(page)
        ok("cross-tab exclusion prevents subsequent requests", len(requests) == n)
        await page.evaluate("openReader(DEMO)")
        await page.locator("#rwrap .analytics-choice").scroll_into_view_if_needed()
        box = await page.locator("#rwrap .analytics-choice").bounding_box()
        ok("opt-out label has a 44px mobile target", box["height"] >= 44)
        await page.screenshot(path=str(ROOT / ".qa" / "analytics-about-390.png"))
        await page.set_viewport_size({"width": 1440, "height": 960})
        await page.locator("#rwrap .analytics-choice").scroll_into_view_if_needed()
        await page.screenshot(path=str(ROOT / ".qa" / "analytics-about-1440.png"))
        ok("no horizontal overflow at desktop width", await page.evaluate("document.documentElement.scrollWidth<=innerWidth"))
        ok("opt-out run has no uncaught errors", not errors, errors)
        await ctx.close()

        cases = [
            ("localhost is excluded", "http://127.0.0.1:8939", True, ""),
            ("preview host is excluded", "https://preview.example.org", True, ""),
            ("lookalike host is excluded", "https://readtheledger.github.io.example.org", True, ""),
            ("automated browser is excluded", PUBLIC, False, ""),
            ("legacy GoatCounter browser exclusion is honored", PUBLIC, True, "localStorage.setItem('skipgc','t');"),
            ("unreadable preference fails closed", PUBLIC, True,
             "const get=Storage.prototype.getItem;Storage.prototype.getItem=function(k){if(k==='ledger.analytics.exclude')throw Error('denied');return get.call(this,k)};"),
        ]
        for label, origin, human, init in cases:
            ctx, page, requests, errors = await fixture(human=human, origin=origin, init=init)
            await navigate(page, origin + ap)
            await page.evaluate("closeReader(); showSection('Newsstand'); openReader(DEMO)")
            await settle(page)
            ok(label, not requests and not errors, {"requests": paths(requests), "errors": errors})
            await ctx.close()

        for view, expected in [("/?view=newsstand&q=never-send", "/newsstand/"),
                               ("/?view=saved&q=never-send", "/saved/"),
                               ("/markets/?q=never-send", "/markets/")]:
            ctx, page, requests, errors = await fixture()
            await navigate(page, PUBLIC + view)
            ok("direct view starts once: " + expected, paths(requests) == [expected])
            await ctx.close()

        ctx, page, requests, errors = await fixture(init="""
            const set=Storage.prototype.setItem;
            Storage.prototype.setItem=function(k,v){if(k==='ledger.analytics.exclude')throw Error('full');return set.call(this,k,v)};
        """)
        await navigate(page, PUBLIC + "/about/")
        n = len(requests)
        await page.locator("#rwrap [data-analytics-exclude]").check()
        await page.evaluate("(id)=>openReader(EDITORIAL.find(a=>a.id===id))", a)
        await page.evaluate("openReader(DEMO)")
        await settle(page)
        ok("failed preference write pauses this document and explains persistence limit",
           len(requests) == n and "could not save or read" in await page.locator("#rwrap [data-analytics-status]").inner_text())
        await ctx.close()

        ctx, page, requests, errors = await fixture(configured=False)
        await navigate(page, PUBLIC + ap)
        await page.evaluate("closeReader(); showSection('Newsstand'); openReader(DEMO)")
        await page.locator("#rwrap [data-analytics-exclude]").check()
        await page.locator("#rwrap [data-analytics-exclude]").uncheck()
        await page.reload()
        await settle(page)
        ok("shipped configuration never emits, even after enabling browser visits", not requests and not errors)
        ok("shipped About truthfully says collection is off", "collection is off" in await page.locator("#rwrap [data-analytics-status]").inner_text())
        await page.locator("#rwrap .analytics-choice").scroll_into_view_if_needed()
        await page.screenshot(path=str(ROOT / ".qa" / "analytics-disabled-390.png"))
        await ctx.close()
        await browser.close()
    report = ROOT / ".qa" / "analytics-results.json"
    report.write_text(json.dumps({"passed": sum(c["pass"] for c in checks), "total": len(checks), "checks": checks}, indent=2), encoding="utf-8")
    print(f"{sum(c['pass'] for c in checks)}/{len(checks)} checks passed; collector requests all intercepted")
    if not all(c["pass"] for c in checks):
        raise SystemExit(1)

if __name__ == "__main__":
    asyncio.run(main())
