<script setup lang="ts">
// 放在 MapExplorer 的 #map 插槽里：机位的点击、选中状态、取景扇形、视野列表与照片标记。
// 底图、比例尺、按钮、面板与键盘操作都由 mapette 的 MapExplorer 提供。
import { fieldOfView, viewCone } from "@mapette/core";
import { ClusterPopover, MapPopover, PhotoPins, useMap, useViewportFeatures } from "@mapette/vue";
import type { GeoJSONSource, MapGeoJSONFeature } from "maplibre-gl";
import { computed, watch } from "vue";
import { fetchSpots, type Spot } from "../spots";
import SpotCluster from "./SpotCluster.vue";

export interface SpotRef {
  id: number;
  shard: string;
}

const props = defineProps<{ focus: Spot | null }>();

const emit = defineEmits<{
  pick: [ref: SpotRef];
  /** 视野里的机位（离中心近的在前）；缩得太小时为 null */
  view: [refs: SpotRef[] | null];
  /** 关掉地图上的弹出卡片（取消选中） */
  close: [];
}>();

const { controller } = useMap();
const toRef = (f: MapGeoJSONFeature): SpotRef => ({ id: Number(f.properties.i), shard: String(f.properties.s) });

// 在地图上直接点的机位就在眼前，镜头不动；从列表或链接选中的看不到时才平移过去
let pickedOnMap = 0;
function pick(r: SpotRef) {
  pickedOnMap = r.id;
  emit("pick", r);
}

watch(controller, (ctrl) => {
  if (!ctrl) return;
  const m = ctrl.map;
  if (import.meta.env.DEV) {
    Object.assign(window, { __map: m }); // 调试用
    m.on("error", (e) => console.error("[map]", e.error));
  }
  ctrl.onStyleLoad(syncFocus); // 首次加载与换主题后重新应用选中状态
  m.on("click", "point", (e) => {
    const f = e.features?.[0];
    if (f) pick(toRef(f));
  });
  m.on("mouseenter", "point", () => (m.getCanvas().style.cursor = "pointer"));
  m.on("mouseleave", "point", () => (m.getCanvas().style.cursor = ""));
}, { immediate: true });

function syncFocus() {
  const m = controller.value?.map;
  const spot = props.focus;
  if (!m?.getSource("cone")) return;
  (m.getSource("focus") as GeoJSONSource).setData({
    type: "FeatureCollection",
    features: spot ? [{ type: "Feature", geometry: { type: "Point", coordinates: [spot.lng, spot.lat] }, properties: {} }] : [],
  });
  (m.getSource("cone") as GeoJSONSource).setData({
    type: "FeatureCollection",
    features: spot?.heading != null ? [viewCone(spot.lng, spot.lat, spot.heading, fieldOfView(spot.focal35))] : [],
  });
}
// 从列表或链接选中：看不到就平移过去，不改缩放
watch(() => props.focus, (spot) => {
  syncFocus();
  if (spot && spot.id !== pickedOnMap) controller.value?.reveal([spot.lng, spot.lat]);
});

// 视野里的机位交给面板列出来
// 缩得太小时单个机位很少（大多在气泡里），不列
const visible = useViewportFeatures(controller, { layers: ["point"], source: "spots", minZoom: 11, limit: 60, featureKey: (f) => Number(f.properties.i) });
watch(visible, (v) => emit("view", v && v.map((x) => toRef(x.feature))));

// 选中机位的弹出卡片：样片、标题与拍摄参数，详情仍在面板里
const popoverAt = computed<[number, number] | null>(() => (props.focus ? [props.focus.lng, props.focus.lat] : null));
const shot = computed(() => {
  const s = props.focus;
  if (!s) return "";
  const n = (v: number) => (Number.isInteger(v) ? String(v) : v.toFixed(1));
  return [s.focal35 ? `${n(s.focal35)}mm` : s.focal ? `${n(s.focal)}mm` : null, s.fnumber ? `f/${n(s.fnumber)}` : null, s.exposure ? `${s.exposure}s` : null, s.iso ? `ISO ${s.iso}` : null]
    .filter(Boolean)
    .join(" · ");
});

// 照片标记：按分片取样片地址
async function images(features: MapGeoJSONFeature[]) {
  const spots = new Map((await fetchSpots(features.map(toRef))).map((s) => [s.id, s.small]));
  return features.map((f) => spots.get(Number(f.properties.i)) ?? null);
}
</script>

<template>
  <!-- 点气泡：不放大，弹出卡片显示里面机位的样片 -->
  <ClusterPopover source="spots">
    <template #default="{ features, count, close }">
      <SpotCluster :features="features" :count="count" @pick="(r) => { close(); emit('pick', r); }" />
    </template>
  </ClusterPopover>
  <PhotoPins
    :layers="['point']"
    :feature-key="(f) => Number(f.properties.i)"
    :images="images"
    :focus="focus?.id ?? null"
    :min-zoom="15.5"
    :max="24"
    @pick="(f) => pick(toRef(f))"
  />
  <MapPopover :lng-lat="popoverAt" @close="emit('close')">
    <div v-if="focus" class="spot-pop">
      <img :src="focus.small" alt="" :style="{ aspectRatio: `${focus.w} / ${focus.h}` }" />
      <div class="spot-pop-text">
        <strong>{{ focus.title }}</strong>
        <span v-if="shot" class="spot-pop-shot">{{ shot }}</span>
      </div>
    </div>
  </MapPopover>
</template>

<style scoped>
.spot-pop {
  width: 240px;
  overflow: hidden;
  border-radius: inherit;
}
.spot-pop img {
  display: block;
  width: 100%;
  max-height: 180px;
  object-fit: cover;
  background: var(--mapette-hover);
}
.spot-pop-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px 10px 10px;
  font-size: 13px;
  line-height: 1.4;
}
.spot-pop-text strong {
  font-weight: 600;
  overflow-wrap: anywhere;
}
.spot-pop-shot {
  font-size: 12px;
  color: var(--mapette-muted);
  font-variant-numeric: tabular-nums;
}
</style>
