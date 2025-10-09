<script setup lang="ts">
import type { EnergySource } from "../../core/models/energySource";
import { EnergySourceType } from "../../core/models/energySource";

const model = defineModel<EnergySource>({ required: true });
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
          placeholder="Energy source name"
        />
        <select
          class="select select-info"
          required
          v-model="model.type"
        >
          <option :value="EnergySourceType.SOLAR">Solar</option>
          <option :value="EnergySourceType.WIND">Wind</option>
          <option :value="EnergySourceType.GRID">Grid</option>
          <option :value="EnergySourceType.HYDROELECTRIC">Hydroelectric</option>
          <option :value="EnergySourceType.OTHER">Other</option>
        </select>
      </div>
    </td>
    <td>
      <label class="input">
        kW
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
        kWh
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
        kW
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
      <input
        class="input input-sm"
        v-model="model.energy_monitor_id"
        type="text"
        placeholder="Optional UUID"
      />
    </td>
    <th></th>
  </tr>
</template>
