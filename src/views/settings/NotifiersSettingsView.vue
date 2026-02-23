<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { useNotifierStore } from "../../core/stores/notifierStore";
import { useExternalServiceStore } from "../../core/stores/externalServiceStore";
import NotifierRow from "../../components/notifiers/NotifierRow.vue";
import type { Notifier, TestNotifierResult } from "../../core/models/notifier";
import NotifierConfigForm from "../../components/notifiers/NotifierConfigForm.vue";

const notifierStore = useNotifierStore();
const externalServiceStore = useExternalServiceStore();
const newNotifier = ref<Notifier | undefined>(undefined);
const editingNotifier = ref<Notifier | undefined>(undefined);
const showModal = ref(false);
const isEditing = ref(false);

// Test result modal state
const showTestModal = ref(false);
const testResult = ref<TestNotifierResult | null>(null);
const testingNotifierName = ref("");
const testLoading = ref(false);

// External service UI state
const newRequiresExternalService = ref(false);
const newCompatibleExternalServices = ref<any[]>([]);
const editingRequiresExternalService = ref(false);
const editingCompatibleExternalServices = ref<any[]>([]);

onMounted(() => {
  notifierStore.loadNotifiers();
  notifierStore.loadAdapterTypes();
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
    const resp = await notifierStore.externalServices(adapterType);

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
      // array of adapter types returned -> external service required and must match one of these adapter_types
      required = true;
      compatibleAdapterTypes = resp;
    }

    newRequiresExternalService.value = required;
    newCompatibleExternalServices.value =
      externalServiceStore.externalServices.filter((s) =>
        compatibleAdapterTypes.includes(s.adapter_type),
      );
  } catch (err) {
    console.error("Failed to load compatible external services:", err);
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
    const resp = await notifierStore.externalServices(adapterType);

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
      // array of adapter types returned -> external service required and must match one of these adapter_types
      required = true;
      compatibleAdapterTypes = resp;
    }

    editingRequiresExternalService.value = required;
    editingCompatibleExternalServices.value =
      externalServiceStore.externalServices.filter((s) =>
        compatibleAdapterTypes.includes(s.adapter_type),
      );
  } catch (err) {
    console.error("Failed to load compatible external services:", err);
  }
};

// Watch adapter_type changes on new/edit objects
watch(
  () => newNotifier.value?.adapter_type,
  (newAdapterType) => {
    if (newAdapterType) {
      updateNewExternalServices(newAdapterType);
    }
  },
);

watch(
  () => editingNotifier.value?.adapter_type,
  (newAdapterType) => {
    if (newAdapterType) {
      updateEditingExternalServices(newAdapterType);
    }
  },
);

function cleanNotifier(notifier: Notifier): Notifier {
  const cleaned = { ...notifier };
  // Remove empty config object if no properties
  if (cleaned.config && Object.keys(cleaned.config).length === 0) {
    delete cleaned.config;
  }
  // Remove empty string values for external_service_id
  if (cleaned.external_service_id === "") {
    delete cleaned.external_service_id;
  }
  return cleaned;
}

function addNotifier() {
  newNotifier.value = {
    name: "",
    adapter_type: notifierStore.adapterTypes[0] || "",
    config: {},
    external_service_id: "",
  };
  isEditing.value = false;
  showModal.value = true;
}

function handleEdit(notifier: Notifier) {
  editingNotifier.value = {
    ...notifier,
    config: { ...notifier.config },
    external_service_id: notifier.external_service_id || "",
  };
  isEditing.value = true;
  showModal.value = true;
  // update compatible external services for this adapter type
  if (editingNotifier.value?.adapter_type) {
    updateEditingExternalServices(editingNotifier.value.adapter_type);
  }
}

function cancelAdd() {
  newNotifier.value = undefined;
  editingNotifier.value = undefined;
  isEditing.value = false;
  showModal.value = false;
}

function confirmAdd() {
  if (!newNotifier.value) return;
  const notifierToAdd = cleanNotifier(newNotifier.value);
  notifierStore.addNotifier(notifierToAdd).then(() => {
    notifierStore.loadNotifiers();
    newNotifier.value = undefined;
    showModal.value = false;
  });
}

function confirmEdit() {
  if (!editingNotifier.value) return;
  const notifierToUpdate = cleanNotifier(editingNotifier.value);
  notifierStore
    .updateNotifier(editingNotifier.value.id!.toString(), notifierToUpdate)
    .then(() => {
      notifierStore.loadNotifiers();
      editingNotifier.value = undefined;
      isEditing.value = false;
      showModal.value = false;
    });
}

function handleDelete(notifier: Notifier) {
  notifierStore.deleteNotifier(notifier.id!.toString()).then(() => {
    notifierStore.loadNotifiers();
  });
}

function handleTest(notifier: Notifier) {
  testingNotifierName.value = notifier.name;
  testLoading.value = true;
  testResult.value = null;
  showTestModal.value = true;

  notifierStore
    .testNotifier(notifier.id!.toString())
    .then((result) => {
      testResult.value = result;
      testLoading.value = false;
    })
    .catch((error) => {
      testResult.value = {
        status: "failed",
        message: error.message || "Test failed",
      };
      testLoading.value = false;
    });
}

function closeTestModal() {
  showTestModal.value = false;
  testResult.value = null;
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
  <div class="card bg-base-200 shadow-sm">
  <h2 class="text-2xl font-bold px-6 pt-5 pb-3">Notifier Settings</h2>

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
        <NotifierRow
          v-for="(notifier, i) in notifierStore.notifiers"
          :key="notifier.id"
          v-model="notifierStore.notifiers[i]"
          @edit="handleEdit"
          @delete="handleDelete"
          @test="handleTest"
        />

        <tr v-if="notifierStore.notifiers.length === 0">
          <td colspan="4" class="text-center opacity-50">
            No notifiers configured yet
          </td>
        </tr>

        <tr>
          <th colspan="3" class="text-center">
            <button class="btn btn-primary" @click="addNotifier">
              Add Notifier
            </button>
          </th>
        </tr>
      </tbody>
    </table>
  </div>
  </div>

  <!-- Modal for adding/editing notifier -->
  <dialog :class="['modal', { 'modal-open': showModal }]">
    <div v-if="newNotifier || editingNotifier" class="modal-box max-w-2xl">
      <h3 class="font-bold text-lg mb-4">
        {{ isEditing ? "Edit Notifier" : "Add Notifier" }}
      </h3>

      <form
        @submit.prevent="isEditing ? confirmEdit() : confirmAdd()"
        class="flex flex-col gap-4"
      >
        <template v-if="isEditing && editingNotifier">
          <!-- Name field -->
          <div class="space-y-1">
            <div class="font-medium">
              Name
              <span class="text-sm text-error opacity-60 ml-1 font-normal"
                >(required)</span
              >
            </div>
            <input
              v-model="editingNotifier.name"
              type="text"
              placeholder="Notifier name"
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
              v-model="editingNotifier.adapter_type"
              required
              class="select select-bordered select-sm w-full"
              disabled
            >
              <option
                v-for="adapterType in notifierStore.adapterTypes"
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

          <!-- External Service dropdown -->
          <div v-if="editingRequiresExternalService" class="space-y-1">
            <div class="font-medium">
              External Service
              <span class="text-sm text-error opacity-60 ml-1 font-normal"
                >(required)</span
              >
            </div>
            <select
              v-model="editingNotifier.external_service_id"
              required
              class="select select-bordered select-sm w-full"
            >
              <option value="">Select external service</option>
              <option
                v-for="service in editingCompatibleExternalServices"
                :key="service.id"
                :value="service.id"
              >
                {{ service.name }}
              </option>
            </select>
            <div class="text-sm italic opacity-70">
              Select the external service for this notifier
            </div>
          </div>

          <!-- Dynamic Config Form -->
          <div class="space-y-1">
            <div class="font-medium">Configuration</div>
            <div class="border border-base-300 rounded-lg p-4">
              <NotifierConfigForm
                v-if="editingNotifier.config"
                v-model="editingNotifier.config"
                :adapter-type="editingNotifier.adapter_type"
              />
            </div>
          </div>
        </template>

        <template v-else-if="newNotifier">
          <!-- Name field -->
          <div class="space-y-1">
            <div class="font-medium">
              Name
              <span class="text-sm text-error opacity-60 ml-1 font-normal"
                >(required)</span
              >
            </div>
            <input
              v-model="newNotifier.name"
              type="text"
              placeholder="Notifier name"
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
              v-model="newNotifier.adapter_type"
              required
              class="select select-bordered select-sm w-full"
            >
              <option
                v-for="adapterType in notifierStore.adapterTypes"
                :key="adapterType"
                :value="adapterType"
              >
                {{ formatAdapterType(adapterType) }}
              </option>
            </select>
            <div class="text-sm italic opacity-70">
              Select the type of notifier adapter
            </div>
          </div>

          <!-- External Service dropdown -->
          <div v-if="newRequiresExternalService" class="space-y-1">
            <div class="font-medium">
              External Service
              <span class="text-sm text-error opacity-60 ml-1 font-normal"
                >(required)</span
              >
            </div>
            <select
              v-model="newNotifier.external_service_id"
              required
              class="select select-bordered select-sm w-full"
            >
              <option value="">Select external service</option>
              <option
                v-for="service in newCompatibleExternalServices"
                :key="service.id"
                :value="service.id"
              >
                {{ service.name }}
              </option>
            </select>
            <div class="text-sm italic opacity-70">
              Select the external service for this notifier
            </div>
          </div>

          <!-- Dynamic Config Form -->
          <div class="space-y-1">
            <div class="font-medium">Configuration</div>
            <div class="border border-base-300 rounded-lg p-4">
              <NotifierConfigForm
                v-if="newNotifier.config"
                v-model="newNotifier.config"
                :adapter-type="newNotifier.adapter_type"
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

  <!-- Test Result Modal -->
  <dialog :class="['modal', { 'modal-open': showTestModal }]">
    <div class="modal-box">
      <h3 class="font-bold text-lg mb-4">
        Test Notifier: {{ testingNotifierName }}
      </h3>

      <div v-if="testLoading" class="flex flex-col items-center gap-4 py-8">
        <span class="loading loading-spinner loading-lg"></span>
        <p>Sending test notification...</p>
      </div>

      <div v-else-if="testResult" class="flex flex-col gap-4">
        <div
          class="alert"
          :class="
            testResult.status === 'success' ? 'alert-success' : 'alert-error'
          "
        >
          <span>{{ testResult.status }}</span>
        </div>

        <p v-if="testResult.message" class="text-sm opacity-70">
          {{ testResult.message }}
        </p>
      </div>

      <div class="modal-action">
        <button class="btn btn-primary" @click="closeTestModal">Close</button>
      </div>
    </div>
    <form method="dialog" class="modal-backdrop">
      <button @click="closeTestModal">close</button>
    </form>
  </dialog>
</template>

<style scoped></style>
