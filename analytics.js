/* Cloudflare owns page/navigation measurement. This adapter only controls when
   its public beacon may load and send; it never emits manual pageview events. */
(function(){
  "use strict";
  const EXCLUDE_KEY = "ledger.analytics.exclude";
  const CANONICAL_ORIGIN = "https://readtheledger.github.io";
  const BEACON_SRC = "https://static.cloudflareinsights.com/beacon.min.js";
  function create({token, origin}){
    let storageFailed = false, sessionExcluded = false, started = false;
    let stopped = false, guardsReady = false, unavailable = false;
    const pending = new Set();
    function excluded(){
      try{
        const saved = localStorage.getItem(EXCLUDE_KEY) === "1" || localStorage.getItem("skipgc") === "t";
        return sessionExcluded || saved;
      }catch(e){ storageFailed = true; return true; }
    }
    function blocked(){
      if(excluded() || storageFailed || stopped) return true;
      if(origin !== CANONICAL_ORIGIN || location.origin !== CANONICAL_ORIGIN || location.protocol !== "https:") return true;
      if(!/^[a-f0-9]{32}$/.test(token || "")) return true;
      if(window.top !== window.self || document.prerendering || document.visibilityState === "prerender") return true;
      if(document.querySelector('meta[name="robots"][content*="noindex"]')) return true;
      return !!navigator.webdriver || /headless|playwright|selenium|phantomjs|\bbot\b|crawler|spider/i.test(navigator.userAgent || "");
    }
    function collector(url){
      try{
        const target = new URL(url, location.href);
        return target.origin === "https://cloudflareinsights.com" && target.pathname === "/cdn-cgi/rum";
      }
      catch(e){ return false; }
    }
    function installGuards(){
      if(guardsReady) return true;
      // Installed before the provider. Recheck storage at send time, including
      // unload beacons and another tab's change. Other destinations stay native.
      try{
        const destinations = new WeakMap();
        const open = XMLHttpRequest.prototype.open, send = XMLHttpRequest.prototype.send;
        const guardedOpen = function(method, url, ...rest){
          destinations.set(this, collector(url));
          return open.call(this, method, url, ...rest);
        };
        const guardedSend = function(...args){
          if(destinations.get(this)){
            if(blocked()){ this.abort(); return; }
            pending.add(this);
            this.addEventListener("loadend", ()=>pending.delete(this), {once:true});
          }
          return send.apply(this, args);
        };
        XMLHttpRequest.prototype.open = guardedOpen;
        XMLHttpRequest.prototype.send = guardedSend;
        if(XMLHttpRequest.prototype.open !== guardedOpen || XMLHttpRequest.prototype.send !== guardedSend) return false;
        if(typeof navigator.sendBeacon === "function"){
          const sendBeacon = navigator.sendBeacon;
          const guardedBeacon = function(url, data){
            return collector(url) && blocked() ? false : sendBeacon.call(this, url, data);
          };
          navigator.sendBeacon = guardedBeacon;
          if(navigator.sendBeacon !== guardedBeacon) return false;
        }
        if(typeof window.fetch === "function"){
          const fetch = window.fetch;
          const guardedFetch = function(input, options){
            if(!collector(typeof input === "string" || input instanceof URL ? input : input.url)) return fetch.call(this, input, options);
            if(blocked()) return Promise.reject(new DOMException("Analytics excluded", "AbortError"));
            const controller = new AbortController();
            const signal = options?.signal || (input instanceof Request ? input.signal : null);
            const abort = ()=>controller.abort();
            if(signal?.aborted) abort();
            else signal?.addEventListener("abort", abort, {once:true});
            pending.add(controller);
            return fetch.call(this, input, {...options, signal:controller.signal}).finally(()=>{
              pending.delete(controller); signal?.removeEventListener("abort", abort);
            });
          };
          window.fetch = guardedFetch;
          if(window.fetch !== guardedFetch) return false;
        }
        guardsReady = true;
        return true;
      }catch(e){ return false; }
    }
    function stop(reload){
      if(!started) return;
      stopped = true;
      for(const request of pending){ try{ request.abort(); }catch(e){} }
      pending.clear();
      // Removing a script cannot undo its listeners. Reload tears down the
      // document; send-time guards block final requests in the meantime.
      // On persistence failure, keep this document blocked instead of losing
      // its in-memory choice. The control explains the reload limitation.
      if(reload) location.reload();
    }
    function setExcluded(value){
      sessionExcluded = !!value;
      try{
        if(value) localStorage.setItem(EXCLUDE_KEY, "1");
        else { localStorage.removeItem(EXCLUDE_KEY); localStorage.removeItem("skipgc"); }
        const stored = localStorage.getItem(EXCLUDE_KEY) === "1" || localStorage.getItem("skipgc") === "t";
        if(stored !== !!value) throw new Error("preference was not saved");
        storageFailed = false; sessionExcluded = false;
        if(value) stop(true);
        else if(stopped) location.reload();
        return true;
      }catch(e){
        storageFailed = true; sessionExcluded = true; stop(false); return false;
      }
    }
    function visit(){
      if(started || unavailable || blocked()) return false;
      if(!installGuards()){ unavailable = true; return false; }
      started = true;
      try{
        const script = document.createElement("script");
        script.type = "module";
        script.src = BEACON_SRC;
        script.setAttribute("data-cf-beacon", JSON.stringify({token}));
        script.addEventListener("error", ()=>{ unavailable = true; }, {once:true});
        document.body.appendChild(script);
        return true;
      }catch(e){ unavailable = true; return false; }
    }
    window.addEventListener("storage", event=>{
      if(event.key === null || event.key === EXCLUDE_KEY || event.key === "skipgc"){
        if(excluded() || storageFailed) stop(!storageFailed);
      }
    });
    window.addEventListener("pageshow", ()=>{
      if(started && (excluded() || storageFailed)) stop(!storageFailed);
    });
    return {visit, excluded, setExcluded, storageFailed:()=>storageFailed,
      unavailable:()=>unavailable, resetNavigation:()=>{}};
  }
  window.LEDGER_ANALYTICS = {create, EXCLUDE_KEY};
})();
