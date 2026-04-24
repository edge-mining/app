<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useHomeLoadsProfileStore } from "../../core/stores/homeLoadsProfileStore";
import { useEnergyLoadForecastProviderStore } from "../../core/stores/energyLoadForecastProviderStore";
import { useEnergyLoadHistoryProviderStore } from "../../core/stores/energyLoadHistoryProviderStore";
import { useExternalServiceStore } from "../../core/stores/externalServiceStore";
import type { LoadDevice } from "../../core/models/homeLoadsProfile";
import type { EnergyLoadForecastProvider } from "../../core/models/energyLoadForecastProvider";
import type { EnergyLoadHistoryProvider } from "../../core/models/energyLoadHistoryProvider";
import LoadDeviceTable from "../../components/homeLoads/LoadDeviceTable.vue";
import LoadDeviceFormModal from "../../components/homeLoads/LoadDeviceFormModal.vue";
import LoadDeviceHistoryModal from "../../components/homeLoads/LoadDeviceHistoryModal.vue";
import {
  PhPlus,
  PhPlug,
  PhHouse,
  PhPencil,
  PhTrash,
  PhCheck,
  PhX,
} from "@phosphor-icons/vue";

const profileStore = useHomeLoadsProfileStore();
const forecastProviderStore = useEnergyLoadForecastProviderStore();
const historyProviderStore = useEnergyLoadHistoryProviderStore();
const externalServiceStore = useExternalServiceStore();

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

function handleSaveDevice(device: LoadDevice, forecastProvider?: EnergyLoadForecastProvider | null, historyProvider?: EnergyLoadHistoryProvider | null) {
  const pid = profileStore.selectedProfileId;
  if (!pid) return;

  const saveForecastProvider = async (deviceId: string) => {
    if (forecastProvider === null) {
      const existingFpId = device.energy_load_forecast_provider_id;
      if (existingFpId) {
        try {
          await forecastProviderStore.deleteProvider(existingFpId);
        } catch {
          // Provider may have been already deleted
        }
      }
    } else if (forecastProvider) {
      if (forecastProvider.id) {
        await forecastProviderStore.updateProvider(forecastProvider.id, forecastProvider);
      } else {
        const existingFpId = device.energy_load_forecast_provider_id;
        if (existingFpId) {
          try {
            await forecastProviderStore.deleteProvider(existingFpId);
          } catch {
            // Provider may have been already deleted
          }
        }
        const created = await forecastProviderStore.addProvider(forecastProvider);
        if (created?.id) {
          await profileStore.updateDevice(pid, deviceId, {
            ...device,
            energy_load_forecast_provider_id: created.id,
          });
        }
      }
    }
    await forecastProviderStore.loadProviders();
  };

  const saveHistoryProvider = async (deviceId: string) => {
    if (historyProvider === null) {
      const existingHpId = device.energy_load_history_provider_id;
      if (existingHpId) {
        try {
          await historyProviderStore.deleteProvider(existingHpId);
        } catch {
          // Provider may have been already deleted
        }
      }
    } else if (historyProvider) {
      if (historyProvider.id) {
        await historyProviderStore.updateProvider(historyProvider.id, historyProvider);
      } else {
        const existingHpId = device.energy_load_history_provider_id;
        if (existingHpId) {
          try {
            await historyProviderStore.deleteProvider(existingHpId);
          } catch {
            // Provider may have been already deleted
          }
        }
        const created = await historyProviderStore.addProvider(historyProvider);
        if (created?.id) {
          await profileStore.updateDevice(pid, deviceId, {
            ...device,
            energy_load_history_provider_id: created.id,
          });
        }
      }
    }
    await historyProviderStore.loadProviders();
  };

  if (isDeviceEditMode.value && device.id) {
    const saveData = {
      ...device,
      ...(forecastProvider === null ? { energy_load_forecast_provider_id: undefined } : {}),
      ...(historyProvider === null ? { energy_load_history_provider_id: undefined } : {}),
    };
    profileStore
      .updateDevice(pid, device.id, saveData)
      .then(async () => {
        await saveForecastProvider(device.id!);
        await saveHistoryProvider(device.id!);
        await profileStore.loadProfiles();
        handleCloseDeviceModal();
      })
      .showToasts("Device updated successfully", "Failed to update device");
  } else {
    profileStore
      .addDevice(pid, device)
      .then(async (created) => {
        const newId = (created as any)?.id ?? device.id;
        if (newId) {
          if (forecastProvider) await saveForecastProvider(newId);
          if (historyProvider) await saveHistoryProvider(newId);
        }
        await profileStore.loadProfiles();
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

        <!-- Devices -->
        <template v-if="selectedProfile">
          <div class="space-y-4">
            <div class="flex justify-end">
              <button class="btn btn-primary gap-2" @click="openAddDevice">
                <PhPlus :size="20" weight="bold" />
                Add Device
              </button>
            </div>

            <LoadDeviceTable
              v-if="devices.length > 0"
              :devices="devices"
              :forecast-providers="forecastProviderStore.providers"
              :history-providers="historyProviderStore.providers"
              @edit="handleEditDevice"
              @delete="handleDeleteDevice"
              @view-history="handleViewHistory"
            />

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
</template>

<style scoped>
.stat-card {
  transition: all 0.2s ease;
}
.stat-card:hover {
  border-color: oklch(50% 0 0 / 0.5);
}
</style>
