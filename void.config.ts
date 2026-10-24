// 骨架沿用 junrei（Void + Vue + MapLibre），只保留 demo 用得上的配置
import { defineConfig } from 'void/config';

export default defineConfig({
  "worker": {
    "compatibility_date": "2026-02-24"
  },
  "cloudflare": {
    "name": "photo-spots",
    "account_id": "ad02684d0205554549c21cd8bfc41d48"
  },
  "head": {
    "meta": [
      { "name": "viewport", "content": "width=device-width, initial-scale=1, viewport-fit=cover, interactive-widget=resizes-visual" },
      { "name": "theme-color", "content": "#f2f4f6", "media": "(prefers-color-scheme: light)" },
      { "name": "theme-color", "content": "#212327", "media": "(prefers-color-scheme: dark)" }
    ],
    // 首次绘制前应用用户保存的外观选择（与 @mapette/core 的 themeInitScript("photo-spots:theme") 相同），避免刷新时闪一下
    "script": [
      { "innerHTML": "try{var t=localStorage.getItem('photo-spots:theme');if(t==='light'||t==='dark')document.documentElement.dataset.theme=t}catch(e){}" }
    ]
  },
  "routing": {
    "headers": {
      "/data/*": ["Cache-Control: public, max-age=3600, stale-while-revalidate=86400"]
    }
  }
});
