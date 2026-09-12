/* Entry points only: no ad/CMP script loading and no consent-status claims.
   Google API contract: https://developers.google.com/funding-choices/fc-api-docs */
(function(){
  "use strict";
  let ready = false;
  const apiAvailable = ()=>ready && typeof window.googlefc?.showRevocationMessage === "function";
  function refresh(){
    document.querySelectorAll("[data-ad-settings]").forEach(button=>{
      button.hidden = !apiAvailable();
      button.disabled = !apiAvailable();
    });
  }
  function status(button, text, focus=false){
    const message = button.closest("[data-privacy-controls]")?.querySelector("[data-consent-status]");
    if(message){ message.textContent = text; message.hidden = false; if(focus) message.focus(); }
  }
  function unavailable(button){
    ready = false; refresh();
    status(button, "Advertising settings could not be opened. No change was confirmed. Please try again later; the Privacy page remains available.", true);
  }
  document.addEventListener("click", event=>{
    const button = event.target.closest?.("[data-ad-settings]");
    if(!button) return;
    event.preventDefault();
    if(!apiAvailable()){ unavailable(button); return; }
    try{
      let invoked = false;
      // The supported queue executes synchronously after CONSENT_API_READY.
      window.googlefc.callbackQueue.push({CONSENT_API_READY: ()=>{
        if(!apiAvailable()) throw new Error("Consent API unavailable");
        invoked = true;
        window.googlefc.showRevocationMessage();
      }});
      if(!invoked){ unavailable(button); return; }
      status(button, "Google has been asked to show advertising choices. This does not confirm a changed choice.");
    }catch(e){ unavailable(button); }
  });
  // This empty namespace/queue is not a loaded CMP. Only Google's readiness
  // callback plus its callable method can reveal the controls.
  window.googlefc = window.googlefc || {};
  window.googlefc.callbackQueue = window.googlefc.callbackQueue || [];
  try{
    window.googlefc.callbackQueue.push({CONSENT_API_READY: ()=>{
      ready = true; refresh();
    }});
  }catch(e){ ready = false; }
  window.LEDGER_CONSENT = {refresh};
  if(document.readyState === "loading") document.addEventListener("DOMContentLoaded", refresh, {once:true});
  else refresh();
})();
