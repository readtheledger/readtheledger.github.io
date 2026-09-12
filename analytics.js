/* One emission per visible navigation, not a timer-based visit estimate.
   This small adapter keeps the existing GoatCounter pixel protocol (p, rnd).
   Collector reception and dashboard session rules are separate from emission.
   See docs/measurement.md for the count model and privacy boundaries. */
(function(){
  "use strict";
  const EXCLUDE_KEY = "ledger.analytics.exclude";
  function create({site, origin, paths}){
    const allowed = new Set(paths);
    let current = null;
    let storageFailed = false;
    let sessionExcluded = false;
    function excluded(){
      try{
        const saved = localStorage.getItem(EXCLUDE_KEY) === "1" || localStorage.getItem("skipgc") === "t";
        return sessionExcluded || saved;
      }catch(e){ storageFailed = true; return true; }
    }
    function setExcluded(value){
      sessionExcluded = !!value;
      try{
        if(value) localStorage.setItem(EXCLUDE_KEY, "1");
        else { localStorage.removeItem(EXCLUDE_KEY); localStorage.removeItem("skipgc"); }
        const stored = localStorage.getItem(EXCLUDE_KEY) === "1" || localStorage.getItem("skipgc") === "t";
        if(stored !== !!value) throw new Error("preference was not saved");
        storageFailed = false;
        sessionExcluded = false;
        return true;
      }catch(e){ storageFailed = true; sessionExcluded = true; return false; }
    }
    function blocked(){
      if(excluded() || storageFailed) return true;
      if(!site || !/^[a-z0-9-]+$/.test(site) || location.origin !== origin || location.protocol !== "https:") return true;
      if(window.top !== window.self || document.prerendering || document.visibilityState === "prerender") return true;
      return !!navigator.webdriver || /headless|playwright|selenium|phantomjs|\bbot\b|crawler|spider/i.test(navigator.userAgent || "");
    }
    function visit(key, path){
      if(!allowed.has(path) || !key || key === current) return false;
      // Remember the visible destination even while excluded: enabling later
      // doesn't replay visits or count a settings change as navigation.
      current = key;
      if(blocked()) return false;
      try{
        const img = new Image();
        if(!("referrerPolicy" in img)) return false;
        img.referrerPolicy = "no-referrer";
        img.src = "https://" + site + ".goatcounter.com/count?p=" + encodeURIComponent(path) + "&rnd=" + Date.now();
        return true;
      }catch(e){ return false; } // analytics must never interrupt reading; no retries
    }
    return {
      visit, excluded, setExcluded,
      storageFailed: ()=>storageFailed,
      // A restored document or activated prerender is a new visible entry.
      resetNavigation: ()=>{ current = null; }
    };
  }
  window.LEDGER_ANALYTICS = {create, EXCLUDE_KEY};
})();
