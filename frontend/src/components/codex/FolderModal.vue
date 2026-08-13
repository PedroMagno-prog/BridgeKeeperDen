<script setup lang="ts">
import { ref, watch } from 'vue'
import { useArticlesStore } from '@/stores/articles'

const props = defineProps<{
  show: boolean
  mode: 'create' | 'rename'
  folderId?: number | null
  parentId?: number | null
  initialName?: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'saved'): void
}>()

const articlesStore = useArticlesStore()
const folderName = ref('')
const loading = ref(false)
const errorMsg = ref('')

watch(
  () => props.show,
  (isShown) => {
    if (isShown) {
      folderName.value = props.initialName || ''
      errorMsg.value = ''
    }
  }
)

async function handleSubmit() {
  const trimmed = folderName.value.trim()
  if (!trimmed) {
    errorMsg.value = 'O nome da pasta é obrigatório.'
    return
  }

  loading.value = true
  errorMsg.value = ''

  try {
    if (props.mode === 'create') {
      await articlesStore.createNewFolder(trimmed, props.parentId || null)
    } else if (props.mode === 'rename' && props.folderId) {
      await articlesStore.renameFolder(props.folderId, trimmed)
    }
    emit('saved')
    emit('close')
  } catch (err: any) {
    errorMsg.value = err.response?.data?.detail || 'Erro ao salvar pasta.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div
    v-if="show"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4"
  >
    <div
      class="w-full max-w-md bg-stone-900 border border-stone-700/80 rounded-xl shadow-2xl p-6 text-stone-100"
    >
      <div class="flex items-center justify-between border-b border-stone-800 pb-3 mb-4">
        <h3 class="text-lg font-amber font-semibold text-amber-400 flex items-center gap-2">
          <span class="text-xl">📁</span>
          {{ mode === 'create' ? 'Nova Pasta' : 'Renomear Pasta' }}
        </h3>
        <button
          @click="emit('close')"
          class="text-stone-400 hover:text-stone-200 transition-colors text-lg"
        >
          ✕
        </button>
      </div>

      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-stone-300 mb-1">
            Nome da Pasta
          </label>
          <input
            v-model="folderName"
            type="text"
            placeholder="Ex: Grimórios, Regiões..."
            class="w-full px-3 py-2 bg-stone-950 border border-stone-700 rounded-lg text-stone-100 placeholder-stone-600 focus:outline-none focus:border-amber-500/80"
            autofocus
          />
          <p v-if="errorMsg" class="mt-1 text-xs text-rose-400">
            {{ errorMsg }}
          </p>
        </div>

        <div class="flex items-center justify-end gap-3 pt-2">
          <button
            type="button"
            @click="emit('close')"
            class="px-4 py-2 text-sm text-stone-400 hover:text-stone-200 bg-stone-800 hover:bg-stone-700 rounded-lg transition-colors"
          >
            Cancelar
          </button>
          <button
            type="submit"
            :disabled="loading"
            class="px-4 py-2 text-sm font-medium text-stone-950 bg-amber-400 hover:bg-amber-300 disabled:opacity-50 rounded-lg shadow-md transition-colors flex items-center gap-2"
          >
            <span v-if="loading" class="animate-spin text-xs">🌀</span>
            {{ mode === 'create' ? 'Criar Pasta' : 'Salvar' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
