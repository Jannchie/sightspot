// PWA 图标与网站小图标：主题色底板上的白色相机（与页面左上角的标志相同，图形来自 @jannchie/icons 的 camera）。
// 改了设计后重跑，再跑 gen_og.py 合成社交分享图：
//   node --experimental-strip-types scripts/gen-icons.mts && python scripts/gen_og.py
import { mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import sharp from "sharp";

const OUT = fileURLToPath(new URL("../public/icons/", import.meta.url));
mkdirSync(OUT, { recursive: true });

// 与站点的主题色（SpotApp.vue 里 --mapette-accent-light）一致
const TILE = "#3567a8";
const CAMERA =
  "M4.5 7.5H7.17a2 2 0 0 0 1.42-.59l.82-.82a2 2 0 0 1 1.42-.59h2.34a2 2 0 0 1 1.42.59l.82.82a2 2 0 0 0 1.42.59H19.5a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H4.5a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2zm4 5.75a3.5 3.5 0 1 0 7 0 3.5 3.5 0 1 0-7 0";

/** bleed：铺满底色、图形缩进安全区（Android 可遮罩图标、iOS 主屏）；否则圆角方形 */
function svg(bleed: boolean) {
  const scale = bleed ? 2.2 : 2.7; // 24 → 100 坐标系里图形的大小
  const glyph = `<g transform="translate(50 50) scale(${scale}) translate(-12 -12.5)"><path d="${CAMERA}" fill="none" stroke="#fff" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></g>`;
  const tile = bleed ? `<rect width="100" height="100" fill="${TILE}"/>` : `<rect width="100" height="100" rx="22" fill="${TILE}"/>`;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="512" height="512">${tile}${glyph}</svg>`;
}

async function png(name: string, size: number, bleed = false) {
  await sharp(Buffer.from(svg(bleed))).resize(size, size).png().toFile(OUT + name);
}

await Promise.all([
  png("icon-192.png", 192),
  png("icon-512.png", 512),
  png("maskable-192.png", 192, true),
  png("maskable-512.png", 512, true),
  png("apple-touch-icon.png", 180, true),
  png("favicon-32.png", 32),
]);
console.log("icons ->", OUT);
