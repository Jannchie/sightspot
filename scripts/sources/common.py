"""Commons 之外的照片来源（iNaturalist、Geograph）共用的输出格式。

每个来源的抓取脚本把照片写成同一格式的 jsonl，一行一张，export_demo.py --extra 读进来与 Commons 合并：
  src        来源："inat" | "geograph"
  id         来源里的编号（字符串）
  lng, lat   拍摄位置
  title      标题；desc 是 {站点语言 或 "_": 文本} 或 null（与 Commons 的描述同一格式）
  page       原始页面（署名、许可都在那里）
  w, h       原图尺寸；small / large 是约 500px / 1280px 宽的图片地址（直接引用来源的图床，不镜像）
  artist, license, licenseUrl, taken, camera, lens, focal, focal35, fnumber, exposure, iso, heading  可为 null
  score      来源内的质量分（收藏数、投票分……），只用来在同一来源里排先后
"""

import json
import time
import urllib.error
import urllib.request
from pathlib import Path

FIELDS = ("src", "id", "lng", "lat", "title", "desc", "page", "w", "h", "small", "large", "artist", "license",
          "licenseUrl", "taken", "camera", "lens", "focal", "focal35", "fnumber", "exposure", "iso", "heading", "score")

# 许可代码 → (名称, 链接)。不收"保留所有权利"和禁止演绎（ND）的
LICENSES = {
    "cc0": ("CC0", "https://creativecommons.org/publicdomain/zero/1.0/"),
    "pdm": ("Public domain", "https://creativecommons.org/publicdomain/mark/1.0/"),
    "cc-by": ("CC BY 4.0", "https://creativecommons.org/licenses/by/4.0/"),
    "cc-by-sa": ("CC BY-SA 4.0", "https://creativecommons.org/licenses/by-sa/4.0/"),
    "cc-by-nc": ("CC BY-NC 4.0", "https://creativecommons.org/licenses/by-nc/4.0/"),
    "cc-by-nc-sa": ("CC BY-NC-SA 4.0", "https://creativecommons.org/licenses/by-nc-sa/4.0/"),
}

UA = "Sightspot/1.0 (https://spot.jannchie.com; photo spot map)"


def get_json(url: str, retries: int = 5, headers: dict | None = None):
    """GET 一个 JSON 接口；429 / 5xx / 网络错误时退避重试"""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429 and e.code < 500:
                raise
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            pass
        time.sleep(min(300, 10 * 2 ** attempt))
    raise RuntimeError(f"giving up: {url}")


def record(**kw) -> dict:
    """补齐缺省字段为 null，字段顺序固定"""
    unknown = set(kw) - set(FIELDS)
    if unknown:
        raise ValueError(f"unknown fields: {unknown}")
    return {k: kw.get(k) for k in FIELDS}


class Writer:
    """追加写 jsonl，记住已写过的编号（中断后重跑不重复）"""

    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self.seen: set[str] = set()
        if path.exists():
            for line in open(path, encoding="utf-8"):
                if line.endswith("\n"):
                    self.seen.add(json.loads(line)["id"])
        self.f = open(path, "a", encoding="utf-8")

    def add(self, rec: dict) -> bool:
        if rec["id"] in self.seen:
            return False
        self.seen.add(rec["id"])
        self.f.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n")
        return True

    def flush(self):
        self.f.flush()
