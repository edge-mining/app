<script setup lang="ts">
import type { EnergySource } from "../../core/models/energySource";
import { useEnergyMonitorStore } from "../../core/stores/energyMonitorStore";
import { useForecastProviderStore } from "../../core/stores/forecastProviderStore";
import { computed, ref } from "vue";
import { PhHash, PhPencil, PhTrash } from "@phosphor-icons/vue";
import ConfirmDialog from "../ConfirmDialog.vue";

const model = defineModel<EnergySource>({ required: true });
const emit = defineEmits<{
  edit: [energySource: EnergySource];
  delete: [energySource: EnergySource];
}>();

const energyMonitorStore = useEnergyMonitorStore();
const forecastProviderStore = useForecastProviderStore();
const showDeleteConfirm = ref(false);

const energyMonitor = computed(() => {
  if (!model.value.energy_monitor_id) return null;
  return energyMonitorStore.energyMonitors.find((em) => em.id === model.value.energy_monitor_id);
});
const forecastProvider = computed(() => {
  if (!model.value.forecast_provider_id) return null;
  return forecastProviderStore.forecastProviders.find((fp) => fp.id === model.value.forecast_provider_id);
});

const energySourceTip = ref<string | null>(null);
const energyMonitorTip = ref<string | null>(null);
const forecastProviderTip = ref<string | null>(null);

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

function flashTip(target: "source" | "monitor" | "forecast", original: string) {
  const tipRef = target === "source" ? energySourceTip : target === "monitor" ? energyMonitorTip : forecastProviderTip;
  tipRef.value = "Copied!";
  window.setTimeout(() => {
    tipRef.value = original;
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
        <div>
          <div class="text-xl flex items-center gap-1">
            <span
              v-if="model.id != null"
              class="tooltip tooltip-right id-tooltip"
              :data-tip="energySourceTip ?? `ID: ${model.id}`"
            >
              <span
                role="button"
                tabindex="0"
                class="inline-flex cursor-pointer select-none opacity-70 hover:opacity-100"
                title="Copy energy source ID"
                aria-label="Copy energy source ID"
                @click.stop="copyToClipboard(String(model.id)); flashTip('source', `ID: ${model.id}`)"
                @keydown.enter.stop.prevent="copyToClipboard(String(model.id)); flashTip('source', `ID: ${model.id}`)"
                @keydown.space.stop.prevent="copyToClipboard(String(model.id)); flashTip('source', `ID: ${model.id}`)"
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
      <div class="text-xl">
        <span class="badge">{{ model.type }}</span>
      </div>
    </td>
    <td>
      <div v-if="model.nominal_power_max" class="text-xl">
        <span>{{ model.nominal_power_max }}</span>
        <span class="ml-1 text-xs opacity-70 align-baseline">Watts</span>
      </div>
      <div v-else class="text-xl">
        <span>-</span>
      </div>
    </td>
    <td>
      <div v-if="model.storage && model.storage.nominal_capacity" class="text-xl">
        <span>{{ model.storage?.nominal_capacity }}</span>
        <span class="ml-1 text-xs opacity-70 align-baseline">Wh</span>
      </div>
      <div v-else class="text-xl">
        <span>-</span>
      </div>
    </td>
    <td>
      <div v-if="model.grid && model.grid.contracted_power" class="text-xl">
        <span>{{ model.grid.contracted_power }}</span>
        <span class="ml-1 text-xs opacity-70 align-baseline">Watts</span>
      </div>
      <div v-else class="text-xl">
        <span>-</span>
      </div>
    </td>
    <td>
      <div v-if="model.external_source" class="text-xl">
        <span>{{ model.external_source  }}</span>
        <span class="ml-1 text-xs opacity-70 align-baseline">Watts</span>
      </div>
      <div v-else class="text-xl">
        <span>-</span>
      </div>
    </td>
    <td>
      <div v-if="model.energy_monitor_id">
        <div class="text-sm opacity-50 flex items-center gap-1">
          <span
            v-if="model.energy_monitor_id != null"
            class="tooltip tooltip-top id-tooltip"
            :data-tip="energyMonitorTip ?? `ID: ${model.energy_monitor_id}`"
          >
            <span
              role="button"
              tabindex="0"
              class="inline-flex cursor-pointer select-none opacity-70 hover:opacity-100"
              title="Copy energy monitor ID"
              aria-label="Copy energy monitor ID"
              @click.stop="copyToClipboard(String(model.energy_monitor_id)); flashTip('monitor', `ID: ${model.energy_monitor_id}`)"
              @keydown.enter.stop.prevent="copyToClipboard(String(model.energy_monitor_id)); flashTip('monitor', `ID: ${model.energy_monitor_id}`)"
              @keydown.space.stop.prevent="copyToClipboard(String(model.energy_monitor_id)); flashTip('monitor', `ID: ${model.energy_monitor_id}`)"
            >
              <PhHash class="size-3" />
            </span>
          </span>
          <span class="text-sm">{{ energyMonitor?.name ?? "Unknown" }}</span>
        </div>
      </div>
      <div v-else class="text-sm opacity-50">-</div>
    </td>
    <td>
      <div v-if="model.forecast_provider_id">
        <div class="text-sm opacity-50 flex items-center gap-1">
          <span
            v-if="model.forecast_provider_id != null"
            class="tooltip tooltip-top id-tooltip"
            :data-tip="energyMonitorTip ?? `ID: ${model.forecast_provider_id}`"
          >
            <span
              role="button"
              tabindex="0"
              class="inline-flex cursor-pointer select-none opacity-70 hover:opacity-100"
              title="Copy forecast provider ID"
              aria-label="Copy forecast provider ID"
              @click.stop="copyToClipboard(String(model.forecast_provider_id)); flashTip('forecast', `ID: ${model.forecast_provider_id}`)"
              @keydown.enter.stop.prevent="copyToClipboard(String(model.forecast_provider_id)); flashTip('forecast', `ID: ${model.forecast_provider_id}`)"
              @keydown.space.stop.prevent="copyToClipboard(String(model.forecast_provider_id)); flashTip('forecast', `ID: ${model.forecast_provider_id}`)"
            >
              <PhHash class="size-3" />
            </span>
          </span>
          <span class="text-sm">{{ forecastProvider?.name ?? "Unknown" }}</span>
        </div>
      </div>
      <div v-else class="text-sm opacity-50">-</div>
    </td>
    <th>
      <div class="flex gap-2">
        <button class="btn btn-sm btn-primary" @click="handleEdit" title="Edit energy source"><PhPencil :size="15" /></button>
        <button class="btn btn-sm btn-error" @click="handleDeleteClick" title="Delete energy source"><PhTrash :size="15" /></button>
      </div>
    </th>
  </tr>

  <ConfirmDialog
    :open="showDeleteConfirm"
    title="Delete Energy Source"
    :message="`Are you sure you want to delete energy source '${model.name}'?`"
    confirm-text="Delete"
    variant="danger"
    @confirm="confirmDelete"
    @cancel="cancelDelete"
  />
</template>
