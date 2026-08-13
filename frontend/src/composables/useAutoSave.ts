import { ref, onUnmounted } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'

export type AutoSaveStatus = 'idle' | 'modified' | 'saving' | 'saved' | 'error'

export function useAutoSave(
  saveFn: (content: string) => Promise<void>,
  delayMs = 800
) {
  const status = ref<AutoSaveStatus>('idle')
  const lastSavedAt = ref<Date | null>(null)

  let timer: ReturnType<typeof setTimeout> | null = null
  let pendingContent: string | null = null
  let isSaving = false
  let idleTimer: ReturnType<typeof setTimeout> | null = null

  const flushSave = async () => {
    if (pendingContent === null || isSaving) return
    const contentToSave = pendingContent
    pendingContent = null

    if (timer) {
      clearTimeout(timer)
      timer = null
    }

    if (idleTimer) {
      clearTimeout(idleTimer)
      idleTimer = null
    }

    isSaving = true
    status.value = 'saving'

    try {
      await saveFn(contentToSave)
      status.value = 'saved'
      lastSavedAt.value = new Date()

      // Voltar suavemente para 'idle' após 2.5 segundos
      idleTimer = setTimeout(() => {
        if (status.value === 'saved') {
          status.value = 'idle'
        }
      }, 2500)
    } catch (err) {
      status.value = 'error'
      console.error('Erro no salvamento automático:', err)
      pendingContent = contentToSave
    } finally {
      isSaving = false
    }
  }

  const triggerChange = (newContent: string) => {
    pendingContent = newContent
    status.value = 'modified'

    if (timer) {
      clearTimeout(timer)
    }
    timer = setTimeout(flushSave, delayMs)
  }

  const resetStatus = () => {
    if (timer) {
      clearTimeout(timer)
      timer = null
    }
    if (idleTimer) {
      clearTimeout(idleTimer)
      idleTimer = null
    }
    pendingContent = null
    status.value = 'idle'
  }

  // Tenta salvar alterações pendentes antes de mudar de rota
  onBeforeRouteLeave(async () => {
    if (pendingContent !== null) {
      await flushSave()
    }
  })

  // Tenta salvar alterações pendentes ao desmontar o componente
  onUnmounted(async () => {
    if (pendingContent !== null) {
      await flushSave()
    }
  })

  return {
    status,
    lastSavedAt,
    triggerChange,
    flushSave,
    resetStatus,
  }
}
