<script setup lang="ts">
import { PhCaretLeft, PhCaretRight } from "@phosphor-icons/vue";

const props = defineProps<{
  showDrawer: boolean;
}>();

const emit = defineEmits<{
  toggleDrawer: [];
}>();
</script>

<template>
  <div class="navbar h-12 border-b border-base-300/40 bg-base-100">
    <div class="navbar-start">
      <button
        class="rounded border border-base-300 text-base-300 size-6 flenter hover:text-base-content hover:border-base-content transition-colors"
        aria-label="Toggle sidebar"
        @click="emit('toggleDrawer')"
      >
        <PhCaretLeft v-if="props.showDrawer" :size="14" />
        <PhCaretRight v-else :size="14" />
      </button>
    </div>
    <div class="navbar-center">

    </div>
    <div class="navbar-end">

    </div>
  </div>
</template>

<style scoped>
.navbar {
  min-height: 0;
}
</style>
