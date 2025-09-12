<script setup lang="ts">
import { onMounted } from "vue";
import { useMinerStore } from "../../core/stores/minerStore";

const minerStore = useMinerStore();

onMounted(() => {
  minerStore.loadMiners();
});
</script>

<template>
  <h1 class="text-3xl font-bold underline">Hello Miners settings!</h1>

  <div>
    <span v-for="value in minerStore.miners" :key="value.id">{{
      value.name
    }}</span>
  </div>
</template>

<style scoped></style>
