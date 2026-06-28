<script setup lang="ts">
import { VueFlow } from '@vue-flow/core';
import { Background } from '@vue-flow/background';
import { PhGraph } from '@phosphor-icons/vue';
import type { RuleConditions } from '../../core/models/ruleEngine';
import '@vue-flow/core/dist/style.css';
import '@vue-flow/core/dist/theme-default.css';

interface Props {
  conditions: RuleConditions;
}

defineProps<Props>();
</script>

<template>
  <div class="h-full w-full relative">
    <VueFlow 
      :nodes="[]" 
      :edges="[]"
      class="vue-flow-container"
    >
      <Background pattern-color="#4b5563" :gap="20" variant="dots" />
    </VueFlow>
    
    <!-- Coming Soon Overlay -->
    <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
      <div class="bg-base-100 rounded-2xl shadow-2xl p-12 max-w-md text-center border border-base-300">
        <PhGraph :size="80" class="mx-auto mb-6 text-primary" weight="duotone" />
        <h3 class="text-2xl font-bold mb-3 text-base-content">Graph Visualization</h3>
        <p class="text-base-content/70 text-lg mb-4">Coming Soon</p>
        <p class="text-base-content/60 text-sm">
          Interactive graph visualization of rule conditions will be available in a future release.
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.vue-flow-container {
  background: oklch(var(--b2));
}
</style>
