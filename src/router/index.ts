import { createRouter, createWebHistory } from "vue-router";
import DashboardView from "../views/DashboardView.vue";
import MinersSettingsView from "../views/settings/MinersSettingsView.vue";
import EnergySourcesSettingsView from "../views/settings/EnergySourcesSettingsView.vue";
import EnergyMonitorSettingsView from "../views/settings/EnergyMonitorSettingsView.vue";

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
      ],
    },
  ],
});

export default router;
