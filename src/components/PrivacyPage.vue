<script setup lang="ts">
// 隐私政策页：静态文字（src/privacy.ts），按页面语言显示
import { localePath, type Locale } from "@mapette/core";
import { ISSUES, PRIVACY, PRIVACY_UPDATED } from "../privacy";
import SightMark from "./SightMark.vue";
import "@mapette/core/mapette.css";

const props = defineProps<{ lang: Locale }>();
const text = PRIVACY[props.lang];
</script>

<template>
  <main class="privacy">
    <a class="brand" :href="localePath(lang, '/')"><SightMark :size="24" /><span>Sightspot</span></a>
    <h1>{{ text.title }}</h1>
    <p class="muted">{{ text.updated }} {{ PRIVACY_UPDATED }}</p>
    <p>{{ text.intro }}</p>
    <section v-for="[title, body] in text.items" :key="title">
      <h2>{{ title }}</h2>
      <p>{{ body }}</p>
    </section>
    <p>{{ text.contact }}：<a :href="ISSUES">{{ ISSUES }}</a></p>
  </main>
</template>

<style scoped>
.privacy {
  max-width: 680px;
  margin: 0 auto;
  padding: 32px 16px 64px;
  line-height: 1.7;
  font-family: -apple-system, system-ui, "PingFang SC", "Microsoft YaHei UI", sans-serif;
}
.brand {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  text-decoration: none;
  color: var(--mapette-accent);
}
h1 {
  margin: 24px 0 4px;
  font-size: 28px;
}
h2 {
  margin: 24px 0 4px;
  font-size: 17px;
}
p {
  margin: 8px 0;
}
.muted {
  color: var(--mapette-muted);
  font-size: 14px;
}
a {
  color: var(--mapette-accent);
}
</style>

<style>
:root:root {
  --mapette-accent-light: #3567a8;
  --mapette-accent-dark: #6b97d6;
}
html,
body {
  margin: 0;
  background: var(--mapette-bg-solid);
  color: var(--mapette-fg);
}
</style>
