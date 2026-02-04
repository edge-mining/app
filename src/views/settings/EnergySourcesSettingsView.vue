<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useEnergySourceStore } from "../../core/stores/energySourceStore";
import { useEnergyMonitorStore } from "../../core/stores/energyMonitorStore";
import { useForecastProviderStore } from "../../core/stores/forecastProviderStore";
import EnergySourceRow from "../../components/energySources/EnergySourceRow.vue";
import type { EnergySource } from "../../core/models/energySource";
import { EnergySourceType } from "../../core/models/energySource";
import EnergySourceRowEdit from "../../components/energySources/EnergySourceRowEdit.vue";

const energySourceStore = useEnergySourceStore();
const energyMonitorStore = useEnergyMonitorStore();
const forecastProviderStore = useForecastProviderStore();
const newEnergySource = ref<EnergySource | undefined>(undefined);
const editingEnergySource = ref<{ index: number; energySource: EnergySource } | undefined>(undefined);

onMounted(() => {
  energySourceStore.loadEnergySources();
  energyMonitorStore.loadEnergyMonitors();
  forecastProviderStore.loadForecastProviders();
});

function addEnergySource() {
  newEnergySource.value = {
    name: "",
    type: EnergySourceType.SOLAR,
  };
}

function cleanEnergySource(energySource: EnergySource): EnergySource {
  const cleaned = { ...energySource };
  // Remove empty string values for energy_monitor_id and forecast_provider_id
  if (cleaned.energy_monitor_id === "") {
    delete cleaned.energy_monitor_id;
  }
  if (cleaned.forecast_provider_id === "") {
    delete cleaned.forecast_provider_id;
  }
  return cleaned;
}

function confirmAdd() {
  const energySourceToAdd = cleanEnergySource(newEnergySource.value!);
  energySourceStore.addEnergySource(energySourceToAdd).then(() => {
    energySourceStore.loadEnergySources();
    newEnergySource.value = undefined;
  });
}

function handleEdit(energySource: EnergySource, index: number) {
  editingEnergySource.value = { index, energySource: { ...energySource } };
}

function confirmEdit() {
  if (editingEnergySource.value) {
    const energySourceToUpdate = cleanEnergySource(editingEnergySource.value.energySource);
    energySourceStore
      .updateEnergySource(editingEnergySource.value.energySource.id!.toString(), energySourceToUpdate)
      .then(() => {
        energySourceStore.loadEnergySources();
        editingEnergySource.value = undefined;
      });
  }
}

function cancelEdit() {
  editingEnergySource.value = undefined;
}

function handleDelete(energySource: EnergySource) {
  energySourceStore.deleteEnergySource(energySource.id!.toString()).then(() => {
    energySourceStore.loadEnergySources();
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
          <th>Name</th>
          <th>Type</th>
          <th>Nominal Power Max</th>
          <th>Storage Capacity</th>
          <th>Grid Contracted Power</th>
          <th>External Source</th>
          <th>Energy Monitor</th>
          <th>Forecast Provider</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <template
          v-for="(energySource, i) in energySourceStore.energySources"
          :key="energySource.id"
        >
          <EnergySourceRowEdit
            v-if="editingEnergySource && editingEnergySource.index === i"
            v-model="editingEnergySource.energySource"
            :all-energy-sources="energySourceStore.energySources"
          />
          <EnergySourceRow
            v-else
            v-model="energySourceStore.energySources[i]"
            @edit="handleEdit(energySource, i)"
            @delete="handleDelete"
          />
        </template>

        <EnergySourceRowEdit v-if="newEnergySource" v-model="newEnergySource" edit />

        <tr>
          <th colspan="7" class="text-center">
            <button
              v-if="!newEnergySource && !editingEnergySource"
              class="btn btn-primary"
              @click="addEnergySource"
            >
              Add Energy Source
            </button>
            <template v-else-if="newEnergySource">
              <button
                class="btn btn-secondary mr-4"
                @click="newEnergySource = undefined"
              >
                Cancel
              </button>
              <button class="btn btn-primary" @click="confirmAdd">
                OK
              </button>
            </template>
            <template v-else-if="editingEnergySource">
              <button class="btn btn-secondary mr-4" @click="cancelEdit">
                Cancel
              </button>
              <button class="btn btn-primary" @click="confirmEdit">
                Save
              </button>
            </template>
          </th>
        </tr>
      </tbody>
      <!-- foot -->
      <tfoot>
        <tr>
          <th>Name</th>
          <th>Type</th>
          <th>Nominal Power Max</th>
          <th>Storage Capacity</th>
          <th>Grid Contracted Power</th>
          <th>External Source</th>
          <th>Energy Monitor</th>
          <th>Forecast Provider</th>
          <th>Actions</th>
        </tr>
      </tfoot>
    </table>
  </div>
</template>

<style scoped></style>
