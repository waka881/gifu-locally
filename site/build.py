"""Markdown記事 → 静的サイト（GitHub Pages / Cloudflare Pages 用）。

python3 site/build.py            # status: 公開 の記事だけ出力
python3 site/build.py --draft    # 下書きも含めて出力（確認用）
"""
import html
import pathlib
import re
import sys

import markdown

ROOT = pathlib.Path(__file__).resolve().parent.parent
ARTICLES = ROOT / "articles"
OUT = ROOT / "dist"
SITE_NAME = "Gifu, Locally"
TAGLINE = "Gifu, Japan, from people who live here."
DRAFT = "--draft" in sys.argv

TRAVELPAYOUTS = """<script nowprocket data-noptimize="1" data-cfasync="false" data-wpfc-render="false" seraph-accel-crit="1" data-no-defer="1" data-cmp-ab="2">
  (function () {
      var script = document.createElement("script");
      script.async = 1;
      script.setAttribute("data-cmp-ab","2");
      script.src = 'https://emrld.ltd/NTg1NTQ5.js?t=585549';
      document.head.appendChild(script);
  })();
</script>"""

CSS = """
:root{--bg:#fbfaf7;--fg:#222;--muted:#666;--accent:#a4472b;--line:#e6e2da}
@media (prefers-color-scheme:dark){:root{--bg:#161514;--fg:#eee;--muted:#aaa;--accent:#e08a6a;--line:#333}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);
font:17px/1.7 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
.wrap{max-width:720px;margin:0 auto;padding:0 16px}
header{border-bottom:1px solid var(--line);padding:18px 0}header a{color:var(--fg);text-decoration:none;font-weight:700}
header p{margin:2px 0 0;color:var(--muted);font-size:14px}
main{padding:24px 0 48px}a{color:var(--accent)}h1{line-height:1.3}
.card{display:block;border:1px solid var(--line);border-radius:10px;padding:16px;margin:12px 0;text-decoration:none;color:var(--fg)}
.card h2{margin:0 0 4px;font-size:20px}.card p{margin:0;color:var(--muted);font-size:15px}
.draft{background:#fff3c4;color:#222;padding:2px 6px;border-radius:4px;font-size:13px}
footer{border-top:1px solid var(--line);padding:18px 0;color:var(--muted);font-size:14px}
"""


def parse(path):
    text = path.read_text()
    meta, body = {}, text
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip().strip('"')
        body = text[m.end():]
    meta["slug"] = path.stem
    meta["is_public"] = meta.get("status") == "公開"
    meta["html"] = markdown.markdown(body, extensions=["extra"])
    return meta


def page(title, desc, content):
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><meta name="description" content="{html.escape(desc)}">
<style>{CSS}</style>{TRAVELPAYOUTS}</head><body>
<header><div class="wrap"><a href="index.html">{SITE_NAME}</a><p>{TAGLINE}</p></div></header>
<main class="wrap">{content}</main>
<footer><div class="wrap"><a href="about.html">About &amp; disclosure</a></div></footer>
</body></html>"""


def main():
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.html"):
        old.unlink()
    posts = [p for p in map(parse, sorted(ARTICLES.glob("*.md"))) if p["is_public"] or DRAFT]
    cards = []
    for p in posts:
        badge = "" if p["is_public"] else ' <span class="draft">draft</span>'
        (OUT / f"{p['slug']}.html").write_text(
            page(f"{p['title']} | {SITE_NAME}", p.get("description", ""),
                 f"<article><h1>{html.escape(p['title'])}{badge}</h1>{p['html']}</article>"))
        cards.append(f'<a class="card" href="{p["slug"]}.html"><h2>{html.escape(p["title"])}{badge}</h2>'
                     f'<p>{html.escape(p.get("description", ""))}</p></a>')
    (OUT / "index.html").write_text(page(SITE_NAME, TAGLINE, "<h1>Guides</h1>" + "".join(cards)))
    (OUT / "about.html").write_text(page(f"About | {SITE_NAME}", "About this site", """
<h1>About</h1><p>Gifu, Locally is a small travel guide to Gifu Prefecture, Japan, written from local knowledge.
Facts such as prices and opening hours come from official sources and carry the date we last checked them.</p>
<h2>Affiliate disclosure</h2><p>Some links on this site are affiliate links. If you book through them we may earn a
commission at no extra cost to you. We only link to things we think are useful for your trip.</p>"""))
    print(f"built {len(posts)} article(s) -> {OUT}")


if __name__ == "__main__":
    main()
