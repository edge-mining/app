<script setup lang="ts">
import { PhCpu, PhLego } from "@phosphor-icons/vue";

defineProps<{
  size?: number;
  weight?: "thin" | "light" | "regular" | "bold" | "fill" | "duotone";
}>();
</script>

<template>
  <div class="relative inline-flex items-center justify-center" :style="{ width: `${size || 26}px`, height: `${size || 26}px` }">
    <PhLego :size="(size || 26) * 0.75" :weight="weight || 'duotone'" class="text-current absolute bottom-0 right-0" />
    <PhCpu :size="(size || 26) * 0.6" weight="fill" class="absolute top-0 left-0 text-current opacity-90" />
  </div>
</template>
