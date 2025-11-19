<script setup lang="ts">
import type { Miner } from "../../core/models/miner";
import { ref } from "vue";

const model = defineModel<Miner>({ required: true });
const emit = defineEmits<{
  edit: [miner: Miner];
  delete: [miner: Miner];
  start: [miner: Miner];
  stop: [miner: Miner];
  activate: [miner: Miner];
  deactivate: [miner: Miner];
}>();

const isProcessing = ref(false);

function handleEdit() {
  emit("edit", model.value);
}

function handleDelete() {
  if (confirm(`Are you sure you want to delete miner "${model.value.name}"?`)) {
    emit("delete", model.value);
  }
}

function handleStart() {
  isProcessing.value = true;
  emit("start", model.value);
}

function handleStop() {
  isProcessing.value = true;
  emit("stop", model.value);
}

function handleActivate() {
  emit("activate", model.value);
}

function handleDeactivate() {
  emit("deactivate", model.value);
}
</script>
<template>
  <tr>
    <th>
      <label>
        <input type="checkbox" class="checkbox" />
      </label>
    </th>
    <td>
      <div class="flex items-center gap-3">
        <div>
          <div class="text-xl">{{ model.name }}</div>
          <div class="text-sm opacity-50">
            <span v-if="model.active" class="badge badge-success badge-sm">Active</span>
            <span v-else class="badge badge-ghost badge-sm">Inactive</span>
          </div>
        </div>
      </div>
    </td>
    <td>
      <div
        class="text-xl"
        :class="model.status === 'active' ? 'text-green-500' : 'text-red-500'"
      >
        {{ model.status }}
      </div>
    </td>
    <td>
      <div class="text-xl">
        {{ model.hash_rate?.value }} {{ model.hash_rate?.unit }}
      </div>
      <div class="text-sm opacity-50">
        ({{ model.hash_rate_max?.value }} {{ model.hash_rate_max?.unit }})
      </div>
    </td>
    <td>
      <div class="text-xl">{{ model.power_consumption }} Watts</div>
      <div class="text-sm opacity-50">
        ({{ model.power_consumption_max }} Watts)
      </div>
    </td>
    <th>
      <div class="flex gap-2">
        <div class="join join-vertical lg:join-horizontal">
          <button
            class="btn btn-sm btn-success join-item"
            @click="handleStart"
            :disabled="isProcessing || model.status === 'active'"
            title="Start miner"
          >
            ▶
          </button>
          <button
            class="btn btn-sm btn-warning join-item"
            @click="handleStop"
            :disabled="isProcessing || model.status !== 'active'"
            title="Stop miner"
          >
            ⏸
          </button>
        </div>
        <button
          v-if="!model.active"
          class="btn btn-sm btn-info"
          @click="handleActivate"
          title="Activate miner"
        >
          Activate
        </button>
        <button
          v-else
          class="btn btn-sm btn-ghost"
          @click="handleDeactivate"
          title="Deactivate miner"
        >
          Deactivate
        </button>
        <button class="btn btn-sm btn-primary" @click="handleEdit" title="Edit miner">
          ✏️
        </button>
        <button class="btn btn-sm btn-error" @click="handleDelete" title="Delete miner">
          🗑️
        </button>
      </div>
    </th>
  </tr>
</template>
