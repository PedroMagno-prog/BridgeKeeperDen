<script setup lang="ts">
import type { AutoSaveStatus } from '@/composables/useAutoSave'

defineProps<{
  status: AutoSaveStatus
  lastSavedAt?: Date | null
}>()

const emit = defineEmits<{
  (e: 'retry'): void
}>()

function formatTime(date?: Date | null) {
  if (!date) return ''
  return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}
</script>

<template>
  <div class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-all select-none">
    <!-- Status: MODIFIED -->
    <div
      v-if="status === 'modified'"
      class="flex items-center gap-1.5 text-amber-400 bg-amber-500/10 border border-amber-500/30 px-2 py-0.5 rounded"
    >
      <span class="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
      <span>Modificado...</span>
    </div>

    <!-- Status: SAVING -->
    <div
      v-else-if="status === 'saving'"
      class="flex items-center gap-1.5 text-sky-400 bg-sky-500/10 border border-sky-500/30 px-2 py-0.5 rounded"
    >
      <span class="animate-spin text-xs">🌀</span>
      <span>Salvando...</span>
    </div>

    <!-- Status: SAVED -->
    <div
      v-else-if="status === 'saved'"
      class="flex items-center gap-1.5 text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 rounded transition-opacity duration-500"
    >
      <span class="text-xs">✓</span>
      <span>Salvo {{ lastSavedAt ? `às ${formatTime(lastSavedAt)}` : '' }}</span>
    </div>

    <!-- Status: ERROR -->
    <div
      v-else-if="status === 'error'"
      class="flex items-center gap-2 text-rose-400 bg-rose-500/10 border border-rose-500/30 px-2 py-0.5 rounded"
    >
      <span>⚠️ Erro ao salvar</span>
      <button
        @click="emit('retry')"
        class="text-xs underline hover:text-rose-200 font-semibold transition-colors"
      >
        Tentar novamente
      </button>
    </div>

    <!-- Status: IDLE -->
    <div
      v-else-if="status === 'idle' && lastSavedAt"
      class="text-stone-500 text-[11px]"
    >
      Salvo {{ formatTime(lastSavedAt) }}
    </div>
  </div>
</template>
