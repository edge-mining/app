<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useClimateZoneStore } from "../../core/stores/climateZoneStore";
import { useMinerStore } from "../../core/stores/minerStore";
import { useOptimizationUnitStore } from "../../core/stores/optimizationUnitStore";
import { usePolicyStore } from "../../core/stores/policyStore";
import { useDashboardPolling } from "../../core/composables/useDashboardPolling";
import { normalizeHashRate, formatPower, formatTimeAgo } from "../../core/utils/index";
import type { ClimateZoneReading } from "../../core/models/climateZone";
import type { TimeSeriesPoint } from "../../core/stores/dashboardStore";
import ClimateZoneDashCard from "../../components/climate/ClimateZoneDashCard.vue";
import KpiCard from "../../components/dashboard/KpiCard.vue";
import ChartPanel from "../../components/dashboard/ChartPanel.vue";
import RealtimeChart from "../../components/dashboard/RealtimeChart.vue";
import {
  PhThermometerSimple,
  PhCpu,
  PhLightning,
  PhSun,
  PhPower,
  PhTarget,
  PhShieldCheck,
  PhArrowsClockwise,
  PhBatteryCharging,
  PhFire,
} from "@phosphor-icons/vue";

const CHART_COLOR_TEMP = "rgba(248, 113, 113, 0.9)"; // red-400
const CHART_COLOR_TARGET = "rgba(52, 211, 153, 0.9)"; // emerald-400
const CHART_COLOR_SOLAR = "rgba(250, 204, 21, 0.9)"; // yellow-400
const CHART_COLOR_CONSUMPTION = "rgba(251, 146, 60, 0.9)"; // orange-400

const climateZoneStore = useClimateZoneStore();
const minerStore = useMinerStore();
const optimizationUnitStore = useOptimizationUnitStore();
const policyStore = usePolicyStore();

const {
  lastUpdated,
  isPolling,
  energyProductionSeries,
  consumptionSeries,
  minerOnOffEvents,
} = useDashboardPolling(5000);

// ---------- State ----------
const zoneReadings = ref<Map<string, ClimateZoneReading>>(new Map());
const temperatureSeries = ref<Map<string, TimeSeriesPoint[]>>(new Map());
const targetSeries = ref<Map<string, TimeSeriesPoint[]>>(new Map());
const loading = ref(true);

// ---------- Tick for time-ago ----------
const now = ref(Date.now());
let tickTimer: ReturnType<typeof setInterval> | undefined;
let pollTimer: ReturnType<typeof setInterval> | undefined;

onMounted(async () => {
  tickTimer = setInterval(() => { now.value = Date.now(); }, 1000);
  await loadInitialData();
  pollTimer = setInterval(pollClimateData, 5000);
});

onUnmounted(() => {
  if (tickTimer) clearInterval(tickTimer);
  if (pollTimer) clearInterval(pollTimer);
});

async function loadInitialData() {
  loading.value = true;
  try {
    await Promise.all([
      climateZoneStore.loadClimateZones(),
      minerStore.loadMiners(),
      optimizationUnitStore.loadOptimizationUnits(),
      policyStore.loadPolicies(),
    ]);
    await pollClimateData();
  } finally {
    loading.value = false;
  }
}

async function pollClimateData() {
  const zones = climateZoneStore.climateZones;
  const results = await Promise.allSettled(
    zones.filter((z) => z.id).map((z) => climateZoneStore.getReading(z.id!))
  );

  const timestamp = Math.floor(Date.now() / 1000);
  for (let i = 0; i < results.length; i++) {
    const zone = zones.filter((z) => z.id)[i];
    if (!zone?.id) continue;
    const result = results[i];
    if (result.status === "fulfilled" && result.value) {
      zoneReadings.value.set(zone.id, result.value);

      // Record temperature series
      const tempPts = temperatureSeries.value.get(zone.id) || [];
      tempPts.push({ time: timestamp, value: result.value.temperature_celsius });
      if (tempPts.length > 360) tempPts.shift();
      temperatureSeries.value.set(zone.id, tempPts);

      // Record target series
      if (result.value.target_temperature != null) {
        const tgtPts = targetSeries.value.get(zone.id) || [];
        tgtPts.push({ time: timestamp, value: result.value.target_temperature });
        if (tgtPts.length > 360) tgtPts.shift();
        targetSeries.value.set(zone.id, tgtPts);
      }
    }
  }
}

// ---------- Computed: Climate KPIs ----------
const zones = computed(() => climateZoneStore.climateZones);

const avgTemperature = computed(() => {
  const readings = [...zoneReadings.value.values()];
  if (readings.length === 0) return null;
  const sum = readings.reduce((acc, r) => acc + r.temperature_celsius, 0);
  return sum / readings.length;
});

const zonesAtTarget = computed(() => {
  let count = 0;
  for (const zone of zones.value) {
    if (!zone.id) continue;
    const reading = zoneReadings.value.get(zone.id);
    if (!reading) continue;
    const target = reading.target_temperature ?? zone.default_target_temperature;
    if (target != null && reading.temperature_celsius >= target - (zone.hysteresis_celsius || 0.5)) {
      count++;
    }
  }
  return count;
});

// ---------- Computed: Miner Status ----------
const runningMiners = computed(() =>
  minerStore.miners.filter((m) => {
    const state = m.id ? minerStore.minerStates.get(m.id) : undefined;
    return state?.status === "on";
  })
);

const totalMiningPower = computed(() =>
  runningMiners.value.reduce((sum, m) => {
    const state = m.id ? minerStore.minerStates.get(m.id) : undefined;
    return sum + (state?.power_consumption || 0);
  }, 0)
);

const totalHashRate = computed(() => {
  let total = 0;
  for (const m of runningMiners.value) {
    const state = m.id ? minerStore.minerStates.get(m.id) : undefined;
    if (state?.hash_rate?.value) {
      total += normalizeHashRate(state.hash_rate.value, state.hash_rate.unit || "TH/s");
    }
  }
  return total;
});

// ---------- Computed: Energy / Solar ----------
const latestProduction = computed(() => {
  const pts = energyProductionSeries.value;
  return pts.length > 0 ? pts[pts.length - 1].value : 0;
});

const latestConsumption = computed(() => {
  const pts = consumptionSeries.value;
  return pts.length > 0 ? pts[pts.length - 1].value : 0;
});

const solarSurplus = computed(() => Math.max(0, latestProduction.value - latestConsumption.value));

const surplusPercent = computed(() => {
  if (latestProduction.value <= 0) return 0;
  return Math.min(100, (solarSurplus.value / latestProduction.value) * 100);
});

// ---------- Computed: Policy ----------
const activePolicies = computed(() => policyStore.policies);

// ---------- Computed: Last updated ----------
const lastUpdateLabel = computed(() => {
  void now.value;
  return formatTimeAgo(lastUpdated.value);
});

// ---------- Helper: selected zone for chart ----------
const selectedZoneId = ref<string | null>(null);

const selectedZone = computed(() => {
  const id = selectedZoneId.value || zones.value[0]?.id;
  return id || null;
});

const selectedZoneTempSeries = computed(() => {
  if (!selectedZone.value) return [];
  return temperatureSeries.value.get(selectedZone.value) || [];
});

const selectedZoneTargetSeries = computed(() => {
  if (!selectedZone.value) return [];
  return targetSeries.value.get(selectedZone.value) || [];
});

const selectedZoneName = computed(() => {
  const id = selectedZone.value;
  if (!id) return "";
  return zones.value.find((z) => z.id === id)?.name || "";
});
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="h-10 w-10 rounded-xl bg-rose-500/15 flex items-center justify-center">
          <PhFire :size="22" class="text-rose-400" weight="duotone" />
        </div>
        <div>
          <h1 class="text-xl font-bold text-base-content">Climate & Heating</h1>
          <p class="text-xs text-base-content/50">Zone monitoring • Miner heating • Solar surplus</p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <span v-if="isPolling" class="relative flex h-2.5 w-2.5">
          <span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-50"></span>
          <span class="relative inline-flex h-2.5 w-2.5 rounded-full bg-primary"></span>
        </span>
        <span class="text-xs text-base-content/40">
          <PhArrowsClockwise :size="12" class="inline mr-1" />
          {{ lastUpdateLabel }}
        </span>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <span class="loading loading-spinner loading-lg text-primary"></span>
    </div>

    <template v-else>
      <!-- KPI Row -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <KpiCard
          label="Avg Temperature"
          :value="avgTemperature !== null ? `${avgTemperature.toFixed(1)}°C` : '--'"
          :icon="PhThermometerSimple"
          icon-color="text-rose-400"
          icon-bg-color="bg-rose-500/15"
        />
        <KpiCard
          label="Zones at Target"
          :value="`${zonesAtTarget}/${zones.length}`"
          :icon="PhTarget"
          icon-color="text-emerald-400"
          icon-bg-color="bg-emerald-500/15"
        />
        <KpiCard
          label="Solar Surplus"
          :value="formatPower(solarSurplus)"
          :sub-value="surplusPercent > 0 ? `${surplusPercent.toFixed(0)}% available` : 'no surplus'"
          :icon="PhSun"
          icon-color="text-yellow-400"
          icon-bg-color="bg-yellow-500/15"
        />
        <KpiCard
          label="Mining Power"
          :value="formatPower(totalMiningPower)"
          :sub-value="`${runningMiners.length} miner${runningMiners.length !== 1 ? 's' : ''} • ${totalHashRate.toFixed(1)} TH/s`"
          :icon="PhCpu"
          icon-color="text-indigo-400"
          icon-bg-color="bg-indigo-500/15"
        />
      </div>

      <!-- Zone Cards Grid -->
      <div>
        <h2 class="text-sm font-semibold text-base-content/70 uppercase tracking-wider mb-3 flex items-center gap-2">
          <PhThermometerSimple :size="16" />
          Climate Zones
        </h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          <ClimateZoneDashCard
            v-for="zone in zones"
            :key="zone.id"
            :zone="zone"
            :reading="zone.id ? zoneReadings.get(zone.id) : undefined"
            class="cursor-pointer"
            :class="{ 'ring-2 ring-primary/40': selectedZone === zone.id }"
            @click="selectedZoneId = zone.id ?? null"
          />
        </div>
        <div v-if="zones.length === 0" class="text-center py-8 text-base-content/40">
          <PhThermometerSimple :size="32" class="mx-auto mb-2 opacity-50" />
          <p class="text-sm">No climate zones configured</p>
        </div>
      </div>

      <!-- Charts Row -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <!-- Temperature History Chart -->
        <ChartPanel
          :title="`Temperature — ${selectedZoneName || 'Select a zone'}`"
          :icon="PhThermometerSimple"
          icon-color="text-rose-400"
          :has-data="selectedZoneTempSeries.length > 0"
          :chart-height="200"
          :show-marker-toggle="true"
        >
          <template #default>
            <RealtimeChart
              :data="selectedZoneTempSeries"
              series-name="Temperature"
              :line-color="CHART_COLOR_TEMP"
              :height="200"
              :range="30 * 60 * 1000"
              :format-value="(v: number) => `${v.toFixed(1)}°C`"
              :miner-events="minerOnOffEvents"
              :secondary-data="selectedZoneTargetSeries"
              secondary-series-name="Target"
              :secondary-line-color="CHART_COLOR_TARGET"
              :secondary-format-value="(v: number) => `${v.toFixed(1)}°C`"
            />
          </template>
        </ChartPanel>

        <!-- Solar Production vs Consumption -->
        <ChartPanel
          title="Solar Production vs Consumption"
          :icon="PhSun"
          icon-color="text-yellow-400"
          :has-data="energyProductionSeries.length > 0"
          :chart-height="200"
          :show-marker-toggle="true"
        >
          <template #default>
            <RealtimeChart
              :data="energyProductionSeries"
              series-name="Production"
              :line-color="CHART_COLOR_SOLAR"
              :height="200"
              :range="30 * 60 * 1000"
              :format-value="(v: number) => formatPower(v)"
              :miner-events="minerOnOffEvents"
              :secondary-data="consumptionSeries"
              secondary-series-name="Consumption"
              :secondary-line-color="CHART_COLOR_CONSUMPTION"
              :secondary-format-value="(v: number) => formatPower(v)"
            />
          </template>
        </ChartPanel>
      </div>

      <!-- Bottom Row: Miner Status + Policy Status -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <!-- Miner Status -->
        <div class="rounded-xl border border-base-300/20 bg-base-100/30 backdrop-blur-sm p-4">
          <div class="flex items-center gap-2 mb-3">
            <PhCpu :size="16" class="text-indigo-400" />
            <span class="text-sm font-medium text-base-content/70">Miner Status</span>
          </div>
          <div v-if="minerStore.miners.length === 0" class="text-center py-4 text-base-content/40 text-sm">
            No miners configured
          </div>
          <div v-else class="space-y-2">
            <div
              v-for="miner in minerStore.miners"
              :key="miner.id"
              class="flex items-center justify-between rounded-lg px-3 py-2 bg-base-200/30"
            >
              <div class="flex items-center gap-2">
                <span
                  class="w-2 h-2 rounded-full"
                  :class="{
                    'bg-success': miner.id && minerStore.minerStates.get(miner.id)?.status === 'on',
                    'bg-error': miner.id && minerStore.minerStates.get(miner.id)?.status === 'off',
                    'bg-base-content/20': !miner.id || !minerStore.minerStates.get(miner.id),
                  }"
                />
                <span class="text-sm font-medium text-base-content/80">{{ miner.name }}</span>
              </div>
              <div class="flex items-center gap-3 text-xs text-base-content/50">
                <template v-if="miner.id && minerStore.minerStates.get(miner.id)?.status === 'on'">
                  <span>{{ formatPower(minerStore.minerStates.get(miner.id)?.power_consumption || 0) }}</span>
                  <span v-if="minerStore.minerStates.get(miner.id)?.hash_rate?.value">
                    {{ minerStore.minerStates.get(miner.id)!.hash_rate!.value.toFixed(1) }}
                    {{ minerStore.minerStates.get(miner.id)!.hash_rate!.unit || 'TH/s' }}
                  </span>
                </template>
                <span v-else class="uppercase text-[10px] tracking-wider">
                  {{ miner.id && minerStore.minerStates.get(miner.id)?.status || 'unknown' }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Active Policies -->
        <div class="rounded-xl border border-base-300/20 bg-base-100/30 backdrop-blur-sm p-4">
          <div class="flex items-center gap-2 mb-3">
            <PhShieldCheck :size="16" class="text-emerald-400" />
            <span class="text-sm font-medium text-base-content/70">Active Policies</span>
          </div>
          <div v-if="activePolicies.length === 0" class="text-center py-4 text-base-content/40 text-sm">
            No active policies
          </div>
          <div v-else class="space-y-2">
            <div
              v-for="policy in activePolicies"
              :key="policy.id"
              class="rounded-lg px-3 py-2 bg-base-200/30"
            >
              <div class="flex items-center justify-between mb-1">
                <span class="text-sm font-medium text-base-content/80">{{ policy.name }}</span>
                <span class="badge badge-xs badge-success">active</span>
              </div>
              <div class="flex items-center gap-3 text-xs text-base-content/50">
                <span class="flex items-center gap-1">
                  <PhLightning :size="10" />
                  {{ policy.start_rules?.length || 0 }} start
                </span>
                <span class="flex items-center gap-1">
                  <PhPower :size="10" />
                  {{ policy.stop_rules?.length || 0 }} stop
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Solar Surplus Indicator -->
      <div class="rounded-xl border border-base-300/20 bg-base-100/30 backdrop-blur-sm p-4">
        <div class="flex items-center gap-2 mb-3">
          <PhBatteryCharging :size="16" class="text-yellow-400" />
          <span class="text-sm font-medium text-base-content/70">Energy Balance</span>
        </div>
        <div class="grid grid-cols-3 gap-4 text-center">
          <div>
            <div class="text-xs text-base-content/40 mb-1">Production</div>
            <div class="text-lg font-bold text-yellow-400 tabular-nums">{{ formatPower(latestProduction) }}</div>
          </div>
          <div>
            <div class="text-xs text-base-content/40 mb-1">Consumption</div>
            <div class="text-lg font-bold text-orange-400 tabular-nums">{{ formatPower(latestConsumption) }}</div>
          </div>
          <div>
            <div class="text-xs text-base-content/40 mb-1">Surplus</div>
            <div
              class="text-lg font-bold tabular-nums"
              :class="solarSurplus > 0 ? 'text-success' : 'text-base-content/30'"
            >
              {{ formatPower(solarSurplus) }}
            </div>
          </div>
        </div>
        <!-- Surplus Bar -->
        <div class="mt-3">
          <div class="w-full h-2 bg-base-300/30 rounded-full overflow-hidden">
            <div
              class="h-full rounded-full transition-all duration-500 bg-gradient-to-r from-yellow-400 to-emerald-400"
              :style="{ width: `${surplusPercent}%` }"
            />
          </div>
          <div class="flex justify-between mt-1 text-[10px] text-base-content/30">
            <span>0%</span>
            <span>Surplus {{ surplusPercent.toFixed(0) }}%</span>
            <span>100%</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
