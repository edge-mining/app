import { ref, computed, onMounted, onUnmounted } from "vue";
import { useMinerStore } from "../stores/minerStore";
import { useOptimizationUnitStore } from "../stores/optimizationUnitStore";
import { useEnergySourceStore } from "../stores/energySourceStore";
import { usePolicyStore } from "../stores/policyStore";
import { useDashboardStore } from "../stores/dashboardStore";
import { normalizeHashRate } from "../utils/index";

// Re-export types from the store for backward compatibility
export type { DashboardEvent, TimeSeriesPoint, MinerOnOffEvent } from "../stores/dashboardStore";

export function useDashboardPolling(intervalMs = 5000) {
  const minerStore = useMinerStore();
  const optimizationUnitStore = useOptimizationUnitStore();
  const energySourceStore = useEnergySourceStore();
  const policyStore = usePolicyStore();
  const dashboardStore = useDashboardStore();

  const lastUpdated = ref<Date>(new Date());
  const isPolling = ref(false);

  // Computed refs that stay reactive to store changes
  const hashRateSeries = computed(() => dashboardStore.hashRateSeries);
  const powerSeries = computed(() => dashboardStore.powerSeries);
  const events = computed(() => dashboardStore.events);
  const minerOnOffEvents = computed(() => dashboardStore.minerOnOffEvents);

  let pollTimer: number | undefined;

  function detectMinerChanges() {
    for (const miner of minerStore.miners) {
      if (!miner.id) continue;
      const prevStatus = dashboardStore.previousMinerStatuses.get(miner.id);
      if (prevStatus && prevStatus !== miner.status) {
        const now = Math.floor(Date.now() / 1000);
        if (miner.status === "on" && prevStatus !== "on") {
          dashboardStore.addEvent({
            type: "miner_start",
            message: `${miner.name} started`,
            timestamp: new Date(),
          });
          dashboardStore.addMinerOnOffEvent({
            time: now,
            minerName: miner.name,
            action: "on",
          });
        } else if (miner.status === "off" && prevStatus !== "off") {
          dashboardStore.addEvent({
            type: "miner_stop",
            message: `${miner.name} stopped`,
            timestamp: new Date(),
          });
          dashboardStore.addMinerOnOffEvent({
            time: now,
            minerName: miner.name,
            action: "off",
          });
        } else {
          dashboardStore.addEvent({
            type: "status_change",
            message: `${miner.name}: ${prevStatus} → ${miner.status}`,
            timestamp: new Date(),
          });
        }
      }
      dashboardStore.previousMinerStatuses.set(miner.id, miner.status);
    }
  }

  async function refreshMinerStatuses() {
    const pollableMiners = minerStore.miners.filter(
      (m) => m.id != null && m.active && m.controller_id
    );
    if (pollableMiners.length > 0) {
      await Promise.all(
        pollableMiners.map((m) => minerStore.getMinerStatus(m.id!.toString()))
      );
    }
  }

  function recordSnapshot() {
    const now = Math.floor(Date.now() / 1000);

    let totalHash = 0;
    let totalPower = 0;
    for (const m of minerStore.miners) {
      if (m.status === "on") {
        if (m.hash_rate?.value) {
          totalHash += normalizeHashRate(m.hash_rate.value, m.hash_rate.unit || "TH/s");
        }
        totalPower += m.power_consumption || 0;
      }
    }

    dashboardStore.addSeriesPoint("hashRate", { time: now, value: totalHash });
    dashboardStore.addSeriesPoint("power", { time: now, value: totalPower });
  }

  async function poll() {
    isPolling.value = true;
    try {
      await refreshMinerStatuses();
      detectMinerChanges();
      recordSnapshot();
      lastUpdated.value = new Date();
    } catch (err) {
      console.warn("[Dashboard] polling error:", err);
    } finally {
      isPolling.value = false;
    }
  }

  async function initLoad() {
    await Promise.all([
      minerStore.loadMiners(),
      optimizationUnitStore.loadOptimizationUnits(),
      energySourceStore.loadEnergySources(),
      policyStore.loadPolicies(),
    ]);
    // Initialize previous statuses only if empty (first visit)
    if (dashboardStore.previousMinerStatuses.size === 0) {
      for (const miner of minerStore.miners) {
        if (miner.id) {
          dashboardStore.previousMinerStatuses.set(miner.id, miner.status);
        }
      }
    }
    await poll();
  }

  onMounted(async () => {
    try {
      await initLoad();
    } catch (err) {
      console.warn("[Dashboard] initial load error:", err);
    }
    pollTimer = window.setInterval(poll, intervalMs);
  });

  onUnmounted(() => {
    if (pollTimer !== undefined) {
      clearInterval(pollTimer);
    }
  });

  return {
    lastUpdated,
    isPolling,
    events,
    hashRateSeries,
    powerSeries,
    minerOnOffEvents,
  };
}
