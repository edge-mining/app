<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { useForecastProviderStore } from "../../core/stores/forecastProviderStore";
import { useEnergySourceStore } from "../../core/stores/energySourceStore";
import { useExternalServiceStore } from "../../core/stores/externalServiceStore";
import ForecastProviderRow from "../../components/forecastProviders/ForecastProviderRow.vue";
import type { ForecastProvider } from "../../core/models/forecastProvider";
import ForecastProviderConfigForm from "../../components/forecastProviders/ForecastProviderConfigForm.vue";

const forecastProviderStore = useForecastProviderStore();
const energySourceStore = useEnergySourceStore();
const externalServiceStore = useExternalServiceStore();
const newForecastProvider = ref<ForecastProvider | undefined>(undefined);
const editingForecastProvider = ref<ForecastProvider | undefined>(undefined);
const showModal = ref(false);
const isEditing = ref(false);

// External service UI state
const newRequiresExternalService = ref(false);
const newCompatibleExternalServices = ref<any[]>([]);
const editingRequiresExternalService = ref(false);
const editingCompatibleExternalServices = ref<any[]>([]);

onMounted(() => {
  forecastProviderStore.loadForecastProviders();
  forecastProviderStore.loadAdapterTypes();
  energySourceStore.loadEnergySources();
  externalServiceStore.loadExternalServices();
});

// Update compatible external services for 'new' modal
const updateNewExternalServices = async (adapterType: string) => {
  if (!adapterType) {
    newRequiresExternalService.value = false;
    newCompatibleExternalServices.value = [];
    return;
  }
  try {
    const resp = await forecastProviderStore.externalServices(adapterType);

    let required = false;
    let compatibleAdapterTypes: string[] = [];

    if (resp === null || resp === undefined) {
      required = false;
      compatibleAdapterTypes = [];
    } else if (typeof resp === "string") {
      // a single adapter type is returned -> external service required and must match this adapter_type
      required = true;
      compatibleAdapterTypes = [resp];
    } else {
      // fallback: do not require external service
      required = false;
      compatibleAdapterTypes = [];
    }

    newRequiresExternalService.value = required;
    if (compatibleAdapterTypes.length > 0) {
      newCompatibleExternalServices.value =
        externalServiceStore.externalServices.filter((s: any) =>
          compatibleAdapterTypes.includes(s.adapter_type),
        );
    } else if (required) {
      // required but no specific adapter types -> allow all external services
      newCompatibleExternalServices.value =
        externalServiceStore.externalServices;
    } else {
      newCompatibleExternalServices.value = [];
    }
  } catch (err) {
    console.error("Failed to get external services info for adapter:", err);
    newRequiresExternalService.value = false;
    newCompatibleExternalServices.value = [];
  }
};

// Update compatible external services for 'edit' modal
const updateEditingExternalServices = async (adapterType: string) => {
  if (!adapterType) {
    editingRequiresExternalService.value = false;
    editingCompatibleExternalServices.value = [];
    return;
  }
  try {
    const resp = await forecastProviderStore.externalServices(adapterType);
    // Per OpenAPI: response is string (ExternalServiceAdapter) or null
    let required = false;
    let compatibleAdapterTypes: string[] = [];

    if (resp === null || resp === undefined) {
      required = false;
      compatibleAdapterTypes = [];
    } else if (typeof resp === "string") {
      required = true;
      compatibleAdapterTypes = [resp];
    } else {
      required = false;
      compatibleAdapterTypes = [];
    }

    editingRequiresExternalService.value = required;
    if (compatibleAdapterTypes.length > 0) {
      editingCompatibleExternalServices.value =
        externalServiceStore.externalServices.filter((s: any) =>
          compatibleAdapterTypes.includes(s.adapter_type),
        );
    } else if (required) {
      editingCompatibleExternalServices.value =
        externalServiceStore.externalServices;
    } else {
      editingCompatibleExternalServices.value = [];
    }
  } catch (err) {
    console.error("Failed to get external services info for adapter:", err);
    editingRequiresExternalService.value = false;
    editingCompatibleExternalServices.value = [];
  }
};

// Watch adapter_type changes on new/edit objects
watch(
  () => newForecastProvider.value?.adapter_type,
  (val) => {
    if (val) updateNewExternalServices(val);
  },
);

watch(
  () => editingForecastProvider.value?.adapter_type,
  (val) => {
    if (val) updateEditingExternalServices(val);
  },
);

function cleanForecastProvider(
  forecastProvider: ForecastProvider,
): ForecastProvider {
  const cleaned = { ...forecastProvider };
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

function addForecastProvider() {
  newForecastProvider.value = {
    name: "",
    adapter_type: forecastProviderStore.adapterTypes[0] || "",
    config: {},
    external_service_id: "",
  };
  isEditing.value = false;
  showModal.value = true;
}

function handleEdit(forecastProvider: ForecastProvider) {
  editingForecastProvider.value = { ...forecastProvider };
  isEditing.value = true;
  showModal.value = true;
  // update compatible external services for this adapter type
  if (editingForecastProvider.value?.adapter_type) {
    updateEditingExternalServices(editingForecastProvider.value.adapter_type);
  }
}

function cancelAdd() {
  newForecastProvider.value = undefined;
  editingForecastProvider.value = undefined;
  isEditing.value = false;
  showModal.value = false;
}

function confirmAdd() {
  if (!newForecastProvider.value) return;
  const forecastProviderToAdd = cleanForecastProvider(
    newForecastProvider.value,
  );
  forecastProviderStore.addForecastProvider(forecastProviderToAdd).then(() => {
    forecastProviderStore.loadForecastProviders();
    newForecastProvider.value = undefined;
    showModal.value = false;
  });
}

function confirmEdit() {
  if (!editingForecastProvider.value) return;
  const forecastProviderToUpdate = cleanForecastProvider(
    editingForecastProvider.value,
  );
  forecastProviderStore
    .updateForecastProvider(
      editingForecastProvider.value.id!.toString(),
      forecastProviderToUpdate,
    )
    .then(() => {
      forecastProviderStore.loadForecastProviders();
      editingForecastProvider.value = undefined;
      isEditing.value = false;
      showModal.value = false;
    });
}

function handleDelete(forecastProvider: ForecastProvider) {
  forecastProviderStore
    .deleteForecastProvider(forecastProvider.id!.toString())
    .then(() => {
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
          <th>Name</th>
          <th>Adapter Type</th>
          <th>Assigned Energy Source</th>
          <th>External Service</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <ForecastProviderRow
          v-for="(
            forecastProvider, i
          ) in forecastProviderStore.forecastProviders"
          :key="forecastProvider.id"
          v-model="forecastProviderStore.forecastProviders[i]"
          :all-energy-sources="energySourceStore.energySources"
          @edit="handleEdit"
          @delete="handleDelete"
        />

        <tr v-if="forecastProviderStore.forecastProviders.length === 0">
          <td colspan="5" class="text-center opacity-50">
            No forecast providers configured yet
          </td>
        </tr>

        <tr>
          <th colspan="5" class="text-center">
            <button class="btn btn-primary" @click="addForecastProvider">
              Add Forecast Provider
            </button>
          </th>
        </tr>
      </tbody>
    </table>
  </div>

  <!-- Modal for adding/editing forecast provider -->
  <dialog :class="['modal', { 'modal-open': showModal }]">
    <div
      v-if="newForecastProvider || editingForecastProvider"
      class="modal-box max-w-2xl"
    >
      <h3 class="font-bold text-lg mb-4">
        {{ isEditing ? "Edit Forecast Provider" : "Add Forecast Provider" }}
      </h3>

      <form
        @submit.prevent="isEditing ? confirmEdit() : confirmAdd()"
        class="flex flex-col gap-4"
      >
        <template v-if="isEditing && editingForecastProvider">
          <!-- Name field -->
          <div class="space-y-1">
            <div class="font-medium">
              Name
              <span class="text-sm text-error opacity-60 ml-1 font-normal"
                >(required)</span
              >
            </div>
            <input
              v-model="editingForecastProvider.name"
              type="text"
              placeholder="Forecast provider name"
              required
              class="input input-bordered input-sm w-full"
            />
          </div>

          <!-- Adapter Type dropdown -->
          <div class="space-y-1">
            <div class="font-medium">
              Adapter Type
              <span class="text-sm text-error opacity-60 ml-1 font-normal"
                >(required)</span
              >
            </div>
            <select
              v-model="editingForecastProvider.adapter_type"
              required
              class="select select-bordered select-sm w-full"
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
            <div class="text-sm italic opacity-70">
              Adapter type cannot be changed after creation
            </div>
          </div>

          <!-- External Service (only shown if required by adapter) -->
          <div v-if="editingRequiresExternalService" class="space-y-1">
            <div class="font-medium">
              External Service
              <span class="text-sm text-error opacity-60 ml-1 font-normal"
                >(required by this adapter)</span
              >
            </div>
            <select
              v-model="editingForecastProvider.external_service_id"
              class="select select-bordered select-sm w-full"
            >
              <option value="">-- None --</option>
              <option
                v-if="editingCompatibleExternalServices.length === 0"
                disabled
              >
                No compatible external services available
              </option>
              <option
                v-for="svc in editingCompatibleExternalServices"
                :key="svc.id"
                :value="svc.id"
              >
                {{ svc.name }}
              </option>
            </select>
            <div class="text-sm italic opacity-70">
              Select an external service
            </div>
          </div>

          <!-- Dynamic Config Form -->
          <div class="space-y-1">
            <div class="font-medium">Configuration</div>
            <div class="border border-base-300 rounded-lg p-4">
              <ForecastProviderConfigForm
                v-if="editingForecastProvider.config"
                v-model="editingForecastProvider.config"
                :adapter-type="editingForecastProvider.adapter_type"
              />
            </div>
          </div>
        </template>

        <template v-else-if="newForecastProvider">
          <!-- Name field -->
          <div class="space-y-1">
            <div class="font-medium">
              Name
              <span class="text-sm text-error opacity-60 ml-1 font-normal"
                >(required)</span
              >
            </div>
            <input
              v-model="newForecastProvider.name"
              type="text"
              placeholder="Forecast provider name"
              required
              class="input input-bordered input-sm w-full"
            />
          </div>

          <!-- Adapter Type dropdown -->
          <div class="space-y-1">
            <div class="font-medium">
              Adapter Type
              <span class="text-sm text-error opacity-60 ml-1 font-normal"
                >(required)</span
              >
            </div>
            <select
              v-model="newForecastProvider.adapter_type"
              required
              class="select select-bordered select-sm w-full"
            >
              <option
                v-for="adapterType in forecastProviderStore.adapterTypes"
                :key="adapterType"
                :value="adapterType"
              >
                {{ formatAdapterType(adapterType) }}
              </option>
            </select>
            <div class="text-sm italic opacity-70">
              Select the type of forecast provider adapter
            </div>
          </div>

          <!-- External Service (only shown if required by adapter) -->
          <div v-if="newRequiresExternalService" class="space-y-1">
            <div class="font-medium">
              External Service
              <span class="text-sm text-error opacity-60 ml-1 font-normal"
                >(required by this adapter)</span
              >
            </div>
            <select
              v-model="newForecastProvider.external_service_id"
              class="select select-bordered select-sm w-full"
            >
              <option value="">-- None --</option>
              <option
                v-if="newCompatibleExternalServices.length === 0"
                disabled
              >
                No compatible external services available
              </option>
              <option
                v-for="svc in newCompatibleExternalServices"
                :key="svc.id"
                :value="svc.id"
              >
                {{ svc.name }}
              </option>
            </select>
            <div class="text-sm italic opacity-70">
              Select an external service
            </div>
          </div>

          <!-- Dynamic Config Form -->
          <div class="space-y-1">
            <div class="font-medium">Configuration</div>
            <div class="border border-base-300 rounded-lg p-4">
              <ForecastProviderConfigForm
                v-if="newForecastProvider.config"
                v-model="newForecastProvider.config"
                :adapter-type="newForecastProvider.adapter_type"
              />
            </div>
          </div>
        </template>

        <!-- Modal actions -->
        <div class="modal-action">
          <button type="button" class="btn btn-secondary" @click="cancelAdd">
            Cancel
          </button>
          <button type="submit" class="btn btn-primary">
            {{ isEditing ? "Save" : "Add" }}
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
