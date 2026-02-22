<script setup lang="ts">
import { ref, defineAsyncComponent } from "vue";
import SidebarMenu from "./components/SidebarMenu.vue";
import TopBar from "./components/TopBar.vue";

const BottomBar = defineAsyncComponent(() => import("./components/BottomBar.vue"));

const showDrawer = ref(true);
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
      <div class="w-60 h-full overflow-y-auto bg-base-200 border-r border-base-300/30">
        <SidebarMenu />
      </div>
    </div>

    <div class="drawer-content flex flex-col h-screen overflow-hidden">
      <TopBar :show-drawer="showDrawer" @toggle-drawer="showDrawer = !showDrawer" />
      <main class="flex-1 overflow-y-auto p-6">
        <RouterView />
      </main>
      <BottomBar />
    </div>
  </div>
</template>

<style scoped></style>
