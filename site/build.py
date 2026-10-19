"""Markdown記事 → 静的サイト（GitHub Pages / Cloudflare Pages 用）。

python3 site/build.py            # status: 公開 の記事だけ出力
python3 site/build.py --draft    # 下書きも含めて出力（確認用）
"""
import html
import json
import pathlib
import re
import sys
import urllib.parse

import markdown

ROOT = pathlib.Path(__file__).resolve().parent.parent
ARTICLES = ROOT / "articles"
OUT = ROOT / "dist"
SITE_NAME = "Gifu Gourmand"
TAGLINE = "Eat and travel your way through Gifu, Japan."
DRAFT = "--draft" in sys.argv
BASE = "https://gifugourmand.com/"
INSTAGRAM = ""  # 例: "https://www.instagram.com/gifu_gourmand/"（決まったら入れる）

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
*{box-sizing:border-box}html,body{overflow-x:hidden}article{overflow-wrap:break-word}article table{display:block;overflow-x:auto}body{margin:0;background:var(--bg);color:var(--fg);
font:17px/1.7 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
.wrap{max-width:760px;margin:0 auto;padding:0 16px}
header{border-bottom:1px solid var(--line);padding:18px 0}header a{color:var(--fg);text-decoration:none;font-weight:700}
header p{margin:2px 0 0;color:var(--muted);font-size:14px}
main{padding:24px 0 48px}a{color:var(--accent)}h1{line-height:1.3}
.card{display:block;border:1px solid var(--line);border-radius:10px;padding:16px;margin:12px 0;text-decoration:none;color:var(--fg)}
.card h2{margin:0 0 4px;font-size:20px}.card p{margin:0;color:var(--muted);font-size:15px}
.tldr{border-left:4px solid var(--accent);background:rgba(164,71,43,.07);padding:12px 14px;margin:0 0 20px;border-radius:6px}
.checked{color:var(--muted);font-size:14px;margin:-8px 0 16px}
figure.hero{margin:0 0 20px}figure.hero img{width:100%;height:auto;max-height:420px;object-fit:cover;border-radius:10px;display:block}
figure.hero figcaption{font-size:12px;color:var(--muted);margin-top:4px}
.cta{display:flex;gap:14px;align-items:center;justify-content:space-between;border:2px solid var(--accent);border-radius:12px;padding:14px 16px;margin:20px 0;text-decoration:none;color:var(--fg)}
.cta strong{display:block;font-size:17px}.cta span.sub{display:block;color:var(--muted);font-size:14px}
.cta span.btn{flex:none;background:var(--accent);color:#fff;border-radius:8px;padding:9px 14px;font-weight:700;font-size:15px;white-space:nowrap}
@media (max-width:480px){.cta{flex-direction:column;align-items:stretch}.cta span.btn{text-align:center}}
.cta.top{margin-top:0}.disc{font-size:13px;color:var(--muted);margin-top:28px}
.sticky{display:none}
@media (max-width:720px){.sticky{display:flex;position:fixed;left:0;right:0;bottom:0;z-index:9;gap:10px;align-items:center;justify-content:space-between;
background:var(--bg);border-top:1px solid var(--line);padding:10px 16px;color:var(--fg);text-decoration:none;font-size:14px;font-weight:600;box-shadow:0 -4px 16px rgba(0,0,0,.08)}
.sticky span:first-child{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.sticky .btn{flex:none;background:var(--accent);color:#fff;border-radius:8px;padding:8px 12px}body{padding-bottom:64px}}
.intro{padding:8px 0 12px}.intro h1{font-size:30px;margin:0 0 8px}.intro p{color:var(--muted);margin:0 0 14px}
.pill{display:inline-block;background:var(--accent);color:#fff;text-decoration:none;border-radius:999px;padding:10px 16px;font-weight:700;font-size:15px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:4px 14px}.grid .card{margin:6px 0}
.card:hover,.cta:hover{box-shadow:0 4px 18px rgba(0,0,0,.08)}.cta span.btn{box-shadow:0 2px 0 rgba(0,0,0,.15)}
article h2{margin-top:2em;border-bottom:1px solid var(--line);padding-bottom:4px}article table{border-collapse:collapse;width:100%;font-size:15px}
article th,article td{border:1px solid var(--line);padding:6px 8px;text-align:left}
.insta{display:block;border:1px dashed var(--accent);border-radius:12px;padding:12px 16px;margin:24px 0;text-decoration:none;color:var(--fg)}
.insta strong{display:block}.insta span{color:var(--muted);font-size:14px}
.card img{width:100%;height:160px;object-fit:cover;border-radius:6px;margin-bottom:8px;display:block}
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
    meta["html"] = markdown.markdown(expand_cta(body), extensions=["extra"])
    meta["faq"] = parse_faq(body)
    return meta


CTA_RE = re.compile(r"^\[\[cta\|([^|\]]+)\|([^|\]]+)\|([^|\]]*)\|([^|\]]+)\]\]\s*$", re.M)


def expand_cta(body):
    """[[cta|URL|見出し|補足|ボタン文言]] を予約ボタン付きのカードに置き換える。"""
    def rep(m):
        url, title, sub, btn = (html.escape(x.strip()) for x in m.groups())
        return (f'<a class="cta" href="{url}" rel="sponsored noopener" target="_blank"><span><strong>{title}</strong>'
                f'<span class="sub">{sub}</span></span><span class="btn">{btn}</span></a>')
    return CTA_RE.sub(rep, body)


def cta_card(spec, cls="cta"):
    """frontmatter の cta: URL|見出し|補足|ボタン文言 からカードを作る。"""
    if not spec:
        return ""
    url, title, sub, btn = (html.escape(x.strip()) for x in (spec.split("|") + ["", "", ""])[:4])
    return (f'<a class="{cls}" href="{url}" rel="sponsored noopener" target="_blank"><span><strong>{title}</strong>'
            f'<span class="sub">{sub}</span></span><span class="btn">{btn or "Check availability"} →</span></a>')


def insta_card(url):
    if not url:
        return ""
    return (f'<a class="insta" href="{html.escape(url)}" rel="noopener" target="_blank"><strong>Watch it on Instagram</strong>'
            f'<span>Real footage from our visit, on @{html.escape(INSTAGRAM.rstrip("/").rsplit("/", 1)[-1]) if INSTAGRAM else SITE_NAME}</span></a>')


def sticky_bar(spec):
    if not spec:
        return ""
    url, title, _, btn = (html.escape(x.strip()) for x in (spec.split("|") + ["", "", ""])[:4])
    return (f'<a class="sticky" href="{url}" rel="sponsored noopener" target="_blank"><span>{title}</span>'
            f'<span class="btn">{btn or "Check availability"}</span></a>')


def image_url(meta, width=1200):
    f = meta.get("image", "")
    if f.startswith("img/"):  # 自前の写真（static/img/ に置く）
        return BASE + f
    return f"https://commons.wikimedia.org/wiki/Special:FilePath/{urllib.parse.quote(f.replace(' ', '_'))}?width={width}" if f else ""


def hero(meta):
    if not meta.get("image"):
        return ""
    if meta["image"].startswith("img/"):
        return (f'<figure class="hero"><img src="{image_url(meta)}" alt="{html.escape(meta.get("image_alt", ""))}" width="1200" height="675" fetchpriority="high">'
                f'<figcaption>Photo: {html.escape(meta.get("image_credit") or SITE_NAME)}</figcaption></figure>')
    page_url = "https://commons.wikimedia.org/wiki/File:" + urllib.parse.quote(meta["image"].replace(" ", "_"))
    lic = meta.get("image_license", "")
    m = re.match(r"CC (BY(?:-SA)?) ([0-9.]+)", lic)
    lic_url = (f"https://creativecommons.org/licenses/{m.group(1).lower()}/{m.group(2)}/" if m
               else "https://creativecommons.org/publicdomain/zero/1.0/" if lic == "CC0" else "")
    lic_html = f'<a href="{lic_url}" rel="noopener license">{html.escape(lic)}</a>' if lic_url else html.escape(lic)
    return (f'<figure class="hero"><img src="{image_url(meta)}" alt="{html.escape(meta.get("image_alt", ""))}" width="1200" height="675" fetchpriority="high">'
            f'<figcaption>Photo: {html.escape(meta.get("image_credit", ""))}, {lic_html}, '
            f'via <a href="{page_url}" rel="noopener">Wikimedia Commons</a></figcaption></figure>')


def parse_faq(body):
    """「## FAQ」節の「### 質問」＋本文を (質問, 回答テキスト) のリストにする（FAQPage構造化データ用）。"""
    m = re.search(r"^## (?:FAQ|Frequently asked questions)\s*$(.*?)(?=^## |^---\s*$|\Z)", body, re.S | re.M | re.I)
    if not m:
        return []
    out = []
    for q, a in re.findall(r"^### (.+?)\s*$(.*?)(?=^### |\Z)", m.group(1), re.S | re.M):
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", a)  # リンクは文字だけ残す
        text = re.sub(r"[*_`]", "", " ".join(text.split()))
        if text:
            out.append((q.strip(), text))
    return out


def page(title, desc, content, path="", jsonld="", img=""):
    url = BASE + path
    t, d = html.escape(title), html.escape(desc)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="p:domain_verify" content="0358eb35ecb74ece18718c935fcfb376"/>
<title>{t}</title><meta name="description" content="{d}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website"><meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:title" content="{t}"><meta property="og:description" content="{d}"><meta property="og:url" content="{url}">
<meta name="twitter:card" content="{'summary_large_image' if img else 'summary'}">{f'<meta property="og:image" content="{img}">' if img else ''}{jsonld}
<style>{CSS}</style>{TRAVELPAYOUTS}</head><body>
<header><div class="wrap"><a href="index.html">{SITE_NAME}</a><p>{TAGLINE}</p></div></header>
<main class="wrap">{content}</main>
<footer><div class="wrap"><a href="about.html">About &amp; disclosure</a>{f' · <a href="{INSTAGRAM}" rel="me noopener">Instagram</a>' if INSTAGRAM else ''}</div></footer>
</body></html>"""


ORG = {"@type": "Organization", "name": SITE_NAME, "alternateName": "岐阜グルマン", "url": BASE, **({"sameAs": [INSTAGRAM]} if INSTAGRAM else {})}


def main():
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.html"):
        old.unlink()
    posts = [p for p in map(parse, sorted(ARTICLES.glob("*.md"))) if p["is_public"] or DRAFT]
    cards = []
    for p in posts:
        badge = "" if p["is_public"] else ' <span class="draft">draft</span>'
        graph = [{"@type": "Article", "headline": p["title"], "description": p.get("description", ""),
                  "abstract": p.get("summary", ""), "image": image_url(p) or None, "inLanguage": "en", "dateModified": p.get("facts_checked", ""),
                  "mainEntityOfPage": f"{BASE}{p['slug']}.html",
                  "author": ORG,
                  "publisher": ORG}]
        graph[0] = {k: v for k, v in graph[0].items() if v}
        if p["faq"]:
            graph.append({"@type": "FAQPage", "mainEntity": [
                {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in p["faq"]]})
        ld = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False)
        top = (f'<p class="checked">Facts checked against official sources: {html.escape(p.get("facts_checked", ""))}</p>'
               + (f'<div class="tldr"><strong>Quick answer:</strong> {html.escape(p["summary"])}</div>' if p.get("summary") else ""))
        more = "".join(f'<li><a href="{q["slug"]}.html">{html.escape(q["title"])}</a></li>'
                       for q in posts if q is not p)
        (OUT / f"{p['slug']}.html").write_text(
            page(f"{p['title']} | {SITE_NAME}", p.get("description", ""),
                 f"<article><h1>{html.escape(p['title'])}{badge}</h1>{top}{hero(p)}{cta_card(p.get('cta'), 'cta top')}{p['html']}{insta_card(p.get('instagram'))}"
                 f"{('<h2>Ready to book?</h2>' + cta_card(p.get('cta'))) if p.get('cta') else ''}"
                 f'<p class="disc">We may earn a commission if you book through links on this page, at no extra cost to you. <a href="about.html">Disclosure</a></p></article>'
                 f"{sticky_bar(p.get('cta'))}"
                 f"<nav><h2>More Gifu guides</h2><ul>{more}</ul></nav>",
                 f"{p['slug']}.html", f'<script type="application/ld+json">{ld}</script>', image_url(p)))
        thumb = f'<img src="{image_url(p, 640)}" alt="" loading="lazy">' if p.get("image") else ""
        cards.append(f'<a class="card" href="{p["slug"]}.html">{thumb}<h2>{html.escape(p["title"])}{badge}</h2>'
                     f'<p>{html.escape(p.get("description", ""))}</p></a>')
    order = ["nagoya-day-trips", "shirakawa-go-from-nagoya", "takayama-from-nagoya", "gero-onsen-guide", "gujo-hachiman-day-trip", "gifu-winter-guide"]
    rank = {s: i for i, s in enumerate(order)}
    cards = [c for _, c in sorted(zip(posts, cards), key=lambda pc: rank.get(pc[0]["slug"], 99))]
    intro = ('<section class="intro"><h1>Eat, explore and stay in Gifu, Japan</h1>'
             '<p>Shirakawa-go, Takayama, Gero Onsen and Gujo Hachiman are all reachable from Nagoya. '
             'Each guide gives you the route, the costs and the booking options, checked against official sources.</p>'
             '<a class="pill" href="nagoya-day-trips.html">Start here: which Gifu day trip from Nagoya? →</a></section>')
    (OUT / "index.html").write_text(page(SITE_NAME, "English travel guides to Gifu, Japan: day trips from Nagoya, Gifu City, Seki, Gujo Hachiman and more, with prices checked against official sources.", intro + '<h2>Guides</h2><div class="grid">' + "".join(cards) + "</div>"))
    (OUT / "about.html").write_text(page(f"About | {SITE_NAME}", "About this site", """
<h1>About</h1><p>Gifu Gourmand is a food-led travel guide to Gifu Prefecture, Japan: what to eat, where to go and how to get there, from Nagoya day trips to onsen stays.
Facts such as prices and opening hours come from official sources and carry the date we last checked them.</p>
<h2>Affiliate disclosure</h2><p>Some links on this site are affiliate links. If you book through them we may earn a
commission at no extra cost to you. We only link to things we think are useful for your trip.</p>""", "about.html"))
    # インスタのプロフィール用の入口ページ（サイトマップには載せない）
    feat = ["shirakawa-go-light-up", "shirakawa-go-from-nagoya", "takayama-from-nagoya", "where-to-stay-takayama", "gero-onsen-guide", "japan-esim-gifu", "nagoya-day-trips"]
    bys = {p["slug"]: p for p in posts}
    links = "".join(f'<a class="card" href="{s}.html"><h2>{html.escape(bys[s]["title"])}</h2></a>' for s in feat if s in bys)
    (OUT / "links.html").write_text(page(f"Links | {SITE_NAME}", "Gifu Gourmand guides featured on Instagram.",
        '<section class="intro"><h1>Gifu Gourmand</h1><p>Eat and travel your way through Gifu, Japan. '
        'Routes, prices and booking options, checked against official sources.</p></section>'
        + links + '<a class="pill" href="index.html">All guides →</a>', "links.html").replace('<meta name="description"', '<meta name="robots" content="noindex"><meta name="description"', 1))
    urls = [BASE] + [f"{BASE}{p['slug']}.html" for p in posts]
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                                     + "".join(f"<url><loc>{u}</loc></url>" for u in urls) + "</urlset>\n")
    for f in (ROOT / "static").rglob("*"):  # IndexNow鍵ファイル・自前の写真など、そのまま配信するファイル
        if f.is_file() and f.name != ".keep":
            dest = OUT / f.relative_to(ROOT / "static")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(f.read_bytes())
    # AIアシスタント向けのサイト案内（llms.txt）
    (OUT / "llms.txt").write_text(f"# {SITE_NAME}\n\n> English travel guides to Gifu Prefecture, Japan, written for first-time visitors. "
        "Prices, hours and dates are checked against official sources, and each page shows the date it was last checked.\n\n## Guides\n\n"
        + "".join(f"- [{q['title']}]({BASE}{q['slug']}.html): {q.get('summary') or q.get('description', '')}\n" for q in posts))
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE}sitemap.xml\n")
    print(f"built {len(posts)} article(s) -> {OUT}")


if __name__ == "__main__":
    main()
