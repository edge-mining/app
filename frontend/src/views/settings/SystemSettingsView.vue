<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { useSystemSettingsStore } from "../../core/stores/systemSettingsStore";
import type { SystemConfiguration } from "../../core/models/systemConfiguration";
import LocationMapPicker from "../../components/LocationMapPicker.vue";
import {
  PhClock,
  PhFloppyDisk,
  PhGlobeHemisphereWest,
  PhMapPin,
} from "@phosphor-icons/vue";

const systemSettingsStore = useSystemSettingsStore();

const loaded = ref(false);

const form = reactive<SystemConfiguration>({
  timezone: "Europe/Rome",
  latitude: 41.9028,
  longitude: 12.4964,
  scheduler_interval_seconds: 5,
});

// The list of selectable IANA timezones is provided by the browser.
const timezones = ref<string[]>([]);

onMounted(async () => {
  loadTimezones();
  await systemSettingsStore.loadConfiguration();
  if (systemSettingsStore.configuration) {
    Object.assign(form, systemSettingsStore.configuration);
  }
  // Make sure the current timezone is always selectable.
  if (form.timezone && !timezones.value.includes(form.timezone)) {
    timezones.value = [form.timezone, ...timezones.value];
  }
  loaded.value = true;
});

function loadTimezones() {
  try {
    const supported = (Intl as unknown as {
      supportedValuesOf?: (key: string) => string[];
    }).supportedValuesOf;
    timezones.value = supported ? supported("timeZone") : [];
  } catch {
    timezones.value = [];
  }
}

function handleSave() {
  systemSettingsStore
    .updateConfiguration({ ...form })
    .showToasts("System settings saved", "Failed to save system settings");
}
</script>

<template>
  <div class="card">
    <div class="card-header">
      <div>
        <h1 class="text-2xl font-bold text-base-content">System</h1>
        <p class="text-sm text-base-content/60 mt-1">
          Configure timezone, location and the optimization scheduler interval
        </p>
      </div>
    </div>
    <div class="card-body">
      <form class="space-y-8 max-w-2xl" @submit.prevent="handleSave">
        <!-- Time -->
        <section class="space-y-4">
          <h2 class="flex items-center gap-2 text-lg font-semibold text-base-content">
            <PhGlobeHemisphereWest :size="20" class="text-primary" />
            Time
          </h2>
          <div class="form-control">
            <label class="label mb-1">
              <span class="label-text font-medium">Timezone</span>
            </label>
            <select v-model="form.timezone" class="select select-bordered w-full">
              <option v-for="tz in timezones" :key="tz" :value="tz">{{ tz }}</option>
            </select>
            <label class="label">
              <span class="label-text-alt text-base-content/50">
                Used for timestamps and Sun-based calculations
              </span>
            </label>
          </div>
        </section>

        <!-- Location -->
        <section class="space-y-4">
          <h2 class="flex items-center gap-2 text-lg font-semibold text-base-content">
            <PhMapPin :size="20" class="text-primary" />
            Location
          </h2>
          <LocationMapPicker
            :latitude="form.latitude"
            :longitude="form.longitude"
            @update:latitude="form.latitude = $event"
            @update:longitude="form.longitude = $event"
          />
        </section>

        <!-- Scheduler -->
        <section class="space-y-4">
          <h2 class="flex items-center gap-2 text-lg font-semibold text-base-content">
            <PhClock :size="20" class="text-primary" />
            Scheduler
          </h2>
          <div class="form-control">
            <label class="label mb-1">
              <span class="label-text font-medium">Evaluation interval (seconds)</span>
            </label>
            <input
              v-model.number="form.scheduler_interval_seconds"
              type="number"
              step="1"
              min="1"
              class="input input-bordered w-full sm:max-w-xs"
            />
            <label class="label">
              <span class="label-text-alt text-base-content/50">
                How often enabled optimization units are evaluated
              </span>
            </label>
          </div>
        </section>

        <div class="flex justify-end">
          <button type="submit" class="btn btn-primary gap-2" :disabled="!loaded">
            <PhFloppyDisk :size="20" weight="bold" />
            Save
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
