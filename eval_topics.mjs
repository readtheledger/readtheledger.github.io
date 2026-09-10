#!/usr/bin/env node
/* The Ledger — evaluates the topic classifier against a labelled sample.

   Reads docs/package-1/topic-sample.json (headline prefixes with the placement
   an editor expects, and any other placement that is defensible), finds each
   story in a gathered edition so the classifier sees the same excerpt the app
   would, classifies it the way fetch_feeds.mjs does, and prints a table of
   expected against actual with the confidence and reason, then the score.

     node eval_topics.mjs --edition data/feed.json [--sample docs/package-1/topic-sample.json] [--md out.md]

   Exit status 0 when at least 90% of the sample is placed appropriately
   (expected or an accepted alternative), 1 otherwise. */
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const argv = process.argv.slice(2);
const opt = (n, d) => { const i = argv.indexOf("--" + n); return i >= 0 ? argv[i + 1] : d; };
const SAMPLE = opt("sample", path.join(ROOT, "docs", "package-1", "topic-sample.json"));
const EDITION = opt("edition", path.join(ROOT, "data", "feed.json"));
const MD = opt("md", "");
const TARGET = Number(opt("target", "0.9"));

const ctx = { window: {} };
vm.runInNewContext(fs.readFileSync(path.join(ROOT, "sources.js"), "utf8"), ctx);
vm.runInNewContext(fs.readFileSync(path.join(ROOT, "topics.js"), "utf8"), ctx);
const SOURCES = ctx.window.LEDGER_SOURCES, T = ctx.window.LEDGER_TOPICS;
const srcOf = n => SOURCES.find(s => s.n === n) || {};
const sample = JSON.parse(fs.readFileSync(SAMPLE, "utf8")).sample;
const edition = fs.existsSync(EDITION) ? JSON.parse(fs.readFileSync(EDITION, "utf8")) : { items: [] };
const norm = s => String(s || "").toLowerCase().replace(/[’‘]/g, "'").replace(/[“”]/g, '"').replace(/\s+/g, " ").trim();
const label = s => s || "General";

const rows = []; let ok = 0, exact = 0, missing = 0;
for (const s of sample) {
  const it = edition.items.find(i => i.source === s.source && norm(i.title).startsWith(norm(s.title))) || null;
  if (!it) missing++;
  const src = srcOf(s.source);
  const r = T.classify({ title: it ? it.title : s.title, html: it ? it.html : "", hint: src.s || "", fixed: !!src.fixed });
  const got = label(r.section), want = label(s.expected);
  const accepted = got === want || (s.accept || []).map(label).includes(got);
  if (accepted) ok++; if (got === want) exact++;
  rows.push({ source: s.source, title: (it ? it.title : s.title), want, accept: (s.accept || []).join(" / "), got, conf: r.confidence, pass: accepted, found: !!it, reason: r.reason });
}
const n = sample.length, rate = ok / n;
const line = `${ok}/${n} placed appropriately (${(rate * 100).toFixed(1)}%), ${exact} exactly as expected, ${n - ok} outside the accepted placements, ${missing} not found in the edition (classified on the headline alone)`;

const pad = (s, w) => String(s).padEnd(w).slice(0, w);
console.log(pad("source", 20) + pad("expected", 17) + pad("got", 17) + pad("conf", 9) + "ok  title");
for (const r of rows) console.log(pad(r.source, 20) + pad(r.want, 17) + pad(r.got, 17) + pad(r.conf, 9) + (r.pass ? "ok  " : "XX  ") + r.title.slice(0, 70));
console.log("\n" + line);

if (MD) {
  const esc = s => String(s).replace(/\|/g, "\\|");
  const md = ["# Topic classification — evaluation", "",
    `Edition: \`${path.relative(ROOT, EDITION)}\` (gathered ${edition.fetched || "n/a"}). Sample: \`${path.relative(ROOT, SAMPLE)}\`, ${n} stories from ${new Set(sample.map(s => s.source)).size} publishers.`, "",
    "**Result: " + line + ".**", "",
    "Labels in the sample were assigned by the implementing agent (agent-reviewed), not by a human editor. \"Accepted\" lists other placements judged defensible for an ambiguous story; a story counts as appropriately placed when the classifier's verdict is the expected placement or one of the accepted ones. \"General\" means the story stays in the Newsstand under no topic tab.", "",
    "| Source | Headline | Expected | Also accepted | Got | Confidence | OK |", "|---|---|---|---|---|---|---|",
    ...rows.map(r => `| ${esc(r.source)} | ${esc(r.title.slice(0, 90))} | ${r.want} | ${esc(r.accept)} | ${r.got} | ${r.conf} | ${r.pass ? "✓" : "✗"} |`),
    "", "## Misplacements and ambiguities", "",
    ...rows.filter(r => !r.pass).map(r => `- **${esc(r.title.slice(0, 90))}** (${esc(r.source)}): expected ${r.want}${r.accept ? " or " + esc(r.accept) : ""}, got ${r.got} (${r.conf}) — ${esc(r.reason)}`),
    ...(rows.filter(r => !r.pass).length ? [] : ["- none outside the accepted placements"]),
    "", "Stories classified on the headline alone because they were not found in the edition: " + rows.filter(r => !r.found).length + ".", ""];
  fs.writeFileSync(MD, md.join("\n"));
  console.log("wrote " + MD);
}
process.exit(rate >= TARGET ? 0 : 1);
