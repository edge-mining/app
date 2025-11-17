<script setup lang="ts">
import { ref, watch } from "vue";
import type {
  ConfigSchema,
  EnergyMonitorConfig,
} from "../../core/models/energyMonitor";
import { EnergyMonitorService } from "../../core/services/energyMonitorService";

const props = defineProps<{
  adapterType: string;
}>();

const config = defineModel<EnergyMonitorConfig>({ required: true });

const service = new EnergyMonitorService();
const schema = ref<ConfigSchema | null>(null);
const loading = ref(false);

// Load schema when adapter type changes
watch(
  () => props.adapterType,
  async (newAdapterType) => {
    if (!newAdapterType) {
      schema.value = null;
      return;
    }

    loading.value = true;
    try {
      schema.value = await service.getConfigSchema(newAdapterType);

      // Initialize config with default values
      if (schema.value?.properties) {
        const newConfig: EnergyMonitorConfig = {};
        Object.entries(schema.value.properties).forEach(([key, property]) => {
          if (property.default !== undefined) {
            newConfig[key] = property.default;
          } else if (property.type === "string") {
            newConfig[key] = "";
          } else if (property.type === "number") {
            newConfig[key] = 0;
          } else if (property.type === "boolean") {
            newConfig[key] = false;
          }
        });
        config.value = newConfig;
      }
    } catch (error) {
      console.error("Failed to load config schema:", error);
      schema.value = null;
    } finally {
      loading.value = false;
    }
  },
  { immediate: true }
);

// Format field name for display
const formatFieldName = (name: string) => {
  return name
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
};

// Check if field is required
const isRequired = (fieldName: string) => {
  return schema.value?.required?.includes(fieldName) || false;
};
</script>

<template>
  <div v-if="loading" class="flex items-center justify-center p-4">
    <span class="loading loading-spinner loading-md"></span>
  </div>
  <div v-else-if="schema && schema.properties" class="flex flex-col gap-3">
    <div
      v-for="(property, fieldName) in schema.properties"
      :key="fieldName"
      class="form-control"
    >
      <label class="label">
        <span class="label-text">
          {{ property.title || formatFieldName(String(fieldName)) }}
          <span v-if="isRequired(String(fieldName))" class="text-error">*</span>
        </span>
      </label>

      <!-- String input -->
      <input
        v-if="property.type === 'string'"
        v-model="config[fieldName]"
        type="text"
        :placeholder="property.description || property.title"
        :required="isRequired(String(fieldName))"
        class="input input-bordered input-sm"
      />

      <!-- Number input -->
      <input
        v-else-if="property.type === 'number'"
        v-model.number="config[fieldName]"
        type="number"
        :placeholder="property.description || property.title"
        :required="isRequired(String(fieldName))"
        class="input input-bordered input-sm"
      />

      <!-- Boolean checkbox -->
      <div v-else-if="property.type === 'boolean'" class="form-control">
        <label class="label cursor-pointer justify-start gap-2">
          <input
            v-model="config[fieldName]"
            type="checkbox"
            class="checkbox checkbox-sm"
          />
          <span class="label-text text-xs opacity-70">
            {{ property.description }}
          </span>
        </label>
      </div>

      <!-- Description helper text for non-boolean fields -->
      <label
        v-if="property.description && property.type !== 'boolean'"
        class="label"
      >
        <span class="label-text-alt opacity-70">{{ property.description }}</span>
      </label>
    </div>
  </div>
</template>
