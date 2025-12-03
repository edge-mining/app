<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
import { PhPulse, PhLightning, PhCpu } from "@phosphor-icons/vue";
import VectorIcon from "./VectorIcon.vue";

const route = useRoute();

const isDashboardActive = computed(() => route.path === "/");

const isEnergyOpen = computed(() => {
  return (
    route.path.startsWith("/settings/energy-sources") ||
    route.path.startsWith("/settings/energy-monitors")
  );
});

const isMiningOpen = computed(() => {
  return (
    route.path.startsWith("/settings/miners") ||
    route.path.startsWith("/settings/miner-controllers")
  );
});
</script>
<template>
  <div class="navbar bg-base-200 p-4">
    <div class="flex-none">
      <div class="flex flex-row">
        <VectorIcon name="logo" class="inline-block size-8 mr-2" />
        <div class="flex flex-col">
          <span class="text-xs">EDGE MINING</span>
          <span>Jean Claude</span>
        </div>
      </div>

      <ul class="menu px-1 w-full">
        <!-- Dashboard -->
        <li class="w-full">
          <RouterLink
            to="/"
            class="flenter w-full text-lg"
            active-class="active text-primary"
            exact
          >
            <PhPulse :weight="isDashboardActive ? 'fill' : 'regular'" />
            Dashboard
          </RouterLink>
        </li>

        <!-- Energy -->
        <li class="w-full">
          <details :open="isEnergyOpen">
            <summary
              class="text-lg"
              :class="{ 'text-primary font-semibold': isEnergyOpen }"
            >
              <PhLightning :weight="isEnergyOpen ? 'fill' : 'regular'" />
              Energy
            </summary>
            <ul class="bg-base-100 rounded-t-none p-2 w-full submenu-curved">
              <li class="w-full submenu-item">
                <RouterLink
                  to="/settings/energy-sources"
                  class="flenter w-full"
                  active-class="active text-primary"
                >
                  Energy Sources
                </RouterLink>
              </li>
              <li class="w-full submenu-item">
                <RouterLink
                  to="/settings/energy-monitors"
                  class="flenter w-full"
                  active-class="active text-primary "
                >
                  Energy Monitors
                </RouterLink>
              </li>
            </ul>
          </details>
        </li>

        <!-- Mining -->
        <li class="w-full">
          <details :open="isMiningOpen">
            <summary
              class="text-lg"
              :class="{ 'text-primary font-semibold': isMiningOpen }"
            >
              <PhCpu :weight="isMiningOpen ? 'fill' : 'regular'" />
              Mining
            </summary>
            <ul class="bg-base-100 rounded-t-none p-2 w-full submenu-curved">
              <li class="w-full submenu-item">
                <RouterLink
                  to="/settings/miners"
                  class="flenter w-full"
                  active-class="active text-primary"
                >
                  Miners
                </RouterLink>
              </li>
              <li class="w-full submenu-item">
                <RouterLink
                  to="/settings/miner-controllers"
                  class="flenter w-full"
                  active-class="active text-primary"
                >
                  Miner Controllers
                </RouterLink>
              </li>
            </ul>
          </details>
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.submenu-curved {
  position: relative;
}

.submenu-item {
  position: relative;
  padding-left: 1rem;
}

.submenu-item::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0;
  bottom: 50%;
  width: 0.75rem;
  border-left: 2px solid oklch(43% 0 0);
  border-bottom: 2px solid oklch(43% 0 0);
  border-bottom-left-radius: 0.5rem;
}

.submenu-item:not(:last-child)::after {
  content: "";
  position: absolute;
  left: 0;
  top: 50%;
  bottom: 0;
  width: 2px;
  background: oklch(43% 0 0);
}
</style>
