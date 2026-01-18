<script setup lang="ts">
import { watch, shallowRef, ref } from 'vue';
import { VueMonacoEditor } from '@guolao/vue-monaco-editor';
import { PhCopy, PhCheck } from '@phosphor-icons/vue';

interface Props {
  modelValue: string;
  readonly?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  readonly: false
});

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void;
}>();

const MONACO_EDITOR_OPTIONS = {
  automaticLayout: true,
  formatOnType: true,
  formatOnPaste: true,
  minimap: { enabled: false },
  scrollBeyondLastLine: false,
  fontSize: 14,
  lineNumbers: 'on' as const,
  readOnly: false,
  wordWrap: 'on' as const,
  theme: 'vs-dark',
  bracketPairColorization: {
    enabled: true
  }
};

const editorRef = shallowRef();
const copied = ref(false);

const handleMount = (editor: any) => {
  editorRef.value = editor;
};

const handleChange = (value: string | undefined) => {
  if (value !== undefined) {
    emit('update:modelValue', value);
  }
};

// Copy JSON to clipboard
const copyToClipboard = async () => {
  try {
    await navigator.clipboard.writeText(props.modelValue);
    copied.value = true;
    setTimeout(() => {
      copied.value = false;
    }, 2000);
  } catch (err) {
    console.error('Failed to copy:', err);
  }
};

// Update readonly option when prop changes
watch(() => props.readonly, (newReadonly) => {
  if (editorRef.value) {
    editorRef.value.updateOptions({ readOnly: newReadonly });
  }
}, { immediate: true });
</script>

<template>
  <div class="monaco-editor-wrapper">
    <div class="relative">
      <VueMonacoEditor
        :value="modelValue"
        language="json"
        :options="{ ...MONACO_EDITOR_OPTIONS, readOnly: readonly }"
        height="500px"
        @mount="handleMount"
        @change="handleChange"
      />
      <button
        @click="copyToClipboard"
        class="btn btn-sm btn-ghost absolute top-2 right-2 z-10"
        :class="{ 'btn-success': copied }"
        title="Copy JSON"
        type="button"
      >
        <PhCheck v-if="copied" :size="16" />
        <PhCopy v-else :size="16" />
        {{ copied ? 'Copied!' : 'Copy' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.monaco-editor-wrapper {
  border: 1px solid oklch(var(--bc) / 0.2);
  border-radius: 0.5rem;
  overflow: hidden;
  min-height: 500px;
}
</style>
