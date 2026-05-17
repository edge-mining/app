<script setup lang="ts">
import { ref, watch } from "vue";
import type {
  ConfigSchema,
  PerformanceTrackerConfig,
} from "../../core/models/performanceTracker";
import { PerformanceTrackerService } from "../../core/services/performanceTrackerService";
import { PhEye, PhEyeSlash } from "@phosphor-icons/vue";

const props = defineProps<{
  adapterType: string;
}>();

const config = defineModel<PerformanceTrackerConfig>({ required: true });

const service = new PerformanceTrackerService();
const schema = ref<ConfigSchema | null>(null);
const loading = ref(false);
const secretVisibility = ref<Record<string, boolean>>({});

const resolveRef = (ref: string, schema: ConfigSchema): any => {
  if (!ref.startsWith("#/$defs/")) return null;
  const defName = ref.replace("#/$defs/", "");
  return schema.$defs?.[defName] || null;
};

const getPropertySchema = (property: any, schema: ConfigSchema): any => {
  if (property.$ref) {
    return resolveRef(property.$ref, schema);
  }

  if (property.anyOf) {
    const nonNullType = property.anyOf.find((item: any) => item.type !== "null");
    if (nonNullType) {
      if (nonNullType.$ref) {
        return resolveRef(nonNullType.$ref, schema);
      }
      return { ...property, ...nonNullType, anyOf: undefined };
    }
  }

  return property;
};

const isNullable = (property: any): boolean => {
  if (property.anyOf) {
    return property.anyOf.some((item: any) => item.type === "null");
  }
  return false;
};

const initializeDefaultValue = (property: any, schema: ConfigSchema): any => {
  if (property.default !== undefined) {
    return property.default;
  }
  const resolved = getPropertySchema(property, schema);

  if (resolved?.default !== undefined) {
    return resolved.default;
  }
  if (isNullable(property)) {
    return null;
  }
  if (resolved?.enum) {
    return resolved.enum[0];
  }
  if (resolved?.type === "string") return "";
  if (resolved?.type === "number" || resolved?.type === "integer") return 0;
  if (resolved?.type === "boolean") return false;
  return null;
};

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
      if (schema.value?.properties) {
        const existingConfig = { ...config.value };
        const newConfig: PerformanceTrackerConfig = {};
        Object.entries(schema.value.properties).forEach(([key, property]) => {
          if (existingConfig[key] !== undefined) {
            newConfig[key] = existingConfig[key];
          } else {
            newConfig[key] = initializeDefaultValue(property, schema.value!);
          }
        });
        config.value = newConfig;
      }
    } catch (error) {
      console.error("Failed to load performance tracker config schema:", error);
      schema.value = null;
    } finally {
      loading.value = false;
    }
  },
  { immediate: true }
);

const formatFieldName = (name: string) => {
  return name
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
};

const isRequired = (fieldName: string) => {
  return schema.value?.required?.includes(fieldName) || false;
};

const getFieldType = (property: any, schema: ConfigSchema) => {
  const resolved = getPropertySchema(property, schema);

  if (resolved?.enum) return "enum";
  if (resolved?.type === "object" && resolved?.properties) return "object";
  if (resolved?.type === "integer" || resolved?.type === "number") return "number";
  if (resolved?.type === "string") return "string";
  if (resolved?.type === "boolean") return "boolean";

  return "unknown";
};

const toggleSecretVisibility = (fieldKey: string) => {
  secretVisibility.value[fieldKey] = !secretVisibility.value[fieldKey];
};

const isSecretField = (fieldName: string): boolean => {
  const lower = String(fieldName).toLowerCase();
  return (
    lower.includes("password") ||
    lower.includes("token") ||
    lower.includes("secret") ||
    lower.includes("api_key") ||
    lower.includes("apikey")
  );
};
</script>

<template>
  <div v-if="loading" class="flex items-center justify-center p-4">
    <span class="loading loading-spinner loading-md"></span>
  </div>
  <div v-else-if="schema && schema.properties" class="flex flex-col gap-4">
    <div
      v-for="(property, fieldName) in schema.properties"
      :key="fieldName"
      class="space-y-1"
    >
      <div class="font-medium">
        {{ property.title || formatFieldName(String(fieldName)) }}
        <span
          v-if="isRequired(String(fieldName))"
          class="text-sm text-error opacity-60 ml-1 font-normal"
          >(required)</span
        >
        <span
          v-else
          class="text-sm opacity-60 ml-1 font-normal"
          >(optional)</span
        >
      </div>

      <!-- Enum select -->
      <select
        v-if="getFieldType(property, schema) === 'enum'"
        v-model="config[fieldName]"
        :required="isRequired(String(fieldName))"
        class="select select-bordered select-sm w-full"
      >
        <option v-if="isNullable(property)" :value="null">-- None --</option>
        <option
          v-for="option in getPropertySchema(property, schema).enum"
          :key="option"
          :value="option"
        >
          {{ option }}
        </option>
      </select>

      <!-- String input -->
      <div
        v-else-if="getFieldType(property, schema) === 'string'"
        class="relative"
      >
        <input
          v-model="config[fieldName]"
          :type="
            isSecretField(String(fieldName)) && !secretVisibility[String(fieldName)]
              ? 'password'
              : 'text'
          "
          :placeholder="property.default || ''"
          :required="isRequired(String(fieldName))"
          class="input input-bordered input-sm w-full"
          :class="{ 'pr-10': isSecretField(String(fieldName)) }"
        />
        <button
          v-if="isSecretField(String(fieldName))"
          type="button"
          class="absolute right-2 top-1/2 -translate-y-1/2 btn btn-ghost btn-xs"
          tabindex="-1"
          @click="toggleSecretVisibility(String(fieldName))"
        >
          <PhEyeSlash v-if="secretVisibility[String(fieldName)]" :size="16" />
          <PhEye v-else :size="16" />
        </button>
      </div>

      <!-- Number input -->
      <input
        v-else-if="getFieldType(property, schema) === 'number'"
        v-model.number="config[fieldName]"
        type="number"
        :step="getPropertySchema(property, schema).type === 'integer' ? '1' : 'any'"
        :min="getPropertySchema(property, schema).minimum"
        :max="getPropertySchema(property, schema).maximum"
        :placeholder="property.default"
        :required="isRequired(String(fieldName))"
        class="input input-bordered input-sm w-full"
      />

      <!-- Boolean -->
      <label
        v-else-if="getFieldType(property, schema) === 'boolean'"
        class="flex items-center gap-2 cursor-pointer"
      >
        <input
          v-model="config[fieldName]"
          type="checkbox"
          class="checkbox checkbox-sm"
        />
        <span class="text-sm">
          {{ property.description || "Enable" }}
        </span>
      </label>

      <!-- Description helper text -->
      <div
        v-if="
          property.description &&
          getFieldType(property, schema) !== 'boolean' &&
          getFieldType(property, schema) !== 'object'
        "
        class="text-sm italic opacity-70"
      >
        {{ property.description }}
      </div>
    </div>
  </div>
</template>
