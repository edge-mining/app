<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useOptimizationUnitStore } from "../../core/stores/optimizationUnitStore";
import { usePolicyStore } from "../../core/stores/policyStore";
import { useMinerStore } from "../../core/stores/minerStore";
import { useEnergySourceStore } from "../../core/stores/energySourceStore";
import { useForecastProviderStore } from "../../core/stores/forecastProviderStore";
import { useNotifierStore } from "../../core/stores/notifierStore";
import OptimizationUnitRow from "../../components/optimizationUnits/OptimizationUnitRow.vue";
import type { OptimizationUnit } from "../../core/models/optimizationUnit";

const optimizationUnitStore = useOptimizationUnitStore();
const policyStore = usePolicyStore();
const minerStore = useMinerStore();
const energySourceStore = useEnergySourceStore();
const forecastProviderStore = useForecastProviderStore();
const notifierStore = useNotifierStore();

// Form data used for both add and edit
const formData = ref({
  name: "",
  description: "",
  policy_id: undefined as string | undefined,
  energy_source_id: undefined as string | undefined,
  home_forecast_provider_id: undefined as string | undefined,
});

const editingUnitId = ref<string | undefined>(undefined);
const showModal = ref(false);
const isEditing = ref(false);

// Multi-select state for miners and notifiers
const selectedMinerIds = ref<string[]>([]);
const selectedNotifierIds = ref<string[]>([]);

onMounted(() => {
  optimizationUnitStore.loadOptimizationUnits();
  policyStore.loadPolicies();
  minerStore.loadMiners();
  energySourceStore.loadEnergySources();
  forecastProviderStore.loadForecastProviders();
  notifierStore.loadNotifiers();
});

function resetForm() {
  formData.value = {
    name: "",
    description: "",
    policy_id: undefined,
    energy_source_id: undefined,
    home_forecast_provider_id: undefined,
  };
  selectedMinerIds.value = [];
  selectedNotifierIds.value = [];
  editingUnitId.value = undefined;
}

function addUnit() {
  resetForm();
  isEditing.value = false;
  showModal.value = true;
}

function handleEdit(unit: OptimizationUnit) {
  formData.value = {
    name: unit.name,
    description: unit.description || "",
    policy_id: unit.policy_id,
    energy_source_id: unit.energy_source_id,
    home_forecast_provider_id: unit.home_forecast_provider_id,
  };
  selectedMinerIds.value = [...unit.target_miner_ids];
  selectedNotifierIds.value = [...unit.notifier_ids];
  editingUnitId.value = unit.id;
  isEditing.value = true;
  showModal.value = true;
}

function cancelModal() {
  resetForm();
  isEditing.value = false;
  showModal.value = false;
}

function confirmAdd() {
  const unitToAdd = {
    name: formData.value.name,
    description: formData.value.description || undefined,
    policy_id: formData.value.policy_id,
    target_miner_ids: selectedMinerIds.value,
    energy_source_id: formData.value.energy_source_id,
    home_forecast_provider_id: formData.value.home_forecast_provider_id,
    notifier_ids: selectedNotifierIds.value,
  };
  optimizationUnitStore.addOptimizationUnit(unitToAdd).then(() => {
    optimizationUnitStore.loadOptimizationUnits();
    resetForm();
    showModal.value = false;
  });
}

function confirmEdit() {
  if (!editingUnitId.value) return;
  const unitToUpdate = {
    name: formData.value.name,
    description: formData.value.description || undefined,
    policy_id: formData.value.policy_id,
    target_miner_ids: selectedMinerIds.value,
    energy_source_id: formData.value.energy_source_id,
    home_forecast_provider_id: formData.value.home_forecast_provider_id,
    notifier_ids: selectedNotifierIds.value,
  };
  optimizationUnitStore
    .updateOptimizationUnit(editingUnitId.value, unitToUpdate)
    .then(() => {
      optimizationUnitStore.loadOptimizationUnits();
      resetForm();
      isEditing.value = false;
      showModal.value = false;
    });
}

function handleDelete(unit: OptimizationUnit) {
  optimizationUnitStore.deleteOptimizationUnit(unit.id!).then(() => {
    optimizationUnitStore.loadOptimizationUnits();
  });
}

function handleToggleEnabled(unit: OptimizationUnit) {
  const action = unit.is_enabled
    ? optimizationUnitStore.disableOptimizationUnit(unit.id!)
    : optimizationUnitStore.enableOptimizationUnit(unit.id!);

  action.then(() => {
    optimizationUnitStore.loadOptimizationUnits();
  });
}

function toggleMinerSelection(minerId: string) {
  const index = selectedMinerIds.value.indexOf(minerId);
  if (index === -1) {
    selectedMinerIds.value.push(minerId);
  } else {
    selectedMinerIds.value.splice(index, 1);
  }
}

function toggleNotifierSelection(notifierId: string) {
  const index = selectedNotifierIds.value.indexOf(notifierId);
  if (index === -1) {
    selectedNotifierIds.value.push(notifierId);
  } else {
    selectedNotifierIds.value.splice(index, 1);
  }
}

function isMinerSelected(minerId: string): boolean {
  return selectedMinerIds.value.includes(minerId);
}

function isNotifierSelected(notifierId: string): boolean {
  return selectedNotifierIds.value.includes(notifierId);
}

function handleSubmit() {
  if (isEditing.value) {
    confirmEdit();
  } else {
    confirmAdd();
  }
}
</script>

<template>
  <div class="card">
    <div class="card-header">
      <h2>Optimization Units Settings</h2>
    </div>
    <div class="card-body">
      <div class="overflow-x-auto">
        <table class="table">
          <thead>
            <tr>
              <th>Enabled</th>
              <th>Name / Description</th>
              <th>ID</th>
              <th>Assignments</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <OptimizationUnitRow v-for="(unit, i) in optimizationUnitStore.optimizationUnits" :key="unit.id"
              v-model="optimizationUnitStore.optimizationUnits[i]" @edit="handleEdit" @delete="handleDelete"
              @toggle-enabled="handleToggleEnabled" />

            <tr>
              <th colspan="5" class="text-center">
                <button class="btn btn-primary" @click="addUnit">
                  Add Optimization Unit
                </button>
              </th>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- Modal for adding/editing optimization unit -->
  <dialog :class="['modal', { 'modal-open': showModal }]">
    <div class="modal-box max-w-3xl">
      <h3 class="font-bold text-lg mb-4">
        {{ isEditing ? "Edit Optimization Unit" : "Add Optimization Unit" }}
      </h3>

      <form @submit.prevent="handleSubmit" class="flex flex-col gap-4">
        <!-- Basic Info -->
        <div class="form-control">
          <label class="label">
            <span class="label-text">Name <span class="text-error">*</span></span>
          </label>
          <input v-model="formData.name" type="text" placeholder="Optimization unit name" required
            class="input input-bordered" />
        </div>

        <div class="form-control">
          <label class="label">
            <span class="label-text">Description</span>
          </label>
          <textarea v-model="formData.description" placeholder="Optimization unit description"
            class="textarea textarea-bordered" rows="2"></textarea>
        </div>

        <!-- Policy Selection -->
        <div class="form-control">
          <label class="label">
            <span class="label-text">Policy</span>
          </label>
          <select v-model="formData.policy_id" class="select select-bordered">
            <option :value="undefined">No policy selected</option>
            <option v-for="policy in policyStore.policies" :key="policy.id" :value="policy.id?.toString()">
              {{ policy.name }}
            </option>
          </select>
        </div>

        <!-- Energy Source Selection -->
        <div class="form-control">
          <label class="label">
            <span class="label-text">Energy Source</span>
          </label>
          <select v-model="formData.energy_source_id" class="select select-bordered">
            <option :value="undefined">No energy source selected</option>
            <option v-for="source in energySourceStore.energySources" :key="source.id" :value="source.id?.toString()">
              {{ source.name }}
            </option>
          </select>
        </div>

        <!-- Forecast Provider Selection -->
        <div class="form-control">
          <label class="label">
            <span class="label-text">Home Forecast Provider</span>
          </label>
          <select v-model="formData.home_forecast_provider_id" class="select select-bordered">
            <option :value="undefined">No forecast provider selected</option>
            <option v-for="provider in forecastProviderStore.forecastProviders" :key="provider.id"
              :value="provider.id?.toString()">
              {{ provider.name }}
            </option>
          </select>
        </div>

        <!-- Miners Multi-Select -->
        <div class="form-control">
          <label class="label">
            <span class="label-text">Target Miners</span>
          </label>
          <div class="border border-base-300 rounded-lg p-3 max-h-48 overflow-y-auto">
            <div v-if="minerStore.miners.length === 0" class="text-base-content/50 text-center py-2">
              No miners available
            </div>
            <div v-for="miner in minerStore.miners" :key="miner.id" class="form-control">
              <label class="label cursor-pointer justify-start gap-3 py-1">
                <input type="checkbox" class="checkbox checkbox-sm checkbox-primary"
                  :checked="isMinerSelected(miner.id!.toString())"
                  @change="toggleMinerSelection(miner.id!.toString())" />
                <span class="label-text">{{ miner.name }}</span>
              </label>
            </div>
          </div>
          <label class="label">
            <span class="label-text-alt">{{ selectedMinerIds.length }} miners selected</span>
          </label>
        </div>

        <!-- Notifiers Multi-Select -->
        <div class="form-control">
          <label class="label">
            <span class="label-text">Notifiers</span>
          </label>
          <div class="border border-base-300 rounded-lg p-3 max-h-48 overflow-y-auto">
            <div v-if="notifierStore.notifiers.length === 0" class="text-base-content/50 text-center py-2">
              No notifiers available
            </div>
            <div v-for="notifier in notifierStore.notifiers" :key="notifier.id" class="form-control">
              <label class="label cursor-pointer justify-start gap-3 py-1">
                <input type="checkbox" class="checkbox checkbox-sm checkbox-primary"
                  :checked="isNotifierSelected(notifier.id!.toString())"
                  @change="toggleNotifierSelection(notifier.id!.toString())" />
                <span class="label-text">{{ notifier.name }}</span>
              </label>
            </div>
          </div>
          <label class="label">
            <span class="label-text-alt">{{ selectedNotifierIds.length }} notifiers selected</span>
          </label>
        </div>

        <!-- Modal actions -->
        <div class="modal-action">
          <button type="button" class="btn btn-secondary" @click="cancelModal">
            Cancel
          </button>
          <button type="submit" class="btn btn-primary">
            {{ isEditing ? "Save" : "Add" }}
          </button>
        </div>
      </form>
    </div>
    <form method="dialog" class="modal-backdrop">
      <button @click="cancelModal">close</button>
    </form>
  </dialog>
</template>

<style scoped></style>
