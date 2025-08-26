import { createRouter, createWebHistory } from "vue-router";
import DashboardView from "../views/DashboardView.vue";
import SettingsView from "../views/SettingsView.vue";

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
      path: "/settings",
      name: "settings",
      // This is the default route, it will be replaced by the setHomeRoute function
      component: SettingsView,
      meta: {
        title: "Settings",
      },
    },
  ],
});

export default router;
