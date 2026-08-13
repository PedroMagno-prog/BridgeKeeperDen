<script setup lang="ts">
import type { Visibility } from '@/stores/articles'

const props = defineProps<{ visibility: Visibility; size?: 'sm' | 'md' }>()

const config: Record<Visibility, { label: string; cls: string; icon: string }> = {
  TOTAL:      { label: 'Total',      cls: 'vis--total',      icon: '⬤' },
  PARCIAL:    { label: 'Parcial',    cls: 'vis--parcial',    icon: '◐' },
  CONTROLADO: { label: 'Controlado', cls: 'vis--controlado', icon: '👤' },
  NULA:       { label: 'Nula',       cls: 'vis--nula',       icon: '○' },
}
</script>

<template>
  <span class="vis-badge" :class="[config[visibility].cls, `vis-badge--${size ?? 'sm'}`]" :title="`Visibilidade: ${config[visibility].label}`">
    <span class="vis-badge__dot">{{ config[visibility].icon }}</span>
    <span v-if="size === 'md'" class="vis-badge__label">{{ config[visibility].label }}</span>
  </span>
</template>

<style scoped>
.vis-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.65rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 2px 7px;
  border-radius: 12px;
  line-height: 1;
  vertical-align: middle;
}
.vis-badge--md { font-size: 0.7rem; padding: 3px 10px; }
.vis-badge__dot { font-size: 0.55em; }
.vis--total      { background: rgba(16, 185, 129, 0.12); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.25); }
.vis--parcial    { background: rgba(201, 168, 76, 0.12); color: var(--color-gold); border: 1px solid rgba(201, 168, 76, 0.25); }
.vis--controlado { background: rgba(59, 130, 246, 0.12); color: #3B82F6; border: 1px solid rgba(59, 130, 246, 0.25); }
.vis--nula       { background: rgba(239, 68, 68, 0.12); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.25); }
</style>
