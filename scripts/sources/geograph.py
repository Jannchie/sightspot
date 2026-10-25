"""Geograph（英国与爱尔兰）：展示廊投过票的照片里、标了拍摄位置、并且已转存到 Wikimedia Commons 的。

Geograph 不允许直接引用它服务器上的图片，但 Commons 上有大批 Geograph 照片的转存（文件名带
"geograph.org.uk - 编号"），图片用 Commons 的；坐标取 Geograph 记录的摄影者位置（viewpoint）和朝向。
数据来自 https://data.geograph.org.uk/dumps/ 的 tsv（CC BY-SA 2.0），放在 --raw 目录：
  gridimage_base.tsv.gz  gridimage_geo.tsv.gz  gridimage_size.tsv.gz  gallery_ids.tsv.gz
  commons_titles.txt     Commons 全部文件名里带 geograph 编号的（titles.sh 从 Commons 的 all-titles 转储里筛）

  python -X utf8 -u scripts/sources/geograph.py --raw raw/geograph --out out/geograph.jsonl
"""

import argparse
import gzip
import math
import re
import sys
import time
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import Writer, get_json, record  # noqa: E402

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
MIN_GRLEN = 8  # 摄影者位置至少 8 位网格坐标（100 m）
# 各网格的中央经线：英国国家网格 -2°，爱尔兰网格 -8°（网格北与真北的夹角按它算）
CENTRAL = {"1": -2.0, "2": -8.0}


def tsv(path):
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
        head = f.readline().rstrip("\n").split("\t")
        for line in f:
            yield dict(zip(head, line.rstrip("\n").split("\t")))


def viewpoint(lat, lng, de, dn, ref):
    """主体的经纬度 + 网格上主体到摄影者的位移（米）→ 摄影者的经纬度。位移通常在几公里内，按局部平面算，
    先把网格方向转到真北（子午线收敛角 ≈ (λ - λ0)·sin φ）"""
    g = math.radians(lng - CENTRAL[ref]) * math.sin(math.radians(lat))
    e = de * math.cos(g) - dn * math.sin(g)
    n = de * math.sin(g) + dn * math.cos(g)
    return lat + n / 111_320, lng + e / (111_320 * math.cos(math.radians(lat)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    raw = Path(a.raw)

    titles = {}
    for line in open(raw / "commons_titles.txt", encoding="utf-8", errors="replace"):
        t = line.rstrip("\n").split("\t", 1)[-1]
        m = re.search(r"geograph\.org\.uk_-_(\d+)", t)
        if m and re.search(r"\.jpe?g$", t, re.I):
            titles.setdefault(int(m[1]), t)
    votes = {int(r["id"]): float(r["baysian"] or 0) for r in tsv(raw / "gallery_ids.tsv.gz")}
    want = {i for i in votes if i in titles}
    print(f"commons {len(titles):,}, voted {len(votes):,}, both {len(want):,}", flush=True)

    geo = {}
    for r in tsv(raw / "gridimage_geo.tsv.gz"):
        i = int(r["gridimage_id"])
        if i in want and int(r["viewpoint_grlen"] or 0) >= MIN_GRLEN and int(r["natgrlen"] or 0) >= 6:
            geo[i] = r
    base = {int(r["gridimage_id"]): r for r in tsv(raw / "gridimage_base.tsv.gz") if int(r["gridimage_id"]) in geo}
    print(f"with viewpoint {len(geo):,}", flush=True)

    w = Writer(Path(a.out))
    todo = [i for i in sorted(geo, key=lambda i: -votes[i]) if str(i) not in w.seen and i in base]
    # Commons 上的实际尺寸与缩略图地址：每次 50 个文件
    for k in range(0, len(todo), 50):
        batch = todo[k:k + 50]
        q = {"action": "query", "format": "json", "formatversion": 2, "prop": "imageinfo", "iiprop": "url|size",
             "iiurlwidth": 500, "titles": "|".join("File:" + titles[i].replace("_", " ") for i in batch)}
        pages = {p["title"]: p for p in get_json(f"{COMMONS_API}?{urllib.parse.urlencode(q)}")["query"]["pages"]}
        for i in batch:
            p = pages.get("File:" + titles[i].replace("_", " "))
            info = (p or {}).get("imageinfo")
            if not info:
                continue
            info = info[0]
            b, g = base[i], geo[i]
            lat, lng = viewpoint(float(b["wgs84_lat"]), float(b["wgs84_long"]),
                                 int(g["viewpoint_eastings"]) - int(g["nateastings"]),
                                 int(g["viewpoint_northings"]) - int(g["natnorthings"]), b["reference_index"])
            url = info["url"].split("?", 1)[0]  # 去掉接口附加的 utm 参数
            small = (info.get("thumburl") or url).split("?", 1)[0]
            large = small.replace("/500px-", "/1280px-") if info["width"] > 1280 and "/500px-" in small else url
            d = int(g["view_direction"])
            w.add(record(src="geograph", id=str(i), lng=round(lng, 6), lat=round(lat, 6), title=b["title"],
                         page=f"https://www.geograph.org.uk/photo/{i}", w=info["width"], h=info["height"],
                         small=small, large=large, artist=b["realname"], license="CC BY-SA 2.0",
                         licenseUrl="https://creativecommons.org/licenses/by-sa/2.0/",
                         taken=b["imagetaken"] if not b["imagetaken"].endswith("-00") else None,
                         heading=d % 360 if d >= 0 else None, score=votes[i]))
        w.flush()
        if k % 2500 == 0:
            print(f"{k:,}/{len(todo):,} total {len(w.seen):,}", flush=True)
        time.sleep(0.2)
    print(f"done: {len(w.seen):,} photos -> {a.out}")


if __name__ == "__main__":
    main()
