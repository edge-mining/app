<script setup lang="ts">
import { computed } from "vue";
import type { ClimateZone, ClimateZoneReading } from "../../core/models/climateZone";
import {
  PhThermometerHot,
  PhThermometerCold,
  PhTarget,
  PhDropHalf,
} from "@phosphor-icons/vue";

const props = defineProps<{
  zone: ClimateZone;
  reading?: ClimateZoneReading | null;
}>();

const temperature = computed(() => props.reading?.temperature_celsius ?? null);
const target = computed(() => props.reading?.target_temperature ?? props.zone.default_target_temperature ?? null);
const humidity = computed(() => props.reading?.humidity ?? null);
const hysteresis = computed(() => props.reading?.hysteresis_celsius ?? props.zone.hysteresis_celsius ?? 0.5);

const tempStatus = computed<"heating" | "comfort" | "cold" | "unknown">(() => {
  if (temperature.value === null || target.value === null) return "unknown";
  if (temperature.value >= target.value) return "comfort";
  if (temperature.value >= target.value - hysteresis.value) return "heating";
  return "cold";
});

const statusColor = computed(() => {
  switch (tempStatus.value) {
    case "comfort": return "text-success";
    case "heating": return "text-warning";
    case "cold": return "text-info";
    default: return "text-base-content/40";
  }
});

const statusBgColor = computed(() => {
  switch (tempStatus.value) {
    case "comfort": return "bg-success/10 border-success/20";
    case "heating": return "bg-warning/10 border-warning/20";
    case "cold": return "bg-info/10 border-info/20";
    default: return "bg-base-200/30 border-base-300/20";
  }
});

const statusLabel = computed(() => {
  switch (tempStatus.value) {
    case "comfort": return "At Target";
    case "heating": return "Heating";
    case "cold": return "Below Target";
    default: return "No Data";
  }
});

const progressPercent = computed(() => {
  if (temperature.value === null || target.value === null) return 0;
  // Show progress from 0°C to target as percentage (clamped 0-100)
  const minTemp = Math.max(0, target.value - 10);
  const range = target.value - minTemp;
  if (range <= 0) return 100;
  return Math.min(100, Math.max(0, ((temperature.value - minTemp) / range) * 100));
});

function formatTemp(value: number | null): string {
  if (value === null) return "--";
  return value.toFixed(1);
}
</script>

<template>
  <div
    class="rounded-xl border p-4 transition-all duration-300 hover:shadow-md"
    :class="statusBgColor"
  >
    <!-- Header -->
    <div class="flex items-center justify-between mb-3">
      <h3 class="font-semibold text-sm text-base-content capitalize">{{ zone.name }}</h3>
      <span
        class="badge badge-sm"
        :class="{
          'badge-success': tempStatus === 'comfort',
          'badge-warning': tempStatus === 'heating',
          'badge-info': tempStatus === 'cold',
          'badge-ghost': tempStatus === 'unknown',
        }"
      >
        {{ statusLabel }}
      </span>
    </div>

    <!-- Temperature Display -->
    <div class="flex items-end gap-1 mb-3">
      <span class="text-3xl font-bold tabular-nums" :class="statusColor">
        {{ formatTemp(temperature) }}
      </span>
      <span class="text-lg text-base-content/50 mb-0.5">°C</span>
    </div>

    <!-- Progress Bar to Target -->
    <div v-if="target !== null" class="mb-3">
      <div class="flex items-center justify-between text-xs text-base-content/50 mb-1">
        <div class="flex items-center gap-1">
          <PhTarget :size="12" />
          <span>Target: {{ formatTemp(target) }}°C</span>
        </div>
        <span v-if="hysteresis">±{{ hysteresis }}°C</span>
      </div>
      <div class="w-full h-1.5 bg-base-300/30 rounded-full overflow-hidden">
        <div
          class="h-full rounded-full transition-all duration-500"
          :class="{
            'bg-success': tempStatus === 'comfort',
            'bg-warning': tempStatus === 'heating',
            'bg-info': tempStatus === 'cold',
          }"
          :style="{ width: `${progressPercent}%` }"
        />
      </div>
    </div>

    <!-- Stats Row -->
    <div class="flex items-center gap-4 text-xs text-base-content/50">
      <div v-if="humidity !== null" class="flex items-center gap-1">
        <PhDropHalf :size="12" />
        <span>{{ humidity.toFixed(0) }}%</span>
      </div>
      <div v-if="zone.area_sqm" class="flex items-center gap-1">
        <span>{{ zone.area_sqm }} m²</span>
      </div>
      <div v-if="temperature !== null && target !== null" class="flex items-center gap-1 ml-auto">
        <component :is="temperature < target ? PhThermometerCold : PhThermometerHot" :size="12" />
        <span>{{ temperature < target ? '-' : '+' }}{{ Math.abs(temperature - target).toFixed(1) }}°C</span>
      </div>
    </div>
  </div>
</template>
