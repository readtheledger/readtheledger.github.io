"""Fourth QA pass: the gatherer. Serves a handful of synthetic feeds — RSS and
Atom, CDATA and escaped markup, a wire-credited story, a future date, a missing
link, a duplicate carried by two desks, a feed that answers 500 and one that
never answers — and runs fetch_feeds.mjs against them with a previous edition
to fall back on. Checks the file it writes: what was kept, what was dropped and
why, what was marked stale and how old it says it is, that a summary source
ships an excerpt and a word count but never the article, that a licensed
source ships its markup, that the same story is carried once, that a wire story
keeps its origin, and that a source with no recorded rights stops the run."""
import http.server, socketserver, threading, os, sys, json, subprocess, tempfile, time

ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = 8934
NOW = "2026-09-08T03:00:00Z"
WORK = tempfile.mkdtemp(prefix="ledger-feed-")

LONG = " ".join(f"Sentence number {i} of a long report on rates, earnings and consumer spending, written at some length." for i in range(1, 40))
FUTURE = "Thu, 11 Sep 2026 09:00:00 GMT"

RSS_A = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:content="http://purl.org/rss/1.0/modules/content/">
<channel><title>Wire Desk</title>
<item><title><![CDATA[Stocks rally as inflation cools &amp; yields fall]]></title><link>https://example.com/a1</link>
  <pubDate>Mon, 07 Sep 2026 14:00:00 GMT</pubDate><dc:creator>Ann Writer</dc:creator>
  <description><![CDATA[<p>Stocks rallied on Monday after inflation data came in below forecasts.</p><p>{LONG}</p><script>alert(1)</script>]]></description></item>
<item><title>Bond yields slip after the auction</title><link>https://example.com/a2?utm_source=rss&amp;id=7</link>
  <pubDate>Mon, 07 Sep 2026 12:00:00 GMT</pubDate><description>Yields slipped after a well-bid auction. {LONG}</description></item>
<item><title>A story from the future</title><link>https://example.com/a3</link><pubDate>{FUTURE}</pubDate><description>Not yet.</description></item>
<item><title>A story with no link</title><pubDate>Mon, 07 Sep 2026 11:00:00 GMT</pubDate><description>Nowhere to go.</description></item>
<item><title></title><link>https://example.com/a5</link><pubDate>Mon, 07 Sep 2026 10:00:00 GMT</pubDate><description>Untitled.</description></item>
</channel></rss>"""

ATOM_B = f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"><title>Open Research</title>
<entry><title>How productivity statistics are revised</title>
  <link rel="alternate" type="text/html" href="https://example.org/b1"/><link rel="self" href="https://example.org/feed"/>
  <author><name>Dr Example</name></author><published>2026-09-07T09:30:00Z</published><updated>2026-09-07T10:00:00Z</updated>
  <content type="html">&lt;p&gt;Productivity statistics are revised for years after first publication.&lt;/p&gt;&lt;h2&gt;Why&lt;/h2&gt;&lt;p&gt;{LONG}&lt;/p&gt;</content></entry>
<entry><title>A shorter note</title><link href="https://example.org/b2"/><updated>2026-09-06T08:00:00Z</updated>
  <summary>Only a summary, and only an updated date.</summary></entry>
</feed>"""

RSS_C = f"""<?xml version="1.0"?>
<rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/"><channel><title>Second Desk</title>
<item><title>Stocks rally as inflation cools &amp; yields fall</title><link>https://example.com/second/1</link>
  <pubDate>Mon, 07 Sep 2026 14:10:00 GMT</pubDate><description>The same story, carried by a second desk. {LONG}</description></item>
<item><title>Oil climbs as supply worries return</title><link>https://example.com/second/2</link><dc:creator>Reuters</dc:creator>
  <pubDate>Mon, 07 Sep 2026 13:00:00 GMT</pubDate><description>LONDON (Reuters) - Oil prices climbed on Monday as supply worries returned. {LONG}</description></item>
<item><title>Bond yields slip after the auction, again</title><link>https://www.example.com/a2/?utm_campaign=x&amp;id=7</link>
  <pubDate>Mon, 07 Sep 2026 12:30:00 GMT</pubDate><description>Same link as the wire desk's story, different tracking.</description></item>
</channel></rss>"""

PREVIOUS = {
  "schema": 1, "fetched": "2026-09-07T20:00:00Z", "duplicates": 0,
  "sources": [{"n": "Broken Desk", "ok": True, "stale": False, "count": 1, "fetchedAt": "2026-09-07T20:00:00Z"}],
  "items": [{"id": "akept", "source": "Broken Desk", "origin": "Broken Desk", "title": "An opinion kept from last time",
             "link": "https://example.net/k1", "author": "K", "date": "2026-09-07T19:00:00Z", "html": "<p>kept</p>",
             "words": 50, "section": "Opinion", "kind": "analysis", "weight": 1, "lic": "", "rights": "summary"}]
}

def sources_js(entries):
    return "window.LEDGER_SOURCES = " + json.dumps(entries) + ";\n"

BASE = f"http://127.0.0.1:{PORT}"
GOOD = [
  {"n": "Wire Desk",     "u": BASE + "/rss-a.xml", "s": "Markets",   "q": 1.0, "k": "news",     "rights": "summary"},
  {"n": "Open Research", "u": BASE + "/atom-b.xml","s": "Economics", "q": 1.2, "k": "deep",     "rights": "full", "lic": "CC BY-ND 4.0"},
  {"n": "Second Desk",   "u": BASE + "/rss-c.xml", "s": "Companies", "q": 0.9, "k": "news",     "rights": "summary"},
  {"n": "Broken Desk",   "u": BASE + "/down",      "s": "Opinion",   "q": 1.0, "k": "analysis", "rights": "summary"},
  {"n": "Silent Desk",   "u": BASE + "/hang",      "s": "Opinion",   "q": 1.0, "k": "analysis", "rights": "summary"},
]

class Feeds(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        body, code, ctype = None, 200, "application/rss+xml; charset=utf-8"
        if self.path == "/rss-a.xml": body = RSS_A
        elif self.path == "/atom-b.xml": body = ATOM_B; ctype = "application/atom+xml; charset=utf-8"
        elif self.path == "/rss-c.xml": body = RSS_C
        elif self.path == "/down": body = "<h1>boom</h1>"; code = 500; ctype = "text/html"
        elif self.path == "/hang": time.sleep(4); body = RSS_A
        else: body = "no"; code = 404; ctype = "text/plain"
        data = body.encode("utf-8")
        try:
            self.send_response(code); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(data))); self.end_headers()
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass   # the gatherer gave up waiting, which is the point of /hang

def serve():
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("127.0.0.1", PORT), Feeds) as s: s.serve_forever()
threading.Thread(target=serve, daemon=True).start()

def run(sources, previous=None, timeout=1500):
    sf = os.path.join(WORK, "sources.js"); open(sf, "w").write(sources_js(sources))
    out = os.path.join(WORK, "out.json")
    if os.path.exists(out): os.remove(out)
    args = ["node", os.path.join(ROOT, "fetch_feeds.mjs"), "--sources", sf, "--out", out, "--now", NOW, "--timeout", str(timeout)]
    if previous is not None:
        pf = os.path.join(WORK, "previous.json"); json.dump(previous, open(pf, "w")); args += ["--previous", pf]
    else:
        args += ["--previous", os.path.join(WORK, "no-such-file.json")]
    r = subprocess.run(args, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr, (json.load(open(out)) if os.path.exists(out) else None)

results = []
def ok(name, cond, extra=""):
    results.append(("PASS" if cond else "FAIL", name, str(extra)))

# ---- the run everything else reads
code, log, ed = run(GOOD, PREVIOUS)
ok("gatherer exits 0 with sources down and silent", code == 0 and ed is not None, log.strip().splitlines()[-1] if log else "")
src = {s["n"]: s for s in ed["sources"]} if ed else {}
by_title = {i["title"]: i for i in ed["items"]} if ed else {}

ok("edition carries the time it was gathered", ed and ed["fetched"].replace(".000Z", "Z") == NOW, ed and ed["fetched"])

a = src.get("Wire Desk", {})
ok("RSS desk: kept the two good items, dropped the rest with reasons",
   a.get("ok") and a.get("count") == 2 and a.get("dropped") == {"date in the future": 1, "no absolute link": 1, "no title": 1}, a)
a1 = by_title.get("Stocks rally as inflation cools & yields fall")
ok("CDATA and entities decoded in the title", a1 is not None, list(by_title)[:4])
ok("summary source ships a plain-text excerpt, never the article",
   a1 and a1["rights"] == "summary" and a1["html"].startswith("<p>") and a1["html"].endswith("</p>")
   and "<" not in a1["html"][3:-4] and "script" not in a1["html"] and len(a1["html"]) <= 1520 and a1["words"] > 300,
   a1 and f"{len(a1['html'])} chars carried, {a1['words']} words counted")
ok("wire desk story keeps the desk as its origin", a1 and a1["origin"] == "Wire Desk", a1 and a1["origin"])
ok("dates are normalised to ISO and the excerpt keeps the byline",
   a1 and a1["date"] == "2026-09-07T14:00:00.000Z" and a1["author"] == "Ann Writer", a1 and (a1["date"], a1["author"]))

b = src.get("Open Research", {})
b1 = by_title.get("How productivity statistics are revised")
ok("Atom feed parsed: alternate link, author name, published date",
   b.get("ok") and b.get("count") == 2 and b1 and b1["link"] == "https://example.org/b1" and b1["author"] == "Dr Example"
   and b1["date"] == "2026-09-07T09:30:00.000Z", b1 and (b1.get("link"), b1.get("author"), b1.get("date")))
ok("licensed source ships its markup in full, with the licence",
   b1 and b1["rights"] == "full" and b1["lic"] == "CC BY-ND 4.0" and "<h2>" in b1["html"] and b1["words"] > 300, b1 and len(b1["html"]))
b2 = by_title.get("A shorter note")
ok("Atom entry with only an updated date still carries a date", b2 and b2["date"] == "2026-09-06T08:00:00.000Z", b2 and b2["date"])

c = src.get("Second Desk", {})
ok("second desk answered with three items", c.get("ok") and c.get("count") == 3, c)
ok("the same story is carried once: duplicate title and duplicate link removed",
   ed and ed["duplicates"] == 2 and "Bond yields slip after the auction, again" not in by_title
   and sum(1 for i in ed["items"] if i["title"].startswith("Stocks rally")) == 1
   and a1 and a1["source"] == "Wire Desk", ed and ed["duplicates"])
c2 = by_title.get("Oil climbs as supply worries return")
ok("a wire story credited to Reuters keeps Reuters as its origin, not the desk that carried it",
   c2 and c2["origin"] == "Reuters" and c2["source"] == "Second Desk", c2 and (c2.get("origin"), c2.get("source")))

d = src.get("Broken Desk", {})
ok("a feed answering 500 keeps its previous items, marked stale with their real time",
   d.get("ok") is False and d.get("stale") is True and d.get("count") == 1 and d.get("fetchedAt") == "2026-09-07T20:00:00Z"
   and "HTTP 500" in d.get("error", "") and "An opinion kept from last time" in by_title, d)
e = src.get("Silent Desk", {})
ok("a feed that never answers is unavailable, with nothing to keep",
   e.get("ok") is False and e.get("stale") is False and e.get("count") == 0 and "timed out" in e.get("error", ""), e)

dates = [i["date"] for i in ed["items"]] if ed else []
ok("items are newest first", dates == sorted(dates, reverse=True), dates[:3])
ok("every shipped item has an absolute link, a date and a title",
   ed and all(i["link"].startswith("http") and i["date"] and i["title"] for i in ed["items"]), ed and len(ed["items"]))

# ---- with no previous edition at all, a down feed is simply unavailable
code, log, ed2 = run(GOOD, previous=None)
d2 = {s["n"]: s for s in ed2["sources"]}["Broken Desk"] if ed2 else {}
ok("without a previous edition a down feed is unavailable, not stale", code == 0 and d2.get("stale") is False and d2.get("count") == 0, d2)

# ---- rights are enforced before anything is fetched
bad = [dict(GOOD[0]), dict(GOOD[1])]; del bad[0]["rights"]
code, log, _ = run(bad)
ok("a source with no recorded rights stops the run", code == 1 and "no recorded rights" in log, log.strip().splitlines()[-1] if log else "")
bad = [dict(GOOD[0]), dict(GOOD[1])]; del bad[1]["lic"]
code, log, _ = run(bad)
ok("rights \"full\" without a licence stops the run", code == 1 and "needs the licence" in log, log.strip().splitlines()[-1] if log else "")

# ---- the real sources file passes the same checks
r = subprocess.run(["node", "-e", 'const vm=require("vm"),fs=require("fs");const c={window:{}};vm.runInNewContext(fs.readFileSync(process.argv[1],"utf8"),c);const s=c.window.LEDGER_SOURCES;console.log(JSON.stringify({n:s.length, ok:s.every(x=>["summary","full"].includes(x.rights) && (x.rights!=="full"||x.lic))}))', os.path.join(ROOT, "sources.js")], capture_output=True, text=True)
real = json.loads(r.stdout or "{}")
ok("every real source records its rights, and full ones name a licence", real.get("ok") and real.get("n", 0) >= 20, real)

width = max(len(n) for _, n, _ in results)
fails = sum(1 for s, _, _ in results if s == "FAIL")
for s, n, e in results: print(f"{s}  {n.ljust(width)}  {e}")
print(f"\n{len(results)-fails}/{len(results)} gatherer checks passed")
sys.exit(1 if fails else 0)
