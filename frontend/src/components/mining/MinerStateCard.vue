<script setup lang="ts">
import { computed } from "vue";
import {
  PhCpu,
  PhLightning,
  PhThermometer,
  PhFan,
  PhCube,
  PhClock,
} from "@phosphor-icons/vue";
import type { Miner, MinerStateSnapshot } from "../../core/models/miner";
import { formatHashRate, formatPower } from "../../core/utils/index";

const props = defineProps<{
  miner: Miner;
  state?: MinerStateSnapshot;
}>();

const isOn = computed(() => props.state?.status === "on");

function formatTemp(value?: number, unit?: string): string {
  if (value == null) return "-";
  return `${value.toFixed(1)} ${unit || "°C"}`;
}

function formatFan(value?: number, unit?: string): string {
  if (value == null) return "-";
  return `${Math.round(value)} ${unit || "RPM"}`;
}

function formatUptime(seconds?: number): string {
  if (seconds == null) return "-";
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (d > 0) return `${d}d ${h}h`;
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}
</script>

<template>
  <div class="rounded-xl border border-base-300/20 bg-base-100/30 backdrop-blur-sm overflow-hidden">
    <div class="flex items-center justify-between px-4 py-3 border-b border-base-300/10">
      <div class="flex items-center gap-2 min-w-0">
        <span
          class="w-2 h-2 rounded-full shrink-0"
          :class="isOn ? 'bg-emerald-400' : 'bg-base-content/30'"
        />
        <span class="text-sm font-medium text-base-content/80 truncate">{{ miner.name }}</span>
        <span v-if="miner.model" class="text-[10px] text-base-content/40 truncate">
          {{ miner.model }}
        </span>
      </div>
      <span class="text-[10px] uppercase tracking-wider text-base-content/40">
        {{ state?.status ?? "unknown" }}
      </span>
    </div>

    <div v-if="!state" class="p-4 text-center text-sm text-base-content/30">
      No runtime state.
    </div>

    <div v-else class="p-3 grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
      <div class="rounded-lg bg-base-content/5 px-2 py-1.5">
        <div class="text-[10px] uppercase tracking-wider text-base-content/40 flex items-center gap-1">
          <PhCpu :size="11" /> Hash Rate
        </div>
        <div class="font-mono text-emerald-400 mt-0.5">
          {{ formatHashRate(state.hash_rate?.value, state.hash_rate?.unit) }}
        </div>
      </div>
      <div class="rounded-lg bg-base-content/5 px-2 py-1.5">
        <div class="text-[10px] uppercase tracking-wider text-base-content/40 flex items-center gap-1">
          <PhLightning :size="11" /> Power
        </div>
        <div class="font-mono text-amber-400 mt-0.5">
          {{ formatPower(state.power_consumption) }}
        </div>
      </div>
      <div class="rounded-lg bg-base-content/5 px-2 py-1.5">
        <div class="text-[10px] uppercase tracking-wider text-base-content/40 flex items-center gap-1">
          <PhClock :size="11" /> Uptime
        </div>
        <div class="font-mono text-base-content/80 mt-0.5">
          {{ formatUptime(state.system_uptime) }}
        </div>
      </div>
      <div class="rounded-lg bg-base-content/5 px-2 py-1.5">
        <div class="text-[10px] uppercase tracking-wider text-base-content/40 flex items-center gap-1">
          <PhThermometer :size="11" /> Max Chip
        </div>
        <div class="font-mono text-red-400 mt-0.5">
          {{ formatTemp(state.max_chip_temperature?.value, state.max_chip_temperature?.unit) }}
        </div>
      </div>
      <div class="rounded-lg bg-base-content/5 px-2 py-1.5">
        <div class="text-[10px] uppercase tracking-wider text-base-content/40 flex items-center gap-1">
          <PhThermometer :size="11" /> Max Board
        </div>
        <div class="font-mono text-orange-400 mt-0.5">
          {{ formatTemp(state.max_board_temperature?.value, state.max_board_temperature?.unit) }}
        </div>
      </div>
      <div class="rounded-lg bg-base-content/5 px-2 py-1.5">
        <div class="text-[10px] uppercase tracking-wider text-base-content/40 flex items-center gap-1">
          <PhFan :size="11" /> Fan
        </div>
        <div class="font-mono text-sky-400 mt-0.5">
          <template v-if="state.internal_fan_speed?.length">
            {{ formatFan(Math.max(...state.internal_fan_speed.map((f) => f.value || 0))) }}
          </template>
          <template v-else>-</template>
        </div>
      </div>
      <div
        v-if="state.blocks_found != null"
        class="rounded-lg bg-base-content/5 px-2 py-1.5"
      >
        <div class="text-[10px] uppercase tracking-wider text-base-content/40 flex items-center gap-1">
          <PhCube :size="11" /> Blocks
        </div>
        <div class="font-mono text-primary mt-0.5">
          {{ state.blocks_found }}
        </div>
      </div>
      <div
        v-if="state.hashboards?.length"
        class="rounded-lg bg-base-content/5 px-2 py-1.5 col-span-2 sm:col-span-3"
      >
        <div class="text-[10px] uppercase tracking-wider text-base-content/40 mb-1">
          Hashboards ({{ state.hashboards.length }})
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
          <div
            v-for="hb in state.hashboards"
            :key="hb.index"
            class="rounded bg-base-100/40 border border-base-300/10 px-2 py-1 flex flex-col gap-0.5"
          >
            <span class="text-[10px] text-base-content/40">#{{ hb.index }}</span>
            <span class="text-[11px] font-mono text-emerald-400">
              {{ formatHashRate(hb.hash_rate?.value, hb.hash_rate?.unit) }}
            </span>
            <span class="text-[10px] text-base-content/50">
              chip {{ formatTemp(hb.chip_temperature?.value, hb.chip_temperature?.unit) }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped></style>
