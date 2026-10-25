"""把 Commons 抓取结果（commons_spots.py 的 spots.jsonl、mirror.py 的 mirror.jsonl）导出成前端静态数据。

只收真实拍摄点：EXIF GPS 与页面坐标一致的照片。
  public/data/spots.geojson   全部机位的坐标（地图热力图与点），属性 i = Commons pageid，s = 详情分片，c = 所属精选集（位掩码）
  public/data/d/{s}.json      机位详情（含站点四种语言的描述，没有时留原文）。按空间四叉树分片（每片最多 SHARD_MAX 个），
                              视野里的机位多半落在同一两片里，浏览一片区域只需加载几个小文件

  python -I -X utf8 scripts/export_demo.py --src <commons_spots/out>
描述来自 spots.jsonl 的 description，早期抓的照片没有这个字段，用 commons_spots.py --descriptions 补到 descriptions.jsonl。
"""

import argparse
import json
import re
from pathlib import Path

SHARD_MAX = 200
DESC_MAX = 400
# Commons 的语言代码 → 站点的语言；其他语言只留一段原文（键 "_"），站点语言都没有时显示它
DESC_LANGS = {"zh": "zh-Hans", "zh-hans": "zh-Hans", "zh-cn": "zh-Hans", "zh-sg": "zh-Hans",
              "zh-hant": "zh-Hant", "zh-tw": "zh-Hant", "zh-hk": "zh-Hant", "zh-mo": "zh-Hant",
              "ja": "ja", "en": "en"}
# WLM / WLE 模板自动加的一句："This is a photo of a monument in Spain, number: RI-51-0001234"
BOILERPLATE = re.compile(r"This is a (?:photo|image) of (?:a |an )?[^.:]*?(?:monument|heritage|protected area|listed building|natural)[^:]*?"
                         r"(?:number|ID|id|identified by)\s*:?\s*[\w./()\-]*\.?", re.I)
CDN = "https://cdn.jannchie.com/photo-spots/commons/"
# 精选集 → 地图点属性 c 的位，前端按位筛选（src/collections.ts 里同样的顺序）
COLLECTIONS = {"fp": 1, "qi": 2, "vi": 4, "wlm": 8, "wle": 16}
ROOT = Path(__file__).resolve().parent.parent


def ratio(v):
    """EXIF 的分数（"27/1"、"10/1600"）→ 数值"""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return v
    m = re.fullmatch(r"\s*(-?[\d.]+)\s*/\s*([\d.]+)\s*", str(v))
    if m:
        return float(m[1]) / float(m[2]) if float(m[2]) else None
    try:
        return float(v)
    except ValueError:
        return None


def exposure(v):
    """快门：1 秒以下写成 1/x"""
    t = ratio(v)
    if not t:
        return None
    return f"1/{round(1 / t)}" if t < 1 else f"{t:g}"


def title(s):
    return s.get("name") or re.sub(r"\.(jpe?g|png|tiff?|webp)$", "", s["title"].removeprefix("File:"), flags=re.I)


def text(v):
    """EXIF 字段偶尔是列表或带语言的字典，只取一个字符串"""
    if isinstance(v, list):
        v = v[0] if v else None
    return v.strip() if isinstance(v, str) else None


def camera(ex):
    """"Canon" + "Canon EOS 650D" 只写一次厂商"""
    make, model = text(ex.get("Make")) or "", text(ex.get("Model")) or ""
    if not model:
        return make or None
    if not make or model.lower().startswith(make.split()[0].lower()):
        return model
    return f"{make} {model}"


def taken(v):
    m = re.match(r"(\d{4})[:\-](\d{2})[:\-](\d{2})", v or "")
    return f"{m[1]}-{m[2]}-{m[3]}" if m else None


def clip(v):
    v = re.sub(r"\s+", " ", BOILERPLATE.sub("", v)).strip(" ,;")
    return v if len(v) <= DESC_MAX else v[:DESC_MAX - 1].rstrip() + "…"


def descriptions(d, title):
    """{Commons 语言: 文本} → {站点语言 或 "_": 文本}，去掉模板句、和标题重复的"""
    out = {}
    for k, v in (d or {}).items():
        v = clip(v)
        if not v or v == title:
            continue
        site = DESC_LANGS.get(k.lower())
        if site:
            out.setdefault(site, v)
        elif "_" not in out:
            out["_"] = v
    return out or None


def commons_thumb(s, width):
    """没镜像的照片先用 Commons 的缩略图；原图不够宽时 thumb_url 就是原图"""
    url = s["thumb_url"] or s["original_url"]
    return url.replace("/1280px-", f"/{width}px-") if "/thumb/" in url else url


def quadtree(items, x0=-180.0, y0=-90.0, x1=180.0, y1=90.0, path="q"):
    """items: [(lng, lat, key)] → {叶子编号: [key]}；叶子编号是象限路径，如 q0213"""
    if len(items) <= SHARD_MAX or len(path) > 24:
        return {path: [k for _, _, k in items]} if items else {}
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    quads = ([], [], [], [])
    for it in items:
        quads[(it[0] >= mx) + 2 * (it[1] >= my)].append(it)
    out = {}
    for q, (a, b, c, d) in enumerate([(x0, y0, mx, my), (mx, y0, x1, my), (x0, my, mx, y1), (mx, my, x1, y1)]):
        out.update(quadtree(quads[q], a, b, c, d, path + str(q)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="commons_spots 的 out 目录")
    a = ap.parse_args()
    src = Path(a.src)

    mirrored = set()
    if (src / "mirror.jsonl").exists():
        for line in open(src / "mirror.jsonl", encoding="utf-8"):
            if line.endswith("\n"):
                r = json.loads(line)
                if r["status"] == "ok":
                    mirrored.add(r["pageid"])

    details = {}
    # 一张照片可能同时在几个分类里（例如既是 QI 又是 WLM 入选作品）：以 members.jsonl 的全部记录为准
    cats: dict[int, set[str]] = {}
    for line in open(src / "members.jsonl", encoding="utf-8"):
        if line.endswith("\n"):
            m = json.loads(line)
            cats.setdefault(m["pageid"], set()).add(m["cat"])

    desc = {}
    if (src / "descriptions.jsonl").exists():
        for line in open(src / "descriptions.jsonl", encoding="utf-8"):
            if line.endswith("\n"):
                r = json.loads(line)
                desc[r["pageid"]] = r["description"]

    for line in open(src / "spots.jsonl", encoding="utf-8"):
        s = json.loads(line)
        if s["exif_gps"] != "match" or s["mime"] not in ("image/jpeg", "image/png", "image/tiff", "image/webp"):
            continue
        i, ex = s["pageid"], s["exif"]
        m = i in mirrored
        heading = ratio(ex.get("GPSImgDirection"))
        name = title(s)
        details[i] = {
            "title": name,
            "desc": descriptions(s["description"] if "description" in s else desc.get(i), name),
            "page": s["page_url"],
            "lng": s["lon"],
            "lat": s["lat"],
            "w": s["width"],
            "h": s["height"],
            "small": f"{CDN}{i}/500.webp" if m else commons_thumb(s, 500),
            "large": f"{CDN}{i}/1280.webp" if m else commons_thumb(s, 1280),
            "mirrored": m,
            "artist": s["artist"],
            "license": s["license"],
            "licenseUrl": s["license_url"],
            "taken": taken(s["taken"]),
            "featured": "fp" in cats.get(i, set(s["cats"])),
            # 摄影比赛入选（Wiki Loves Monuments 含国家赛提名，Wiki Loves Earth 为获奖）
            "contest": "wlm" if "wlm" in cats.get(i, ()) else "wle" if "wle" in cats.get(i, ()) else None,
            "camera": camera(ex),
            "lens": text(ex.get("LensModel")),
            "focal": ratio(ex.get("FocalLength")),
            "focal35": ratio(ex.get("FocalLengthIn35mmFilm")) or None,
            "fnumber": ratio(ex.get("FNumber")),
            "exposure": exposure(ex.get("ExposureTime")),
            "iso": ex.get("ISOSpeedRatings") if isinstance(ex.get("ISOSpeedRatings"), (int, float)) else None,
            "heading": round(heading % 360) if heading is not None else None,
            "_cats": cats.get(i, set()) | set(s["cats"]),
        }

    shards = quadtree([(d["lng"], d["lat"], i) for i, d in details.items()])
    shard_of = {i: k for k, ids in shards.items() for i in ids}
    features = [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [round(d["lng"], 6), round(d["lat"], 6)]},
                 "properties": {"i": i, "s": shard_of[i], "c": sum(COLLECTIONS[c] for c in d.pop("_cats"))}}
                for i, d in details.items()]

    data = ROOT / "public" / "data"
    if (data / "d").exists():
        for f in (data / "d").glob("*.json"):
            f.unlink()
    (data / "d").mkdir(parents=True, exist_ok=True)
    (data / "spots.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": features},
                                                   separators=(",", ":")), encoding="utf-8")
    (data / "meta.json").write_text(json.dumps({
        "count": len(details), "mirrored": sum(1 for d in details.values() if d["mirrored"]),
        "withHeading": sum(1 for d in details.values() if d["heading"] is not None),
        "withDesc": sum(1 for d in details.values() if d["desc"]),
        "collections": {k: sum(1 for f in features if f["properties"]["c"] & bit) for k, bit in COLLECTIONS.items()},
    }), encoding="utf-8")
    for k, ids in shards.items():
        (data / "d" / f"{k}.json").write_text(json.dumps({i: details[i] for i in ids}, ensure_ascii=False, separators=(",", ":")),
                                              encoding="utf-8")
    print(f"{len(features):,} spots ({sum(1 for f in features if f['properties']['i'] in mirrored):,} mirrored) "
          f"-> {data / 'spots.geojson'} ({(data / 'spots.geojson').stat().st_size / 2**20:.1f} MiB), {len(shards)} shards")


if __name__ == "__main__":
    main()
