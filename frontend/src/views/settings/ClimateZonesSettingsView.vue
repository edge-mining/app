<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useClimateZoneStore } from "../../core/stores/climateZoneStore";
import { useClimateMonitorStore } from "../../core/stores/climateMonitorStore";
import ClimateZoneCard from "../../components/climateZones/ClimateZoneCard.vue";
import ClimateZoneFormModal from "../../components/climateZones/ClimateZoneFormModal.vue";
import type { ClimateZone, ClimateZoneReading } from "../../core/models/climateZone";
import {
  PhPlus,
  PhThermometerSimple,
} from "@phosphor-icons/vue";

const climateZoneStore = useClimateZoneStore();
const climateMonitorStore = useClimateMonitorStore();

// Modal state
const showModal = ref(false);
const editingZone = ref<ClimateZone | undefined>(undefined);
const isEditMode = ref(false);

// Readings cache
const readings = ref<Record<string, ClimateZoneReading | null>>({});

// Stats
const stats = computed(() => {
  const zones = climateZoneStore.climateZones;
  const totalZones = zones.length;
  const linkedZones = zones.filter((z) => z.climate_monitor_id).length;
  const totalArea = zones.reduce((sum, z) => sum + (z.area_sqm || 0), 0);
  return { totalZones, linkedZones, totalArea };
});

onMounted(async () => {
  await climateZoneStore.loadClimateZones();
  await climateMonitorStore.loadClimateMonitors();
  // Load readings for all zones
  refreshReadings();
});

async function refreshReadings() {
  for (const zone of climateZoneStore.climateZones) {
    if (zone.id && zone.climate_monitor_id) {
      try {
        readings.value[zone.id] = await climateZoneStore.getReading(zone.id);
      } catch {
        readings.value[zone.id] = null;
      }
    }
  }
}

function getLinkedMonitor(zone: ClimateZone) {
  if (!zone.climate_monitor_id) return null;
  return climateMonitorStore.climateMonitors.find((m) => m.id === zone.climate_monitor_id) || null;
}

function openAddModal() {
  editingZone.value = undefined;
  isEditMode.value = false;
  showModal.value = true;
}

function handleEdit(zone: ClimateZone) {
  editingZone.value = { ...zone };
  isEditMode.value = true;
  showModal.value = true;
}

function handleCloseModal() {
  showModal.value = false;
  editingZone.value = undefined;
}

function handleSave(zone: ClimateZone) {
  const monitorId = zone.climate_monitor_id;
  // Remove climate_monitor_id from the payload (handled via link/unlink)
  const { climate_monitor_id, ...zoneData } = zone;

  if (isEditMode.value && zone.id) {
    climateZoneStore
      .updateClimateZone(zone.id.toString(), zoneData)
      .then(async () => {
        // Handle monitor link/unlink
        const originalZone = editingZone.value;
        if (monitorId && monitorId !== originalZone?.climate_monitor_id) {
          await climateZoneStore.linkMonitor(zone.id!, monitorId);
        } else if (!monitorId && originalZone?.climate_monitor_id) {
          await climateZoneStore.unlinkMonitor(zone.id!);
        }
        await climateZoneStore.loadClimateZones();
        refreshReadings();
        handleCloseModal();
      })
      .showToasts(
        "Climate zone updated successfully",
        "Failed to update climate zone"
      );
  } else {
    climateZoneStore
      .addClimateZone(zoneData as ClimateZone)
      .then(async (created: ClimateZone) => {
        if (monitorId && created.id) {
          await climateZoneStore.linkMonitor(created.id, monitorId);
        }
        await climateZoneStore.loadClimateZones();
        refreshReadings();
        handleCloseModal();
      })
      .showToasts(
        "Climate zone created successfully",
        "Failed to create climate zone"
      );
  }
}

function handleDelete(zone: ClimateZone) {
  climateZoneStore
    .deleteClimateZone(zone.id!.toString())
    .then(() => {
      climateZoneStore.loadClimateZones();
    })
    .showToasts(
      "Climate zone deleted successfully",
      "Failed to delete climate zone"
    );
}
</script>

<template>
  <div class="card">
    <div class="card-header">
      <!-- Header with Stats -->
      <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-base-content">Climate Zones</h1>
          <p class="text-sm text-base-content/60 mt-1">
            Define rooms and areas to monitor for heating via miner
          </p>
        </div>

        <button class="btn btn-primary gap-2" @click="openAddModal">
          <PhPlus :size="20" weight="bold" />
          Add Zone
        </button>
      </div>
    </div>
    <div class="card-body">
      <div class="space-y-6">
        <!-- Stats Cards -->
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4">
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0">
            <div class="stat-value text-primary">{{ stats.totalZones }}</div>
            <div class="stat-label">Total Zones</div>
          </div>
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0">
            <div class="stat-value text-success">{{ stats.linkedZones }}</div>
            <div class="stat-label">With Monitor</div>
          </div>
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0">
            <div class="stat-value text-info">{{ stats.totalArea > 0 ? stats.totalArea.toFixed(0) + ' m²' : '-' }}</div>
            <div class="stat-label">Total Area</div>
          </div>
        </div>

        <!-- Cards Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          <ClimateZoneCard
            v-for="zone in climateZoneStore.climateZones"
            :key="zone.id"
            :climate-zone="zone"
            :reading="zone.id ? readings[zone.id] : null"
            :linked-monitor="getLinkedMonitor(zone)"
            @edit="handleEdit"
            @delete="handleDelete"
          />

          <!-- Empty State -->
          <div
            v-if="climateZoneStore.climateZones.length === 0"
            class="col-span-full flex flex-col items-center justify-center py-16 text-center"
          >
            <div
              class="w-20 h-20 rounded-full bg-base-200 flex items-center justify-center mb-4"
            >
              <PhThermometerSimple :size="40" class="text-base-content/30" />
            </div>
            <h3 class="text-lg font-semibold text-base-content/80">
              No climate zones yet
            </h3>
            <p class="text-sm text-base-content/50 mt-1 max-w-sm">
              Add your first climate zone to start monitoring room temperatures.
            </p>
            <button
              class="btn btn-primary btn-sm mt-4 gap-2"
              @click="openAddModal"
            >
              <PhPlus :size="16" />
              Add Zone
            </button>
          </div>
        </div>

        <!-- Form Modal -->
        <ClimateZoneFormModal
          :open="showModal"
          :climate-zone="editingZone"
          :is-edit="isEditMode"
          @close="handleCloseModal"
          @save="handleSave"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.stat-card {
  transition: all 0.2s ease;
}
</style>
