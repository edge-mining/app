<script setup lang="ts">
import type { ExternalService } from "../../core/models/externalService";
import type { EnergyMonitor } from "../../core/models/energyMonitor";
import type { ForecastProvider } from "../../core/models/forecastProvider";
import type { MinerController } from "../../core/models/minerController";
import { computed, ref } from "vue";
import { PhHash, PhPencil, PhTrash } from "@phosphor-icons/vue";
import ConfirmDialog from "../ConfirmDialog.vue";

const model = defineModel<ExternalService>({ required: true });
const props = defineProps<{
  allEnergyMonitors?: EnergyMonitor[];
  allForecastProviders?: ForecastProvider[];
  allMinerControllers?: MinerController[];
}>();
const emit = defineEmits<{
  edit: [externalService: ExternalService];
  delete: [externalService: ExternalService];
}>();

const showDeleteConfirm = ref(false);

const associatedEnergyMonitors = computed(() => {
  if (!props.allEnergyMonitors || !model.value.id) return [];
  return props.allEnergyMonitors.filter(em => em.external_service_id === model.value.id?.toString());
});

const associatedForecastProviders = computed(() => {
  if (!props.allForecastProviders || !model.value.id) return [];
  return props.allForecastProviders.filter(fp => fp.external_service_id === model.value.id?.toString());
});

const associatedMinerControllers = computed(() => {
  if (!props.allMinerControllers || !model.value.id) return [];
  return props.allMinerControllers.filter(mc => mc.external_service_id === model.value.id?.toString());
});

const associatedEnergyMonitorsText = computed(() => {
  if (associatedEnergyMonitors.value.length === 0) return "-";
  return associatedEnergyMonitors.value.map(em => em.name).join(", ");
});

const associatedForecastProvidersText = computed(() => {
  if (associatedForecastProviders.value.length === 0) return "-";
  return associatedForecastProviders.value.map(fp => fp.name).join(", ");
});

const associatedMinerControllersText = computed(() => {
  if (associatedMinerControllers.value.length === 0) return "-";
  return associatedMinerControllers.value.map(mc => mc.name).join(", ");
});

const externalServiceTip = ref<string | null>(null);

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

function flashTip(original: string) {
  externalServiceTip.value = "Copied!";
  window.setTimeout(() => {
    externalServiceTip.value = original;
  }, 1200);
}

function handleEdit() {
  emit("edit", model.value);
}

function handleDeleteClick() {
  showDeleteConfirm.value = true;
}

function confirmDelete() {
  showDeleteConfirm.value = false;
  emit("delete", model.value);
}

function cancelDelete() {
  showDeleteConfirm.value = false;
}
</script>
<template>
  <tr>
    <th>
      <div class="flex items-center gap-3">
        <div class="text-xl flex items-center gap-1">
          <span
            v-if="model.id != null"
            class="tooltip tooltip-right id-tooltip"
            :data-tip="externalServiceTip ?? `ID: ${model.id}`"
          >
            <span
              role="button"
              tabindex="0"
              class="inline-flex cursor-pointer select-none opacity-70 hover:opacity-100"
              title="Copy external service ID"
              aria-label="Copy external service ID"
              @click.stop="copyToClipboard(String(model.id)); flashTip(`ID: ${model.id}`)"
              @keydown.enter.stop.prevent="copyToClipboard(String(model.id)); flashTip(`ID: ${model.id}`)"
              @keydown.space.stop.prevent="copyToClipboard(String(model.id)); flashTip(`ID: ${model.id}`)"
            >
              <PhHash class="size-3" />
            </span>
          </span>
          <span>{{ model.name }}</span>
        </div>
      </div>
    </th>
    <td>
      <div class="text-sm opacity-70">{{ model.adapter_type }}</div>
    </td>
    <td>
      <div class="text-sm opacity-70">{{ associatedEnergyMonitorsText }}</div>
    </td>
    <td>
      <div class="text-sm opacity-70">{{ associatedForecastProvidersText }}</div>
    </td>
    <td>
      <div class="text-sm opacity-70">{{ associatedMinerControllersText }}</div>
    </td>
    <th>
      <div class="flex gap-2">
        <button class="btn btn-sm btn-primary" @click="handleEdit" title="Edit external service"><PhPencil :size="15" /></button>
        <button class="btn btn-sm btn-error" @click="handleDeleteClick" title="Delete external service"><PhTrash :size="15" /></button>
      </div>
    </th>
  </tr>

  <ConfirmDialog
    :open="showDeleteConfirm"
    title="Delete External Service"
    :message="`Are you sure you want to delete external service '${model.name}'?`"
    confirm-text="Delete"
    variant="danger"
    @confirm="confirmDelete"
    @cancel="cancelDelete"
  />
</template>
