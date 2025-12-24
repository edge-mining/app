<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useEnergyMonitorStore } from "../../core/stores/energyMonitorStore";
import { useEnergySourceStore } from "../../core/stores/energySourceStore";
import { useExternalServiceStore } from "../../core/stores/externalServiceStore";
import EnergyMonitorRow from "../../components/energyMonitors/EnergyMonitorRow.vue";
import type { EnergyMonitor } from "../../core/models/energyMonitor";
import EnergyMonitorConfigForm from "../../components/energyMonitors/EnergyMonitorConfigForm.vue";

const energyMonitorStore = useEnergyMonitorStore();
const energySourceStore = useEnergySourceStore();
const externalServiceStore = useExternalServiceStore();
const newEnergyMonitor = ref<EnergyMonitor | undefined>(undefined);
const editingEnergyMonitor = ref<EnergyMonitor | undefined>(undefined);
const showModal = ref(false);
const isEditing = ref(false);

onMounted(() => {
  energyMonitorStore.loadEnergyMonitors();
  energyMonitorStore.loadAdapterTypes();
  energySourceStore.loadEnergySources();
  externalServiceStore.loadExternalServices();
});

function cleanEnergyMonitor(energyMonitor: EnergyMonitor): EnergyMonitor {
  const cleaned = { ...energyMonitor };
  // Remove empty string values for external_service_id
  if (cleaned.external_service_id === "") {
    delete cleaned.external_service_id;
  }
  // Remove empty config object if no properties
  if (cleaned.config && Object.keys(cleaned.config).length === 0) {
    delete cleaned.config;
  }
  return cleaned;
}

function addEnergyMonitor() {
  newEnergyMonitor.value = {
    name: "",
    adapter_type: energyMonitorStore.adapterTypes[0] || "",
    config: {},
  };
  isEditing.value = false;
  showModal.value = true;
}

function handleEdit(energyMonitor: EnergyMonitor) {
  editingEnergyMonitor.value = { ...energyMonitor };
  isEditing.value = true;
  showModal.value = true;
}

function cancelAdd() {
  newEnergyMonitor.value = undefined;
  editingEnergyMonitor.value = undefined;
  isEditing.value = false;
  showModal.value = false;
}

function confirmAdd() {
  if (!newEnergyMonitor.value) return;
  const energyMonitorToAdd = cleanEnergyMonitor(newEnergyMonitor.value);
  energyMonitorStore.addEnergyMonitor(energyMonitorToAdd).then(() => {
    energyMonitorStore.loadEnergyMonitors();
    newEnergyMonitor.value = undefined;
    showModal.value = false;
  });
}

function confirmEdit() {
  if (!editingEnergyMonitor.value) return;
  const energyMonitorToUpdate = cleanEnergyMonitor(editingEnergyMonitor.value);
  energyMonitorStore
    .updateEnergyMonitor(editingEnergyMonitor.value.id!.toString(), energyMonitorToUpdate)
    .then(() => {
      energyMonitorStore.loadEnergyMonitors();
      editingEnergyMonitor.value = undefined;
      isEditing.value = false;
      showModal.value = false;
    });
}

function handleDelete(energyMonitor: EnergyMonitor) {
  energyMonitorStore.deleteEnergyMonitor(energyMonitor.id!.toString()).then(() => {
    energyMonitorStore.loadEnergyMonitors();
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
          <th>Name</th>
          <th>Adapter Type</th>
          <th>External Service</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <EnergyMonitorRow
          v-for="(energyMonitor, i) in energyMonitorStore.energyMonitors"
          :key="energyMonitor.id"
          v-model="energyMonitorStore.energyMonitors[i]"
          :all-energy-sources="energySourceStore.energySources"
          @edit="handleEdit"
          @delete="handleDelete"
        />

        <tr v-if="energyMonitorStore.energyMonitors.length === 0">
          <td colspan="4" class="text-center opacity-50">
            No energy monitors configured yet
          </td>
        </tr>

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
          <th>Name</th>
          <th>Adapter Type</th>
          <th>External Service</th>
          <th>Actions</th>
        </tr>
      </tfoot>
    </table>
  </div>

  <!-- Modal for adding/editing energy monitor -->
  <dialog :class="['modal', { 'modal-open': showModal }]">
    <div v-if="newEnergyMonitor || editingEnergyMonitor" class="modal-box max-w-2xl">
      <h3 class="font-bold text-lg mb-4">
        {{ isEditing ? 'Edit Energy Monitor' : 'Add Energy Monitor' }}
      </h3>

      <form
        @submit.prevent="isEditing ? confirmEdit() : confirmAdd()"
        class="flex flex-col gap-4"
      >
        <template v-if="isEditing && editingEnergyMonitor">
          <!-- Name field -->
          <div class="space-y-1">
            <div class="font-medium">
              Name
              <span class="text-sm text-error opacity-60 ml-1 font-normal">(required)</span>
            </div>
            <input
              v-model="editingEnergyMonitor.name"
              type="text"
              placeholder="Energy monitor name"
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
              v-model="editingEnergyMonitor.adapter_type"
              required
              class="select select-bordered select-sm w-full"
              disabled
            >
              <option
                v-for="adapterType in energyMonitorStore.adapterTypes"
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

          <!-- External Service ID -->
          <div class="space-y-1">
            <div class="font-medium">External Service</div>
            <select
              v-model="editingEnergyMonitor.external_service_id"
              class="select select-bordered select-sm w-full"
            >
              <option value="">-- None --</option>
              <option
                v-for="svc in externalServiceStore.externalServices"
                :key="svc.id"
                :value="svc.id"
              >
                {{ svc.name }}
              </option>
            </select>
            <div class="text-sm italic opacity-70">Optional: select an external service</div>
          </div>

          <!-- Dynamic Config Form -->
          <div class="space-y-1">
            <div class="font-medium">Configuration</div>
            <div class="border border-base-300 rounded-lg p-4">
              <EnergyMonitorConfigForm
                v-if="editingEnergyMonitor.config"
                v-model="editingEnergyMonitor.config"
                :adapter-type="editingEnergyMonitor.adapter_type"
              />
            </div>
          </div>
        </template>

        <template v-else-if="newEnergyMonitor">
          <!-- Name field -->
          <div class="space-y-1">
            <div class="font-medium">
              Name
              <span class="text-sm text-error opacity-60 ml-1 font-normal">(required)</span>
            </div>
            <input
              v-model="newEnergyMonitor.name"
              type="text"
              placeholder="Energy monitor name"
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
              v-model="newEnergyMonitor.adapter_type"
              required
              class="select select-bordered select-sm w-full"
            >
              <option
                v-for="adapterType in energyMonitorStore.adapterTypes"
                :key="adapterType"
                :value="adapterType"
              >
                {{ formatAdapterType(adapterType) }}
              </option>
            </select>
            <div class="text-sm italic opacity-70">
              Select the type of energy monitor adapter
            </div>
          </div>

          <!-- External Service ID -->
          <div class="space-y-1">
            <div class="font-medium">External Service</div>
            <select
              v-model="newEnergyMonitor.external_service_id"
              class="select select-bordered select-sm w-full"
            >
              <option value="">-- None --</option>
              <option
                v-for="svc in externalServiceStore.externalServices"
                :key="svc.id"
                :value="svc.id"
              >
                {{ svc.name }}
              </option>
            </select>
            <div class="text-sm italic opacity-70">Optional: select an external service</div>
          </div>

          <!-- Dynamic Config Form -->
          <div class="space-y-1">
            <div class="font-medium">Configuration</div>
            <div class="border border-base-300 rounded-lg p-4">
              <EnergyMonitorConfigForm
                v-if="newEnergyMonitor.config"
                v-model="newEnergyMonitor.config"
                :adapter-type="newEnergyMonitor.adapter_type"
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
