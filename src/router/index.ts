import { createRouter, createWebHistory } from "vue-router";
import DashboardView from "../views/DashboardView.vue";
import MiningDashboardView from "../views/dashboard/MiningDashboardView.vue";
import MinersSettingsView from "../views/settings/MinersSettingsView.vue";
import EnergySourcesSettingsView from "../views/settings/EnergySourcesSettingsView.vue";
import EnergyMonitorSettingsView from "../views/settings/EnergyMonitorSettingsView.vue";
import MinerControllersSettingsView from "../views/settings/MinerControllersSettingsView.vue";
import PerformanceTrackersSettingsView from "../views/settings/PerformanceTrackersSettingsView.vue";
import ForecastProvidersSettingsView from "../views/settings/ForecastProvidersSettingsView.vue";
import PoliciesSettingsView from "../views/settings/PoliciesSettingsView.vue";
import NotifiersSettingsView from "../views/settings/NotifiersSettingsView.vue";
import ExternalServicesSettingsView from "../views/settings/ExternalServicesSettingsView.vue";
import OptimizationUnitsSettingsView from "../views/settings/OptimizationUnitsSettingsView.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      name: "dashboard",
      // This is the default route, it will be replaced by the setHomeRoute function
      component: DashboardView,
    },
    {
      path: "/dashboard/mining",
      name: "dashboard.mining",
      component: MiningDashboardView,
    },
    {
      path: "/settings/",
      name: "settings",
      redirect: "/settings/miners",
      children: [
        {
          path: "miners",
          name: "settings.miners",
          component: MinersSettingsView,
        },
        {
          path: "energy-sources",
          name: "settings.energySources",
          component: EnergySourcesSettingsView,
        },
        {
          path: "energy-monitors",
          name: "settings.energyMonitors",
          component: EnergyMonitorSettingsView,
        },
        {
          path: "miner-controllers",
          name: "settings.minerControllers",
          component: MinerControllersSettingsView,
        },
        {
          path: "performance-trackers",
          name: "settings.performanceTrackers",
          component: PerformanceTrackersSettingsView,
        },
        {
          path: "forecast-providers",
          name: "settings.forecastProviders",
          component: ForecastProvidersSettingsView,
        },
        {
          path: "policies",
          name: "settings.policies",
          component: PoliciesSettingsView,
        },
        {
          path: "optimization-units",
          name: "settings.optimizationUnits",
          component: OptimizationUnitsSettingsView,
        },
        {
          path: "notifiers",
          name: "settings.notifiers",
          component: NotifiersSettingsView,
        },
        {
          path: "external-services",
          name: "settings.externalServices",
          component: ExternalServicesSettingsView,
        },
      ],
    },
  ],
});

export default router;
