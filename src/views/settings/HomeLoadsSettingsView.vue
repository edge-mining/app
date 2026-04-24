<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useHomeLoadsProfileStore } from "../../core/stores/homeLoadsProfileStore";
import { useEnergyLoadForecastProviderStore } from "../../core/stores/energyLoadForecastProviderStore";
import { useEnergyLoadHistoryProviderStore } from "../../core/stores/energyLoadHistoryProviderStore";
import { useLoadTrainingStore } from "../../core/stores/loadTrainingStore";
import { useExternalServiceStore } from "../../core/stores/externalServiceStore";
import type { LoadDevice } from "../../core/models/homeLoadsProfile";
import type { EnergyLoadForecastProvider } from "../../core/models/energyLoadForecastProvider";
import type { EnergyLoadHistoryProvider } from "../../core/models/energyLoadHistoryProvider";
import LoadDeviceCard from "../../components/homeLoads/LoadDeviceCard.vue";
import LoadDeviceFormModal from "../../components/homeLoads/LoadDeviceFormModal.vue";
import LoadDeviceHistoryModal from "../../components/homeLoads/LoadDeviceHistoryModal.vue";
import EnergyLoadForecastProviderCard from "../../components/homeLoads/EnergyLoadForecastProviderCard.vue";
import EnergyLoadForecastProviderFormModal from "../../components/homeLoads/EnergyLoadForecastProviderFormModal.vue";
import EnergyLoadHistoryProviderCard from "../../components/homeLoads/EnergyLoadHistoryProviderCard.vue";
import EnergyLoadHistoryProviderFormModal from "../../components/homeLoads/EnergyLoadHistoryProviderFormModal.vue";
import TrainingPanel from "../../components/homeLoads/TrainingPanel.vue";
import {
  PhPlus,
  PhPlug,
  PhBrain,
  PhChartLine,
  PhHouse,
  PhPencil,
  PhTrash,
  PhCheck,
  PhX,
} from "@phosphor-icons/vue";

const profileStore = useHomeLoadsProfileStore();
const forecastProviderStore = useEnergyLoadForecastProviderStore();
const historyProviderStore = useEnergyLoadHistoryProviderStore();
const trainingStore = useLoadTrainingStore();
const externalServiceStore = useExternalServiceStore();

// Tab management
type Tab = "devices" | "forecast" | "history" | "training";
const activeTab = ref<Tab>("devices");

const tabs: { value: Tab; label: string; icon: typeof PhPlug }[] = [
  { value: "devices", label: "Devices", icon: PhPlug },
  { value: "forecast", label: "Forecast Providers", icon: PhBrain },
  { value: "history", label: "History Providers", icon: PhChartLine },
  { value: "training", label: "Training", icon: PhBrain },
];

// Profile management
const showNewProfileInput = ref(false);
const newProfileName = ref("");
const editingProfileId = ref<string | null>(null);
const editProfileName = ref("");

// Device modal state
const showDeviceModal = ref(false);
const editingDevice = ref<LoadDevice | undefined>(undefined);
const isDeviceEditMode = ref(false);

// Device history modal state
const showHistoryModal = ref(false);
const historyDevice = ref<LoadDevice | undefined>(undefined);

// Forecast provider modal state
const showForecastModal = ref(false);
const editingForecastProvider = ref<EnergyLoadForecastProvider | undefined>(undefined);
const isForecastEditMode = ref(false);

// History provider modal state
const showHistoryProviderModal = ref(false);
const editingHistoryProvider = ref<EnergyLoadHistoryProvider | undefined>(undefined);
const isHistoryProviderEditMode = ref(false);

// Computed
const selectedProfile = computed(() => {
  return profileStore.profiles.find((p) => p.id === profileStore.selectedProfileId);
});

const devices = computed(() => selectedProfile.value?.devices ?? []);

onMounted(() => {
  profileStore.loadProfiles();
  forecastProviderStore.loadProviders();
  forecastProviderStore.loadAdapterTypes();
  historyProviderStore.loadProviders();
  historyProviderStore.loadAdapterTypes();
  trainingStore.loadModels();
  externalServiceStore.loadExternalServices();
});

// ── Profile CRUD ──────────────────────────────
function selectProfile(profileId: string) {
  profileStore.selectedProfileId = profileId;
}

function startAddProfile() {
  newProfileName.value = "";
  showNewProfileInput.value = true;
}

function cancelAddProfile() {
  showNewProfileInput.value = false;
  newProfileName.value = "";
}

function confirmAddProfile() {
  const name = newProfileName.value.trim();
  if (!name) return;
  profileStore
    .addProfile(name)
    .then(() => {
      profileStore.loadProfiles();
      showNewProfileInput.value = false;
      newProfileName.value = "";
    })
    .showToasts("Profile created successfully", "Failed to create profile");
}

function startEditProfile(profile: { id?: string; name: string }) {
  editingProfileId.value = profile.id ?? null;
  editProfileName.value = profile.name;
}

function cancelEditProfile() {
  editingProfileId.value = null;
  editProfileName.value = "";
}

function confirmEditProfile() {
  if (!editingProfileId.value || !editProfileName.value.trim()) return;
  profileStore
    .updateProfile(editingProfileId.value, editProfileName.value.trim())
    .then(() => {
      profileStore.loadProfiles();
      editingProfileId.value = null;
    })
    .showToasts("Profile updated successfully", "Failed to update profile");
}

function deleteProfile(profileId: string) {
  profileStore
    .deleteProfile(profileId)
    .then(() => {
      if (profileStore.selectedProfileId === profileId) {
        profileStore.selectedProfileId = null;
      }
      profileStore.loadProfiles();
    })
    .showToasts("Profile deleted successfully", "Failed to delete profile");
}

// ── Device CRUD ──────────────────────────────
function openAddDevice() {
  editingDevice.value = undefined;
  isDeviceEditMode.value = false;
  showDeviceModal.value = true;
}

function handleEditDevice(device: LoadDevice) {
  editingDevice.value = { ...device };
  isDeviceEditMode.value = true;
  showDeviceModal.value = true;
}

function handleCloseDeviceModal() {
  showDeviceModal.value = false;
  editingDevice.value = undefined;
}

function handleSaveDevice(device: LoadDevice) {
  const pid = profileStore.selectedProfileId;
  if (!pid) return;

  if (isDeviceEditMode.value && device.id) {
    profileStore
      .updateDevice(pid, device.id, device)
      .then(() => {
        profileStore.loadProfiles();
        handleCloseDeviceModal();
      })
      .showToasts("Device updated successfully", "Failed to update device");
  } else {
    profileStore
      .addDevice(pid, device)
      .then(() => {
        profileStore.loadProfiles();
        handleCloseDeviceModal();
      })
      .showToasts("Device created successfully", "Failed to create device");
  }
}

function handleDeleteDevice(device: LoadDevice) {
  const pid = profileStore.selectedProfileId;
  if (!pid || !device.id) return;
  profileStore
    .deleteDevice(pid, device.id)
    .then(() => profileStore.loadProfiles())
    .showToasts("Device deleted successfully", "Failed to delete device");
}

function handleViewHistory(device: LoadDevice) {
  historyDevice.value = device;
  showHistoryModal.value = true;
}

function handleCloseHistory() {
  showHistoryModal.value = false;
  historyDevice.value = undefined;
}

function handleTrainDevice(device: LoadDevice) {
  const pid = profileStore.selectedProfileId;
  if (!pid || !device.id) return;
  trainingStore
    .triggerTrainingDevice(pid, device.id)
    .then(() => trainingStore.loadModels())
    .showToasts("Training started for " + device.name, "Failed to start training");
}

// ── Forecast Provider CRUD ──────────────────────────────
function openAddForecast() {
  editingForecastProvider.value = undefined;
  isForecastEditMode.value = false;
  showForecastModal.value = true;
}

function handleEditForecast(provider: EnergyLoadForecastProvider) {
  editingForecastProvider.value = { ...provider };
  isForecastEditMode.value = true;
  showForecastModal.value = true;
}

function handleCloseForecastModal() {
  showForecastModal.value = false;
  editingForecastProvider.value = undefined;
}

function handleSaveForecast(provider: EnergyLoadForecastProvider) {
  if (isForecastEditMode.value && provider.id) {
    forecastProviderStore
      .updateProvider(provider.id, provider)
      .then(() => {
        forecastProviderStore.loadProviders();
        handleCloseForecastModal();
      })
      .showToasts("Forecast provider updated", "Failed to update forecast provider");
  } else {
    forecastProviderStore
      .addProvider(provider)
      .then(() => {
        forecastProviderStore.loadProviders();
        handleCloseForecastModal();
      })
      .showToasts("Forecast provider created", "Failed to create forecast provider");
  }
}

function handleDeleteForecast(provider: EnergyLoadForecastProvider) {
  if (!provider.id) return;
  forecastProviderStore
    .deleteProvider(provider.id)
    .then(() => forecastProviderStore.loadProviders())
    .showToasts("Forecast provider deleted", "Failed to delete forecast provider");
}

// ── History Provider CRUD ──────────────────────────────
function openAddHistory() {
  editingHistoryProvider.value = undefined;
  isHistoryProviderEditMode.value = false;
  showHistoryProviderModal.value = true;
}

function handleEditHistory(provider: EnergyLoadHistoryProvider) {
  editingHistoryProvider.value = { ...provider };
  isHistoryProviderEditMode.value = true;
  showHistoryProviderModal.value = true;
}

function handleCloseHistoryModal() {
  showHistoryProviderModal.value = false;
  editingHistoryProvider.value = undefined;
}

function handleSaveHistory(provider: EnergyLoadHistoryProvider) {
  if (isHistoryProviderEditMode.value && provider.id) {
    historyProviderStore
      .updateProvider(provider.id, provider)
      .then(() => {
        historyProviderStore.loadProviders();
        handleCloseHistoryModal();
      })
      .showToasts("History provider updated", "Failed to update history provider");
  } else {
    historyProviderStore
      .addProvider(provider)
      .then(() => {
        historyProviderStore.loadProviders();
        handleCloseHistoryModal();
      })
      .showToasts("History provider created", "Failed to create history provider");
  }
}

function handleDeleteHistory(provider: EnergyLoadHistoryProvider) {
  if (!provider.id) return;
  historyProviderStore
    .deleteProvider(provider.id)
    .then(() => historyProviderStore.loadProviders())
    .showToasts("History provider deleted", "Failed to delete history provider");
}

// ── Training ──────────────────────────────
function handleTrainAll() {
  trainingStore
    .triggerTrainingAll()
    .then(() => trainingStore.loadModels())
    .showToasts("Training triggered for all devices", "Failed to trigger training");
}

function handleTrainSingleDevice(deviceId: string) {
  const pid = profileStore.selectedProfileId;
  if (!pid) return;
  trainingStore
    .triggerTrainingDevice(pid, deviceId)
    .then(() => trainingStore.loadModels())
    .showToasts("Training started", "Failed to start training");
}
</script>

<template>
  <div class="card">
    <div class="card-header">
      <!-- Header -->
      <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <PhHouse :size="28" class="text-primary" />
          <div>
            <h1 class="text-2xl font-bold text-base-content">Home Loads</h1>
            <p class="text-sm text-base-content/60 mt-0.5">
              Configure domestic load profiles, devices, and forecast providers
            </p>
          </div>
        </div>
      </div>
    </div>
    <div class="card-body">
      <div class="space-y-6">
        <!-- Profile Selector -->
        <div class="bg-base-200/40 rounded-xl border border-base-300/40 p-4">
          <div class="flex items-center justify-between mb-3">
            <span class="text-sm font-semibold text-base-content/70 uppercase tracking-wider">
              Load Profile
            </span>
            <button
              v-if="!showNewProfileInput"
              class="btn btn-ghost btn-xs gap-1"
              @click="startAddProfile"
            >
              <PhPlus :size="14" />
              New Profile
            </button>
          </div>

          <!-- New Profile Input -->
          <div v-if="showNewProfileInput" class="flex items-center gap-2 mb-3">
            <input
              v-model="newProfileName"
              type="text"
              placeholder="Profile name"
              class="input input-bordered input-sm flex-1"
              @keyup.enter="confirmAddProfile"
              @keyup.escape="cancelAddProfile"
            />
            <button class="btn btn-primary btn-sm btn-square" @click="confirmAddProfile">
              <PhCheck :size="16" />
            </button>
            <button class="btn btn-ghost btn-sm btn-square" @click="cancelAddProfile">
              <PhX :size="16" />
            </button>
          </div>

          <!-- Profile Tabs -->
          <div class="flex flex-wrap gap-2">
            <template v-for="profile in profileStore.profiles" :key="profile.id">
              <div
                v-if="editingProfileId === profile.id"
                class="flex items-center gap-1"
              >
                <input
                  v-model="editProfileName"
                  type="text"
                  class="input input-bordered input-sm w-36"
                  @keyup.enter="confirmEditProfile"
                  @keyup.escape="cancelEditProfile"
                />
                <button class="btn btn-success btn-sm btn-square" @click="confirmEditProfile">
                  <PhCheck :size="14" />
                </button>
                <button class="btn btn-ghost btn-sm btn-square" @click="cancelEditProfile">
                  <PhX :size="14" />
                </button>
              </div>
              <div v-else class="btn-group">
                <button
                  class="btn btn-sm"
                  :class="profileStore.selectedProfileId === profile.id ? 'btn-primary' : 'btn-ghost'"
                  @click="selectProfile(profile.id!)"
                >
                  {{ profile.name }}
                  <span class="badge badge-xs ml-1 opacity-70">{{ profile.devices.length }}</span>
                </button>
                <button
                  v-if="profileStore.selectedProfileId === profile.id"
                  class="btn btn-sm btn-ghost btn-square"
                  title="Rename"
                  @click.stop="startEditProfile(profile)"
                >
                  <PhPencil :size="14" />
                </button>
                <button
                  v-if="profileStore.selectedProfileId === profile.id"
                  class="btn btn-sm btn-ghost btn-square"
                  title="Delete"
                  @click.stop="deleteProfile(profile.id!)"
                >
                  <PhTrash :size="14" class="text-error" />
                </button>
              </div>
            </template>

            <div
              v-if="profileStore.profiles.length === 0 && !showNewProfileInput"
              class="text-sm text-base-content/50 italic py-1"
            >
              No profiles yet — create one to start adding devices
            </div>
          </div>
        </div>

        <!-- Tab Bar -->
        <div v-if="selectedProfile" class="flex gap-2 flex-wrap border-b border-base-300/40 pb-2">
          <button
            v-for="tab in tabs"
            :key="tab.value"
            class="btn btn-sm gap-2 transition-all"
            :class="activeTab === tab.value ? 'btn-primary' : 'btn-ghost opacity-70 hover:opacity-100'"
            @click="activeTab = tab.value"
          >
            <component :is="tab.icon" :size="16" />
            {{ tab.label }}
          </button>
        </div>

        <!-- Tab Content -->
        <template v-if="selectedProfile">
          <!-- DEVICES TAB -->
          <div v-if="activeTab === 'devices'" class="space-y-4">
            <div class="flex justify-end">
              <button class="btn btn-primary gap-2" @click="openAddDevice">
                <PhPlus :size="20" weight="bold" />
                Add Device
              </button>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              <LoadDeviceCard
                v-for="device in devices"
                :key="device.id"
                :device="device"
                :forecast-providers="forecastProviderStore.providers"
                :history-providers="historyProviderStore.providers"
                @edit="handleEditDevice"
                @delete="handleDeleteDevice"
                @view-history="handleViewHistory"
                @train="handleTrainDevice"
              />
            </div>

            <div
              v-if="devices.length === 0"
              class="flex flex-col items-center justify-center py-16 text-center"
            >
              <div class="w-20 h-20 rounded-full bg-base-200 flex items-center justify-center mb-4">
                <PhPlug :size="40" class="text-base-content/30" />
              </div>
              <h3 class="text-lg font-semibold text-base-content/80">No devices yet</h3>
              <p class="text-sm text-base-content/50 mt-1 max-w-sm">
                Add your first device to this load profile.
              </p>
              <button class="btn btn-primary btn-sm mt-4 gap-2" @click="openAddDevice">
                <PhPlus :size="16" />
                Add Device
              </button>
            </div>
          </div>

          <!-- FORECAST PROVIDERS TAB -->
          <div v-if="activeTab === 'forecast'" class="space-y-4">
            <div class="flex justify-end">
              <button class="btn btn-primary gap-2" @click="openAddForecast">
                <PhPlus :size="20" weight="bold" />
                Add Forecast Provider
              </button>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              <EnergyLoadForecastProviderCard
                v-for="provider in forecastProviderStore.providers"
                :key="provider.id"
                :provider="provider"
                :all-devices="devices"
                @edit="handleEditForecast"
                @delete="handleDeleteForecast"
              />
            </div>

            <div
              v-if="forecastProviderStore.providers.length === 0"
              class="flex flex-col items-center justify-center py-16 text-center"
            >
              <div class="w-20 h-20 rounded-full bg-base-200 flex items-center justify-center mb-4">
                <PhBrain :size="40" class="text-base-content/30" />
              </div>
              <h3 class="text-lg font-semibold text-base-content/80">No forecast providers</h3>
              <p class="text-sm text-base-content/50 mt-1 max-w-sm">
                Add a forecast provider to enable energy load predictions for your devices.
              </p>
              <button class="btn btn-primary btn-sm mt-4 gap-2" @click="openAddForecast">
                <PhPlus :size="16" />
                Add Forecast Provider
              </button>
            </div>
          </div>

          <!-- HISTORY PROVIDERS TAB -->
          <div v-if="activeTab === 'history'" class="space-y-4">
            <div class="flex justify-end">
              <button class="btn btn-primary gap-2" @click="openAddHistory">
                <PhPlus :size="20" weight="bold" />
                Add History Provider
              </button>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              <EnergyLoadHistoryProviderCard
                v-for="provider in historyProviderStore.providers"
                :key="provider.id"
                :provider="provider"
                :all-devices="devices"
                @edit="handleEditHistory"
                @delete="handleDeleteHistory"
              />
            </div>

            <div
              v-if="historyProviderStore.providers.length === 0"
              class="flex flex-col items-center justify-center py-16 text-center"
            >
              <div class="w-20 h-20 rounded-full bg-base-200 flex items-center justify-center mb-4">
                <PhChartLine :size="40" class="text-base-content/30" />
              </div>
              <h3 class="text-lg font-semibold text-base-content/80">No history providers</h3>
              <p class="text-sm text-base-content/50 mt-1 max-w-sm">
                Add a history provider to track energy consumption data from your devices.
              </p>
              <button class="btn btn-primary btn-sm mt-4 gap-2" @click="openAddHistory">
                <PhPlus :size="16" />
                Add History Provider
              </button>
            </div>
          </div>

          <!-- TRAINING TAB -->
          <div v-if="activeTab === 'training'">
            <TrainingPanel
              :profile-id="profileStore.selectedProfileId ?? undefined"
              :devices="devices"
              @train-all="handleTrainAll"
              @train-device="handleTrainSingleDevice"
            />
          </div>
        </template>

        <!-- No Profile Selected State -->
        <div
          v-if="profileStore.profiles.length > 0 && !selectedProfile"
          class="flex flex-col items-center justify-center py-16 text-center"
        >
          <PhHouse :size="48" class="text-base-content/30 mb-4" />
          <h3 class="text-lg font-semibold text-base-content/80">Select a profile</h3>
          <p class="text-sm text-base-content/50 mt-1">
            Choose a load profile above to manage its devices and providers.
          </p>
        </div>
      </div>
    </div>
  </div>

  <!-- Modals -->
  <LoadDeviceFormModal
    :open="showDeviceModal"
    :device="editingDevice"
    :is-edit="isDeviceEditMode"
    :forecast-providers="forecastProviderStore.providers"
    :history-providers="historyProviderStore.providers"
    @close="handleCloseDeviceModal"
    @save="handleSaveDevice"
  />

  <LoadDeviceHistoryModal
    :open="showHistoryModal"
    :device="historyDevice"
    :profile-id="profileStore.selectedProfileId ?? undefined"
    @close="handleCloseHistory"
  />

  <EnergyLoadForecastProviderFormModal
    :open="showForecastModal"
    :provider="editingForecastProvider"
    :is-edit="isForecastEditMode"
    @close="handleCloseForecastModal"
    @save="handleSaveForecast"
  />

  <EnergyLoadHistoryProviderFormModal
    :open="showHistoryProviderModal"
    :provider="editingHistoryProvider"
    :is-edit="isHistoryProviderEditMode"
    @close="handleCloseHistoryModal"
    @save="handleSaveHistory"
  />
</template>

<style scoped>
.stat-card {
  transition: all 0.2s ease;
}
.stat-card:hover {
  border-color: oklch(50% 0 0 / 0.5);
}
</style>
