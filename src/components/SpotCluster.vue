<script setup lang="ts">
// 气泡弹出菜单的内容（ClusterPopover 的插槽）：气泡里全部机位的样片缩略图，滚到底再加载下一批，点一张就选中那个机位。
// 样片地址在 CDN 上的静态分片里（按空间分片，同一片区域的机位多半在同一两个文件里），按批取不会给服务器添负担。
import type { Feature } from "geojson";
import { computed, onBeforeUnmount, ref, shallowRef, watch } from "vue";
import { useI18n } from "../i18n";
import { fetchSpots, type Spot } from "../spots";
import type { SpotRef } from "./SpotLayers.vue";

const props = defineProps<{ features: Feature[]; count: number }>();
const emit = defineEmits<{ pick: [ref: SpotRef] }>();

const { t } = useI18n();
const PAGE = 24;
const refs = computed(() => props.features.map((f) => ({ id: Number(f.properties?.i), shard: String(f.properties?.s) })));
const spots = shallowRef<Spot[]>([]);
let loading = false;

async function more() {
  const all = refs.value;
  if (loading || spots.value.length >= all.length) return;
  loading = true;
  const got = await fetchSpots(all.slice(spots.value.length, spots.value.length + PAGE)).catch(() => []);
  loading = false;
  if (all !== refs.value) return;
  spots.value = [...spots.value, ...got];
}
watch(refs, () => {
  spots.value = [];
  void more();
}, { immediate: true });

// 底部的哨兵进入可见区域（菜单滚到底）就加载下一批
const sentinel = ref<HTMLElement>();
let observer: IntersectionObserver | undefined;
watch(sentinel, (el) => {
  observer?.disconnect();
  if (!el) return;
  observer = new IntersectionObserver((entries) => entries.some((e) => e.isIntersecting) && void more(), { rootMargin: "120px" });
  observer.observe(el);
});
onBeforeUnmount(() => observer?.disconnect());
</script>

<template>
  <div class="spot-cluster">
    <div class="head">{{ t.spots(count) }}</div>
    <div class="grid">
      <button v-for="s in spots" :key="s.id" type="button" :title="s.title" @click="emit('pick', { id: s.id, shard: s.shard })">
        <img :src="s.small" alt="" loading="lazy" />
      </button>
    </div>
    <div v-if="spots.length < refs.length" ref="sentinel" class="foot">{{ spots.length }} / {{ refs.length }}</div>
  </div>
</template>

<style scoped>
.spot-cluster {
  width: 252px;
  padding-bottom: 8px;
  font-size: 13px;
}
/* 吸顶：照片多时卡片在 mapette 的 .mapette-popover-body 里滚动，数量一直看得到 */
.head {
  position: sticky;
  top: 0;
  z-index: 1;
  padding: 10px 40px 8px 12px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  background: var(--mapette-bg-solid);
}
.grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 4px;
  padding: 0 8px;
}
.grid button {
  padding: 0;
  background: none;
  border: 0;
  cursor: pointer;
}
.grid img {
  display: block;
  width: 100%;
  aspect-ratio: 1;
  object-fit: cover;
  border-radius: 6px;
  background: var(--mapette-hover);
}
.grid button:hover img {
  outline: 2px solid var(--mapette-accent);
}
.foot {
  padding: 8px 12px 0;
  font-size: 12px;
  color: var(--mapette-muted);
  font-variant-numeric: tabular-nums;
  text-align: center;
}
</style>
