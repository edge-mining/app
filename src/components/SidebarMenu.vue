<script setup lang="ts">
import { ref, computed } from "vue";
import { useRoute } from "vue-router";
import {
  PhPulse,
  PhLightning,
  PhCpu,
  PhPlug,
  PhBell,
  PhGraph,
  PhHouse,
} from "@phosphor-icons/vue";
import VectorIcon from "./VectorIcon.vue";

const route = useRoute();

const isDashboardOpen = ref(true);
const isEnergyOpen = ref(true);
const isMiningOpen = ref(true);
const isAutomationOpen = ref(true);
const isHomeLoadsOpen = ref(true);

const isDashboardActive = computed(() =>
  route.path === "/" || route.path.startsWith("/dashboard")
);

const isEnergyActive = computed(() =>
  ["/settings/energy-sources", "/settings/energy-monitors", "/settings/forecast-providers"].some(
    (p) => route.path.startsWith(p)
  )
);

const isMiningActive = computed(() =>
  ["/settings/miners", "/settings/miner-controllers"].some((p) =>
    route.path.startsWith(p)
  )
);

const isAutomationActive = computed(() =>
  ["/settings/optimization-units", "/settings/policies"].some((p) =>
    route.path.startsWith(p)
  )
);

const isHomeLoadsActive = computed(() =>
  ["/settings/home-loads"].some((p) => route.path.startsWith(p))
);
</script>
<template>
  <div class="sidebar-container relative h-full">
    <!-- Top glow effect -->
    <div class="sidebar-glow"></div>

    <div class="navbar p-4 h-full relative z-10">
      <div class="flex-none h-full">
        <div class="flex flex-row items-center py-4 mb-2">
          <VectorIcon name="logo" class="inline-block size-9" />
          <div class="flex flex-col ml-3">
            <span
              class="text-[10px] uppercase tracking-wider text-base-300 font-medium"
              >Edge Mining</span
            >
            <!-- <span class="text-sm font-medium">Satoshi Nakamoto</span> -->
          </div>
        </div>

        <ul class="menu px-0 w-full gap-0.5">
          <!-- Dashboard -->
          <li class="w-full">
            <details :open="isDashboardOpen">
              <summary
                class="text-sm font-medium"
                :class="{ 'text-primary': isDashboardActive }"
                @click.prevent="isDashboardOpen = !isDashboardOpen"
              >
                <PhPulse :size="18" />
                Dashboard
              </summary>
              <ul class="rounded-t-none p-2 w-full">
                <li class="w-full">
                  <RouterLink
                    to="/"
                    class="w-full text-sm"
                    active-class="active text-primary"
                    exact
                  >
                    Overview
                  </RouterLink>
                </li>
                <li class="w-full">
                  <RouterLink
                    to="/dashboard/home-loads"
                    class="w-full text-sm"
                    active-class="active text-primary"
                  >
                    Home Loads
                  </RouterLink>
                </li>
              </ul>
            </details>
          </li>

          <!-- Optimization -->
          <li class="w-full">
            <details :open="isAutomationOpen">
              <summary
                class="text-sm font-medium"
                :class="{ 'text-primary': isAutomationActive }"
                @click.prevent="isAutomationOpen = !isAutomationOpen"
              >
                <PhGraph :size="18" />
                Optimization
              </summary>
              <ul class="rounded-t-none p-2 w-full">
                <li class="w-full">
                  <RouterLink
                    to="/settings/optimization-units"
                    class="w-full text-sm"
                    active-class="active text-primary"
                  >
                    Units
                  </RouterLink>
                </li>
                <li class="w-full">
                  <RouterLink
                    to="/settings/policies"
                    class="w-full text-sm"
                    active-class="active text-primary"
                  >
                    Policies
                  </RouterLink>
                </li>
              </ul>
            </details>
          </li>

          <!-- Energy -->
          <li class="w-full">
            <details :open="isEnergyOpen">
              <summary
                class="text-sm font-medium"
                :class="{ 'text-primary': isEnergyActive }"
                @click.prevent="isEnergyOpen = !isEnergyOpen"
              >
                <PhLightning :size="18" />
                Energy
              </summary>
              <ul class="rounded-t-none p-2 w-full">
                <li class="w-full">
                  <RouterLink
                    to="/settings/energy-sources"
                    class="w-full text-sm"
                    active-class="active text-primary"
                  >
                    Energy Sources
                  </RouterLink>
                </li>
                <li class="w-full">
                  <RouterLink
                    to="/settings/energy-monitors"
                    class="w-full text-sm"
                    active-class="active text-primary"
                  >
                    Energy Monitors
                  </RouterLink>
                </li>
                <li class="w-full">
                  <RouterLink
                    to="/settings/forecast-providers"
                    class="w-full text-sm"
                    active-class="active text-primary"
                  >
                    Forecast Providers
                  </RouterLink>
                </li>
              </ul>
            </details>
          </li>

          <!-- Home Loads -->
          <li class="w-full">
            <details :open="isHomeLoadsOpen">
              <summary
                class="text-sm font-medium"
                :class="{ 'text-primary': isHomeLoadsActive }"
                @click.prevent="isHomeLoadsOpen = !isHomeLoadsOpen"
              >
                <PhHouse :size="18" />
                Home Loads
              </summary>
              <ul class="rounded-t-none p-2 w-full">
                <li class="w-full">
                  <RouterLink
                    to="/settings/home-loads"
                    class="w-full text-sm"
                    active-class="active text-primary"
                    exact
                  >
                    Profiles
                  </RouterLink>
                </li>
                <li class="w-full">
                  <RouterLink
                    to="/settings/home-loads-training"
                    class="w-full text-sm"
                    active-class="active text-primary"
                  >
                    Training
                  </RouterLink>
                </li>
              </ul>
            </details>
          </li>

          <!-- Mining -->
          <li class="w-full">
            <details :open="isMiningOpen">
              <summary
                class="text-sm font-medium"
                :class="{ 'text-primary': isMiningActive }"
                @click.prevent="isMiningOpen = !isMiningOpen"
              >
                <PhCpu :size="18" />
                Mining
              </summary>
              <ul class="rounded-t-none p-2 w-full">
                <li class="w-full">
                  <RouterLink
                    to="/settings/miners"
                    class="w-full text-sm"
                    active-class="active text-primary"
                  >
                    Miners
                  </RouterLink>
                </li>
                <li class="w-full">
                  <RouterLink
                    to="/settings/miner-controllers"
                    class="w-full text-sm"
                    active-class="active text-primary"
                  >
                    Miner Controllers
                  </RouterLink>
                </li>
              </ul>
            </details>
          </li>

          <!-- Integrations -->
          <li class="w-full">
            <RouterLink
              to="/settings/external-services"
              class="w-full text-sm font-medium"
              active-class="active text-primary"
            >
              <PhPlug :size="18" />
              External Services
            </RouterLink>
          </li>

          <!-- Notifiers -->
          <li class="w-full">
            <RouterLink
              to="/settings/notifiers"
              class="w-full text-sm font-medium"
              active-class="active text-primary"
            >
              <PhBell :size="18" />
              Notifiers
            </RouterLink>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sidebar-container {
  overflow: hidden;
}

.sidebar-glow {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 12rem;
  background: radial-gradient(
    ellipse 120% 100% at 50% -30%,
    oklch(75% 0.25 130 / 0.3) 0%,
    oklch(75% 0.2 130 / 0.15) 30%,
    oklch(75% 0.15 130 / 0.05) 50%,
    transparent 80%
  );
  pointer-events: none;
  z-index: 0;
}

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
  border-left: 2px solid oklch(35% 0 0);
  border-bottom: 2px solid oklch(35% 0 0);
  border-bottom-left-radius: 0.5rem;
}

.submenu-item:not(:last-child)::after {
  content: "";
  position: absolute;
  left: 0;
  top: 50%;
  bottom: 0;
  width: 2px;
  background: oklch(35% 0 0);
}
</style>
