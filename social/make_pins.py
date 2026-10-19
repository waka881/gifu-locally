"""Pinterest用の縦長ピン（1000x1500）のHTMLと、一括アップロード用CSVを作る。Actionsで画像にする。"""
import csv, html, json, pathlib, re, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "social" / "pins"
BASE = "https://gifugourmand.com/"
RAW = "https://raw.githubusercontent.com/waka881/gifu-locally/main/social/pins/"

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=block');
*{box-sizing:border-box;margin:0}html,body{width:1000px;height:1500px}
body{font-family:Inter,sans-serif;background:#fbfaf7;color:#222;overflow:hidden}
.photo{height:760px;background:#111 center/cover no-repeat;position:relative}
.photo .credit{position:absolute;right:16px;bottom:12px;font-size:18px;color:#fff;background:rgba(0,0,0,.55);padding:4px 10px;border-radius:6px}
.tag{position:absolute;left:56px;top:56px;background:#a4472b;color:#fff;font-weight:800;font-size:30px;padding:12px 22px;border-radius:12px;letter-spacing:.03em}
.body{padding:48px 56px 0}
h1{font-size:76px;line-height:1.05;font-weight:800}
ul{margin-top:28px;padding-left:38px}li{font-size:36px;line-height:1.35;margin-top:12px}
.foot{position:absolute;left:0;right:0;bottom:0;height:120px;background:#a4472b;color:#fff;display:flex;align-items:center;justify-content:space-between;padding:0 56px;font-size:34px}
.foot b{font-weight:800}
"""

def lic_short(meta):
    return f"Photo: {meta['image_credit']}, {meta['image_license']}"

def front(slug):
    t = (ROOT / "articles" / f"{slug}.md").read_text()
    m = re.match(r"---\n(.*?)\n---", t, re.S)
    d = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            d[k.strip()] = v.strip().strip('"')
    return d

def main():
    pins = json.loads((OUT / "pins.json").read_text())
    rows = []
    for i, p in enumerate(pins, 1):
        meta = front(p["slug"])
        img = f"https://commons.wikimedia.org/wiki/Special:FilePath/{urllib.parse.quote(meta['image'].replace(' ', '_'))}?width=1400"
        lis = "".join(f"<li>{html.escape(b)}</li>" for b in p["bullets"])
        doc = (f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>'
               f'<div class="photo" style="background-image:url(\'{img}\')"><div class="tag">{html.escape(p["tag"])}</div>'
               f'<div class="credit">{html.escape(lic_short(meta))} (cropped)</div></div>'
               f'<div class="body"><h1>{html.escape(p["headline"])}</h1><ul>{lis}</ul></div>'
               f'<div class="foot"><b>Gifu Gourmand</b><span>Full guide · gifugourmand.com</span></div></body></html>')
        name = f"slide{i}"  # social.yml は slide*.html を描画する
        (OUT / f"{name}.html").write_text(doc)
        link = f"{BASE}{p['slug']}.html?utm_source=pinterest&utm_medium=social&utm_campaign=pins"
        rows.append({"Title": p["title"][:100], "Media URL": RAW + f"{name}.png", "Pinterest board": p["board"],
                     "Thumbnail": "", "Description": (p["description"] + " " + lic_short(meta) + ".")[:500],
                     "Link": link, "Publish date": "", "Keywords": p["keywords"]})
    with open(OUT / "pins.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)

if __name__ == "__main__":
    main()
