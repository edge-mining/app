<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
import VectorIcon from "./VectorIcon.vue";

const route = useRoute();

const isSettingsOpen = computed(() => {
  return route.path.startsWith("/settings");
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
        <li class="w-full">
          <RouterLink
            to="/"
            class="flenter w-full"
            active-class="active bg-primary text-primary-content font-semibold"
            exact
          >
            Dashboard
          </RouterLink>
        </li>
        <li class="w-full">
          <details :open="isSettingsOpen">
            <summary>Settings</summary>
            <ul class="bg-base-100 rounded-t-none p-2 w-full submenu-curved">
              <li class="w-full submenu-item">
                <RouterLink
                  to="/settings/miners"
                  class="flenter w-full"
                  active-class="active bg-primary text-primary-content font-semibold"
                >
                  Miners
                </RouterLink>
              </li>
              <li class="w-full submenu-item">
                <RouterLink
                  to="/settings/energy-sources"
                  class="flenter w-full"
                  active-class="active bg-primary text-primary-content font-semibold"
                >
                  Energy Sources
                </RouterLink>
              </li>
              <li class="w-full submenu-item">
                <RouterLink
                  to="/settings/energy-monitors"
                  class="flenter w-full"
                  active-class="active bg-primary text-primary-content font-semibold"
                >
                  Energy Monitors
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
