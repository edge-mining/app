<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useMinerControllerStore } from "../../core/stores/minerControllerStore";
import { useExternalServiceStore } from "../../core/stores/externalServiceStore";
import { useMinerStore } from "../../core/stores/minerStore";
import MinerControllerRow from "../../components/minerControllers/MinerControllerRow.vue";
import type { MinerController } from "../../core/models/minerController";
import MinerControllerConfigForm from "../../components/minerControllers/MinerControllerConfigForm.vue";

const minerControllerStore = useMinerControllerStore();
const externalServiceStore = useExternalServiceStore();
const minerStore = useMinerStore();
const newMinerController = ref<MinerController | undefined>(undefined);
const editingMinerController = ref<MinerController | undefined>(undefined);
const showModal = ref(false);
const isEditing = ref(false);

onMounted(() => {
  minerControllerStore.loadMinerControllers();
  minerControllerStore.loadAdapterTypes();
  externalServiceStore.loadExternalServices();
  minerStore.loadMiners();
});

function cleanMinerController(minerController: MinerController): MinerController {
  const cleaned = { ...minerController };
  // Remove empty config object if no properties
  if (cleaned.config && Object.keys(cleaned.config).length === 0) {
    delete cleaned.config;
  }
  // Remove empty string values for external_service_id
  if ((cleaned as any).external_service_id === "") {
    delete (cleaned as any).external_service_id;
  }
  return cleaned;
}

function addMinerController() {
  newMinerController.value = {
    name: "",
    adapter_type: minerControllerStore.adapterTypes[0] || "",
    config: {},
    external_service_id: "",
  };
  isEditing.value = false;
  showModal.value = true;
}

function handleEdit(minerController: MinerController) {
  editingMinerController.value = { ...minerController };
  isEditing.value = true;
  showModal.value = true;
}

function cancelAdd() {
  newMinerController.value = undefined;
  editingMinerController.value = undefined;
  isEditing.value = false;
  showModal.value = false;
}

function confirmAdd() {
  if (!newMinerController.value) return;
  const minerControllerToAdd = cleanMinerController(newMinerController.value);
  minerControllerStore.addMinerController(minerControllerToAdd).then(() => {
    minerControllerStore.loadMinerControllers();
    newMinerController.value = undefined;
    showModal.value = false;
  });
}

function confirmEdit() {
  if (!editingMinerController.value) return;
  const minerControllerToUpdate = cleanMinerController(editingMinerController.value);
  minerControllerStore
    .updateMinerController(editingMinerController.value.id!.toString(), minerControllerToUpdate)
    .then(() => {
      minerControllerStore.loadMinerControllers();
      editingMinerController.value = undefined;
      isEditing.value = false;
      showModal.value = false;
    });
}

function handleDelete(minerController: MinerController) {
  minerControllerStore.deleteMinerController(minerController.id!.toString()).then(() => {
    minerControllerStore.loadMinerControllers();
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
  <h1 class="text-3xl font-bold">Miner Controller Settings</h1>

  <div class="overflow-x-auto">
    <table class="table">
      <!-- head -->
      <thead>
        <tr>
          <th>Name</th>
          <th>Controller Type</th>
          <th>Assigned Miners</th>
          <th>External Service</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <MinerControllerRow
          v-for="(minerController, i) in minerControllerStore.minerControllers" 
          :key="minerController.id"
          v-model="minerControllerStore.minerControllers[i]"
          :all-miners="minerStore.miners"
          @edit="handleEdit"
          @delete="handleDelete"
        />
        
        <tr v-if="minerControllerStore.minerControllers.length === 0">
          <td colspan="5" class="text-center opacity-50">
            No miner controllers configured yet
          </td>
        </tr>

        <tr>
          <th colspan="5" class="text-center">
            <button class="btn btn-primary" @click="addMinerController">
              Add Miner Controller
            </button>
          </th>
        </tr>
      </tbody>
      <!-- foot -->
      <tfoot>
        <tr>
          <th>Name</th>
          <th>Controller Type</th>
          <th>Assigned Miners</th>
          <th>External Service</th>
          <th>Actions</th>
        </tr>
      </tfoot>
    </table>
  </div>

  <!-- Modal for adding/editing miner controller -->
  <dialog :class="['modal', { 'modal-open': showModal }]">
    <div v-if="newMinerController || editingMinerController" class="modal-box max-w-2xl">
      <h3 class="font-bold text-lg mb-4">
        {{ isEditing ? 'Edit Miner Controller' : 'Add Miner Controller' }}
      </h3>

      <form
        @submit.prevent="isEditing ? confirmEdit() : confirmAdd()"
        class="flex flex-col gap-4"
      >
        <template v-if="isEditing && editingMinerController">
          <!-- Name field -->
          <div class="space-y-1">
            <div class="font-medium">
              Name
              <span class="text-sm text-error opacity-60 ml-1 font-normal">(required)</span>
            </div>
            <input
              v-model="editingMinerController.name"
              type="text"
              placeholder="Miner controller name"
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
              v-model="editingMinerController.adapter_type"
              required
              class="select select-bordered select-sm w-full"
              disabled
            >
              <option
                v-for="adapterType in minerControllerStore.adapterTypes"
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
          
          <!-- External Service selection -->
          <div class="space-y-1">
            <div class="font-medium">External Service</div>
            <select
              v-model="editingMinerController.external_service_id"
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
            <div class="font-medium">
              Configuration
            </div>
            <div class="border border-base-300 rounded-lg p-4">
              <MinerControllerConfigForm
                v-if="editingMinerController.config"
                v-model="editingMinerController.config"
                :adapter-type="editingMinerController.adapter_type"
              />
            </div>
          </div>
        </template>

        <template v-else-if="newMinerController">
          <!-- Name field -->
          <div class="space-y-1">
            <div class="font-medium">
              Name
              <span class="text-sm text-error opacity-60 ml-1 font-normal">(required)</span>
            </div>
            <input
              v-model="newMinerController.name"
              type="text"
              placeholder="Miner controller name"
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
              v-model="newMinerController.adapter_type"
              required
              class="select select-bordered select-sm w-full"
            >
              <option
                v-for="adapterType in minerControllerStore.adapterTypes"
                :key="adapterType"
                :value="adapterType"
              >
                {{ formatAdapterType(adapterType) }}
              </option>
            </select>
            <div class="text-sm italic opacity-70">
              Select the type of miner controller adapter
            </div>
          </div>

          <!-- External Service selection -->
          <div class="space-y-1">
            <div class="font-medium">External Service</div>
            <select
              v-model="newMinerController.external_service_id"
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
            <div class="font-medium">
              Configuration
            </div>
            <div class="border border-base-300 rounded-lg p-4">
              <MinerControllerConfigForm
                v-if="newMinerController.config"
                v-model="newMinerController.config"
                :adapter-type="newMinerController.adapter_type"
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
            {{ isEditing ? 'Save' : 'Add' }}
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
