<script setup lang="ts">
import { onMounted } from "vue";
import { useExternalServiceStore } from "../core/stores/externalServiceStore";
import type { ExternalServiceStatusType } from "../core/models/externalService";

const store = useExternalServiceStore();

const badgeClass: Record<ExternalServiceStatusType, string> = {
  connected: "border-success text-success bg-success/10",
  disconnected: "border-error text-error bg-error/10",
  unauthorized: "border-warning text-warning bg-warning/10",
};

const statusClass: Record<ExternalServiceStatusType, string> = {
  connected: "status-success",
  disconnected: "status-error",
  unauthorized: "status-warning",
};

onMounted(async () => {
  if (store.externalServices.length === 0) {
    await store.loadExternalServices();
  }
  store.loadServicesStatus();
});
</script>

<template>
  <footer
    class="h-8 flex-shrink-0 flex items-center justify-end gap-2 px-4 border-t border-base-300/40 bg-base-100 overflow-hidden"
  >
    <template v-if="store.serviceStatuses.size > 0">
      <span
        v-for="[, status] in store.serviceStatuses"
        :key="status.name"
        class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded border text-xs"
        :class="badgeClass[status.status] ?? 'border-base-300 text-base-300'"
        :title="status.error_message ?? status.status"
      >
        <div class="inline-grid *:[grid-area:1/1]">
          <div v-if="status.status === 'connected'" class="status" :class="statusClass[status.status] + ' animate-ping'"></div>
          <div class="status" :class="statusClass[status.status]"></div>
        </div>
        {{ status.name }}
      </span>
    </template>

    <span class="inline-flex items-center px-2 py-0.5 rounded border border-primary/40 text-primary/70 bg-primary/10 text-xs">
      v0.1.0
    </span>
  </footer>
</template>

<style scoped></style>
