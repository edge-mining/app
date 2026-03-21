<script setup lang="ts">
import type { Miner } from "../../core/models/miner";
import { computed } from "vue";
import {
  PhPower,
  PhCircleNotch,
  PhWarningCircle,
  PhQuestion,
  PhCpu,
  PhLightning,
} from "@phosphor-icons/vue";
import { formatHashRate, formatPower, normalizeHashRate } from "../../core/utils/index";

const props = defineProps<{
  miner: Miner;
}>();

const isOn = computed(() => props.miner.status === "on");
const isTransitioning = computed(
  () => props.miner.status === "starting" || props.miner.status === "stopping"
);

const statusConfig = computed(() => {
  const configs: Record<string, { color: string; bg: string; border: string; label: string; icon: typeof PhPower }> = {
    on: { color: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/30", label: "Running", icon: PhPower },
    off: { color: "text-base-content/40", bg: "bg-base-100/30", border: "border-base-300/20", label: "Off", icon: PhPower },
    starting: { color: "text-amber-400", bg: "bg-amber-500/10", border: "border-amber-500/30", label: "Starting", icon: PhCircleNotch },
    stopping: { color: "text-orange-400", bg: "bg-orange-500/10", border: "border-orange-500/30", label: "Stopping", icon: PhCircleNotch },
    error: { color: "text-red-400", bg: "bg-red-500/10", border: "border-red-500/30", label: "Error", icon: PhWarningCircle },
    unknown: { color: "text-base-content/30", bg: "bg-base-100/20", border: "border-base-300/20", label: "Unknown", icon: PhQuestion },
  };
  return configs[props.miner.status] || configs.unknown;
});

// Hash rate % of max (normalized to common unit)
const hashRatePct = computed(() => {
  if (!props.miner.hash_rate?.value || !props.miner.hash_rate_max?.value) return 0;
  const current = normalizeHashRate(props.miner.hash_rate.value, props.miner.hash_rate.unit);
  const max = normalizeHashRate(props.miner.hash_rate_max.value, props.miner.hash_rate_max.unit);
  if (max === 0) return 0;
  return Math.min((current / max) * 100, 100);
});

// Power consumption % of max
const powerPct = computed(() => {
  if (!props.miner.power_consumption || !props.miner.power_consumption_max) return 0;
  return Math.min((props.miner.power_consumption / props.miner.power_consumption_max) * 100, 100);
});
</script>

<template>
  <div
    class="miner-tile relative rounded-xl border p-3 transition-all duration-300"
    :class="[
      statusConfig.bg,
      statusConfig.border,
      { 'opacity-40': !miner.active },
    ]"
  >
    <!-- Top: status dot + name -->
    <div class="flex items-center gap-2 mb-3">
      <!-- Status indicator -->
      <div class="relative flex-shrink-0">
        <div
          class="w-2.5 h-2.5 rounded-full"
          :class="statusConfig.color.replace('text-', 'bg-')"
        ></div>
        <div
          v-if="isOn"
          class="absolute inset-0 w-2.5 h-2.5 rounded-full animate-ping opacity-40"
          :class="statusConfig.color.replace('text-', 'bg-')"
        ></div>
      </div>
      <div class="min-w-0 flex-1">
        <div class="text-sm font-semibold text-base-content truncate">{{ miner.name }}</div>
        <div class="text-[10px] text-base-content/40">{{ miner.model || statusConfig.label }}</div>
      </div>
      <component
        :is="statusConfig.icon"
        :size="16"
        :class="[statusConfig.color, { 'animate-spin': isTransitioning }]"
      />
    </div>

    <!-- Metrics -->
    <div class="space-y-2">
      <!-- Hash Rate -->
      <div>
        <div class="flex items-center justify-between text-[11px] mb-1">
          <span class="text-base-content/50 flex items-center gap-1">
            <PhCpu :size="11" /> Hash
          </span>
          <span class="font-mono" :class="isOn ? 'text-emerald-400' : 'text-base-content/30'">
            {{ formatHashRate(miner.hash_rate?.value, miner.hash_rate?.unit) }}
          </span>
        </div>
        <div class="h-1 rounded-full bg-base-300/30 overflow-hidden">
          <div
            class="h-full rounded-full transition-all duration-700"
            :class="isOn ? 'bg-emerald-500' : 'bg-base-content/10'"
            :style="{ width: `${hashRatePct}%` }"
          ></div>
        </div>
      </div>

      <!-- Power -->
      <div>
        <div class="flex items-center justify-between text-[11px] mb-1">
          <span class="text-base-content/50 flex items-center gap-1">
            <PhLightning :size="11" /> Power
          </span>
          <span class="font-mono" :class="isOn ? 'text-amber-400' : 'text-base-content/30'">
            {{ formatPower(miner.power_consumption) }}
          </span>
        </div>
        <div class="h-1 rounded-full bg-base-300/30 overflow-hidden">
          <div
            class="h-full rounded-full transition-all duration-700"
            :class="powerPct > 90 ? 'bg-red-500' : powerPct > 70 ? 'bg-amber-500' : 'bg-sky-500'"
            :style="{ width: `${powerPct}%` }"
          ></div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.miner-tile {
  backdrop-filter: blur(8px);
}
</style>
