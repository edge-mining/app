<script setup lang="ts">
import { onMounted, computed } from "vue";
import { useHomeLoadsProfileStore } from "../../core/stores/homeLoadsProfileStore";
import { useLoadTrainingStore } from "../../core/stores/loadTrainingStore";
import TrainingPanel from "../../components/homeLoads/TrainingPanel.vue";
import { PhBrain } from "@phosphor-icons/vue";

const profileStore = useHomeLoadsProfileStore();
const trainingStore = useLoadTrainingStore();

const devices = computed(() => {
  const profile = profileStore.profiles.find((p) => p.id === profileStore.selectedProfileId);
  return profile?.devices ?? [];
});

onMounted(() => {
  if (profileStore.profiles.length === 0) {
    profileStore.loadProfiles();
  }
  trainingStore.loadModels();
});

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
      <div class="flex items-center gap-3">
        <PhBrain :size="28" class="text-purple-400" />
        <div>
          <h1 class="text-2xl font-bold text-base-content">Model Training</h1>
          <p class="text-sm text-base-content/60 mt-0.5">
            Train and manage forecast models for your load devices
          </p>
        </div>
      </div>
    </div>
    <div class="card-body">
      <TrainingPanel
        :profile-id="profileStore.selectedProfileId ?? undefined"
        :devices="devices"
        @train-all="handleTrainAll"
        @train-device="handleTrainSingleDevice"
      />
    </div>
  </div>
</template>
