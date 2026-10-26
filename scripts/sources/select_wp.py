"""从被维基百科条目使用的 Commons 照片里挑出要收进网站的，追加到 members.jsonl（分类 "wp"），再由 commons_spots.py 取详情。

  1. 被 STRICT_WIKIS 个以上语言的维基百科使用、长边 ≥ STRICT_PX
  2. 点少的国家和地区（站上已有的 + 第 1 步的不到 TARGET 个）放宽到 RELAX_WIKIS 个语言、长边 ≥ RELAX_PX，
     按使用的语言数从多到少补到 TARGET 个
尺寸按需向 Commons API 查（每次 50 个）。

用法：select_wp.py out raw/commons-dumps/ne_50m_admin_0_countries.geojson site_ids.txt [--dry]
"""
import collections
import json
import sys
import urllib.parse
from pathlib import Path

import numpy as np
import shapely
from shapely import STRtree

sys.path.insert(0, str(Path(__file__).parent))
from common import get_json  # noqa: E402

STRICT_WIKIS, STRICT_PX = 10, 2000
RELAX_WIKIS, RELAX_PX = 3, 1280
TARGET = 2000
PHOTO = {"image/jpeg", "image/png", "image/webp", "image/tiff"}

OUT, NE, SITE = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
DRY = "--dry" in sys.argv

fc = json.load(open(NE))
geoms = [shapely.geometry.shape(f["geometry"]) for f in fc["features"]]
names = [f["properties"]["NAME_ZH"] or f["properties"]["NAME"] for f in fc["features"]]
tree = STRtree(geoms)


def countries(coords):
    """[(lng, lat)] → 国家名；落在海上的取 0.2° 内最近的国家，再远的是 None"""
    pts = shapely.points(np.array(coords))
    hit = np.full(len(coords), -1)
    pi, gi = tree.query(pts, predicate="within")
    hit[pi] = gi
    miss = np.where(hit < 0)[0]
    mi, mg = tree.query_nearest(pts[miss], max_distance=0.2)
    hit[miss[mi]] = mg
    return [names[h] if h >= 0 else None for h in hit]


site = set(int(x) for x in open(SITE).read().split())
site_pts = [(s["lon"], s["lat"]) for s in map(json.loads, open(OUT / "spots.jsonl", encoding="utf-8"))
            if s["pageid"] in site]
have = collections.Counter(countries(site_pts))
print(f"site: {len(site_pts):,}", flush=True)

used = [r for r in map(json.loads, open(OUT / "commons_used.jsonl")) if len(r["wikis"]) >= RELAX_WIKIS
        and r["pageid"] not in site]
for r, c in zip(used, countries([(r["lng"], r["lat"]) for r in used])):
    r["country"] = c
print(f"candidates (>= {RELAX_WIKIS} wikis, not on site): {len(used):,}", flush=True)

sizes = {}
for r in map(json.loads, open(OUT / "commons_used_sizes.jsonl")):
    sizes[r["pageid"]] = (r["w"], r["h"], r["mime"])


def fetch_sizes(ids):
    ids = [i for i in ids if i not in sizes]
    for k in range(0, len(ids), 50):
        q = {"action": "query", "format": "json", "formatversion": 2, "prop": "imageinfo", "iiprop": "size|mime",
             "pageids": "|".join(map(str, ids[k:k + 50]))}
        for p in get_json("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(q))["query"]["pages"]:
            info = (p.get("imageinfo") or [{}])[0]
            sizes[p["pageid"]] = (info.get("width"), info.get("height"), info.get("mime"))


def ok(r, px):
    w, h, mime = sizes.get(r["pageid"], (None, None, None))
    return mime in PHOTO and max(w or 0, h or 0) >= px


picked = {r["pageid"]: r for r in used if len(r["wikis"]) >= STRICT_WIKIS and ok(r, STRICT_PX)}
print(f"strict: {len(picked):,}", flush=True)
total = have + collections.Counter(r["country"] for r in picked.values())

by_country = collections.defaultdict(list)
for r in used:
    if r["country"] and r["pageid"] not in picked:
        by_country[r["country"]].append(r)
relaxed = collections.Counter()
for c, rows in sorted(by_country.items(), key=lambda kv: total[kv[0]]):
    need = TARGET - total[c]
    if need <= 0:
        continue
    rows.sort(key=lambda r: len(r["wikis"]), reverse=True)
    for k in range(0, len(rows), 500):
        if relaxed[c] >= need:
            break
        chunk = rows[k:k + 500]
        fetch_sizes([r["pageid"] for r in chunk])
        for r in chunk:
            if relaxed[c] < need and ok(r, RELAX_PX):
                picked[r["pageid"]] = r
                relaxed[c] += 1
print(f"relaxed: {sum(relaxed.values()):,} in {len(relaxed)} countries", flush=True)

final = have + collections.Counter(r["country"] for r in picked.values())
print(f"\npicked: {len(picked):,}\n{'国家/地区':　<10} 站上  新收（其中放宽）  合计")
for c in sorted(set(final), key=lambda c: -final[c])[:40] + ["中华人民共和国", "日本", "中华民国", "香港", "大韩民国",
                                                             "朝鲜", "蒙古", "越南", "泰国", "新加坡", "澳门"]:
    new = final[c] - have[c]
    print(f"{str(c):　<10} {have[c]:7,} {new:7,} ({relaxed[c]:,}) {final[c]:7,}")
top_relaxed = relaxed.most_common(25)
print("\n放宽补得最多的：", ", ".join(f"{c} {n:,}" for c, n in top_relaxed))

if not DRY:
    have_wp = {json.loads(l)["pageid"] for l in open(OUT / "members.jsonl", encoding="utf-8") if '"wp"' in l}
    with open(OUT / "members.jsonl", "a", encoding="utf-8") as f:
        for p, r in picked.items():
            if p not in have_wp:
                f.write(json.dumps({"pageid": p, "title": None, "cat": "wp", "lat": r["lat"], "lon": r["lng"]}) + "\n")
    print(f"appended to members.jsonl")
