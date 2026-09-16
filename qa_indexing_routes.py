"""Focused history, canonical and robots regressions for the app reader.

The test builds a private local artifact, blocks every non-local request, and
checks direct and in-app routing at the 390px mobile width. It intentionally
does not exercise Search Console or a public Imperium Post URL.
"""
import asyncio
import functools
import http.server
import os
import shutil
import socketserver
import subprocess
import tempfile
import threading

from playwright.async_api import async_playwright


ROOT = os.path.dirname(os.path.abspath(__file__))
SITE_URL = "https://imperiumpost.com"
INDEX = "index,follow,max-image-preview:large"
NOINDEX = "noindex,follow"
TAX_ID = "led-missed-september-15-tax-instalment"
PUDDERY_ID = "led-puddery-viral-comeback"
TAX = f"/story/{TAX_ID}/"
PUDDERY = f"/story/{PUDDERY_ID}/"

RESULTS = []


def ok(name, condition, detail=""):
    RESULTS.append(("PASS" if condition else "FAIL", name, detail))
    print(f"{'PASS' if condition else 'FAIL'}  {name}" + (f" — {detail}" if detail else ""))


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


class QuietServer(socketserver.ThreadingTCPServer):
    def handle_error(self, _request, _client_address):
        pass


HISTORY_PROBE = r"""
(() => {
  window.__routeLog = [{op:"document", url:location.pathname + location.search + location.hash}];
  for (const name of ["replaceState", "pushState"]) {
    const original = history[name].bind(history);
    history[name] = function(state, title, url) {
      const answer = original(state, title, url);
      window.__routeLog.push({op:name, url:location.pathname + location.search + location.hash,
                              state:JSON.parse(JSON.stringify(history.state || {}))});
      return answer;
    };
  }
  addEventListener("popstate", () => window.__routeLog.push({op:"popstate",
    url:location.pathname + location.search + location.hash,
    state:JSON.parse(JSON.stringify(history.state || {}))}));
})();
"""


async def snapshot(page):
    return await page.evaluate("""() => ({
      url: location.pathname + location.search + location.hash,
      canonical: document.querySelector('link[rel="canonical"]').href,
      robots: document.querySelector('#robotsMeta').content,
      reader: document.querySelector('#reader').classList.contains('on'),
      state: JSON.parse(JSON.stringify(history.state || {})),
      log: window.__routeLog || [],
      overflow: document.documentElement.scrollWidth > innerWidth
    })""")


def no_manufactured_home(log):
    return not any(entry.get("url") == "/" for entry in log)


def safe_remove_test_dir(path):
    resolved = os.path.realpath(path)
    temp_root = os.path.realpath(tempfile.gettempdir())
    if os.path.commonpath([temp_root, resolved]) != temp_root or not os.path.basename(resolved).startswith("ledger-indexing-routes-"):
        raise RuntimeError(f"refusing to remove unexpected test directory: {resolved}")
    shutil.rmtree(resolved, ignore_errors=True)


async def main():
    work = tempfile.mkdtemp(prefix="ledger-indexing-routes-")
    site = os.path.join(work, "site")
    build = subprocess.run(["node", os.path.join(ROOT, "build.mjs"), site],
                           cwd=ROOT, capture_output=True, text=True)
    if build.returncode:
        print(build.stdout)
        print(build.stderr)
        raise SystemExit("build failed")
    print(build.stdout.strip())

    handler = functools.partial(QuietHandler, directory=site)
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    server = QuietServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    blocked = []
    finished = []
    page_errors = []

    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch()
            context = await browser.new_context(viewport={"width": 390, "height": 844},
                                                is_mobile=True, has_touch=True,
                                                service_workers="block")

            async def local_only(route):
                if route.request.url == base or route.request.url.startswith(base + "/"):
                    await route.continue_()
                else:
                    blocked.append(route.request.url)
                    await route.abort()

            await context.route("**/*", local_only)
            await context.add_init_script(HISTORY_PROBE)
            page = await context.new_page()
            page.on("pageerror", lambda error: page_errors.append(str(error)))
            page.on("requestfinished", lambda request: finished.append(request.url))

            # Direct story entries keep one same-URL history entry and correct SEO signals.
            for story_id, path in [(TAX_ID, TAX), (PUDDERY_ID, PUDDERY)]:
                await page.goto(base + path, wait_until="load")
                await page.wait_for_selector("#reader.on")
                state = await snapshot(page)
                ok(f"direct {story_id} keeps its URL without a synthetic home entry",
                   state["url"] == path and state["state"] == {"reader": True, "id": story_id, "direct": True}
                   and no_manufactured_home(state["log"])
                   and not any(entry.get("op") == "pushState" for entry in state["log"]), str(state["log"]))
                ok(f"direct {story_id} has story canonical and index robots",
                   state["canonical"] == SITE_URL + path and state["robots"] == INDEX and not state["overflow"],
                   f"{state['canonical']} {state['robots']}")

            # Escape and the app Back button close direct landings to the front page.
            await page.keyboard.press("Escape")
            await page.wait_for_function("location.pathname === '/' && !document.querySelector('#reader').classList.contains('on')")
            state = await snapshot(page)
            ok("Escape from a direct story closes to an indexable front page",
               state["canonical"] == SITE_URL + "/" and state["robots"] == INDEX)

            await page.goto(base + TAX, wait_until="load")
            await page.wait_for_selector("#reader.on")
            await page.locator("#rBack").click()
            await page.wait_for_function("location.pathname === '/' && !document.querySelector('#reader').classList.contains('on')")
            state = await snapshot(page)
            ok("app Back from a direct story closes to the front page",
               state["canonical"] == SITE_URL + "/" and state["robots"] == INDEX)

            # Browser Back retains the actual preceding browser entry.
            await page.goto(base + "/markets/", wait_until="load")
            await page.goto(base + TAX, wait_until="load")
            await page.wait_for_selector("#reader.on")
            await page.go_back()
            await page.wait_for_function("location.pathname === '/markets/'")
            state = await snapshot(page)
            ok("browser Back from a direct story returns to the real prior route",
               state["url"] == "/markets/" and not state["reader"]
               and state["canonical"] == SITE_URL + "/markets/" and state["robots"] == INDEX)
            await page.go_forward()
            await page.wait_for_selector("#reader.on")
            state = await snapshot(page)
            ok("browser Forward restores the direct story",
               state["url"] == TAX and state["canonical"] == SITE_URL + TAX and state["robots"] == INDEX)

            # Home -> story -> back/forward carries the story and listing signals.
            await page.goto(base + "/", wait_until="load")
            await page.wait_for_selector(f'a[href="{TAX}"]')
            await page.locator(f'a[href="{TAX}"]').first.click()
            await page.wait_for_selector("#reader.on")
            state = await snapshot(page)
            ok("home to story replaces the home canonical with the story canonical",
               state["canonical"] == SITE_URL + TAX and state["robots"] == INDEX
               and any(entry.get("op") == "pushState" and entry.get("url") == TAX for entry in state["log"]),
               f"{state['canonical']} {state['log']}")

            # Reading and sharing still use the story reached inside the app.
            await page.evaluate("Object.defineProperty(navigator, 'share', {configurable:true, value:d => {window.__shared=d; return Promise.resolve();}})")
            await page.locator("#rShare").click()
            shared = await page.evaluate("window.__shared")
            read = await page.evaluate("id => JSON.parse(localStorage.getItem('ledger.read') || '{}')[id]", TAX_ID)
            ok("internal story keeps share and read state", shared and shared["url"] == base + TAX and read == 1,
               str(shared))

            await page.locator("#rBack").click()
            await page.wait_for_function("location.pathname === '/' && !document.querySelector('#reader').classList.contains('on')")
            state = await snapshot(page)
            ok("closing an internal story restores the home canonical and robots",
               state["canonical"] == SITE_URL + "/" and state["robots"] == INDEX)
            await page.go_forward()
            await page.wait_for_selector("#reader.on")
            state = await snapshot(page)
            ok("forward to an internal story restores its canonical and robots",
               state["canonical"] == SITE_URL + TAX and state["robots"] == INDEX)
            await page.keyboard.press("Escape")
            await page.wait_for_function("location.pathname === '/' && !document.querySelector('#reader').classList.contains('on')")

            # An empty editorial section stays noindex, but a story opened over it does not.
            await page.goto(base + "/opinion/", wait_until="load")
            state = await snapshot(page)
            ok("empty Opinion remains noindex with its own canonical",
               state["canonical"] == SITE_URL + "/opinion/" and state["robots"] == NOINDEX)
            await page.evaluate("id => openReader(EDITORIAL.find(item => item.id === id))", TAX_ID)
            await page.wait_for_selector("#reader.on")
            state = await snapshot(page)
            ok("a story opened from empty Opinion gets story signals",
               state["canonical"] == SITE_URL + TAX and state["robots"] == INDEX)
            await page.locator("#rBack").click()
            await page.wait_for_function("location.pathname === '/opinion/' && !document.querySelector('#reader').classList.contains('on')")
            state = await snapshot(page)
            ok("closing the Opinion story restores Opinion noindex",
               state["canonical"] == SITE_URL + "/opinion/" and state["robots"] == NOINDEX)

            # Saved and search are noindex listings; their own stories are indexable.
            await page.goto(base + "/", wait_until="load")
            await page.evaluate("id => toggleSave(id, EDITORIAL.find(item => item.id === id))", TAX_ID)
            await page.goto(base + "/?view=saved", wait_until="load")
            await page.wait_for_selector(f'a[href="{TAX}"]')
            state = await snapshot(page)
            ok("Saved remains noindex with its own canonical",
               state["canonical"] == base + "/?view=saved" and state["robots"] == NOINDEX)
            await page.locator(f'a[href="{TAX}"]').first.click()
            await page.wait_for_selector("#reader.on")
            state = await snapshot(page)
            ok("a Saved story gets story canonical and index robots",
               state["canonical"] == SITE_URL + TAX and state["robots"] == INDEX)
            await page.keyboard.press("Escape")
            await page.wait_for_function("location.search === '?view=saved' && !document.querySelector('#reader').classList.contains('on')")
            state = await snapshot(page)
            ok("closing the Saved story restores Saved noindex",
               state["canonical"] == base + "/?view=saved" and state["robots"] == NOINDEX)

            await page.goto(base + "/?q=paycheque", wait_until="load")
            # The focused test blocks feed fallbacks; seed the already-built
            # editorial set rather than waiting for those intentionally aborted requests.
            await page.evaluate("() => { S.section = 'Front page'; S.query = 'paycheque'; S.items = EDITORIAL.concat([DEMO]); render(); }")
            await page.wait_for_selector(f'a[href="{TAX}"]')
            state = await snapshot(page)
            ok("Search remains noindex with its own canonical",
               state["canonical"] == base + "/?q=paycheque" and state["robots"] == NOINDEX)
            await page.locator(f'a[href="{TAX}"]').first.click()
            await page.wait_for_selector("#reader.on")
            state = await snapshot(page)
            ok("a search result story gets story canonical and index robots",
               state["canonical"] == SITE_URL + TAX and state["robots"] == INDEX)
            await page.locator("#rBack").click()
            await page.wait_for_function("location.search === '?q=paycheque' && !document.querySelector('#reader').classList.contains('on')")
            state = await snapshot(page)
            ok("closing the search story restores search noindex",
               state["canonical"] == base + "/?q=paycheque" and state["robots"] == NOINDEX)

            # Direct information pages use the same direct-entry contract.
            for path in ["/about/", "/privacy/", "/work-with-us/", "/resources/money-headline-checklist/"]:
                await page.goto(base + path, wait_until="load")
                await page.wait_for_selector("#reader.on")
                state = await snapshot(page)
                ok(f"direct info page {path} keeps its route and canonical",
                   state["url"] == path and state["canonical"] == SITE_URL + path
                   and state["robots"] == INDEX and state["state"].get("direct") is True
                   and no_manufactured_home(state["log"]), str(state["log"]))

            await page.keyboard.press("Escape")
            await page.wait_for_function("location.pathname === '/' && !document.querySelector('#reader').classList.contains('on')")
            await page.locator("#btnMenu").click()
            await page.locator("#menuAbout").click()
            await page.wait_for_selector("#reader.on")
            state = await snapshot(page)
            ok("internal About navigation uses the About canonical",
               state["url"] == "/about/" and state["canonical"] == SITE_URL + "/about/" and state["robots"] == INDEX)
            await page.locator("#rBack").click()
            await page.wait_for_function("location.pathname === '/' && !document.querySelector('#reader').classList.contains('on')")

            ok("focused browser run has no page errors", not page_errors, "; ".join(page_errors))
            ok("every completed request stayed on the exact local test origin",
               all(url == base or url.startswith(base + "/") for url in finished),
               f"{len(finished)} local completed; {len(blocked)} external attempts blocked")
            await context.close()
            await browser.close()
    finally:
        server.shutdown()
        server.server_close()
        safe_remove_test_dir(work)


asyncio.run(main())
failures = [result for result in RESULTS if result[0] == "FAIL"]
print(f"\n{len(RESULTS) - len(failures)}/{len(RESULTS)} passed")
if failures:
    raise SystemExit(1)
