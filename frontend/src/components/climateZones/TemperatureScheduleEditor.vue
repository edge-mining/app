<script setup lang="ts">
import { ref, watch } from "vue";
import type { TemperatureSlot } from "../../core/models/climateZone";
import { PhPlus, PhTrash, PhClock } from "@phosphor-icons/vue";

const props = defineProps<{
  modelValue: TemperatureSlot[];
}>();

const emit = defineEmits<{
  "update:modelValue": [slots: TemperatureSlot[]];
}>();

const slots = ref<TemperatureSlot[]>([]);

watch(
  () => props.modelValue,
  (val) => {
    slots.value = val ? [...val] : [];
  },
  { immediate: true, deep: true }
);

function addSlot() {
  slots.value.push({
    start_time: "08:00",
    end_time: "22:00",
    target_temperature: 21,
  });
  emitUpdate();
}

function removeSlot(index: number) {
  slots.value.splice(index, 1);
  emitUpdate();
}

function emitUpdate() {
  emit("update:modelValue", [...slots.value]);
}
</script>

<template>
  <div class="space-y-3">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2 text-sm font-semibold text-base-content/70 uppercase tracking-wider">
        <PhClock :size="16" />
        Temperature Schedule
      </div>
      <button
        type="button"
        class="btn btn-ghost btn-xs gap-1"
        @click="addSlot"
      >
        <PhPlus :size="14" />
        Add Slot
      </button>
    </div>

    <div v-if="slots.length === 0" class="text-sm text-base-content/40 italic py-2">
      No schedule defined — default target temperature will be used.
    </div>

    <div v-for="(slot, index) in slots" :key="index" class="flex items-center gap-2 p-3 bg-base-200/40 rounded-lg">
      <!-- Start time -->
      <div class="form-control flex-1">
        <label class="label py-0 mb-1">
          <span class="label-text text-xs">From</span>
        </label>
        <input
          v-model="slot.start_time"
          type="time"
          class="input input-bordered input-sm w-full"
          @change="emitUpdate"
        />
      </div>

      <!-- End time -->
      <div class="form-control flex-1">
        <label class="label py-0 mb-1">
          <span class="label-text text-xs">To</span>
        </label>
        <input
          v-model="slot.end_time"
          type="time"
          class="input input-bordered input-sm w-full"
          @change="emitUpdate"
        />
      </div>

      <!-- Target temperature -->
      <div class="form-control flex-1">
        <label class="label py-0 mb-1">
          <span class="label-text text-xs">Target °C</span>
        </label>
        <input
          v-model.number="slot.target_temperature"
          type="number"
          step="0.5"
          min="5"
          max="35"
          class="input input-bordered input-sm w-full"
          @change="emitUpdate"
        />
      </div>

      <!-- Remove button -->
      <button
        type="button"
        class="btn btn-ghost btn-sm btn-square mt-5"
        title="Remove slot"
        @click="removeSlot(index)"
      >
        <PhTrash :size="16" class="text-error" />
      </button>
    </div>

    <p class="text-xs text-base-content/40">
      Slots with start &gt; end cross midnight (e.g. 22:00 → 06:00).
    </p>
  </div>
</template>
