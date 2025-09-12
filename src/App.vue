<script setup lang="ts">
import { ref } from "vue";
import SidebarMenu from "./components/SidebarMenu.vue";

const showDrawer = ref(true);
</script>

<template>
  <div class="drawer">
    <input
      id="my-drawer"
      type="checkbox"
      class="drawer-toggle"
      v-model="showDrawer"
    />

    <div
      class="drawer-side relative border-r"
      :class="showDrawer ? 'w-60' : 'w-0'"
    >
      <label for="my-drawer" aria-label="close sidebar"></label>
      <SidebarMenu />
    </div>

    <div class="drawer-content relative pl-12">
      <!-- Page content here -->
      <label
        for="my-drawer"
        class="absolute top-2 -left-2 btn btn-sm btn-neutral drawer-button z-10"
        >{{ showDrawer ? "<" : ">" }}</label
      >
      <RouterView />
    </div>
  </div>
</template>

<style scoped></style>
