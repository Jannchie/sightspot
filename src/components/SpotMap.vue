<script setup lang="ts">
// 地图部分的骨架来自 junrei 的 PilgrimMap.vue：同一套样式、热力图到单点的过渡、比例尺、放大后显示照片标记
import { JIcon } from "@jannchie/icons-vue";
import type { Feature, Point, Polygon } from "geojson";
import maplibregl, { type GeoJSONSource, type PaddingOptions } from "maplibre-gl";
import { Protocol } from "pmtiles";
import "maplibre-gl/dist/maplibre-gl.css";
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import { ICONS } from "../icons";
import { CJK_FONT_FAMILY, createStyle, HEAT_FADE, readPalette } from "../map-style";
import { fetchSpots, fieldOfView, type Spot } from "../spots";
import { isDark } from "../theme";

export interface SpotRef {
  id: number;
  shard: string;
}

const props = defineProps<{
  focus: Spot | null;
  /** 被浮层面板挡住的边距，地图的可视中心会避开它 */
  padding: PaddingOptions;
}>();

const emit = defineEmits<{
  pick: [ref: SpotRef];
  /** 视野里的机位（离中心近的在前）；还在热力图阶段时为 null */
  view: [refs: SpotRef[] | null];
}>();

const el = ref<HTMLDivElement>();
let map: maplibregl.Map | null = null;
let geolocate: maplibregl.GeolocateControl | null = null;
const ready = ref(false);

defineExpose({
  flyTo: (center: [number, number], zoom: number) => map?.flyTo({ center, zoom, duration: 1600 }),
});

// 换主题只换颜色：两个 geojson 源沿用当前的定义，否则 diff 会把它们当成新源，重新加载 12 万个点
function restyle() {
  map?.setStyle(createStyle(readPalette(), "zh-Hans"), {
    transformStyle: (prev, next) => ({
      ...next,
      sources: { ...next.sources, spots: prev!.sources.spots, cone: prev!.sources.cone },
    }),
  });
}

// ---- 比例尺（同 junrei）----
const SCALE_MAX = 100;
const scale = ref<{ width: number; label: string } | null>(null);
function updateScale() {
  if (!map) return;
  const mpp = (40075016.686 * Math.cos((map.getCenter().lat * Math.PI) / 180)) / (512 * 2 ** map.getZoom());
  const pow = 10 ** Math.floor(Math.log10(mpp * SCALE_MAX));
  const meters = [5, 2, 1].map((f) => f * pow).find((d) => d / mpp <= SCALE_MAX) ?? pow;
  scale.value = { width: Math.round(meters / mpp), label: meters >= 1000 ? `${meters / 1000} km` : `${meters} m` };
}

// ---- 取景扇形：以机位为顶点、沿拍摄朝向张开，角度取自等效焦距 ----
const CONE_RADIUS = 160; // 米
function cone(spot: Spot): Feature<Polygon> {
  const fov = fieldOfView(spot);
  const ring: [number, number][] = [[spot.lng, spot.lat]];
  const mPerDegLat = 111_320;
  const mPerDegLng = 111_320 * Math.cos((spot.lat * Math.PI) / 180);
  for (let k = 0; k <= 24; k++) {
    const bearing = ((spot.heading! - fov / 2 + (fov * k) / 24) * Math.PI) / 180;
    ring.push([spot.lng + (CONE_RADIUS * Math.sin(bearing)) / mPerDegLng, spot.lat + (CONE_RADIUS * Math.cos(bearing)) / mPerDegLat]);
  }
  ring.push([spot.lng, spot.lat]);
  return { type: "Feature", geometry: { type: "Polygon", coordinates: [ring] }, properties: {} };
}

function syncFocus() {
  if (!ready.value || !map) return;
  const spot = props.focus;
  map.setGlobalStateProperty("focus", spot?.id ?? 0);
  (map.getSource("cone") as GeoJSONSource).setData({
    type: "FeatureCollection",
    features: spot?.heading != null ? [cone(spot)] : [],
  });
  for (const [id, marker] of photoMarkers) marker.getElement().classList.toggle("focus", id === spot?.id);
}

// 在地图上直接点的机位就在眼前，镜头不动；从列表或链接选中的才移过去
let pickedOnMap = 0;
function syncCamera() {
  const spot = props.focus;
  if (!ready.value || !map || !spot) return;
  if (spot.id === pickedOnMap) return;
  map.setPadding(usablePadding());
  map.easeTo({ center: [spot.lng, spot.lat], zoom: Math.max(map.getZoom(), 16), duration: 800 });
}

/** 面板挡住的留白，但至少给地图留出 200px 见方 */
function usablePadding(): PaddingOptions {
  const p = props.padding;
  const c = map?.getContainer();
  if (!c) return p;
  const room = (size: number, a: number, b: number) => Math.max(0, Math.min(a, size - 200 - b));
  return { ...p, bottom: room(c.clientHeight, p.bottom, p.top), left: room(c.clientWidth, p.left, p.right) };
}

// ---- 视野里的机位，交给面板列出来 ----
const VIEW_MAX = 60;
function visibleRefs(m: maplibregl.Map): (SpotRef & { d: number; x: number; y: number; lngLat: [number, number] })[] {
  const center = m.project(m.getCenter());
  const seen = new Set<number>();
  const out = [];
  for (const f of m.queryRenderedFeatures({ layers: ["point"] })) {
    const { i, s } = f.properties as { i: number; s: string };
    if (seen.has(i)) continue;
    seen.add(i);
    const lngLat = (f.geometry as Point).coordinates as [number, number];
    const { x, y } = m.project(lngLat);
    out.push({ id: Number(i), shard: String(s), d: Math.hypot(x - center.x, y - center.y), x, y, lngLat });
  }
  return out.sort((a, b) => a.d - b.d);
}

// ---- 放大到街区级别时，视野里的机位直接显示样片（同 junrei 的截图标记）----
const PHOTO_ZOOM = 15.5;
const PHOTO_MAX = 24;
const PHOTO_GAP = 120;
const photoMarkers = new Map<number, maplibregl.Marker>();
let photoSeq = 0;

async function syncView() {
  const m = map;
  if (!m) return;
  const seq = ++photoSeq;
  if (m.getZoom() < HEAT_FADE[0]) {
    emit("view", null);
    clearPhotos();
    return;
  }
  const refs = visibleRefs(m);
  emit("view", refs.slice(0, VIEW_MAX).map(({ id, shard }) => ({ id, shard })));
  if (m.getZoom() < PHOTO_ZOOM) {
    clearPhotos();
    return;
  }
  // 按屏幕位置挑出互不重叠的机位
  const picked: typeof refs = [];
  for (const r of refs) {
    if (picked.some((q) => Math.hypot(q.x - r.x, q.y - r.y) < PHOTO_GAP)) continue;
    picked.push(r);
    if (picked.length >= PHOTO_MAX) break;
  }
  const spots = new Map((await fetchSpots(picked)).map((s) => [s.id, s]));
  if (seq !== photoSeq) return;
  const keep = new Set<number>();
  for (const r of picked) {
    const spot = spots.get(r.id);
    if (!spot) continue;
    keep.add(r.id);
    if (photoMarkers.has(r.id)) continue;
    const pin = document.createElement("button");
    pin.className = props.focus?.id === r.id ? "photo-pin focus" : "photo-pin";
    pin.setAttribute("aria-label", spot.title);
    const img = document.createElement("img");
    img.alt = "";
    img.loading = "lazy";
    img.addEventListener("error", () => (pin.style.display = "none"));
    img.src = spot.small;
    pin.append(img);
    pin.addEventListener("click", (ev) => {
      ev.stopPropagation();
      pickedOnMap = r.id;
      emit("pick", { id: r.id, shard: r.shard });
    });
    photoMarkers.set(r.id, new maplibregl.Marker({ element: pin, anchor: "bottom", offset: [0, -8] }).setLngLat(r.lngLat).addTo(m));
  }
  for (const [id, marker] of photoMarkers) {
    if (!keep.has(id)) {
      marker.remove();
      photoMarkers.delete(id);
    }
  }
}

function clearPhotos() {
  for (const marker of photoMarkers.values()) marker.remove();
  photoMarkers.clear();
}

let pmtilesAdded = false;

onMounted(() => {
  if (!pmtilesAdded) {
    maplibregl.addProtocol("pmtiles", new Protocol().tile);
    pmtilesAdded = true;
  }
  const m = (map = new maplibregl.Map({
    container: el.value!,
    style: createStyle(readPalette(), "zh-Hans"),
    center: [10, 35],
    zoom: 2,
    hash: "map",
    padding: usablePadding(),
    localIdeographFontFamily: CJK_FONT_FAMILY,
    attributionControl: false, // 署名放在面板底部
    maxTileCacheZoomLevels: 10,
    fadeDuration: 150,
  }));
  if (import.meta.env.DEV) {
    Object.assign(window, { __map: m });
    m.on("error", (e) => console.error("[map]", e.error));
  }

  geolocate = new maplibregl.GeolocateControl({ positionOptions: { enableHighAccuracy: true }, trackUserLocation: true });
  m.addControl(geolocate, "bottom-right");
  m.on("move", updateScale);
  updateScale();

  m.on("style.load", () => {
    ready.value = true;
    syncFocus();
    syncCamera();
  });

  // 热力图阶段没有可点的机位：点击地图即以该处为中心放大两级
  m.on("click", (e) => {
    if (m.getZoom() >= HEAT_FADE[0]) return;
    m.easeTo({ center: e.lngLat, zoom: m.getZoom() + 2 });
  });
  m.on("click", "point", (e) => {
    const p = e.features?.[0]?.properties;
    if (!p) return;
    pickedOnMap = Number(p.i);
    emit("pick", { id: Number(p.i), shard: String(p.s) });
  });
  m.on("mouseenter", "point", () => (m.getCanvas().style.cursor = "pointer"));
  m.on("mouseleave", "point", () => (m.getCanvas().style.cursor = ""));
  m.on("moveend", syncView);
  // 机位数据在 worker 里解析完才渲染得出来，首次统计要等数据就绪后的第一次 idle
  m.on("sourcedata", function onData(e) {
    if (e.sourceId === "spots" && e.isSourceLoaded) {
      m.off("sourcedata", onData);
      m.once("idle", syncView);
    }
  });
});

onBeforeUnmount(() => {
  clearPhotos();
  map?.remove();
});

watch(isDark, restyle);
watch(() => props.padding, () => {
  if (!map) return;
  if (map.isMoving()) map.once("moveend", () => map?.setPadding(usablePadding()));
  else map.setPadding(usablePadding());
});
watch(() => props.focus, () => {
  syncFocus();
  syncCamera();
});
</script>

<template>
  <div ref="el" class="map" />
  <div v-if="scale" class="scale" :style="{ '--pad-left': `${padding.left ?? 0}px` }" aria-hidden="true">
    <span class="scale-bar" :style="{ width: `${scale.width}px` }"><i /><i /><i /><i /></span>
    <span>{{ scale.label }}</span>
  </div>
  <div class="controls">
    <button title="定位" aria-label="定位" @click="geolocate?.trigger()"><JIcon :icon="ICONS.locate" /></button>
    <div class="group">
      <button title="放大" aria-label="放大" @click="map?.zoomIn()"><JIcon :icon="ICONS.zoomIn" /></button>
      <button title="缩小" aria-label="缩小" @click="map?.zoomOut()"><JIcon :icon="ICONS.zoomOut" /></button>
    </div>
  </div>
</template>

<style scoped>
.map {
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 60% 50%, var(--map-horizon), var(--map-space) 70%);
}
.map :deep(.maplibregl-ctrl-geolocate) {
  display: none;
}
.scale {
  position: absolute;
  left: calc(var(--pad-left, 0px) + 12px);
  bottom: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  font-size: 11px;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
  color: var(--fg);
  background: var(--bg);
  border-radius: 8px;
  box-shadow: var(--shadow);
  backdrop-filter: var(--glass);
  pointer-events: none;
}
.scale-bar {
  display: flex;
  height: 5px;
  border: 1px solid var(--fg);
  box-sizing: content-box;
}
.scale-bar i {
  flex: 1;
  background: var(--fg);
}
.scale-bar i:nth-child(even) {
  background: var(--bg-solid);
}
@media (max-width: 640px) {
  .scale {
    top: calc(env(safe-area-inset-top) + 10px);
    bottom: auto;
    left: 50%;
    transform: translateX(-50%);
  }
}
.map :deep(.photo-pin) {
  display: block;
  width: 112px;
  height: 76px;
  padding: 3px;
  background: #ffffff;
  border: 0;
  border-radius: 10px;
  box-shadow: 0 1px 4px rgb(0 0 0 / 0.18);
  cursor: pointer;
}
.map :deep(.maplibregl-marker:has(.photo-pin.focus)) {
  z-index: 1;
}
.map :deep(.photo-pin.focus),
.map :deep(.photo-pin.focus)::after {
  background: var(--accent);
}
.map :deep(.photo-pin)::after {
  content: "";
  position: absolute;
  left: 50%;
  bottom: -6px;
  width: 12px;
  height: 12px;
  background: #ffffff;
  transform: translateX(-50%) rotate(45deg);
  border-radius: 0 0 2px 0;
}
.map :deep(.photo-pin img) {
  position: relative;
  z-index: 1;
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 7px;
  background: #e5e7eb;
}
.controls {
  position: absolute;
  right: 12px;
  bottom: calc(var(--panel-inset-bottom, 0px) + 36px);
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.group {
  display: flex;
  flex-direction: column;
}
.controls button {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  padding: 0;
  color: var(--fg);
  background: var(--bg);
  border: 0;
  border-radius: 10px;
  box-shadow: var(--shadow);
  backdrop-filter: var(--glass);
  cursor: pointer;
}
.group button:first-child {
  border-radius: 10px 10px 0 0;
  box-shadow: var(--shadow), inset 0 -0.5px 0 var(--line);
}
.group button:last-child {
  border-radius: 0 0 10px 10px;
}
.controls button:hover {
  background: var(--hover);
}
</style>
