<script setup lang="ts">
import { ref, computed } from 'vue';

interface Condition {
  field: string;
  operator: string;
  value: string | number | boolean;
}

interface Group {
  any_of?: (Condition | Group)[];
  all_of?: (Condition | Group)[];
}

type RuleNode = Condition | Group;

interface Props {
  modelValue: RuleNode;
  depth?: number;
}

const props = withDefaults(defineProps<Props>(), {
  depth: 0
});

const emit = defineEmits<{
  'update:modelValue': [value: RuleNode];
}>();

// View mode toggle
const viewMode = ref<'builder' | 'json'>('builder');

// JSON string for editing
const jsonString = ref(JSON.stringify(props.modelValue, null, 2));

// Update rule from JSON
const updateFromJson = () => {
  try {
    emit('update:modelValue', JSON.parse(jsonString.value));
  } catch (e) {
    console.error('Invalid JSON:', e);
  }
};

// Update JSON from rule
const updateJson = () => {
  jsonString.value = JSON.stringify(props.modelValue, null, 2);
};

// Available operators
const operators = [
  { value: 'eq', label: 'Equal (=)' },
  { value: 'ne', label: 'Not Equal (≠)' },
  { value: 'gt', label: 'Greater Than (>)' },
  { value: 'gte', label: 'Greater or Equal (≥)' },
  { value: 'lt', label: 'Less Than (<)' },
  { value: 'lte', label: 'Less or Equal (≤)' },
  { value: 'contains', label: 'Contains' },
  { value: 'in', label: 'In' },
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
const isGroup = (node: RuleNode): node is Group => {
  return 'any_of' in node || 'all_of' in node;
};

// Check if node is a condition
const isCondition = (node: RuleNode): node is Condition => {
  return 'field' in node && 'operator' in node && 'value' in node;
};

// Get group type
const groupType = computed(() => {
  if (isGroup(props.modelValue)) {
    return 'any_of' in props.modelValue ? 'any_of' : 'all_of';
  }
  return null;
});

// Get group items
const groupItems = computed(() => {
  if (isGroup(props.modelValue)) {
    return props.modelValue[groupType.value as 'any_of' | 'all_of'] || [];
  }
  return [];
});

// Update condition field
const updateConditionField = (field: keyof Condition, value: any) => {
  if (isCondition(props.modelValue)) {
    emit('update:modelValue', {
      ...props.modelValue,
      [field]: value
    });
  }
};

// Update group item
const updateGroupItem = (index: number, newValue: RuleNode) => {
  if (isGroup(props.modelValue)) {
    const type = groupType.value as 'any_of' | 'all_of';
    const items = [...(props.modelValue[type] || [])];
    items[index] = newValue;
    emit('update:modelValue', {
      [type]: items
    });
  }
};

// Add condition to group
const addCondition = () => {
  if (isGroup(props.modelValue)) {
    const type = groupType.value as 'any_of' | 'all_of';
    const items = [...(props.modelValue[type] || [])];
    items.push({
      field: '',
      operator: 'eq',
      value: ''
    });
    emit('update:modelValue', {
      [type]: items
    });
  }
};

// Add group to group
const addGroup = (type: 'any_of' | 'all_of') => {
  if (isGroup(props.modelValue)) {
    const currentType = groupType.value as 'any_of' | 'all_of';
    const items = [...(props.modelValue[currentType] || [])];
    items.push({
      [type]: [
        {
          field: '',
          operator: 'eq',
          value: ''
        }
      ]
    });
    emit('update:modelValue', {
      [currentType]: items
    });
  }
};

// Remove item from group
const removeItem = (index: number) => {
  if (isGroup(props.modelValue)) {
    const type = groupType.value as 'any_of' | 'all_of';
    const items = [...(props.modelValue[type] || [])];
    items.splice(index, 1);
    emit('update:modelValue', {
      [type]: items
    });
  }
};

// Toggle group type (any_of <-> all_of)
const toggleGroupType = () => {
  if (isGroup(props.modelValue)) {
    const currentType = groupType.value as 'any_of' | 'all_of';
    const newType = currentType === 'any_of' ? 'all_of' : 'any_of';
    const items = props.modelValue[currentType] || [];
    emit('update:modelValue', {
      [newType]: items
    });
  }
};

// Parse value based on type
const parseValue = (val: string): string | number | boolean => {
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
    <div v-if="depth === 0" class="flex justify-between items-center">
        <h3 class="text-lg font-semibold">Conditions</h3>
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
      <div v-if="!isCondition(modelValue) && !isGroup(modelValue)" class="text-center py-8">
        <p class="text-sm text-base-content/50 mb-4">No conditions defined</p>
        <div class="flex gap-2 justify-center">
          <button 
            @click="emit('update:modelValue', { all_of: [{ field: '', operator: 'eq', value: '' }] })"
            class="btn btn-sm btn-primary"
          >
            Start with ALL OF (AND)
          </button>
          <button 
            @click="emit('update:modelValue', { any_of: [{ field: '', operator: 'eq', value: '' }] })"
            class="btn btn-sm btn-secondary"
          >
            Start with ANY OF (OR)
          </button>
        </div>
      </div>
      
      <!-- Condition (leaf node) -->
      <div v-else-if="isCondition(modelValue)" class="flex gap-2 items-start">
        <div class="flex-1">
          <input
            :value="modelValue.field"
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
          :value="modelValue.operator"
          @change="updateConditionField('operator', ($event.target as HTMLSelectElement).value)"
          class="select select-bordered select-sm w-32"
        >
          <option v-for="op in operators" :key="op.value" :value="op.value">
            {{ op.label }}
          </option>
        </select>
        
        <input
          :value="modelValue.value"
          @input="updateConditionField('value', parseValue(($event.target as HTMLInputElement).value))"
          type="text"
          placeholder="Value"
          class="input input-bordered input-sm w-32"
        />
      </div>

      <!-- Group (parent node) -->
      <div v-else-if="isGroup(modelValue)" class="card bg-base-200 shadow-sm" :class="`ml-${depth * 4}`">
        <div class="card-body p-4 gap-3">
          <!-- Group header -->
          <div class="flex items-center justify-between gap-2">
            <div class="flex items-center gap-2">
              <button
                @click="toggleGroupType"
                class="btn btn-sm"
                :class="groupType === 'all_of' ? 'btn-primary' : 'btn-secondary'"
              >
                {{ groupType === 'all_of' ? 'ALL OF' : 'ANY OF' }}
              </button>
              <span class="text-sm opacity-70">
                {{ groupType === 'all_of' ? '(AND logic)' : '(OR logic)' }}
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
                :disabled="groupItems.length === 1"
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
