// 生成各语言的 PWA 清单 public/manifest-<lang>.webmanifest 与 sitemap public/sitemap.xml。
// 每种语言的应用名、简介和启动页不同（从英文页安装，打开的就是英文首页）。改了文案后重跑：
//   node --experimental-strip-types scripts/gen-pwa.mts
import { writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { LOCALES, localePath, type Locale } from "@mapette/core";

export const SITE = "https://spot.jannchie.com";
const OUT = fileURLToPath(new URL("../public/", import.meta.url));

const TEXT: Record<Locale, { name: string; short: string; description: string }> = {
  "zh-Hans": { name: "Sightspot", short: "Sightspot", description: "高质量照片的真实拍摄位置，附样片、焦距与朝向" },
  "zh-Hant": { name: "Sightspot", short: "Sightspot", description: "高品質照片的真實拍攝位置，附樣片、焦距與朝向" },
  ja: { name: "Sightspot", short: "Sightspot", description: "高品質な写真の実際の撮影位置を、作例・焦点距離・向きとともに" },
  en: { name: "Sightspot", short: "Sightspot", description: "Where great photos were actually taken, with the photo, focal length and direction" },
};

const ICONS = [
  { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png", purpose: "any" },
  { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png", purpose: "any" },
  { src: "/icons/maskable-192.png", sizes: "192x192", type: "image/png", purpose: "maskable" },
  { src: "/icons/maskable-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
];

for (const l of LOCALES) {
  const t = TEXT[l];
  const home = localePath(l, "/");
  const manifest = {
    // 各语言是不同的应用：id 与启动页都是该语言的首页
    id: home,
    name: t.name,
    short_name: t.short,
    description: t.description,
    start_url: home,
    scope: "/",
    display: "standalone",
    orientation: "any",
    background_color: "#f2f4f6",
    theme_color: "#f2f4f6",
    lang: l,
    categories: ["photo", "travel", "navigation"],
    icons: ICONS,
  };
  writeFileSync(`${OUT}manifest-${l.toLowerCase()}.webmanifest`, `${JSON.stringify(manifest, null, 2)}\n`);
}

// 站点只有各语言的首页；同一页面的语言版本互相指向
const alternates = LOCALES.map((l) => `    <xhtml:link rel="alternate" hreflang="${l}" href="${SITE}${localePath(l, "/")}"/>`).join("\n");
writeFileSync(
  `${OUT}sitemap.xml`,
  `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">
${LOCALES.map((l) => `  <url>\n    <loc>${SITE}${localePath(l, "/")}</loc>\n${alternates}\n  </url>`).join("\n")}
</urlset>
`,
);
console.log("pwa ->", OUT);
