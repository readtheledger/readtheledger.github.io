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
const OUT  = path.resolve(process.argv[2] || path.join(ROOT, "_site"));
const SITE = "https://readtheledger.github.io";
const SITE_TITLE = "The Ledger — Finance, read properly";
const SITE_DESC  = "A quiet reader for high-quality, free-to-read financial journalism.";

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
const contentSrc = read("content.js");
const swSrc = read("sw.js");

for (const marker of ["<!-- meta:start", "<!-- meta:end -->", "<!-- static:slot"]) {
  if (!index.includes(marker)) fail("index.html is missing the " + marker + " marker");
}
if (!swSrc.includes('const BUILD = "dev";')) fail("sw.js is missing the BUILD stamp");

// the app's own slug rule must be the one the pages were written with
const appSlug = /function slugOf\(section\)\{[^\n]*\}/.exec(index);
if (!appSlug) fail("could not find slugOf() in index.html");
const appSlugOf = vm.runInNewContext("(" + appSlug[0].replace(/^function slugOf/, "function") + ")");
for (const s of PAGE_SECTIONS) {
  if (appSlugOf(s) !== slugOf(s)) fail("slug for '" + s + "' differs between index.html and build.mjs");
}

const ctx = { window: {} };
vm.runInNewContext(contentSrc, ctx);
const content = ctx.window.LEDGER_CONTENT;
if (!content || !Array.isArray(content.articles) || !content.articles.length) fail("content.js carries no articles");
const articles = content.articles;

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
  if (!a.standfirst || !a.standfirst.trim()) fail(where + ": missing standfirst");
  if (!a.html || !a.html.trim()) fail(where + ": missing body");
  for (const re of RISKY) if (re.test(a.html)) fail(where + ": body contains markup the static page will not carry (" + re + ")");
  if (!Array.isArray(a.sources) || !a.sources.length) fail(where + ": needs at least one source");
  for (const s of a.sources) {
    if (!s.t || !s.p || !/^https:\/\/[^\s"<>]+$/.test(s.u || "")) fail(where + ": every source needs a title, an https URL and a publisher");
  }
}
if (articles.filter(a => a.weekly).length > 1) fail("more than one article is marked weekly");

/* ----------------------------------------------------------------- helpers */
const words = html => html.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim().split(" ").filter(Boolean).length;
const readMins = w => Math.max(1, Math.round(w / 220));
const plain = s => String(s || "").replace(/<[^>]+>/g, "").replace(/\s+/g, " ").trim();
const descOf = s => { const t = plain(s); return t.length <= 300 ? t : t.slice(0, 297).replace(/\s\S*$/, "") + "…"; };
const dateLong = iso => new Date(iso).toLocaleString("en-GB", {day:"numeric", month:"long", year:"numeric", timeZone:"UTC"});
const dateShort = iso => new Date(iso).toLocaleString("en-GB", {day:"numeric", month:"short", year:"numeric", timeZone:"UTC"});
const dateTime = iso => dateLong(iso) + ", " + new Date(iso).toLocaleString("en-GB", {hour:"2-digit", minute:"2-digit", timeZone:"UTC"}) + " UTC";
const jsonLd = obj => '<script type="application/ld+json">' + JSON.stringify(obj).replace(/</g, "\\u003c") + "</script>";
const byDate = (x, y) => Date.parse(y.date) - Date.parse(x.date);

const ORG = { "@type":"Organization", "name":"The Ledger", "url": SITE + "/", "logo": { "@type":"ImageObject", "url": SITE + "/icon-512.png" } };

function metaBlock({ title, ogTitle, description, canonical, ogType, extra, ld }) {
  return [
    "<!-- meta:start — written by build.mjs -->",
    `<title>${esc(title)}</title>`,
    `<meta name="description" content="${esc(description)}">`,
    `<link rel="canonical" href="${esc(canonical)}">`,
    `<meta property="og:type" content="${ogType}">`,
    `<meta property="og:site_name" content="The Ledger">`,
    `<meta property="og:title" content="${esc(ogTitle || title)}">`,
    `<meta property="og:description" content="${esc(description)}">`,
    `<meta property="og:url" content="${esc(canonical)}">`,
    `<meta property="og:image" content="${SITE}/icon-512.png">`,
    `<meta name="twitter:card" content="summary">`,
    `<meta name="twitter:title" content="${esc(ogTitle || title)}">`,
    `<meta name="twitter:description" content="${esc(description)}">`,
    `<meta name="twitter:image" content="${SITE}/icon-512.png">`,
    ...(extra || []),
    jsonLd(ld),
    "<!-- meta:end -->"
  ].join("\n");
}

function navHTML(current) {
  return '<nav class="static-nav" aria-label="Sections">' +
    ["Front page", ...PAGE_SECTIONS].map(s =>
      `<a class="seclink" href="${sectionPath(s)}"${s === current ? ' aria-current="page"' : ""}>${esc(s)}</a>`).join("") +
    "</nav>";
}

function cardHTML(a, lead) {
  const w = words(a.html);
  return `<article class="card${lead ? " lead" : ""}${a.weekly ? " weekly" : ""}">
      <div class="cardtop"><div>
        ${a.weekly ? '<p class="weeklylabel">The Ledger Weekly · Deep dive</p>' : `<p class="kicker">${esc(a.section)}</p>`}
        <h2 class="hl"><a href="${storyPath(a)}">${esc(a.title)}</a></h2>
        <p class="standfirst">${esc(a.standfirst)}</p>
        <div class="meta"><span class="badge">The Ledger</span><time class="dot" datetime="${esc(a.date)}">${dateShort(a.date)}</time><span class="dot">${readMins(w)} min read</span></div>
      </div></div>
    </article>`;
}

function listHTML(current, list, emptyText) {
  return `<div id="static">${navHTML(current)}
    ${list.length ? list.map((a, i) => cardHTML(a, i === 0)).join("\n") : `<div class="notice"><h3>Nothing here yet</h3><p style="margin:0">${esc(emptyText)}</p></div>`}
  </div>`;
}

function storyHTML(a) {
  const w = words(a.html);
  const srcs = a.sources.map(s =>
    `<li><a href="${esc(s.u)}" target="_blank" rel="noopener noreferrer">${esc(s.t)}</a> — ${esc(s.p)}</li>`).join("");
  return `<div id="static">${navHTML(a.section)}
    <article class="rwrap">
      <p class="kicker"><a href="${sectionPath(a.section)}">${esc(a.section)}</a></p>
      <h1>${esc(a.title)}</h1>
      <p class="rstand">${esc(a.standfirst)}</p>
      <div class="rmeta"><span class="badge">The Ledger</span><time class="dot" datetime="${esc(a.date)}">${dateTime(a.date)}</time><span class="dot">${readMins(w)} min read</span></div>
      <div class="rbody">${a.html}</div>
      <aside class="sourcesbox"><h3>Sources &amp; further reading</h3><ul>${srcs}</ul></aside>
      <p class="attrline">Reported and written by <strong>The Ledger</strong>. Material sources are credited and linked above; quotations are brief and attributed.</p>
      <p class="static-home"><a href="/">← The Ledger front page</a></p>
    </article>
  </div>`;
}

function page(meta, staticHtml) {
  return index
    .replace(/<!-- meta:start[\s\S]*?<!-- meta:end -->/, metaBlock(meta))
    .replace(/<!-- static:slot[^>]*-->/, staticHtml);
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
  ld: { "@context":"https://schema.org", "@type":"WebSite", "name":"The Ledger", "url": SITE + "/", "description": SITE_DESC, "publisher": ORG }
}, listHTML("Front page", frontList, "")));

// sections
const sectionUrls = [];
for (const s of PAGE_SECTIONS) {
  const list = sorted.filter(a => a.section === s);
  const canonical = SITE + sectionPath(s);
  write(sectionPath(s).slice(1) + "index.html", page({
    title: s + " — The Ledger", ogTitle: s + " — The Ledger",
    description: "The Ledger's " + s + " desk: original reporting and analysis, every source credited and linked.",
    canonical, ogType: "website",
    ld: { "@context":"https://schema.org", "@type":"CollectionPage", "name": s + " — The Ledger", "url": canonical, "isPartOf": { "@type":"WebSite", "name":"The Ledger", "url": SITE + "/" } }
  }, listHTML(s, list, "The Ledger has not published in " + s + " yet. The front page carries the latest edition.")));
  if (list.length) sectionUrls.push({ loc: canonical, lastmod: list[0].date });
}

// stories
for (const a of articles) {
  const canonical = SITE + storyPath(a);
  const description = descOf(a.standfirst);
  write("story/" + a.id + "/index.html", page({
    title: a.title + " — The Ledger", ogTitle: a.title, description, canonical, ogType: "article",
    extra: [
      `<meta property="article:published_time" content="${esc(a.date)}">`,
      `<meta property="article:section" content="${esc(a.section)}">`,
      `<meta property="article:author" content="${SITE}/">`
    ],
    ld: {
      "@context":"https://schema.org", "@type":"NewsArticle",
      "headline": a.title, "description": description,
      "datePublished": a.date, "dateModified": a.date,
      "articleSection": a.section, "wordCount": words(a.html),
      "isAccessibleForFree": true, "inLanguage": "en",
      "url": canonical, "mainEntityOfPage": { "@type":"WebPage", "@id": canonical },
      "image": [SITE + "/icon-512.png"],
      "author": { "@type":"Organization", "name":"The Ledger", "url": SITE + "/" },
      "publisher": ORG,
      "citation": a.sources.map(s => ({ "@type":"CreativeWork", "name": s.t, "url": s.u, "publisher": { "@type":"Organization", "name": s.p } }))
    }
  }, storyHTML(a)));
}

// sitemap and robots
const urls = [{ loc: SITE + "/", lastmod: newest }]
  .concat(sectionUrls)
  .concat(articles.map(a => ({ loc: SITE + storyPath(a), lastmod: a.date })));
write("sitemap.xml",
  '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
  urls.map(u => `  <url><loc>${esc(u.loc)}</loc><lastmod>${esc(u.lastmod)}</lastmod></url>`).join("\n") +
  "\n</urlset>\n");
write("robots.txt", "User-agent: *\nAllow: /\n\nSitemap: " + SITE + "/sitemap.xml\n");

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
  <nav aria-label="Sections">${PAGE_SECTIONS.map(s => `<a href="${sectionPath(s)}">${esc(s)}</a>`).join("")}</nav>
</main>
</body>
</html>
`);

// the app's files, with the service worker stamped by the edition it ships
const stamp = crypto.createHash("sha256").update(index).update(contentSrc).update(swSrc).digest("hex").slice(0, 8);
write("sw.js", swSrc.replace('const BUILD = "dev";', 'const BUILD = "' + stamp + '";'));
for (const f of ["content.js", "manifest.webmanifest", "icon-180.png", "icon-192.png", "icon-512.png", "icon-maskable-512.png"]) {
  fs.copyFileSync(path.join(ROOT, f), path.join(OUT, f));
  written.push(f);
}
write(".nojekyll", "");

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
for (const m of fs.readFileSync(path.join(OUT, "sw.js"), "utf8").matchAll(/"(\/[^"]*)"/g)) check("", m[1]);
for (const m of fs.readFileSync(path.join(OUT, "manifest.webmanifest"), "utf8").matchAll(/"src": *"([^"]+)"/g)) check("", m[1]);
if (missing.size) fail("references to files that are not in the output:\n  " + [...missing].join("\n  "));

console.log("build: " + written.filter(f => f.endsWith(".html")).length + " pages, " + articles.length + " stories, " + sectionUrls.length + " sections with content, shell " + stamp + " → " + OUT);
