<script setup lang="ts">
import { computed, ref } from "vue";
import { PhEye, PhEyeSlash } from "@phosphor-icons/vue";
import {
	type ConfigSchema,
	type ConfigSchemaProperty,
	formatFieldName,
	getEntityDomainOptions,
	getEntityPrefix,
	getFieldType,
	getPropertySchema,
	getUnitOptions,
	isEntityField,
	isNullable,
	isPasswordField,
	stripEntityPrefix,
} from "../core/utils/configSchema";

const props = withDefaults(
	defineProps<{
		name: string;
		property: ConfigSchemaProperty;
		schema: ConfigSchema;
		required?: boolean;
		/** If true, string entity fields get a fixed Home Assistant domain prefix
		 *  chip (e.g. "sensor.", "switch."), derived per field from its default. */
		sensorPrefix?: boolean;
		/** Hide the field label (used when rendered inline as another field's addon). */
		hideLabel?: boolean;
		/** Hide the helper/description text. */
		hideDescription?: boolean;
	}>(),
	{ required: false, sensorPrefix: false, hideLabel: false, hideDescription: false }
);

const value = defineModel<any>();

const fieldType = computed(() => getFieldType(props.property, props.schema));
const resolved = computed(() => getPropertySchema(props.property, props.schema));

const isSensorEntityField = computed(
	() => props.sensorPrefix && isEntityField(props.name)
);

// Home Assistant entity-domain prefix (e.g. "sensor.", "switch.") shown as a
// selectable dropdown. It defaults to the domain derived from the field's
// current value / default / name, but the user can override it; the override
// is sticky even while the entity object id is empty.
const domainOverride = ref<string | null>(null);

const entityPrefix = computed(
	() => domainOverride.value ?? getEntityPrefix(props.name, props.property, value.value)
);

const entityDomain = computed<string>({
	get: () => entityPrefix.value,
	set: (newPrefix: string) => {
		const objectId = stripEntityPrefix(value.value, entityPrefix.value);
		domainOverride.value = newPrefix;
		value.value = objectId ? newPrefix + objectId : "";
	},
});

const entityDomainOptions = computed(() => getEntityDomainOptions(entityPrefix.value));

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

// ── Entity with fixed Home Assistant domain prefix ──────────────

const entityDisplayValue = computed(() =>
	stripEntityPrefix(value.value, entityPrefix.value)
);

const onEntityInput = (event: Event) => {
	const v = (event.target as HTMLInputElement).value;
	value.value = v ? entityPrefix.value + v : "";
};

// ── Nested object fields ────────────────────────────────────────

const nestedEntityPrefix = (key: string, nestedProp: ConfigSchemaProperty) =>
	getEntityPrefix(key, nestedProp, value.value?.[key]);

const nestedEntityDisplayValue = (key: string, nestedProp: ConfigSchemaProperty) =>
	stripEntityPrefix(value.value?.[key], nestedEntityPrefix(key, nestedProp));

const onNestedEntityInput = (
	key: string,
	nestedProp: ConfigSchemaProperty,
	event: Event
) => {
	const v = (event.target as HTMLInputElement).value;
	if (value.value) value.value[key] = v ? nestedEntityPrefix(key, nestedProp) + v : "";
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

						<!-- Nested entity with fixed domain prefix -->
						<div
							v-if="nestedProp.type === 'string' && sensorPrefix && isEntityField(String(nestedKey))"
							class="join w-full"
						>
							<span class="join-item flex items-center px-2 bg-base-200 border border-base-300 text-xs opacity-70 select-none">{{ nestedEntityPrefix(String(nestedKey), nestedProp) }}</span>
							<input
								:value="nestedEntityDisplayValue(String(nestedKey), nestedProp)"
								@input="onNestedEntityInput(String(nestedKey), nestedProp, $event)"
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

				<!-- String entity with selectable Home Assistant domain prefix -->
				<div
					v-else-if="fieldType === 'string' && isSensorEntityField"
					class="join w-full"
				>
					<select
						v-model="entityDomain"
						class="select select-bordered select-sm join-item w-fit bg-base-200 opacity-80"
						aria-label="Entity domain"
					>
						<option v-for="domain in entityDomainOptions" :key="domain" :value="domain">{{ domain }}</option>
					</select>
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
