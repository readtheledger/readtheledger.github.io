#!/usr/bin/env node
/* The Ledger — gathers the Newsstand.

   Reads every public feed in sources.js and writes one file, data/feed.json,
   that the app loads with a single request: the items, the time they were
   gathered, and the state of every source. Run by the Pages workflow before
   the build, on every push and on a schedule.

   What it promises:
     - A feed that does not answer never empties the page: its items from the
       previous gathering (read from the live site) are kept and marked stale,
       with the time they were actually gathered.
     - Every item is checked: an absolute http(s) link, a publication date that
       parses and is not in the future, a title. Anything else is dropped and
       counted, never shipped.
     - The same story is carried once. Duplicates are removed by link and then
       by title, and a wire story credited to Reuters, AP or the like is marked
       with that origin, so copies of one syndicated report can never pass for
       independent confirmations.
     - Rights are enforced in the data. Each source declares what The Ledger may
       carry from it; a source with no rights value, or "full" with no licence,
       stops the run. A "summary" source ships an excerpt of the text and a word
       count — never the article — so nothing downstream can republish what it
       was never given.

     node fetch_feeds.mjs                       # sources.js → data/feed.json
     node fetch_feeds.mjs --sources s.js --previous prev.json --out out.json
                          --now 2026-09-08T03:00:00Z --timeout 15000

   Node 18 or later, no dependencies. */

import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const argv = process.argv.slice(2);
const opt = (name, dflt) => { const i = argv.indexOf("--" + name); return i >= 0 ? argv[i + 1] : dflt; };
const SOURCES_FILE = path.resolve(opt("sources", path.join(ROOT, "sources.js")));
const OUT          = path.resolve(opt("out", path.join(ROOT, "data", "feed.json")));
const PREVIOUS     = opt("previous", "https://readtheledger.github.io/data/feed.json");
const NOW          = new Date(opt("now", new Date().toISOString()));
const TIMEOUT      = Number(opt("timeout", 15000));
const PER_SOURCE   = 15;        // items kept per source
const EXCERPT      = 1500;      // characters of text shipped for a "summary" source
const FULL_MAX     = 120000;    // characters of markup shipped for a "full" source
const FUTURE_SLACK = 24 * 3600 * 1000;
const RIGHTS = ["summary", "full"];

const fail = msg => { console.error("fetch_feeds: " + msg); process.exit(1); };

/* ------------------------------------------------------------- the sources */
const ctx = { window: {} };
try { vm.runInNewContext(fs.readFileSync(SOURCES_FILE, "utf8"), ctx); } catch (e) { fail("cannot read " + SOURCES_FILE + ": " + e.message); }
const SOURCES = ctx.window.LEDGER_SOURCES;
if (!Array.isArray(SOURCES) || !SOURCES.length) fail("no sources in " + SOURCES_FILE);
for (const s of SOURCES) {
  if (!s.n || !/^https?:\/\//.test(s.u || "")) fail("a source needs a name and an http(s) URL: " + JSON.stringify(s));
  if (!RIGHTS.includes(s.rights)) fail(s.n + ": no recorded rights — every source must say \"summary\" or \"full\"");
  if (s.rights === "full" && !s.lic) fail(s.n + ": rights \"full\" needs the licence named in lic");
}
if (new Set(SOURCES.map(s => s.n)).size !== SOURCES.length) fail("two sources share a name");

/* --------------------------------------------------------------- helpers */
const ENT = { amp:"&", lt:"<", gt:">", quot:'"', apos:"'", nbsp:" ", ndash:"–", mdash:"—", hellip:"…", rsquo:"’", lsquo:"‘", rdquo:"”", ldquo:"“", copy:"©", reg:"®", trade:"™", pound:"£", euro:"€", yen:"¥", cent:"¢", deg:"°", middot:"·" };
function decode(s) {
  return String(s || "")
    .replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(parseInt(h, 16)))
    .replace(/&#(\d+);/g, (_, d) => String.fromCodePoint(Number(d)))
    .replace(/&([a-z]+);/gi, (m, n) => (n.toLowerCase() in ENT) ? ENT[n.toLowerCase()] : m);
}
const unwrapCdata = s => String(s || "").replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1");
function textOf(html) {
  return decode(String(html || "")
    .replace(/<(script|style)\b[\s\S]*?<\/\1>/gi, " ")
    .replace(/<\/(p|div|li|h[1-6]|blockquote|tr|br)\s*>|<br\s*\/?>/gi, "\n")
    .replace(/<[^>]+>/g, " "))
    .replace(/[ \t ]+/g, " ").replace(/\s*\n\s*/g, "\n").replace(/\n{3,}/g, "\n\n").trim();
}
const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;" }[c]));
const wordsOf = t => t ? t.trim().split(/\s+/).filter(Boolean).length : 0;
function hash(s) { let h = 0; s = String(s); for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0; return "a" + Math.abs(h).toString(36); }
const normTitle = t => String(t || "").toLowerCase().replace(/[^a-z0-9 ]/g, "").replace(/\s+/g, " ").trim().slice(0, 70);
function normLink(u) {
  try {
    const x = new URL(u);
    x.hash = "";
    for (const k of [...x.searchParams.keys()]) if (/^(utm_|fbclid|gclid|ref$|source$|cmpid|ncid|mc_cid|mc_eid)/i.test(k)) x.searchParams.delete(k);
    x.hostname = x.hostname.replace(/^www\./, "");
    return (x.origin + x.pathname.replace(/\/+$/, "") + (x.search || "")).toLowerCase();
  } catch (e) { return String(u || "").toLowerCase(); }
}

/* Element text by tag name, with or without a namespace prefix, CDATA unwrapped. */
function tag(xml, names) {
  for (const n of names) {
    const re = new RegExp("<" + n + "(?:\\s[^>]*)?>([\\s\\S]*?)<\\/" + n + "\\s*>", "i");
    const m = re.exec(xml);
    if (m && m[1].trim()) return unwrapCdata(m[1]).trim();
  }
  return "";
}
function attrs(s) {
  const out = {};
  for (const m of s.matchAll(/([a-zA-Z:_-]+)\s*=\s*("([^"]*)"|'([^']*)')/g)) out[m[1].toLowerCase()] = m[3] != null ? m[3] : m[4];
  return out;
}
function atomLink(entry) {
  let first = "";
  for (const m of entry.matchAll(/<link\b([^>]*?)\/?>/gi)) {
    const a = attrs(m[1]);
    if (!a.href) continue;
    if ((a.rel || "alternate") === "alternate" && (!a.type || /html/i.test(a.type))) return a.href;
    if (!first) first = a.href;
  }
  return first;
}

/* ---------------------------------------------------------------- parsing */
function parseFeed(xml) {
  xml = String(xml).replace(/^﻿/, "");
  const atom = /<feed[\s>]/i.test(xml) && !/<rss[\s>]/i.test(xml);
  const nodes = [...xml.matchAll(atom ? /<entry\b[\s\S]*?<\/entry>/gi : /<item\b[\s\S]*?<\/item>/gi)].map(m => m[0]);
  if (!nodes.length) throw new Error(atom ? "no entries" : (/<rss|<rdf|<feed/i.test(xml) ? "empty feed" : "not a feed"));
  return nodes.map(node => {
    let link = atom ? atomLink(node) : decode(tag(node, ["link"])) || atomLink(node);
    if (!link && !atom) { const g = tag(node, ["guid"]); if (/^https?:\/\//.test(g)) link = g; }
    // Atom type="html" and many RSS descriptions carry the markup entity-escaped
    // rather than in CDATA; unescape it once so text and markup are derived from
    // the same thing (real markup is left as it is)
    let rawHtml = tag(node, ["content:encoded", "content", "description", "summary"]);
    if (!/<[a-z!\/]/i.test(rawHtml) && /&lt;[a-z\/]/i.test(rawHtml)) rawHtml = decode(rawHtml);
    const title   = decode(textOf(tag(node, ["title"]))).replace(/\s+/g, " ").trim();
    const author  = decode(textOf(tag(node, ["dc:creator", "creator", "name", "author"]))).replace(/\s+/g, " ").trim();
    const date    = decode(tag(node, ["pubDate", "published", "updated", "dc:date", "date"])).trim();
    return { title, link: decode(link || "").trim(), rawHtml, author, date };
  });
}

/* A wire story keeps its origin, whoever carried it. */
const WIRE = /\b(Reuters|Associated Press|\(AP\)|AP News|Bloomberg News|Agence France-Presse|\(AFP\)|PA Media|Press Association|Dow Jones Newswires)\b/;
function originOf(author, text, source) {
  const head = (author || "") + " " + (text || "").slice(0, 240);
  const m = WIRE.exec(head);
  if (!m) return source;
  const w = m[1];
  if (/^Associated Press|\(AP\)|AP News/.test(w)) return "Associated Press";
  if (/Agence France-Presse|\(AFP\)/.test(w)) return "AFP";
  if (/PA Media|Press Association/.test(w)) return "PA Media";
  return w.replace(/ News(wires)?$/, "");
}

/* ------------------------------------------------------------ one source */
async function fetchOne(src) {
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), TIMEOUT);
  try {
    const res = await fetch(src.u, {
      signal: ctl.signal, redirect: "follow",
      headers: { "User-Agent": "TheLedger/1.0 (+https://readtheledger.github.io/)", "Accept": "application/rss+xml, application/atom+xml, application/xml;q=0.9, text/xml;q=0.9, */*;q=0.5" }
    });
    if (!res.ok) throw new Error("HTTP " + res.status);
    const xml = await res.text();
    const parsed = parseFeed(xml);
    const dropped = {};
    const drop = why => { dropped[why] = (dropped[why] || 0) + 1; return null; };
    const items = parsed.map(p => {
      if (!p.title) return drop("no title");
      if (!/^https?:\/\/\S+$/i.test(p.link)) return drop("no absolute link");
      const ts = Date.parse(p.date);
      if (!p.date || isNaN(ts)) return drop("no publication date");
      if (ts > NOW.getTime() + FUTURE_SLACK) return drop("date in the future");
      const text = textOf(p.rawHtml);
      const words = wordsOf(text);
      let html;
      if (src.rights === "full") {
        html = p.rawHtml.length > FULL_MAX ? p.rawHtml.slice(0, FULL_MAX) : p.rawHtml;
      } else {
        // an excerpt, as plain text in one paragraph: enough for a standfirst and
        // one short quote, never the article
        let ex = text.replace(/\s+/g, " ").trim();
        if (ex.length > EXCERPT) { const cut = ex.slice(0, EXCERPT); const stop = cut.lastIndexOf(". "); ex = (stop > 400 ? cut.slice(0, stop + 1) : cut.replace(/\s\S*$/, "")) + " …"; }
        html = ex ? "<p>" + esc(ex) + "</p>" : "";
      }
      return {
        id: hash(p.link || p.title),
        source: src.n, origin: originOf(p.author, text, src.n),
        title: p.title, link: p.link, author: p.author || src.n,
        date: new Date(ts).toISOString(),
        html, words,
        section: src.s || "Markets", kind: src.k || "news", weight: src.q || 1, lic: src.lic || "", rights: src.rights
      };
    }).filter(Boolean).slice(0, PER_SOURCE);
    return { ok: true, items, dropped };
  } catch (e) {
    return { ok: false, items: [], error: (e && e.name === "AbortError") ? "timed out after " + TIMEOUT + " ms" : String(e && e.message || e) };
  } finally { clearTimeout(timer); }
}

/* ------------------------------------------------------- previous edition */
async function readPrevious(where) {
  try {
    let text;
    if (/^https?:\/\//.test(where)) {
      const ctl = new AbortController(); const t = setTimeout(() => ctl.abort(), TIMEOUT);
      try { const r = await fetch(where, { signal: ctl.signal, headers: { "User-Agent": "TheLedger/1.0" } }); if (!r.ok) throw new Error("HTTP " + r.status); text = await r.text(); }
      finally { clearTimeout(t); }
    } else if (fs.existsSync(where)) text = fs.readFileSync(where, "utf8");
    else return null;
    const j = JSON.parse(text);
    return (j && Array.isArray(j.items) && Array.isArray(j.sources)) ? j : null;
  } catch (e) { return null; }
}

/* ------------------------------------------------------------------- run */
const previous = await readPrevious(PREVIOUS);
const prevSource = n => previous ? previous.sources.find(s => s.n === n) : null;
const prevItems  = n => previous ? previous.items.filter(i => i.source === n) : [];

const results = await Promise.all(SOURCES.map(async src => ({ src, ...(await fetchOne(src)) })));

const sources = [];
let all = [];
for (const r of results) {
  if (r.ok) {
    sources.push({ n: r.src.n, ok: true, stale: false, count: r.items.length, dropped: r.dropped, fetchedAt: NOW.toISOString() });
    all.push(...r.items);
  } else {
    const kept = prevItems(r.src.n);
    const ps = prevSource(r.src.n);
    sources.push({ n: r.src.n, ok: false, stale: kept.length > 0, count: kept.length, error: r.error, fetchedAt: kept.length && ps ? ps.fetchedAt : "" });
    all.push(...kept);
  }
}

/* the same story once: by link, then by title; the higher-weighted source keeps it */
all.sort((a, b) => (b.weight || 1) - (a.weight || 1) || Date.parse(b.date) - Date.parse(a.date));
const seenLink = new Set(), seenTitle = new Set();
let duplicates = 0;
const items = all.filter(it => {
  const l = normLink(it.link), t = normTitle(it.title);
  if (seenLink.has(l) || (t && seenTitle.has(t))) { duplicates++; return false; }
  seenLink.add(l); if (t) seenTitle.add(t);
  return true;
}).sort((a, b) => Date.parse(b.date) - Date.parse(a.date));

const edition = { schema: 1, fetched: NOW.toISOString(), duplicates, sources, items };
fs.mkdirSync(path.dirname(OUT), { recursive: true });
fs.writeFileSync(OUT, JSON.stringify(edition));

const okN = sources.filter(s => s.ok).length, staleN = sources.filter(s => s.stale).length, downN = sources.filter(s => !s.ok && !s.stale).length;
for (const s of sources) {
  const d = s.dropped && Object.keys(s.dropped).length ? "  dropped " + Object.entries(s.dropped).map(([k, v]) => v + " (" + k + ")").join(", ") : "";
  console.log((s.ok ? "  ok     " : s.stale ? "  stale  " : "  down   ") + s.n.padEnd(24) + String(s.count).padStart(3) + " items" + d + (s.error ? "  — " + s.error : ""));
}
console.log("fetch_feeds: " + items.length + " items from " + okN + " sources answering, " + staleN + " kept from an earlier gathering, " + downN + " unavailable, " + duplicates + " duplicates removed → " + path.relative(ROOT, OUT) + " (gathered " + edition.fetched + ")");
