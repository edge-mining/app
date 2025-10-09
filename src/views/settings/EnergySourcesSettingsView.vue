<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useEnergySourceStore } from "../../core/stores/energySourceStore";
import EnergySourceRow from "../../components/energySources/EnergySourceRow.vue";
import type { EnergySource } from "../../core/models/energySource";
import { EnergySourceType } from "../../core/models/energySource";
import EnergySourceRowEdit from "../../components/energySources/EnergySourceRowEdit.vue";

const energySourceStore = useEnergySourceStore();
const newEnergySource = ref<EnergySource | undefined>(undefined);

onMounted(() => {
  energySourceStore.loadEnergySources();
});

function addEnergySource() {
  newEnergySource.value = {
    name: "",
    type: EnergySourceType.SOLAR,
  };
}

function confirmAdd() {
  // Clean up the energy source before sending to API
  const energySourceToAdd = { ...newEnergySource.value! };

  // Remove empty string values for energy_monitor_id and forecast_provider_id
  if (energySourceToAdd.energy_monitor_id === "") {
    delete energySourceToAdd.energy_monitor_id;
  }
  if (energySourceToAdd.forecast_provider_id === "") {
    delete energySourceToAdd.forecast_provider_id;
  }

  energySourceStore.addEnergySource(energySourceToAdd).then(() => {
    energySourceStore.loadEnergySources();
    newEnergySource.value = undefined;
  });
}
</script>

<template>
  <h1 class="text-3xl font-bold">Energy Sources Settings</h1>

  <div class="overflow-x-auto">
    <table class="table">
      <!-- head -->
      <thead>
        <tr>
          <th></th>
          <th>Name / Type</th>
          <th>Nominal Power Max</th>
          <th>Storage Capacity</th>
          <th>Grid Contracted Power</th>
          <th>Monitor ID</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <template
          v-for="(energySource, i) in energySourceStore.energySources"
          :key="energySource.id"
        >
          <EnergySourceRow v-model="energySourceStore.energySources[i]" />
        </template>

        <EnergySourceRowEdit v-if="newEnergySource" v-model="newEnergySource" edit />

        <tr>
          <th colspan="7" class="text-center">
            <button
              v-if="!newEnergySource"
              class="btn btn-primary"
              @click="addEnergySource"
            >
              Add Energy Source
            </button>
            <template v-else>
              <button class="btn btn-primary mr-4" @click="confirmAdd">
                OK
              </button>
              <button
                class="btn btn-secondary"
                @click="newEnergySource = undefined"
              >
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
          <th>Name / Type</th>
          <th>Nominal Power Max</th>
          <th>Storage Capacity</th>
          <th>Grid Contracted Power</th>
          <th>Monitor ID</th>
          <th></th>
        </tr>
      </tfoot>
    </table>
  </div>
</template>

<style scoped></style>
