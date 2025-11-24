<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  size?: number | string
  color?: string
  strokeWidth?: number | string
}

const props = withDefaults(defineProps<Props>(), {
  size: 46,
  color: '#BEFFA3',
  strokeWidth: 4.17
})

const sizeValue = computed(() => {
  return typeof props.size === 'number' ? `${props.size}px` : props.size
})
</script>

<template>
  <svg
    :width="sizeValue"
    :height="sizeValue"
    viewBox="0 0 46 46"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M31.825 13.917L43.6549 2.08496M2.085 13.917L13.915 2.08496M31.805 13.952V43.705M31.835 13.923H2.085M31.825 43.653L43.6549 31.821"
      :stroke="color"
      :stroke-width="strokeWidth"
      stroke-miterlimit="1.5"
      stroke-linecap="round"
      stroke-linejoin="round"
    />
  </svg>
</template>
