<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useForecastProviderStore } from "../../core/stores/forecastProviderStore";
import ForecastProviderRow from "../../components/forecastProviders/ForecastProviderRow.vue";
import type { ForecastProvider } from "../../core/models/forecastProvider";
import ForecastProviderConfigForm from "../../components/forecastProviders/ForecastProviderConfigForm.vue";

const forecastProviderStore = useForecastProviderStore();
const newForecastProvider = ref<ForecastProvider | undefined>(undefined);
const editingForecastProvider = ref<ForecastProvider | undefined>(undefined);
const showModal = ref(false);
const isEditing = ref(false);

onMounted(() => {
  forecastProviderStore.loadForecastProviders();
  forecastProviderStore.loadAdapterTypes();
});

function cleanForecastProvider(forecastProvider: ForecastProvider): ForecastProvider {
  const cleaned = { ...forecastProvider };
  // Remove empty config object if no properties
  if (cleaned.config && Object.keys(cleaned.config).length === 0) {
    delete cleaned.config;
  }
  return cleaned;
}

function addForecastProvider() {
  newForecastProvider.value = {
    name: "",
    adapter_type: forecastProviderStore.adapterTypes[0] || "",
    config: {},
  };
  isEditing.value = false;
  showModal.value = true;
}

function handleEdit(forecastProvider: ForecastProvider) {
  editingForecastProvider.value = { ...forecastProvider };
  isEditing.value = true;
  showModal.value = true;
}

function cancelAdd() {
  newForecastProvider.value = undefined;
  editingForecastProvider.value = undefined;
  isEditing.value = false;
  showModal.value = false;
}

function confirmAdd() {
  if (!newForecastProvider.value) return;
  const forecastProviderToAdd = cleanForecastProvider(newForecastProvider.value);
  forecastProviderStore.addForecastProvider(forecastProviderToAdd).then(() => {
    forecastProviderStore.loadForecastProviders();
    newForecastProvider.value = undefined;
    showModal.value = false;
  });
}

function confirmEdit() {
  if (!editingForecastProvider.value) return;
  const forecastProviderToUpdate = cleanForecastProvider(editingForecastProvider.value);
  forecastProviderStore
    .updateForecastProvider(editingForecastProvider.value.id!.toString(), forecastProviderToUpdate)
    .then(() => {
      forecastProviderStore.loadForecastProviders();
      editingForecastProvider.value = undefined;
      isEditing.value = false;
      showModal.value = false;
    });
}

function handleDelete(forecastProvider: ForecastProvider) {
  forecastProviderStore.deleteForecastProvider(forecastProvider.id!.toString()).then(() => {
    forecastProviderStore.loadForecastProviders();
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
  <h1 class="text-3xl font-bold">Forecast Provider Settings</h1>

  <div class="overflow-x-auto">
    <table class="table">
      <!-- head -->
      <thead>
        <tr>
          <th></th>
          <th>Name / Adapter Type</th>
          <th>ID</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <template>
          <ForecastProviderRow
            v-for="(forecastProvider, i) in forecastProviderStore.forecastProviders" :key="forecastProvider.id"
            v-model="forecastProviderStore.forecastProviders[i]"
            @edit="handleEdit"
            @delete="handleDelete"
          />
        </template>

        <tr>
          <th colspan="4" class="text-center">
            <button class="btn btn-primary" @click="addForecastProvider">
              Add Forecast Provider
            </button>
          </th>
        </tr>
      </tbody>
      <!-- foot -->
      <tfoot>
        <tr>
          <th></th>
          <th>Name / Adapter Type</th>
          <th>ID</th>
          <th></th>
        </tr>
      </tfoot>
    </table>
  </div>

  <!-- Modal for adding/editing forecast provider -->
  <dialog :class="['modal', { 'modal-open': showModal }]">
    <div v-if="newForecastProvider || editingForecastProvider" class="modal-box max-w-2xl">
      <h3 class="font-bold text-lg mb-4">
        {{ isEditing ? 'Edit Forecast Provider' : 'Add Forecast Provider' }}
      </h3>

      <form
        @submit.prevent="isEditing ? confirmEdit() : confirmAdd()"
        class="flex flex-col gap-4"
      >
        <template v-if="isEditing && editingForecastProvider">
          <!-- Name field -->
          <div class="form-control">
            <label class="label">
              <span class="label-text">Name <span class="text-error">*</span></span>
            </label>
            <input
              v-model="editingForecastProvider.name"
              type="text"
              placeholder="Forecast provider name"
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
              v-model="editingForecastProvider.adapter_type"
              required
              class="select select-bordered"
              disabled
            >
              <option
                v-for="adapterType in forecastProviderStore.adapterTypes"
                :key="adapterType"
                :value="adapterType"
              >
                {{ formatAdapterType(adapterType) }}
              </option>
            </select>
          </div>

          <!-- Dynamic Config Form -->
          <div class="form-control">
            <label class="label">
              <span class="label-text font-semibold">Configuration</span>
            </label>
            <div class="border border-base-300 rounded-lg p-4">
              <ForecastProviderConfigForm
                v-model="editingForecastProvider.config!"
                :adapter-type="editingForecastProvider.adapter_type"
              />
            </div>
          </div>
        </template>

        <template v-else-if="newForecastProvider">
          <!-- Name field -->
          <div class="form-control">
            <label class="label">
              <span class="label-text">Name <span class="text-error">*</span></span>
            </label>
            <input
              v-model="newForecastProvider.name"
              type="text"
              placeholder="Forecast provider name"
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
              v-model="newForecastProvider.adapter_type"
              required
              class="select select-bordered"
            >
              <option
                v-for="adapterType in forecastProviderStore.adapterTypes"
                :key="adapterType"
                :value="adapterType"
              >
                {{ formatAdapterType(adapterType) }}
              </option>
            </select>
          </div>

          <!-- Dynamic Config Form -->
          <div class="form-control">
            <label class="label">
              <span class="label-text font-semibold">Configuration</span>
            </label>
            <div class="border border-base-300 rounded-lg p-4">
              <ForecastProviderConfigForm
                v-model="newForecastProvider.config!"
                :adapter-type="newForecastProvider.adapter_type"
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
