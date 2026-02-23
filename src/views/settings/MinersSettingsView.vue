<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import { useMinerStore } from "../../core/stores/minerStore";
import { useMinerControllerStore } from "../../core/stores/minerControllerStore";
import MinerRow from "../../components/miners/MinerRow.vue";
import type { Miner } from "../../core/models/miner";
import MinerRowEdit from "../../components/miners/MinerRowEdit.vue";

const minerStore = useMinerStore();
const minerControllerStore = useMinerControllerStore();
const newMiner = ref<Miner | undefined>(undefined);
const editingMiner = ref<{ index: number; miner: Miner } | undefined>(
  undefined,
);
let statusInterval: number | undefined;

async function refreshMinersStatus() {
  const activeMiners = minerStore.miners.filter(
    (miner) => miner.id != null && miner.active,
  );
  if (activeMiners.length > 0) {
    const statusPromises = activeMiners.map((miner) =>
      minerStore.getMinerStatus(miner.id!.toString()),
    );

    await Promise.all(statusPromises);
  }
}

onMounted(async () => {
  await minerStore.loadMiners();
  minerControllerStore.loadMinerControllers();

  // Refresh status for all miners on mount
  await refreshMinersStatus();

  // Set up interval to refresh status every 5 seconds
  statusInterval = window.setInterval(() => {
    refreshMinersStatus();
  }, 2000);
});

onUnmounted(() => {
  // Clear interval when component is unmounted
  if (statusInterval !== undefined) {
    clearInterval(statusInterval);
  }
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

function handleEdit(miner: Miner, index: number) {
  editingMiner.value = { index, miner: { ...miner } };
}

function confirmEdit() {
  if (editingMiner.value) {
    minerStore
      .updateMiner(
        editingMiner.value.miner.id!.toString(),
        editingMiner.value.miner,
      )
      .then(() => {
        minerStore.loadMiners();
        editingMiner.value = undefined;
      });
  }
}

function cancelEdit() {
  editingMiner.value = undefined;
}

function handleDelete(miner: Miner) {
  minerStore.deleteMiner(miner.id!.toString()).then(() => {
    minerStore.loadMiners();
  });
}

function handleStart(miner: Miner) {
  minerStore.startMiner(miner.id!.toString()).then(() => {
    minerStore.loadMiners();
  });
}

function handleStop(miner: Miner) {
  minerStore.stopMiner(miner.id!.toString()).then(() => {
    minerStore.loadMiners();
  });
}

function handleActivate(miner: Miner) {
  minerStore.activateMiner(miner.id!.toString()).then(() => {
    minerStore.loadMiners();
  });
}

function handleDeactivate(miner: Miner) {
  minerStore.deactivateMiner(miner.id!.toString()).then(() => {
    minerStore.loadMiners();
  });
}

function handleRefresh(miner: Miner) {
  minerStore.getMinerStatus(miner.id!.toString());
}
</script>

<template>
  <div class="card bg-base-200 shadow-sm">
  <h2 class="text-2xl font-bold px-6 pt-5 pb-3">Miners settings</h2>

  <div class="overflow-x-auto">
    <table class="table">
      <!-- head -->
      <thead>
        <tr>
          <th>Name</th>
          <th>Model</th>
          <th>Status</th>
          <th>Hash Rate (Max)</th>
          <th>Power Consumption (Max)</th>
          <th>Miner Controller</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <template v-for="(miner, i) in minerStore.miners" :key="miner.id">
          <MinerRowEdit
            v-if="editingMiner && editingMiner.index === i"
            v-model="editingMiner.miner"
            :all-miners="minerStore.miners"
          />
          <MinerRow
            v-else
            v-model="minerStore.miners[i]"
            @edit="handleEdit(miner, i)"
            @delete="handleDelete"
            @start="handleStart"
            @stop="handleStop"
            @activate="handleActivate"
            @deactivate="handleDeactivate"
            @refresh="handleRefresh"
          />
        </template>

        <MinerRowEdit
          v-if="newMiner"
          v-model="newMiner"
          :all-miners="minerStore.miners"
          edit
        />

        <tr>
          <th colspan="7" class="text-center">
            <button
              v-if="!newMiner && !editingMiner"
              class="btn btn-primary"
              @click="addMiner"
            >
              Add Miner
            </button>
            <template v-else-if="newMiner">
              <button
                class="btn btn-secondary mr-4"
                @click="newMiner = undefined"
              >
                Cancel
              </button>
              <button class="btn btn-primary" @click="confirmAdd">OK</button>
            </template>
            <template v-else-if="editingMiner">
              <button class="btn btn-secondary mr-4" @click="cancelEdit">
                Cancel
              </button>
              <button class="btn btn-primary" @click="confirmEdit">Save</button>
            </template>
          </th>
        </tr>
      </tbody>
    </table>
  </div>
  </div>
</template>

<style scoped></style>
