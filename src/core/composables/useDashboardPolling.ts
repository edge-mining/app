import { ref, computed, onMounted, onUnmounted } from "vue";
import { useMinerStore } from "../stores/minerStore";
import { useOptimizationUnitStore } from "../stores/optimizationUnitStore";
import { useEnergySourceStore } from "../stores/energySourceStore";
import { usePolicyStore } from "../stores/policyStore";
import { useDashboardStore } from "../stores/dashboardStore";
import { normalizeHashRate } from "../utils/index";
import { OptimizationUnitService } from "../services/optimizationUnitService";
import type { DecisionalContext } from "../models/policy";
import type { ForecastPowerPoint } from "../models/forecast";

// Re-export types from the store for backward compatibility
export type { DashboardEvent, TimeSeriesPoint, MinerOnOffEvent } from "../stores/dashboardStore";

export function useDashboardPolling(intervalMs = 5000) {
  const minerStore = useMinerStore();
  const optimizationUnitStore = useOptimizationUnitStore();
  const energySourceStore = useEnergySourceStore();
  const policyStore = usePolicyStore();
  const dashboardStore = useDashboardStore();
  const ouService = new OptimizationUnitService();

  const lastUpdated = ref<Date>(new Date());
  const isPolling = ref(false);

  // Computed refs that stay reactive to store changes
  const hashRateSeries = computed(() => dashboardStore.hashRateSeries);
  const powerSeries = computed(() => dashboardStore.powerSeries);
  const energyProductionSeries = computed(() => dashboardStore.energyProductionSeries);
  const batterySOCSeries = computed(() => dashboardStore.batterySOCSeries);
  const batteryPowerSeries = computed(() => dashboardStore.batteryPowerSeries);
  const gridPowerSeries = computed(() => dashboardStore.gridPowerSeries);
  const consumptionSeries = computed(() => dashboardStore.consumptionSeries);
  const events = computed(() => dashboardStore.events);
  const minerOnOffEvents = computed(() => dashboardStore.minerOnOffEvents);
  const latestDecisionalContexts = computed(() => dashboardStore.latestDecisionalContexts);
  const forecastPowerPoints = computed(() => dashboardStore.forecastPowerPoints);

  let pollTimer: number | undefined;
  let pollInProgress = false;

  function detectMinerChanges() {
    for (const miner of minerStore.miners) {
      if (!miner.id) continue;
      const state = minerStore.minerStates.get(miner.id);
      const currentStatus = state?.status ?? 'unknown';
      const prevStatus = dashboardStore.previousMinerStatuses.get(miner.id);
      if (prevStatus && prevStatus !== currentStatus) {
        const now = Math.floor(Date.now() / 1000);
        if (currentStatus === "on" && prevStatus !== "on") {
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
        } else if (currentStatus === "off" && prevStatus !== "off") {
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
            message: `${miner.name}: ${prevStatus} → ${currentStatus}`,
            timestamp: new Date(),
          });
        }
      }
      dashboardStore.previousMinerStatuses.set(miner.id, currentStatus);
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
      const state = m.id ? minerStore.minerStates.get(m.id) : undefined;
      if (state?.status === "on") {
        if (state.hash_rate?.value) {
          totalHash += normalizeHashRate(state.hash_rate.value, state.hash_rate.unit || "TH/s");
        }
        totalPower += state.power_consumption || 0;
      }
    }

    dashboardStore.addSeriesPoint("hashRate", { time: now, value: totalHash });
    dashboardStore.addSeriesPoint("power", { time: now, value: totalPower });
  }

  async function fetchDecisionalContexts() {
    const units = optimizationUnitStore.optimizationUnits.filter((u) => u.id);
    if (units.length === 0) return;

    const results = await Promise.allSettled(
      units.map((u) => ouService.getDecisionalContext(u.id!))
    );

    const now = Math.floor(Date.now() / 1000);
    let totalProduction = 0;
    let totalConsumption = 0;
    let batterySOCSum = 0;
    let batteryPowerSum = 0;
    let batteryCount = 0;
    let totalGridPower = 0;
    let hasEnergyData = false;
    const allForecastPoints: ForecastPowerPoint[] = [];

    for (let i = 0; i < results.length; i++) {
      const result = results[i];
      if (result.status !== "fulfilled") {
        console.warn(
          `[Dashboard] Failed to fetch decisional context for unit ${units[i].id}:`,
          result.reason
        );
        continue;
      }
      const ctx: DecisionalContext = result.value;
      const unitId = units[i].id!;
      dashboardStore.latestDecisionalContexts.set(unitId, ctx);

      if (ctx.energy_state) {
        hasEnergyData = true;
        totalProduction += ctx.energy_state.production ?? 0;

        if (ctx.energy_state.consumption) {
          totalConsumption += ctx.energy_state.consumption.current_power ?? 0;
        }

        if (ctx.energy_state.battery != null) {
          batterySOCSum += ctx.energy_state.battery.state_of_charge ?? 0;
          batteryPowerSum += ctx.energy_state.battery.current_power ?? 0;
          batteryCount++;
        }

        if (ctx.energy_state.grid != null) {
          totalGridPower += ctx.energy_state.grid.current_power ?? 0;
        }
      }

      if (ctx.forecast?.intervals) {
        for (const interval of ctx.forecast.intervals) {
          if (interval.power_points?.length) {
            allForecastPoints.push(...interval.power_points);
          }
        }
      }
    }

    if (hasEnergyData) {
      dashboardStore.addSeriesPoint("energyProduction", { time: now, value: totalProduction });
      dashboardStore.addSeriesPoint("consumption", { time: now, value: totalConsumption });
      dashboardStore.addSeriesPoint("gridPower", { time: now, value: totalGridPower });
      if (batteryCount > 0) {
        dashboardStore.addSeriesPoint("batterySOC", {
          time: now,
          value: batterySOCSum / batteryCount,
        });
        dashboardStore.addSeriesPoint("batteryPower", {
          time: now,
          value: batteryPowerSum / batteryCount,
        });
      }
    }

    // Deduplicate and sort forecast points by timestamp
    if (allForecastPoints.length > 0) {
      const seen = new Set<string>();
      const unique = allForecastPoints.filter((p) => {
        if (seen.has(p.timestamp)) return false;
        seen.add(p.timestamp);
        return true;
      });
      unique.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
      dashboardStore.forecastPowerPoints = unique;
    }
  }

  async function poll() {
    if (pollInProgress) return; // Prevent overlapping polls
    pollInProgress = true;
    isPolling.value = true;
    try {
      await Promise.all([
        refreshMinerStatuses(),
        fetchDecisionalContexts(),
      ]);
      detectMinerChanges();
      recordSnapshot();
      lastUpdated.value = new Date();
    } catch (err) {
      console.warn("[Dashboard] polling error:", err);
    } finally {
      isPolling.value = false;
      pollInProgress = false;
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
          const state = minerStore.minerStates.get(miner.id);
          dashboardStore.previousMinerStatuses.set(miner.id, state?.status ?? 'unknown');
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
    energyProductionSeries,
    batterySOCSeries,
    batteryPowerSeries,
    gridPowerSeries,
    consumptionSeries,
    minerOnOffEvents,
    latestDecisionalContexts,
    forecastPowerPoints,
  };
}
