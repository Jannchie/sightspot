<script setup lang="ts">
// 页面：骨架（地图、侧栏 / 抽屉、留白、键盘操作、页脚）来自 @mapette/vue，这里只有机位自己的图层和面板内容
import { JIcon } from "@jannchie/icons-vue";
import { baseShortcuts, directions, fieldOfView, switchLocaleUrl, type Locale, type SheetSnap } from "@mapette/core";
import { MapExplorer, MapFooter, UpdateToast, useThemePref } from "@mapette/vue";
import { computed, onMounted, ref, shallowRef, watch } from "vue";
import { COLLECTION_KEYS, inCollections, parseCollections, type Collection } from "../collections";
import { provideLocale } from "../i18n";
import { ICONS } from "../icons";
import { KEEP_SOURCES, spotStyle } from "../spot-style";
import { fetchSpot, fetchSpots, loadSample, pickDesc, type SampleSpot, type Spot } from "../spots";
import SpotLayers, { type SpotRef } from "./SpotLayers.vue";
import "@mapette/core/mapette.css";

const props = defineProps<{ lang: Locale }>();
const { locale, t } = provideLocale(props.lang);

/** 外观偏好由 mapette 管（页脚按钮与 T 快捷键共用）；存储键与 void.config.ts 的首屏脚本一致 */
const THEME_KEY = "photo-spots:theme";
const { cycle: cycleTheme } = useThemePref(THEME_KEY);

interface Meta {
  count: number;
  mirrored: number;
  withHeading: number;
  withDesc?: number;
  collections?: Record<Collection, number>;
}
const meta = ref<Meta | null>(null);

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
  document.querySelector(".mapette-sheet-body")?.scrollTo({ top: 0 });
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

// ---- 精选集筛选（多选，全不选为全部），写进 ?c=fp,wlm ----
const collections = ref<Collection[]>([]);
function toggleCollection(k: Collection) {
  const on = new Set(collections.value);
  if (!on.delete(k)) on.add(k);
  collections.value = COLLECTION_KEYS.filter((x) => on.has(x));
}
watch(collections, (c) => {
  const url = new URL(location.href);
  if (c.length) url.searchParams.set("c", c.join(","));
  else url.searchParams.delete("c");
  history.replaceState(history.state, "", url);
});

// ---- 缩小地图时：视野里随机的一组样本（放大后换成视野里的全部机位） ----
const RANDOM_COUNT = 24;
const sample = shallowRef<SampleSpot[]>([]);
const bounds = shallowRef<[number, number, number, number] | null>(null);
const shuffleSeed = ref(0);
function inBounds(s: SampleSpot, [w, south, e, n]: [number, number, number, number]) {
  if (s.lat < south || s.lat > n) return false;
  if (e - w >= 360) return true;
  // 经度换算到 [w, w + 360) 再比较，跨过 180° 经线的视野也对
  const lng = ((((s.lng - w) % 360) + 360) % 360) + w;
  return lng <= e;
}
const randomPicks = computed(() => {
  void shuffleSeed.value; // 点「换一批」时重新抽
  const b = bounds.value;
  if (!b) return [];
  const pool = sample.value.filter((s) => inBounds(s, b) && inCollections(s.c, collections.value));
  // 部分 Fisher–Yates：只洗出前 RANDOM_COUNT 个
  for (let i = 0; i < Math.min(RANDOM_COUNT, pool.length); i++) {
    const j = i + Math.floor(Math.random() * (pool.length - i));
    [pool[i], pool[j]] = [pool[j], pool[i]];
  }
  return pool.slice(0, RANDOM_COUNT);
});

// 手机端抽屉：收起 / 半屏 / 全屏（拖动与吸附由 mapette 处理），选中机位时打开到半屏
const sheet = ref<SheetSnap>("half");

// ---- 详情的展示字段 ----
const f = (n: number) => (Number.isInteger(n) ? String(n) : n.toFixed(1).replace(/\.0$/, ""));
const description = computed(() => focus.value && pickDesc(focus.value.desc, locale));

const settings = computed(() => {
  const s = focus.value;
  if (!s) return [];
  const out: { label: string; value: string }[] = [];
  if (s.focal) out.push({ label: t.focal, value: t.focalValue(f(s.focal), s.focal35 && Math.abs(s.focal35 - s.focal) > 1 ? f(s.focal35) : null) });
  if (s.fnumber) out.push({ label: t.aperture, value: `f/${f(s.fnumber)}` });
  if (s.exposure) out.push({ label: t.shutter, value: `${s.exposure} s` });
  if (s.iso) out.push({ label: "ISO", value: String(s.iso) });
  return out;
});
// 地图飞到这个机位，至少放大到街区级别（已经更近就不拉远）；留白由 mapette 处理，机位落在面板外的可见区域中间
const explorer = ref<InstanceType<typeof MapExplorer>>();
function showOnMap(s: Spot) {
  const m = explorer.value?.controller?.map;
  m?.flyTo({ center: [s.lng, s.lat], zoom: Math.max(m.getZoom(), 17), duration: 1200 });
}
const navUrl = (s: Spot) => directions.google(s.lat, s.lng);
const appleUrl = (s: Spot) => directions.apple(s.lat, s.lng);
const coords = (s: Spot) => `${s.lat.toFixed(5)}, ${s.lng.toFixed(5)}`;
const compass = (deg: number) => t.compass[Math.round(deg / 45) % 8];

onMounted(() => {
  loadSample().then((s) => (sample.value = s), () => {});
  fetch("/data/meta.json").then((r) => r.json() as Promise<Meta>).then((m) => (meta.value = m), () => {});
  const query = new URLSearchParams(location.search);
  collections.value = parseCollections(query.get("c"));
  const [id, shard] = (query.get("spot") ?? "").split(".");
  if (Number(id) && shard) void pick({ id: Number(id), shard });
});

// ---- 键盘：Esc 退一层（关掉机位详情；快捷键说明开着时交给它自己关），T 外观，? 快捷键说明 ----
const footer = ref<InstanceType<typeof MapFooter>>();
const shortcuts = {
  Escape: () => {
    if (footer.value?.shortcutsOpen() || !focusRef.value) return false;
    void pick(null);
  },
  t: () => cycleTheme(),
  "?": () => footer.value?.toggleShortcuts(),
};
const SHORTCUTS = computed(() => [{ keys: ["Esc"], label: t.kbBack }, ...baseShortcuts(locale)]);
const SOURCES = [{ label: "Wikimedia Commons", href: "https://commons.wikimedia.org/wiki/Commons:Quality_images" }];
// 开发时不注册 Service Worker（它会缓存 vite 的模块）
const isProd = import.meta.env.PROD;
const switchLocale = (next: Locale) => (location.href = switchLocaleUrl(next));
</script>

<template>
  <MapExplorer
    ref="explorer"
    v-model:snap="sheet"
    :map-style="spotStyle"
    :locale="locale"
    :keep-sources="KEEP_SOURCES"
    :shortcuts="shortcuts"
  >
    <template #map><SpotLayers :focus="focus" :collections="collections" @bounds="(b) => (bounds = b)" @pick="pick" @view="onView" @close="pick(null)" /></template>

    <!-- 标题与筛选只在浏览时显示；打开机位详情时让出位置 -->
    <template v-if="!focus" #header>
      <div class="head">
        <div class="brand">
          <span class="mark"><JIcon :icon="ICONS.camera" /></span>
          <div>
            <h1>{{ t.brand }}</h1>
            <p class="muted stat">
              <template v-if="meta">{{ t.count(meta.count) }}</template>
              <template v-else>{{ t.loading }}</template>
            </p>
          </div>
        </div>
      </div>
      <div class="filters" role="group" :aria-label="t.collectionsLabel">
        <button
          v-for="k in COLLECTION_KEYS"
          :key="k"
          class="chip"
          :class="{ on: collections.includes(k) }"
          :aria-pressed="collections.includes(k)"
          :title="meta?.collections ? `${t.collectionNames[k]} · ${t.collectionCount(meta.collections[k])}` : t.collectionNames[k]"
          @click="toggleCollection(k)"
        >
          {{ t.collections[k] }}
        </button>
      </div>
    </template>

    <div v-if="focus || inView || randomPicks.length" class="body">
      <!-- 机位详情 -->
      <article v-if="focus" class="detail">
        <div class="detail-bar">
          <button class="text-btn" @click="pick(null)">← {{ t.back }}</button>
          <button class="icon-btn" :title="t.close" :aria-label="t.close" @click="pick(null)"><JIcon :icon="ICONS.close" /></button>
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
        <p v-if="focus.featured || focus.contest" class="badges">
          <span v-if="focus.featured" class="badge">{{ t.featured }}</span>
          <span v-if="focus.contest" class="badge">{{ t.contest[focus.contest] }}</span>
        </p>
        <p v-if="description" class="desc" :lang="description.lang">{{ description.text }}</p>

        <dl class="facts">
          <div><dt>{{ t.position }}</dt><dd class="stat">{{ coords(focus) }}</dd></div>
          <div v-if="focus.heading != null">
            <dt>{{ t.heading }}</dt>
            <dd class="stat">{{ t.headingValue(focus.heading, compass(focus.heading), Math.round(fieldOfView(focus.focal35))) }}</dd>
          </div>
          <div v-if="focus.taken"><dt>{{ t.taken }}</dt><dd class="stat">{{ focus.taken }}</dd></div>
          <div v-if="focus.camera"><dt>{{ t.camera }}</dt><dd>{{ focus.camera }}</dd></div>
          <div v-if="focus.lens"><dt>{{ t.lens }}</dt><dd>{{ focus.lens }}</dd></div>
        </dl>
        <ul v-if="settings.length" class="settings">
          <li v-for="x in settings" :key="x.label"><span class="muted">{{ x.label }}</span><b class="stat">{{ x.value }}</b></li>
        </ul>

        <div class="actions">
          <button type="button" class="btn primary" @click="showOnMap(focus)"><JIcon :icon="ICONS.focus" />{{ t.showOnMap }}</button>
          <div class="actions-row">
            <a class="btn" :href="navUrl(focus)" target="_blank" rel="noopener"><JIcon :icon="ICONS.navigate" />{{ t.navigate }}</a>
            <a class="btn" :href="appleUrl(focus)" target="_blank" rel="noopener">{{ t.appleMaps }}</a>
          </div>
        </div>

        <p class="credit muted">
          © {{ focus.artist ?? t.anonymous }} ·
          <a v-if="focus.licenseUrl" :href="focus.licenseUrl" target="_blank" rel="noopener">{{ focus.license }}</a>
          <template v-else>{{ focus.license }}</template>
          · <a :href="focus.page" target="_blank" rel="noopener">Wikimedia Commons <JIcon :icon="ICONS.external" /></a>
        </p>
      </article>

      <!-- 视野里的机位 -->
      <section v-else-if="inView" class="list">
        <p class="muted stat section-title">{{ t.inView(inView.length, inView.length >= 60) }}</p>
        <p v-if="!inView.length" class="muted empty">{{ t.emptyHere }}</p>
        <div class="grid">
          <button v-for="s in inView" :key="s.id" class="thumb" :title="s.title" @click="pick({ id: s.id, shard: s.shard })">
            <img :src="s.small" alt="" loading="lazy" />
            <span>{{ s.title }}</span>
          </button>
        </div>
      </section>

      <!-- 缩小时：视野里随机的一组 -->
      <section v-else class="list">
        <div class="section-head">
          <p class="muted section-title">{{ t.randomInView }}</p>
          <button class="text-btn" @click="shuffleSeed++">{{ t.shuffle }}</button>
        </div>
        <div class="grid">
          <button v-for="s in randomPicks" :key="s.id" class="thumb" :title="s.title" @click="pick({ id: s.id, shard: s.shard })">
            <img :src="s.small" alt="" loading="lazy" />
            <span>{{ s.title }}</span>
          </button>
        </div>
      </section>
    </div>

    <template #footer>
      <MapFooter ref="footer" :locale="locale" :theme-key="THEME_KEY" :sources="SOURCES" :shortcuts="SHORTCUTS" @locale="switchLocale" />
    </template>
  </MapExplorer>
  <!-- 放在面板外面：面板的 backdrop-filter 会让里面 fixed 定位的元素相对面板定位 -->
  <UpdateToast :locale="locale" :register="isProd" />
</template>

<style>
* {
  box-sizing: border-box;
}
html,
body {
  margin: 0;
  height: 100%;
  background: var(--mapette-bg-solid);
  color: var(--mapette-fg);
}
/* 主题色：mapette 默认是茜红，这里换成蓝色（暗色模式用提亮的同色系）。:root:root 保证盖过 mapette.css 的 :root */
:root:root {
  --mapette-accent-light: #3567a8;
  --mapette-accent-dark: #6b97d6;
}
:root {
  font-family: -apple-system, system-ui, "PingFang SC", "Microsoft YaHei UI", "Microsoft YaHei", "Noto Sans SC", "Source Han Sans SC", sans-serif;
}
a {
  color: inherit;
}
* {
  scrollbar-width: thin;
  scrollbar-color: var(--mapette-scroll-thumb) transparent;
}
</style>

<style scoped>
.head {
  flex: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 14px 12px 16px;
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
  background: var(--mapette-accent);
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
  padding: 12px;
}
/* 一行排开；窄屏放不下时横向滑动，不换行 */
.filters {
  display: flex;
  gap: 6px;
  padding: 0 14px 12px 16px;
  overflow-x: auto;
  scrollbar-width: none;
}
.filters .chip {
  flex: none;
  padding: 4px 10px;
  font-size: 12px;
}
.chip.on,
.chip.on:hover {
  color: #fff;
  background: var(--mapette-accent);
}
.muted {
  color: var(--mapette-muted);
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
  color: var(--mapette-muted);
  background: none;
  border: 0;
  border-radius: 8px;
  cursor: pointer;
}
.icon-btn:hover,
.text-btn:hover {
  background: var(--mapette-hover);
  color: var(--mapette-fg);
}
.text-btn {
  padding: 4px 8px;
  margin-left: -6px;
  font: inherit;
  font-size: 13px;
  color: var(--mapette-muted);
  background: none;
  border: 0;
  border-radius: 8px;
  cursor: pointer;
}

.chip {
  padding: 6px 12px;
  font: inherit;
  font-size: 13px;
  color: var(--mapette-fg);
  background: var(--mapette-hover);
  border: 0;
  border-radius: 999px;
  cursor: pointer;
}
.chip:hover {
  background: var(--mapette-line);
}

/* ---- 视野列表 ---- */
.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
.section-head .section-title {
  margin: 0 4px;
}
.section-head .text-btn {
  margin: -4px 0;
  font-size: 12px;
}
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
  color: var(--mapette-fg);
  background: none;
  border: 0;
  cursor: pointer;
}
.thumb img {
  width: 100%;
  aspect-ratio: 4 / 3;
  object-fit: cover;
  border-radius: 8px;
  background: var(--mapette-hover);
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
  outline: 2px solid var(--mapette-accent);
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
  background: var(--mapette-hover);
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
.desc {
  margin: 6px 2px 0;
  font-size: 13px;
  line-height: 1.6;
  overflow-wrap: anywhere;
}
.badges {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin: 2px 2px 0;
}
.badge {
  display: inline-block;
  padding: 2px 8px;
  font-size: 11px;
  color: var(--mapette-accent);
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
  border-bottom: 1px solid var(--mapette-line);
}
.facts dt {
  color: var(--mapette-muted);
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
  background: var(--mapette-hover);
  border-radius: 8px;
}
.settings b {
  font-size: 13px;
  font-weight: 600;
}
/* 主按钮（在地图上查看）占一整行，下面一行是两个外部地图 App */
.actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 14px;
}
.actions-row {
  display: flex;
  gap: 8px;
}
.actions-row .btn {
  flex: 1;
}
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 12px;
  font: inherit;
  font-size: 13px;
  color: inherit;
  text-decoration: none;
  background: var(--mapette-hover);
  border: 0;
  border-radius: 9px;
  cursor: pointer;
}
.btn:hover {
  background: var(--mapette-line);
}
.btn.primary {
  padding: 10px 12px;
  font-weight: 600;
  color: #fff;
  background: var(--mapette-accent);
}
.btn.primary:hover {
  background: linear-gradient(rgb(0 0 0 / 0.08), rgb(0 0 0 / 0.08)), var(--mapette-accent);
}
.credit {
  margin: 14px 2px 4px;
  font-size: 12px;
  line-height: 1.6;
  overflow-wrap: anywhere;
}
</style>
