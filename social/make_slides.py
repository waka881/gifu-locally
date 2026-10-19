"""インスタ用カルーセル（1080x1350）のHTMLを作る。Actionsでスクリーンショットにする。"""
import html, json, pathlib, sys

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=block');
*{box-sizing:border-box;margin:0}html,body{width:1080px;height:1350px}
body{font-family:Inter,sans-serif;background:#fbfaf7;color:#222;position:relative;overflow:hidden}
.pad{position:absolute;inset:0;padding:96px 88px 140px;display:flex;flex-direction:column;justify-content:center}
.kicker{color:#a4472b;font-weight:800;font-size:34px;letter-spacing:.04em;text-transform:uppercase}
h1{font-size:92px;line-height:1.05;font-weight:800;margin-top:28px}
h2{font-size:84px;line-height:1.08;font-weight:800;margin-top:24px}
p,li{font-size:46px;line-height:1.4;margin-top:28px}ul{padding-left:44px}
.big{font-size:64px;font-weight:800;line-height:1.25;margin-top:36px}
.foot{position:absolute;left:88px;right:88px;bottom:56px;font-size:24px;color:#777;display:flex;justify-content:space-between}
.brand{font-weight:800;color:#a4472b}
.cover{background:#111 center/cover no-repeat;color:#fff}
.cover .shade{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.15) 30%,rgba(0,0,0,.8))}
.cover .pad{justify-content:flex-end}.cover .kicker{color:#f2b38f}.cover .foot{color:#ddd}
.cta{background:#a4472b;color:#fff}.cta .kicker{color:#ffd9c4}.cta .foot{color:#ffd9c4}.cta .brand{color:#fff}
.btn{display:inline-block;background:#fff;color:#a4472b;font-weight:800;font-size:46px;padding:22px 34px;border-radius:18px;margin-top:48px;align-self:flex-start}
"""

def slide(i, n, body, cls="", style="", foot=""):
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head>'
            f'<body class="{cls}" style="{style}"><div class="shade"></div><div class="pad">{body}</div>'
            f'<div class="foot"><span class="brand">Gifu Gourmand</span><span>{foot}</span><span>{i}/{n}</span></div></body></html>')

def main(spec_path):
    spec = json.loads(pathlib.Path(spec_path).read_text())
    out = pathlib.Path(spec_path).parent
    n = len(spec["slides"])
    for i, s in enumerate(spec["slides"], 1):
        style = f"background-image:url('{s['photo']}')" if s.get("photo") else ""
        (out / f"slide{i}.html").write_text(slide(i, n, s["html"], s.get("cls", ""), style, s.get("foot", spec.get("foot", ""))))

if __name__ == "__main__":
    main(sys.argv[1])
