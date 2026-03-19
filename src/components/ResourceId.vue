<script setup lang="ts">
import { ref } from "vue";
import { PhHash } from "@phosphor-icons/vue";

const props = withDefaults(defineProps<{
  id: string | number;
  tooltipPosition?: "tooltip-top" | "tooltip-bottom" | "tooltip-left" | "tooltip-right";
}>(), {
  tooltipPosition: "tooltip-top",
});

const idCopied = ref(false);

async function copyId() {
  if (!props.id) return;
  const text = String(props.id);
  try {
    await navigator.clipboard.writeText(text);
    idCopied.value = true;
    setTimeout(() => (idCopied.value = false), 1500);
  } catch {
    const el = document.createElement("textarea");
    el.value = text;
    document.body.appendChild(el);
    el.select();
    document.execCommand("copy");
    document.body.removeChild(el);
    idCopied.value = true;
    setTimeout(() => (idCopied.value = false), 1500);
  }
}
</script>

<template>
  <button
    class="tooltip text-xs opacity-50 hover:opacity-100 transition-opacity flex items-center gap-0.5"
    :class="tooltipPosition"
    :data-tip="idCopied ? 'Copied!' : `ID: ${id}`"
    @click="copyId"
  >
    <PhHash :size="12" />
    <span class="font-mono small text-left">{{ String(id).split('-')[0] }}</span>
  </button>
</template>
