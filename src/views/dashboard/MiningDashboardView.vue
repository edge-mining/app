<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from "vue";
import { useMinerStore } from "../../core/stores/minerStore";
import { useOptimizationUnitStore } from "../../core/stores/optimizationUnitStore";
import { useDashboardPolling } from "../../core/composables/useDashboardPolling";
import { normalizeHashRate, formatPower, formatTimeAgo } from "../../core/utils/index";
import KpiCard from "../../components/dashboard/KpiCard.vue";
import PoolStatsCard from "../../components/mining/PoolStatsCard.vue";
import PayoutCard from "../../components/mining/PayoutCard.vue";
import MinerStateCard from "../../components/mining/MinerStateCard.vue";
import {
  PhCpu,
  PhLightning,
  PhPower,
  PhArrowsClockwise,
  PhCurrencyBtc,
  PhUsersFour,
  PhClockCountdown,
  PhTrendUp,
} from "@phosphor-icons/vue";
import type { MiningPerformanceSnapshot } from "../../core/models/policy";

const minerStore = useMinerStore();
const optimizationUnitStore = useOptimizationUnitStore();
const { lastUpdated, isPolling, latestDecisionalContexts } = useDashboardPolling(5000);

// ---------- Tick for "time ago" reactivity ----------
const now = ref(Date.now());
let tickTimer: ReturnType<typeof setInterval> | undefined;
onMounted(() => { tickTimer = setInterval(() => { now.value = Date.now(); }, 1000); });
onUnmounted(() => { if (tickTimer) clearInterval(tickTimer); });

const lastUpdateLabel = computed(() => {
  void now.value;
  return formatTimeAgo(lastUpdated.value);
});

// ---------- Miner KPIs (from miner store) ----------
const totalMiners = computed(() => minerStore.miners.length);
const runningMiners = computed(
  () => minerStore.miners.filter((m) => {
    const state = m.id ? minerStore.minerStates.get(m.id) : undefined;
    return state?.status === "on";
  }).length
);
const activeMiners = computed(
  () => minerStore.miners.filter((m) => m.active).length
);

const totalDeviceHashRate = computed(() => {
  let total = 0;
  for (const m of minerStore.miners) {
    const state = m.id ? minerStore.minerStates.get(m.id) : undefined;
    if (state?.status === "on" && state.hash_rate?.value) {
      total += normalizeHashRate(state.hash_rate.value, state.hash_rate.unit || "TH/s");
    }
  }
  return total;
});

const totalDevicePower = computed(() => {
  return minerStore.miners
    .filter((m) => {
      const state = m.id ? minerStore.minerStates.get(m.id) : undefined;
      return state?.status === "on";
    })
    .reduce((sum, m) => {
      const state = m.id ? minerStore.minerStates.get(m.id) : undefined;
      return sum + (state?.power_consumption || 0);
    }, 0);
});

// ---------- Mining performance aggregates (per OU) ----------
interface UnitPerformance {
  unitId: string;
  unitName: string;
  snapshot: MiningPerformanceSnapshot;
}

const unitPerformances = computed<UnitPerformance[]>(() => {
  const out: UnitPerformance[] = [];
  for (const [unitId, ctx] of latestDecisionalContexts.value.entries()) {
    if (!ctx.mining_performance) continue;
    const unit = optimizationUnitStore.optimizationUnits.find((u) => u.id === unitId);
    out.push({
      unitId,
      unitName: unit?.name || unitId,
      snapshot: ctx.mining_performance,
    });
  }
  return out;
});

// Aggregated pool-side hashrate (sum across units, normalized to TH/s)
const totalPoolHashRate = computed(() => {
  let total = 0;
  for (const p of unitPerformances.value) {
    const hr = p.snapshot.current_hashrate;
    if (hr?.value) total += normalizeHashRate(hr.value, hr.unit || "TH/s");
  }
  return total;
});

const totalPoolHashRate24h = computed(() => {
  let total = 0;
  for (const p of unitPerformances.value) {
    const hr = p.snapshot.pool_stats?.average_hashrate_24h;
    if (hr?.value) total += normalizeHashRate(hr.value, hr.unit || "TH/s");
  }
  return total;
});

const totalUnpaidBalance = computed(() => {
  let total = 0;
  for (const p of unitPerformances.value) {
    const sats = p.snapshot.pool_stats?.unpaid_balance;
    if (sats != null) total += sats;
  }
  return total;
});

const totalEstimatedPayout = computed(() => {
  let total = 0;
  for (const p of unitPerformances.value) {
    const sats = p.snapshot.pool_stats?.estimated_next_payout;
    if (sats != null) total += sats;
  }
  return total;
});

const totalWorkers = computed(() => {
  let total = 0;
  for (const p of unitPerformances.value) {
    total += p.snapshot.pool_stats?.workers?.length ?? 0;
  }
  return total;
});

// Soonest next payout across all units
const nextPayoutAt = computed<string | null>(() => {
  let soonest: number | null = null;
  for (const p of unitPerformances.value) {
    const ts = p.snapshot.payout_schedule?.next_payout_at;
    if (!ts) continue;
    const t = new Date(ts).getTime();
    if (soonest === null || t < soonest) soonest = t;
  }
  return soonest != null ? new Date(soonest).toISOString() : null;
});

const nextPayoutLabel = computed(() => {
  void now.value;
  if (!nextPayoutAt.value) return "-";
  const diffMs = new Date(nextPayoutAt.value).getTime() - now.value;
  if (diffMs <= 0) return "due";
  const minutes = Math.floor(diffMs / 60000);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  if (days > 0) return `in ~${days}d`;
  if (hours > 0) return `in ~${hours}h`;
  return `in ${minutes}m`;
});

// ---------- Formatters ----------
function formatHashRateTH(thPerS: number): string {
  if (thPerS === 0) return "-";
  if (thPerS >= 1000) return `${(thPerS / 1000).toFixed(2)} PH/s`;
  if (thPerS >= 1) return `${thPerS.toFixed(1)} TH/s`;
  if (thPerS >= 0.001) return `${(thPerS * 1000).toFixed(0)} GH/s`;
  return `${(thPerS * 1_000_000).toFixed(0)} MH/s`;
}

function formatSats(sats: number | null | undefined): string {
  if (sats == null) return "-";
  if (Math.abs(sats) >= 100_000_000) {
    return `${(sats / 100_000_000).toFixed(4)} BTC`;
  }
  return `${sats.toLocaleString()} sat`;
}

const formattedDeviceHashRate = computed(() => formatHashRateTH(totalDeviceHashRate.value));
const formattedPoolHashRate = computed(() => formatHashRateTH(totalPoolHashRate.value));
const formattedPoolHashRate24h = computed(() => formatHashRateTH(totalPoolHashRate24h.value));
</script>

<template>
  <div class="dashboard-root space-y-5">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-base-content">Mining</h1>
        <p class="text-sm text-base-content/50 mt-0.5">
          Pool performance, payouts &amp; miner devices
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
    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-7 gap-3">
      <KpiCard
        label="Pool Hash Rate"
        :value="formattedPoolHashRate"
        :sub-value="totalPoolHashRate24h > 0 ? `24h ${formattedPoolHashRate24h}` : ''"
        :icon="PhTrendUp"
        icon-color="text-primary"
        icon-bg-color="bg-primary/15"
        :value-color="totalPoolHashRate > 0 ? 'text-primary' : 'text-base-content/30'"
      />
      <KpiCard
        label="Device Hash Rate"
        :value="formattedDeviceHashRate"
        :icon="PhCpu"
        icon-color="text-emerald-400"
        icon-bg-color="bg-emerald-400/15"
        :value-color="totalDeviceHashRate > 0 ? 'text-emerald-400' : 'text-base-content/30'"
      />
      <KpiCard
        label="Power Draw"
        :value="totalDevicePower > 0 ? formatPower(totalDevicePower) : '-'"
        :icon="PhLightning"
        icon-color="text-warning"
        icon-bg-color="bg-warning/15"
        :value-color="totalDevicePower > 0 ? 'text-warning' : 'text-base-content/30'"
      />
      <KpiCard
        label="Miners"
        :value="`${runningMiners} / ${activeMiners}`"
        :sub-value="`of ${totalMiners} total`"
        :icon="PhPower"
        icon-color="text-primary"
        icon-bg-color="bg-primary/15"
        value-color="text-primary"
      />
      <KpiCard
        label="Workers"
        :value="totalWorkers > 0 ? `${totalWorkers}` : '-'"
        sub-value="reporting"
        :icon="PhUsersFour"
        icon-color="text-sky-400"
        icon-bg-color="bg-sky-400/15"
        :value-color="totalWorkers > 0 ? 'text-sky-400' : 'text-base-content/30'"
      />
      <KpiCard
        label="Unpaid Balance"
        :value="formatSats(totalUnpaidBalance > 0 ? totalUnpaidBalance : null)"
        :sub-value="totalEstimatedPayout > 0 ? `est. ${formatSats(totalEstimatedPayout)}` : ''"
        :icon="PhCurrencyBtc"
        icon-color="text-yellow-400"
        icon-bg-color="bg-yellow-400/15"
        :value-color="totalUnpaidBalance > 0 ? 'text-yellow-400' : 'text-base-content/30'"
      />
      <KpiCard
        label="Next Payout"
        :value="nextPayoutLabel"
        :icon="PhClockCountdown"
        icon-color="text-teal-400"
        icon-bg-color="bg-teal-400/15"
        :value-color="nextPayoutAt ? 'text-teal-400' : 'text-base-content/30'"
      />
    </div>

    <!-- Empty state when no performance tracker data -->
    <div
      v-if="unitPerformances.length === 0"
      class="rounded-xl border border-base-300/20 bg-base-100/30 backdrop-blur-sm p-8 text-center"
    >
      <PhTrendUp :size="36" class="mx-auto text-base-content/15 mb-2" />
      <span class="block text-sm text-base-content/40">
        No mining performance data available
      </span>
      <span class="block text-xs text-base-content/30 mt-1">
        Assign a performance tracker to an optimization unit to see pool stats here.
      </span>
    </div>

    <!-- Per-unit Pool Stats and Payout -->
    <div
      v-for="perf in unitPerformances"
      :key="perf.unitId"
      class="space-y-3"
    >
      <div class="flex items-center gap-2">
        <PhTrendUp :size="16" class="text-base-content/40" />
        <h2 class="text-sm font-semibold text-base-content/60 uppercase tracking-wider">
          {{ perf.unitName }}
        </h2>
        <span class="text-[10px] text-base-content/30 ml-auto">
          {{ formatTimeAgo(perf.snapshot.timestamp) }}
        </span>
      </div>
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-3">
        <PoolStatsCard
          class="lg:col-span-2"
          :snapshot="perf.snapshot"
        />
        <PayoutCard :snapshot="perf.snapshot" />
      </div>
    </div>

    <!-- Per-miner runtime state (from miner_state in decisional context) -->
    <div>
      <div class="flex items-center gap-2 mb-3">
        <PhCpu :size="16" class="text-base-content/40" />
        <h2 class="text-sm font-semibold text-base-content/60 uppercase tracking-wider">
          Miner Runtime State
        </h2>
        <span class="text-xs text-base-content/30 ml-auto">
          {{ runningMiners }} running
        </span>
      </div>
      <div v-if="minerStore.miners.length === 0" class="flex flex-col items-center py-12 text-center">
        <PhCpu :size="36" class="text-base-content/15 mb-2" />
        <span class="text-sm text-base-content/30">No miners configured</span>
        <RouterLink to="/settings/miners" class="text-xs text-primary/60 hover:text-primary mt-1">
          Add miners in Settings
        </RouterLink>
      </div>
      <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <MinerStateCard
          v-for="miner in minerStore.miners"
          :key="miner.id"
          :miner="miner"
          :state="miner.id ? minerStore.minerStates.get(miner.id) : undefined"
        />
      </div>
    </div>
  </div>
</template>

<style scoped></style>
