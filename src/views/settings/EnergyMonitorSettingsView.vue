<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useEnergyMonitorStore } from "../../core/stores/energyMonitorStore";
import EnergyMonitorRow from "../../components/energyMonitors/EnergyMonitorRow.vue";
import type { EnergyMonitor } from "../../core/models/energyMonitor";
import EnergyMonitorConfigForm from "../../components/energyMonitors/EnergyMonitorConfigForm.vue";

const energyMonitorStore = useEnergyMonitorStore();
const newEnergyMonitor = ref<EnergyMonitor | undefined>(undefined);
const editingEnergyMonitor = ref<EnergyMonitor | undefined>(undefined);
const showModal = ref(false);
const isEditing = ref(false);

onMounted(() => {
  energyMonitorStore.loadEnergyMonitors();
  energyMonitorStore.loadAdapterTypes();
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
          <EnergyMonitorRow
            v-model="energyMonitorStore.energyMonitors[i]"
            @edit="handleEdit"
            @delete="handleDelete"
          />
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
          <div class="form-control">
            <label class="label">
              <span class="label-text">Name <span class="text-error">*</span></span>
            </label>
            <input
              v-model="editingEnergyMonitor.name"
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
              v-model="editingEnergyMonitor.adapter_type"
              required
              class="select select-bordered"
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
          </div>

          <!-- External Service ID -->
          <div class="form-control">
            <label class="label">
              <span class="label-text">External Service ID</span>
            </label>
            <input
              v-model="editingEnergyMonitor.external_service_id"
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
                v-model="editingEnergyMonitor.config!"
                :adapter-type="editingEnergyMonitor.adapter_type"
              />
            </div>
          </div>
        </template>

        <template v-else-if="newEnergyMonitor">
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
