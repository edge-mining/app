<script setup lang="ts">
import { ref } from "vue";
import SidebarMenu from "./components/SidebarMenu.vue";
import { PhCaretLeft, PhCaretRight } from "@phosphor-icons/vue";

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

    <div class="drawer-side relative" :class="showDrawer ? 'w-60' : 'w-0'">
      <label for="my-drawer" aria-label="close sidebar"></label>
      <SidebarMenu />
    </div>

    <div class="drawer-content relative pl-12">
      <!-- Page content here -->
      <label
        for="my-drawer"
        class="absolute top-12 -left-2 rounded border border-base-300 text-base-300 size-6 z-10 flenter"
      >
        <div>
          <PhCaretLeft v-if="showDrawer" />
          <PhCaretRight v-else />
        </div>
      </label>
      <div class="mt-8">
        <RouterView />
      </div>
    </div>
  </div>
</template>

<style scoped></style>
