// 页面 loader 与 <head>：简体中文没有语言前缀（/），其他语言带前缀（/zh-hant、/ja、/en），同一套逻辑（与 junrei 相同）
import { localeFromSegment, seoHead, type Locale } from "@mapette/core";
import { defineHandler, defineHead, type InferProps } from "void";
import { messagesFor } from "../i18n";

const SITE = "https://spot.jannchie.com";

type Params = { req: { param(name: string): string | undefined } };

/** 路由里没有 :lang 段就是简体中文；有但不认识的语言返回 null（404） */
function localeOf(c: Params): Locale | null {
  const seg = c.req.param("lang");
  return seg === undefined ? "zh-Hans" : localeFromSegment(seg);
}

export const homeLoader = defineHandler(async (c) => {
  const lang = localeOf(c);
  if (!lang) return c.notFound();
  return { lang };
});

export const homePageHead = defineHead<InferProps<typeof homeLoader>>((_c, { lang }) => {
  const t = messagesFor(lang);
  return seoHead({
    site: SITE,
    locale: lang,
    path: "/",
    title: `${t.brand} · ${t.tagline}`,
    description: t.description,
    siteName: t.brand,
    image: `${SITE}/icons/og-${lang.toLowerCase()}.png`,
    // 加到主屏幕后图标下的名字（iOS）
    meta: [{ name: "apple-mobile-web-app-title", content: t.appName }],
    // 各语言各自的 PWA 清单（应用名、启动页），scripts/gen-pwa.mts 生成
    link: [{ rel: "manifest", href: `/manifest-${lang.toLowerCase()}.webmanifest` }],
    jsonLd: { "@context": "https://schema.org", "@type": "WebSite", name: t.brand, url: SITE, inLanguage: lang },
  });
});
