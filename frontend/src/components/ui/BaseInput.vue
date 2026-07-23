<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  id: string
  label: string
  modelValue: string
  type?: string
  placeholder?: string
  error?: string
  disabled?: boolean
  hint?: string
}

const props = withDefaults(defineProps<Props>(), {
  type: 'text',
  placeholder: '',
  error: '',
  disabled: false,
  hint: '',
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const hasError = computed(() => !!props.error)
</script>

<template>
  <div class="field">
    <label :for="id" class="field__label">{{ label }}</label>
    <input
      :id="id"
      class="field__input"
      :class="{ 'field__input--error': hasError }"
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    />
    <span v-if="hasError" class="field__error">{{ error }}</span>
    <span v-else-if="hint" class="field__hint">{{ hint }}</span>
  </div>
</template>

<style scoped>
.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field__label {
  font-family: var(--font-body);
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--color-text-muted);
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.field__input {
  width: 100%;
  padding: 0.65rem 0.9rem;
  background: var(--color-surface);
  border: 1.5px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text);
  font-family: var(--font-body);
  font-size: 0.95rem;
  outline: none;
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.field__input::placeholder {
  color: var(--color-text-dim);
}

.field__input:focus {
  border-color: var(--color-gold);
  box-shadow: 0 0 0 3px var(--color-gold-glow);
}

.field__input--error {
  border-color: var(--color-danger);
  box-shadow: 0 0 0 3px var(--color-danger-dim);
}

.field__input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.field__error {
  font-size: 0.78rem;
  color: var(--color-danger);
  display: flex;
  align-items: center;
  gap: 4px;
}

.field__error::before {
  content: '⚠';
  font-size: 0.7rem;
}

.field__hint {
  font-size: 0.78rem;
  color: var(--color-text-dim);
}
</style>
