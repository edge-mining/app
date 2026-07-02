<script setup lang="ts">
import { computed, ref, watch, toRaw } from "vue";
import { MinerFeatureType, type Miner, type MinerInfo, type MinerLimit } from "../../core/models/miner";
import { useMinerControllerStore } from "../../core/stores/minerControllerStore";
import { MinerService } from "../../core/services/minerService";
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
const minerService = new MinerService();

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
const showFeatures = ref(false);

// Device info state (fetched from /miners/{id}/info)
const deviceInfo = ref<MinerInfo | null>(null);

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
        showFeatures.value = false;
        deviceInfo.value = null;
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
        showFeatures.value = false;
        deviceInfo.value = null;
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
const addingController = ref(false);

async function addController() {
  const controllerId = controllerToAdd.value;
  if (!controllerId || selectedControllerIds.value.includes(controllerId)) return;
  selectedControllerIds.value.push(controllerId);
  controllerToAdd.value = undefined;
  await ensureFeaturesForController(controllerId);
}

function removeController(controllerId: string) {
  selectedControllerIds.value = selectedControllerIds.value.filter((id) => id !== controllerId);
  // Drop the controller's features from both working and baseline copies. The
  // backend recreates them at default (enabled, priority 50) if it is re-linked.
  localFeatures.value = localFeatures.value.filter((f) => f.controller_id !== controllerId);
  originalFeatures.value = originalFeatures.value.filter((f) => f.controller_id !== controllerId);
}

// Generate placeholder features for a freshly-selected controller so they can be
// configured/ordered before the miner is saved. The backend auto-creates the
// same set (enabled, priority 50) when the controller is linked on save.
async function ensureFeaturesForController(controllerId: string) {
  // Already have features for this controller (e.g. loaded from an existing miner)
  if (localFeatures.value.some((f) => f.controller_id === controllerId)) return;
  addingController.value = true;
  fetchError.value = null;
  try {
    const featureTypes = await minerService.getControllerSupportedFeatures(controllerId);
    const synthetic: MinerFeature[] = featureTypes.map((ft) => ({
      feature_type: ft as MinerFeatureType,
      controller_id: controllerId,
      priority: 50,
      enabled: true,
    }));
    localFeatures.value.push(...synthetic);
    // Record the defaults as baseline so the "modified" badge and the save-time
    // diff only reflect changes the user actually makes.
    originalFeatures.value.push(...synthetic.map((f) => ({ ...f })));
  } catch (error: any) {
    fetchError.value =
      error?.response?.data?.detail || error?.message || "Failed to load controller features";
  } finally {
    addingController.value = false;
  }
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

// Swap priority between two controllers for a given feature type
// direction: 'up' = swap with higher-priority neighbor, 'down' = swap with lower-priority neighbor
function swapFeaturePriority(featureType: MinerFeatureType, controllerId: string, direction: 'up' | 'down') {
  const group = featuresByType.value.get(featureType);
  if (!group || group.length < 2) return;
  const currentIdx = group.findIndex((f) => f.controller_id === controllerId);
  if (currentIdx === -1) return;
  // group is sorted descending by priority: index 0 = highest
  const neighborIdx = direction === 'up' ? currentIdx - 1 : currentIdx + 1;
  if (neighborIdx < 0 || neighborIdx >= group.length) return;
  const currentPriority = group[currentIdx].priority;
  const neighborPriority = group[neighborIdx].priority;
  updateFeaturePriority(featureType, controllerId, neighborPriority);
  updateFeaturePriority(featureType, group[neighborIdx].controller_id, currentPriority);
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


// Check if miner has the DEVICE_INFO_DETECTION feature enabled
const hasDeviceInfoFeature = computed(() => {
  return localFeatures.value.some(
    (f) =>
      f.feature_type === MinerFeatureType.DEVICE_INFO_DETECTION &&
      f.enabled &&
      selectedControllerIds.value.includes(f.controller_id)
  );
});

async function ensureDeviceInfo(): Promise<MinerInfo | null> {
  if (deviceInfo.value) return deviceInfo.value;
  if (!formData.value.id) {
    fetchError.value = "Miner must be saved before fetching info";
    return null;
  }
  const info = await minerService.getMinerInfo(formData.value.id);
  if (info) deviceInfo.value = info;
  return info;
}

async function fetchInfoField(field: "name" | "model") {
  fieldFetching.value = { ...fieldFetching.value, [field]: true };
  fieldFetchSuccess.value = { ...fieldFetchSuccess.value, [field]: false };
  fetchError.value = null;
  try {
    const info = await ensureDeviceInfo();
    if (!info) return;
    let updated = false;
    if (field === "name" && info.hostname) {
      formData.value.name = info.hostname;
      updated = true;
    } else if (field === "model" && info.model) {
      formData.value.model = info.model;
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
      error?.response?.data?.detail || error?.message || "Failed to fetch miner info";
  } finally {
    fieldFetching.value = { ...fieldFetching.value, [field]: false };
  }
}

async function fetchLimit(field: "hash_rate_max" | "power_consumption_max") {
  if (!formData.value.id) {
    fetchError.value = "Miner must be saved before fetching limits";
    return;
  }
  fieldFetching.value = { ...fieldFetching.value, [field]: true };
  fieldFetchSuccess.value = { ...fieldFetchSuccess.value, [field]: false };
  fetchError.value = null;
  try {
    const limits: MinerLimit = await minerService.getMinerLimits(formData.value.id);
    let updated = false;
    if (field === "hash_rate_max" && limits.max_hash_rate && limits.max_hash_rate.value > 0) {
      formData.value.hash_rate_max = {
        value: limits.max_hash_rate.value,
        unit: limits.max_hash_rate.unit || "TH/s",
      };
      updated = true;
    } else if (field === "power_consumption_max" && limits.max_power && limits.max_power > 0) {
      formData.value.power_consumption_max = limits.max_power;
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
      error?.response?.data?.detail || error?.message || "Failed to fetch limits";
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
            <div class="flex gap-2">
              <input
                v-model="formData.name"
                type="text"
                placeholder="Enter miner name"
                class="input input-bordered w-full flex-1 transition-colors duration-500"
                :class="{ 'input-success border-success': highlightedFields.has('name') }"
                required
              />
              <!-- Fetch hostname from device info -->
              <button
                v-if="isEdit && formData.id && hasDeviceInfoFeature"
                type="button"
                class="btn btn-sm btn-square"
                :class="fieldFetchSuccess['name'] ? 'btn-success' : 'btn-ghost'"
                :disabled="fieldFetching['name']"
                @click="fetchInfoField('name')"
                title="Fetch hostname from miner"
              >
                <PhCheck v-if="fieldFetchSuccess['name']" :size="16" />
                <PhDownloadSimple v-else :size="16" :class="{ 'animate-bounce': fieldFetching['name'] }" />
              </button>
            </div>
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
              <!-- Fetch model from device info -->
              <button
                v-if="isEdit && formData.id && hasDeviceInfoFeature"
                type="button"
                class="btn btn-sm btn-square"
                :class="fieldFetchSuccess['model'] ? 'btn-success' : 'btn-ghost'"
                :disabled="fieldFetching['model']"
                @click="fetchInfoField('model')"
                title="Fetch model from miner"
              >
                <PhCheck v-if="fieldFetchSuccess['model']" :size="16" />
                <PhDownloadSimple v-else :size="16" :class="{ 'animate-bounce': fieldFetching['model'] }" />
              </button>
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
              :disabled="!controllerToAdd || addingController"
              @click="addController"
              title="Add Controller"
            >
              <PhPlus :size="18" :class="{ 'animate-spin': addingController }" />
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
          <!-- Manage Features toggle button -->
          <div class="flex items-center justify-center my-2">
            <button
              type="button"
              class="btn btn-xs btn-ghost gap-1.5 text-base-content/50 hover:text-base-content"
              @click="showFeatures = !showFeatures"
            >
              <PhArrowsDownUp :size="14" />
              {{ showFeatures ? 'Hide Features' : 'Manage Features' }}
              <span v-if="hasFeatureChanges" class="badge badge-xs badge-warning">modified</span>
            </button>
          </div>

          <div v-if="showFeatures" class="space-y-2">
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
                      :class="{ 'invisible': !(features.length > 1 && features[features.length - 1].controller_id === feature.controller_id) }"
                      :disabled="!feature.enabled"
                      @click="swapFeaturePriority(feature.feature_type, feature.controller_id, 'up')"
                      title="Increase priority"
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
                      :class="{ 'invisible': !(features.length > 1 && features[0].controller_id === feature.controller_id) }"
                      :disabled="!feature.enabled"
                      @click="swapFeaturePriority(feature.feature_type, feature.controller_id, 'down')"
                      title="Decrease priority"
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
              <!-- Fetch limits from miner -->
              <button
                v-if="isEdit && formData.id"
                type="button"
                class="btn btn-sm btn-square"
                :class="fieldFetchSuccess['hash_rate_max'] ? 'btn-success' : 'btn-ghost'"
                :disabled="fieldFetching['hash_rate_max']"
                @click="fetchLimit('hash_rate_max')"
                title="Fetch max hash rate from miner"
              >
                <PhCheck v-if="fieldFetchSuccess['hash_rate_max']" :size="16" />
                <PhDownloadSimple v-else :size="16" :class="{ 'animate-bounce': fieldFetching['hash_rate_max'] }" />
              </button>
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
              <!-- Fetch max power from miner -->
              <button
                v-if="isEdit && formData.id"
                type="button"
                class="btn btn-sm btn-square"
                :class="fieldFetchSuccess['power_consumption_max'] ? 'btn-success' : 'btn-ghost'"
                :disabled="fieldFetching['power_consumption_max']"
                @click="fetchLimit('power_consumption_max')"
                title="Fetch max power from miner"
              >
                <PhCheck v-if="fieldFetchSuccess['power_consumption_max']" :size="16" />
                <PhDownloadSimple v-else :size="16" :class="{ 'animate-bounce': fieldFetching['power_consumption_max'] }" />
              </button>
            </div>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex items-end gap-3 pt-4 border-t border-base-300/40">
          <!-- Device info (footer left) -->
          <div v-if="deviceInfo" class="flex-1 text-xs text-base-content/40 truncate">
            <div>
              <template v-if="deviceInfo.firmware_type">
                <span class="text-base-content/50">FW:</span> {{ deviceInfo.firmware_type }}<template v-if="deviceInfo.firmware_version"> {{ deviceInfo.firmware_version }}</template>
              </template>
              <template v-else-if="deviceInfo.firmware_version">
                <span class="text-base-content/50">FW:</span> {{ deviceInfo.firmware_version }}
              </template>
            </div>
            <div>
              <template v-if="deviceInfo.mac_address">
                <span class="text-base-content/50">MAC:</span> {{ deviceInfo.mac_address }}
              </template>
              <template v-if="deviceInfo.serial_number">
                <span v-if="deviceInfo.mac_address"> · </span><span class="text-base-content/50">S/N:</span> {{ deviceInfo.serial_number }}
              </template>
            </div>
          </div>
          <div v-else class="flex-1"></div>

          <!-- Buttons (footer right) -->
          <div class="flex gap-3">
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
