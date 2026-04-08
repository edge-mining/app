<script setup lang="ts">
import { ref, defineAsyncComponent, computed } from "vue";
import SidebarMenu from "./components/SidebarMenu.vue";
import TopBar from "./components/TopBar.vue";
import { useAppStore } from "./core/stores/appStore";
import { PhCheckCircle, PhWarning, PhInfo, PhXCircle } from "@phosphor-icons/vue";

const BottomBar = defineAsyncComponent(() => import("./components/BottomBar.vue"));

const showDrawer = ref(true);
const appStore = useAppStore();

const toastIcon = computed(() => {
  switch (appStore.userNotification?.status) {
    case "success": return PhCheckCircle;
    case "warning": return PhWarning;
    case "info": return PhInfo;
    case "error": return PhXCircle;
    default: return PhInfo;
  }
});

const toastClass = computed(() => {
  switch (appStore.userNotification?.status) {
    case "success": return "alert-success";
    case "warning": return "alert-warning";
    case "info": return "alert-info";
    case "error": return "alert-error";
    default: return "alert-info";
  }
});
</script>

<template>
  <div class="drawer h-screen" :class="{ 'drawer-open': showDrawer }">
    <input
      id="my-drawer"
      type="checkbox"
      class="drawer-toggle"
      v-model="showDrawer"
    />

    <div class="drawer-side">
      <label for="my-drawer" aria-label="close sidebar" class="drawer-overlay"></label>
      <div class="w-60 h-full overflow-y-auto bg-base-100 border-r border-base-300/40">
        <SidebarMenu />
      </div>
    </div>

    <div class="drawer-content flex flex-col h-screen overflow-hidden bg-base-200">
      <TopBar :show-drawer="showDrawer" @toggle-drawer="showDrawer = !showDrawer" />
      <main class="flex-1 overflow-y-auto p-5">
        <RouterView />
      </main>
      <BottomBar />
    </div>
  </div>

  <!-- Toast Notifications -->
  <div class="toast toast-end toast-bottom z-50">
    <Transition name="slide-fade">
      <div v-if="appStore.userNotification" class="alert" :class="toastClass">
        <component :is="toastIcon" :size="20" weight="bold" />
        <span>{{ appStore.userNotification.message }}</span>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.slide-fade-enter-active {
  transition: all 0.3s ease-out;
}
.slide-fade-leave-active {
  transition: all 0.2s ease-in;
}
.slide-fade-enter-from {
  transform: translateX(20px);
  opacity: 0;
}
.slide-fade-leave-to {
  transform: translateX(20px);
  opacity: 0;
}
</style>
