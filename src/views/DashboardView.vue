<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from "vue";
import { useMinerStore } from "../core/stores/minerStore";
import { useOptimizationUnitStore } from "../core/stores/optimizationUnitStore";
import { useDashboardPolling } from "../core/composables/useDashboardPolling";
import { normalizeHashRate, formatPower, formatTimeAgo } from "../core/utils/index";

const CHART_COLOR_PRIMARY = 'rgba(190, 255, 163, 0.9)';  // #beffa3
const CHART_COLOR_WARNING = 'rgba(244, 184, 96, 0.9)';   // #f4b860
import KpiCard from "../components/dashboard/KpiCard.vue";
import MinerTile from "../components/dashboard/MinerTile.vue";
import ChartPanel from "../components/dashboard/ChartPanel.vue";
import RealtimeChart from "../components/dashboard/RealtimeChart.vue";
import ActivityFeed from "../components/dashboard/ActivityFeed.vue";
import {
  PhCpu,
  PhLightning,
  PhPower,
  PhGraph,
  PhSun,
  PhBatteryCharging,
  PhThermometer,
  PhChartLine,
  PhClockCounterClockwise,
  PhShieldCheck,
  PhArrowsClockwise,
} from "@phosphor-icons/vue";

const minerStore = useMinerStore();
const optimizationUnitStore = useOptimizationUnitStore();
const { lastUpdated, isPolling, events, hashRateSeries, powerSeries, minerOnOffEvents } = useDashboardPolling(5000);

// ---------- KPI computations ----------

const totalMiners = computed(() => minerStore.miners.length);

const runningMiners = computed(
  () => minerStore.miners.filter((m) => m.status === "on").length
);

const activeMiners = computed(
  () => minerStore.miners.filter((m) => m.active).length
);

const totalHashRate = computed(() => {
  let total = 0;
  for (const m of minerStore.miners) {
    if (m.status === "on" && m.hash_rate?.value) {
      total += normalizeHashRate(m.hash_rate.value, m.hash_rate.unit || "TH/s");
    }
  }
  return total;
});

const formattedHashRate = computed(() => {
  const val = totalHashRate.value;
  if (val === 0) return "-";
  if (val >= 1000) return `${(val / 1000).toFixed(1)} PH/s`;
  return `${val.toFixed(1)} TH/s`;
});

const totalPowerConsumption = computed(() => {
  return minerStore.miners
    .filter((m) => m.status === "on")
    .reduce((sum, m) => sum + (m.power_consumption || 0), 0);
});

const enabledUnits = computed(
  () => optimizationUnitStore.optimizationUnits.filter((u) => u.is_enabled).length
);

const totalUnits = computed(
  () => optimizationUnitStore.optimizationUnits.length
);

const now = ref(Date.now());
let tickTimer: ReturnType<typeof setInterval> | undefined;
onMounted(() => { tickTimer = setInterval(() => { now.value = Date.now(); }, 1000); });
onUnmounted(() => { if (tickTimer) clearInterval(tickTimer); });

const lastUpdateLabel = computed(() => {
  void now.value; // reactive tick
  return formatTimeAgo(lastUpdated.value);
});

function formatHashRateValue(v: number): string {
  if (v <= 0) return "0 TH/s";
  if (v >= 1000) return `${(v / 1000).toFixed(2)} PH/s`;
  if (v >= 1) return `${v.toFixed(2)} TH/s`;
  if (v >= 0.001) return `${(v * 1000).toFixed(2)} GH/s`;
  return `${(v * 1000000).toFixed(2)} MH/s`;
}

function formatPowerValue(v: number): string {
  if (v <= 0) return "0 W";
  if (v >= 1000000) return `${(v / 1000000).toFixed(2)} MW`;
  if (v >= 1000) return `${(v / 1000).toFixed(2)} kW`;
  return `${v.toFixed(0)} W`;
}
</script>

<template>
  <div class="dashboard-root space-y-5">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-base-content">Dashboard</h1>
        <p class="text-sm text-base-content/50 mt-0.5">
          Real-time mining &amp; energy overview
        </p>
      </div>
      <div class="flex items-center gap-2 text-xs text-base-content/40">
        <PhArrowsClockwise
          :size="14"
          :class="{ 'animate-spin': isPolling }"
        />
        <span>Updated {{ lastUpdateLabel }}</span>
      </div>
    </div>

    <!-- KPI Strip -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
      <KpiCard
        label="Total Hash Rate"
        :value="formattedHashRate"
        :icon="PhCpu"
        icon-color="text-primary"
        icon-bg-color="bg-primary/15"
        :value-color="totalHashRate > 0 ? 'text-primary' : 'text-base-content/30'"
      />
      <KpiCard
        label="Power Draw"
        :value="totalPowerConsumption > 0 ? formatPower(totalPowerConsumption) : '-'"
        :icon="PhLightning"
        icon-color="text-warning"
        icon-bg-color="bg-warning/15"
        :value-color="totalPowerConsumption > 0 ? 'text-warning' : 'text-base-content/30'"
      />
      <KpiCard
        label="Miners"
        :value="`${runningMiners} / ${activeMiners}`"
        :sub-value="`of ${totalMiners} total`"
        :icon="PhPower"
        icon-color="text-sky-400"
        icon-bg-color="bg-sky-400/15"
        value-color="text-sky-400"
      />
      <KpiCard
        label="Optimization Units"
        :value="`${enabledUnits} / ${totalUnits}`"
        sub-value="units enabled"
        :icon="PhGraph"
        icon-color="text-teal-400"
        icon-bg-color="bg-teal-400/15"
        value-color="text-teal-400"
      />
    </div>

    <!-- Main Content: 2/3 + 1/3 layout -->
    <div class="grid grid-cols-1 xl:grid-cols-3 gap-5">
      <!-- Left Column: Miners + Charts -->
      <div class="xl:col-span-2 space-y-5">
        <!-- Miner Fleet -->
        <div>
          <div class="flex items-center gap-2 mb-3">
            <PhCpu :size="16" class="text-base-content/40" />
            <h2 class="text-sm font-semibold text-base-content/60 uppercase tracking-wider">
              Miner Fleet
            </h2>
            <span class="text-xs text-base-content/30 ml-auto">
              {{ runningMiners }} running
            </span>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            <MinerTile
              v-for="miner in minerStore.miners"
              :key="miner.id"
              :miner="miner"
            />
            <div
              v-if="minerStore.miners.length === 0"
              class="col-span-full flex flex-col items-center py-12 text-center"
            >
              <PhCpu :size="36" class="text-base-content/15 mb-2" />
              <span class="text-sm text-base-content/30">No miners configured</span>
              <RouterLink to="/settings/miners" class="text-xs text-primary/60 hover:text-primary mt-1">
                Add miners in Settings
              </RouterLink>
            </div>
          </div>
        </div>

        <!-- Mining Charts -->
        <div>
          <div class="flex items-center gap-2 mb-3">
            <PhCpu :size="16" class="text-base-content/40" />
            <h2 class="text-sm font-semibold text-base-content/60 uppercase tracking-wider">
              Mining
            </h2>
          </div>
          <div class="grid grid-cols-1 lg:grid-cols-3 gap-3">
            <ChartPanel
              title="Hash Rate"
              :icon="PhCpu"
              icon-color="text-primary"
              :chart-height="160"
              :has-data="hashRateSeries.length > 1"
              v-slot="{ expanded, expandedHeight, showMinerEvents }"
            >
              <RealtimeChart
                v-if="hashRateSeries.length > 1"
                :data="hashRateSeries"
                :height="expanded ? expandedHeight : 136"
                class="w-full h-full"
                series-name="Hash Rate"
                :line-color="CHART_COLOR_PRIMARY"
                :format-value="formatHashRateValue"
                :miner-events="minerOnOffEvents"
                :show-miner-events="showMinerEvents"
              />
            </ChartPanel>
            <ChartPanel
              title="Power Consumption"
              :icon="PhLightning"
              icon-color="text-warning"
              :chart-height="160"
              :has-data="powerSeries.length > 1"
              v-slot="{ expanded, expandedHeight, showMinerEvents }"
            >
              <RealtimeChart
                v-if="powerSeries.length > 1"
                :data="powerSeries"
                :height="expanded ? expandedHeight : 136"
                class="w-full h-full"
                series-name="Power"
                :line-color="CHART_COLOR_WARNING"
                :format-value="formatPowerValue"
                :miner-events="minerOnOffEvents"
                :show-miner-events="showMinerEvents"
              />
            </ChartPanel>
            <ChartPanel
              title="Temperature"
              :icon="PhThermometer"
              icon-color="text-red-400"
              :chart-height="160"
            />
          </div>
        </div>

        <!-- Energy Charts -->
        <div>
          <div class="flex items-center gap-2 mb-3">
            <PhSun :size="16" class="text-base-content/40" />
            <h2 class="text-sm font-semibold text-base-content/60 uppercase tracking-wider">
              Energy
            </h2>
          </div>
          <div class="grid grid-cols-1 lg:grid-cols-3 gap-3">
            <ChartPanel
              title="Energy Production"
              :icon="PhSun"
              icon-color="text-yellow-400"
              :chart-height="160"
            />
            <ChartPanel
              title="Energy Forecast"
              :icon="PhChartLine"
              icon-color="text-sky-400"
              :chart-height="160"
            />
            <ChartPanel
              title="Battery Level"
              :icon="PhBatteryCharging"
              icon-color="text-teal-400"
              :chart-height="160"
            />
          </div>
        </div>
      </div>

      <!-- Right Column: Activity + Policy -->
      <div class="space-y-5">
        <!-- Activity Feed -->
        <div>
          <div class="flex items-center gap-2 mb-3">
            <PhClockCounterClockwise :size="16" class="text-base-content/40" />
            <h2 class="text-sm font-semibold text-base-content/60 uppercase tracking-wider">
              Activity
            </h2>
          </div>
          <div class="rounded-xl border border-base-300/20 bg-base-100/30 backdrop-blur-sm p-3 max-h-[420px] overflow-y-auto">
            <ActivityFeed :events="events" />
          </div>
        </div>

        <!-- Last Policy Action (placeholder) -->
        <div>
          <div class="flex items-center gap-2 mb-3">
            <PhShieldCheck :size="16" class="text-base-content/40" />
            <h2 class="text-sm font-semibold text-base-content/60 uppercase tracking-wider">
              Last Policy Rule
            </h2>
          </div>
          <div class="rounded-xl border border-base-300/20 bg-base-100/30 backdrop-blur-sm p-4">
            <div class="flex flex-col items-center justify-center py-6 text-center">
              <div class="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-3">
                <PhShieldCheck :size="24" class="text-primary/30" />
              </div>
              <span class="text-sm text-base-content/30">No rule engaged yet</span>
              <span class="text-[11px] text-base-content/20 mt-1">
                Rules trigger based on energy conditions
              </span>
            </div>
          </div>
        </div>

        <!-- Miner On/Off Events -->
        <ChartPanel
          title="Miner On/Off Events"
          :icon="PhPower"
          icon-color="text-sky-400"
          :chart-height="140"
          :has-data="minerOnOffEvents.length > 0"
          :maximizable="false"
        >
          <div v-if="minerOnOffEvents.length > 0" class="space-y-1.5 max-h-[120px] overflow-y-auto">
            <div
              v-for="(evt, i) in [...minerOnOffEvents].reverse().slice(0, 20)"
              :key="i"
              class="flex items-center gap-2 text-xs px-1 py-1 rounded hover:bg-base-content/5"
            >
              <span
                class="w-2 h-2 rounded-full shrink-0"
                :class="evt.action === 'on' ? 'bg-emerald-400' : 'bg-red-400'"
              />
              <span class="text-base-content/50 tabular-nums shrink-0">
                {{ new Date(evt.time * 1000).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) }}
              </span>
              <span class="text-base-content/70 truncate">{{ evt.minerName }}</span>
              <span
                class="ml-auto text-[10px] font-semibold uppercase tracking-wider shrink-0"
                :class="evt.action === 'on' ? 'text-emerald-400' : 'text-red-400'"
              >
                {{ evt.action }}
              </span>
            </div>
          </div>
        </ChartPanel>
      </div>
    </div>
  </div>
</template>

<style scoped></style>
