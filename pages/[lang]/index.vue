<script setup lang="ts">
import SpotApp from "../../src/components/SpotApp.vue";
import type { Props } from "./index.server";

defineProps<Props>();
</script>

<template>
  <SpotApp :lang="lang" />
</template>
