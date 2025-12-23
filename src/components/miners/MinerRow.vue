<script setup lang="ts">
import type { Miner } from "../../core/models/miner";
import { computed, ref } from "vue";
import { useMinerControllerStore } from "../../core/stores/minerControllerStore";
import { PhCpu, PhCircuitry } from "@phosphor-icons/vue";

const model = defineModel<Miner>({ required: true });
const emit = defineEmits<{
  edit: [miner: Miner];
  delete: [miner: Miner];
  start: [miner: Miner];
  stop: [miner: Miner];
  activate: [miner: Miner];
  deactivate: [miner: Miner];
}>();

const minerControllerStore = useMinerControllerStore();

const minerController = computed(() => {
  if (!model.value.controller_id) return null;
  return minerControllerStore.minerControllers.find((mc) => mc.id === model.value.controller_id);
});

const isProcessing = ref(false);

const minerIdTip = ref<string | null>(null);
const controllerIdTip = ref<string | null>(null);

async function copyToClipboard(text: string) {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    const el = document.createElement("textarea");
    el.value = text;
    el.style.position = "fixed";
    el.style.left = "-9999px";
    document.body.appendChild(el);
    el.select();
    document.execCommand("copy");
    document.body.removeChild(el);
  }
}

function flashTip(target: "miner" | "controller", original: string) {
  const tipRef = target === "miner" ? minerIdTip : controllerIdTip;
  tipRef.value = "Copied!";
  window.setTimeout(() => {
    tipRef.value = original;
  }, 1200);
}

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
      <div class="flex items-center gap-3">
        <div>
          <div class="text-xl flex items-center gap-1">
            <span
              v-if="model.id != null"
              class="tooltip tooltip-top whitespace-nowrap"
              :data-tip="minerIdTip ?? `ID: ${model.id}`"
            >
              <span
                role="button"
                tabindex="0"
                class="inline-flex cursor-pointer select-none opacity-70 hover:opacity-100"
                title="Copy miner ID"
                aria-label="Copy miner ID"
                @click.stop="copyToClipboard(String(model.id)); flashTip('miner', `ID: ${model.id}`)"
                @keydown.enter.stop.prevent="copyToClipboard(String(model.id)); flashTip('miner', `ID: ${model.id}`)"
                @keydown.space.stop.prevent="copyToClipboard(String(model.id)); flashTip('miner', `ID: ${model.id}`)"
              >
                <PhCpu class="size-3" />
              </span>
            </span>
            <span>{{ model.name }}</span>
          </div>

          <div class="text-sm opacity-50">
            <span v-if="model.active" class="badge badge-success badge-sm">Active</span>
            <span v-else class="badge badge-ghost badge-sm">Inactive</span>
          </div>
        </div>
      </div>
    </th>

    <td>
      <div
        class="text-xl"
        :class="
          model.status === 'active'
            ? 'text-green-500'
            : model.status === 'unknown'
              ? 'text-amber-500'
              : 'text-red-500'
        "
      >
        {{ model.status }}
      </div>
    </td>

    <td>
      <div class="text-xl">
        <span>{{ model.hash_rate?.value }}</span>
        <span class="ml-1 text-xs opacity-70 align-baseline">{{ model.hash_rate?.unit }}</span>
      </div>
      <div class="text-sm opacity-50">
        (<span>{{ model.hash_rate_max?.value }}</span>
        <span class="ml-1 text-xs opacity-70 align-baseline">{{ model.hash_rate_max?.unit }}</span>)
      </div>
    </td>

    <td>
      <div class="text-xl">
        <span>{{ model.power_consumption }}</span>
        <span class="ml-1 text-xs opacity-70 align-baseline">Watts</span>
      </div>
      <div class="text-sm opacity-50">
        (<span>{{ model.power_consumption_max }}</span>
        <span class="ml-1 text-xs opacity-70 align-baseline">Watts</span>)
      </div>
    </td>

    <td>
      <div v-if="model.controller_id">
        <div class="text-sm opacity-50 flex items-center gap-1">
          <span
            v-if="model.controller_id != null"
            class="tooltip tooltip-bottom whitespace-nowrap"
            :data-tip="controllerIdTip ?? `ID: ${model.controller_id}`"
          >
            <span
              role="button"
              tabindex="0"
              class="inline-flex cursor-pointer select-none opacity-70 hover:opacity-100"
              title="Copy miner controller ID"
              aria-label="Copy miner controller ID"
              @click.stop="copyToClipboard(String(model.controller_id)); flashTip('controller', `ID: ${model.controller_id}`)"
              @keydown.enter.stop.prevent="copyToClipboard(String(model.controller_id)); flashTip('controller', `ID: ${model.controller_id}`)"
              @keydown.space.stop.prevent="copyToClipboard(String(model.controller_id)); flashTip('controller', `ID: ${model.controller_id}`)"
            >
              <PhCircuitry class="size-3" />
            </span>
          </span>
          <span class="text-sm">{{ minerController?.name ?? "Unknown" }}</span>
        </div>
      </div>
      <div v-else class="text-sm opacity-50">-</div>
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

        <button class="btn btn-sm btn-primary" @click="handleEdit" title="Edit miner">✏️</button>
        <button class="btn btn-sm btn-error" @click="handleDelete" title="Delete miner">🗑️</button>
      </div>
    </th>
  </tr>
</template>
