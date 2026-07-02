<script setup lang="ts">
import { computed } from "vue";
import { PhChartLine, PhCloudSun } from "@phosphor-icons/vue";
import type { DecisionalContext } from "../../core/models/policy";
import type { ForecastPowerPoint } from "../../core/models/forecast";

interface Props {
  latestDecisionalContexts: Map<string, DecisionalContext>;
  forecastPowerPoints: ForecastPowerPoint[];
}

const props = defineProps<Props>();

// Forecast summary: today, remaining today, tomorrow
const forecastSummary = computed(() => {
  const ctxs = props.latestDecisionalContexts;
  let todayEnergy = 0;
  let remainingToday = 0;
  let tomorrowEnergy = 0;
  let hasData = false;

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);
  const dayAfter = new Date(tomorrow);
  dayAfter.setDate(dayAfter.getDate() + 1);

  for (const ctx of ctxs.values()) {
    if (!ctx.forecast?.intervals) continue;
    hasData = true;
    for (const interval of ctx.forecast.intervals) {
      const start = new Date(interval.start).getTime();
      if (start >= today.getTime() && start < tomorrow.getTime()) {
        todayEnergy += interval.energy ?? 0;
        remainingToday += interval.energy_remaining ?? 0;
      } else if (start >= tomorrow.getTime() && start < dayAfter.getTime()) {
        tomorrowEnergy += interval.energy ?? 0;
      }
    }
  }

  return hasData ? { todayEnergy, remainingToday, tomorrowEnergy } : null;
});

// Forecast power summary: average and max power for today and tomorrow
const forecastPowerSummary = computed(() => {
  const points = props.forecastPowerPoints;
  if (points.length === 0) return null;

  let todayPowerSum = 0;
  let todayPowerCount = 0;
  let tomorrowPowerSum = 0;
  let tomorrowPowerCount = 0;
  let maxPower = 0;

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);
  const dayAfter = new Date(tomorrow);
  dayAfter.setDate(dayAfter.getDate() + 1);

  for (const point of points) {
    const pointTime = new Date(point.timestamp).getTime();
    maxPower = Math.max(maxPower, point.power);

    if (pointTime >= today.getTime() && pointTime < tomorrow.getTime()) {
      todayPowerSum += point.power;
      todayPowerCount++;
    } else if (pointTime >= tomorrow.getTime() && pointTime < dayAfter.getTime()) {
      tomorrowPowerSum += point.power;
      tomorrowPowerCount++;
    }
  }

  return {
    avgPowerToday: todayPowerCount > 0 ? todayPowerSum / todayPowerCount : 0,
    avgPowerTomorrow: tomorrowPowerCount > 0 ? tomorrowPowerSum / tomorrowPowerCount : 0,
    maxPower,
  };
});

function parseEnergy(wh: number): { value: string; unit: string } {
  if (wh <= 0) return { value: '0', unit: 'Wh' };
  if (wh >= 1000000) return { value: (wh / 1000000).toFixed(1), unit: 'MWh' };
  if (wh >= 1000) return { value: (wh / 1000).toFixed(1), unit: 'kWh' };
  return { value: wh.toFixed(0), unit: 'Wh' };
}

function formatPowerValue(v: number): string {
  if (v <= 0) return "0 W";
  if (v >= 1000000) return `${parseFloat((v / 1000000).toFixed(2))} MW`;
  if (v >= 1000) return `${parseFloat((v / 1000).toFixed(2))} kW`;
  return `${Math.round(v)} W`;
}
</script>

<template>
  <div class="rounded-xl border border-base-300/20 bg-base-100/30 backdrop-blur-sm p-4">
    <div class="flex items-center gap-2 mb-4">
      <div class="w-7 h-7 rounded-lg bg-indigo-400/15 flex items-center justify-center">
        <PhChartLine :size="14" class="text-indigo-400" />
      </div>
      <span class="text-sm font-medium text-base-content/70">Forecast Summary</span>
    </div>
    <div v-if="forecastSummary" class="space-y-4">
      <!-- Energy Section -->
      <div>
        <div class="text-xs font-semibold text-base-content/50 uppercase tracking-wider mb-2 px-1">Energy</div>
        <div class="grid grid-cols-3 gap-2">
          <div class="flex flex-col items-center gap-1 rounded-lg bg-base-content/5 p-3">
            <div class="flex items-baseline gap-1">
              <span class="text-2xl font-bold text-indigo-400 leading-tight">{{ parseEnergy(forecastSummary.todayEnergy).value }}</span>
              <span class="text-[10px] text-base-content/40 font-medium">{{ parseEnergy(forecastSummary.todayEnergy).unit }}</span>
            </div>
            <span class="text-[10px] text-base-content/40 uppercase tracking-wider mt-1">Today</span>
          </div>
          <div class="flex flex-col items-center gap-1 rounded-lg bg-base-content/5 p-3">
            <div class="flex items-baseline gap-1">
              <span class="text-2xl font-bold text-indigo-300 leading-tight">{{ parseEnergy(forecastSummary.remainingToday).value }}</span>
              <span class="text-[10px] text-base-content/40 font-medium">{{ parseEnergy(forecastSummary.remainingToday).unit }}</span>
            </div>
            <span class="text-[10px] text-base-content/40 uppercase tracking-wider mt-1">Remaining</span>
          </div>
          <div class="flex flex-col items-center gap-1 rounded-lg bg-base-content/5 p-3">
            <div class="flex items-baseline gap-1">
              <span class="text-2xl font-bold text-indigo-400/70 leading-tight">{{ parseEnergy(forecastSummary.tomorrowEnergy).value }}</span>
              <span class="text-[10px] text-base-content/40 font-medium">{{ parseEnergy(forecastSummary.tomorrowEnergy).unit }}</span>
            </div>
            <span class="text-[10px] text-base-content/40 uppercase tracking-wider mt-1">Tomorrow</span>
          </div>
        </div>
      </div>
      <!-- Power Section -->
      <div v-if="forecastPowerSummary" class="pt-2 border-t border-base-content/10">
        <div class="text-xs font-semibold text-base-content/50 uppercase tracking-wider mb-2 px-1">Power</div>
        <div class="grid grid-cols-3 gap-2">
          <div class="flex flex-col items-center gap-1 rounded-lg bg-base-content/5 p-3">
            <div class="flex items-baseline gap-1">
              <span class="text-2xl font-bold text-cyan-400 leading-tight">{{ formatPowerValue(forecastPowerSummary.avgPowerToday).split(' ')[0] }}</span>
              <span class="text-[10px] text-base-content/40 font-medium">{{ formatPowerValue(forecastPowerSummary.avgPowerToday).split(' ')[1] }}</span>
            </div>
            <span class="text-[10px] text-base-content/40 uppercase tracking-wider mt-1">Avg Today</span>
          </div>
          <div class="flex flex-col items-center gap-1 rounded-lg bg-base-content/5 p-3">
            <div class="flex items-baseline gap-1">
              <span class="text-2xl font-bold text-cyan-300 leading-tight">{{ formatPowerValue(forecastPowerSummary.avgPowerTomorrow).split(' ')[0] }}</span>
              <span class="text-[10px] text-base-content/40 font-medium">{{ formatPowerValue(forecastPowerSummary.avgPowerTomorrow).split(' ')[1] }}</span>
            </div>
            <span class="text-[10px] text-base-content/40 uppercase tracking-wider mt-1">Avg Tomorrow</span>
          </div>
          <div class="flex flex-col items-center gap-1 rounded-lg bg-base-content/5 p-3">
            <div class="flex items-baseline gap-1">
              <span class="text-2xl font-bold text-cyan-400/70 leading-tight">{{ formatPowerValue(forecastPowerSummary.maxPower).split(' ')[0] }}</span>
              <span class="text-[10px] text-base-content/40 font-medium">{{ formatPowerValue(forecastPowerSummary.maxPower).split(' ')[1] }}</span>
            </div>
            <span class="text-[10px] text-base-content/40 uppercase tracking-wider mt-1">Peak</span>
          </div>
        </div>
      </div>
    </div>
    <div v-else class="flex flex-col items-center justify-center py-6 text-center">
      <PhCloudSun :size="28" class="text-base-content/15 mb-2" />
      <span class="text-sm text-base-content/30">No forecast data</span>
    </div>
  </div>
</template>

<style scoped></style>
