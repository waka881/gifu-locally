"""Commonsで記事ごとの写真候補を探し、ライセンス情報つきで出力する（Actionsで実行）。"""
import json, re, urllib.parse, urllib.request
Q = {
    "osaka-kyoto-to-takayama": "Takayama Station Gifu",
    "tokyo-to-takayama": "HC85 Hida limited express",
    "monets-pond-from-nagoya": "Monet's Pond",
    "shirakawa-go-overnight-stay": "Shirakawa-go gassho minshuku",
    "hida-folk-village": "Hida Folk Village Takayama",
    "takayama-festival": "Takayama Festival yatai",
    "takayama-morning-market": "Miyagawa morning market Takayama",
    "is-gero-onsen-worth-visiting": "Gero Onsen Gifu",
    "hida-furukawa-or-takayama": "Hida Furukawa Seto river",
    "takayama-to-kanazawa-bus": "Kanazawa Station Tsuzumi gate",
 "shirakawa-go-light-up": "Shirakawa-go light up",
 "where-to-stay-takayama": "Takayama Miyagawa",
 "japan-esim-gifu": "Takayama station Gifu",
 "shirakawa-go-from-nagoya": "Shirakawa-go gassho village",
 "takayama-from-nagoya": "Takayama Sanmachi old town",
 "hida-beef-takayama": "Hida beef",
 "gero-onsen-guide": "Gero Onsen Hida River",
 "gujo-hachiman-day-trip": "Gujo Hachiman",
 "gifu-city-one-day": "Gifu Castle Mount Kinka",
 "gifu-winter-guide": "Shirakawa-go snow",
 "nagoya-day-trips": "Gifu Castle",
 "seki-knife-guide": "Seki Gifu sword",
 "mino-washi-day-trip": "Mino Udatsu",
 "magome-tsumago-walk": "Tsumago-juku",
 "where-to-stay-gifu-city": "Nagara River Gifu",
 "gifu-morning-service": "Japanese coffee morning set",
 "is-shirakawa-go-worth-visiting": "Shirakawa-go Ogimachi",
 "best-time-to-visit-shirakawa-go": "Shirakawa-go autumn",
 "gero-vs-okuhida-onsen": "Okuhida onsen rotenburo",
 "shinhotaka-ropeway": "Shinhotaka Ropeway",
 "takayama-in-winter": "Takayama snow winter",
 "kamikochi-from-takayama": "Kamikochi Kappa bridge",
 "takayama-gero-okuhida-ryokan": "Okuhida onsen rotenburo",
}
OK = re.compile(r"^(CC BY(-SA)? [0-9.]+|CC0|Public domain)", re.I)
UA = {"User-Agent": "gifu-locally-image-check/1.0 (https://gifugourmand.com/)"}
def api(params):
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({**params, "format": "json"})
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30))
def clean(s): return re.sub(r"<[^>]+>", "", s or "").strip()
import os
ONLY = set(filter(None, os.environ.get("ONLY", "").split(",")))
out = {}
for slug, q in Q.items():
    if ONLY and slug not in ONLY:
        continue
    d = api({"action": "query", "generator": "search", "gsrsearch": f"{q} filetype:bitmap", "gsrnamespace": 6, "gsrlimit": 20,
             "prop": "imageinfo", "iiprop": "extmetadata|size"})
    cands = []
    for p in sorted(d.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 99)):
        ii = (p.get("imageinfo") or [{}])[0]; m = ii.get("extmetadata", {})
        lic = clean(m.get("LicenseShortName", {}).get("value"))
        if not OK.match(lic) or ii.get("width", 0) < 1200 or ii.get("width", 0) < ii.get("height", 0):
            continue
        cands.append({"file": p["title"][5:], "license": lic, "artist": clean(m.get("Artist", {}).get("value"))[:80],
                      "desc": clean(m.get("ImageDescription", {}).get("value"))[:120], "w": ii["width"], "h": ii["height"]})
        if len(cands) == 5: break
    out[slug] = cands
print("CANDIDATES_JSON_START"); print(json.dumps(out, ensure_ascii=False, indent=1)); print("CANDIDATES_JSON_END")
