<script setup lang="ts">
import { computed, ref, watch, toRaw } from "vue";
import type { Miner } from "../../core/models/miner";
import { useMinerControllerStore } from "../../core/stores/minerControllerStore";
import {
  PhX,
  PhFloppyDisk,
  PhCpu,
  PhLightning,
  PhGear,
} from "@phosphor-icons/vue";

const props = defineProps<{
  open: boolean;
  miner?: Miner;
  allMiners?: Miner[];
  isEdit?: boolean;
}>();

const emit = defineEmits<{
  close: [];
  save: [miner: Miner];
}>();

const minerControllerStore = useMinerControllerStore();

// Hash rate unit options
const hashRateUnits = ["H/s", "KH/s", "MH/s", "GH/s", "TH/s", "PH/s", "EH/s"];

// Local form state
const formData = ref<Miner>({
  name: "",
  status: "unknown",
  active: false,
  hash_rate_max: { value: 100, unit: "TH/s" },
  power_consumption_max: 3000,
});

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
      } else {
        formData.value = {
          name: "",
          status: "unknown",
          active: false,
          hash_rate_max: { value: 100, unit: "TH/s" },
          power_consumption_max: 3000,
        };
      }
    }
  },
  { immediate: true }
);

// Compute the controller IDs already assigned to other miners
const assignedControllerIds = computed(() => {
  if (!props.allMiners) return new Set<string>();
  return new Set(
    props.allMiners
      .filter((m) => m.id !== formData.value.id && m.controller_id)
      .map((m) => String(m.controller_id))
  );
});

// Filter available controllers
const availableControllers = computed(() => {
  return minerControllerStore.minerControllers.filter(
    (controller) =>
      !assignedControllerIds.value.has(controller.id!) ||
      controller.id === formData.value.controller_id
  );
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

function handleSave() {
  if (isFormValid.value) {
    // Deep clone to remove Vue reactive proxies
    const rawData = JSON.parse(JSON.stringify(toRaw(formData.value)));
    emit("save", rawData);
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
              class="input input-bordered w-full"
            />
          </div>
        </div>

        <!-- Controller -->
        <div class="divider text-xs text-base-content/50 my-4">
          CONTROLLER
        </div>

        <div class="form-control">
          <label class="label mb-1">
            <span class="label-text flex items-center gap-2">
              <PhGear :size="16" class="text-info" />
              Miner Controller
            </span>
          </label>
          <select
            v-model="formData.controller_id"
            class="select select-bordered w-full"
          >
            <option :value="undefined">None</option>
            <option
              v-for="controller in availableControllers"
              :key="controller.id"
              :value="controller.id"
            >
              {{ controller.name }}
            </option>
          </select>
          <label class="label mt-1">
            <span class="label-text-alt text-base-content/50">
              Controllers manage remote start/stop operations
            </span>
          </label>
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
                class="input input-bordered flex-1"
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
            <label class="input input-bordered flex items-center gap-2">
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

<style scoped></style>
