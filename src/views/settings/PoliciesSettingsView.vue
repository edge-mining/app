<script setup lang="ts">
import { onMounted, ref } from "vue";
import { usePolicyStore } from "../../core/stores/policyStore";
import PolicyRow from "../../components/policies/PolicyRow.vue";
import PolicyRuleRow from "../../components/policies/PolicyRuleRow.vue";
import type { Policy, PolicyRule, PolicyCheckResult } from "../../core/models/policy";

const policyStore = usePolicyStore();

// Policy modal state
const newPolicy = ref<Policy | undefined>(undefined);
const editingPolicy = ref<Policy | undefined>(undefined);
const showPolicyModal = ref(false);
const isEditingPolicy = ref(false);

// Rule modal state
const selectedPolicy = ref<Policy | undefined>(undefined);
const newRule = ref<PolicyRule | undefined>(undefined);
const editingRule = ref<PolicyRule | undefined>(undefined);
const showRulesModal = ref(false);
const showRuleEditModal = ref(false);
const isEditingRule = ref(false);

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
    name: "",
    description: "",
    enabled: true,
    rules: [],
  };
  isEditingPolicy.value = false;
  showPolicyModal.value = true;
}

function handleEditPolicy(policy: Policy) {
  editingPolicy.value = { ...policy };
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

function handleDeletePolicy(policy: Policy) {
  policyStore.deletePolicy(policy.id!.toString()).then(() => {
    policyStore.loadPolicies();
  });
}

function handleCheckPolicy(policy: Policy) {
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
function handleManageRules(policy: Policy) {
  selectedPolicy.value = policy;
  showRulesModal.value = true;
}

function closeRulesModal() {
  showRulesModal.value = false;
  selectedPolicy.value = undefined;
}

function addRule() {
  newRule.value = {
    name: "",
    description: "",
    rule_type: "",
    conditions: {},
    actions: {},
    priority: 0,
    enabled: true,
  };
  isEditingRule.value = false;
  showRuleEditModal.value = true;
}

function handleEditRule(rule: PolicyRule) {
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
  policyStore.addRule(selectedPolicy.value.id!.toString(), newRule.value).then(() => {
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

function handleDeleteRule(rule: PolicyRule) {
  if (!selectedPolicy.value) return;
  policyStore
    .deleteRule(selectedPolicy.value.id!.toString(), rule.id!.toString())
    .then(() => {
      policyStore.loadPolicy(selectedPolicy.value!.id!.toString()).then((updatedPolicy) => {
        selectedPolicy.value = updatedPolicy;
      });
      policyStore.loadPolicies();
    });
}

function handleToggleRuleEnabled(rule: PolicyRule) {
  if (!selectedPolicy.value) return;
  const policyId = selectedPolicy.value.id!.toString();
  const ruleId = rule.id!.toString();

  const action = rule.enabled
    ? policyStore.disableRule(policyId, ruleId)
    : policyStore.enableRule(policyId, ruleId);

  action.then(() => {
    policyStore.loadPolicy(policyId).then((updatedPolicy) => {
      selectedPolicy.value = updatedPolicy;
    });
    policyStore.loadPolicies();
  });
}
</script>

<template>
  <h1 class="text-3xl font-bold">Policy Settings</h1>

  <div class="overflow-x-auto">
    <table class="table">
      <thead>
        <tr>
          <th>Name / Description</th>
          <th>Status</th>
          <th>Rules</th>
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
          <th colspan="4" class="text-center">
            <button class="btn btn-primary" @click="addPolicy">
              Add Policy
            </button>
          </th>
        </tr>
      </tbody>
      <tfoot>
        <tr>
          <th>Name / Description</th>
          <th>Status</th>
          <th>Rules</th>
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
          <div class="form-control">
            <label class="label">
              <span class="label-text">Name <span class="text-error">*</span></span>
            </label>
            <input
              v-model="editingPolicy.name"
              type="text"
              placeholder="Policy name"
              required
              class="input input-bordered"
            />
          </div>

          <div class="form-control">
            <label class="label">
              <span class="label-text">Description</span>
            </label>
            <textarea
              v-model="editingPolicy.description"
              placeholder="Policy description"
              class="textarea textarea-bordered"
              rows="3"
            ></textarea>
          </div>

          <div class="form-control">
            <label class="label cursor-pointer justify-start gap-4">
              <input
                v-model="editingPolicy.enabled"
                type="checkbox"
                class="toggle toggle-primary"
              />
              <span class="label-text">Enabled</span>
            </label>
          </div>
        </template>

        <template v-else-if="newPolicy">
          <div class="form-control">
            <label class="label">
              <span class="label-text">Name <span class="text-error">*</span></span>
            </label>
            <input
              v-model="newPolicy.name"
              type="text"
              placeholder="Policy name"
              required
              class="input input-bordered"
            />
          </div>

          <div class="form-control">
            <label class="label">
              <span class="label-text">Description</span>
            </label>
            <textarea
              v-model="newPolicy.description"
              placeholder="Policy description"
              class="textarea textarea-bordered"
              rows="3"
            ></textarea>
          </div>

          <div class="form-control">
            <label class="label cursor-pointer justify-start gap-4">
              <input
                v-model="newPolicy.enabled"
                type="checkbox"
                class="toggle toggle-primary"
              />
              <span class="label-text">Enabled</span>
            </label>
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

      <div class="overflow-x-auto">
        <table class="table table-sm">
          <thead>
            <tr>
              <th>Enabled</th>
              <th>Name / Description</th>
              <th>Type</th>
              <th>Priority</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <template v-if="selectedPolicy.rules && selectedPolicy.rules.length > 0">
              <PolicyRuleRow
                v-for="(rule, i) in selectedPolicy.rules"
                :key="rule.id"
                v-model="selectedPolicy.rules[i]"
                @edit="handleEditRule"
                @delete="handleDeleteRule"
                @toggle-enabled="handleToggleRuleEnabled"
              />
            </template>
            <tr v-else>
              <td colspan="5" class="text-center text-base-content/50">
                No rules defined for this policy
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="modal-action">
        <button class="btn btn-primary" @click="addRule">
          Add Rule
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
        {{ isEditingRule ? 'Edit Rule' : 'Add Rule' }}
      </h3>

      <form
        @submit.prevent="isEditingRule ? confirmEditRule() : confirmAddRule()"
        class="flex flex-col gap-4"
      >
        <template v-if="isEditingRule && editingRule">
          <div class="form-control">
            <label class="label">
              <span class="label-text">Name <span class="text-error">*</span></span>
            </label>
            <input
              v-model="editingRule.name"
              type="text"
              placeholder="Rule name"
              required
              class="input input-bordered"
            />
          </div>

          <div class="form-control">
            <label class="label">
              <span class="label-text">Description</span>
            </label>
            <textarea
              v-model="editingRule.description"
              placeholder="Rule description"
              class="textarea textarea-bordered"
              rows="2"
            ></textarea>
          </div>

          <div class="form-control">
            <label class="label">
              <span class="label-text">Rule Type <span class="text-error">*</span></span>
            </label>
            <input
              v-model="editingRule.rule_type"
              type="text"
              placeholder="Rule type (e.g., threshold, schedule)"
              required
              class="input input-bordered"
            />
          </div>

          <div class="form-control">
            <label class="label">
              <span class="label-text">Priority</span>
            </label>
            <input
              v-model.number="editingRule.priority"
              type="number"
              placeholder="Priority (lower = higher priority)"
              class="input input-bordered"
            />
          </div>

          <div class="form-control">
            <label class="label">
              <span class="label-text">Conditions (JSON)</span>
            </label>
            <textarea
              :value="JSON.stringify(editingRule.conditions, null, 2)"
              @input="editingRule.conditions = JSON.parse(($event.target as HTMLTextAreaElement).value || '{}')"
              placeholder='{"field": "value"}'
              class="textarea textarea-bordered font-mono text-sm"
              rows="4"
            ></textarea>
          </div>

          <div class="form-control">
            <label class="label">
              <span class="label-text">Actions (JSON)</span>
            </label>
            <textarea
              :value="JSON.stringify(editingRule.actions, null, 2)"
              @input="editingRule.actions = JSON.parse(($event.target as HTMLTextAreaElement).value || '{}')"
              placeholder='{"action": "value"}'
              class="textarea textarea-bordered font-mono text-sm"
              rows="4"
            ></textarea>
          </div>

          <div class="form-control">
            <label class="label cursor-pointer justify-start gap-4">
              <input
                v-model="editingRule.enabled"
                type="checkbox"
                class="toggle toggle-primary"
              />
              <span class="label-text">Enabled</span>
            </label>
          </div>
        </template>

        <template v-else-if="newRule">
          <div class="form-control">
            <label class="label">
              <span class="label-text">Name <span class="text-error">*</span></span>
            </label>
            <input
              v-model="newRule.name"
              type="text"
              placeholder="Rule name"
              required
              class="input input-bordered"
            />
          </div>

          <div class="form-control">
            <label class="label">
              <span class="label-text">Description</span>
            </label>
            <textarea
              v-model="newRule.description"
              placeholder="Rule description"
              class="textarea textarea-bordered"
              rows="2"
            ></textarea>
          </div>

          <div class="form-control">
            <label class="label">
              <span class="label-text">Rule Type <span class="text-error">*</span></span>
            </label>
            <input
              v-model="newRule.rule_type"
              type="text"
              placeholder="Rule type (e.g., threshold, schedule)"
              required
              class="input input-bordered"
            />
          </div>

          <div class="form-control">
            <label class="label">
              <span class="label-text">Priority</span>
            </label>
            <input
              v-model.number="newRule.priority"
              type="number"
              placeholder="Priority (lower = higher priority)"
              class="input input-bordered"
            />
          </div>

          <div class="form-control">
            <label class="label">
              <span class="label-text">Conditions (JSON)</span>
            </label>
            <textarea
              :value="JSON.stringify(newRule.conditions, null, 2)"
              @input="newRule.conditions = JSON.parse(($event.target as HTMLTextAreaElement).value || '{}')"
              placeholder='{"field": "value"}'
              class="textarea textarea-bordered font-mono text-sm"
              rows="4"
            ></textarea>
          </div>

          <div class="form-control">
            <label class="label">
              <span class="label-text">Actions (JSON)</span>
            </label>
            <textarea
              :value="JSON.stringify(newRule.actions, null, 2)"
              @input="newRule.actions = JSON.parse(($event.target as HTMLTextAreaElement).value || '{}')"
              placeholder='{"action": "value"}'
              class="textarea textarea-bordered font-mono text-sm"
              rows="4"
            ></textarea>
          </div>

          <div class="form-control">
            <label class="label cursor-pointer justify-start gap-4">
              <input
                v-model="newRule.enabled"
                type="checkbox"
                class="toggle toggle-primary"
              />
              <span class="label-text">Enabled</span>
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
