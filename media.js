/* The Ledger — editorial media.
   One contract and one renderer for a piece's own image, shared by the app
   (index.html) and the build (build.mjs), so the static page and the reader
   produce the same markup and the browser fetches the picture once.

   A piece in content.js may carry:
     image: {
       u:       "/assets/editorial/<id>/hero-1200.jpg"   // the fallback JPEG; https or root-relative
       alt:     "what is visible in the picture",         // required
       w, h:    1200, 800,                                // the fallback's pixel size; required
       caption: "editorial caption — what the picture means for the story",   // optional
       credit:  "The Ledger",                             // who made it; optional
       ai:      true,                                     // an AI-generated illustration; rendered as a visible disclosure
       widths:  [480, 768, 1200]                          // WebP derivatives beside u, named hero-<w>.webp; optional
     }
   Nothing here is a claim about the story's facts; the caption must not add one.
   The site's own icon is never a piece's image. */
(function(){
  const esc = s => String(s==null?"":s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const URL_OK = /^(https:\/\/[^\s"<>]+|\/[^\s"<>]+)$/;

  /* the rendered width of each placement, so the browser picks the right derivative:
     the reader and the static story fill the viewport up to the column's width,
     a lead or feature card fills the feed column, a compact card shows a thumbnail */
  const SIZES = {
    hero:    "(min-width: 756px) 684px, 100vw",
    lead:    "(min-width: 1128px) 382px, (min-width: 820px) calc((100vw - 362px) * 0.52), calc(100vw - 28px)",
    feature: "(min-width: 1128px) 738px, (min-width: 820px) calc(100vw - 362px), calc(100vw - 28px)",
    thumb:   "112px"
  };
  const WIDTHS = [480, 768, 1200];

  function validate(im){
    if(im === undefined || im === null) return {ok:true, image:null};
    if(typeof im !== "object") return {ok:false, error:"image must be an object"};
    if(!URL_OK.test(im.u||"")) return {ok:false, error:"image.u must be an https address or a root-relative path"};
    if(/icon-\d+\.png$/.test(im.u)) return {ok:false, error:"the site icon is not a piece's image"};
    if(!im.alt || !String(im.alt).trim()) return {ok:false, error:"image.alt is required"};
    if(!(im.w > 0) || !(im.h > 0)) return {ok:false, error:"image.w and image.h are required"};
    if(im.widths !== undefined && (!Array.isArray(im.widths) || !im.widths.length || im.widths.some(x=>!(x>0)))) return {ok:false, error:"image.widths must be a list of pixel widths"};
    if(im.widths && Math.max.apply(null, im.widths) > im.w) return {ok:false, error:"image.widths must not exceed the fallback's width (no upscaling)"};
    return {ok:true, image:{
      u:String(im.u), alt:String(im.alt).trim(), w:Number(im.w), h:Number(im.h),
      caption:String(im.caption||"").trim(), credit:String(im.credit||"").trim(), ai:!!im.ai,
      widths: im.widths ? im.widths.map(Number).sort((a,b)=>a-b) : []
    }};
  }

  /* the WebP derivatives live beside the fallback, named hero-<width>.webp */
  function derivative(im, w){ return im.u.replace(/[^\/]+$/, "hero-" + w + ".webp"); }
  function srcsetOf(im){ return im.widths.map(w => derivative(im, w) + " " + w + "w").join(", "); }
  /* every address a page must serve for this image: the fallback and each derivative */
  function urlsOf(im){ return [im.u].concat(im.widths.map(w => derivative(im, w))); }

  function captionHTML(im){
    const bits = [];
    if(im.caption) bits.push(`<span class="fig-cap">${esc(im.caption)}</span>`);
    const credit = [];
    if(im.ai) credit.push(`<span class="fig-ai">AI-generated illustration</span>`);
    if(im.credit) credit.push(esc(im.credit));
    if(credit.length) bits.push(`<span class="fig-credit">${credit.join(" · ")}</span>`);
    return bits.length ? `<figcaption>${bits.join(" ")}</figcaption>` : "";
  }

  /* variant: hero (story page and reader), lead, feature, thumb (a compact card).
     eager: the one image likely to be the largest thing on the first screen. */
  function figureHTML(im, opts){
    opts = opts || {};
    const variant = SIZES[opts.variant] ? opts.variant : "hero";
    const eager = !!opts.eager;
    const srcset = srcsetOf(im);
    const img = `<img src="${esc(im.u)}" alt="${esc(im.alt)}" width="${im.w}" height="${im.h}"` +
      (srcset ? ` srcset="${esc(srcset)}" sizes="${SIZES[variant]}"` : "") +
      ` decoding="async"` + (eager ? ` loading="eager" fetchpriority="high"` : ` loading="lazy"`) + `>`;
    const cap = opts.caption === false ? "" : captionHTML(im);
    return `<figure class="fig fig-${variant}">${img}${cap}</figure>`;
  }

  const api = { validate, figureHTML, srcsetOf, urlsOf, captionHTML, SIZES, WIDTHS };
  if(typeof window !== "undefined") window.LEDGER_MEDIA = api;
})();
