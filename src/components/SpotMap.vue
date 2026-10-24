<script setup lang="ts">
// 地图：底图、热力图到单点的过渡、比例尺、按钮与照片标记都来自 meisho，这里只有机位自己的数据源和图层
import type { MapGeoJSONFeature, Map as MaplibreMap, PaddingOptions } from "maplibre-gl";
import { type GeoJSONSource } from "maplibre-gl";
import { coneLayers, createBasemap, fieldOfView, focusPointLayer, HEAT_FADE, heatmapLayer, pointLayer, viewCone, type Palette } from "meisho/style";
import { MapControls, MapView, PhotoPins, ScaleBar, useViewportFeatures } from "meisho/vue";
import { shallowRef, watch } from "vue";
import { fetchSpots, type Spot } from "../spots";

export interface SpotRef {
  id: number;
  shard: string;
}

const props = defineProps<{
  focus: Spot | null;
  padding: PaddingOptions;
}>();

const emit = defineEmits<{
  pick: [ref: SpotRef];
  /** 视野里的机位（离中心近的在前）；还在热力图阶段时为 null */
  view: [refs: SpotRef[] | null];
}>();

const RAIL = "pmtiles://https://cdn.jannchie.com/junrei/rail/rail-v4.pmtiles";

function mapStyle(c: Palette) {
  return createBasemap({
    palette: c,
    locale: "zh-Hans",
    rail: RAIL,
    // focus：选中机位的 pageid（0 表示没有选中）
    state: { focus: { default: 0 } },
    sources: {
      // 全部机位：maplibre 在 worker 里抓取、解析，主线程不碰这 12 万个点
      spots: { type: "geojson", data: "/data/spots.geojson" },
      // 选中机位的取景扇形（有朝向时）
      cone: { type: "geojson", data: { type: "FeatureCollection", features: [] } },
    },
    belowLabels: [heatmapLayer({ source: "spots", palette: c })],
    overlays: [
      ...coneLayers({ source: "cone", palette: c }),
      pointLayer({ source: "spots", palette: c }),
      focusPointLayer({ source: "spots", palette: c, filter: ["==", ["get", "i"], ["global-state", "focus"]] }),
    ],
  });
}

const map = shallowRef<MaplibreMap | null>(null);
const toRef = (f: MapGeoJSONFeature): SpotRef => ({ id: Number(f.properties.i), shard: String(f.properties.s) });

function onLoad(m: MaplibreMap) {
  map.value = m;
  if (import.meta.env.DEV) {
    Object.assign(window, { __map: m }); // 调试用
    m.on("error", (e) => console.error("[map]", e.error));
  }
  m.on("style.load", syncFocus);
  // 热力图阶段没有可点的机位：点击地图即以该处为中心放大两级
  m.on("click", (e) => {
    if (m.getZoom() < HEAT_FADE[0]) m.easeTo({ center: e.lngLat, zoom: m.getZoom() + 2 });
  });
  m.on("click", "point", (e) => {
    const f = e.features?.[0];
    if (f) pick(toRef(f));
  });
  m.on("mouseenter", "point", () => (m.getCanvas().style.cursor = "pointer"));
  m.on("mouseleave", "point", () => (m.getCanvas().style.cursor = ""));
}

// 在地图上直接点的机位就在眼前，镜头不动；从列表或链接选中的才移过去
let pickedOnMap = 0;
function pick(r: SpotRef) {
  pickedOnMap = r.id;
  emit("pick", r);
}

function syncFocus() {
  const m = map.value;
  const spot = props.focus;
  if (!m?.getSource("cone")) return;
  m.setGlobalStateProperty("focus", spot?.id ?? 0);
  (m.getSource("cone") as GeoJSONSource).setData({
    type: "FeatureCollection",
    features: spot?.heading != null ? [viewCone(spot.lng, spot.lat, spot.heading, fieldOfView(spot.focal35))] : [],
  });
}
watch(() => props.focus, (spot) => {
  syncFocus();
  if (spot && spot.id !== pickedOnMap) map.value?.easeTo({ center: [spot.lng, spot.lat], zoom: Math.max(map.value.getZoom(), 16), duration: 800 });
});

// 视野里的机位交给面板列出来
const visible = useViewportFeatures(map, { layers: ["point"], source: "spots", minZoom: HEAT_FADE[0], limit: 60, featureKey: (f) => Number(f.properties.i) });
watch(visible, (v) => emit("view", v && v.map((x) => toRef(x.feature))));

// 照片标记：按分片取样片地址
async function images(features: MapGeoJSONFeature[]) {
  const spots = new Map((await fetchSpots(features.map(toRef))).map((s) => [s.id, s.small]));
  return features.map((f) => spots.get(Number(f.properties.i)) ?? null);
}

defineExpose({
  flyTo: (center: [number, number], zoom: number) => map.value?.flyTo({ center, zoom, duration: 1600 }),
});
</script>

<template>
  <MapView :map-style="mapStyle" :keep-sources="['spots', 'cone']" :padding="padding" @load="onLoad">
    <ScaleBar />
    <MapControls :labels="{ locate: '定位', zoomIn: '放大', zoomOut: '缩小' }" />
    <PhotoPins
      :layers="['point']"
      :feature-key="(f) => Number(f.properties.i)"
      :images="images"
      :focus="focus?.id ?? null"
      :min-zoom="15.5"
      :max="24"
      @pick="(f) => pick(toRef(f))"
    />
  </MapView>
</template>
