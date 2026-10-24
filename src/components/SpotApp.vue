<script setup lang="ts">
// 页面骨架沿用 junrei 的 JunreiApp：全屏地图 + 桌面端左侧面板 / 手机端底部抽屉，面板挡住的部分作为地图留白
import { JIcon } from "@jannchie/icons-vue";
import { computed, onBeforeUnmount, onMounted, ref, shallowRef, watch } from "vue";
import "../theme.css";
import { ICONS } from "../icons";
import { compass, fetchSpot, fetchSpots, fieldOfView, type Spot } from "../spots";
import { cycleTheme, initTheme, themePref } from "../theme";
import SpotMap, { type SpotRef } from "./SpotMap.vue";

const app = ref<HTMLDivElement>();
const panel = ref<HTMLElement>();
const mapPadding = ref({ top: 0, right: 0, bottom: 0, left: 0 });
const meta = ref<{ count: number; mirrored: number; withHeading: number } | null>(null);

// ---- 选中的机位，写进 ?spot=pageid.分片，链接可分享 ----
const focus = shallowRef<Spot | null>(null);
const focusRef = ref<SpotRef | null>(null);
let pickSeq = 0;
async function pick(r: SpotRef | null) {
  const seq = ++pickSeq;
  focusRef.value = r;
  if (!r) {
    focus.value = null;
    return;
  }
  const spot = await fetchSpot(r.id, r.shard).catch(() => null);
  if (seq !== pickSeq) return;
  focus.value = spot;
  sheet.value = "half";
  panel.value?.querySelector(".body")?.scrollTo({ top: 0 });
}
watch(focusRef, (r) => {
  const url = new URL(location.href);
  if (r) url.searchParams.set("spot", `${r.id}.${r.shard}`);
  else url.searchParams.delete("spot");
  history.replaceState(history.state, "", url);
});

// ---- 视野里的机位 ----
const inView = shallowRef<Spot[] | null>(null);
let viewSeq = 0;
async function onView(refs: SpotRef[] | null) {
  const seq = ++viewSeq;
  if (!refs) {
    inView.value = null;
    return;
  }
  const spots = await fetchSpots(refs).catch(() => []);
  if (seq === viewSeq) inView.value = spots;
}

// ---- 手机端抽屉：收起 / 半屏 / 全屏，点把手切换 ----
const sheet = ref<"peek" | "half" | "full">("peek");
function toggleSheet() {
  sheet.value = sheet.value === "peek" ? "half" : sheet.value === "half" ? "full" : "peek";
}

const map = ref<InstanceType<typeof SpotMap>>();
const PLACES = [
  { name: "京都", center: [135.775, 35.0] as [number, number], zoom: 13 },
  { name: "巴黎", center: [2.335, 48.857] as [number, number], zoom: 13 },
  { name: "柏林", center: [13.39, 52.515] as [number, number], zoom: 13 },
  { name: "布拉格", center: [14.418, 50.087] as [number, number], zoom: 14 },
  { name: "纽约", center: [-73.985, 40.75] as [number, number], zoom: 13 },
  { name: "阿尔卑斯", center: [8.0, 46.55] as [number, number], zoom: 9.5 },
];

// ---- 详情的展示字段 ----
const f = (n: number) => (Number.isInteger(n) ? String(n) : n.toFixed(1).replace(/\.0$/, ""));
const settings = computed(() => {
  const s = focus.value;
  if (!s) return [];
  const out: { label: string; value: string }[] = [];
  if (s.focal) out.push({ label: "焦距", value: s.focal35 && Math.abs(s.focal35 - s.focal) > 1 ? `${f(s.focal)}mm（等效 ${f(s.focal35)}mm）` : `${f(s.focal)}mm` });
  if (s.fnumber) out.push({ label: "光圈", value: `f/${f(s.fnumber)}` });
  if (s.exposure) out.push({ label: "快门", value: `${s.exposure} s` });
  if (s.iso) out.push({ label: "ISO", value: String(s.iso) });
  return out;
});
const navUrl = (s: Spot) => `https://www.google.com/maps/dir/?api=1&destination=${s.lat},${s.lng}`;
const appleUrl = (s: Spot) => `https://maps.apple.com/?daddr=${s.lat},${s.lng}`;
const coords = (s: Spot) => `${s.lat.toFixed(5)}, ${s.lng.toFixed(5)}`;

let observer: ResizeObserver | undefined;
onMounted(() => {
  initTheme();
  fetch("/data/meta.json").then((r) => r.json()).then((m) => (meta.value = m), () => {});
  observer = new ResizeObserver(() => {
    const a = app.value!.getBoundingClientRect();
    const r = panel.value!.getBoundingClientRect();
    const beside = r.width < a.width * 0.6; // 桌面端在左侧，手机端在底部
    const next = beside
      ? { top: 0, right: 0, bottom: 0, left: Math.round(r.right - a.left) }
      : { top: 0, right: 0, bottom: Math.round(a.bottom - r.top), left: 0 };
    const cur = mapPadding.value;
    if (cur.bottom !== next.bottom || cur.left !== next.left) mapPadding.value = next;
  });
  observer.observe(panel.value!);
  observer.observe(app.value!);
  const [id, shard] = (new URLSearchParams(location.search).get("spot") ?? "").split(".");
  if (Number(id) && shard) void pick({ id: Number(id), shard });
  addEventListener("keydown", onKey);
});
onBeforeUnmount(() => {
  observer?.disconnect();
  removeEventListener("keydown", onKey);
});
function onKey(e: KeyboardEvent) {
  if (e.key === "Escape" && focusRef.value) void pick(null);
}

const themeIcon = computed(() => ({ auto: ICONS.themeAuto, light: ICONS.themeLight, dark: ICONS.themeDark })[themePref.value]);
const themeLabel = computed(() => ({ auto: "外观：跟随系统", light: "外观：浅色", dark: "外观：深色" })[themePref.value]);
</script>

<template>
  <div ref="app" class="app" :style="{ '--panel-inset-bottom': `${mapPadding.bottom}px` }">
    <SpotMap ref="map" :focus="focus" :padding="mapPadding" @pick="pick" @view="onView" />

    <aside ref="panel" class="panel" :class="`sheet-${sheet}`">
      <div class="handle" @click="toggleSheet" />
      <header class="head">
        <div class="brand">
          <span class="mark"><JIcon :icon="ICONS.camera" /></span>
          <div>
            <h1>摄影机位地图</h1>
            <p class="muted stat">
              <template v-if="meta">{{ meta.count.toLocaleString() }} 个真实拍摄点</template>
              <template v-else>加载中…</template>
            </p>
          </div>
        </div>
        <button class="icon-btn" :title="themeLabel" :aria-label="themeLabel" @click="cycleTheme"><JIcon :icon="themeIcon" /></button>
      </header>

      <div class="body">
        <!-- 机位详情 -->
        <article v-if="focus" class="detail">
          <div class="detail-bar">
            <button class="text-btn" @click="pick(null)">← 返回</button>
            <button class="icon-btn" title="关闭" aria-label="关闭" @click="pick(null)"><JIcon :icon="ICONS.close" /></button>
          </div>
          <a class="photo" :href="focus.page" target="_blank" rel="noopener" :style="{ aspectRatio: `${focus.w} / ${focus.h}` }">
            <img
              :key="focus.id"
              :src="focus.large"
              :srcset="`${focus.small} 500w, ${focus.large} 1280w`"
              sizes="(max-width: 640px) 100vw, 356px"
              :alt="focus.title"
            />
          </a>
          <h2>{{ focus.title }}</h2>
          <p v-if="focus.featured" class="badge">Commons 精选图片</p>

          <dl class="facts">
            <div><dt>位置</dt><dd class="stat">{{ coords(focus) }}</dd></div>
            <div v-if="focus.heading != null">
              <dt>朝向</dt>
              <dd class="stat">{{ focus.heading }}° {{ compass(focus.heading) }}，视角约 {{ Math.round(fieldOfView(focus)) }}°</dd>
            </div>
            <div v-if="focus.taken"><dt>拍摄</dt><dd class="stat">{{ focus.taken }}</dd></div>
            <div v-if="focus.camera"><dt>相机</dt><dd>{{ focus.camera }}</dd></div>
            <div v-if="focus.lens"><dt>镜头</dt><dd>{{ focus.lens }}</dd></div>
          </dl>
          <ul v-if="settings.length" class="settings">
            <li v-for="x in settings" :key="x.label"><span class="muted">{{ x.label }}</span><b class="stat">{{ x.value }}</b></li>
          </ul>

          <div class="actions">
            <a class="btn primary" :href="navUrl(focus)" target="_blank" rel="noopener"><JIcon :icon="ICONS.navigate" />Google 地图导航</a>
            <a class="btn" :href="appleUrl(focus)" target="_blank" rel="noopener">Apple 地图</a>
          </div>

          <p class="credit muted">
            © {{ focus.artist ?? "佚名" }} ·
            <a v-if="focus.licenseUrl" :href="focus.licenseUrl" target="_blank" rel="noopener">{{ focus.license }}</a>
            <template v-else>{{ focus.license }}</template>
            · <a :href="focus.page" target="_blank" rel="noopener">Wikimedia Commons <JIcon :icon="ICONS.external" /></a>
          </p>
        </article>

        <!-- 视野里的机位 -->
        <section v-else-if="inView" class="list">
          <p class="muted stat section-title">
            视野内 {{ inView.length }}{{ inView.length >= 60 ? "+" : "" }} 个机位{{ inView.length >= 60 ? "，显示离中心最近的 60 个" : "" }}
          </p>
          <p v-if="!inView.length" class="muted empty">这一带还没有收录的机位，换个地方看看。</p>
          <div class="grid">
            <button
              v-for="s in inView"
              :key="s.id"
              class="thumb"
              :title="s.title"
              @click="pick({ id: s.id, shard: s.shard })"
            >
              <img :src="s.small" alt="" loading="lazy" />
              <span>{{ s.title }}</span>
            </button>
          </div>
        </section>

        <!-- 还在热力图阶段 -->
        <section v-else class="intro">
          <p>每个点都是一张高质量照片真实的拍摄位置：坐标来自相机 EXIF，附样片、焦距、光圈和许可信息。放大地图，或者从这里开始：</p>
          <div class="places">
            <button v-for="p in PLACES" :key="p.name" class="chip" @click="map?.flyTo(p.center, p.zoom)">{{ p.name }}</button>
          </div>
        </section>
      </div>

      <footer class="foot muted">
        照片来自 <a href="https://commons.wikimedia.org/wiki/Commons:Quality_images" target="_blank" rel="noopener">Wikimedia Commons</a>，版权归各作者 ·
        地图 © <a href="https://openfreemap.org" target="_blank" rel="noopener">OpenFreeMap</a> © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>
      </footer>
    </aside>
  </div>
</template>

<style>
* {
  box-sizing: border-box;
}
html,
body {
  margin: 0;
  height: 100%;
  background: var(--bg-solid);
  color: var(--fg);
}
:root {
  font-family: -apple-system, system-ui, "PingFang SC", "Microsoft YaHei UI", "Microsoft YaHei", "Noto Sans SC", "Source Han Sans SC", sans-serif;
}
a {
  color: inherit;
}
* {
  scrollbar-width: thin;
  scrollbar-color: var(--scroll-thumb) transparent;
}
</style>

<style scoped>
.app {
  position: fixed;
  inset: 0;
}
.panel {
  position: absolute;
  top: 12px;
  left: 12px;
  bottom: 12px;
  width: 380px;
  display: flex;
  flex-direction: column;
  background: var(--bg);
  border-radius: 16px;
  box-shadow: var(--shadow);
  backdrop-filter: var(--glass);
  overflow: hidden;
}
.handle {
  display: none;
}
@media (max-width: 640px) {
  .panel {
    top: auto;
    left: 0;
    right: 0;
    bottom: 0;
    width: auto;
    padding-bottom: env(safe-area-inset-bottom);
    border-radius: 16px 16px 0 0;
    transition: height 0.28s cubic-bezier(0.2, 0.8, 0.2, 1);
  }
  .sheet-peek {
    height: calc(84px + env(safe-area-inset-bottom));
  }
  .sheet-half {
    height: 52dvh;
  }
  .sheet-full {
    height: calc(100dvh - 48px - env(safe-area-inset-top));
  }
  .handle {
    display: block;
    flex: none;
    height: 22px;
    margin-bottom: -10px;
    cursor: pointer;
  }
  .handle::before {
    content: "";
    display: block;
    width: 36px;
    height: 5px;
    margin: 8px auto 0;
    border-radius: 3px;
    background: var(--muted);
    opacity: 0.45;
  }
}
.head {
  flex: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 14px 12px 16px;
  border-bottom: 1px solid var(--line);
}
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
}
.mark {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  color: #fff;
  background: var(--accent);
  border-radius: 10px;
  font-size: 18px;
}
h1 {
  margin: 0;
  font-size: 16px;
  font-weight: 650;
}
.head p {
  margin: 2px 0 0;
  font-size: 12px;
}
.body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 12px;
}
.foot {
  flex: none;
  padding: 8px 14px 10px;
  font-size: 11px;
  line-height: 1.5;
  border-top: 1px solid var(--line);
}
.muted {
  color: var(--muted);
}
.stat {
  font-variant-numeric: tabular-nums;
}
.icon-btn {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  padding: 0;
  color: var(--muted);
  background: none;
  border: 0;
  border-radius: 8px;
  cursor: pointer;
}
.icon-btn:hover,
.text-btn:hover {
  background: var(--hover);
  color: var(--fg);
}
.text-btn {
  padding: 4px 8px;
  margin-left: -6px;
  font: inherit;
  font-size: 13px;
  color: var(--muted);
  background: none;
  border: 0;
  border-radius: 8px;
  cursor: pointer;
}

/* ---- 首页 ---- */
.intro p {
  margin: 4px 4px 14px;
  font-size: 14px;
  line-height: 1.65;
}
.places {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 0 4px;
}
.chip {
  padding: 6px 12px;
  font: inherit;
  font-size: 13px;
  color: var(--fg);
  background: var(--hover);
  border: 0;
  border-radius: 999px;
  cursor: pointer;
}
.chip:hover {
  background: var(--line);
}

/* ---- 视野列表 ---- */
.section-title {
  margin: 2px 4px 10px;
  font-size: 12px;
}
.empty {
  margin: 4px;
  font-size: 13px;
}
.grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}
.thumb {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 0;
  font: inherit;
  text-align: left;
  color: var(--fg);
  background: none;
  border: 0;
  cursor: pointer;
}
.thumb img {
  width: 100%;
  aspect-ratio: 4 / 3;
  object-fit: cover;
  border-radius: 8px;
  background: var(--hover);
}
.thumb span {
  font-size: 12px;
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  overflow-wrap: anywhere;
}
.thumb:hover img {
  outline: 2px solid var(--accent);
}

/* ---- 详情 ---- */
.detail-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.photo {
  display: block;
  max-height: 60vh;
  border-radius: 10px;
  overflow: hidden;
  background: var(--hover);
}
.photo img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
h2 {
  margin: 12px 2px 4px;
  font-size: 15px;
  font-weight: 600;
  line-height: 1.4;
  overflow-wrap: anywhere;
}
.badge {
  display: inline-block;
  margin: 2px 2px 0;
  padding: 2px 8px;
  font-size: 11px;
  color: var(--accent);
  border: 1px solid currentColor;
  border-radius: 999px;
}
.facts {
  margin: 12px 2px 0;
  font-size: 13px;
}
.facts div {
  display: grid;
  grid-template-columns: 40px 1fr;
  gap: 8px;
  padding: 5px 0;
  border-bottom: 1px solid var(--line);
}
.facts dt {
  color: var(--muted);
}
.facts dd {
  margin: 0;
  overflow-wrap: anywhere;
}
.settings {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(70px, 1fr));
  gap: 6px;
  margin: 12px 0 0;
  padding: 0;
  list-style: none;
}
.settings li {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px 10px;
  font-size: 11px;
  background: var(--hover);
  border-radius: 8px;
}
.settings b {
  font-size: 13px;
  font-weight: 600;
}
.actions {
  display: flex;
  gap: 8px;
  margin-top: 14px;
}
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 12px;
  font-size: 13px;
  text-decoration: none;
  background: var(--hover);
  border-radius: 9px;
}
.btn.primary {
  flex: 1;
  color: #fff;
  background: var(--accent);
}
.credit {
  margin: 14px 2px 4px;
  font-size: 12px;
  line-height: 1.6;
  overflow-wrap: anywhere;
}
</style>
