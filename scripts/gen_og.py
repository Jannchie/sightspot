"""生成各语言的社交分享图（og-<locale>.png，og.png 为简体中文的副本）。
标志由 scripts/gen-icons.mts 生成，先跑那个：
  node --experimental-strip-types scripts/gen-icons.mts && python scripts/gen_og.py
"""

import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "public" / "icons"
FONTS = Path("C:/Windows/Fonts")
LAND = (242, 244, 246)
INK = (29, 29, 31)

# 语言 → (标题, 副标题, 标题字体, 副标题字体)；每种语言用它自己的字形
LOCALES = {
    "zh-hans": ("摄影机位地图", "高质量照片的真实拍摄位置", "msyhbd.ttc", "msyh.ttc"),
    "zh-hant": ("攝影機位地圖", "高品質照片的真實拍攝位置", "msjhbd.ttc", "msjh.ttc"),
    "ja": ("撮影スポットマップ", "高品質な写真の実際の撮影位置", "YuGothB.ttc", "YuGothM.ttc"),
    "en": ("Photo Spot Map", "Where great photos were actually taken", "segoeuib.ttf", "segoeui.ttf"),
}


def fit(font_file, text, size, width):
    """字号从 size 往下缩，直到标题放得进 width"""
    while True:
        font = ImageFont.truetype(str(FONTS / font_file), size)
        if font.getlength(text) <= width or size <= 40:
            return font
        size -= 4


def main():
    icon = Image.open(OUT / "icon-512.png").convert("RGBA").resize((220, 220), Image.Resampling.LANCZOS)
    small = ImageFont.truetype(str(FONTS / "segoeui.ttf"), 28)
    for key, (title, sub, title_font, sub_font) in LOCALES.items():
        og = Image.new("RGB", (1200, 630), LAND)
        og.paste(icon, (130, 205), icon)
        d = ImageDraw.Draw(og)
        d.text((400, 300), title, font=fit(title_font, title, 92, 720), fill=INK, anchor="ls")
        d.text((404, 372), sub, font=ImageFont.truetype(str(FONTS / sub_font), 38), fill=(110, 110, 115), anchor="ls")
        d.text((1150, 580), "spot.jannchie.com", font=small, fill=(150, 150, 155), anchor="rs")
        og.save(OUT / f"og-{key}.png", optimize=True)
    shutil.copyfile(OUT / "og-zh-hans.png", OUT / "og.png")
    print("og ->", OUT)


if __name__ == "__main__":
    main()
