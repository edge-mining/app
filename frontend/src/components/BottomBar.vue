<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount, ref, nextTick } from "vue";
import { useRouter } from "vue-router";
import { useExternalServiceStore } from "../core/stores/externalServiceStore";
import { useAppStore } from "../core/stores/appStore";
import type { ExternalServiceStatusType } from "../core/models/externalService";
import { PhHouse, PhArrowRight } from "@phosphor-icons/vue";

type IndicatorStatus = ExternalServiceStatusType | "not_configured" | "unknown";

const store = useExternalServiceStore();
const appStore = useAppStore();
const router = useRouter();

const HA_ADAPTER_PREFIX = "home_assistant";

const badgeClass: Record<IndicatorStatus, string> = {
  connected: "border-success text-success bg-success/10",
  disconnected: "border-error text-error bg-error/10",
  unauthorized: "border-warning text-warning bg-warning/10",
  not_configured: "border-error text-error bg-error/10",
  unknown: "border-error text-error bg-error/10",
};

const statusClass: Record<IndicatorStatus, string> = {
  connected: "status-success",
  disconnected: "status-error",
  unauthorized: "status-warning",
  not_configured: "status-error",
  unknown: "status-error",
};

const statusLabel: Record<IndicatorStatus, string> = {
  connected: "Connected",
  disconnected: "Disconnected",
  unauthorized: "Unauthorized",
  not_configured: "Not configured",
  unknown: "Unknown",
};

// Home Assistant services (api and/or mqtt adapters)
const haServices = computed(() =>
  store.externalServices.filter((s) => s.adapter_type.startsWith(HA_ADAPTER_PREFIX))
);

interface HaServiceStatus {
  name: string;
  adapter_type: string;
  status: IndicatorStatus;
  error_message?: string;
}

// Aggregated HA indicator: always present, even when HA is not configured.
const haIndicator = computed<{ status: IndicatorStatus; services: HaServiceStatus[] }>(() => {
  const services: HaServiceStatus[] = haServices.value.map((s) => {
    const st = s.id ? store.serviceStatuses.get(String(s.id)) : undefined;
    return {
      name: s.name,
      adapter_type: s.adapter_type,
      status: st?.status ?? "unknown",
      error_message: st?.error_message,
    };
  });

  let status: IndicatorStatus;
  if (services.length === 0) {
    status = "not_configured";
  } else if (services.every((s) => s.status === "connected")) {
    status = "connected";
  } else if (services.some((s) => s.status === "unauthorized")) {
    status = "unauthorized";
  } else {
    status = "disconnected";
  }

  return { status, services };
});

// Non-HA service badges (kept as before).
const otherStatuses = computed(() => {
  const haIds = new Set(haServices.value.map((s) => String(s.id)));
  return [...store.serviceStatuses.entries()]
    .filter(([id]) => !haIds.has(id))
    .map(([, status]) => status);
});

// --- Popover (teleported to body so the bottom bar's overflow does not clip it) ---
const showPopover = ref(false);
const triggerRef = ref<HTMLElement | null>(null);
const popoverRef = ref<HTMLElement | null>(null);
const popoverStyle = ref<Record<string, string>>({});

function positionPopover() {
  const el = triggerRef.value;
  if (!el) return;
  const rect = el.getBoundingClientRect();
  popoverStyle.value = {
    position: "fixed",
    bottom: `${window.innerHeight - rect.top + 8}px`,
    right: `${Math.max(window.innerWidth - rect.right, 8)}px`,
  };
}

async function togglePopover() {
  if (showPopover.value) {
    showPopover.value = false;
    return;
  }
  positionPopover();
  showPopover.value = true;
  await nextTick();
  positionPopover();
}

function handleOutside(event: MouseEvent) {
  if (!showPopover.value) return;
  const target = event.target as Node;
  if (triggerRef.value?.contains(target) || popoverRef.value?.contains(target)) return;
  showPopover.value = false;
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === "Escape") showPopover.value = false;
}

function openHaSettings() {
  showPopover.value = false;
  const adapter = haServices.value[0]?.adapter_type;
  router.push({
    name: "settings.externalServices",
    query: adapter ? { adapter } : {},
  });
}

onMounted(async () => {
  document.addEventListener("click", handleOutside, true);
  document.addEventListener("keydown", handleKeydown);
  window.addEventListener("resize", positionPopover);

  if (store.externalServices.length === 0) {
    await store.loadExternalServices();
  }
  store.loadServicesStatus();

  if (!appStore.version) {
    appStore.fetchVersion();
  }
});

onBeforeUnmount(() => {
  document.removeEventListener("click", handleOutside, true);
  document.removeEventListener("keydown", handleKeydown);
  window.removeEventListener("resize", positionPopover);
});
</script>

<template>
  <footer
    class="h-8 flex-shrink-0 flex items-center justify-end gap-2 px-4 border-t border-base-300/40 bg-base-100 overflow-hidden"
  >
    <!-- Other external service statuses -->
    <span
      v-for="status in otherStatuses"
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

    <!-- Home Assistant connection indicator (always visible) -->
    <button
      ref="triggerRef"
      type="button"
      class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded border text-xs cursor-pointer"
      :class="badgeClass[haIndicator.status]"
      :title="`Home Assistant: ${statusLabel[haIndicator.status]}`"
      @click="togglePopover"
    >
      <div class="inline-grid *:[grid-area:1/1]">
        <div v-if="haIndicator.status === 'connected'" class="status" :class="statusClass[haIndicator.status] + ' animate-ping'"></div>
        <div class="status" :class="statusClass[haIndicator.status]"></div>
      </div>
      <PhHouse :size="14" weight="bold" />
      Home Assistant
    </button>

    <span
      class="inline-flex items-center px-2 py-0.5 rounded border border-primary/40 text-primary/70 bg-primary/10 text-xs"
    >
      <template v-if="appStore.versionLoading">...</template>
      <template v-else-if="appStore.version">v{{ appStore.version }}</template>
      <template v-else>v?</template>
    </span>
  </footer>

  <!-- Teleported popover -->
  <Teleport to="body">
    <Transition name="popover-fade">
      <div
        v-if="showPopover"
        ref="popoverRef"
        class="z-[100] w-72 rounded-box border border-base-300/40 bg-base-200 shadow-lg p-3"
        :style="popoverStyle"
      >
        <div class="flex items-center gap-2 mb-2">
          <PhHouse :size="16" weight="bold" class="text-sky-400" />
          <span class="text-sm font-semibold">Home Assistant</span>
        </div>

        <p v-if="haIndicator.status === 'not_configured'" class="text-xs text-base-content/60 mb-3">
          No Home Assistant service is configured yet.
        </p>

        <ul v-else class="space-y-2 mb-3">
          <li
            v-for="svc in haIndicator.services"
            :key="svc.name"
            class="flex items-start gap-2 text-xs"
          >
            <div class="inline-grid *:[grid-area:1/1] mt-0.5">
              <div class="status" :class="statusClass[svc.status]"></div>
            </div>
            <div class="min-w-0">
              <div class="font-medium truncate">{{ svc.name }}</div>
              <div class="text-base-content/60">{{ statusLabel[svc.status] }}</div>
              <div v-if="svc.error_message" class="text-error/80 break-words">{{ svc.error_message }}</div>
            </div>
          </li>
        </ul>

        <button class="btn btn-primary btn-sm w-full gap-2" @click="openHaSettings">
          Open Home Assistant settings
          <PhArrowRight :size="14" weight="bold" />
        </button>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.popover-fade-enter-active,
.popover-fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.popover-fade-enter-from,
.popover-fade-leave-to {
  opacity: 0;
  transform: translateY(4px);
}
</style>
