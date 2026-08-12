<script setup lang="ts">
/**
 * Modal para o Mestre criar ou editar um Mapa do Mundo.
 */
import { ref, watch } from 'vue'
import { useMapsStore, type MapItem } from '@/stores/maps'

const props = defineProps<{
  show: boolean
  mapItem?: MapItem | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'save', map: MapItem): void
}>()

const mapsStore = useMapsStore()

const title = ref('')
const imageUrl = ref('')
const saving = ref(false)

watch(
  () => props.show,
  (show) => {
    if (show) {
      const mapItem = props.mapItem
      if (mapItem) {
        title.value = mapItem.title
        imageUrl.value = mapItem.image_url
      } else {
        title.value = ''
        imageUrl.value = ''
      }
    }
  },
  { immediate: true }
)

async function handleSave() {
  if (!title.value.trim() || !imageUrl.value.trim()) return
  saving.value = true
  try {
    let saved: MapItem | undefined
    if (props.mapItem) {
      saved = await mapsStore.updateMap(props.mapItem.id, {
        title: title.value.trim(),
        image_url: imageUrl.value.trim(),
      })
    } else {
      saved = await mapsStore.createMap(title.value.trim(), imageUrl.value.trim())
    }
    if (saved) {
      emit('save', saved)
    }
    emit('close')
  } catch (err: any) {
    alert(err?.response?.data?.detail || 'Erro ao salvar mapa.')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="show" class="modal-overlay" @click.self="emit('close')">
        <div class="modal">
          <h3 class="modal-title">{{ mapItem ? 'Editar Mapa' : 'Novo Mapa do Mundo' }}</h3>

          <div class="form-group">
            <label>Título do Mapa</label>
            <input v-model="title" type="text" class="form-input" placeholder="Ex: Continente de Valoria" autofocus />
          </div>

          <div class="form-group">
            <label>URL da Imagem de Fundo (High-Res WebP/JPG)</label>
            <input v-model="imageUrl" type="text" class="form-input" placeholder="https://exemplo.com/mapa.webp" />
          </div>

          <div v-if="imageUrl.trim()" class="image-preview">
            <span class="preview-label">Pré-visualização da Imagem:</span>
            <img :src="imageUrl" alt="Preview" class="preview-img" @error="imageUrl = ''" />
          </div>

          <div class="modal-actions">
            <button class="btn btn-ghost" @click="emit('close')">Cancelar</button>
            <button class="btn btn-gold" @click="handleSave" :disabled="saving || !title.trim() || !imageUrl.trim()">
              {{ saving ? 'Salvando...' : 'Salvar Mapa' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  z-index: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(4px);
}

.modal {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-6);
  width: 100%;
  max-width: 440px;
  box-shadow: var(--shadow-lg);
}

.modal-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-gold);
  margin-bottom: var(--space-4);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: var(--space-4);
}

.form-group label {
  font-size: 0.75rem;
  color: var(--color-text-dim);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.form-input {
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 8px 12px;
  color: var(--color-text);
  font-family: var(--font-body);
  font-size: 0.85rem;
  outline: none;
}
.form-input:focus { border-color: var(--color-gold); }

.image-preview {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: var(--space-4);
}

.preview-label {
  font-size: 0.7rem;
  color: var(--color-text-dim);
}

.preview-img {
  width: 100%;
  max-height: 140px;
  object-fit: cover;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
  margin-top: var(--space-5);
}

.btn {
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
}
.btn-ghost { background: none; color: var(--color-text-muted); border: 1px solid var(--color-border); }
.btn-gold { background: var(--color-gold); color: #111827; }
</style>
