"""Observable worker/cache waits for browser QA; no product instrumentation."""


async def wait_for_active_controller(page, timeout=25000):
    return await page.evaluate("""timeout => new Promise((resolve, reject) => {
      const watched = new Set();
      const timer = setTimeout(() => finish(new Error('No activated controller within '+timeout+'ms')), timeout);
      function finish(error) {
        clearTimeout(timer);
        navigator.serviceWorker.removeEventListener('controllerchange', observe);
        for (const worker of watched) worker.removeEventListener('statechange', observe);
        error ? reject(error) : resolve(true);
      }
      function observe() {
        const worker = navigator.serviceWorker.controller;
        if (!worker) return;
        if (worker.state === 'activated') return finish();
        if (!watched.has(worker)) { watched.add(worker); worker.addEventListener('statechange', observe); }
      }
      navigator.serviceWorker.addEventListener('controllerchange', observe);
      observe();
    })""", timeout)


async def update_and_wait_for_controller(page, timeout=25000):
    """Resolve only for a different, activated worker that controls this page.
    update() completion and a non-null controller do not establish this state.
    The timer is a failure bound, never a pause before assuming success.
    """
    return await page.evaluate("""async timeout => {
      const registration = await navigator.serviceWorker.getRegistration();
      if (!registration) throw new Error('No worker registration');
      const previous = navigator.serviceWorker.controller;
      return new Promise((resolve, reject) => {
        const watched = new Set(), events = [];
        let finished = false;
        const timer = setTimeout(() => finish(new Error('Update did not activate and control this page within '+timeout+'ms')), timeout);
        function finish(error) {
          if (finished) return;
          finished = true;
          clearTimeout(timer);
          registration.removeEventListener('updatefound', observe);
          navigator.serviceWorker.removeEventListener('controllerchange', observe);
          for (const worker of watched) worker.removeEventListener('statechange', observe);
          error ? reject(error) : resolve({events, state:navigator.serviceWorker.controller.state, changed:true});
        }
        function observe(event) {
          if (finished) return;
          const worker = registration.installing || registration.waiting || registration.active;
          if (worker && worker !== previous && !watched.has(worker)) {
            watched.add(worker); worker.addEventListener('statechange', observe);
          }
          events.push({event:event?.type || 'inspect', state:worker?.state || null,
                       controllerState:navigator.serviceWorker.controller?.state || null});
          const active = registration.active;
          if (active && active !== previous && active.state === 'activated' &&
              navigator.serviceWorker.controller === active) finish();
          else if (worker && worker !== previous && worker.state === 'redundant') finish(new Error('Update became redundant'));
        }
        registration.addEventListener('updatefound', observe);
        navigator.serviceWorker.addEventListener('controllerchange', observe);
        observe();
        registration.update().then(() => observe()).catch(finish);
      });
    }""", timeout)


async def wait_for_cached_response(page, cache_name, url, timeout=15000):
    """Await the actual Cache API result. Poll only until the response is stored.
    A Promise-returning wait_for_function predicate is not an async poll.
    """
    return await page.evaluate("""async ({name, url, timeout}) => {
      const deadline = performance.now() + timeout;
      while (performance.now() < deadline) {
        if (await caches.has(name)) {
          const cache = await caches.open(name);
          if (await cache.match(url)) return true;
        }
        await new Promise(requestAnimationFrame);
      }
      throw new Error('Response was not cached within '+timeout+'ms: '+url);
    }""", {"name": cache_name, "url": url, "timeout": timeout})
