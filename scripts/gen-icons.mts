// PWA 图标与网站小图标：白底上的蓝色标志（图形在 src/logo.ts，与页面左上角的标志相同）。
// 改了设计后重跑，再跑 gen_og.py 合成社交分享图：
//   node --experimental-strip-types scripts/gen-icons.mts && python scripts/gen_og.py
import { mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import sharp from "sharp";
import { iconSvg } from "../src/logo.ts";

const OUT = fileURLToPath(new URL("../public/icons/", import.meta.url));
mkdirSync(OUT, { recursive: true });

// 与站点的主题色（SpotApp.vue 里 --mapette-accent-light）一致
const COLOR = "#3567a8";

async function png(name: string, size: number, o: { bleed?: boolean; bold?: boolean } = {}) {
  let img = sharp(Buffer.from(iconSvg({ color: COLOR, ...o }))).resize(size, size);
  if (o.bleed) img = img.flatten({ background: "#ffffff" }); // iOS 主屏图标不支持透明
  await img.png().toFile(OUT + name);
}

await Promise.all([
  png("icon-192.png", 192),
  png("icon-512.png", 512),
  png("maskable-192.png", 192, { bleed: true }),
  png("maskable-512.png", 512, { bleed: true }),
  png("apple-touch-icon.png", 180, { bleed: true }),
  png("favicon-32.png", 32, { bold: true }),
]);
console.log("icons ->", OUT);
