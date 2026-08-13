import { ref, watch, onUnmounted } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'

export type AutoSaveStatus = 'SAVED' | 'SAVING' | 'PENDING' | 'ERROR'

export function useAutoSave<T>(
  source: () => T,
  saveFn: (data: T) => Promise<void>,
  delayMs = 3000
) {
  const status = ref<AutoSaveStatus>('SAVED')
  let timer: ReturnType<typeof setTimeout> | null = null
  let pendingData: T | null = null
  let isSaving = false

  const triggerSave = async () => {
    if (!pendingData || isSaving) return
    const dataToSave = pendingData
    pendingData = null
    if (timer) {
      clearTimeout(timer)
      timer = null
    }

    isSaving = true
    status.value = 'SAVING'
    try {
      await saveFn(dataToSave)
      status.value = 'SAVED'
    } catch (err) {
      status.value = 'ERROR'
      console.error('Erro no Auto-Save:', err)
      // Restaurar pendingData se falhou para tentar novamente
      pendingData = dataToSave
    } finally {
      isSaving = false
    }
  }

  // Monitora alterações nos dados
  watch(
    source,
    (newData) => {
      if (!newData) return
      pendingData = JSON.parse(JSON.stringify(newData))
      status.value = 'PENDING'
      if (timer) clearTimeout(timer)
      timer = setTimeout(triggerSave, delayMs)
    },
    { deep: true }
  )

  // Salva imediatamente se o usuário tentar mudar de rota
  onBeforeRouteLeave(async () => {
    if (timer) clearTimeout(timer)
    if (pendingData) {
      await triggerSave()
    }
  })

  // Salva se o componente for desmontado
  onUnmounted(async () => {
    if (timer) clearTimeout(timer)
    if (pendingData) {
      await triggerSave()
    }
  })

  const resetStatus = () => {
    if (timer) {
      clearTimeout(timer)
      timer = null
    }
    pendingData = null
    status.value = 'SAVED'
  }

  return { status, triggerSave, resetStatus }
}
