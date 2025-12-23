<script setup lang="ts">
import type { EnergySource } from "../../core/models/energySource";
import { EnergySourceType } from "../../core/models/energySource";
import { useEnergyMonitorStore } from "../../core/stores/energyMonitorStore";
import { useForecastProviderStore } from "../../core/stores/forecastProviderStore";
import { computed } from "vue";

const model = defineModel<EnergySource>({ required: true });
const props = defineProps<{
  allEnergySources?: EnergySource[];
}>();

const energyMonitorStore = useEnergyMonitorStore();
const forecastProviderStore = useForecastProviderStore();

// Compute the monitor IDs already assigned to other energy sources
const assignedEnergyMonitorIds = computed(() => {
  if (!props.allEnergySources) return new Set<string>();
  return new Set(
    props.allEnergySources
      .filter((es) => es.id !== model.value.id && es.energy_monitor_id)
      .map((es) => String(es.energy_monitor_id))
  );
});

// Compute the forecast provider IDs already assigned to other energy sources
const assignedForecastProviderIds = computed(() => {
  if (!props.allEnergySources) return new Set<string>();
  return new Set(
    props.allEnergySources
      .filter((es) => es.id !== model.value.id && es.forecast_provider_id)
      .map((es) => String(es.forecast_provider_id))
  );
});

// Filter available energy monitors (not assigned or assigned to the current energy source)
const availableEnergyMonitors = computed(() => {
  return energyMonitorStore.energyMonitors.filter(
    (monitor) => 
      !assignedEnergyMonitorIds.value.has(String(monitor.id)) || 
      String(monitor.id) === String(model.value.energy_monitor_id)
  );
});

// Filter available forecast providers (not assigned or assigned to the current energy source)
const availableForecastProviders = computed(() => {
  return forecastProviderStore.forecastProviders.filter(
    (provider) => 
      !assignedForecastProviderIds.value.has(String(provider.id)) || 
      String(provider.id) === String(model.value.forecast_provider_id)
  );
});
</script>
<template>
  <tr>
    <td>
      <div class="flex flex-col gap-2">
        <input
          class="input validator"
          v-model="model.name"
          type="text"
          required
          placeholder="Energy source name"
        />
      </div>
    </td>
    <td>
      <select
          class="select select-info"
          required
          v-model="model.type"
        >
          <option v-for="energySourceType in EnergySourceType" :value="energySourceType">
            {{ String(energySourceType) }}
          </option>
        </select>
    </td>
    <td>
      <label class="input">
        Watts
        <input
          v-model.number="model.nominal_power_max"
          type="number"
          class="grow"
          placeholder="Optional"
        />
      </label>
    </td>
    <td>
      <label class="input">
        Wh
        <input
          :value="model.storage?.nominal_capacity ?? ''"
          @input="(e) => {
            if (!model.storage) model.storage = { nominal_capacity: 0 };
            model.storage.nominal_capacity = Number((e.target as HTMLInputElement).value);
          }"
          type="number"
          class="grow"
          placeholder="Optional"
        />
      </label>
    </td>
    <td>
      <label class="input">
        Watts
        <input
          :value="model.grid?.contracted_power ?? ''"
          @input="(e) => {
            if (!model.grid) model.grid = { contracted_power: 0 };
            model.grid.contracted_power = Number((e.target as HTMLInputElement).value);
          }"
          type="number"
          class="grow"
          placeholder="Optional"
        />
      </label>
    </td>
    <td>
      <label class="input">
        Watts
        <input
          v-model.number="model.external_source"
          type="number"
          class="grow"
          placeholder="Optional"
        />
      </label>
    </td>
    <td>
      <select
        class="select select-bordered select-sm w-full"
        v-model="model.energy_monitor_id"
      >
        <option :value="undefined">None</option>
        <option
          v-for="energyMonitor in availableEnergyMonitors"
          :key="energyMonitor.id"
          :value="energyMonitor.id"
        >
          {{ energyMonitor.name }}
        </option>
      </select>
    </td>
    <td>
      <select
        class="select select-bordered select-sm w-full"
        v-model="model.forecast_provider_id"
      >
        <option :value="undefined">None</option>
        <option
          v-for="forecastProvider in availableForecastProviders"
          :key="forecastProvider.id"
          :value="forecastProvider.id"
        >
          {{ forecastProvider.name }}
        </option>
      </select>
    </td>
    <th></th>
  </tr>
</template>
