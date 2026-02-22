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
  <header
    class="h-14 flex-shrink-0 flex items-center gap-3 px-4 border-b border-base-300/30 bg-base-200 z-10"
  >
    <button
      class="rounded border border-base-300 text-base-300 size-6 flenter hover:text-base-content hover:border-base-content transition-colors"
      aria-label="Toggle sidebar"
      @click="emit('toggleDrawer')"
    >
      <PhCaretLeft v-if="props.showDrawer" :size="14" />
      <PhCaretRight v-else :size="14" />
    </button>

    <slot />
  </header>
</template>

<style scoped></style>
