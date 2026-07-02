<script setup lang="ts">
import { computed, ref } from "vue";
import { PhEye, PhEyeSlash } from "@phosphor-icons/vue";
import {
	type ConfigSchema,
	type ConfigSchemaProperty,
	formatFieldName,
	getFieldType,
	getPropertySchema,
	getUnitOptions,
	isEntityField,
	isNullable,
	isPasswordField,
} from "../core/utils/configSchema";

const props = withDefaults(
	defineProps<{
		name: string;
		property: ConfigSchemaProperty;
		schema: ConfigSchema;
		required?: boolean;
		/** If true, string entity fields get a "sensor." prefix (Home Assistant). */
		sensorPrefix?: boolean;
		/** Hide the field label (used when rendered inline as another field's addon). */
		hideLabel?: boolean;
		/** Hide the helper/description text. */
		hideDescription?: boolean;
	}>(),
	{ required: false, sensorPrefix: false, hideLabel: false, hideDescription: false }
);

const value = defineModel<any>();

const SENSOR_PREFIX = "sensor.";

const fieldType = computed(() => getFieldType(props.property, props.schema));
const resolved = computed(() => getPropertySchema(props.property, props.schema));

const isSensorEntityField = computed(
	() => props.sensorPrefix && isEntityField(props.name)
);

// Unit fields (issue #18): render a segmented control instead of free text.
const unitOptions = computed<string[] | null>(() => {
	if (fieldType.value !== "string" || isSensorEntityField.value) return null;
	return getUnitOptions(props.name, props.property, value.value);
});

const showDescription = computed(
	() =>
		!props.hideDescription &&
		!!props.property.description &&
		fieldType.value !== "boolean" &&
		fieldType.value !== "object"
);

// ── Sensor entity (Home Assistant "sensor." prefix) ─────────────

const entityDisplayValue = computed(() => {
	const val = String(value.value ?? "");
	return val.startsWith(SENSOR_PREFIX) ? val.slice(SENSOR_PREFIX.length) : val;
});

const onEntityInput = (event: Event) => {
	const v = (event.target as HTMLInputElement).value;
	value.value = v ? SENSOR_PREFIX + v : "";
};

// ── Nested object fields ────────────────────────────────────────

const nestedEntityDisplayValue = (key: string) => {
	const val = String(value.value?.[key] ?? "");
	return val.startsWith(SENSOR_PREFIX) ? val.slice(SENSOR_PREFIX.length) : val;
};

const onNestedEntityInput = (key: string, event: Event) => {
	const v = (event.target as HTMLInputElement).value;
	if (value.value) value.value[key] = v ? SENSOR_PREFIX + v : "";
};

// ── Password visibility ─────────────────────────────────────────

const passwordVisibility = ref<Record<string, boolean>>({});
const togglePassword = (key: string) => {
	passwordVisibility.value[key] = !passwordVisibility.value[key];
};
</script>

<template>
	<div class="space-y-1">
		<!-- Field label -->
		<div v-if="!hideLabel" class="font-medium">
			{{ property.title || formatFieldName(name) }}
			<span v-if="required" class="text-sm text-error opacity-60 ml-1 font-normal">(required)</span>
			<span v-else class="text-sm opacity-60 ml-1 font-normal">(optional)</span>
		</div>

		<div class="flex items-start gap-3">
			<div class="flex-1 min-w-0">
				<!-- Enum -->
				<select
					v-if="fieldType === 'enum'"
					v-model="value"
					:required="required"
					class="select select-bordered select-sm w-full"
				>
					<option v-if="isNullable(property)" :value="null">-- None --</option>
					<option v-for="option in resolved.enum" :key="option" :value="option">{{ option }}</option>
				</select>

				<!-- Object (nested) -->
				<div
					v-else-if="fieldType === 'object'"
					class="border border-base-300 rounded-lg p-3 space-y-3"
				>
					<div
						v-for="(nestedProp, nestedKey) in resolved.properties"
						:key="nestedKey"
						class="space-y-1"
					>
						<div class="font-medium text-sm">
							{{ nestedProp.title || formatFieldName(String(nestedKey)) }}
						</div>

						<!-- Nested sensor entity -->
						<div
							v-if="nestedProp.type === 'string' && sensorPrefix && isEntityField(String(nestedKey))"
							class="join w-full"
						>
							<span class="join-item flex items-center px-2 bg-base-200 border border-base-300 text-xs opacity-70 select-none">sensor.</span>
							<input
								:value="nestedEntityDisplayValue(String(nestedKey))"
								@input="onNestedEntityInput(String(nestedKey), $event)"
								type="text"
								placeholder="entity_id"
								class="input input-bordered input-xs join-item flex-1"
							/>
						</div>

						<!-- Nested string -->
						<div v-else-if="nestedProp.type === 'string'" class="relative">
							<input
								v-model="value[nestedKey]"
								:type="isPasswordField(String(nestedKey)) && !passwordVisibility[String(nestedKey)] ? 'password' : 'text'"
								:placeholder="nestedProp.default || ''"
								class="input input-bordered input-xs w-full"
								:class="{ 'pr-10': isPasswordField(String(nestedKey)) }"
							/>
							<button
								v-if="isPasswordField(String(nestedKey))"
								type="button"
								@click="togglePassword(String(nestedKey))"
								class="absolute right-2 top-1/2 -translate-y-1/2 btn btn-ghost btn-xs"
								tabindex="-1"
							>
								<PhEyeSlash v-if="passwordVisibility[String(nestedKey)]" :size="16" />
								<PhEye v-else :size="16" />
							</button>
						</div>

						<!-- Nested number -->
						<input
							v-else-if="nestedProp.type === 'number' || nestedProp.type === 'integer'"
							v-model.number="value[nestedKey]"
							type="number"
							:step="nestedProp.type === 'integer' ? '1' : 'any'"
							:min="nestedProp.minimum"
							:max="nestedProp.maximum"
							:placeholder="nestedProp.default || ''"
							class="input input-bordered input-xs w-full"
						/>

						<div v-if="nestedProp.description" class="text-xs italic opacity-70">
							{{ nestedProp.description }}
						</div>
					</div>
				</div>

				<!-- Unit segmented control (issue #18) -->
				<div v-else-if="unitOptions" class="join">
					<button
						v-for="option in unitOptions"
						:key="option"
						type="button"
						class="btn btn-sm join-item"
						:class="value === option ? 'btn-primary' : 'btn-ghost border border-base-300'"
						:aria-pressed="value === option"
						@click="value = option"
					>{{ option }}</button>
				</div>

				<!-- String with sensor prefix -->
				<div
					v-else-if="fieldType === 'string' && isSensorEntityField"
					class="join w-full"
				>
					<span class="join-item flex items-center px-3 bg-base-200 border border-base-300 text-sm opacity-70 select-none">sensor.</span>
					<input
						:value="entityDisplayValue"
						@input="onEntityInput"
						type="text"
						placeholder="entity_id"
						:required="required"
						class="input input-bordered input-sm join-item flex-1"
					/>
				</div>

				<!-- String -->
				<div v-else-if="fieldType === 'string'" class="relative">
					<input
						v-model="value"
						:type="isPasswordField(name) && !passwordVisibility[name] ? 'password' : 'text'"
						:placeholder="property.default || ''"
						:required="required"
						class="input input-bordered input-sm w-full"
						:class="{ 'pr-10': isPasswordField(name) }"
					/>
					<button
						v-if="isPasswordField(name)"
						type="button"
						@click="togglePassword(name)"
						class="absolute right-2 top-1/2 -translate-y-1/2 btn btn-ghost btn-xs"
						tabindex="-1"
					>
						<PhEyeSlash v-if="passwordVisibility[name]" :size="16" />
						<PhEye v-else :size="16" />
					</button>
				</div>

				<!-- Number -->
				<input
					v-else-if="fieldType === 'number'"
					v-model.number="value"
					type="number"
					:step="resolved.type === 'integer' ? '1' : 'any'"
					:min="resolved.minimum"
					:max="resolved.maximum"
					:placeholder="property.default"
					:required="required"
					class="input input-bordered input-sm w-full"
				/>

				<!-- Boolean -->
				<label
					v-else-if="fieldType === 'boolean'"
					class="flex items-center gap-2 cursor-pointer"
				>
					<input v-model="value" type="checkbox" class="checkbox checkbox-sm" />
					<span class="text-sm">{{ property.description || "Enable" }}</span>
				</label>
			</div>

			<!-- Inline addon (e.g. the paired unit-of-measure control) -->
			<div v-if="$slots.addon" class="shrink-0">
				<slot name="addon" />
			</div>
		</div>

		<!-- Description -->
		<div v-if="showDescription" class="text-sm italic opacity-70">
			{{ property.description }}
		</div>
	</div>
</template>
