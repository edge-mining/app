<script setup lang="ts">
import type { EnergyMonitor } from "../../core/models/energyMonitor";
import { useEnergyMonitorStore } from "../../core/stores/energyMonitorStore";

const model = defineModel<EnergyMonitor>({ required: true });
const energyMonitorStore = useEnergyMonitorStore();

// Format adapter type for display (e.g., "dummy_solar" -> "Dummy Solar")
const formatAdapterType = (type: string) => {
  return type
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
};
</script>
<template>
  <tr>
    <th>
      <label>
        <input type="checkbox" class="checkbox" />
      </label>
    </th>
    <td>
      <div class="flex flex-col gap-2">
        <input
          class="input validator"
          v-model="model.name"
          type="text"
          required
          placeholder="Energy monitor name"
        />
        <select
          class="select select-info"
          required
          v-model="model.adapter_type"
        >
          <option
            v-for="adapterType in energyMonitorStore.adapterTypes"
            :key="adapterType"
            :value="adapterType"
          >
            {{ formatAdapterType(adapterType) }}
          </option>
        </select>
      </div>
    </td>
    <td>
      <input
        class="input input-sm"
        v-model="model.external_service_id"
        type="text"
        placeholder="Optional service ID"
      />
    </td>
    <th></th>
  </tr>
</template>
