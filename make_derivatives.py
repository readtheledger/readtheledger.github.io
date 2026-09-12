#!/usr/bin/env python3
"""Web derivatives for an editorial image.

    python3 make_derivatives.py <master.png> <article-id> [--credit "..."] [--ai]

Reads a master (kept outside the repository; only its hash is recorded), writes
assets/editorial/<article-id>/hero-{480,768,1200}.webp and hero-1200.jpg, and
records provenance in assets/editorial/<article-id>/manifest.json: the master's
sha256, size and dimensions, the derivatives' sizes and bytes, and the date.
Never upscales: a width larger than the master is skipped. The 3:2 composition
is kept whole — no crop is made here, by policy (see docs/design/README.md).
Needs Pillow with WebP support."""
import sys, os, json, hashlib, datetime
from PIL import Image

WIDTHS = [480, 768, 1200]
ROOT = os.path.dirname(os.path.abspath(__file__))

def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("master"); ap.add_argument("article_id")
    ap.add_argument("--credit", default=""); ap.add_argument("--ai", action="store_true")
    a = ap.parse_args()
    master, aid, ai, credit = a.master, a.article_id, a.ai, a.credit
    raw = open(master, "rb").read()
    im = Image.open(master).convert("RGB")
    w, h = im.size
    out = os.path.join(ROOT, "assets", "editorial", aid)
    os.makedirs(out, exist_ok=True)
    files = []
    for tw in WIDTHS:
        if tw > w: print(f"skip {tw}px: master is {w}px wide"); continue
        th = round(h * tw / w)
        d = im.resize((tw, th), Image.LANCZOS)
        p = os.path.join(out, f"hero-{tw}.webp"); d.save(p, "WEBP", quality=82, method=6)
        files.append({"file": os.path.basename(p), "w": tw, "h": th, "bytes": os.path.getsize(p), "type": "image/webp"})
        if tw == 1200 or (tw == max(x for x in WIDTHS if x <= w)):
            pj = os.path.join(out, f"hero-{tw}.jpg"); d.save(pj, "JPEG", quality=84, optimize=True, progressive=True)
            files.append({"file": os.path.basename(pj), "w": tw, "h": th, "bytes": os.path.getsize(pj), "type": "image/jpeg"})
    manifest = {
        "articleId": aid,
        "master": {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "w": w, "h": h, "committed": False},
        "aiGenerated": ai, "credit": credit,
        "crop": "none — full 3:2 composition at every size",
        "derived": datetime.date.today().isoformat(),
        "files": files
    }
    json.dump(manifest, open(os.path.join(out, "manifest.json"), "w"), indent=2)
    for f in files: print(f"{aid}/{f['file']}: {f['w']}x{f['h']} {f['bytes']//1024} KB")

if __name__ == "__main__": main()
