<script setup lang="ts">
import { computed, ref, watch, toRaw } from "vue";
import type { Miner, MinerStateSnapshot } from "../../core/models/miner";
import { useMinerControllerStore } from "../../core/stores/minerControllerStore";
import { MinerControllerService } from "../../core/services/minerControllerService";
import {
  PhX,
  PhFloppyDisk,
  PhCpu,
  PhLightning,
  PhGear,
  PhDownloadSimple,
  PhCheck,
  PhPlus,
  PhTrash,
} from "@phosphor-icons/vue";

const props = defineProps<{
  open: boolean;
  miner?: Miner;
  allMiners?: Miner[];
  isEdit?: boolean;
}>();

const emit = defineEmits<{
  close: [];
  save: [miner: Miner, controllerChanges: { add: string[]; remove: string[] }];
}>();

const minerControllerStore = useMinerControllerStore();
const minerControllerService = new MinerControllerService();

// Hash rate unit options
const hashRateUnits = ["H/s", "KH/s", "MH/s", "GH/s", "TH/s", "PH/s", "EH/s"];

// Local form state
const formData = ref<Miner>({
  name: "",
  active: false,
  hash_rate_max: { value: 100, unit: "TH/s" },
  power_consumption_max: 3000,
});

// Controller binding state (managed separately from miner data)
const selectedControllerIds = ref<string[]>([]);
const originalControllerIds = ref<string[]>([]);

// Watch for changes in the prop to reset form
watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      if (props.miner) {
        formData.value = {
          ...props.miner,
          hash_rate_max: props.miner.hash_rate_max
            ? { ...props.miner.hash_rate_max }
            : { value: 100, unit: "TH/s" },
        };
        selectedControllerIds.value = [...(props.miner.controller_ids ?? [])];
        originalControllerIds.value = [...(props.miner.controller_ids ?? [])];
      } else {
        formData.value = {
          name: "",
          active: false,
          hash_rate_max: { value: 100, unit: "TH/s" },
          power_consumption_max: 3000,
        };
        selectedControllerIds.value = [];
        originalControllerIds.value = [];
      }
    }
  },
  { immediate: true }
);

// Available controllers not yet selected
const availableControllers = computed(() => {
  return minerControllerStore.minerControllers.filter(
    (controller) => !selectedControllerIds.value.includes(controller.id!)
  );
});

// Controller ID being added from the dropdown
const controllerToAdd = ref<string | undefined>(undefined);

function addController() {
  if (controllerToAdd.value && !selectedControllerIds.value.includes(controllerToAdd.value)) {
    selectedControllerIds.value.push(controllerToAdd.value);
    controllerToAdd.value = undefined;
  }
}

function removeController(controllerId: string) {
  selectedControllerIds.value = selectedControllerIds.value.filter((id) => id !== controllerId);
}

function getControllerName(controllerId: string): string {
  const controller = minerControllerStore.minerControllers.find((mc) => mc.id === controllerId);
  return controller?.name ?? controllerId;
}

// Compute controller changes (diff)
const controllerChanges = computed(() => {
  const add = selectedControllerIds.value.filter(
    (id) => !originalControllerIds.value.includes(id)
  );
  const remove = originalControllerIds.value.filter(
    (id) => !selectedControllerIds.value.includes(id)
  );
  return { add, remove };
});

const isFormValid = computed(() => {
  return (
    formData.value.name.trim().length > 0 &&
    formData.value.hash_rate_max &&
    formData.value.hash_rate_max.value > 0 &&
    formData.value.power_consumption_max &&
    formData.value.power_consumption_max > 0
  );
});

function handleClose() {
  emit("close");
}

const isFetchingDetails = ref(false);
const fetchSuccess = ref(false);
const fetchError = ref<string | null>(null);
const highlightedFields = ref<Set<string>>(new Set());
const fetchControllerId = ref<string | undefined>(undefined);

async function fetchMinerDetails(controllerId: string) {
  if (!controllerId) return;
  fetchControllerId.value = controllerId;
  isFetchingDetails.value = true;
  fetchError.value = null;
  fetchSuccess.value = false;
  highlightedFields.value = new Set();
  try {
    const snapshot: MinerStateSnapshot = await minerControllerService.getMinerDetails(controllerId);
    const updated = new Set<string>();
    // Auto-fill max values from current runtime readings
    if (snapshot.hash_rate && snapshot.hash_rate.value > 0) {
      formData.value.hash_rate_max = { value: snapshot.hash_rate.value, unit: snapshot.hash_rate.unit || "TH/s" };
      updated.add("hash_rate_max");
    }
    if (snapshot.power_consumption && snapshot.power_consumption > 0) {
      formData.value.power_consumption_max = snapshot.power_consumption;
      updated.add("power_consumption_max");
    }
    highlightedFields.value = updated;
    fetchSuccess.value = true;
    setTimeout(() => {
      fetchSuccess.value = false;
      highlightedFields.value = new Set();
      fetchControllerId.value = undefined;
    }, 3000);
  } catch (error: any) {
    fetchError.value = error?.response?.data?.detail || error?.message || "Failed to fetch miner details from controller";
  } finally {
    isFetchingDetails.value = false;
  }
}

function handleSave() {
  if (isFormValid.value) {
    // Deep clone to remove Vue reactive proxies
    const rawData = JSON.parse(JSON.stringify(toRaw(formData.value)));
    // Remove controller-related fields from miner payload (backend no longer accepts them)
    delete rawData.features;
    delete rawData.controller_ids;
    emit("save", rawData, { ...controllerChanges.value });
  }
}
</script>

<template>
  <dialog class="modal" :class="{ 'modal-open': open }">
    <div class="modal-box max-w-2xl bg-base-100 border border-base-300/60">
      <!-- Header -->
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-3">
          <div class="h-10 w-10 rounded-xl bg-base-200/60 flex items-center justify-center">
            <PhCpu :size="22" class="text-primary" />
          </div>
          <h3 class="text-xl font-bold">
            {{ isEdit ? "Edit Miner" : "Add Miner" }}
          </h3>
        </div>
        <button class="btn btn-ghost btn-sm btn-square" @click="handleClose">
          <PhX :size="20" />
        </button>
      </div>

      <!-- Required fields note -->
      <p class="text-xs text-base-content/50 mb-4">* Required fields</p>

      <!-- Form -->
      <form class="space-y-6" @submit.prevent="handleSave">
        <!-- Basic Info -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- Name Input -->
          <div class="form-control">
            <label class="label mb-1">
              <span class="label-text font-medium">Name *</span>
            </label>
            <input
              v-model="formData.name"
              type="text"
              placeholder="Enter miner name"
              class="input input-bordered w-full"
              required
            />
          </div>

          <!-- Model Input -->
          <div class="form-control">
            <label class="label mb-1">
              <span class="label-text font-medium">Model</span>
            </label>
            <input
              v-model="formData.model"
              type="text"
              placeholder="e.g., Antminer S19 Pro"
              class="input input-bordered w-full transition-colors duration-500"
              :class="{ 'input-success border-success': highlightedFields.has('model') }"
            />
          </div>
        </div>

        <!-- Controllers -->
        <div class="divider text-xs text-base-content/50 my-4">
          CONTROLLERS
        </div>

        <div class="form-control">
          <label class="label mb-1">
            <span class="label-text flex items-center gap-2">
              <PhGear :size="16" class="text-info" />
              Miner Controllers
            </span>
          </label>

          <!-- Selected controllers list -->
          <div v-if="selectedControllerIds.length > 0" class="space-y-2 mb-3">
            <div
              v-for="controllerId in selectedControllerIds"
              :key="controllerId"
              class="flex items-center gap-2 bg-base-200/40 rounded-lg px-3 py-2"
            >
              <PhGear :size="14" class="text-info flex-shrink-0" />
              <span class="text-sm text-base-content flex-1 truncate">{{ getControllerName(controllerId) }}</span>
              <button
                type="button"
                class="btn btn-ghost btn-xs btn-square"
                :class="fetchControllerId === controllerId && fetchSuccess ? 'text-success' : 'text-primary'"
                :disabled="isFetchingDetails"
                @click="fetchMinerDetails(controllerId)"
                title="Fetch Miner Details"
              >
                <PhCheck v-if="fetchControllerId === controllerId && fetchSuccess" :size="14" />
                <PhDownloadSimple v-else :size="14" :class="{ 'animate-bounce': isFetchingDetails && fetchControllerId === controllerId }" />
              </button>
              <button
                type="button"
                class="btn btn-ghost btn-xs btn-square text-error"
                @click="removeController(controllerId)"
                title="Remove controller"
              >
                <PhTrash :size="14" />
              </button>
            </div>
          </div>

          <!-- Add controller row -->
          <div class="flex gap-2">
            <select
              v-model="controllerToAdd"
              class="select select-bordered flex-1"
            >
              <option :value="undefined">Select a controller to add...</option>
              <option
                v-for="controller in availableControllers"
                :key="controller.id"
                :value="controller.id"
              >
                {{ controller.name }}
              </option>
            </select>
            <button
              type="button"
              class="btn btn-outline btn-primary"
              :disabled="!controllerToAdd"
              @click="addController"
              title="Add Controller"
            >
              <PhPlus :size="18" />
            </button>
          </div>
          <label class="label mt-1">
            <span class="label-text-alt text-base-content/50">
              Controllers provide monitoring and control capabilities
            </span>
          </label>
          <div v-if="fetchError" class="alert alert-error alert-sm mt-2 py-2 text-sm">
            <PhX :size="16" class="cursor-pointer shrink-0" @click="fetchError = null" />
            <span>{{ fetchError }}</span>
          </div>
        </div>

        <!-- Performance Settings -->
        <div class="divider text-xs text-base-content/50 my-4">
          PERFORMANCE LIMITS
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- Hash Rate Max -->
          <div class="form-control">
            <label class="label mb-1">
              <span class="label-text flex items-center gap-2">
                <PhCpu :size="16" class="text-emerald-400" />
                Max Hash Rate *
              </span>
            </label>
            <div class="flex gap-2">
              <input
                v-model.number="formData.hash_rate_max!.value"
                type="number"
                min="0"
                class="input input-bordered flex-1 transition-colors duration-500"
                :class="{ 'input-success border-success': highlightedFields.has('hash_rate_max') }"
                placeholder="100"
                required
              />
              <select
                v-model="formData.hash_rate_max!.unit"
                class="select select-bordered w-24"
              >
                <option v-for="unit in hashRateUnits" :key="unit" :value="unit">
                  {{ unit }}
                </option>
              </select>
            </div>
          </div>

          <!-- Power Consumption Max -->
          <div class="form-control">
            <label class="label mb-1">
              <span class="label-text flex items-center gap-2">
                <PhLightning :size="16" class="text-amber-400" />
                Max Power Consumption *
              </span>
            </label>
            <label class="input input-bordered flex items-center gap-2 transition-colors duration-500"
              :class="{ 'input-success border-success': highlightedFields.has('power_consumption_max') }">
              <input
                v-model.number="formData.power_consumption_max"
                type="number"
                min="0"
                class="grow"
                placeholder="3000"
                required
              />
              <span class="text-sm text-base-content/50">W</span>
            </label>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex justify-end gap-3 pt-4 border-t border-base-300/40">
          <button type="button" class="btn btn-ghost" @click="handleClose">Cancel</button>
          <button
            type="submit"
            class="btn btn-primary"
            :disabled="!isFormValid"
          >
            <PhFloppyDisk :size="18" />
            {{ isEdit ? "Save Changes" : "Create" }}
          </button>
        </div>
      </form>
    </div>
    <form method="dialog" class="modal-backdrop bg-black/60" @click="handleClose">
      <button>close</button>
    </form>
  </dialog>
</template>

<style scoped>
.input-success {
  animation: highlight-fade 3s ease-out;
}

@keyframes highlight-fade {
  0%, 60% {
    border-color: oklch(var(--su));
    background-color: oklch(var(--su) / 0.05);
  }
  100% {
    border-color: initial;
    background-color: initial;
  }
}
</style>
