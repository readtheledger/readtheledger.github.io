"""Focused privacy route, offline and Google API-entry checks.
Only a loopback server is reachable; all external browser requests are aborted.
CMP readiness is simulated, not a claim about a published Google message.
"""
import asyncio,functools,http.server,json,pathlib,re,subprocess,threading,urllib.parse,xml.etree.ElementTree as ET
from playwright.async_api import async_playwright
from qa_worker_helpers import wait_for_active_controller
ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/'.qa'/'privacy-site'
R=[]
def ok(name,condition,detail=None):
    R.append(dict(name=name,passed=bool(condition),detail=detail))
    print(('PASS ' if condition else 'FAIL ')+name,flush=True)
class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args): pass

async def main():
    subprocess.run(['node','build.mjs',str(OUT)],cwd=ROOT,check=True)
    (OUT/'data').mkdir(exist_ok=True)
    (OUT/'data/feed.json').write_text(json.dumps(dict(schema=1,fetched='2026-09-12T12:00:00Z',sources=[],items=[])),encoding='utf-8')
    html=(OUT/'privacy/index.html').read_text(encoding='utf-8')
    sw=(OUT/'sw.js').read_text(encoding='utf-8')
    ld=[json.loads(v) for v in re.findall(r'<script type="application/ld\+json">(.*?)</script>',html,re.S)]
    ok('privacy has WebPage schema and no article/publication date',any(x.get('@type')=='WebPage' for x in ld) and 'NewsArticle' not in json.dumps(ld) and 'datePublished' not in json.dumps(ld))
    ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
    entries=ET.fromstring((OUT/'sitemap.xml').read_text(encoding='utf-8')).findall('s:url',ns)
    entry=next(x for x in entries if x.find('s:loc',ns).text.endswith('/privacy/'))
    ok('privacy sitemap entry has no invented lastmod',entry.find('s:lastmod',ns) is None)
    ok('privacy excluded from news sitemap and Atom articles','/privacy/' not in (OUT/'sitemap-news.xml').read_text() and '/privacy/' not in (OUT/'feed.xml').read_text(encoding='utf-8'))
    ok('worker precaches privacy/consent modules and knows privacy route','"/privacy.js"' in sw and '"/consent.js"' in sw and '"/privacy/"' in re.search(r'^const ROUTES = (.*);',sw,re.M).group(1))
    original=subprocess.check_output(['git','show','HEAD:index.html'],cwd=ROOT).decode('utf-8')
    csp=lambda s: re.search(r'<meta http-equiv="Content-Security-Policy" content="(.*?)">',s,re.S).group(1)
    ok('CSP unchanged; no ad/CMP allowance added',csp(original)==csp(html))
    bodies=[p.read_text(encoding='utf-8') for p in OUT.rglob('*.html')]
    ok('all generated pages have a normal privacy link',all('href="/privacy/"' in body for body in bodies))
    ok('no remote advertising/consent script tag added',not any(re.search(r'<script[^>]+src=["\'][^"\']*(?:googlesyndication|fundingchoices|doubleclick)',body) for body in bodies))
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(OUT)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    base=f'http://127.0.0.1:{server.server_port}'
    try:
        async with async_playwright() as pw:
            browser=await pw.chromium.launch()
            async def context(js=True,init='',worker=False,width=390):
                ctx=await browser.new_context(java_script_enabled=js,service_workers='allow' if worker else 'block',viewport=dict(width=width,height=844))
                if init: await ctx.add_init_script(init)
                external=[]
                async def handle(route):
                    if route.request.url.startswith(base+'/'): await route.continue_()
                    else: external.append(route.request.url);await route.abort()
                await ctx.route('**/*',handle)
                page=await ctx.new_page();errors=[]
                page.on('pageerror',lambda e:errors.append(str(e)))
                return ctx,page,errors,external
            ctx,page,errors,external=await context(js=False)
            response=await page.goto(base+'/privacy/')
            ok('privacy readable without JavaScript or advertising consent',response.status==200 and await page.locator('#static h1').inner_text()=='Privacy at The Ledger')
            ok('privacy canonical and title are correct',await page.title()=='Privacy — The Ledger' and await page.locator('link[rel=canonical]').get_attribute('href')=='https://readtheledger.github.io/privacy/')
            static_text=await page.locator('#static').inner_text()
            ok('static privacy retains actual analytics/speech/conditional-ad disclosures',all(t in static_text for t in ['OpenAI','Cloudflare Web Analytics','Advertising is currently disabled','under review','Posts there are public']))
            ok('no-JS advertising control is hidden',not await page.locator('#siteFooter [data-ad-settings]').is_visible())
            await page.goto(base+'/');await page.locator('#siteFooter a[href="/privacy/"]').click()
            ok('footer privacy link works without JavaScript',urllib.parse.urlsplit(page.url).path=='/privacy/' and await page.locator('#static h1').is_visible())
            await ctx.close()
            ctx,page,errors,external=await context()
            await page.goto(base+'/privacy/');await page.wait_for_selector('#reader.on')
            ok('privacy deep link restores reader, title and address',await page.locator('#rwrap h1').inner_text()=='Privacy at The Ledger' and urllib.parse.urlsplit(page.url).path=='/privacy/' and await page.title()=='Privacy — The Ledger')
            ok('privacy reader has no publication/byline invention','no publication date' in await page.locator('#rwrap').inner_text() and await page.locator('#rwrap .byline').count()==0)
            ok('absent CMP stays hidden and disabled',await page.locator('[data-ad-settings]:not([hidden])').count()==0 and await page.locator('[data-ad-settings]:not([disabled])').count()==0)
            ok('Cloudflare exclusion remains separate',await page.locator('#rwrap [data-analytics-exclude]').count()==1)
            await page.go_back();await page.wait_for_selector('#reader:not(.on)',state='attached')
            await page.locator('#btnMenu').click();await page.locator('#menu a[data-open-privacy]').click()
            ok('menu privacy entry opens the dedicated reader',await page.locator('#rwrap h1').inner_text()=='Privacy at The Ledger' and urllib.parse.urlsplit(page.url).path=='/privacy/')
            await page.goto(base+'/story/led-20260817-record/');await page.wait_for_selector('#reader.on')
            await page.locator('#rwrap a[data-open-privacy]').click();await page.go_back()
            ok('article footer privacy navigation preserves Back to article',urllib.parse.urlsplit(page.url).path=='/story/led-20260817-record/' and await page.locator('#rwrap h1').inner_text()!='Privacy at The Ledger')
            await page.goto(base+'/privacy/');await page.wait_for_selector('#reader.on')
            control=page.locator('#rwrap [data-analytics-exclude]');await control.check()
            ok('privacy checkbox saves existing analytics exclusion',await page.evaluate("localStorage.getItem('ledger.analytics.exclude')")=='1')
            await page.reload();await page.wait_for_selector('#reader.on')
            ok('privacy checkbox restores saved exclusion',await page.locator('#rwrap [data-analytics-exclude]').is_checked())
            await page.goto(base+'/about/');await page.wait_for_selector('#reader.on')
            ok('About still opens normally and shares exclusion',await page.title()=='About — The Ledger' and await page.locator('#rwrap [data-analytics-exclude]').is_checked())
            ok('route and control checks have no runtime errors',not errors,errors)
            await ctx.close()
            mock="""window.cmpCalls=0;window.googlefc={callbackQueue:[],showRevocationMessage(){window.cmpCalls++;if(window.failCMP)throw Error('fixture failure')}};"""
            ctx,page,errors,external=await context(init=mock)
            await page.goto(base+'/privacy/');await page.wait_for_selector('#reader.on')
            ok('method presence alone does not reveal CMP control',await page.locator('[data-ad-settings]:not([hidden])').count()==0)
            await page.evaluate("""()=>{
              const queued=googlefc.callbackQueue;
              googlefc.callbackQueue={push(value){value.CONSENT_API_READY();return 1}};
              queued.forEach(value=>value.CONSENT_API_READY());
            }""")
            control=page.locator('#rwrap [data-ad-settings]')
            ok('readiness plus callable API reveals advertising control',await control.is_visible() and await control.is_enabled())
            await control.scroll_into_view_if_needed();box=await control.bounding_box()
            ok('advertising control has a 44px touch target',box['height']>=44)
            await control.focus();await page.keyboard.press('Enter')
            ok('keyboard entry calls documented revocation API exactly once',await page.evaluate('window.cmpCalls')==1)
            ok('successful request does not claim a consent change','does not confirm a changed choice' in await page.locator('#rwrap [data-consent-status]').inner_text())
            await page.evaluate('()=>{window.failCMP=true;}');await control.click()
            ok('throwing API hides control and reports failure',not await control.is_visible() and 'No change was confirmed' in await page.locator('#rwrap [data-consent-status]').inner_text())
            ok('failure status receives accessible focus',await page.locator('#rwrap [data-consent-status]').evaluate('(el)=>el===document.activeElement'))
            ok('CMP failure does not block privacy content',await page.locator('#rwrap h1').inner_text()=='Privacy at The Ledger' and not errors,errors)
            await ctx.close()
            ctx,page,errors,external=await context(init="window.googlefc={callbackQueue:{push(){throw Error('unavailable')}}};")
            await page.goto(base+'/privacy/');await page.wait_for_selector('#reader.on')
            ok('unavailable callback queue leaves page usable and controls hidden',not errors and await page.locator('[data-ad-settings]:not([hidden])').count()==0)
            await ctx.close()
            for width in [360,1440]:
                ctx,page,errors,external=await context(width=width)
                await page.goto(base+'/privacy/');await page.wait_for_selector('#reader.on')
                await page.locator('#rwrap footer').scroll_into_view_if_needed()
                ok(f'privacy reader fits width {width}',await page.locator('#reader').evaluate('(el)=>el.scrollWidth<=el.clientWidth'))
                await page.screenshot(path=str(ROOT/'.qa'/f'privacy-{width}.png'))
                await ctx.close()
            # Real service worker, cached privacy page and unvisited-route fallback.
            ctx,page,errors,external=await context(worker=True)
            await page.goto(base+'/');await wait_for_active_controller(page)
            cached=await page.evaluate("""async()=>{
              const names=await caches.keys();const name=names.find(k=>k.startsWith('ledger-shell-'));
              const cache=await caches.open(name);
              return {privacy:!!await cache.match('/privacy.js'),consent:!!await cache.match('/consent.js')};
            }""")
            ok('real worker caches privacy and consent modules',cached==dict(privacy=True,consent=True))
            await ctx.set_offline(True)
            await page.goto(base+'/privacy/');await page.wait_for_selector('#reader.on')
            ok('unvisited privacy route opens offline through app shell',await page.locator('#rwrap h1').inner_text()=='Privacy at The Ledger')
            ok('offline privacy has no available CMP',await page.locator('[data-ad-settings]:not([hidden])').count()==0)
            await ctx.close();await browser.close()
    finally: server.shutdown();server.server_close()
    (ROOT/'.qa'/'privacy-results.json').write_text(json.dumps(dict(checks=R,external_requests_sent=0,cmp='mocked readiness only; no real message configured'),indent=2),encoding='utf-8')
    if not all(x['passed'] for x in R): raise SystemExit(1)
if __name__=='__main__': asyncio.run(main())
