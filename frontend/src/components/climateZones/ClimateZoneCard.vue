<script setup lang="ts">
import type { ClimateZone, ClimateZoneReading } from "../../core/models/climateZone";
import type { ClimateMonitor } from "../../core/models/climateMonitor";
import { computed, ref } from "vue";
import {
  PhPencil,
  PhTrash,
  PhThermometerSimple,
  PhDrop,
  PhLink,
  PhLinkBreak,
} from "@phosphor-icons/vue";
import ConfirmDialog from "../ConfirmDialog.vue";
import EdgeMiningCard, { type CardStyleConfig } from "../EdgeMiningCard.vue";
import ResourceId from "../ResourceId.vue";

const props = defineProps<{
  climateZone: ClimateZone;
  reading?: ClimateZoneReading | null;
  linkedMonitor?: ClimateMonitor | null;
}>();

const emit = defineEmits<{
  edit: [zone: ClimateZone];
  delete: [zone: ClimateZone];
}>();

const showDeleteConfirm = ref(false);

const styleConfig = computed<CardStyleConfig>(() => {
  if (props.reading) {
    return {
      gradient: "hover:from-orange-500/20 hover:to-red-500/10",
      iconColor: "text-orange-400",
      badgeClass: "badge-warning",
      accentBorder: "border-l-base-300/50 hover:border-l-orange-500",
    };
  }
  return {
    gradient: "hover:from-slate-500/20 hover:to-gray-500/10",
    iconColor: "text-slate-400",
    badgeClass: "bg-slate-500/20 text-slate-400",
    accentBorder: "border-l-base-300/50 hover:border-l-slate-500",
  };
});

function handleEdit() {
  emit("edit", props.climateZone);
}

function handleDeleteClick() {
  showDeleteConfirm.value = true;
}

function confirmDelete() {
  showDeleteConfirm.value = false;
  emit("delete", props.climateZone);
}

function cancelDelete() {
  showDeleteConfirm.value = false;
}
</script>

<template>
  <EdgeMiningCard
    :icon="PhThermometerSimple"
    :style-config="styleConfig"
    card-class="min-h-[220px]"
  >
    <!-- Title -->
    <template #title>
      {{ climateZone.name }}
    </template>

    <!-- Badges -->
    <template #badges>
      <span v-if="climateZone.area_sqm" class="badge badge-sm badge-ghost px-2">
        {{ climateZone.area_sqm }} m²
      </span>
      <ResourceId v-if="climateZone.id" :id="climateZone.id" />
    </template>

    <!-- Actions -->
    <template #actions>
      <button
        class="btn btn-ghost btn-sm btn-square hover:bg-primary/20"
        title="Edit"
        @click="handleEdit"
      >
        <PhPencil :size="18" class="text-primary" />
      </button>
      <button
        class="btn btn-ghost btn-sm btn-square hover:bg-error/20"
        title="Delete"
        @click="handleDeleteClick"
      >
        <PhTrash :size="18" class="text-error" />
      </button>
    </template>

    <!-- Main Content -->
    <div class="space-y-3">
      <!-- Temperature Reading -->
      <div v-if="reading" class="space-y-2">
        <div class="flex items-center gap-3">
          <PhThermometerSimple :size="20" class="text-orange-400" />
          <span class="text-2xl font-bold text-base-content">
            {{ reading.temperature_celsius.toFixed(1) }}°C
          </span>
          <div v-if="reading.humidity != null" class="flex items-center gap-1 ml-auto">
            <PhDrop :size="16" class="text-sky-400" />
            <span class="text-sm text-base-content/70">{{ reading.humidity.toFixed(0) }}%</span>
          </div>
        </div>
        <div class="text-xs text-base-content/40">
          {{ new Date(reading.timestamp).toLocaleString() }}
        </div>
      </div>

      <div v-else class="text-sm text-base-content/40 italic py-2">
        No reading available
      </div>
    </div>

    <!-- Footer -->
    <template #footer>
      <div class="flex items-center gap-2">
        <template v-if="linkedMonitor">
          <PhLink :size="16" class="text-success" />
          <span class="text-xs text-base-content/60 truncate">{{ linkedMonitor.name }}</span>
        </template>
        <template v-else>
          <PhLinkBreak :size="16" class="text-base-content/30" />
          <span class="text-xs text-base-content/40 italic">No monitor linked</span>
        </template>
      </div>
    </template>
  </EdgeMiningCard>

  <!-- Delete Confirmation -->
  <ConfirmDialog
    :open="showDeleteConfirm"
    title="Delete Climate Zone"
    :message="`Are you sure you want to delete '${climateZone.name}'?`"
    confirm-text="Delete"
    confirm-class="btn-error"
    @confirm="confirmDelete"
    @cancel="cancelDelete"
  />
</template>
