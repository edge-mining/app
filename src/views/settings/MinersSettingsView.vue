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

  <!-- <div>
    <span v-for="value in minerStore.miners" :key="value.id">{{
      value.name
    }}</span>
  </div> -->

  <div class="stats shadow" v-for="miner in minerStore.miners" :key="miner.id">
    <div class="stat">
      <div class="stat-title">{{ miner.name }}</div>
      <div class="stat-value">
        {{ miner.hash_rate?.value }} {{ miner.hash_rate?.unit }}
      </div>
      <div class="stat-desc">{{ miner.status }}</div>
      <div class="stat-desc">{{ miner.power_consumption }} Watts</div>
    </div>
  </div>

  <div
    class="card bg-base-100 w-96 shadow-sm"
    v-for="miner in minerStore.miners"
    :key="miner.id"
  >
    <div class="card-body">
      <h2 class="card-title">{{ miner.name }}</h2>
      <p>{{ miner.hash_rate?.value }} {{ miner.hash_rate?.unit }}</p>
      <p>{{ miner.status }}</p>
      <p>{{ miner.power_consumption }} Watts</p>
      <!-- <div class="card-actions justify-end">
        <button class="btn btn-primary">Buy Now</button>
      </div> -->
    </div>
  </div>
</template>

<style scoped></style>
