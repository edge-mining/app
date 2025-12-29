<script setup lang="ts">
  import { computed, ref } from "vue";
import type { ForecastProvider } from "../../core/models/forecastProvider";
import type { EnergySource } from "../../core/models/energySource";
import { useExternalServiceStore } from "../../core/stores/externalServiceStore";
import { PhHash, PhPencil, PhTrash } from "@phosphor-icons/vue";


const model = defineModel<ForecastProvider>({ required: true });
const props = defineProps<{
  allEnergySources?: EnergySource[];
}>();

const emit = defineEmits<{
  edit: [forecastProvider: ForecastProvider];
  delete: [forecastProvider: ForecastProvider];
}>();

const externalServiceStore = useExternalServiceStore();

const externalService = computed(() => {
  if (!model.value.external_service_id) return null;
  return externalServiceStore.externalServices.find(
    (es) => es.id?.toString() === model.value.external_service_id
  );
});

const assignedEnergySources = computed(() => {
  if (!props.allEnergySources || !model.value.id) return [];
  return props.allEnergySources
    .filter((es) => es.energy_monitor_id === model.value.id)
    .map((es) => es.name);
});

const assignedEnergySourcesText = computed(() => {
  if (assignedEnergySources.value.length === 0) return "-";
  return assignedEnergySources.value.join(", ");
});

const forecastProviderTip = ref<string | null>(null);
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

function flashTip(target: "forecast" | "external", original: string) {
  const tipRef = target === "forecast" ? forecastProviderTip : externalServiceIdTip;
  tipRef.value = "Copied!";
  window.setTimeout(() => {
    tipRef.value = original;
  }, 1200);
}

function handleEdit() {
  emit("edit", model.value);
}

function handleDelete() {
  if (confirm(`Are you sure you want to delete forecast provider "${model.value.name}"?`)) {
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
              :data-tip="forecastProviderTip ?? `ID: ${model.id}`"
            >
              <span
                role="button"
                tabindex="0"
                class="inline-flex cursor-pointer select-none opacity-70 hover:opacity-100"
                title="Copy forecast provider ID"
                aria-label="Copy forecast provider ID"
                @click.stop="copyToClipboard(String(model.id)); flashTip('forecast', `ID: ${model.id}`)"
                @keydown.enter.stop.prevent="copyToClipboard(String(model.id)); flashTip('forecast', `ID: ${model.id}`)"
                @keydown.space.stop.prevent="copyToClipboard(String(model.id)); flashTip('forecast', `ID: ${model.id}`)"
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
      <div class="text-sm opacity-70">{{ assignedEnergySourcesText }}</div>
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
        <button class="btn btn-sm btn-primary" @click="handleEdit" title="Edit energy monitor"><PhPencil :size="15" /></button>
        <button class="btn btn-sm btn-error" @click="handleDelete" title="Delete energy monitor"><PhTrash :size="15" /></button>
      </div>
    </th>
  </tr>
</template>
