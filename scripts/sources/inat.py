"""iNaturalist：收藏最多的观察记录（每条取第一张自由许可的照片），坐标是观察地点。

接口按收藏数排序，单个查询最多翻到第 10000 条：把世界切成格子分别查，
格子里收藏数 ≥ MIN_FAVES 的超过 10000 条就再切成四块。已完成的格子记在 state 文件里，中断后重跑接着来。
照片在 AWS 开放数据（inaturalist-open-data）上，直接引用。

  python -X utf8 -u scripts/sources/inat.py --out out/inat.jsonl [--min-faves 3]
"""

import argparse
import json
import sys
import time
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import LICENSES, Writer, get_json, record  # noqa: E402

API = "https://api.inaturalist.org/v1/observations"
PER_PAGE = 200
MAX_RESULTS = 10000
ALLOWED = ("cc0", "cc-by", "cc-by-sa", "cc-by-nc", "cc-by-nc-sa")
PAUSE = 1.0  # 官方建议每秒不超过 1 次


def query(tile, page, locale):
    w, s, e, n = tile
    q = {"photo_license": ",".join(ALLOWED), "geoprivacy": "open", "acc_below": 100, "photos": "true",
         "order_by": "votes", "order": "desc", "per_page": PER_PAGE, "page": page, "locale": locale,
         "swlng": w, "swlat": s, "nelng": e, "nelat": n}
    time.sleep(PAUSE)
    return get_json(f"{API}?{urllib.parse.urlencode(q)}")


def to_record(o, zh_names):
    photo = next((p for p in o["photos"] if p.get("license_code") in ALLOWED), None)
    if not photo or not o.get("location"):
        return None
    lat, lng = map(float, o["location"].split(","))
    t = o.get("taxon") or {}
    sci = t.get("name")
    en = t.get("english_common_name") or t.get("preferred_common_name")
    zh = zh_names.get(o["id"])
    title = en or sci or o.get("species_guess") or "iNaturalist observation"
    desc = {}
    if zh and sci:
        desc["zh-Hans"] = f"{zh}（{sci}）"
    if en and sci:
        desc["en"] = f"{en} ({sci})"
    note = (o.get("description") or "").strip()
    if note:
        desc["_"] = note[:400]
    place = o.get("place_guess")
    if place:
        for k in ("zh-Hans", "en"):
            if k in desc:
                desc[k] += f" · {place}"
    lic = LICENSES[photo["license_code"]]
    dims = photo.get("original_dimensions") or {}
    base = photo["url"].rsplit("/", 1)
    ext = base[1].split(".", 1)[1]
    u = o["user"]
    return record(src="inat", id=str(o["id"]), lng=lng, lat=lat, title=title, desc=desc or None, page=o["uri"],
                  w=dims.get("width"), h=dims.get("height"),
                  small=f"{base[0]}/medium.{ext}", large=f"{base[0]}/large.{ext}",
                  artist=u.get("name") or u.get("login"), license=lic[0], licenseUrl=lic[1],
                  taken=o.get("observed_on"), score=o.get("faves_count") or 0)


def crawl(tile, w: Writer, min_faves, done):
    key = ",".join(f"{v:g}" for v in tile)
    if key in done:
        return
    rows = []
    d = query(tile, 1, "en")
    # 先看能翻到的最后一页：那里的收藏数还不低于门槛，说明翻完也收不全，直接细分
    last = MAX_RESULTS // PER_PAGE
    capped = d["total_results"] > MAX_RESULTS and any(
        o["faves_count"] >= min_faves for o in query(tile, last, "en")["results"][-1:])
    page = 1
    while not capped:
        batch = d["results"]
        rows += [o for o in batch if o["faves_count"] >= min_faves]
        if not batch or batch[-1]["faves_count"] < min_faves or page * PER_PAGE >= min(d["total_results"], MAX_RESULTS):
            break
        page += 1
        d = query(tile, page, "en")
    if capped:
        x, y = (tile[0] + tile[2]) / 2, (tile[1] + tile[3]) / 2
        for sub in ((tile[0], tile[1], x, y), (x, tile[1], tile[2], y), (tile[0], y, x, tile[3]), (x, y, tile[2], tile[3])):
            crawl(sub, w, min_faves, done)
    else:
        # 中文名：同一批再按中文请求一遍（只要名字），只请求有结果的页数
        zh = {}
        for p in range(1, (len(rows) + PER_PAGE - 1) // PER_PAGE + 1):
            for o in query(tile, p, "zh-CN")["results"]:
                t = o.get("taxon") or {}
                if t.get("preferred_common_name") and t.get("preferred_common_name") != t.get("english_common_name"):
                    zh[o["id"]] = t["preferred_common_name"]
        n = sum(w.add(r) for o in rows if (r := to_record(o, zh)))
        w.flush()
        print(f"tile {key}: {len(rows)} obs, {n} new, total {len(w.seen):,}", flush=True)
    done.add(key)
    w.state.write_text(json.dumps(sorted(done)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--min-faves", type=int, default=3)
    a = ap.parse_args()
    out = Path(a.out)
    w = Writer(out)
    w.state = out.with_suffix(".state.json")
    done = set(json.loads(w.state.read_text())) if w.state.exists() else set()
    for lng in range(-180, 180, 30):
        for lat in range(-90, 90, 30):
            crawl((lng, lat, lng + 30, lat + 30), w, a.min_faves, done)
    print(f"done: {len(w.seen):,} photos -> {out}")


if __name__ == "__main__":
    main()
