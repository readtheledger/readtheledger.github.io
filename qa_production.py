"""Attribution checks against built pages and the actual reader.
All browser traffic is fulfilled from local artifacts or aborted; no analytics,
speech API, publisher or live-site request leaves this test.
"""
import asyncio
import copy
import json
import mimetypes
import pathlib
import subprocess
import tempfile
import urllib.parse

from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parent
PUBLIC = "https://readtheledger.github.io"
NOTICE = "From The Ledger archive. A factual review record is not available for this article."
HUMAN = "Reported and written by The Ledger."
ASSISTED = "Drafted with AI assistance from the credited sources and reviewed by The Ledger's editor before publication."
SUFFIXES = ["record", "fed", "consumer", "river", "aitrade", "badnews", "savers", "weekly"]
EXPECTED = {"led-20260817-" + suffix for suffix in SUFFIXES}
checks = []


def ok(name, passed):
    checks.append({"name": name, "pass": bool(passed)})
    print(("PASS " if passed else "FAIL ") + name, flush=True)


def build(out, content_file=None):
    args = ["node", str(ROOT / "build.mjs"), str(out)]
    if content_file:
        args += ["--content", str(content_file)]
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8")


async def main():
    original = json.loads(subprocess.check_output([
        "node", "-e", 'global.window={};require(process.argv[1]);console.log(JSON.stringify(window.LEDGER_CONTENT));',
        str(ROOT / "content.js")], text=True, encoding="utf-8"))
    legacy = [a for a in original["articles"] if a["id"] in EXPECTED]
    ok("all eight audited originals have an explicit legacy category",
       {a["id"] for a in legacy} == EXPECTED and all(a.get("produced") == "legacy-unrecorded" for a in legacy))

    with tempfile.TemporaryDirectory(prefix="ledger-attribution-") as tmp:
        work = pathlib.Path(tmp)
        site = work / "site"
        built = build(site)
        if built.returncode:
            raise RuntimeError(built.stdout + built.stderr)
        ok("real publication builds with the shared attribution asset", (site / "production.js").is_file())

        fixture = copy.deepcopy(legacy[0])
        fixture.update(id="test-reported", produced="reported", date="2026-09-12T12:00:00Z")
        fixture.pop("image", None)
        fixture.pop("updated", None)
        fixture.pop("weekly", None)
        assisted = dict(fixture, id="test-assisted", produced="assisted")
        fixture_file = work / "fixtures.js"
        fixture_file.write_text("window.LEDGER_CONTENT=" + json.dumps({"articles": [fixture, assisted]}) + ";", encoding="utf-8")
        fixture_site = work / "fixtures"
        built = build(fixture_site, fixture_file)
        if built.returncode:
            raise RuntimeError(built.stdout + built.stderr)

        invalid = []
        for value in [None, "", "automated", True]:
            invalid.append(("unsupported " + repr(value), dict(fixture, produced=value)))
        omitted = dict(fixture)
        omitted.pop("produced")
        invalid.append(("omitted new production", omitted))
        omitted_legacy = dict(legacy[0])
        omitted_legacy.pop("produced")
        invalid.append(("omitted archive production", omitted_legacy))
        invalid += [
            ("new ID claiming legacy", dict(fixture, produced="legacy-unrecorded", date=legacy[0]["date"])),
            ("archive ID with a new publication date", dict(legacy[0], date=fixture["date"])),
            ("archive ID with a new edition date", dict(legacy[0], updated=fixture["date"])),
        ]
        for i, (name, article) in enumerate(invalid):
            cf = work / f"invalid-{i}.js"
            cf.write_text("window.LEDGER_CONTENT=" + json.dumps({"articles": [article]}) + ";", encoding="utf-8")
            rejected = build(work / f"invalid-{i}", cf)
            ok(name + " fails the build", rejected.returncode == 1 and
               ("produced must be explicitly set" in rejected.stderr or "legacy-unrecorded is limited" in rejected.stderr))

        async with async_playwright() as pw:
            browser = await pw.chromium.launch()
            async def context_for(artifact, js=True, width=390):
                ctx = await browser.new_context(java_script_enabled=js, service_workers="block",
                                                viewport={"width": width, "height": 844})
                attempts, errors = [], []
                async def route(req):
                    u = urllib.parse.urlsplit(req.request.url)
                    if f"{u.scheme}://{u.netloc}" != PUBLIC:
                        attempts.append(req.request.url)
                        await req.abort()
                        return
                    if u.path == "/data/feed.json":
                        await req.fulfill(json={"schema": 1, "fetched": "2026-09-12T12:00:00Z", "sources": [], "items": []})
                        return
                    path = (artifact / urllib.parse.unquote(u.path).lstrip("/")).resolve()
                    if path.is_dir():
                        path /= "index.html"
                    if not path.is_relative_to(artifact.resolve()) or not path.is_file():
                        await req.fulfill(status=404, body="Not found")
                        return
                    mime = "text/javascript" if path.suffix == ".js" else mimetypes.guess_type(path)[0] or "application/octet-stream"
                    await req.fulfill(body=path.read_bytes(), content_type=mime)
                await ctx.route("**/*", route)
                page = await ctx.new_page()
                page.on("pageerror", lambda e: errors.append(str(e)))
                return ctx, page, attempts, errors

            for js in [False, True]:
                ctx, page, attempts, errors = await context_for(site, js)
                selector = "#rwrap" if js else "#static"
                for a in legacy:
                    await page.goto(PUBLIC + f"/story/{a['id']}/")
                    await page.locator(selector + " .attrline").wait_for(state="visible")
                    line = await page.locator(selector + " .attrline").inner_text()
                    ok(f"{a['id']} {'reader' if js else 'static'} truthful attribution",
                       line.startswith(NOTICE) and HUMAN not in line and ASSISTED not in line and
                       await page.locator(selector + ' .attrline a[href="/about/"]').count() == 1)
                    if js:
                        texts = await page.evaluate("id => {const a=EDITORIAL.find(x=>x.id===id); return [plainText(a),speechText(a)];}", a["id"])
                        ok(a["id"] + " Copy and Listen carry the archive status", all(t.count(NOTICE) == 1 for t in texts))
                    else:
                        ld = await page.locator('script[type="application/ld+json"]').first.text_content()
                        data = json.loads(ld)
                        if isinstance(data, list):
                            data = next(x for x in data if x.get("@type") == "NewsArticle")
                        ok(a["id"] + " dates/headline/sources preserved in static output",
                           data["datePublished"] == a["date"] and data["dateModified"] == a.get("updated", a["date"]) and
                           await page.locator(selector + " h1").inner_text() == a["title"] and
                           await page.locator(selector + " .rstand").inner_text() == a["standfirst"] and
                           await page.locator(selector + " .sourcesbox a").evaluate_all("nodes=>nodes.map(n=>n.href)") == [s["u"] for s in a["sources"]])
                for width in [320, 390, 1440]:
                    await page.set_viewport_size({"width": width, "height": 844})
                    ok(f"{'reader' if js else 'static'} attribution has no horizontal overflow at {width}",
                       await page.evaluate("document.documentElement.scrollWidth <= innerWidth && [...document.querySelectorAll('.attrline')].every(e=>e.scrollWidth<=e.clientWidth)"))
                if js:
                    for name, article in invalid:
                        line = await page.evaluate("a=>{const it=makeEditorial(a);openReader(it);return document.querySelector('#rwrap .attrline').textContent;}", article)
                        ok(name + " stays neutral in runtime reader", "Production status is unavailable." in line and
                           HUMAN not in line and ASSISTED not in line and NOTICE not in line)
                    await page.goto(PUBLIC + "/")
                    await page.wait_for_function("typeof EDITORIAL !== 'undefined'")
                    ok("archive notice does not clutter front-page cards", NOTICE not in await page.locator("#main").inner_text())
                ok(f"{'reader' if js else 'static'} has no browser errors or analytics attempts",
                   not errors and not any("goatcounter" in u or "/count" in u for u in attempts))
                await ctx.close()

            for js in [False, True]:
                ctx, page, attempts, errors = await context_for(fixture_site, js)
                selector = "#rwrap" if js else "#static"
                for a, wanted in [(fixture, HUMAN), (assisted, ASSISTED)]:
                    await page.goto(PUBLIC + f"/story/{a['id']}/")
                    await page.locator(selector + " .attrline").wait_for(state="visible")
                    line = await page.locator(selector + " .attrline").inner_text()
                    ok(f"explicit {a['produced']} {'reader' if js else 'static'} retains semantics", line.startswith(wanted) and NOTICE not in line)
                ok(f"normal {'reader' if js else 'static'} fixtures have no browser errors", not errors)
                await ctx.close()
            await browser.close()

    report = ROOT / "_site" / "qa-production-results.json"
    report.parent.mkdir(exist_ok=True)
    report.write_text(json.dumps({"checks": checks, "passed": sum(c["pass"] for c in checks), "total": len(checks)}, indent=2), encoding="utf-8")
    print(f"{sum(c['pass'] for c in checks)}/{len(checks)} checks passed")
    if not all(c["pass"] for c in checks):
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
