<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useMinerStore } from "../../core/stores/minerStore";
import MinerRow from "../../components/miners/MinerRow.vue";
import type { Miner } from "../../core/models/miner";
import MinerRowEdit from "../../components/miners/MinerRowEdit.vue";

const minerStore = useMinerStore();
const newMiner = ref<Miner | undefined>(undefined);

onMounted(() => {
  minerStore.loadMiners();
});

function addMiner() {
  newMiner.value = {
    name: "",
    status: "",
    active: false,
    hash_rate_max: { value: 100, unit: "TH/s" },
    power_consumption_max: 3000,
  };
}

function confirmAdd() {
  minerStore.addMiner(newMiner.value!).then(() => {
    minerStore.loadMiners();
    newMiner.value = undefined;
  });
}
</script>

<template>
  <h1 class="text-3xl font-bold">Miners settings</h1>

  <div class="overflow-x-auto">
    <table class="table">
      <!-- head -->
      <thead>
        <tr>
          <th>
            <!-- <label>
              <input type="checkbox" class="checkbox" />
            </label> -->
          </th>
          <th>Name</th>
          <th>Status</th>
          <th>Hash Rate (Max)</th>
          <th>Power Consumption (Max)</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <template v-for="(miner, i) in minerStore.miners" :key="miner.id">
          <MinerRow v-model="minerStore.miners[i]" />
        </template>

        <MinerRowEdit v-if="newMiner" v-model="newMiner" edit />

        <tr>
          <th colspan="5" class="text-center">
            <button v-if="!newMiner" class="btn btn-primary" @click="addMiner">
              Add Miner
            </button>
            <template v-else>
              <button class="btn btn-primary mr-4" @click="confirmAdd">
                OK
              </button>
              <button class="btn btn-secondary" @click="newMiner = undefined">
                Cancel
              </button>
            </template>
          </th>
        </tr>
      </tbody>
      <!-- foot -->
      <tfoot>
        <tr>
          <th></th>
          <th>Name</th>
          <th>Status</th>
          <th>Hash Rate (Max)</th>
          <th>Power Consumption (Max)</th>
          <th></th>
        </tr>
      </tfoot>
    </table>
  </div>
</template>

<style scoped></style>
