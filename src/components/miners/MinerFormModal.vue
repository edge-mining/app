<script setup lang="ts">
import { computed, ref, watch, toRaw } from "vue";
import { MinerFeatureType, type Miner, type MinerStateSnapshot } from "../../core/models/miner";
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
  PhEye,
  PhToggleRight,
  PhMagnifyingGlass,
  PhWarningCircle,
  PhArrowsDownUp,
  PhCaretUp,
  PhCaretDown,
} from "@phosphor-icons/vue";
import type { MinerFeature } from "../../core/models/miner";
import { formatType } from "../../core/utils/formatters";

const props = defineProps<{
  open: boolean;
  miner?: Miner;
  allMiners?: Miner[];
  isEdit?: boolean;
}>();

const emit = defineEmits<{
  close: [];
  save: [miner: Miner, controllerChanges: { add: string[]; remove: string[] }, featureUpdates: MinerFeature[]];
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

// Feature state (working copy for editing)
const localFeatures = ref<MinerFeature[]>([]);
const originalFeatures = ref<MinerFeature[]>([]);

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
        localFeatures.value = (props.miner.features ?? []).map((f) => ({ ...f }));
        originalFeatures.value = (props.miner.features ?? []).map((f) => ({ ...f }));
      } else {
        formData.value = {
          name: "",
          active: false,
          hash_rate_max: { value: 100, unit: "TH/s" },
          power_consumption_max: 3000,
        };
        selectedControllerIds.value = [];
        originalControllerIds.value = [];
        localFeatures.value = [];
        originalFeatures.value = [];
      }
    }
  },
  { immediate: true }
);

// Controller IDs already assigned to other miners
const assignedControllerIds = computed(() => {
  if (!props.allMiners) return new Set<string>();
  return new Set(
    props.allMiners
      .filter((m) => m.id !== formData.value.id)
      .flatMap((m) => m.controller_ids ?? [])
  );
});

// Available controllers: not yet selected for this miner AND not assigned to other miners
const availableControllers = computed(() => {
  return minerControllerStore.minerControllers.filter(
    (controller) =>
      !selectedControllerIds.value.includes(controller.id!) &&
      !assignedControllerIds.value.has(controller.id!)
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

function getControllerAdapterType(controllerId: string): string | undefined {
  const controller = minerControllerStore.minerControllers.find((mc) => mc.id === controllerId);
  return controller?.adapter_type;
}

const adapterBadgeClass: Record<string, string> = {
  dummy: "bg-slate-500/20 text-slate-400",
  pyasic: "bg-emerald-500/20 text-emerald-400",
  generic_socket_home_assistant_api: "bg-sky-500/20 text-sky-400",
};

function getAdapterBadgeClass(controllerId: string): string {
  const adapterType = getControllerAdapterType(controllerId);
  return adapterType ? (adapterBadgeClass[adapterType] ?? "badge-ghost") : "badge-ghost";
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

const fetchError = ref<string | null>(null);
const highlightedFields = ref<Set<string>>(new Set());

// Per-field fetch state
const fieldFetching = ref<Record<string, boolean>>({});
const fieldFetchSuccess = ref<Record<string, boolean>>({});

// Resolve which selected controllers provide a given feature type (from localFeatures)
function controllersForFeature(featureType: MinerFeatureType): string[] {
  const seen = new Set<string>();
  return localFeatures.value
    .filter(
      (f) =>
        f.feature_type === featureType &&
        f.enabled &&
        selectedControllerIds.value.includes(f.controller_id)
    )
    .sort((a, b) => b.priority - a.priority)
    .map((f) => f.controller_id)
    .filter((id) => {
      if (seen.has(id)) return false;
      seen.add(id);
      return true;
    });
}

// --- Feature management ---

// Group features by type (only for selected controllers)
const featuresByType = computed(() => {
  const groups = new Map<MinerFeatureType, MinerFeature[]>();
  for (const feature of localFeatures.value) {
    if (!selectedControllerIds.value.includes(feature.controller_id)) continue;
    const existing = groups.get(feature.feature_type) || [];
    existing.push(feature);
    groups.set(feature.feature_type, existing);
  }
  // Sort each group by priority descending
  for (const [key, features] of groups) {
    groups.set(key, features.sort((a, b) => b.priority - a.priority));
  }
  return groups;
});

// Feature category icon
function getFeatureCategoryIcon(featureType: string) {
  if (featureType.endsWith('_control')) return PhToggleRight;
  if (featureType === 'model_detection') return PhMagnifyingGlass;
  return PhEye;
}

// Determine role of a feature within its group
function getFeatureRole(feature: MinerFeature): 'active' | 'fallback' | 'disabled' {
  if (!feature.enabled) return 'disabled';
  const group = featuresByType.value.get(feature.feature_type) || [];
  const enabledFeatures = group.filter((f) => f.enabled);
  if (enabledFeatures.length === 0) return 'disabled';
  // The one with highest priority is active
  if (enabledFeatures[0].controller_id === feature.controller_id) return 'active';
  return 'fallback';
}

// Check if a feature type has multiple enabled providers
function hasMultipleProviders(featureType: MinerFeatureType): boolean {
  const group = featuresByType.value.get(featureType) || [];
  return group.filter((f) => f.enabled).length > 1;
}

// Toggle feature enabled state
function toggleFeatureEnabled(featureType: MinerFeatureType, controllerId: string) {
  const idx = localFeatures.value.findIndex(
    (f) => f.feature_type === featureType && f.controller_id === controllerId
  );
  if (idx !== -1) {
    localFeatures.value[idx] = {
      ...localFeatures.value[idx],
      enabled: !localFeatures.value[idx].enabled,
    };
  }
}

// Update feature priority
function updateFeaturePriority(featureType: MinerFeatureType, controllerId: string, priority: number) {
  const idx = localFeatures.value.findIndex(
    (f) => f.feature_type === featureType && f.controller_id === controllerId
  );
  if (idx !== -1) {
    localFeatures.value[idx] = {
      ...localFeatures.value[idx],
      priority: Math.max(1, Math.min(100, priority)),
    };
  }
}

// Check if features have been modified
const hasFeatureChanges = computed(() => {
  if (localFeatures.value.length !== originalFeatures.value.length) return true;
  return localFeatures.value.some((f) => {
    const orig = originalFeatures.value.find(
      (o) => o.feature_type === f.feature_type && o.controller_id === f.controller_id
    );
    if (!orig) return true;
    return f.enabled !== orig.enabled || f.priority !== orig.priority;
  });
});

const modelControllers = computed(() => controllersForFeature(MinerFeatureType.MODEL_DETECTION));
const hashRateControllers = computed(() => controllersForFeature(MinerFeatureType.HASHRATE_MONITORING));
const powerControllers = computed(() => controllersForFeature(MinerFeatureType.POWER_MONITORING));

async function fetchField(field: string, controllerId: string) {
  fieldFetching.value = { ...fieldFetching.value, [field]: true };
  fieldFetchSuccess.value = { ...fieldFetchSuccess.value, [field]: false };
  fetchError.value = null;
  try {
    const snapshot: MinerStateSnapshot = await minerControllerService.getMinerDetails(controllerId);
    let updated = false;
    if (field === "hash_rate_max" && snapshot.hash_rate && snapshot.hash_rate.value > 0) {
      formData.value.hash_rate_max = {
        value: snapshot.hash_rate.value,
        unit: snapshot.hash_rate.unit || "TH/s",
      };
      updated = true;
    } else if (field === "power_consumption_max" && snapshot.power_consumption && snapshot.power_consumption > 0) {
      formData.value.power_consumption_max = snapshot.power_consumption;
      updated = true;
    }
    if (updated) {
      highlightedFields.value = new Set([field]);
      fieldFetchSuccess.value = { ...fieldFetchSuccess.value, [field]: true };
      setTimeout(() => {
        fieldFetchSuccess.value = { ...fieldFetchSuccess.value, [field]: false };
        highlightedFields.value = new Set();
      }, 3000);
    }
  } catch (error: any) {
    fetchError.value =
      error?.response?.data?.detail || error?.message || "Failed to fetch from controller";
  } finally {
    fieldFetching.value = { ...fieldFetching.value, [field]: false };
  }
}

function handleSave() {
  if (isFormValid.value) {
    // Deep clone to remove Vue reactive proxies
    const rawData = JSON.parse(JSON.stringify(toRaw(formData.value)));
    // Remove controller-related fields from miner payload (backend no longer accepts them)
    delete rawData.features;
    delete rawData.controller_ids;
    // Clone features for emission
    const rawFeatures: MinerFeature[] = JSON.parse(JSON.stringify(toRaw(localFeatures.value)));
    emit("save", rawData, { ...controllerChanges.value }, rawFeatures);
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
            <div class="flex gap-2">
              <input
                v-model="formData.model"
                type="text"
                placeholder="e.g., Antminer S19 Pro"
                class="input input-bordered w-full flex-1 transition-colors duration-500"
                :class="{ 'input-success border-success': highlightedFields.has('model') }"
              />
              <!-- Fetch Model: single controller -->
              <button
                v-if="modelControllers.length === 1"
                type="button"
                class="btn btn-sm btn-square"
                :class="fieldFetchSuccess['model'] ? 'btn-success' : 'btn-ghost'"
                :disabled="fieldFetching['model']"
                @click="fetchField('model', modelControllers[0])"
                :title="`Fetch from ${getControllerName(modelControllers[0])}`"
              >
                <PhCheck v-if="fieldFetchSuccess['model']" :size="16" />
                <PhDownloadSimple v-else :size="16" :class="{ 'animate-bounce': fieldFetching['model'] }" />
              </button>
              <!-- Fetch Model: multiple controllers -->
              <div v-else-if="modelControllers.length > 1" class="dropdown dropdown-end">
                <label tabindex="0" class="btn btn-sm btn-square" :class="fieldFetchSuccess['model'] ? 'btn-success' : 'btn-ghost'">
                  <PhCheck v-if="fieldFetchSuccess['model']" :size="16" />
                  <PhDownloadSimple v-else :size="16" :class="{ 'animate-bounce': fieldFetching['model'] }" />
                </label>
                <ul tabindex="0" class="dropdown-content z-[1] menu p-1 shadow-lg bg-base-200 rounded-box w-52">
                  <li v-for="cid in modelControllers" :key="cid">
                    <a @click="fetchField('model', cid)">{{ getControllerName(cid) }} <span v-if="getControllerAdapterType(cid)" class="badge badge-xs" :class="getAdapterBadgeClass(cid)">{{ formatType(getControllerAdapterType(cid)!) }}</span></a>
                  </li>
                </ul>
              </div>
            </div>
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
              <span v-if="getControllerAdapterType(controllerId)" class="badge badge-xs" :class="getAdapterBadgeClass(controllerId)">{{ formatType(getControllerAdapterType(controllerId)!) }}</span>
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
                {{ controller.name }} ({{ formatType(controller.adapter_type) }})
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

        <!-- Controller Features Section -->
        <template v-if="localFeatures.length > 0 && selectedControllerIds.length > 0">
          <div class="divider text-xs text-base-content/50 my-4">
            <PhArrowsDownUp :size="14" />
            CONTROLLER FEATURES
          </div>

          <div class="space-y-2">
            <div
              v-for="[featureType, features] in featuresByType"
              :key="featureType"
              class="bg-base-200/30 rounded-lg px-3 py-2.5"
            >
              <!-- Feature Type Header -->
              <div class="flex items-center gap-2 mb-1.5">
                <component :is="getFeatureCategoryIcon(featureType)" :size="14" class="text-info flex-shrink-0" />
                <span class="text-sm font-medium text-base-content">{{ formatType(featureType) }}</span>
                <span
                  v-if="hasMultipleProviders(featureType)"
                  class="badge badge-xs badge-warning gap-1"
                  title="Multiple controllers provide this feature"
                >
                  <PhWarningCircle :size="10" />
                  {{ features.filter((f) => f.enabled).length }} providers
                </span>
              </div>

              <!-- Controllers providing this feature -->
              <div class="space-y-1">
                <div
                  v-for="feature in features"
                  :key="feature.controller_id"
                  class="flex items-center gap-2 py-1 pl-5"
                  :class="{ 'opacity-40': !feature.enabled }"
                >
                  <!-- Role indicator dot -->
                  <span
                    class="w-2 h-2 rounded-full flex-shrink-0"
                    :class="{
                      'bg-success': getFeatureRole(feature) === 'active',
                      'bg-warning': getFeatureRole(feature) === 'fallback',
                      'bg-base-content/20': getFeatureRole(feature) === 'disabled',
                    }"
                  />

                  <!-- Controller name -->
                  <span class="text-xs flex-1 truncate">
                    {{ getControllerName(feature.controller_id) }}
                  </span>

                  <!-- Adapter type badge -->
                  <span
                    v-if="getControllerAdapterType(feature.controller_id)"
                    class="badge badge-xs"
                    :class="getAdapterBadgeClass(feature.controller_id)"
                  >
                    {{ formatType(getControllerAdapterType(feature.controller_id)!) }}
                  </span>

                  <!-- Priority input -->
                  <div class="flex items-center gap-0.5 ml-1">
                    <span class="text-[10px] text-base-content/40 uppercase">Pri</span>
                    <button
                      type="button"
                      class="btn btn-ghost btn-xs btn-square min-h-0 h-5 w-5"
                      :disabled="!feature.enabled || feature.priority >= 100"
                      @click="updateFeaturePriority(feature.feature_type, feature.controller_id, feature.priority + 10)"
                      title="Priority +10"
                    >
                      <PhCaretUp :size="12" />
                    </button>
                    <input
                      type="number"
                      :value="feature.priority"
                      @change="updateFeaturePriority(feature.feature_type, feature.controller_id, parseInt(($event.target as HTMLInputElement).value) || 50)"
                      min="1"
                      max="100"
                      class="input input-xs input-bordered w-14 text-center"
                      :disabled="!feature.enabled"
                    />
                    <button
                      type="button"
                      class="btn btn-ghost btn-xs btn-square min-h-0 h-5 w-5"
                      :disabled="!feature.enabled || feature.priority <= 1"
                      @click="updateFeaturePriority(feature.feature_type, feature.controller_id, feature.priority - 10)"
                      title="Priority -10"
                    >
                      <PhCaretDown :size="12" />
                    </button>
                  </div>

                  <!-- Enable/disable toggle -->
                  <input
                    type="checkbox"
                    class="toggle toggle-xs toggle-primary"
                    :checked="feature.enabled"
                    @change="toggleFeatureEnabled(feature.feature_type, feature.controller_id)"
                  />

                  <!-- Role badge -->
                  <span
                    class="badge badge-xs w-16 justify-center"
                    :class="{
                      'badge-success': getFeatureRole(feature) === 'active',
                      'badge-warning': getFeatureRole(feature) === 'fallback',
                      'badge-ghost text-base-content/30': getFeatureRole(feature) === 'disabled',
                    }"
                  >
                    {{ getFeatureRole(feature) === 'active' ? 'Active' : getFeatureRole(feature) === 'fallback' ? 'Fallback' : 'Off' }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Note for newly added controllers -->
          <p v-if="controllerChanges.add.length > 0" class="text-xs text-base-content/40 mt-2 italic">
            Features for newly added controllers will appear after saving.
          </p>
        </template>

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
              <!-- Fetch Hash Rate: single controller -->
              <button
                v-if="hashRateControllers.length === 1"
                type="button"
                class="btn btn-sm btn-square"
                :class="fieldFetchSuccess['hash_rate_max'] ? 'btn-success' : 'btn-ghost'"
                :disabled="fieldFetching['hash_rate_max']"
                @click="fetchField('hash_rate_max', hashRateControllers[0])"
                :title="`Fetch from ${getControllerName(hashRateControllers[0])}`"
              >
                <PhCheck v-if="fieldFetchSuccess['hash_rate_max']" :size="16" />
                <PhDownloadSimple v-else :size="16" :class="{ 'animate-bounce': fieldFetching['hash_rate_max'] }" />
              </button>
              <!-- Fetch Hash Rate: multiple controllers -->
              <div v-else-if="hashRateControllers.length > 1" class="dropdown dropdown-end">
                <label tabindex="0" class="btn btn-sm btn-square" :class="fieldFetchSuccess['hash_rate_max'] ? 'btn-success' : 'btn-ghost'">
                  <PhCheck v-if="fieldFetchSuccess['hash_rate_max']" :size="16" />
                  <PhDownloadSimple v-else :size="16" :class="{ 'animate-bounce': fieldFetching['hash_rate_max'] }" />
                </label>
                <ul tabindex="0" class="dropdown-content z-[1] menu p-1 shadow-lg bg-base-200 rounded-box w-52">
                  <li v-for="cid in hashRateControllers" :key="cid">
                    <a @click="fetchField('hash_rate_max', cid)">{{ getControllerName(cid) }} <span v-if="getControllerAdapterType(cid)" class="badge badge-xs" :class="getAdapterBadgeClass(cid)">{{ formatType(getControllerAdapterType(cid)!) }}</span></a>
                  </li>
                </ul>
              </div>
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
            <div class="flex gap-2">
              <label class="input input-bordered flex items-center gap-2 flex-1 transition-colors duration-500"
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
              <!-- Fetch Power: single controller -->
              <button
                v-if="powerControllers.length === 1"
                type="button"
                class="btn btn-sm btn-square"
                :class="fieldFetchSuccess['power_consumption_max'] ? 'btn-success' : 'btn-ghost'"
                :disabled="fieldFetching['power_consumption_max']"
                @click="fetchField('power_consumption_max', powerControllers[0])"
                :title="`Fetch from ${getControllerName(powerControllers[0])}`"
              >
                <PhCheck v-if="fieldFetchSuccess['power_consumption_max']" :size="16" />
                <PhDownloadSimple v-else :size="16" :class="{ 'animate-bounce': fieldFetching['power_consumption_max'] }" />
              </button>
              <!-- Fetch Power: multiple controllers -->
              <div v-else-if="powerControllers.length > 1" class="dropdown dropdown-end">
                <label tabindex="0" class="btn btn-sm btn-square" :class="fieldFetchSuccess['power_consumption_max'] ? 'btn-success' : 'btn-ghost'">
                  <PhCheck v-if="fieldFetchSuccess['power_consumption_max']" :size="16" />
                  <PhDownloadSimple v-else :size="16" :class="{ 'animate-bounce': fieldFetching['power_consumption_max'] }" />
                </label>
                <ul tabindex="0" class="dropdown-content z-[1] menu p-1 shadow-lg bg-base-200 rounded-box w-52">
                  <li v-for="cid in powerControllers" :key="cid">
                    <a @click="fetchField('power_consumption_max', cid)">{{ getControllerName(cid) }} <span v-if="getControllerAdapterType(cid)" class="badge badge-xs" :class="getAdapterBadgeClass(cid)">{{ formatType(getControllerAdapterType(cid)!) }}</span></a>
                  </li>
                </ul>
              </div>
            </div>
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
