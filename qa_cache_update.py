"""Gated, real-worker update regression: local server and disposable browser only.
Exercise slow installation, an old client's in-flight response, repeated updates,
fresh image bytes, stale-cache cleanup, unrelated caches, saved state and offline reading.
"""
import asyncio, hashlib, http.server, json, mimetypes, pathlib, re, shutil, subprocess, tempfile, threading, urllib.parse
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from qa_worker_helpers import update_and_wait_for_controller, wait_for_active_controller, wait_for_cached_response

ROOT=pathlib.Path(__file__).resolve().parent
HERO='/assets/editorial/led-20260817-savers/hero-1200.webp'
STORY='/story/led-20260817-savers/'
NOTICE='A factual review record is not available for this article.'
R=[]


def ok(name, condition, detail=None):
    R.append({'name':name,'pass':bool(condition),'detail':detail})
    print(('PASS ' if condition else 'FAIL ')+name+((' '+str(detail)) if not condition else ''),flush=True)


async def main():
    with tempfile.TemporaryDirectory(prefix='ledger-cache-update-') as tmp:
        work=pathlib.Path(tmp); site_a=work/'a'; site_b=work/'b'
        subprocess.run(['node',str(ROOT/'build.mjs'),str(site_a)],check=True)
        alt=work/'assets'; shutil.copytree(ROOT/'assets/editorial',alt)
        for name in ['hero-1200.webp','hero-768.webp','hero-480.webp','hero-1200.jpg']:
            shutil.copyfile(alt/'led-20260817-weekly'/name,alt/'led-20260817-savers'/name)
        subprocess.run(['node',str(ROOT/'build.mjs'),str(site_b),'--assets',str(alt)],check=True)
        for site in [site_a,site_b]:
            (site/'data').mkdir(exist_ok=True)
            (site/'data/feed.json').write_text(json.dumps({'schema':1,'fetched':'2026-09-12T12:00:00Z','sources':[],'items':[]}),encoding='utf-8')
        stamp=lambda site:re.search(r'const BUILD = "([a-f0-9]{8})"',(site/'sw.js').read_text(encoding='utf-8')).group(1)
        a,b=stamp(site_a),stamp(site_b)
        hashes=[hashlib.sha256((site/HERO.lstrip('/')).read_bytes()).hexdigest() for site in [site_a,site_b]]
        ok('two real artifacts have distinct worker stamps and image bytes',a!=b and hashes[0]!=hashes[1])
        state={'root':site_a,'gate':False,'offline':False}
        install_started=threading.Event(); install_release=threading.Event()
        held_started=threading.Event(); held_release=threading.Event()

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self,*args): pass
            def do_GET(self):
                path=urllib.parse.urlsplit(self.path).path
                if state['offline']:
                    self.close_connection=True; return
                if path=='/data/held.json':
                    held_started.set()
                    if not held_release.wait(20): self.send_error(504);return
                    data=b'{"old_client_response":"completed"}'; mime='application/json'
                else:
                    root=state['root']
                    if state['gate'] and path=='/context.js':
                        install_started.set()
                        if not install_release.wait(20): self.send_error(504);return
                    fp=(root/path.lstrip('/')).resolve()
                    if fp.is_dir(): fp/='index.html'
                    if not fp.is_relative_to(root.resolve()) or not fp.is_file(): self.send_error(404);return
                    data=fp.read_bytes(); mime='text/javascript' if fp.suffix=='.js' else mimetypes.guess_type(fp)[0] or 'application/octet-stream'
                self.send_response(200);self.send_header('Content-Type',mime)
                self.send_header('Cache-Control','max-age=600' if path.startswith('/assets/') else 'no-store')
                # Applies to pages AND the worker: no external network can escape QA.
                self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; worker-src 'self'")
                self.send_header('Content-Length',str(len(data)));self.end_headers()
                try: self.wfile.write(data)
                except (BrokenPipeError,ConnectionAbortedError,ConnectionResetError): pass

        server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
        server.daemon_threads=True
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        base='http://127.0.0.1:'+str(server.server_port)
        try:
            async with async_playwright() as pw:
                browser=await pw.chromium.launch()
                ctx=await browser.new_context(viewport={'width':390,'height':844})
                page=await ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                await page.goto(base+STORY);await page.locator('#reader.on').wait_for()
                await wait_for_active_controller(page)
                await page.reload();await page.locator('#reader.on').wait_for()
                await page.locator('#rSave').click()
                await page.evaluate("localStorage.setItem('ledger.analytics.exclude','1');localStorage.setItem('cache-qa-preference','keep-me')")
                saved=await page.evaluate("JSON.stringify(S.saved)")
                await page.evaluate("""async () => {
                  for(const name of ['another-app-cache','ledger-notebook-v1','ledger-shell-v4-not-a-build']) {
                    const c=await caches.open(name);await c.put('/__other-app/value',new Response('keep:'+name));
                  }
                  await caches.open('ledger-shell-v3');await caches.open('ledger-runtime-v3');
                }""")
                await page.evaluate('u=>fetch(u).then(r=>r.arrayBuffer())',HERO)
                await wait_for_cached_response(page,'ledger-images-v4-'+a,HERO)
                await page.evaluate("window.heldResponse=fetch('/data/held.json').then(r=>r.json());void 0")
                assert await asyncio.to_thread(held_started.wait,10),'old-client request did not start'
                state.update(root=site_b,gate=True)
                update=asyncio.create_task(update_and_wait_for_controller(page))
                assert await asyncio.to_thread(install_started.wait,10),'new installation did not reach gate'
                stage=await page.evaluate("async()=>{const r=await navigator.serviceWorker.getRegistration();return {installing:r.installing?.state,controller:navigator.serviceWorker.controller?.state,keys:await caches.keys()};}")
                ok('gated install retains the old usable controller and caches',stage['installing']=='installing' and stage['controller']=='activated' and 'ledger-shell-v4-'+a in stage['keys'],stage)
                ok('event-based update wait stays pending while installation is blocked',not update.done())
                try:
                    false_handle=await page.wait_for_function("([a,b])=>navigator.serviceWorker.controller && caches.keys().then(ks=>ks.some(k=>k.includes(b))&&!ks.some(k=>k.includes(a)))",arg=[a,b],timeout=1000)
                    old_wait_observation=await false_handle.json_value()
                except PlaywrightTimeoutError:
                    # A future driver may correctly await and re-poll the predicate.
                    old_wait_observation='timed out while installation was gated'
                ok('old async predicate cannot establish successful activation',old_wait_observation is False or isinstance(old_wait_observation,str),old_wait_observation)
                install_release.set()
                # Release the observed old request; no arbitrary delay or assumption of activation.
                held_release.set()
                old_response=await page.evaluate('window.heldResponse')
                event_record=await update
                ok('old in-flight response completes across update',old_response=={'old_client_response':'completed'},old_response)
                ok('new worker reaches activated state and controls the old client',event_record['changed'] and event_record['state']=='activated',event_record)
                keys=await page.evaluate('caches.keys()')
                ok('actual completed activation removes prior Ledger generations',not any(a in k or k in ['ledger-shell-v3','ledger-runtime-v3'] for k in keys),keys)
                async def unrelated_intact():
                    return await page.evaluate("""async()=>{const out={};for(const n of ['another-app-cache','ledger-notebook-v1','ledger-shell-v4-not-a-build']){out[n]=await caches.has(n)?await(await(await caches.open(n)).match('/__other-app/value')).text():null;}return out;}""")
                unrelated=await unrelated_intact()
                ok('unrelated and lookalike caches retain their exact values',all(v=='keep:'+k for k,v in unrelated.items()),unrelated)
                async def image_hash():
                    return await page.evaluate("async u=>{const b=await(await fetch(u)).arrayBuffer();return [...new Uint8Array(await crypto.subtle.digest('SHA-256',b))].map(x=>x.toString(16).padStart(2,'0')).join('');}",HERO)
                ok('old client receives exact replacement image despite HTTP max-age',await image_hash()==hashes[1])
                await wait_for_cached_response(page,'ledger-images-v4-'+b,HERO)
                state['gate']=False
                await page.reload();await page.locator('#reader.on').wait_for()
                ok('reload keeps saved reading and user preferences',await page.evaluate("JSON.stringify(S.saved)")==saved and await page.evaluate("localStorage.getItem('ledger.analytics.exclude')==='1' && localStorage.getItem('cache-qa-preference')==='keep-me'"))
                state['offline']=True
                await page.reload();await page.locator('#reader.on').wait_for()
                ok('updated reader and image work offline',NOTICE in await page.locator('#rwrap .attrline').inner_text() and await image_hash()==hashes[1])
                keys=await page.evaluate('caches.keys()')
                ok('old Ledger caches do not reappear after fetches/reload/offline reading',not any(a in k for k in keys),keys)
                state.update(root=site_a,offline=False)
                rollback=await update_and_wait_for_controller(page)
                ok('a second update/rollback activates and serves its exact image',rollback['state']=='activated' and await image_hash()==hashes[0],rollback)
                keys=await page.evaluate('caches.keys()')
                ok('second update removes only the superseded Ledger generation',not any(b in k for k in keys) and all(v=='keep:'+k for k,v in (await unrelated_intact()).items()),keys)
                ok('user state and attribution remain intact after repeated updates',await page.evaluate("JSON.stringify(S.saved)")==saved and NOTICE in await page.locator('#rwrap .attrline').inner_text() and await page.evaluate("localStorage.getItem('ledger.analytics.exclude')==='1'"))
                ok('update sequence has no uncaught browser errors',not errors,errors)
                await browser.close()
        finally:
            install_release.set();held_release.set();server.shutdown();server.server_close()
    out=ROOT/'.qa/cache-update-results.json';out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({'checks':R,'passed':sum(x['pass'] for x in R),'total':len(R)},indent=2)+'\n',encoding='utf-8')
    print(f"{sum(x['pass'] for x in R)}/{len(R)} checks passed",flush=True)
    if not all(x['pass'] for x in R): raise SystemExit(1)


if __name__=='__main__': asyncio.run(main())
