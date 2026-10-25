// 隐私政策的文字（网站与 iOS App 共用，App Store 的隐私政策链接指向 /privacy）：页面与 <head> 都从这里取
import type { Locale } from "@mapette/core";

export const PRIVACY_UPDATED = "2026-10-25";
export const ISSUES = "https://github.com/Jannchie/sightspot/issues";

/** 每种语言：标题、导语、各条（标题 + 正文）、反馈 */
export const PRIVACY: Record<Locale, { title: string; intro: string; items: [string, string][]; contact: string; updated: string }> = {
  "zh-Hans": {
    title: "隐私政策",
    intro: "本政策适用于 Sightspot 网站（spot.jannchie.com）与 iOS App。我们不收集、不存储、也不分享任何个人数据：没有账号、统计、广告或追踪。",
    items: [
      ["位置", "只有在你点定位按钮并允许访问后，才会在你的设备上用位置在地图上显示你在哪里，不会发送到任何地方。"],
      ["设备上保存的设置", "网站在浏览器本地保存外观偏好，并缓存页面以便离线打开；这些只存在你的设备上。"],
      ["网络请求", "为显示地图和机位，会从 spot.jannchie.com、cdn.jannchie.com 获取数据与照片，从 tiles.openfreemap.org 获取底图，从 AWS 获取地形。与任何网页请求一样，这些服务器会在连接中获知你的 IP 地址和设备类型；我们不发送其他信息，也不会用这些日志识别你。"],
      ["外部链接", "Wikimedia Commons、许可协议、地图或 GitHub 等链接会打开其他网站或 App，适用它们各自的隐私政策。"],
    ],
    contact: "问题反馈",
    updated: "更新于",
  },
  "zh-Hant": {
    title: "隱私政策",
    intro: "本政策適用於 Sightspot 網站（spot.jannchie.com）與 iOS App。我們不收集、不儲存、也不分享任何個人資料：沒有帳號、統計、廣告或追蹤。",
    items: [
      ["位置", "只有在你點定位按鈕並允許存取後，才會在你的裝置上用位置在地圖上顯示你在哪裡，不會傳送到任何地方。"],
      ["裝置上儲存的設定", "網站在瀏覽器本機儲存外觀偏好，並快取頁面以便離線開啟；這些只存在你的裝置上。"],
      ["網路請求", "為顯示地圖和機位，會從 spot.jannchie.com、cdn.jannchie.com 取得資料與照片，從 tiles.openfreemap.org 取得底圖，從 AWS 取得地形。與任何網頁請求一樣，這些伺服器會在連線中得知你的 IP 位址和裝置類型；我們不傳送其他資訊，也不會用這些記錄識別你。"],
      ["外部連結", "Wikimedia Commons、授權條款、地圖或 GitHub 等連結會開啟其他網站或 App，適用它們各自的隱私政策。"],
    ],
    contact: "問題回報",
    updated: "更新於",
  },
  ja: {
    title: "プライバシーポリシー",
    intro: "本ポリシーは Sightspot のウェブサイト（spot.jannchie.com）と iOS アプリに適用されます。個人データの収集・保存・共有は行いません。アカウント、解析、広告、トラッキングはありません。",
    items: [
      ["位置情報", "現在地ボタンを押して許可した場合のみ、端末上で地図に現在地を表示するために使います。どこにも送信しません。"],
      ["端末に保存する設定", "ウェブサイトは外観の設定をブラウザ内に保存し、オフラインで開けるようページをキャッシュします。いずれも端末内にのみ保存されます。"],
      ["通信", "地図と撮影地点を表示するため、spot.jannchie.com・cdn.jannchie.com からデータと写真を、tiles.openfreemap.org から地図タイルを、AWS から地形データを取得します。通常の Web 通信と同様に、これらのサーバーは接続に伴って IP アドレスと端末の種類を受け取ります。それ以外の情報は送信せず、これらの記録で利用者を特定することもありません。"],
      ["外部リンク", "Wikimedia Commons、ライセンス、マップ、GitHub などへのリンクは他のサイトやアプリで開き、それぞれのプライバシーポリシーが適用されます。"],
    ],
    contact: "お問い合わせ",
    updated: "更新日",
  },
  en: {
    title: "Privacy Policy",
    intro: "This policy covers the Sightspot website (spot.jannchie.com) and iOS app. We do not collect, store or share personal data. There are no accounts, analytics, advertising or tracking.",
    items: [
      ["Location", "Only if you tap the locate button and allow access, your location is used on your device to show where you are on the map. It is never sent anywhere."],
      ["Settings on your device", "The website keeps your appearance setting in your browser, and caches pages so they open offline. These stay on your device."],
      ["Network requests", "To show the map and spots, data and photos are loaded from spot.jannchie.com and cdn.jannchie.com, map tiles from tiles.openfreemap.org, and terrain from AWS. Like any web request, these servers receive your IP address and device type as part of the connection; nothing else is sent, and we do not use these logs to identify you."],
      ["External links", "Links to Wikimedia Commons, licenses, Maps or GitHub open other websites or apps, which have their own privacy policies."],
    ],
    contact: "Questions",
    updated: "Last updated",
  },
};
