<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useExternalServiceStore } from "../../core/stores/externalServiceStore";
import { useEnergyMonitorStore } from "../../core/stores/energyMonitorStore";
import { useForecastProviderStore } from "../../core/stores/forecastProviderStore";
import { useMinerControllerStore } from "../../core/stores/minerControllerStore";
import ExternalServiceRow from "../../components/externalServices/ExternalServiceRow.vue";
import type { ExternalService } from "../../core/models/externalService";
import ExternalServiceConfigForm from "../../components/externalServices/ExternalServiceConfigForm.vue";

const externalServiceStore = useExternalServiceStore();
const energyMonitorStore = useEnergyMonitorStore();
const forecastProviderStore = useForecastProviderStore();
const minerControllerStore = useMinerControllerStore();
const newExternalService = ref<ExternalService | undefined>(undefined);
const editingExternalService = ref<ExternalService | undefined>(undefined);
const showModal = ref(false);
const isEditing = ref(false);

onMounted(() => {
  externalServiceStore.loadExternalServices();
  externalServiceStore.loadAdapterTypes();
  energyMonitorStore.loadEnergyMonitors();
  forecastProviderStore.loadForecastProviders();
  minerControllerStore.loadMinerControllers();
});

function cleanExternalService(externalService: ExternalService): ExternalService {
  const cleaned = { ...externalService };
  // Remove empty config object if no properties
  if (cleaned.config && Object.keys(cleaned.config).length === 0) {
    delete cleaned.config;
  }
  return cleaned;
}

function addExternalService() {
  newExternalService.value = {
    name: "",
    adapter_type: externalServiceStore.adapterTypes[0] || "",
    config: {},
  };
  isEditing.value = false;
  showModal.value = true;
}

function handleEdit(externalService: ExternalService) {
  editingExternalService.value = { ...externalService, config: { ...externalService.config } };
  isEditing.value = true;
  showModal.value = true;
}

function cancelAdd() {
  newExternalService.value = undefined;
  editingExternalService.value = undefined;
  isEditing.value = false;
  showModal.value = false;
}

function confirmAdd() {
  if (!newExternalService.value) return;
  const externalServiceToAdd = cleanExternalService(newExternalService.value);
  externalServiceStore.addExternalService(externalServiceToAdd).then(() => {
    externalServiceStore.loadExternalServices();
    newExternalService.value = undefined;
    showModal.value = false;
  });
}

function confirmEdit() {
  if (!editingExternalService.value) return;
  const externalServiceToUpdate = cleanExternalService(editingExternalService.value);
  externalServiceStore
    .updateExternalService(editingExternalService.value.id!.toString(), externalServiceToUpdate)
    .then(() => {
      externalServiceStore.loadExternalServices();
      editingExternalService.value = undefined;
      isEditing.value = false;
      showModal.value = false;
    });
}

function handleDelete(externalService: ExternalService) {
  externalServiceStore.deleteExternalService(externalService.id!.toString()).then(() => {
    externalServiceStore.loadExternalServices();
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
  <h1 class="text-3xl font-bold">External Services Settings</h1>

  <div class="overflow-x-auto">
    <table class="table">
      <!-- head -->
      <thead>
        <tr>
          <th>Name</th>
          <th>Adapter Type</th>
          <th>Assigned Energy Monitors</th>
          <th>Assigned Forecast Providers</th>
          <th>Assigned Miner Controllers</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <ExternalServiceRow
          v-for="(externalService, i) in externalServiceStore.externalServices"
          :key="externalService.id"
          v-model="externalServiceStore.externalServices[i]"
          :all-energy-monitors="energyMonitorStore.energyMonitors"
          :all-forecast-providers="forecastProviderStore.forecastProviders"
          :all-miner-controllers="minerControllerStore.minerControllers"
          @edit="handleEdit"
          @delete="handleDelete"
        />

        <tr v-if="externalServiceStore.externalServices.length === 0">
          <td colspan="6" class="text-center opacity-50">
            No external services configured yet
          </td>
        </tr>

        <tr>
          <th colspan="6" class="text-center">
            <button class="btn btn-primary" @click="addExternalService">
              Add External Service
            </button>
          </th>
        </tr>
      </tbody>
      <!-- foot -->
      <tfoot>
        <tr>
          <th>Name</th>
          <th>Adapter Type</th>
          <th>Assigned Energy Monitors</th>
          <th>Assigned Forecast Providers</th>
          <th>Assigned Miner Controllers</th>
          <th>Actions</th>
        </tr>
      </tfoot>
    </table>
  </div>

  <!-- Modal for adding/editing external service -->
  <dialog :class="['modal', { 'modal-open': showModal }]">
    <div v-if="newExternalService || editingExternalService" class="modal-box max-w-2xl">
      <h3 class="font-bold text-lg mb-4">
        {{ isEditing ? 'Edit External Service' : 'Add External Service' }}
      </h3>

      <form
        @submit.prevent="isEditing ? confirmEdit() : confirmAdd()"
        class="flex flex-col gap-4"
      >
        <template v-if="isEditing && editingExternalService">
          <!-- Name field -->
          <div class="space-y-1">
            <div class="font-medium">
              Name
              <span class="text-sm text-error opacity-60 ml-1 font-normal">(required)</span>
            </div>
            <input
              v-model="editingExternalService.name"
              type="text"
              placeholder="External service name"
              required
              class="input input-bordered input-sm w-full"
            />
          </div>

          <!-- Adapter Type dropdown -->
          <div class="space-y-1">
            <div class="font-medium">
              Adapter Type
              <span class="text-sm text-error opacity-60 ml-1 font-normal">(required)</span>
            </div>
            <select
              v-model="editingExternalService.adapter_type"
              required
              class="select select-bordered select-sm w-full"
              disabled
            >
              <option
                v-for="adapterType in externalServiceStore.adapterTypes"
                :key="adapterType"
                :value="adapterType"
              >
                {{ formatAdapterType(adapterType) }}
              </option>
            </select>
            <div class="text-sm italic opacity-70">
              Adapter type cannot be changed after creation
            </div>
          </div>

          <!-- Dynamic Config Form -->
          <div class="space-y-1">
            <div class="font-medium">Configuration</div>
            <div class="border border-base-300 rounded-lg p-4">
              <ExternalServiceConfigForm
                v-if="editingExternalService.config"
                v-model="editingExternalService.config"
                :adapter-type="editingExternalService.adapter_type"
              />
            </div>
          </div>
        </template>

        <template v-else-if="newExternalService">
          <!-- Name field -->
          <div class="space-y-1">
            <div class="font-medium">
              Name
              <span class="text-sm text-error opacity-60 ml-1 font-normal">(required)</span>
            </div>
            <input
              v-model="newExternalService.name"
              type="text"
              placeholder="External service name"
              required
              class="input input-bordered input-sm w-full"
            />
          </div>

          <!-- Adapter Type dropdown -->
          <div class="space-y-1">
            <div class="font-medium">
              Adapter Type
              <span class="text-sm text-error opacity-60 ml-1 font-normal">(required)</span>
            </div>
            <select
              v-model="newExternalService.adapter_type"
              required
              class="select select-bordered select-sm w-full"
            >
              <option
                v-for="adapterType in externalServiceStore.adapterTypes"
                :key="adapterType"
                :value="adapterType"
              >
                {{ formatAdapterType(adapterType) }}
              </option>
            </select>
            <div class="text-sm italic opacity-70">
              Select the type of external service adapter
            </div>
          </div>

          <!-- Dynamic Config Form -->
          <div class="space-y-1">
            <div class="font-medium">Configuration</div>
            <div class="border border-base-300 rounded-lg p-4">
              <ExternalServiceConfigForm
                v-if="newExternalService.config"
                v-model="newExternalService.config"
                :adapter-type="newExternalService.adapter_type"
              />
            </div>
          </div>
        </template>

        <!-- Modal actions -->
        <div class="modal-action">
          <button type="submit" class="btn btn-primary">
            {{ isEditing ? 'Save' : 'Add' }}
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
