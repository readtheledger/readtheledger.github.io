"""Actual provider tests. Every browser request is locally fulfilled or aborted.
Supply a reviewed public script via --beacon; the suite never sends live events.
"""
import argparse, asyncio, hashlib, json, mimetypes, pathlib, subprocess, urllib.parse
from playwright.async_api import async_playwright
ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/'.qa'/'analytics-site'
PUBLIC='https://readtheledger.github.io'
SCRIPT='https://static.cloudflareinsights.com/beacon.min.js'
COLLECTOR='https://cloudflareinsights.com/cdn-cgi/rum'
SPEECH_PROBE='https://api.openai.com/v1/audio/speech'
FEED_PROBE='https://api.allorigins.win/raw?url=https%3A%2F%2Fexample.org%2Ffixture.xml'
TOKEN='e1563ba6decb4bfcae56ce3d7c2d3366'
KEY='ledger.analytics.exclude'
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130.0.0.0 Safari/537.36'
checks=[]
def ok(name, condition, detail=None):
    checks.append(dict(name=name,passed=bool(condition),detail=detail))
    print(('PASS ' if condition else 'FAIL ')+name,flush=True)

async def main(beacon):
    source=beacon.read_bytes()
    subprocess.run(['node','build.mjs',str(OUT)],cwd=ROOT,check=True)
    content=json.loads(subprocess.check_output(['node','-e','global.window={};require("./content.js");console.log(JSON.stringify(window.LEDGER_CONTENT));'],cwd=ROOT))
    a,b=[x['id'] for x in content['articles'][:2]]
    ap,bp=f'/story/{a}/',f'/story/{b}/'
    async with async_playwright() as pw:
        browser=await pw.chromium.launch()
        async def fixture(origin=PUBLIC,init='',human=True,js=True,beacon_mode='real',noindex=False):
            ctx=await browser.new_context(user_agent=UA,service_workers='block',java_script_enabled=js,viewport=dict(width=390,height=844))
            if human: await ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>false});")
            if init: await ctx.add_init_script(init)
            events=[];scripts=[];errors=[];other=[]
            async def handle(route):
                request=route.request;url=urllib.parse.urlsplit(request.url)
                if request.url in [SPEECH_PROBE,FEED_PROBE]:
                    other.append(dict(url=request.url,method=request.method,body=request.post_data,headers=await request.all_headers()))
                    await route.fulfill(body='native transport works',headers={'Access-Control-Allow-Origin':'*'});return
                if request.url==SCRIPT:
                    scripts.append(request.url)
                    if beacon_mode=='fail': await route.abort()
                    else: await route.fulfill(body=source if beacon_mode=='real' else b'/* transport fixture */',content_type='text/javascript',headers={'Access-Control-Allow-Origin':'*'})
                    return
                if f'{url.scheme}://{url.netloc}'=='https://cloudflareinsights.com':
                    try: data=json.loads(request.post_data or '')
                    except ValueError: data={'raw':request.post_data}
                    events.append(dict(url=request.url,data=data,headers=await request.all_headers()))
                    await route.fulfill(status=204,headers={'Access-Control-Allow-Origin':'*'});return
                if f'{url.scheme}://{url.netloc}'!=origin:
                    other.append(request.url);await route.abort();return
                if url.path=='/guard-probe': await route.fulfill(body='native transport works');return
                if url.path=='/data/feed.json':
                    await route.fulfill(json=dict(schema=1,fetched='2026-09-12T12:00:00Z',sources=[],items=[]));return
                path=(OUT/urllib.parse.unquote(url.path).lstrip('/')).resolve()
                if path.is_dir(): path=path/'index.html'
                if not path.is_relative_to(OUT.resolve()) or not path.is_file(): await route.fulfill(status=404,body='Not found');return
                body=path.read_bytes()
                if noindex and path.suffix=='.html': body=body.replace(b'<head>',b'<head><meta name="robots" content="noindex,nofollow">')
                await route.fulfill(body=body,content_type='text/javascript' if path.suffix=='.js' else mimetypes.guess_type(str(path))[0] or 'application/octet-stream')
            await ctx.route('**/*',handle)
            page=await ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
            return ctx,page,events,scripts,errors,other
        async def settle(page): await page.wait_for_timeout(180)
        async def nav(page,path='/'):
            await page.goto(path if path.startswith('http') else PUBLIC+path);await settle(page)
        def views(events): return [e['data'].get('location') for e in events if e['data'].get('eventType')==1]
        async def story(page,id):
            await page.evaluate('(id)=>openReader(EDITORIAL.find(a=>a.id===id))',id);await settle(page)
        for fallback in [False,True]:
            ctx,page,events,scripts,errors,other=await fixture(init="delete window.navigation;" if fallback else '')
            await nav(page,ap+'?q=private-query#private-fragment')
            ok(f'direct story has one load (fallback={fallback})',views(events)==[PUBLIC+ap],views(events))
            await story(page,b)
            ok(f'story navigation has one new load (fallback={fallback})',views(events)==[PUBLIC+ap,PUBLIC+bp],views(events))
            await page.go_back();await settle(page)
            ok(f'Back has one restored load (fallback={fallback})',views(events)==[PUBLIC+ap,PUBLIC+bp,PUBLIC+ap],views(events))
            await page.go_forward();await settle(page)
            ok(f'Forward has one restored load (fallback={fallback})',views(events)==[PUBLIC+ap,PUBLIC+bp,PUBLIC+ap,PUBLIC+bp],views(events))
            n=len(views(events));await page.reload();await settle(page)
            ok(f'reload has one new load (fallback={fallback})',len(views(events))==n+1)
            ok(f'one provider load per document (fallback={fallback})',len(scripts)==2)
            ok(f'expected public token (fallback={fallback})',all(e['data'].get('siteToken')==TOKEN for e in events))
            ok(f'no private query or fragment in payload (fallback={fallback})',all('private-query' not in json.dumps(e['data']) and 'private-fragment' not in json.dumps(e['data']) for e in events))
            ok(f'no GoatCounter or ads (fallback={fallback})',not any('goatcounter' in x or 'doubleclick' in x for x in other))
            ok(f'no runtime errors (fallback={fallback})',not errors,errors)
            await ctx.close()
        ctx,page,events,scripts,errors,other=await fixture()
        await nav(page,'/about/');ok('direct About has one load',views(events)==[PUBLIC+'/about/'],views(events))
        n=len(events);await page.locator('#rwrap [data-analytics-exclude]').check();await settle(page)
        await story(page,a);await page.reload();await settle(page)
        ok('opt-out blocks unload and later navigation/reload',len(events)==n,(n,len(events)))
        ok('saved opt-out prevents provider reload',len(scripts)==1 and await page.evaluate('ANALYTICS.excluded()'))
        await nav(page,'/about/');await page.locator('#rwrap [data-analytics-exclude]').uncheck();await settle(page)
        ok('re-enable alone does not start collection',len(events)==n and len(scripts)==1)
        await story(page,b)
        ok('re-enable starts next navigation once',len(views(events))==2 and views(events)[-1]==PUBLIC+bp,views(events))
        second=await ctx.new_page();await second.goto(PUBLIC+'/about/');await settle(second)
        n=len(events);await second.locator('#rwrap [data-analytics-exclude]').check();await settle(page)
        await story(page,a);await page.reload();await settle(page)
        ok('second-tab opt-out blocks both documents',len(events)==n,(n,len(events)))
        ok('first tab reads second-tab exclusion',await page.evaluate('ANALYTICS.excluded()'))
        await ctx.close()
        excluded=[
            ('local host','http://127.0.0.1:8765','',True,True,False),
            ('preview host','https://preview.example','',True,True,False),
            ('other HTTPS host','https://example.org','',True,True,False),
            ('owner exclusion',PUBLIC,f"localStorage.setItem('{KEY}','1');",True,True,False),
            ('legacy exclusion',PUBLIC,"localStorage.setItem('skipgc','t');",True,True,False),
            ('storage read failure',PUBLIC,"Storage.prototype.getItem=function(){throw Error('denied')};",True,True,False),
            ('WebDriver',PUBLIC,'',False,True,False),
            ('no JavaScript',PUBLIC,'',True,False,False),
            ('noindex canonical fixture',PUBLIC,'',True,True,True),
            ('guard installation failure',PUBLIC,"Object.defineProperty(navigator,'sendBeacon',{value:navigator.sendBeacon,writable:false});",True,True,False)]
        for label,origin,init,human,js,noindex in excluded:
            ctx,page,events,scripts,errors,other=await fixture(origin,init,human,js,noindex=noindex)
            await nav(page,origin+ap)
            ok(label+' makes no provider/script request',not events and not scripts);await ctx.close()
        ctx,page,events,scripts,errors,other=await fixture(init="Object.defineProperty(document,'prerendering',{configurable:true,get:()=>true});")
        await nav(page,ap);ok('prerender delays beacon',not events and not scripts)
        await page.evaluate("Object.defineProperty(document,'prerendering',{get:()=>false});document.dispatchEvent(new Event('prerenderingchange'))")
        await settle(page);ok('prerender activation starts one beacon',views(events)==[PUBLIC+ap] and len(scripts)==1);await ctx.close()
        ctx,page,events,scripts,errors,other=await fixture()
        await nav(page,'/about/');await page.evaluate("()=>{const set=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(k==='ledger.analytics.exclude')throw Error('full');return set.call(this,k,v)};}")
        n=len(events);await page.locator('#rwrap [data-analytics-exclude]').check();await story(page,a)
        ok('write failure blocks already-loaded provider',len(events)==n and await page.evaluate('ANALYTICS.storageFailed()'))
        await page.evaluate('openReader(DEMO)');await settle(page)
        ok('failure disclosure explains reload limitation','may not survive a reload' in await page.locator('#rwrap [data-analytics-status]').inner_text());await ctx.close()
        ctx,page,events,scripts,errors,other=await fixture(beacon_mode='fail')
        await nav(page,ap);await story(page,b)
        ok('beacon failure leaves reader usable with no retries',len(scripts)==1 and not events and await page.locator('#reader').evaluate('(el)=>el.classList.contains("on")'));await ctx.close()
        # Challenge each transport between storage mutation and event/reload.
        ctx,page,events,scripts,errors,other=await fixture(beacon_mode='empty');await nav(page)
        result=await page.evaluate("""async ({key,url})=>{
          const original=await fetch('/guard-probe').then(r=>r.text());
          localStorage.setItem(key,'1');
          const beacon=navigator.sendBeacon(url,'{}');
          const xhr=new XMLHttpRequest();xhr.open('POST',url);xhr.send('{}');
          const rejected=await fetch(url,{method:'POST',body:'{}'}).then(()=>false,()=>true);
          const after=await fetch('/guard-probe').then(r=>r.text());
          return {beacon,rejected,original,after};
        }""",dict(key=KEY,url=COLLECTOR))
        await settle(page)
        ok('sendBeacon/XHR/fetch recheck exclusion synchronously',not events and result['beacon'] is False and result['rejected'])
        ok('non-analytics fetch keeps working',result['original']==result['after']=='native transport works');await ctx.close()
        ctx,page,events,scripts,errors,other=await fixture(beacon_mode='empty');await nav(page)
        result=await page.evaluate("""async ({key,speech,feed})=>{
          localStorage.setItem(key,'1');
          const fetched=await fetch(speech,{method:'POST',headers:{'Content-Type':'text/plain'},body:'public offline fixture',credentials:'omit'}).then(r=>r.text());
          const xhr=await new Promise((resolve,reject)=>{
            const request=new XMLHttpRequest();request.open('GET',feed);
            request.onload=()=>resolve(request.responseText);request.onerror=reject;request.send();
          });
          const beacon=navigator.sendBeacon(feed,'offline beacon fixture');
          return {fetched,xhr,beacon};
        }""",dict(key=KEY,speech=SPEECH_PROBE,feed=FEED_PROBE))
        await settle(page)
        probes=[x for x in other if isinstance(x,dict)]
        ok('opt-out preserves unrelated speech fetch and feed XHR/sendBeacon',not events and
           result==dict(fetched='native transport works',xhr='native transport works',beacon=True) and
           [(x['url'],x['method'],x['body']) for x in probes]==[
               (SPEECH_PROBE,'POST','public offline fixture'),(FEED_PROBE,'GET',None),(FEED_PROBE,'POST','offline beacon fixture')],probes)
        ok('speech request keeps its supplied Content-Type',probes[0]['headers'].get('content-type')=='text/plain')
        await ctx.close()
        ctx,page,events,scripts,errors,other=await fixture(init=f"localStorage.setItem('{KEY}','1');")
        await nav(page,'/about/');control=page.locator('#rwrap .analytics-choice');await control.scroll_into_view_if_needed()
        box=await control.bounding_box();ok('mobile exclusion control at least 44px tall',box['height']>=44)
        text=await page.locator('#rwrap').inner_text()
        ok('About names Cloudflare and keeps ads off','Cloudflare Web Analytics' in text and 'There is no advertising.' in text)
        await page.screenshot(path=str(ROOT/'.qa'/'analytics-cloudflare-about-390.png'))
        await ctx.close();await browser.close()
    report=dict(beacon_sha256=hashlib.sha256(source).hexdigest(),live_requests=0,checks=checks,
                limitations=['Headless Chromium; prerender simulated','Collection locally fulfilled; dashboard receipt pending','eventType=1 is page load; eventType=3 is performance, not another pageview'])
    (ROOT/'.qa'/'analytics-results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    if not all(x['passed'] for x in checks): raise SystemExit(1)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--beacon',type=pathlib.Path,required=True)
    asyncio.run(main(parser.parse_args().beacon))
