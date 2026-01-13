<script setup lang="ts">
import { onMounted, ref } from "vue";
import { usePolicyStore } from "../../core/stores/policyStore";
import PolicyRow from "../../components/policies/PolicyRow.vue";
import PolicyRuleRow from "../../components/policies/PolicyRuleRow.vue";
import type { OptimizationPolicy, AutomationRule, PolicyCheckResult } from "../../core/models/policy";
import { PhPlay, PhStop } from "@phosphor-icons/vue";

const policyStore = usePolicyStore();

// Policy modal state
const newPolicy = ref<OptimizationPolicy | undefined>(undefined);
const editingPolicy = ref<OptimizationPolicy | undefined>(undefined);
const showPolicyModal = ref(false);
const isEditingPolicy = ref(false);

// Rule modal state
const selectedPolicy = ref<OptimizationPolicy | undefined>(undefined);
const newRule = ref<AutomationRule | undefined>(undefined);
const editingRule = ref<AutomationRule | undefined>(undefined);
const showRulesModal = ref(false);
const showRuleEditModal = ref(false);
const isEditingRule = ref(false);
const activeRuleTab = ref<'start' | 'stop'>('start');
const currentRuleType = ref<'start' | 'stop'>('start');

// Check result modal state
const showCheckModal = ref(false);
const checkResult = ref<PolicyCheckResult | null>(null);
const checkingPolicyName = ref("");

onMounted(() => {
  policyStore.loadPolicies();
});

// Policy CRUD handlers
function addPolicy() {
  newPolicy.value = {
    id: "",
    name: "",
    description: "",
    start_rules: [],
    stop_rules: [],
    metadata: {
      author: undefined,
      version: undefined,
      created: undefined,
      last_modified: undefined
    }
  };
  isEditingPolicy.value = false;
  showPolicyModal.value = true;
}

function handleEditPolicy(policy: OptimizationPolicy) {
  editingPolicy.value = { 
    ...policy,
    metadata: policy.metadata || {
      author: undefined,
      version: undefined,
      created: undefined,
      last_modified: undefined
    }
  };
  isEditingPolicy.value = true;
  showPolicyModal.value = true;
}

function cancelPolicyModal() {
  newPolicy.value = undefined;
  editingPolicy.value = undefined;
  isEditingPolicy.value = false;
  showPolicyModal.value = false;
}

function confirmAddPolicy() {
  if (!newPolicy.value) return;
  policyStore.addPolicy(newPolicy.value).then(() => {
    policyStore.loadPolicies();
    newPolicy.value = undefined;
    showPolicyModal.value = false;
  });
}

function confirmEditPolicy() {
  if (!editingPolicy.value) return;
  policyStore
    .updatePolicy(editingPolicy.value.id!.toString(), editingPolicy.value)
    .then(() => {
      policyStore.loadPolicies();
      editingPolicy.value = undefined;
      isEditingPolicy.value = false;
      showPolicyModal.value = false;
    });
}

function handleDeletePolicy(policy: OptimizationPolicy) {
  policyStore.deletePolicy(policy.id!.toString()).then(() => {
    policyStore.loadPolicies();
  });
}

function handleCheckPolicy(policy: OptimizationPolicy) {
  checkingPolicyName.value = policy.name;
  policyStore.checkPolicy(policy.id!.toString()).then((result) => {
    checkResult.value = result;
    showCheckModal.value = true;
  });
}

function closeCheckModal() {
  showCheckModal.value = false;
  checkResult.value = null;
}

// Rule management handlers
function handleManageRules(policy: OptimizationPolicy) {
  selectedPolicy.value = policy;
  showRulesModal.value = true;
}

function closeRulesModal() {
  showRulesModal.value = false;
  selectedPolicy.value = undefined;
}

function addRule() {
  currentRuleType.value = activeRuleTab.value;
  newRule.value = {
    id: "",
    name: "",
    description: "",
    priority: 0,
    enabled: true,
    conditions: {},
  };
  isEditingRule.value = false;
  showRuleEditModal.value = true;
}

function handleEditRule(rule: AutomationRule, ruleType: 'start' | 'stop') {
  currentRuleType.value = ruleType;
  editingRule.value = { ...rule };
  isEditingRule.value = true;
  showRuleEditModal.value = true;
}

function cancelRuleModal() {
  newRule.value = undefined;
  editingRule.value = undefined;
  isEditingRule.value = false;
  showRuleEditModal.value = false;
}

function confirmAddRule() {
  if (!newRule.value || !selectedPolicy.value) return;
  policyStore.addRule(selectedPolicy.value.id!.toString(), currentRuleType.value, newRule.value).then(() => {
    // Reload the policy to get updated rules
    policyStore.loadPolicy(selectedPolicy.value!.id!.toString()).then((updatedPolicy) => {
      selectedPolicy.value = updatedPolicy;
    });
    policyStore.loadPolicies();
    newRule.value = undefined;
    showRuleEditModal.value = false;
  });
}

function confirmEditRule() {
  if (!editingRule.value || !selectedPolicy.value) return;
  policyStore
    .updateRule(
      selectedPolicy.value.id!.toString(),
      currentRuleType.value,
      editingRule.value.id!.toString(),
      editingRule.value
    )
    .then(() => {
      policyStore.loadPolicy(selectedPolicy.value!.id!.toString()).then((updatedPolicy) => {
        selectedPolicy.value = updatedPolicy;
      });
      policyStore.loadPolicies();
      editingRule.value = undefined;
      isEditingRule.value = false;
      showRuleEditModal.value = false;
    });
}

function handleDeleteRule(rule: AutomationRule, ruleType: 'start' | 'stop') {
  if (!selectedPolicy.value) return;
  policyStore
    .deleteRule(selectedPolicy.value.id!.toString(), ruleType, rule.id!.toString())
    .then(() => {
      policyStore.loadPolicy(selectedPolicy.value!.id!.toString()).then((updatedPolicy) => {
        selectedPolicy.value = updatedPolicy;
      });
      policyStore.loadPolicies();
    });
}

function handleToggleRuleEnabled(rule: AutomationRule, ruleType: 'start' | 'stop') {
  if (!selectedPolicy.value) return;
  const policyId = selectedPolicy.value.id!.toString();
  const ruleId = rule.id!.toString();

  const action = rule.enabled
    ? policyStore.disableRule(policyId, ruleType, ruleId)
    : policyStore.enableRule(policyId, ruleType, ruleId);

  action.then(() => {
    policyStore.loadPolicy(policyId).then((updatedPolicy) => {
      selectedPolicy.value = updatedPolicy;
    });
    policyStore.loadPolicies();
  });
}
</script>

<template>
  <h1 class="text-3xl font-bold">Optimization Policy Settings</h1>

  <div class="overflow-x-auto">
    <table class="table">
      <thead>
        <tr>
          <th>Name / Description</th>
          <th>Author</th>
          <th>Modified</th>
          <th>Start Rules</th>
          <th>Stop Rules</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <PolicyRow
          v-for="(policy, i) in policyStore.policies"
          :key="policy.id"
          v-model="policyStore.policies[i]"
          @edit="handleEditPolicy"
          @delete="handleDeletePolicy"
          @manage-rules="handleManageRules"
          @check="handleCheckPolicy"
        />

        <tr>
          <th colspan="6" class="text-center">
            <button class="btn btn-primary" @click="addPolicy">
              Add Policy
            </button>
          </th>
        </tr>
      </tbody>
      <tfoot>
        <tr>
          <th>Name / Description</th>
          <th>Author</th>
          <th>Modified</th>
          <th>Start Rules</th>
          <th>Stop Rules</th>
          <th>Actions</th>
        </tr>
      </tfoot>
    </table>
  </div>

  <!-- Policy Add/Edit Modal -->
  <dialog :class="['modal', { 'modal-open': showPolicyModal }]">
    <div v-if="newPolicy || editingPolicy" class="modal-box max-w-2xl">
      <h3 class="font-bold text-lg mb-4">
        {{ isEditingPolicy ? 'Edit Policy' : 'Add Policy' }}
      </h3>

      <form
        @submit.prevent="isEditingPolicy ? confirmEditPolicy() : confirmAddPolicy()"
        class="flex flex-col gap-4"
      >
        <template v-if="isEditingPolicy && editingPolicy">
          <!-- Name field -->
          <div class="space-y-1">
            <div class="font-medium">
              Name
              <span class="text-sm text-error opacity-60 ml-1 font-normal">(required)</span>
            </div>
            <input
              v-model="editingPolicy.name"
              type="text"
              placeholder="Policy name"
              required
              class="input input-bordered input-sm w-full"
            />
          </div>

          <div class="space-y-1">
            <div class="font-medium">Description</div>
            <textarea
              v-model="editingPolicy.description"
              placeholder="Policy description"
              class="textarea textarea-bordered textarea-sm w-full"
              rows="3"
            ></textarea>
          </div>

          <!-- Metadata Section -->
          <div class="divider text-sm">Metadata</div>

          <div class="grid grid-cols-4 gap-4">
            <div class="space-y-1">
              <div class="font-medium">Author</div>
              <div class="text-sm opacity-70">{{ editingPolicy.metadata?.author || '—' }}</div>
            </div>

            <div class="space-y-1">
              <div class="font-medium">Version</div>
              <div class="text-sm opacity-70">{{ editingPolicy.metadata?.version || '—' }}</div>
            </div>

            <div class="space-y-1">
              <div class="font-medium">Created</div>
              <div class="text-sm opacity-70">{{ editingPolicy.metadata?.created || '—' }}</div>
            </div>

            <div class="space-y-1">
              <div class="font-medium">Last Modified</div>
              <div class="text-sm opacity-70">{{ editingPolicy.metadata?.last_modified || '—' }}</div>
            </div>
          </div>
        </template>

        <template v-else-if="newPolicy">
          <div class="space-y-1">
            <div class="font-medium">
              Name
              <span class="text-sm text-error opacity-60 ml-1 font-normal">(required)</span>
            </div>
            <input
              v-model="newPolicy.name"
              type="text"
              placeholder="Policy name"
              required
              class="input input-bordered input-sm w-full"
            />
          </div>

          <div class="space-y-1">
            <div class="font-medium">Description</div>
            <textarea
              v-model="newPolicy.description"
              placeholder="Policy description"
              class="textarea textarea-bordered textarea-sm w-full"
              rows="3"
            ></textarea>
          </div>
        </template>

        <div class="modal-action">
          <button type="submit" class="btn btn-primary">
            {{ isEditingPolicy ? 'Save' : 'Add' }}
          </button>
          <button type="button" class="btn btn-secondary" @click="cancelPolicyModal">
            Cancel
          </button>
        </div>
      </form>
    </div>
    <form method="dialog" class="modal-backdrop">
      <button @click="cancelPolicyModal">close</button>
    </form>
  </dialog>

  <!-- Rules Management Modal -->
  <dialog :class="['modal', { 'modal-open': showRulesModal }]">
    <div v-if="selectedPolicy" class="modal-box max-w-4xl">
      <h3 class="font-bold text-lg mb-4">
        Rules for "{{ selectedPolicy.name }}"
      </h3>

      <!-- Tabs for Start/Stop Rules -->
      <div class="tabs tabs-lifted justify-center">
        <label class="tab">
          <input 
            type="radio" 
            name="rule_tabs" 
            :checked="activeRuleTab === 'start'"
            @change="activeRuleTab = 'start'"
          />
          <PhPlay :size="16" class="me-2" />
          Start Rules
        </label>
        <div class="tab-content bg-base-100 border-base-300 p-6">
          <div class="overflow-x-auto">
            <table class="table table-sm">
              <thead>
                <tr>
                  <th>Enabled</th>
                  <th>Name / Description</th>
                  <th>Priority</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <template v-if="selectedPolicy.start_rules && selectedPolicy.start_rules.length > 0">
                  <PolicyRuleRow
                    v-for="(rule, i) in selectedPolicy.start_rules"
                    :key="rule.id"
                    v-model="selectedPolicy.start_rules[i]"
                    @edit="(r) => handleEditRule(r, 'start')"
                    @delete="(r) => handleDeleteRule(r, 'start')"
                    @toggle-enabled="(r) => handleToggleRuleEnabled(r, 'start')"
                  />
                </template>
                <tr v-else>
                  <td colspan="4" class="text-center text-base-content/50">
                    No start rules defined for this policy
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <label class="tab">
          <input 
            type="radio" 
            name="rule_tabs"
            :checked="activeRuleTab === 'stop'"
            @change="activeRuleTab = 'stop'"
          />
          <PhStop :size="16" class="me-2" />
          Stop Rules
        </label>
        <div class="tab-content bg-base-100 border-base-300 p-6">
          <div class="overflow-x-auto">
            <table class="table table-sm">
              <thead>
                <tr>
                  <th>Enabled</th>
                  <th>Name / Description</th>
                  <th>Priority</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <template v-if="selectedPolicy.stop_rules && selectedPolicy.stop_rules.length > 0">
                  <PolicyRuleRow
                    v-for="(rule, i) in selectedPolicy.stop_rules"
                    :key="rule.id"
                    v-model="selectedPolicy.stop_rules[i]"
                    @edit="(r) => handleEditRule(r, 'stop')"
                    @delete="(r) => handleDeleteRule(r, 'stop')"
                    @toggle-enabled="(r) => handleToggleRuleEnabled(r, 'stop')"
                  />
                </template>
                <tr v-else>
                  <td colspan="4" class="text-center text-base-content/50">
                    No stop rules defined for this policy
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div class="modal-action">
        <button class="btn btn-primary" @click="addRule">
          Add {{ activeRuleTab === 'start' ? 'Start' : 'Stop' }} Rule
        </button>
        <button class="btn btn-secondary" @click="closeRulesModal">
          Close
        </button>
      </div>
    </div>
    <form method="dialog" class="modal-backdrop">
      <button @click="closeRulesModal">close</button>
    </form>
  </dialog>

  <!-- Rule Add/Edit Modal -->
  <dialog :class="['modal', { 'modal-open': showRuleEditModal }]">
    <div v-if="newRule || editingRule" class="modal-box max-w-2xl">
      <h3 class="font-bold text-lg mb-4">
        {{ isEditingRule ? 'Edit' : 'Add' }} {{ currentRuleType === 'start' ? 'Start' : 'Stop' }} Rule
      </h3>

      <form
        @submit.prevent="isEditingRule ? confirmEditRule() : confirmAddRule()"
        class="flex flex-col gap-4"
      >
        <template v-if="isEditingRule && editingRule">
          <div class="space-y-1">
            <div class="font-medium">
              Name
              <span class="text-sm text-error opacity-60 ml-1 font-normal">(required)</span>
            </div>
            <input
              v-model="editingRule.name"
              type="text"
              placeholder="Rule name"
              required
              class="input input-bordered input-sm w-full"
            />
          </div>

          <div class="space-y-1">
            <div class="font-medium">Description</div>
            <textarea
              v-model="editingRule.description"
              placeholder="Rule description"
              class="textarea textarea-bordered textarea-sm w-full"
              rows="2"
            ></textarea>
          </div>

          <div class="space-y-1">
            <div class="font-medium">Priority</div>
            <input
              v-model.number="editingRule.priority"
              type="number"
              placeholder="Priority (higher = higher priority)"
              class="input input-bordered input-sm w-full"
            />
            <div class="text-sm italic opacity-70">
              Higher values have higher priority
            </div>
          </div>

          <div class="space-y-1">
            <div class="font-medium">Conditions (JSON)</div>
            <textarea
              :value="JSON.stringify(editingRule.conditions, null, 2)"
              @input="editingRule.conditions = JSON.parse(($event.target as HTMLTextAreaElement).value || '{}')"
              placeholder='{"field": "value"}'
              class="textarea textarea-bordered textarea-sm font-mono text-sm w-full"
              rows="4"
            ></textarea>
          </div>

          <div class="space-y-1">
            <label class="label cursor-pointer justify-start gap-4 p-0">
              <input
                v-model="editingRule.enabled"
                type="checkbox"
                class="toggle toggle-primary toggle-sm"
              />
              <span class="font-medium">Enabled</span>
            </label>
          </div>
        </template>

        <template v-else-if="newRule">
          <div class="space-y-1">
            <div class="font-medium">
              Name
              <span class="text-sm text-error opacity-60 ml-1 font-normal">(required)</span>
            </div>
            <input
              v-model="newRule.name"
              type="text"
              placeholder="Rule name"
              required
              class="input input-bordered input-sm w-full"
            />
          </div>

          <div class="space-y-1">
            <div class="font-medium">Description</div>
            <textarea
              v-model="newRule.description"
              placeholder="Rule description"
              class="textarea textarea-bordered textarea-sm w-full"
              rows="2"
            ></textarea>
          </div>

          <div class="space-y-1">
            <div class="font-medium">Priority</div>
            <input
              v-model.number="newRule.priority"
              type="number"
              placeholder="Priority (higher = higher priority)"
              class="input input-bordered input-sm w-full"
            />
            <div class="text-sm italic opacity-70">
              Higher values have higher priority
            </div>
          </div>

          <div class="space-y-1">
            <div class="font-medium">Conditions (JSON)</div>
            <textarea
              :value="JSON.stringify(newRule.conditions, null, 2)"
              @input="newRule.conditions = JSON.parse(($event.target as HTMLTextAreaElement).value || '{}')"
              placeholder='{"field": "value"}'
              class="textarea textarea-bordered textarea-sm font-mono text-sm w-full"
              rows="4"
            ></textarea>
          </div>

          <div class="space-y-1">
            <label class="label cursor-pointer justify-start gap-4 p-0">
              <input
                v-model="newRule.enabled"
                type="checkbox"
                class="toggle toggle-primary toggle-sm"
              />
              <span class="font-medium">Enabled</span>
            </label>
          </div>
        </template>

        <div class="modal-action">
          <button type="submit" class="btn btn-primary">
            {{ isEditingRule ? 'Save' : 'Add' }}
          </button>
          <button type="button" class="btn btn-secondary" @click="cancelRuleModal">
            Cancel
          </button>
        </div>
      </form>
    </div>
    <form method="dialog" class="modal-backdrop">
      <button @click="cancelRuleModal">close</button>
    </form>
  </dialog>

  <!-- Policy Check Result Modal -->
  <dialog :class="['modal', { 'modal-open': showCheckModal }]">
    <div v-if="checkResult" class="modal-box">
      <h3 class="font-bold text-lg mb-4">
        Policy Check: {{ checkingPolicyName }}
      </h3>

      <div class="flex flex-col gap-4">
        <div class="alert" :class="checkResult.valid ? 'alert-success' : 'alert-error'">
          <span>{{ checkResult.valid ? 'Policy is valid' : 'Policy has issues' }}</span>
        </div>

        <div v-if="checkResult.errors && checkResult.errors.length > 0">
          <h4 class="font-semibold text-error mb-2">Errors:</h4>
          <ul class="list-disc list-inside">
            <li v-for="(error, i) in checkResult.errors" :key="i" class="text-error">
              {{ error }}
            </li>
          </ul>
        </div>

        <div v-if="checkResult.warnings && checkResult.warnings.length > 0">
          <h4 class="font-semibold text-warning mb-2">Warnings:</h4>
          <ul class="list-disc list-inside">
            <li v-for="(warning, i) in checkResult.warnings" :key="i" class="text-warning">
              {{ warning }}
            </li>
          </ul>
        </div>
      </div>

      <div class="modal-action">
        <button class="btn btn-primary" @click="closeCheckModal">
          Close
        </button>
      </div>
    </div>
    <form method="dialog" class="modal-backdrop">
      <button @click="closeCheckModal">close</button>
    </form>
  </dialog>
</template>

<style scoped></style>
