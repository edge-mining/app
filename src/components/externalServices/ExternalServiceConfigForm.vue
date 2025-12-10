<script setup lang="ts">
import { ref, watch, onMounted } from "vue";
import { useExternalServiceStore } from "../../core/stores/externalServiceStore";
import type { ExternalServiceConfig, ConfigSchema } from "../../core/models/externalService";

const model = defineModel<ExternalServiceConfig>({ required: true });
const props = defineProps<{
  adapterType: string;
}>();

const externalServiceStore = useExternalServiceStore();
const schema = ref<ConfigSchema | null>(null);
const loading = ref(false);

async function loadSchema() {
  if (!props.adapterType) return;

  loading.value = true;
  try {
    const cached = externalServiceStore.configSchemas.get(props.adapterType);
    if (cached) {
      schema.value = cached;
    } else {
      schema.value = await externalServiceStore.loadConfigSchema(props.adapterType);
    }

    // Initialize model with default values if empty
    if (schema.value && Object.keys(model.value).length === 0) {
      const defaults: ExternalServiceConfig = {};
      for (const [key, prop] of Object.entries(schema.value.properties)) {
        if (prop.default !== undefined) {
          defaults[key] = prop.default;
        }
      }
      model.value = defaults;
    }
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadSchema();
});

watch(() => props.adapterType, () => {
  schema.value = null;
  model.value = {};
  loadSchema();
});

function getInputType(schemaType: string): string {
  switch (schemaType) {
    case "integer":
    case "number":
      return "number";
    case "boolean":
      return "checkbox";
    default:
      return "text";
  }
}
</script>

<template>
  <div v-if="loading" class="flex justify-center p-4">
    <span class="loading loading-spinner loading-md"></span>
  </div>

  <div v-else-if="schema" class="flex flex-col gap-3">
    <div v-for="(prop, key) in schema.properties" :key="key" class="form-control">
      <label class="label">
        <span class="label-text">
          {{ prop.title }}
          <span v-if="schema.required?.includes(String(key))" class="text-error">*</span>
        </span>
      </label>

      <template v-if="prop.type === 'boolean'">
        <input
          v-model="model[key]"
          type="checkbox"
          class="toggle toggle-primary"
        />
      </template>

      <template v-else>
        <input
          v-model="model[key]"
          :type="getInputType(prop.type)"
          :placeholder="prop.description || prop.title"
          :required="schema.required?.includes(String(key))"
          class="input input-bordered input-sm"
        />
      </template>

      <label v-if="prop.description" class="label">
        <span class="label-text-alt opacity-60">{{ prop.description }}</span>
      </label>
    </div>

    <div v-if="Object.keys(schema.properties).length === 0" class="text-center text-base-content/50 py-2">
      No configuration required for this adapter type.
    </div>
  </div>

  <div v-else class="text-center text-base-content/50 py-2">
    Select an adapter type to see configuration options.
  </div>
</template>
