<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useNotifierStore } from "../../core/stores/notifierStore";
import { useExternalServiceStore } from "../../core/stores/externalServiceStore";
import NotifierCard from "../../components/notifiers/NotifierCard.vue";
import NotifierFormModal from "../../components/notifiers/NotifierFormModal.vue";
import type { Notifier, TestNotifierResult } from "../../core/models/notifier";
import { formatType } from "../../core/utils/index";
import {
  PhPlus,
  PhBell,
  PhPlugs,
  PhTelegramLogo,
  PhEnvelope,
  PhWebhooksLogo,
  PhChatDots,
  PhCheckCircle,
  PhXCircle,
  PhX,
} from "@phosphor-icons/vue";

const notifierStore = useNotifierStore();
const externalServiceStore = useExternalServiceStore();

// Modal state
const showModal = ref(false);
const editingNotifier = ref<Notifier | undefined>(undefined);
const isEditMode = ref(false);

// Test result modal state
const showTestModal = ref(false);
const testResult = ref<TestNotifierResult | null>(null);
const testingNotifierName = ref("");
const testLoading = ref(false);

// Filter state
const selectedAdapterFilter = ref<string>("all");

const adapterFilters = computed(() => {
  const types = notifierStore.adapterTypes;
  return [
    { value: "all", label: "All", icon: PhBell, iconColor: "" },
    ...types.map((type) => ({
      value: type,
      label: formatType(type),
      icon: getAdapterIcon(type),
      iconColor: getAdapterIconColor(type),
    })),
  ];
});

const filteredNotifiers = computed(() => {
  if (selectedAdapterFilter.value === "all") {
    return notifierStore.notifiers;
  }
  return notifierStore.notifiers.filter(
    (n) => n.adapter_type === selectedAdapterFilter.value
  );
});

// Stats
const stats = computed(() => {
  const notifiers = notifierStore.notifiers;
  const totalNotifiers = notifiers.length;

  const withExternalService = notifiers.filter(
    (n) => n.external_service_id
  ).length;

  const adapterCounts = notifiers.reduce((acc, n) => {
    acc[n.adapter_type] = (acc[n.adapter_type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return {
    totalNotifiers,
    withExternalService,
    adapterCounts,
  };
});

onMounted(() => {
  notifierStore.loadNotifiers();
  notifierStore.loadAdapterTypes();
  externalServiceStore.loadExternalServices();
});

function getAdapterIcon(type: string) {
  const icons: Record<string, any> = {
    telegram: PhTelegramLogo,
    email: PhEnvelope,
    webhook: PhWebhooksLogo,
    slack: PhChatDots,
  };
  return icons[type] || PhBell;
}

function getAdapterIconColor(type: string): string {
  const colors: Record<string, string> = {
    telegram: "text-sky-400",
    email: "text-rose-400",
    webhook: "text-emerald-400",
    slack: "text-purple-400",
  };
  return colors[type] || "text-amber-400";
}

function openAddModal() {
  editingNotifier.value = undefined;
  isEditMode.value = false;
  showModal.value = true;
}

function handleEdit(notifier: Notifier) {
  editingNotifier.value = {
    ...notifier,
    config: notifier.config ? { ...notifier.config } : {},
    external_service_id: notifier.external_service_id || "",
  };
  isEditMode.value = true;
  showModal.value = true;
}

function handleCloseModal() {
  showModal.value = false;
  editingNotifier.value = undefined;
}

function handleSave(notifier: Notifier) {
  if (isEditMode.value && notifier.id) {
    notifierStore
      .updateNotifier(notifier.id.toString(), notifier)
      .then(() => {
        notifierStore.loadNotifiers();
        handleCloseModal();
      })
      .showToasts(
        "Notifier updated successfully",
        "Failed to update notifier"
      );
  } else {
    notifierStore
      .addNotifier(notifier)
      .then(() => {
        notifierStore.loadNotifiers();
        handleCloseModal();
      })
      .showToasts(
        "Notifier created successfully",
        "Failed to create notifier"
      );
  }
}

function handleDelete(notifier: Notifier) {
  notifierStore
    .deleteNotifier(notifier.id!.toString())
    .then(() => {
      notifierStore.loadNotifiers();
    })
    .showToasts(
      "Notifier deleted successfully",
      "Failed to delete notifier"
    );
}

function handleTest(notifier: Notifier) {
  testingNotifierName.value = notifier.name;
  testLoading.value = true;
  testResult.value = null;
  showTestModal.value = true;

  notifierStore
    .testNotifier(notifier.id!.toString())
    .then((result) => {
      testResult.value = result;
      testLoading.value = false;
    })
    .catch((error) => {
      testResult.value = {
        status: "failed",
        message: error.message || "Test failed",
      };
      testLoading.value = false;
    });
}

function closeTestModal() {
  showTestModal.value = false;
  testResult.value = null;
}

function getFilterCount(adapterType: string): number {
  if (adapterType === "all") return stats.value.totalNotifiers;
  return stats.value.adapterCounts[adapterType] || 0;
}
</script>

<template>
  <div class="card">
    <div class="card-header">
      <!-- Header -->
      <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-base-content">Notifiers</h1>
          <p class="text-sm text-base-content/60 mt-1">
            Manage notification channels and alert delivery
          </p>
        </div>

        <button class="btn btn-primary gap-2" @click="openAddModal">
          <PhPlus :size="20" weight="bold" />
          Add Notifier
        </button>
      </div>
    </div>
    <div class="card-body">
      <div class="space-y-6">
        <!-- Stats Cards -->
        <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3 sm:gap-4">
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0">
            <div class="stat-value text-primary">{{ stats.totalNotifiers }}</div>
            <div class="stat-label">Total Notifiers</div>
          </div>
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0">
            <div class="stat-value text-info flex items-center gap-2">
              {{ stats.withExternalService }}
              <PhPlugs :size="20" class="opacity-60" />
            </div>
            <div class="stat-label">With External Service</div>
          </div>
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0 overflow-hidden">
            <div class="flex flex-wrap gap-2 sm:gap-3 items-center min-h-[2rem] sm:min-h-[2.25rem]">
              <div
                v-for="(count, adapterType) in stats.adapterCounts"
                :key="adapterType"
                class="flex items-center gap-0.5 sm:gap-1"
              >
                <component :is="getAdapterIcon(String(adapterType))" :size="18" :class="[getAdapterIconColor(String(adapterType)), 'flex-shrink-0 sm:w-6 sm:h-6']" />
                <span class="stat-type-count">{{ count }}</span>
              </div>
              <div v-if="Object.keys(stats.adapterCounts).length === 0" class="text-base-content/40">
                -
              </div>
            </div>
            <div class="stat-label">By Adapter</div>
          </div>
        </div>

        <!-- Filter Tabs -->
        <div class="flex gap-2 flex-wrap">
          <button
            v-for="filter in adapterFilters"
            :key="filter.value"
            class="btn btn-sm gap-2 transition-all"
            :class="[
              selectedAdapterFilter === filter.value
                ? 'btn-primary'
                : 'btn-ghost opacity-70 hover:opacity-100',
            ]"
            @click="selectedAdapterFilter = filter.value"
          >
            <component :is="filter.icon" :size="16" />
            {{ filter.label }}
            <span
              v-if="getFilterCount(filter.value) > 0"
              class="badge badge-sm"
              :class="selectedAdapterFilter === filter.value ? 'bg-white/20 text-neutral-900' : 'badge-neutral'"
            >
              {{ getFilterCount(filter.value) }}
            </span>
          </button>
        </div>

        <!-- Cards Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          <NotifierCard
            v-for="notifier in filteredNotifiers"
            :key="notifier.id"
            :notifier="notifier"
            @edit="handleEdit"
            @delete="handleDelete"
            @test="handleTest"
          />

          <!-- Empty State -->
          <div
            v-if="filteredNotifiers.length === 0"
            class="col-span-full flex flex-col items-center justify-center py-16 text-center"
          >
            <div
              class="w-20 h-20 rounded-full bg-base-200 flex items-center justify-center mb-4"
            >
              <PhBell :size="40" class="text-base-content/30" />
            </div>
            <h3 class="text-lg font-semibold text-base-content/80">
              {{ selectedAdapterFilter === "all" ? "No notifiers yet" : "No notifiers of this type" }}
            </h3>
            <p class="text-sm text-base-content/50 mt-1 max-w-sm">
              {{
                selectedAdapterFilter === "all"
                  ? "Add your first notifier to start receiving alerts and notifications."
                  : "Try selecting a different filter or add a new notifier."
              }}
            </p>
            <button
              v-if="selectedAdapterFilter === 'all'"
              class="btn btn-primary btn-sm mt-4 gap-2"
              @click="openAddModal"
            >
              <PhPlus :size="16" />
              Add Notifier
            </button>
          </div>
        </div>

        <!-- Form Modal -->
        <NotifierFormModal
          :open="showModal"
          :notifier="editingNotifier"
          :is-edit="isEditMode"
          @close="handleCloseModal"
          @save="handleSave"
        />

        <!-- Test Result Modal -->
        <dialog class="modal" :class="{ 'modal-open': showTestModal }">
          <div class="modal-box bg-base-100 border border-base-300/60">
            <!-- Header -->
            <div class="flex items-center justify-between mb-6">
              <div class="flex items-center gap-3">
                <div class="h-10 w-10 rounded-xl bg-base-200/60 flex items-center justify-center">
                  <PhBell :size="22" class="text-amber-400" />
                </div>
                <div>
                  <h3 class="text-lg font-bold">Test Notification</h3>
                  <p class="text-sm text-base-content/60">{{ testingNotifierName }}</p>
                </div>
              </div>
              <button class="btn btn-ghost btn-sm btn-square" @click="closeTestModal">
                <PhX :size="20" />
              </button>
            </div>

            <!-- Loading State -->
            <div v-if="testLoading" class="flex flex-col items-center gap-4 py-10">
              <span class="loading loading-spinner loading-lg text-primary"></span>
              <p class="text-base-content/60">Sending test notification...</p>
            </div>

            <!-- Result -->
            <div v-else-if="testResult" class="space-y-4">
              <!-- Success -->
              <div
                v-if="testResult.status === 'success'"
                class="flex flex-col items-center gap-3 py-6"
              >
                <div class="w-16 h-16 rounded-full bg-success/20 flex items-center justify-center">
                  <PhCheckCircle :size="36" class="text-success" />
                </div>
                <p class="text-lg font-semibold text-success">Test Passed</p>
                <p v-if="testResult.message" class="text-sm text-base-content/60 text-center max-w-sm">
                  {{ testResult.message }}
                </p>
              </div>

              <!-- Failure -->
              <div v-else class="flex flex-col items-center gap-3 py-6">
                <div class="w-16 h-16 rounded-full bg-error/20 flex items-center justify-center">
                  <PhXCircle :size="36" class="text-error" />
                </div>
                <p class="text-lg font-semibold text-error">Test Failed</p>
                <p v-if="testResult.message" class="text-sm text-base-content/60 text-center max-w-sm">
                  {{ testResult.message }}
                </p>
              </div>
            </div>

            <!-- Close Button -->
            <div v-if="!testLoading" class="flex justify-end pt-4 border-t border-base-300/40 mt-4">
              <button class="btn btn-primary btn-sm" @click="closeTestModal">Close</button>
            </div>
          </div>
          <form method="dialog" class="modal-backdrop bg-black/50">
            <button @click="closeTestModal">close</button>
          </form>
        </dialog>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stat-card {
  transition: all 0.2s ease;
}

.stat-card:hover {
  border-color: oklch(50% 0 0 / 0.5);
}

.stat-value {
  font-weight: 700;
  font-size: clamp(1.25rem, 4vw, 1.875rem);
  line-height: 1.2;
}

.stat-label {
  font-size: clamp(0.7rem, 2vw, 0.875rem);
  color: oklch(80% 0 0 / 0.6);
  margin-top: 0.125rem;
}
</style>
