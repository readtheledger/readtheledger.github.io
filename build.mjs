#!/usr/bin/env node
/* The Ledger — build.

   The app is still one file, index.html, and the publication is still content.js.
   This script gives every Ledger story and every editorial section a page of its
   own: the app, with that page's title, description, canonical address and
   sharing metadata in its head, and a static copy of the content inside <main>
   so the page reads in full without JavaScript. When the app boots on one of
   those pages it removes the static copy and opens the same thing in the reader.

   It also writes the sitemap, robots.txt, a real 404 page, stamps the service
   worker with a hash of the edition, and refuses to ship if any file a page
   references is missing from the output.

     node build.mjs            # writes ./_site
     node build.mjs /some/dir  # writes there instead

   Node 18 or later, no dependencies. */

import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import crypto from "node:crypto";
import { fileURLToPath } from "node:url";

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const argv = process.argv.slice(2);
const opt  = (name, dflt) => { const i = argv.indexOf("--" + name); return i >= 0 ? argv[i + 1] : dflt; };
const OUT  = path.resolve(argv.find(a => !a.startsWith("--") && !argv[argv.indexOf(a) - 1]?.startsWith("--")) || path.join(ROOT, "_site"));
const CONTENT_FILE = path.resolve(opt("content", path.join(ROOT, "content.js")));   // the tests build from a content file of their own
const ASSETS_DIR   = path.resolve(opt("assets", path.join(ROOT, "assets", "editorial")));   // and, for the worker's cache test, from pictures of their own
const SITE = "https://readtheledger.github.io";
const SITE_TITLE = "The Ledger — Finance, read properly";
const SITE_DESC  = "The Ledger's own financial reporting and analysis — markets, central banks, the economy, tech and personal finance — every source credited and linked.";
const ABOUT_PATH = "/about/";
const PRIVACY_PATH = "/privacy/";
const FEED_PATH  = "/feed.xml";
const NEWS_SITEMAP = "/sitemap-news.xml";
const REPO = "https://github.com/readtheledger/readtheledger.github.io";
/* a news sitemap lists what was published in the last two days, and nothing older */
const NEWS_WINDOW_MS = 48 * 3600 * 1000;
const NOW = Date.parse(opt("now", "")) || Date.now();   // the tests build "as of" a date

/* mirrors the app (index.html, "1b. addresses"); the build checks they agree */
const PAGE_SECTIONS = ["Markets","Companies","Economics","Central Banks","Opinion","Tech & Finance","Personal Finance"];
const KINDS = ["news","analysis","deep"];
function slugOf(section){ return String(section).toLowerCase().replace(/&/g,"and").replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,""); }
function sectionPath(section){ return section==="Front page" ? "/" : "/"+slugOf(section)+"/"; }
function storyPath(a){ return "/story/"+encodeURIComponent(a.id)+"/"; }

const fail = msg => { console.error("build: " + msg); process.exit(1); };
const esc = s => String(s==null?"":s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const read = f => fs.readFileSync(path.join(ROOT, f), "utf8");

/* ------------------------------------------------------------------ inputs */
const index = read("index.html");
const contentSrc = fs.readFileSync(CONTENT_FILE, "utf8");
const swSrc = read("sw.js");
const aboutSrc = read("about.js");
const privacySrc = read("privacy.js");
const consentSrc = read("consent.js");
const analyticsSrc = read("analytics.js");
const mediaSrc = read("media.js");
const productionSrc = read("production.js");

for (const marker of ["<!-- meta:start", "<!-- meta:end -->", "<!-- static:slot", '<p class="datestrip" id="datestrip"', '<meta name="robots" id="robotsMeta" content="index,follow">']) {
  if (!index.includes(marker)) fail("index.html is missing the " + marker + " marker");
}
if (!swSrc.includes('const BUILD = "dev";')) fail("sw.js is missing the BUILD stamp");
if (!/^const ROUTES = \[[^\n]*\];$/m.test(swSrc)) fail("sw.js is missing the ROUTES list");

// the app's own slug rule must be the one the pages were written with
const appSlug = /function slugOf\(section\)\{[^\n]*\}/.exec(index);
if (!appSlug) fail("could not find slugOf() in index.html");
const appSlugOf = vm.runInNewContext("(" + appSlug[0].replace(/^function slugOf/, "function") + ")");
for (const s of PAGE_SECTIONS) {
  if (appSlugOf(s) !== slugOf(s)) fail("slug for '" + s + "' differs between index.html and build.mjs");
}

const ctx = { window: {} };
vm.runInNewContext(productionSrc, ctx);
const production = ctx.window.LEDGER_PRODUCTION;
vm.runInNewContext(contentSrc, ctx);
const content = ctx.window.LEDGER_CONTENT;
if (!content || !Array.isArray(content.articles) || !content.articles.length) fail("content.js carries no articles");
const articles = content.articles;
vm.runInNewContext(aboutSrc, ctx);
const about = ctx.window.LEDGER_ABOUT;
vm.runInNewContext(privacySrc, ctx);
const privacy = ctx.window.LEDGER_PRIVACY;
vm.runInNewContext(mediaSrc, ctx);
const M = ctx.window.LEDGER_MEDIA;
if (!M || !M.figureHTML) fail("media.js carries no LEDGER_MEDIA");
if (!about || !about.title || !about.standfirst || !about.html) fail("about.js carries no About page (title, standfirst, html)");
if (!privacy || !privacy.title || !privacy.standfirst || !privacy.html) fail("privacy.js carries no Privacy page (title, standfirst, html)");

/* ---------------------------------------------------------------- checking */
/* The article bodies are The Ledger's own, but a static page has no runtime
   sanitiser in front of it, so the build refuses anything that could run. */
const RISKY = [/<\s*(script|iframe|object|embed|style|form|link|meta|base)\b/i, /\son[a-z]+\s*=/i, /javascript\s*:/i, /srcdoc\s*=/i];
const ids = new Set();
for (const a of articles) {
  const where = "article " + (a.id || "(no id)");
  if (!a.id || !/^[a-z0-9-]+$/.test(a.id)) fail(where + ": id must be lowercase letters, digits and hyphens");
  if (ids.has(a.id)) fail(where + ": duplicate id");
  ids.add(a.id);
  if (!KINDS.includes(a.kind)) fail(where + ": kind must be one of " + KINDS.join(", "));
  if (!PAGE_SECTIONS.includes(a.section)) fail(where + ": section '" + a.section + "' has no page");
  if (!a.date || isNaN(Date.parse(a.date))) fail(where + ": date must be ISO 8601");
  if (!a.title || !a.title.trim()) fail(where + ": missing title");
  const productionError = production.error(a);
  if (productionError) fail(where + ": " + productionError);
  if (!a.standfirst || !a.standfirst.trim()) fail(where + ": missing standfirst");
  if (!a.html || !a.html.trim()) fail(where + ": missing body");
  for (const re of RISKY) if (re.test(a.html)) fail(where + ": body contains markup the static page will not carry (" + re + ")");
  if (a.updated !== undefined && (isNaN(Date.parse(a.updated)) || Date.parse(a.updated) < Date.parse(a.date))) fail(where + ": updated must be an ISO 8601 date on or after date");
  // an optional representative image, checked by the same contract the app
  // uses (media.js): fallback address, alt text, size, derivatives; never the logo
  const v = M.validate(a.image);
  if (!v.ok) fail(where + ": " + v.error);
  a.image = v.image;
  if (!Array.isArray(a.sources) || !a.sources.length) fail(where + ": needs at least one source");
  for (const s of a.sources) {
    if (!s.t || !s.p || !/^https:\/\/[^\s"<>]+$/.test(s.u || "")) fail(where + ": every source needs a title, an https URL and a publisher");
  }
}
if (articles.filter(a => a.weekly).length > 1) fail("more than one article is marked weekly");
for (const re of RISKY) if (re.test(about.html)) fail("about.js: body contains markup the static page will not carry (" + re + ")");
for (const re of RISKY) if (re.test(privacy.html)) fail("privacy.js: body contains markup the static page will not carry (" + re + ")");

/* ----------------------------------------------------------------- helpers */
const words = html => html.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim().split(" ").filter(Boolean).length;
const readMins = w => Math.max(1, Math.round(w / 220));
const plain = s => String(s || "").replace(/<[^>]+>/g, "").replace(/\s+/g, " ").trim();
const descOf = s => { const t = plain(s); return t.length <= 300 ? t : t.slice(0, 297).replace(/\s\S*$/, "") + "…"; };
const dateLong = iso => new Date(iso).toLocaleString("en-GB", {day:"numeric", month:"long", year:"numeric", timeZone:"UTC"});
const dateShort = iso => new Date(iso).toLocaleString("en-GB", {day:"numeric", month:"short", year:"numeric", timeZone:"UTC"});
const dateTime = iso => dateLong(iso) + ", " + new Date(iso).toLocaleString("en-GB", {hour:"2-digit", minute:"2-digit", timeZone:"UTC"}) + " UTC";
const jsonLd = obj => [].concat(obj).map(o => '<script type="application/ld+json">' + JSON.stringify(o).replace(/</g, "\\u003c") + "</script>").join("\n");
const byDate = (x, y) => Date.parse(y.date) - Date.parse(x.date);

/* the publisher, with only what the publication has stated about itself: its
   name, its address, its logo and its public source repository */
const ORG = { "@type":"Organization", "@id": SITE + "/#organization", "name":"The Ledger", "url": SITE + "/", "logo": { "@type":"ImageObject", "url": SITE + "/icon-512.png", "width": 512, "height": 512 }, "sameAs": [REPO] };
/* Home › Section › Story, as structured data, so the page's place in the site is stated */
const crumbs = items => ({ "@context":"https://schema.org", "@type":"BreadcrumbList",
  "itemListElement": items.map((it, i) => ({ "@type":"ListItem", "position": i + 1, "name": it.name, "item": it.url })) });
const HOME = { name: "The Ledger", url: SITE + "/" };

function metaBlock({ title, ogTitle, description, canonical, ogType, extra, ld, image }) {
  // the sharing image: the piece's own when it has one, otherwise the icon
  // (a sharing preview, not a claim that the icon is the article's image)
  const share = image ? absUrl(image.u) : SITE + "/icon-512.png";
  return [
    "<!-- meta:start — written by build.mjs -->",
    `<title>${esc(title)}</title>`,
    `<meta name="description" content="${esc(description)}">`,
    `<link rel="canonical" href="${esc(canonical)}">`,
    `<link rel="alternate" type="application/atom+xml" title="The Ledger" href="${FEED_PATH}">`,
    `<meta property="og:type" content="${ogType}">`,
    `<meta property="og:site_name" content="The Ledger">`,
    `<meta property="og:title" content="${esc(ogTitle || title)}">`,
    `<meta property="og:description" content="${esc(description)}">`,
    `<meta property="og:url" content="${esc(canonical)}">`,
    `<meta property="og:image" content="${esc(share)}">`,
    ...(image ? [`<meta property="og:image:width" content="${image.w}">`, `<meta property="og:image:height" content="${image.h}">`, `<meta property="og:image:alt" content="${esc(image.alt)}">`] : []),
    `<meta name="twitter:card" content="${image ? "summary_large_image" : "summary"}">`,
    `<meta name="twitter:title" content="${esc(ogTitle || title)}">`,
    `<meta name="twitter:description" content="${esc(description)}">`,
    `<meta name="twitter:image" content="${esc(share)}">`,
    ...(extra || []),
    jsonLd(ld),
    "<!-- meta:end -->"
  ].join("\n");
}

function navHTML(current) {
  return '<nav class="static-nav" aria-label="Sections">' +
    ["Front page", ...PAGE_SECTIONS].map(s =>
      `<a class="seclink" href="${sectionPath(s)}"${s === current ? ' aria-current="page"' : ""}>${esc(s)}</a>`).join("") +
    `<a class="seclink" href="${ABOUT_PATH}"${current === "About" ? ' aria-current="page"' : ""}>About</a>` +
    "</nav>";
}

/* pace, as the app keeps it: the lead's picture, thumbnails on the two stories after
   it, then text-led rows, then the feature's picture */
const THUMBS_AFTER_LEAD = 2;
function cardHTML(a, lead, pos) {
  const w = words(a.html);
  const variant = a.weekly ? "feature" : lead ? "lead" : "compact";
  const image = a.image && (variant !== "compact" || pos <= THUMBS_AFTER_LEAD) ? a.image : null;
  const fig = image ? M.figureHTML(image, { variant: variant === "compact" ? "thumb" : variant, eager: variant === "lead", caption: false }) : "";
  const cls = "card " + variant + (a.weekly ? " weekly" : "") + (image ? " has-image" : "");
  const meta = `<div class="meta"><span class="badge">The Ledger</span><time class="dot" datetime="${esc(a.date)}">${dateShort(a.date)}</time><span class="dot">${readMins(w)} min read</span></div>`;
  const thumb = variant === "compact" && !!image;
  const below = `<p class="standfirst">${esc(a.standfirst)}</p>
        ${meta}`;
  return `<article class="${cls}">
      ${variant !== "compact" ? fig : ""}
      <div class="cardtop"><div>
        ${a.weekly ? '<p class="weeklylabel">The Ledger Weekly · Deep dive</p>' : kickerHTML(a)}
        <h2 class="hl${a.weekly ? " feature-hl" : ""}"><a href="${storyPath(a)}">${esc(a.title)}</a></h2>
        ${thumb ? "" : below}
      </div>${thumb ? fig : ""}</div>
      ${thumb ? `<div class="cardbelow">${below}</div>` : ""}
    </article>`;
}

/* the About card at the foot of the front page, as the app shows it: no date */
function aboutCardHTML() {
  return `<article class="card about">
      <div class="cardtop"><div>
        <p class="kicker">About</p>
        <h2 class="hl"><a href="${ABOUT_PATH}">${esc(about.title)}</a></h2>
        <p class="standfirst">${esc(about.standfirst)}</p>
        <div class="meta"><span class="badge">The Ledger</span><span class="dot">Part of the app · no date</span></div>
      </div></div>
    </article>`;
}

/* every page opens with one h1: the front page's is for readers of the structure
   (the wordmark is the visible one), a section's is the heading the app shows */
function listHTML(current, list, emptyText) {
  const n = list.length;
  const head = current === "Front page"
    ? `<h1 class="sr">${esc(SITE_TITLE)}</h1>`
    : `<header class="viewhead"><h1>${esc(current)}</h1><p class="viewnote">${n} ${n === 1 ? "story" : "stories"}</p></header>`;
  return `<div id="static">${navHTML(current)}
    ${head}
    ${n ? list.map((a, i) => cardHTML(a, i === 0, i)).join("\n") : `<div class="notice"><h2>Nothing here yet</h2><p style="margin:0">${esc(emptyText)}</p></div>`}
    ${current === "Front page" ? aboutCardHTML() : ""}
  </div>`;
}

/* up to four other pieces, the same desk first, then the newest: real links
   between the Ledger's own pages, so no story is a dead end */
function relatedHTML(a) {
  const others = sorted.filter(x => x.id !== a.id);
  const pick = others.filter(x => x.section === a.section).concat(others.filter(x => x.section !== a.section)).slice(0, 4);
  if (!pick.length) return "";
  return `<nav class="related" aria-label="More from The Ledger"><h2>More from The Ledger</h2><ul>${
    pick.map(x => `<li><a href="${storyPath(x)}">${esc(x.title)}</a> <span class="dot">${esc(x.section)} · <time datetime="${esc(x.date)}">${dateShort(x.date)}</time></span></li>`).join("")
  }</ul></nav>`;
}

/* the story's own picture, rendered by media.js exactly as the reader renders it */
function ledeImageHTML(a) {
  return a.image ? M.figureHTML(a.image, { variant: "hero", eager: true }) : "";
}
const absUrl = u => /^https?:/.test(u) ? u : SITE + u;

/* as the app labels it: a news story more than a week old at build time is from
   the archive; analysis and deep work carry their date and are not expired by age */
const ARCHIVE_MS = 7 * 24 * 3600 * 1000;
const isArchive = a => (a.kind || "news") === "news" && NOW - Date.parse(a.date) > ARCHIVE_MS;
const kickerHTML = (a, link) => `<p class="kicker">${isArchive(a) ? '<span class="arch">From the archive · </span>' : ""}${link ? `<a href="${sectionPath(a.section)}">${esc(a.section)}</a>` : esc(a.section)}</p>`;

function storyHTML(a) {
  const w = words(a.html);
  const srcs = a.sources.map(s =>
    `<li><a href="${esc(s.u)}" target="_blank" rel="noopener noreferrer">${esc(s.t)}</a> — ${esc(s.p)}</li>`).join("");
  return `<div id="static">${navHTML(a.section)}
    <article class="rwrap${a.kind === "deep" ? " feature" : ""}">
      ${kickerHTML(a, true)}
      <h1>${esc(a.title)}</h1>
      <p class="rstand">${esc(a.standfirst)}</p>
      ${ledeImageHTML(a)}
      <div class="rmeta"><span class="badge">The Ledger</span><time class="dot" datetime="${esc(a.date)}">${dateTime(a.date)}</time><span class="dot">${readMins(w)} min read</span></div>
      <div class="rbody">${a.html}</div>
      <aside class="sourcesbox"><h2>Sources &amp; further reading</h2><ul>${srcs}</ul></aside>
      <p class="attrline">${production.line(a)} Material sources are credited and linked above; quotations are brief and attributed.</p>
      ${relatedHTML(a)}
      <p class="static-home"><a href="/">← The Ledger front page</a></p>
    </article>
  </div>`;
}

function infoHTML(info, label) {
  return `<div id="static">${navHTML(label)}
    <article class="rwrap">
      <p class="kicker">${esc(label)}</p>
      <h1>${esc(info.title)}</h1>
      <p class="rstand">${esc(info.standfirst)}</p>
      <div class="rmeta"><span class="badge">The Ledger</span><span class="dot">Part of the app · no date</span></div>
      <div class="rbody">${info.html}</div>
      <p class="attrline">This page is part of the app and is not an article; it carries no publication date.</p>
      <p class="static-home"><a href="/">← The Ledger front page</a></p>
    </article>
  </div>`;
}

function page(meta, staticHtml) {
  return index
    .replace(/<!-- meta:start[\s\S]*?<!-- meta:end -->/, metaBlock(meta))
    // a section with no stories yet is a real page with nothing to index; the
    // app keeps whatever value the build wrote here
    .replace('<meta name="robots" id="robotsMeta" content="index,follow">', `<meta name="robots" id="robotsMeta" content="${meta.robots || "index,follow"}">`)
    .replace(/<!-- static:slot[^>]*-->/, staticHtml)
    // the edition line comes from the publication, never from a clock: the
    // newest date in content.js, written here so it reads without JavaScript
    .replace(/(<p class="datestrip" id="datestrip"[^>]*>)[^<]*(<\/p>)/, "$1Latest edition " + esc(dateLong(newest)) + "$2");
}

/* ------------------------------------------------------------------ output */
fs.rmSync(OUT, { recursive:true, force:true });
fs.mkdirSync(OUT, { recursive:true });
const written = [];
function write(rel, body) {
  const f = path.join(OUT, rel);
  fs.mkdirSync(path.dirname(f), { recursive:true });
  fs.writeFileSync(f, body);
  written.push(rel);
}

const sorted = articles.slice().sort(byDate);
const frontList = sorted.filter(a => !a.weekly).concat(sorted.filter(a => a.weekly));
const newest = sorted[0].date;

// front page
write("index.html", page({
  title: SITE_TITLE, description: SITE_DESC, canonical: SITE + "/", ogType: "website",
  ld: [
    { "@context":"https://schema.org", "@type":"WebSite", "name":"The Ledger", "url": SITE + "/", "description": SITE_DESC, "publisher": ORG },
    Object.assign({ "@context":"https://schema.org" }, ORG)
  ]
}, listHTML("Front page", frontList, "")));

// about
write(ABOUT_PATH.slice(1) + "index.html", page({
  title: "About — The Ledger", ogTitle: "About The Ledger",
  description: descOf(about.standfirst), canonical: SITE + ABOUT_PATH, ogType: "website",
  ld: [
    { "@context":"https://schema.org", "@type":"AboutPage", "name":"About The Ledger", "url": SITE + ABOUT_PATH, "description": descOf(about.standfirst), "isPartOf": { "@type":"WebSite", "name":"The Ledger", "url": SITE + "/" }, "mainEntity": ORG },
    crumbs([HOME, { name: "About", url: SITE + ABOUT_PATH }])
  ]
}, infoHTML(about, "About")));

// Privacy is an informational WebPage, never an article or a dated edition.
write(PRIVACY_PATH.slice(1) + "index.html", page({
  title: "Privacy — The Ledger", ogTitle: privacy.title,
  description: descOf(privacy.standfirst), canonical: SITE + PRIVACY_PATH, ogType: "website",
  ld: [
    { "@context":"https://schema.org", "@type":"WebPage", "name":privacy.title, "url":SITE + PRIVACY_PATH, "description":descOf(privacy.standfirst), "isPartOf":{ "@type":"WebSite", "name":"The Ledger", "url":SITE + "/" } },
    crumbs([HOME, { name:"Privacy", url:SITE + PRIVACY_PATH }])
  ]
}, infoHTML(privacy, "Privacy")));

// sections
const sectionUrls = [];
for (const s of PAGE_SECTIONS) {
  const list = sorted.filter(a => a.section === s);
  const canonical = SITE + sectionPath(s);
  // the description says what is actually on the page: how many pieces, and the
  // latest one; an empty section says so, and is noindex until it has a story
  const description = list.length
    ? `${list.length} original ${list.length === 1 ? "piece" : "pieces"} from The Ledger's ${s} desk, every source credited and linked. Latest: ${plain(list[0].title)} (${dateLong(list[0].date)}).`
    : `The Ledger has not published in ${s} yet. The front page carries the latest edition.`;
  write(sectionPath(s).slice(1) + "index.html", page({
    title: s + " — The Ledger", ogTitle: s + " — The Ledger",
    description: descOf(description),
    canonical, ogType: "website",
    robots: list.length ? "index,follow" : "noindex,follow",
    ld: [
      { "@context":"https://schema.org", "@type":"CollectionPage", "name": s + " — The Ledger", "url": canonical, "description": descOf(description), "isPartOf": { "@type":"WebSite", "name":"The Ledger", "url": SITE + "/" },
        ...(list.length ? { "hasPart": list.map(a => ({ "@type":"NewsArticle", "headline": a.title, "url": SITE + storyPath(a), "datePublished": a.date })) } : {}) },
      crumbs([HOME, { name: s, url: canonical }])
    ]
  }, listHTML(s, list, "The Ledger has not published in " + s + " yet. The front page carries the latest edition.")));
  if (list.length) sectionUrls.push({ loc: canonical, lastmod: list[0].date });
}

// stories
for (const a of articles) {
  const canonical = SITE + storyPath(a);
  const description = descOf(a.standfirst);
  write("story/" + a.id + "/index.html", page({
    title: a.title + " — The Ledger", ogTitle: a.title, description, canonical, ogType: "article", image: a.image,
    extra: [
      `<meta property="article:published_time" content="${esc(a.date)}">`,
      `<meta property="article:section" content="${esc(a.section)}">`,
      `<meta property="article:author" content="${SITE}/">`
    ],
    ld: [{
      "@context":"https://schema.org", "@type":"NewsArticle",
      "headline": a.title, "description": description,
      "datePublished": a.date, "dateModified": a.updated || a.date,
      "articleSection": a.section, "wordCount": words(a.html),
      "isAccessibleForFree": true, "inLanguage": "en",
      "url": canonical, "mainEntityOfPage": { "@type":"WebPage", "@id": canonical },
      // image only when the piece has a representative one of its own: Google's
      // Article guidance asks for an image of the article, not a logo, and has
      // no required properties, so a piece without one simply carries none
      ...(a.image ? { "image": [Object.assign({ "@type":"ImageObject", "url": absUrl(a.image.u), "width": a.image.w, "height": a.image.h, "caption": a.image.caption || a.image.alt },
                                              a.image.credit ? { "creditText": a.image.credit } : {},
                                              // IPTC's digital source type, the vocabulary Google reads for AI-generated images
                                              a.image.ai ? { "digitalSourceType": "https://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia" } : {})] } : {}),
      "author": { "@type":"Organization", "name":"The Ledger", "url": SITE + "/" },
      "publisher": ORG,
      "citation": a.sources.map(s => ({ "@type":"CreativeWork", "name": s.t, "url": s.u, "publisher": { "@type":"Organization", "name": s.p } }))
    },
    crumbs([HOME, { name: a.section, url: SITE + sectionPath(a.section) }, { name: a.title, url: canonical }])]
  }, storyHTML(a)));
}

// sitemap and robots. The About page has no date of its own, so it carries none.
const urls = [{ loc: SITE + "/", lastmod: newest }]
  .concat(sectionUrls)
  .concat(articles.map(a => ({ loc: SITE + storyPath(a), lastmod: a.updated || a.date })))
  .concat([{ loc: SITE + ABOUT_PATH }, { loc: SITE + PRIVACY_PATH }]);
write("sitemap.xml",
  '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
  urls.map(u => `  <url><loc>${esc(u.loc)}</loc>${u.lastmod ? `<lastmod>${esc(u.lastmod)}</lastmod>` : ""}</url>`).join("\n") +
  "\n</urlset>\n");

// the news sitemap: only what was published in the last two days, which is what
// Google reads one for; an archive does not qualify, and the file says so by
// listing nothing. Whether to submit it is the owner's decision in Search Console.
const fresh = sorted.filter(a => NOW - Date.parse(a.date) <= NEWS_WINDOW_MS && Date.parse(a.date) <= NOW);
write(NEWS_SITEMAP.slice(1),
  '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">\n' +
  fresh.map(a => `  <url><loc>${esc(SITE + storyPath(a))}</loc><news:news><news:publication><news:name>The Ledger</news:name><news:language>en</news:language></news:publication><news:publication_date>${esc(a.date)}</news:publication_date><news:title>${esc(a.title)}</news:title></news:news></url>`).join("\n") +
  (fresh.length ? "\n" : "") + "</urlset>\n");

// nothing is disallowed: the app-only views (?view=, ?q=) are marked noindex on
// the page itself, and a crawler can only read that if it is allowed to fetch them
write("robots.txt", "User-agent: *\nAllow: /\n\nSitemap: " + SITE + "/sitemap.xml\nSitemap: " + SITE + NEWS_SITEMAP + "\n");

// an Atom feed of The Ledger's own pieces, in full: they are its own work, and a
// feed reader is a legitimate place to read them
const atomDate = iso => new Date(iso).toISOString();
write(FEED_PATH.slice(1),
  '<?xml version="1.0" encoding="UTF-8"?>\n<feed xmlns="http://www.w3.org/2005/Atom">\n' +
  `  <title>The Ledger</title>\n  <subtitle>${esc(SITE_DESC)}</subtitle>\n  <id>${SITE}/</id>\n` +
  `  <link href="${SITE}/"/>\n  <link rel="self" type="application/atom+xml" href="${SITE}${FEED_PATH}"/>\n` +
  `  <updated>${atomDate(sorted.reduce((m, a) => Math.max(m, Date.parse(a.updated || a.date)), 0))}</updated>\n` +
  `  <author><name>The Ledger</name><uri>${SITE}/</uri></author>\n` +
  sorted.map(a => `  <entry>\n    <title>${esc(a.title)}</title>\n    <id>${esc(SITE + storyPath(a))}</id>\n    <link href="${esc(SITE + storyPath(a))}"/>\n    <published>${atomDate(a.date)}</published>\n    <updated>${atomDate(a.updated || a.date)}</updated>\n    <category term="${esc(a.section)}"/>\n    <summary>${esc(plain(a.standfirst))}</summary>\n    <content type="html">${esc(a.html)}</content>\n  </entry>`).join("\n") +
  "\n</feed>\n");

// a real not-found page: no app, no service-worker registration, plain links out
write("404.html", `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>Page not found — The Ledger</title>
<link rel="icon" href="/icon-192.png">
<style>
:root{--paper:#FFF1E5;--ink:#12100E;--ink-3:#6B6560;--rule:#DCCFC4;--claret:#990F3D;--accent:#0F5499}
@media (prefers-color-scheme:dark){:root{--paper:#12100E;--ink:#F5EFE8;--ink-3:#9C948C;--rule:#332E29;--claret:#E4718F;--accent:#6FA8DC}}
body{margin:0;background:var(--paper);color:var(--ink);font-family:"Source Serif 4",Charter,Georgia,serif;line-height:1.6}
main{max-width:720px;margin:0 auto;padding:40px 18px}
.wordmark{font-family:"Playfair Display",Georgia,serif;font-weight:800;font-size:1.4rem;letter-spacing:-.02em;text-decoration:none;color:inherit}
.wordmark span{color:var(--claret)}
h1{font-family:"Playfair Display",Georgia,serif;font-weight:700;font-size:2rem;line-height:1.15;margin:28px 0 12px}
p{margin:0 0 14px;color:var(--ink-3)}
a{color:var(--accent)}
nav{border-top:1px solid var(--rule);margin-top:28px;padding-top:14px;font-family:Inter,-apple-system,sans-serif;font-size:.85rem;display:flex;flex-wrap:wrap;gap:6px 16px}
</style>
</head>
<body>
<main>
  <a class="wordmark" href="/">The Ledger<span>.</span></a>
  <h1>That page isn't in this edition.</h1>
  <p>The address may have been mistyped, or the story it pointed to is no longer published. Everything The Ledger has written is on the front page.</p>
  <p><a href="/">Go to the front page →</a></p>
  <nav aria-label="Sections">${PAGE_SECTIONS.map(s => `<a href="${sectionPath(s)}">${esc(s)}</a>`).join("")}<a href="${ABOUT_PATH}">About</a><a href="${PRIVACY_PATH}">Privacy</a></nav>
</main>
</body>
</html>
`);

// the app's files, with the service worker stamped by the edition it ships and
// told exactly which addresses the app can render offline: the front page, the
// sections and the stories that exist in this edition, and nothing else
const sourcesSrc = read("sources.js");
// the stamp covers the pictures too — hashed from their source files, before
// they are copied — so a replaced picture is a new build to the worker and its
// image cache is started afresh
const assetHash = crypto.createHash("sha256");
if (fs.existsSync(ASSETS_DIR)) {
  for (const f of fs.readdirSync(ASSETS_DIR, { recursive: true }).map(String).sort()) {
    const src = path.join(ASSETS_DIR, f);
    if (fs.statSync(src).isFile()) assetHash.update(f.replace(/\\/g, "/")).update(fs.readFileSync(src));
  }
}
const stamp = crypto.createHash("sha256").update(index).update(contentSrc).update(sourcesSrc).update(read("topics.js")).update(read("context.js")).update(aboutSrc).update(privacySrc).update(consentSrc).update(analyticsSrc).update(mediaSrc).update(productionSrc).update(swSrc).update(assetHash.digest()).digest("hex").slice(0, 8);
const routes = ["/", "/index.html", ABOUT_PATH, PRIVACY_PATH].concat(PAGE_SECTIONS.map(sectionPath), articles.map(storyPath));
const sw = swSrc
  .replace('const BUILD = "dev";', 'const BUILD = "' + stamp + '";')
  .replace(/^const ROUTES = \[[^\n]*\];$/m, "const ROUTES = " + JSON.stringify(routes) + ";");
if (!sw.includes('const BUILD = "' + stamp + '"') || !sw.includes('"/story/' + articles[0].id + '/"')) fail("sw.js was not stamped");
write("sw.js", sw);
for (const f of ["content.js", "sources.js", "topics.js", "context.js", "about.js", "privacy.js", "consent.js", "analytics.js", "media.js", "production.js", "manifest.webmanifest", "ads.txt", "icon-180.png", "icon-192.png", "icon-512.png", "icon-maskable-512.png"]) {
  // the publication the pages were written from is the one the app loads, so a
  // build from another content file (the tests do this) is consistent with itself
  fs.copyFileSync(f === "content.js" ? CONTENT_FILE : path.join(ROOT, f), path.join(OUT, f));
  written.push(f);
}
write(".nojekyll", "");

// the editorial pictures: web derivatives and their provenance, never a master
const assetsDir = ASSETS_DIR;
if (fs.existsSync(assetsDir)) {
  for (const f of fs.readdirSync(assetsDir, { recursive: true })) {
    const src = path.join(assetsDir, String(f));
    if (!fs.statSync(src).isFile()) continue;
    if (!/\.(webp|jpe?g|png|avif|json)$/i.test(src)) fail("assets/editorial carries a file the site does not serve: " + f);
    if (fs.statSync(src).size > 600 * 1024) fail("assets/editorial/" + f + " is larger than 600 KB — a master, not a web derivative");
    const rel = path.posix.join("assets", "editorial", String(f).replace(/\\/g, "/"));
    fs.mkdirSync(path.dirname(path.join(OUT, rel)), { recursive: true });
    fs.copyFileSync(src, path.join(OUT, rel));
    written.push(rel);
  }
}

// the gathered Newsstand, when fetch_feeds.mjs has run before the build; the app
// falls back to gathering in the browser when the file is absent
const editionFile = path.join(ROOT, "data", "feed.json");
if (fs.existsSync(editionFile)) {
  let edition;
  try { edition = JSON.parse(fs.readFileSync(editionFile, "utf8")); } catch (e) { fail("data/feed.json is not valid JSON: " + e.message); }
  if (!edition || !edition.fetched || !Array.isArray(edition.items) || !Array.isArray(edition.sources)) fail("data/feed.json is not an edition (needs fetched, sources, items)");
  fs.mkdirSync(path.join(OUT, "data"), { recursive:true });
  fs.copyFileSync(editionFile, path.join(OUT, "data", "feed.json"));
  written.push("data/feed.json");
  console.log("build: Newsstand edition gathered " + edition.fetched + ", " + edition.items.length + " items from " + edition.sources.filter(s => s.ok).length + " of " + edition.sources.length + " sources");
} else {
  console.log("build: no data/feed.json — the app will gather the Newsstand in the browser");
}

/* ------------------------------------------------------------------- guard */
/* Every address a page refers to must exist in the output: an asset, a page, or
   the service worker's precache list. A missing one fails the build here, not in
   the field. */
const missing = new Set();
function check(fromDir, ref) {
  if (!ref || /^(https?:|mailto:|data:|#|tel:)/i.test(ref)) return;
  if (ref.includes("${")) return;   // a template placeholder in the app's own script, not an address
  const clean = ref.split(/[?#]/)[0];
  if (!clean) return;
  const abs = clean.startsWith("/") ? clean : path.posix.join("/", fromDir, clean);
  const target = abs.endsWith("/") ? abs + "index.html" : abs;
  if (!fs.existsSync(path.join(OUT, target))) missing.add(ref + "  (from " + (fromDir || "/") + ")");
}
for (const rel of written) {
  if (!rel.endsWith(".html")) continue;
  const html = fs.readFileSync(path.join(OUT, rel), "utf8");
  const fromDir = path.posix.dirname(rel.replace(/\\/g, "/"));
  // a relative reference is resolved from the page's own directory, so a stray
  // src="content.js" inside /story/<id>/ is caught as the missing file it would be
  for (const m of html.matchAll(/\b(?:src|href)="([^"]+)"/g)) check(fromDir === "." ? "" : fromDir, m[1]);
}
// the worker's precache list and route list name files and pages that must exist
// (other strings in it, like a path prefix, are not addresses)
for (const list of ["FILES", "ROUTES"]) {
  const m = new RegExp("^const " + list + " = (\\[[\\s\\S]*?\\]);", "m").exec(sw);
  if (!m) fail("sw.js is missing " + list);
  for (const ref of JSON.parse(m[1].replace(/\/\/[^\n]*/g, ""))) check("", ref);
}
for (const m of fs.readFileSync(path.join(OUT, "manifest.webmanifest"), "utf8").matchAll(/"src": *"([^"]+)"/g)) check("", m[1]);
// every address a piece's picture needs must be in the output
for (const a of articles) if (a.image) for (const u of M.urlsOf(a.image)) if (!/^https?:/.test(u)) check("", u);
if (missing.size) fail("references to files that are not in the output:\n  " + [...missing].join("\n  "));

console.log("build: " + written.filter(f => f.endsWith(".html")).length + " pages, " + articles.length + " stories, " + sectionUrls.length + " sections with content, " + fresh.length + " in the news sitemap, shell " + stamp + " → " + OUT);
