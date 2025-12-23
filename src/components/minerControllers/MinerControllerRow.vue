<script setup lang="ts">
import { computed, ref } from "vue";
import type { MinerController } from "../../core/models/minerController";
import type { Miner } from "../../core/models/miner";
import { useExternalServiceStore } from "../../core/stores/externalServiceStore";
import { PhHash } from "@phosphor-icons/vue";

const model = defineModel<MinerController>({ required: true });
const props = defineProps<{
  allMiners?: Miner[];
}>();

const emit = defineEmits<{
  edit: [minerController: MinerController];
  delete: [minerController: MinerController];
}>();

const externalServiceStore = useExternalServiceStore();

const externalService = computed(() => {
  if (!model.value.external_service_id) return null;
  return externalServiceStore.externalServices.find(
    (es) => es.id?.toString() === model.value.external_service_id
  );
});

const assignedMiners = computed(() => {
  if (!props.allMiners || !model.value.id) return [];
  return props.allMiners
    .filter((miner) => miner.controller_id === model.value.id)
    .map((miner) => miner.name);
});

const assignedMinersText = computed(() => {
  if (assignedMiners.value.length === 0) return "-";
  return assignedMiners.value.join(", ");
});

const controllerIdTip = ref<string | null>(null);
const externalServiceIdTip = ref<string | null>(null);

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

function flashTip(target: "controller" | "external", original: string) {
  const tipRef = target === "controller" ? controllerIdTip : externalServiceIdTip;
  tipRef.value = "Copied!";
  window.setTimeout(() => {
    tipRef.value = original;
  }, 1200);
}

function handleEdit() {
  emit("edit", model.value);
}

function handleDelete() {
  if (confirm(`Are you sure you want to delete miner controller "${model.value.name}"?`)) {
    emit("delete", model.value);
  }
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
              :data-tip="controllerIdTip ?? `ID: ${model.id}`"
            >
              <span
                role="button"
                tabindex="0"
                class="inline-flex cursor-pointer select-none opacity-70 hover:opacity-100"
                title="Copy miner controller ID"
                aria-label="Copy miner controller ID"
                @click.stop="copyToClipboard(String(model.id)); flashTip('controller', `ID: ${model.id}`)"
                @keydown.enter.stop.prevent="copyToClipboard(String(model.id)); flashTip('controller', `ID: ${model.id}`)"
                @keydown.space.stop.prevent="copyToClipboard(String(model.id)); flashTip('controller', `ID: ${model.id}`)"
              >
                <PhHash class="size-3" />
              </span>
            </span>
            <span>{{ model.name }}</span>
          </div>
        </div>
      </div>
    </th>
    <td>
      <div class="text-sm opacity-70">{{ model.adapter_type }}</div>
    </td>

    <td>
      <div class="text-sm opacity-70">{{ assignedMinersText }}</div>
    </td>

    <td>
      <div v-if="model.external_service_id">
        <div class="text-sm opacity-50 flex items-center gap-1">
          <span
            class="tooltip tooltip-top id-tooltip"
            :data-tip="externalServiceIdTip ?? `ID: ${model.external_service_id}`"
          >
            <span
              role="button"
              tabindex="0"
              class="inline-flex cursor-pointer select-none opacity-70 hover:opacity-100"
              title="Copy external service ID"
              aria-label="Copy external service ID"
              @click.stop="copyToClipboard(model.external_service_id); flashTip('external', `ID: ${model.external_service_id}`)"
              @keydown.enter.stop.prevent="copyToClipboard(model.external_service_id); flashTip('external', `ID: ${model.external_service_id}`)"
              @keydown.space.stop.prevent="copyToClipboard(model.external_service_id); flashTip('external', `ID: ${model.external_service_id}`)"
            >
              <PhHash class="size-3" />
            </span>
          </span>
          <span class="text-sm">{{ externalService?.name ?? "Unknown" }}</span>
        </div>
      </div>
      <div v-else class="text-sm opacity-50">-</div>
    </td>

    <th>
      <div class="flex gap-2">
        <button class="btn btn-sm btn-primary" @click="handleEdit" title="Edit miner controller">Edit</button>
        <button class="btn btn-sm btn-error" @click="handleDelete" title="Delete miner controller">Delete</button>
      </div>
    </th>
  </tr>
</template>
