<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useNotifierStore } from "../../core/stores/notifierStore";
import NotifierRow from "../../components/notifiers/NotifierRow.vue";
import type { Notifier, TestNotifierResult } from "../../core/models/notifier";
import NotifierConfigForm from "../../components/notifiers/NotifierConfigForm.vue";

const notifierStore = useNotifierStore();
const newNotifier = ref<Notifier | undefined>(undefined);
const editingNotifier = ref<Notifier | undefined>(undefined);
const showModal = ref(false);
const isEditing = ref(false);

// Test result modal state
const showTestModal = ref(false);
const testResult = ref<TestNotifierResult | null>(null);
const testingNotifierName = ref("");
const testLoading = ref(false);

onMounted(() => {
  notifierStore.loadNotifiers();
  notifierStore.loadAdapterTypes();
});

function cleanNotifier(notifier: Notifier): Notifier {
  const cleaned = { ...notifier };
  // Remove empty config object if no properties
  if (cleaned.config && Object.keys(cleaned.config).length === 0) {
    delete cleaned.config;
  }
  return cleaned;
}

function addNotifier() {
  newNotifier.value = {
    name: "",
    adapter_type: notifierStore.adapterTypes[0] || "",
    config: {},
  };
  isEditing.value = false;
  showModal.value = true;
}

function handleEdit(notifier: Notifier) {
  editingNotifier.value = { ...notifier, config: { ...notifier.config } };
  isEditing.value = true;
  showModal.value = true;
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

  notifierStore.testNotifier(notifier.id!.toString()).then((result) => {
    testResult.value = result;
    testLoading.value = false;
  }).catch((error) => {
    testResult.value = {
      success: false,
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
  <h1 class="text-3xl font-bold">Notifier Settings</h1>

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
        <NotifierRow
          v-for="(notifier, i) in notifierStore.notifiers"
          :key="notifier.id"
          v-model="notifierStore.notifiers[i]"
          @edit="handleEdit"
          @delete="handleDelete"
          @test="handleTest"
        />

        <tr>
          <th colspan="4" class="text-center">
            <button class="btn btn-primary" @click="addNotifier">
              Add Notifier
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

  <!-- Modal for adding/editing notifier -->
  <dialog :class="['modal', { 'modal-open': showModal }]">
    <div v-if="newNotifier || editingNotifier" class="modal-box max-w-2xl">
      <h3 class="font-bold text-lg mb-4">
        {{ isEditing ? 'Edit Notifier' : 'Add Notifier' }}
      </h3>

      <form
        @submit.prevent="isEditing ? confirmEdit() : confirmAdd()"
        class="flex flex-col gap-4"
      >
        <template v-if="isEditing && editingNotifier">
          <!-- Name field -->
          <div class="form-control">
            <label class="label">
              <span class="label-text">Name <span class="text-error">*</span></span>
            </label>
            <input
              v-model="editingNotifier.name"
              type="text"
              placeholder="Notifier name"
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
              v-model="editingNotifier.adapter_type"
              required
              class="select select-bordered"
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
          </div>

          <!-- Dynamic Config Form -->
          <div class="form-control">
            <label class="label">
              <span class="label-text font-semibold">Configuration</span>
            </label>
            <div class="border border-base-300 rounded-lg p-4">
              <NotifierConfigForm
                v-model="editingNotifier.config!"
                :adapter-type="editingNotifier.adapter_type"
              />
            </div>
          </div>
        </template>

        <template v-else-if="newNotifier">
          <!-- Name field -->
          <div class="form-control">
            <label class="label">
              <span class="label-text">Name <span class="text-error">*</span></span>
            </label>
            <input
              v-model="newNotifier.name"
              type="text"
              placeholder="Notifier name"
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
              v-model="newNotifier.adapter_type"
              required
              class="select select-bordered"
            >
              <option
                v-for="adapterType in notifierStore.adapterTypes"
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
              <NotifierConfigForm
                v-model="newNotifier.config!"
                :adapter-type="newNotifier.adapter_type"
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
        <div class="alert" :class="testResult.success ? 'alert-success' : 'alert-error'">
          <span>{{ testResult.success ? 'Test notification sent successfully!' : 'Test notification failed' }}</span>
        </div>

        <p v-if="testResult.message" class="text-sm opacity-70">
          {{ testResult.message }}
        </p>
      </div>

      <div class="modal-action">
        <button class="btn btn-primary" @click="closeTestModal">
          Close
        </button>
      </div>
    </div>
    <form method="dialog" class="modal-backdrop">
      <button @click="closeTestModal">close</button>
    </form>
  </dialog>
</template>

<style scoped></style>
