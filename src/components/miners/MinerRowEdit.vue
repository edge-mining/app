<script setup lang="ts">
import type { Miner } from "../../core/models/miner";
import { useMinerControllerStore } from "../../core/stores/minerControllerStore";
import { computed } from "vue";

const model = defineModel<Miner>({ required: true });
const props = defineProps<{
  allMiners?: Miner[];
}>();

const minerControllerStore = useMinerControllerStore();

// Compute the controller IDs already assigned to other miners
const assignedControllerIds = computed(() => {
  if (!props.allMiners) return new Set<string>();
  return new Set(
    props.allMiners
      .filter((m) => m.id !== model.value.id && m.controller_id)
      .map((m) => String(m.controller_id))
  );
});

// Filter available controllers (not assigned or assigned to the current miner)
const availableControllers = computed(() => {
  return minerControllerStore.minerControllers.filter(
    (controller) => 
      !assignedControllerIds.value.has(controller.id!) || 
      controller.id === model.value.controller_id
  );
});
</script>
<template>
  <tr>
    <th>
      <div class="flex items-center gap-3">
        <div>
          <div class="text-xl">
            <input
              class="input validator"
              v-model="model.name"
              type="text"
              required
              placeholder="Miner name"
            />
          </div>
        </div>
      </div>
    </th>
    <td>
      <div
        class="text-xl"
        :class="model.status === 'active' ? 'text-green-500' : 'text-red-500'"
      ></div>
    </td>
    <td>
      <div class="text-xl grid grid-cols-7 gap-1" v-if="model.hash_rate_max">
        <input
          class="input validator col-span-4"
          v-model="model.hash_rate_max.value"
          type="number"
          required
          placeholder="100"
        />
        <!-- "GH/s", "TH/s", "PH/s", "EH/s" -->
        <select
          class="select select-info col-span-3"
          required
          v-model="model.hash_rate_max.unit"
        >
          <option>GH/s</option>
          <option>TH/s</option>
          <option>PH/s</option>
          <option>EH/s</option>
        </select>

        <!-- {{ model.hash_rate?.unit }} -->
      </div>
    </td>
    <td>
      <div class="text-xl">
        <label class="input">
          Watts
          <input
            v-model="model.power_consumption_max"
            type="number"
            class="grow"
            required
          />
        </label>
        <!-- <input
          class="input validator"
          v-model="model.power_consumption"
          type="number"
          required
          placeholder="100"
        />
        Watts -->
      </div>
    </td>
    <td>
      <select
        class="select select-bordered select-sm w-full"
        v-model="model.controller_id"
      >
        <option :value="undefined">None</option>
        <option
          v-for="controller in availableControllers"
          :key="controller.id"
          :value="controller.id"
        >
          {{ controller.name }}
        </option>
      </select>
    </td>
    <th></th>
  </tr>
</template>
