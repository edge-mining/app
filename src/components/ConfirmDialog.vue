<script setup lang="ts">
import { PhWarning } from "@phosphor-icons/vue";

const props = defineProps<{
  open: boolean;
  title?: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  variant?: "danger" | "warning" | "info";
}>();

const emit = defineEmits<{
  confirm: [];
  cancel: [];
}>();

function handleConfirm() {
  emit("confirm");
}

function handleCancel() {
  emit("cancel");
}
</script>

<template>
  <dialog :class="['modal', { 'modal-open': open }]">
    <div class="modal-box">
      <h3 class="font-bold text-lg flex items-center gap-2">
        <PhWarning
          v-if="variant === 'danger' || variant === 'warning'"
          :size="24"
          :class="variant === 'danger' ? 'text-error' : 'text-warning'"
        />
        {{ title || "Confirm" }}
      </h3>
      <p class="py-4">{{ message }}</p>
      <div class="modal-action">
        <button class="btn btn-secondary" @click="handleCancel">
          {{ cancelText || "Cancel" }}
        </button>
        <button
          class="btn"
          :class="{
            'btn-error': variant === 'danger',
            'btn-warning': variant === 'warning',
            'btn-primary': !variant || variant === 'info',
          }"
          @click="handleConfirm"
        >
          {{ confirmText || "Confirm" }}
        </button>
      </div>
    </div>
    <form method="dialog" class="modal-backdrop">
      <button @click="handleCancel">close</button>
    </form>
  </dialog>
</template>
