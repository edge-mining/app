<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useMinerStore } from "../../core/stores/minerStore";
import MinerRow from "../../components/miners/MinerRow.vue";
import type { Miner } from "../../core/models/miner";
import MinerRowEdit from "../../components/miners/MinerRowEdit.vue";

const minerStore = useMinerStore();
const newMiner = ref<Miner | undefined>(undefined);
const editingMiner = ref<{ index: number; miner: Miner } | undefined>(undefined);

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

function handleEdit(miner: Miner, index: number) {
  editingMiner.value = { index, miner: { ...miner } };
}

function confirmEdit() {
  if (editingMiner.value) {
    minerStore
      .updateMiner(editingMiner.value.miner.id!.toString(), editingMiner.value.miner)
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
          <MinerRowEdit
            v-if="editingMiner && editingMiner.index === i"
            v-model="editingMiner.miner"
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
          />
        </template>

        <MinerRowEdit v-if="newMiner" v-model="newMiner" edit />

        <tr>
          <th colspan="6" class="text-center">
            <button
              v-if="!newMiner && !editingMiner"
              class="btn btn-primary"
              @click="addMiner"
            >
              Add Miner
            </button>
            <template v-else-if="newMiner">
              <button class="btn btn-primary mr-4" @click="confirmAdd">
                OK
              </button>
              <button class="btn btn-secondary" @click="newMiner = undefined">
                Cancel
              </button>
            </template>
            <template v-else-if="editingMiner">
              <button class="btn btn-primary mr-4" @click="confirmEdit">
                Save
              </button>
              <button class="btn btn-secondary" @click="cancelEdit">
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
