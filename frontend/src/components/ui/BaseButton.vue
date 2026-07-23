<script setup lang="ts">
interface Props {
  variant?: 'primary' | 'ghost' | 'danger'
  type?: 'button' | 'submit' | 'reset'
  loading?: boolean
  disabled?: boolean
  fullWidth?: boolean
}

withDefaults(defineProps<Props>(), {
  variant: 'primary',
  type: 'button',
  loading: false,
  disabled: false,
  fullWidth: false,
})

const emit = defineEmits<{ click: [] }>()
</script>

<template>
  <button
    class="btn"
    :class="[`btn--${variant}`, { 'btn--full': fullWidth, 'btn--loading': loading }]"
    :type="type"
    :disabled="disabled || loading"
    @click="emit('click')"
  >
    <span v-if="loading" class="btn__spinner" aria-hidden="true" />
    <slot />
  </button>
</template>

<style scoped>
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.65rem 1.4rem;
  border-radius: var(--radius-sm);
  font-family: var(--font-body);
  font-size: 0.9rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  border: 1.5px solid transparent;
  cursor: pointer;
  transition:
    background var(--transition-fast),
    box-shadow var(--transition-fast),
    transform var(--transition-fast),
    opacity var(--transition-fast);
  user-select: none;
}

.btn:active:not(:disabled) {
  transform: translateY(1px);
}

.btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

/* Primary — gold */
.btn--primary {
  background: linear-gradient(135deg, var(--color-gold) 0%, var(--color-gold-light) 100%);
  color: #1a1400;
  border-color: var(--color-gold);
}

.btn--primary:hover:not(:disabled) {
  box-shadow: 0 0 18px var(--color-gold-glow), 0 2px 8px rgba(0,0,0,0.4);
}

/* Ghost — outline */
.btn--ghost {
  background: transparent;
  color: var(--color-text-muted);
  border-color: var(--color-border);
}

.btn--ghost:hover:not(:disabled) {
  border-color: var(--color-gold-dim);
  color: var(--color-gold);
}

/* Danger */
.btn--danger {
  background: transparent;
  color: var(--color-danger);
  border-color: var(--color-danger);
}

.btn--danger:hover:not(:disabled) {
  background: var(--color-danger-dim);
}

/* Full width */
.btn--full { width: 100%; }

/* Loading spinner */
.btn__spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }
</style>
