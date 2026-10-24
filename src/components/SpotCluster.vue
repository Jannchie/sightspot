<script setup lang="ts">
// 气泡弹出卡片的内容（ClusterPopover 的插槽）：气泡里机位的样片缩略图，点一张就选中那个机位。
import type { Feature } from "geojson";
import { shallowRef, watch } from "vue";
import { fetchSpots, type Spot } from "../spots";
import type { SpotRef } from "./SpotLayers.vue";

const props = defineProps<{ features: Feature[]; count: number }>();
const emit = defineEmits<{ pick: [ref: SpotRef]; zoomIn: [] }>();

const SHOW = 9;
const spots = shallowRef<Spot[]>([]);
watch(() => props.features, async (fs) => {
  const refs = fs.slice(0, SHOW).map((f) => ({ id: Number(f.properties?.i), shard: String(f.properties?.s) }));
  const got = await fetchSpots(refs).catch(() => []);
  if (fs === props.features) spots.value = got;
}, { immediate: true });
</script>

<template>
  <div class="spot-cluster">
    <div class="head">{{ count.toLocaleString() }} 个机位</div>
    <div class="grid">
      <button v-for="s in spots" :key="s.id" type="button" :title="s.title" @click="emit('pick', { id: s.id, shard: s.shard })">
        <img :src="s.small" alt="" loading="lazy" />
      </button>
    </div>
    <div class="foot">
      <span v-if="count > spots.length" class="more">另有 {{ (count - spots.length).toLocaleString() }} 个</span>
      <button type="button" @click="emit('zoomIn')">放大查看</button>
    </div>
  </div>
</template>

<style scoped>
.spot-cluster {
  width: 252px;
  font-size: 13px;
}
.head {
  padding: 10px 40px 8px 12px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
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
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 8px 8px 12px;
}
.more {
  font-size: 12px;
  color: var(--mapette-muted);
  font-variant-numeric: tabular-nums;
}
.foot button {
  margin-left: auto;
  padding: 4px 10px;
  font: inherit;
  font-size: 12px;
  color: var(--mapette-fg);
  background: var(--mapette-hover);
  border: 0;
  border-radius: 999px;
  cursor: pointer;
}
</style>
