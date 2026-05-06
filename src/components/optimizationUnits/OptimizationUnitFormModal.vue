<script setup lang="ts">
import { computed, ref, watch } from "vue";
import type { OptimizationUnit, OptimizationUnitCreate } from "../../core/models/optimizationUnit";
import { usePolicyStore } from "../../core/stores/policyStore";
import { useMinerStore } from "../../core/stores/minerStore";
import { useEnergySourceStore } from "../../core/stores/energySourceStore";
import { useNotifierStore } from "../../core/stores/notifierStore";
import { useHomeLoadsProfileStore } from "../../core/stores/homeLoadsProfileStore";
import {
  PhX,
  PhFloppyDisk,
  PhGraph,
  PhCpu,
  PhLightning,
  PhChartLine,
  PhBell,
  PhShieldCheck,
} from "@phosphor-icons/vue";

const props = defineProps<{
  open: boolean;
  unit?: OptimizationUnit;
  isEdit?: boolean;
}>();

const emit = defineEmits<{
  close: [];
  save: [data: OptimizationUnitCreate];
}>();

const policyStore = usePolicyStore();
const minerStore = useMinerStore();
const energySourceStore = useEnergySourceStore();
//const forecastProviderStore = useForecastProviderStore();
const notifierStore = useNotifierStore();
const homeLoadsProfileStore = useHomeLoadsProfileStore();

// Local form state
const formData = ref({
  name: "",
  description: "",
  policy_id: undefined as string | undefined,
  energy_source_id: undefined as string | undefined,
  home_loads_profile_id: undefined as string | undefined,
});

const selectedMinerIds = ref<string[]>([]);
const selectedNotifierIds = ref<string[]>([]);

// Watch for modal open to reset/populate form
watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      if (props.unit) {
        formData.value = {
          name: props.unit.name,
          description: props.unit.description || "",
          policy_id: props.unit.policy_id,
          energy_source_id: props.unit.energy_source_id,
          home_loads_profile_id: props.unit.home_loads_profile_id,
        };
        selectedMinerIds.value = [...props.unit.target_miner_ids];
        selectedNotifierIds.value = [...props.unit.notifier_ids];
      } else {
        formData.value = {
          name: "",
          description: "",
          policy_id: undefined,
          energy_source_id: undefined,
          home_loads_profile_id: undefined,
        };
        selectedMinerIds.value = [];
        selectedNotifierIds.value = [];
      }
    }
  },
  { immediate: true }
);

const isFormValid = computed(() => {
  return formData.value.name.trim().length > 0;
});

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

function handleClose() {
  emit("close");
}

function handleSave() {
  if (!isFormValid.value) return;
  emit("save", {
    name: formData.value.name,
    description: formData.value.description || undefined,
    policy_id: formData.value.policy_id,
    energy_source_id: formData.value.energy_source_id,
    home_loads_profile_id: formData.value.home_loads_profile_id,
    target_miner_ids: selectedMinerIds.value,
    notifier_ids: selectedNotifierIds.value,
  });
}
</script>

<template>
  <dialog class="modal" :class="{ 'modal-open': open }">
    <div class="modal-box max-w-2xl bg-base-100 border border-base-300/60">
      <!-- Header -->
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-3">
          <div class="h-10 w-10 rounded-xl bg-teal-500/20 flex items-center justify-center">
            <PhGraph :size="22" class="text-teal-400" />
          </div>
          <h3 class="text-xl font-bold">
            {{ isEdit ? "Edit Optimization Unit" : "Add Optimization Unit" }}
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
        <div class="grid grid-cols-1 gap-4">
          <!-- Name -->
          <div class="form-control">
            <label class="label mb-1">
              <span class="label-text font-medium">Name *</span>
            </label>
            <input
              v-model="formData.name"
              type="text"
              placeholder="Enter optimization unit name"
              class="input input-bordered w-full"
              required
            />
          </div>

          <!-- Description -->
          <div class="form-control">
            <label class="label mb-1">
              <span class="label-text font-medium">Description</span>
            </label>
            <textarea
              v-model="formData.description"
              placeholder="Brief description of this optimization unit"
              class="textarea textarea-bordered w-full"
              rows="2"
            ></textarea>
          </div>
        </div>

        <!-- Resource Assignments -->
        <div class="divider text-xs text-base-content/50 my-4">
          RESOURCE ASSIGNMENTS
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <!-- Policy -->
          <div class="form-control">
            <label class="label mb-1">
              <span class="label-text flex items-center gap-2">
                <PhShieldCheck :size="16" class="text-primary" />
                Policy
              </span>
            </label>
            <select v-model="formData.policy_id" class="select select-bordered w-full">
              <option :value="undefined">None</option>
              <option
                v-for="policy in policyStore.policies"
                :key="policy.id"
                :value="policy.id?.toString()"
              >
                {{ policy.name }}
              </option>
            </select>
          </div>

          <!-- Energy Source -->
          <div class="form-control">
            <label class="label mb-1">
              <span class="label-text flex items-center gap-2">
                <PhLightning :size="16" class="text-amber-400" />
                Energy Source
              </span>
            </label>
            <select v-model="formData.energy_source_id" class="select select-bordered w-full">
              <option :value="undefined">None</option>
              <option
                v-for="source in energySourceStore.energySources"
                :key="source.id"
                :value="source.id?.toString()"
              >
                {{ source.name }}
              </option>
            </select>
          </div>

          <!-- Home Loads Profile -->
          <div class="form-control">
            <label class="label mb-1">
              <span class="label-text flex items-center gap-2">
                <PhChartLine :size="16" class="text-info" />
                Home Loads Profile
              </span>
            </label>
            <select v-model="formData.home_loads_profile_id" class="select select-bordered w-full">
              <option :value="undefined">None</option>
              <option
                v-for="profile in homeLoadsProfileStore.profiles"
                :key="profile.id"
                :value="profile.id?.toString()"
              >
                {{ profile.name }}
              </option>
            </select>
          </div>
        </div>

        <!-- Target Miners -->
        <div class="divider text-xs text-base-content/50 my-4">
          TARGET MINERS
        </div>

        <div class="form-control">
          <label class="label mb-1">
            <span class="label-text flex items-center gap-2">
              <PhCpu :size="16" class="text-emerald-400" />
              Select Miners
              <span class="badge badge-sm badge-ghost">{{ selectedMinerIds.length }} selected</span>
            </span>
          </label>
          <div class="border border-base-300/50 rounded-lg p-3 max-h-48 overflow-y-auto bg-base-200/30">
            <div v-if="minerStore.miners.length === 0" class="text-base-content/40 text-center py-3 text-sm">
              No miners available
            </div>
            <label
              v-for="miner in minerStore.miners"
              :key="miner.id"
              class="flex items-center gap-3 py-1.5 px-2 rounded-lg cursor-pointer hover:bg-base-300/30 transition-colors"
            >
              <input
                type="checkbox"
                class="checkbox checkbox-sm checkbox-primary"
                :checked="selectedMinerIds.includes(String(miner.id))"
                @change="toggleMinerSelection(String(miner.id))"
              />
              <div class="flex items-center gap-2 min-w-0">
                <PhCpu :size="14" class="text-base-content/40 flex-shrink-0" />
                <span class="text-sm truncate">{{ miner.name }}</span>
              </div>
            </label>
          </div>
        </div>

        <!-- Notifiers -->
        <div class="divider text-xs text-base-content/50 my-4">
          NOTIFIERS
        </div>

        <div class="form-control">
          <label class="label mb-1">
            <span class="label-text flex items-center gap-2">
              <PhBell :size="16" class="text-purple-400" />
              Select Notifiers
              <span class="badge badge-sm badge-ghost">{{ selectedNotifierIds.length }} selected</span>
            </span>
          </label>
          <div class="border border-base-300/50 rounded-lg p-3 max-h-48 overflow-y-auto bg-base-200/30">
            <div v-if="notifierStore.notifiers.length === 0" class="text-base-content/40 text-center py-3 text-sm">
              No notifiers available
            </div>
            <label
              v-for="notifier in notifierStore.notifiers"
              :key="notifier.id"
              class="flex items-center gap-3 py-1.5 px-2 rounded-lg cursor-pointer hover:bg-base-300/30 transition-colors"
            >
              <input
                type="checkbox"
                class="checkbox checkbox-sm checkbox-primary"
                :checked="selectedNotifierIds.includes(String(notifier.id))"
                @change="toggleNotifierSelection(String(notifier.id))"
              />
              <div class="flex items-center gap-2 min-w-0">
                <PhBell :size="14" class="text-base-content/40 flex-shrink-0" />
                <span class="text-sm truncate">{{ notifier.name }}</span>
              </div>
            </label>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex justify-end gap-3 pt-4 border-t border-base-300/40">
          <button type="button" class="btn btn-ghost" @click="handleClose">Cancel</button>
          <button type="submit" class="btn btn-primary" :disabled="!isFormValid">
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
