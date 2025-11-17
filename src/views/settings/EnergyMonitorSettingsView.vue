<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useEnergyMonitorStore } from "../../core/stores/energyMonitorStore";
import EnergyMonitorRow from "../../components/energyMonitors/EnergyMonitorRow.vue";
import type { EnergyMonitor } from "../../core/models/energyMonitor";
import EnergyMonitorConfigForm from "../../components/energyMonitors/EnergyMonitorConfigForm.vue";

const energyMonitorStore = useEnergyMonitorStore();
const newEnergyMonitor = ref<EnergyMonitor | undefined>(undefined);
const showModal = ref(false);

onMounted(() => {
  energyMonitorStore.loadEnergyMonitors();
  energyMonitorStore.loadAdapterTypes();
});

function addEnergyMonitor() {
  newEnergyMonitor.value = {
    name: "",
    adapter_type: energyMonitorStore.adapterTypes[0] || "",
    config: {},
  };
  showModal.value = true;
}

function cancelAdd() {
  newEnergyMonitor.value = undefined;
  showModal.value = false;
}

function confirmAdd() {
  if (!newEnergyMonitor.value) return;

  // Clean up the energy monitor before sending to API
  const energyMonitorToAdd = { ...newEnergyMonitor.value! };

  // Remove empty string values for external_service_id
  if (energyMonitorToAdd.external_service_id === "") {
    delete energyMonitorToAdd.external_service_id;
  }

  // Remove empty config object if no properties
  if (energyMonitorToAdd.config && Object.keys(energyMonitorToAdd.config).length === 0) {
    delete energyMonitorToAdd.config;
  }

  energyMonitorStore.addEnergyMonitor(energyMonitorToAdd).then(() => {
    energyMonitorStore.loadEnergyMonitors();
    newEnergyMonitor.value = undefined;
    showModal.value = false;
  });
}

// Format adapter type for display
const formatAdapterType = (type: string) => {
  return type
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
};
</script>

<template>
  <h1 class="text-3xl font-bold">Energy Monitor Settings</h1>

  <div class="overflow-x-auto">
    <table class="table">
      <!-- head -->
      <thead>
        <tr>
          <th></th>
          <th>Name / Adapter Type</th>
          <th>External Service ID</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <template
          v-for="(energyMonitor, i) in energyMonitorStore.energyMonitors"
          :key="energyMonitor.id"
        >
          <EnergyMonitorRow v-model="energyMonitorStore.energyMonitors[i]" />
        </template>

        <tr>
          <th colspan="4" class="text-center">
            <button class="btn btn-primary" @click="addEnergyMonitor">
              Add Energy Monitor
            </button>
          </th>
        </tr>
      </tbody>
      <!-- foot -->
      <tfoot>
        <tr>
          <th></th>
          <th>Name / Adapter Type</th>
          <th>External Service ID</th>
          <th></th>
        </tr>
      </tfoot>
    </table>
  </div>

  <!-- Modal for adding energy monitor -->
  <dialog :class="['modal', { 'modal-open': showModal }]">
    <div v-if="newEnergyMonitor" class="modal-box max-w-2xl">
      <h3 class="font-bold text-lg mb-4">Add Energy Monitor</h3>

      <form @submit.prevent="confirmAdd" class="flex flex-col gap-4">
        <!-- Name field -->
        <div class="form-control">
          <label class="label">
            <span class="label-text">Name <span class="text-error">*</span></span>
          </label>
          <input
            v-model="newEnergyMonitor.name"
            type="text"
            placeholder="Energy monitor name"
            required
            class="input input-bordered"
          />
        </div>

        <!-- Adapter Type dropdown -->
        <div class="form-control">
          <label class="label">
            <span class="label-text">Adapter Type <span class="text-error">*</span></span>
          </label>
          <select
            v-model="newEnergyMonitor.adapter_type"
            required
            class="select select-bordered"
          >
            <option
              v-for="adapterType in energyMonitorStore.adapterTypes"
              :key="adapterType"
              :value="adapterType"
            >
              {{ formatAdapterType(adapterType) }}
            </option>
          </select>
        </div>

        <!-- External Service ID -->
        <div class="form-control">
          <label class="label">
            <span class="label-text">External Service ID</span>
          </label>
          <input
            v-model="newEnergyMonitor.external_service_id"
            type="text"
            placeholder="Optional service ID"
            class="input input-bordered"
          />
        </div>

        <!-- Dynamic Config Form -->
        <div class="form-control">
          <label class="label">
            <span class="label-text font-semibold">Configuration</span>
          </label>
          <div class="border border-base-300 rounded-lg p-4">
            <EnergyMonitorConfigForm
              v-model="newEnergyMonitor.config!"
              :adapter-type="newEnergyMonitor.adapter_type"
            />
          </div>
        </div>

        <!-- Modal actions -->
        <div class="modal-action">
          <button type="submit" class="btn btn-primary">
            Add
          </button>
          <button type="button" class="btn btn-secondary" @click="cancelAdd">
            Cancel
          </button>
        </div>
      </form>
    </div>
    <form method="dialog" class="modal-backdrop">
      <button @click="cancelAdd">close</button>
    </form>
  </dialog>
</template>

<style scoped></style>
