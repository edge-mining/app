<script setup lang="ts">
import type { Miner } from "../../core/models/miner";
import { computed, ref, watch } from "vue";
import { useMinerControllerStore } from "../../core/stores/minerControllerStore";
import { PhHash, PhPlay, PhStop, PhArrowClockwise, PhPencil, PhTrash } from "@phosphor-icons/vue";

const model = defineModel<Miner>({ required: true });
const emit = defineEmits<{
  edit: [miner: Miner];
  delete: [miner: Miner];
  start: [miner: Miner];
  stop: [miner: Miner];
  refresh: [miner: Miner];
  activate: [miner: Miner];
  deactivate: [miner: Miner];
}>();

const minerControllerStore = useMinerControllerStore();

const minerController = computed(() => {
  if (!model.value.controller_id) return null;
  return minerControllerStore.minerControllers.find((mc) => mc.id === model.value.controller_id);
});

const isProcessing = ref(false);

const isOn = computed(() => model.value.status === "on");
const isStarting = computed(() => model.value.status === "starting");
const isStopping = computed(() => model.value.status === "stopping");
const canStart = computed(() => model.value.active && !isOn.value && (!isStarting.value || isStopping.value) && !isProcessing.value);
const canStop = computed(() => model.value.active && (isOn.value || isStarting.value) && !isProcessing.value);

// Reset isProcessing when status changes
watch(() => model.value.status, (newStatus, oldStatus) => {
  if (newStatus !== oldStatus && isProcessing.value) {
    isProcessing.value = false;
  }
});

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
  if (!canStart.value) return;
  isProcessing.value = true;
  emit("start", model.value);
}

function handleStop() {
  if (!canStop.value) return;
  isProcessing.value = true;
  emit("stop", model.value);
}

function handleRefresh() {
  emit("refresh", model.value);
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
              class="tooltip tooltip-right id-tooltip"
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
                <PhHash class="size-3" />
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
      <div class="text-sm">{{ model.model ?? '-' }}</div>
    </td>

    <td>
      <div
        class="text-xl"
        :class="
          model.status === 'on'
            ? 'text-green-500'
            : model.status === 'starting' || model.status === 'stopping'
              ? 'text-amber-500'
              : model.status === 'unknown'
                ? 'text-gray-500'
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
            class="tooltip tooltip-top id-tooltip"
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
              <PhHash class="size-3" />
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
            class="btn btn-sm join-item"
            :class="canStart ? 'btn-success' : 'btn-ghost opacity-60'"
            @click="handleStart"
            :disabled="!canStart"
            title="Start miner"
          >
            <PhPlay :size="15" />
          </button>
          <button
            class="btn btn-sm join-item"
            :class="canStop ? 'btn-warning' : 'btn-ghost opacity-60'"
            @click="handleStop"
            :disabled="!canStop"
            title="Stop miner"
          >
            <PhStop :size="15" />
          </button>
          <button
            class="btn btn-sm btn-info join-item"
            @click="handleRefresh"
            title="Refresh miner status"
          >
            <PhArrowClockwise :size="15" />
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

        <button class="btn btn-sm btn-primary" @click="handleEdit" title="Edit miner"><PhPencil :size="15" /></button>
        <button class="btn btn-sm btn-error" @click="handleDelete" title="Delete miner"><PhTrash :size="15" /></button>
      </div>
    </th>
  </tr>
</template>
