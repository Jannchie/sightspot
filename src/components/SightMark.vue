<script setup lang="ts">
// 页面里的 Sightspot 标志：只有图形、没有底板，颜色跟随 currentColor（图形在 src/logo.ts，与 PWA 图标相同）
import { markShapes } from "../logo";

withDefaults(defineProps<{ size?: number }>(), { size: 34 });
const shapes = markShapes({ color: "currentColor", id: "sightspot-mark" });
</script>

<template>
  <!-- eslint-disable-next-line vue/no-v-html -- 图形来自本地常量，不含外部输入 -->
  <svg :width="size" :height="size" viewBox="0 0 100 100" aria-hidden="true" v-html="shapes" />
</template>
