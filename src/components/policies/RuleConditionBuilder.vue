<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';
import { useRuleEngineStore } from '../../core/stores/ruleEngineStore';
import type { RuleConditions, RuleCondition, LogicalGroup, RuleValidationResult, OperatorType } from '../../core/models/ruleEngine';
import { OPERATOR_SYMBOLS } from '../../core/models/ruleEngine';
import { PhCheckCircle, PhXCircle, PhCheck, PhX, PhFloppyDisk } from '@phosphor-icons/vue';

interface Props {
  modelValue: RuleConditions;
  depth?: number;
}

const props = withDefaults(defineProps<Props>(), {
  depth: 0
});

const emit = defineEmits<{
  'update:modelValue': [value: RuleConditions];
}>();

const ruleEngineStore = useRuleEngineStore();

// Only use local editing state at root level (depth === 0)
const useLocalState = computed(() => props.depth === 0);

// Local editing state (only for root level)
const localValue = ref<RuleConditions>(JSON.parse(JSON.stringify(props.modelValue)));
const hasChanges = ref(false);

// Get the current working value (local if root, props if nested)
const workingValue = computed(() => {
  return useLocalState.value ? localValue.value : props.modelValue;
});

// Initialize local value from props
onMounted(() => {
  if (useLocalState.value) {
    localValue.value = JSON.parse(JSON.stringify(props.modelValue));
  }
});

// Watch for external changes to props
watch(() => props.modelValue, (newVal) => {
  if (useLocalState.value && !hasChanges.value) {
    localValue.value = JSON.parse(JSON.stringify(newVal));
  }
}, { deep: true });

// Save changes (only at root level)
const saveChanges = () => {
  if (useLocalState.value) {
    emit('update:modelValue', JSON.parse(JSON.stringify(localValue.value)));
    hasChanges.value = false;
    validateConditions();
  }
};

// Cancel changes (only at root level)
const cancelChanges = () => {
  if (useLocalState.value) {
    localValue.value = JSON.parse(JSON.stringify(props.modelValue));
    hasChanges.value = false;
    validationResult.value = null;
  }
};

// Mark as changed (only at root level)
const markAsChanged = () => {
  if (useLocalState.value) {
    hasChanges.value = true;
  }
};

// Update working value
const updateWorkingValue = (newValue: RuleConditions) => {
  if (useLocalState.value) {
    localValue.value = newValue;
    markAsChanged();
  } else {
    emit('update:modelValue', newValue);
  }
};

// View mode toggle
const viewMode = ref<'builder' | 'json'>('builder');

// JSON string for editing
const jsonString = ref(JSON.stringify(localValue.value, null, 2));

// Validation state
const validationResult = ref<RuleValidationResult | null>(null);
const isValidating = ref(false);

// Update rule from JSON
const updateFromJson = () => {
  try {
    updateWorkingValue(JSON.parse(jsonString.value));
  } catch (e) {
    console.error('Invalid JSON:', e);
  }
};

// Update JSON from rule
const updateJson = () => {
  jsonString.value = JSON.stringify(workingValue.value, null, 2);
};

// Validate conditions using rule engine
const validateConditions = async () => {
  if (props.depth !== 0) return; // Only validate at root level
  
  isValidating.value = true;
  try {
    const result = await ruleEngineStore.validate({
      conditions: workingValue.value as RuleCondition | LogicalGroup
    });
    validationResult.value = result;
  } catch (error) {
    console.error('Validation error:', error);
    validationResult.value = {
      is_valid: false,
      validation_errors: ['Failed to validate conditions'],
      syntax_errors: [],
      field_errors: []
    };
  } finally {
    isValidating.value = false;
  }
};

// Available operators - mapped from OPERATOR_SYMBOLS
const operators = [
  { value: 'eq' as OperatorType, label: `Equal ${OPERATOR_SYMBOLS.eq}`, description: 'Equal to' },
  { value: 'ne' as OperatorType, label: `Not Equal ${OPERATOR_SYMBOLS.ne}`, description: 'Not equal to' },
  { value: 'gt' as OperatorType, label: `Greater Than ${OPERATOR_SYMBOLS.gt}`, description: 'Greater than' },
  { value: 'gte' as OperatorType, label: `Greater or Equal ${OPERATOR_SYMBOLS.gte}`, description: 'Greater than or equal to' },
  { value: 'lt' as OperatorType, label: `Less Than ${OPERATOR_SYMBOLS.lt}`, description: 'Less than' },
  { value: 'lte' as OperatorType, label: `Less or Equal ${OPERATOR_SYMBOLS.lte}`, description: 'Less than or equal to' },
  { value: 'in' as OperatorType, label: `In ${OPERATOR_SYMBOLS.in}`, description: 'Value is in list' },
  { value: 'not_in' as OperatorType, label: `Not In ${OPERATOR_SYMBOLS.not_in}`, description: 'Value is not in list' },
  { value: 'contains' as OperatorType, label: `Contains ${OPERATOR_SYMBOLS.contains}`, description: 'String contains substring' },
  { value: 'starts_with' as OperatorType, label: `Starts With ${OPERATOR_SYMBOLS.starts_with}`, description: 'String starts with' },
  { value: 'ends_with' as OperatorType, label: `Ends With ${OPERATOR_SYMBOLS.ends_with}`, description: 'String ends with' },
  { value: 'regex' as OperatorType, label: `Regex ${OPERATOR_SYMBOLS.regex}`, description: 'Matches regular expression' },
];

// Common field suggestions
const fieldSuggestions = [
  'energy_state.production',
  'energy_state.consumption',
  'energy_state.battery.state_of_charge',
  'energy_state.battery.power',
  'energy_state.grid.power',
  'miner.hashrate',
  'miner.temperature',
  'miner.power',
  'forecast.production',
  'price.electricity',
];

// Check if node is a group
const isGroup = (node: RuleConditions): node is LogicalGroup => {
  return 'any_of' in node || 'all_of' in node || 'not_' in node;
};

// Check if node is a condition
const isCondition = (node: RuleConditions): node is RuleCondition => {
  return 'field' in node && 'operator' in node && 'value' in node;
};

// Get group type
const groupType = computed(() => {
  if (isGroup(workingValue.value)) {
    if ('not_' in workingValue.value) return 'not_';
    return 'any_of' in workingValue.value ? 'any_of' : 'all_of';
  }
  return null;
});

// Get group items
const groupItems = computed(() => {
  if (isGroup(workingValue.value)) {
    const type = groupType.value as 'any_of' | 'all_of' | 'not_';
    if (type === 'not_') {
      // not_ contains a single item, not an array
      const notItem = workingValue.value.not_;
      return notItem ? [notItem] : [];
    }
    return workingValue.value[type] || [];
  }
  return [];
});

// Update condition field
const updateConditionField = (field: keyof RuleCondition, value: any) => {
  if (isCondition(workingValue.value)) {
    updateWorkingValue({
      ...workingValue.value,
      [field]: value
    });
  }
};

// Update group item
const updateGroupItem = (index: number, newValue: RuleConditions) => {
  if (isGroup(workingValue.value)) {
    const type = groupType.value as 'any_of' | 'all_of' | 'not_';
    if (type === 'not_') {
      // not_ contains a single item, not an array
      updateWorkingValue({
        not_: newValue
      });
    } else {
      const items = [...(workingValue.value[type] || [])];
      items[index] = newValue;
      updateWorkingValue({
        [type]: items
      });
    }
  }
};

// Add condition to group
const addCondition = () => {
  if (isGroup(workingValue.value)) {
    const type = groupType.value as 'any_of' | 'all_of' | 'not_';
    if (type === 'not_') {
      // not_ can only contain one item, so replace it
      updateWorkingValue({
        not_: {
          field: '',
          operator: 'eq' as OperatorType,
          value: ''
        }
      });
    } else {
      const items = [...(workingValue.value[type] || [])];
      items.push({
        field: '',
        operator: 'eq' as OperatorType,
        value: ''
      });
      updateWorkingValue({
        [type]: items
      });
    }
  }
};

// Add group to group
const addGroup = (type: 'any_of' | 'all_of' | 'not_') => {
  if (isGroup(workingValue.value)) {
    const currentType = groupType.value as 'any_of' | 'all_of' | 'not_';
    
    const newGroup = type === 'not_' 
      ? {
          [type]: {
            field: '',
            operator: 'eq' as OperatorType,
            value: ''
          }
        }
      : {
          [type]: [
            {
              field: '',
              operator: 'eq' as OperatorType,
              value: ''
            }
          ]
        };
    
    if (currentType === 'not_') {
      // not_ can only contain one item, so replace it
      updateWorkingValue(newGroup);
    } else {
      const items = [...(workingValue.value[currentType] || [])];
      items.push(newGroup);
      updateWorkingValue({
        [currentType]: items
      });
    }
  }
};

// Remove item from group
const removeItem = (index: number) => {
  if (isGroup(workingValue.value)) {
    const type = groupType.value as 'any_of' | 'all_of' | 'not_';
    if (type === 'not_') {
      // Can't remove the only item from not_, should be disabled in UI
      return;
    }
    const items = [...(workingValue.value[type] || [])];
    items.splice(index, 1);
    updateWorkingValue({
      [type]: items
    });
  }
};

// Toggle group type (any_of <-> all_of <-> not_)
const toggleGroupType = (event?: Event) => {
  if (event) {
    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation();
  }
  
  if (isGroup(workingValue.value)) {
    const currentType = groupType.value as 'any_of' | 'all_of' | 'not_';
    // Cycle: any_of -> all_of -> not_ -> any_of
    let newType: 'any_of' | 'all_of' | 'not_';
    if (currentType === 'any_of') newType = 'all_of';
    else if (currentType === 'all_of') newType = 'not_';
    else newType = 'any_of';
    
    // Preserve content but change group type
    if (currentType === 'not_') {
      // Converting from not_ (single item) to any_of/all_of (array)
      const item = workingValue.value.not_;
      updateWorkingValue({
        [newType]: item ? [item] : []
      });
    } else if (newType === 'not_') {
      // Converting to not_ (single item) from any_of/all_of (array)
      // Keep only the first item
      const items = workingValue.value[currentType] || [];
      updateWorkingValue({
        not_: items.length > 0 ? items[0] : { field: '', operator: 'eq' as OperatorType, value: '' }
      });
    } else {
      // Converting between any_of and all_of (both arrays) - preserve all items
      const items = workingValue.value[currentType] || [];
      updateWorkingValue({
        [newType]: items
      });
    }
  }
};

// Parse value based on type
const parseValue = (val: string, operator: OperatorType): string | number | boolean | Array<number | string> => {
  // For array operators (in, not_in), try to parse as JSON array
  if (operator === 'in' || operator === 'not_in') {
    try {
      const parsed = JSON.parse(val);
      if (Array.isArray(parsed)) {
        return parsed;
      }
    } catch (e) {
      // If not valid JSON, try to split by comma
      if (val.includes(',')) {
        return val.split(',').map(v => {
          const trimmed = v.trim();
          if (!isNaN(Number(trimmed)) && trimmed !== '') {
            return Number(trimmed);
          }
          return trimmed;
        });
      }
    }
  }
  
  // Try to parse as number
  if (!isNaN(Number(val)) && val !== '') {
    return Number(val);
  }
  // Try to parse as boolean
  if (val === 'true') return true;
  if (val === 'false') return false;
  // Return as string
  return val;
};
</script>

<template>
  <div class="space-y-4">
    <!-- Tabs for Builder/JSON view (only show at root level) -->
    <div v-if="depth === 0" class="space-y-4">
      <div class="flex justify-between items-center">
        <h3 class="text-lg font-semibold">Conditions</h3>
        <div class="flex gap-2 items-center">
          <!-- Save/Cancel buttons -->
          <button 
            v-if="hasChanges"
            @click="cancelChanges" 
            class="btn btn-sm btn-ghost"
          >
            <PhX :size="16" />
            Cancel
          </button>
          <button 
            v-if="hasChanges"
            @click="saveChanges" 
            class="btn btn-sm btn-primary"
          >
            <PhFloppyDisk :size="16" />
            Save
          </button>
          
          <button 
            @click="validateConditions" 
            class="btn btn-sm btn-outline"
            :disabled="isValidating"
          >
            <PhCheck v-if="!isValidating" :size="16" />
            <span v-if="isValidating" class="loading loading-spinner loading-xs"></span>
            Validate
          </button>
          <div role="tablist" class="tabs tabs-boxed">
            <a 
            role="tab" 
            class="tab"
            :class="{ 'tab-active': viewMode === 'builder' }"
            @click="viewMode = 'builder'; updateJson()"
            >
            Builder
            </a>
            <a 
            role="tab" 
            class="tab"
            :class="{ 'tab-active': viewMode === 'json' }"
            @click="viewMode = 'json'; updateJson()"
            >
            JSON
            </a>
          </div>
        </div>
      </div>

      <!-- Validation Results -->
      <div v-if="validationResult" class="alert" :class="{
        'alert-success': validationResult.is_valid,
        'alert-error': !validationResult.is_valid
      }">
        <PhCheckCircle v-if="validationResult.is_valid" :size="24" weight="fill" />
        <PhXCircle v-else :size="24" weight="fill" />
        <div class="flex-1">
          <div class="font-semibold">
            {{ validationResult.is_valid ? 'Conditions are valid' : 'Validation failed' }}
          </div>
          <div v-if="!validationResult.is_valid" class="text-sm mt-2 space-y-1">
            <div v-if="validationResult.validation_errors.length > 0">
              <div class="font-medium">Validation Errors:</div>
              <ul class="list-disc list-inside">
                <li v-for="(error, idx) in validationResult.validation_errors" :key="idx">{{ error }}</li>
              </ul>
            </div>
            <div v-if="validationResult.syntax_errors.length > 0">
              <div class="font-medium">Syntax Errors:</div>
              <ul class="list-disc list-inside">
                <li v-for="(error, idx) in validationResult.syntax_errors" :key="idx">{{ error }}</li>
              </ul>
            </div>
            <div v-if="validationResult.field_errors.length > 0">
              <div class="font-medium">Field Errors:</div>
              <ul class="list-disc list-inside">
                <li v-for="(error, idx) in validationResult.field_errors" :key="idx">{{ error }}</li>
              </ul>
            </div>
          </div>
        </div>
        <span v-if="isValidating" class="loading loading-spinner loading-sm"></span>
        <button 
          @click="validationResult = null" 
          class="btn btn-ghost btn-sm btn-circle"
          aria-label="Close validation results"
        >
          <PhX :size="20" />
        </button>
      </div>
    </div>

    <!-- JSON View (only at root level) -->
    <div v-if="depth === 0 && viewMode === 'json'">
      <textarea
        v-model="jsonString"
        @blur="updateFromJson"
        class="textarea textarea-bordered w-full font-mono text-sm"
        rows="15"
      ></textarea>
      <button @click="updateFromJson" class="btn btn-sm btn-primary mt-2">
        Apply JSON Changes
      </button>
    </div>

    <!-- Builder View -->
    <div v-if="depth > 0 || viewMode === 'builder'">
      <!-- Empty object - show initialization button -->
      <div v-if="!isCondition(workingValue) && !isGroup(workingValue)" class="text-center py-8">
        <p class="text-sm text-base-content/50 mb-4">No conditions defined</p>
        <div class="flex gap-2 justify-center">
          <button 
            @click="updateWorkingValue({ all_of: [{ field: '', operator: 'eq', value: '' }] })"
            class="btn btn-sm btn-primary"
          >
            Start with ALL OF (AND)
          </button>
          <button 
            @click="updateWorkingValue({ any_of: [{ field: '', operator: 'eq', value: '' }] })"
            class="btn btn-sm btn-secondary"
          >
            Start with ANY OF (OR)
          </button>
        </div>
      </div>
      
      <!-- Condition (leaf node) -->
      <div v-else-if="isCondition(workingValue)" class="flex gap-2 items-start">
        <div class="flex-1">
          <input
            :value="workingValue.field"
            @input="updateConditionField('field', ($event.target as HTMLInputElement).value)"
            type="text"
            placeholder="Field name (e.g., energy_state.production)"
            list="field-suggestions"
            class="input input-bordered input-sm w-full font-mono text-xs"
          />
          <datalist id="field-suggestions">
            <option v-for="field in fieldSuggestions" :key="field" :value="field" />
          </datalist>
        </div>
        
        <select
          :value="workingValue.operator"
          @change="updateConditionField('operator', ($event.target as HTMLSelectElement).value)"
          class="select select-bordered select-sm w-32"
        >
          <option v-for="op in operators" :key="op.value" :value="op.value">
            {{ op.label }}
          </option>
        </select>
        
        <input
          :value="Array.isArray(workingValue.value) ? JSON.stringify(workingValue.value) : workingValue.value"
          @input="updateConditionField('value', parseValue(($event.target as HTMLInputElement).value, workingValue.operator))"
          type="text"
          :placeholder="workingValue.operator === 'in' || workingValue.operator === 'not_in' ? '[1,2,3] or 1,2,3' : 'Value'"
          class="input input-bordered input-sm w-48"
        />
      </div>

      <!-- Group (parent node) -->
      <div v-else-if="isGroup(workingValue)" class="card bg-base-200 shadow-sm" :class="`ml-${depth * 4}`">
        <div class="card-body p-4 gap-3">
          <!-- Group header -->
          <div class="flex items-center justify-between gap-2">
            <div class="flex items-center gap-2">
              <button
                @click.prevent.stop="toggleGroupType($event)"
                type="button"
                class="btn btn-sm"
                :class="{
                  'btn-primary': groupType === 'all_of',
                  'btn-secondary': groupType === 'any_of',
                  'btn-accent': groupType === 'not_'
                }"
              >
                {{ groupType === 'all_of' ? 'ALL OF' : groupType === 'any_of' ? 'ANY OF' : 'NOT' }}
              </button>
              <span class="text-sm opacity-70">
                {{ groupType === 'all_of' ? '(AND logic)' : groupType === 'any_of' ? '(OR logic)' : '(NOT logic)' }}
              </span>
            </div>
            
            <div class="flex gap-1">
              <div class="dropdown dropdown-end">
                <label tabindex="0" class="btn btn-sm btn-ghost">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                  </svg>
                  Add
                </label>
                <ul tabindex="0" class="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-52">
                  <li><a @click="addCondition">Add Condition</a></li>
                  <li><a @click="addGroup('all_of')">Add ALL OF Group</a></li>
                  <li><a @click="addGroup('any_of')">Add ANY OF Group</a></li>
                  <li><a @click="addGroup('not_')">Add NOT Group</a></li>
                </ul>
              </div>
            </div>
          </div>

          <!-- Group items -->
          <div class="space-y-2">
            <div
              v-for="(item, index) in groupItems"
              :key="index"
              class="flex gap-2 items-start"
            >
              <div class="flex-1">
                <RuleConditionBuilder
                  :model-value="item"
                  @update:model-value="updateGroupItem(index, $event)"
                  :depth="depth + 1"
                />
              </div>
              
              <button
                @click="removeItem(index)"
                class="btn btn-sm btn-ghost btn-circle text-error"
                :disabled="groupItems.length === 1 || groupType === 'not_'"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Custom depth-based margin for nested groups */
.ml-0 { margin-left: 0; }
.ml-4 { margin-left: 1rem; }
.ml-8 { margin-left: 2rem; }
.ml-12 { margin-left: 3rem; }
.ml-16 { margin-left: 4rem; }
</style>
