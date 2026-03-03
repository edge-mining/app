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
  <dialog :class="['modal', { 'modal-open': props.open }]">
    <div class="modal-box">
      <h3 class="font-bold text-lg flex items-center gap-2">
        <PhWarning
          v-if="props.variant === 'danger' || props.variant === 'warning'"
          :size="24"
          :class="props.variant === 'danger' ? 'text-error' : 'text-warning'"
        />
        {{ props.title || "Confirm" }}
      </h3>
      <p class="py-4">{{ props.message }}</p>
      <div class="modal-action">
        <button class="btn btn-secondary" @click="handleCancel">
          {{ props.cancelText || "Cancel" }}
        </button>
        <button
          class="btn"
          :class="{
            'btn-error': props.variant === 'danger',
            'btn-warning': props.variant === 'warning',
            'btn-primary': !props.variant || props.variant === 'info',
          }"
          @click="handleConfirm"
        >
          {{ props.confirmText || "Confirm" }}
        </button>
      </div>
    </div>
    <form method="dialog" class="modal-backdrop">
      <button @click="handleCancel">close</button>
    </form>
  </dialog>
</template>
