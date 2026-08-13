<script setup lang="ts">
/**
 * Modal para o Mestre criar ou editar um Marcador de Mapa (Pin).
 */
import { ref, computed, watch } from 'vue'
import { useMapsStore, type MapPin, type MapLayer, type MapItem } from '@/stores/maps'
import { useArticlesStore, type MentionSuggestion, type Visibility } from '@/stores/articles'
import { useWorldsStore } from '@/stores/worlds'
import VisibilityBadge from '@/components/ui/VisibilityBadge.vue'

const props = defineProps<{
  show: boolean
  mapId: string
  pin?: MapPin | null
  layers: MapLayer[]
  maps: MapItem[]
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'save'): void
}>()

const mapsStore = useMapsStore()
const articlesStore = useArticlesStore()
const worldsStore = useWorldsStore()
const isMestre = computed(() => worldsStore.isMestre)

const title = ref('')
const icon = ref('city')
const color = ref('#EAB308')
const visibility = ref<Visibility>('NULA')
const layerId = ref<string | null>(null)
const linkType = ref<'NONE' | 'ARTICLE' | 'MAP'>('NONE')
const targetArticleId = ref<string | null>(null)
const targetArticleTitle = ref('')
const targetMapId = ref<string | null>(null)

const articleSearch = ref('')
const articleSuggestions = ref<MentionSuggestion[]>([])
const showArticleDropdown = ref(false)
const saving = ref(false)

const ICON_OPTIONS = [
  { id: 'city', label: 'Cidade', emoji: '🏙️' },
  { id: 'castle', label: 'Castelo', emoji: '🏰' },
  { id: 'dungeon', label: 'Masmorra', emoji: '🗝️' },
  { id: 'ruins', label: 'Ruínas', emoji: '🏛️' },
  { id: 'cave', label: 'Caverna', emoji: '⛰️' },
  { id: 'tavern', label: 'Taverna', emoji: '🍺' },
  { id: 'poi', label: 'Ponto de Interesse', emoji: '📍' },
  { id: 'monster', label: 'Perigo / Monstro', emoji: '👾' },
]

const COLOR_OPTIONS = ['#EAB308', '#EF4444', '#3B82F6', '#10B981', '#8B5CF6', '#F97316', '#EC4899', '#6B7280']

watch(
  () => props.show,
  (show) => {
    if (show) {
      const pin = props.pin
      if (pin) {
        title.value = pin.title
        icon.value = pin.icon || 'city'
        color.value = pin.color || '#EAB308'
        visibility.value = pin.visibility
        layerId.value = pin.layer_id
        if (pin.target_article_id) {
          linkType.value = 'ARTICLE'
          targetArticleId.value = pin.target_article_id
          targetArticleTitle.value = pin.target_article?.title || 'Artigo Selecionado'
        } else if (pin.target_map_id) {
          linkType.value = 'MAP'
          targetMapId.value = pin.target_map_id
        } else {
          linkType.value = 'NONE'
        }
      } else {
        title.value = ''
        icon.value = 'city'
        color.value = '#EAB308'
        visibility.value = isMestre.value ? 'NULA' : 'CONTROLADO'
        layerId.value = props.layers[0]?.id || null
        linkType.value = 'NONE'
        targetArticleId.value = null
        targetArticleTitle.value = ''
        targetMapId.value = null
      }
    }
  },
  { immediate: true }
)

async function handleArticleSearch(e: Event) {
  const q = (e.target as HTMLInputElement).value
  articleSearch.value = q
  if (q.trim()) {
    articleSuggestions.value = await articlesStore.searchMentions(q)
    showArticleDropdown.value = articleSuggestions.value.length > 0
  } else {
    showArticleDropdown.value = false
  }
}

function selectArticle(item: MentionSuggestion) {
  targetArticleId.value = item.id
  targetArticleTitle.value = item.title
  articleSearch.value = item.title
  showArticleDropdown.value = false
}

async function handleSave() {
  if (!title.value.trim()) return
  saving.value = true
  try {
    const payload: Partial<MapPin> = {
      title: title.value.trim(),
      icon: icon.value,
      color: color.value,
      visibility: visibility.value,
      layer_id: layerId.value || null,
      target_article_id: linkType.value === 'ARTICLE' ? targetArticleId.value : null,
      target_map_id: linkType.value === 'MAP' ? targetMapId.value : null,
    }

    if (props.pin) {
      await mapsStore.updatePin(props.mapId, props.pin.id, payload)
    } else {
      // Posição inicial no centro
      payload.x_position = 50.0
      payload.y_position = 50.0
      await mapsStore.createPin(props.mapId, payload)
    }
    emit('save')
    emit('close')
  } catch (err: any) {
    alert(err?.response?.data?.detail || 'Erro ao salvar marcador.')
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
          <h3 class="modal-title">{{ pin ? 'Editar Marcador' : 'Novo Marcador de Mapa' }}</h3>

          <div class="form-group">
            <label>Título do Local</label>
            <input v-model="title" type="text" class="form-input" placeholder="Ex: Cidade de Thanatos" autofocus />
          </div>

          <div class="form-row">
            <div class="form-group flex-1">
              <label>Ícone</label>
              <select v-model="icon" class="form-input">
                <option v-for="opt in ICON_OPTIONS" :key="opt.id" :value="opt.id">
                  {{ opt.emoji }} {{ opt.label }}
                </option>
              </select>
            </div>

            <div v-if="isMestre" class="form-group flex-1">
              <label>Visibilidade (Névoa)</label>
              <select v-model="visibility" class="form-input">
                <option value="NULA">Nula</option>
                <option value="PARCIAL">Parcial</option>
                <option value="TOTAL">Total</option>
              </select>
            </div>
          </div>

          <!-- Seletor de Cor -->
          <div class="form-group">
            <label>Cor de Destaque</label>
            <div class="color-picker-row">
              <button
                v-for="c in COLOR_OPTIONS"
                :key="c"
                class="color-btn"
                :class="{ 'color-btn--active': color === c }"
                :style="{ backgroundColor: c }"
                @click="color = c"
              ></button>
            </div>
          </div>

          <!-- Seletor de Camada -->
          <div v-if="layers.length > 0" class="form-group">
            <label>Camada (Layer)</label>
            <select v-model="layerId" class="form-input">
              <option :value="null">Nenhuma (Sempre Visível)</option>
              <option v-for="l in layers" :key="l.id" :value="l.id">{{ l.name }}</option>
            </select>
          </div>

          <!-- Vínculo Polimórfico -->
          <div class="form-group">
            <label>Tipo de Vínculo</label>
            <select v-model="linkType" class="form-input">
              <option value="NONE">Nenhum (Apenas Marcador)</option>
              <option value="ARTICLE">Vincular a Artigo do Codex</option>
              <option v-if="isMestre" value="MAP">Vincular a Sub-Mapa</option>
            </select>
          </div>

          <!-- Autocomplete de Artigo -->
          <div v-if="linkType === 'ARTICLE'" class="form-group relative">
            <label>Buscar Artigo no Codex</label>
            <input
              type="text"
              :value="targetArticleTitle || articleSearch"
              class="form-input"
              placeholder="Digite o título do artigo..."
              @input="handleArticleSearch"
            />
            <div v-if="showArticleDropdown" class="article-dropdown">
              <button
                v-for="item in articleSuggestions"
                :key="item.id"
                class="dropdown-item"
                @click="selectArticle(item)"
              >
                <span>📖 {{ item.title }}</span>
                <VisibilityBadge :visibility="item.visibility" size="sm" />
              </button>
            </div>
          </div>

          <!-- Dropdown de Sub-Mapa -->
          <div v-if="linkType === 'MAP'" class="form-group">
            <label>Selecione o Sub-Mapa</label>
            <select v-model="targetMapId" class="form-input">
              <option :value="null">Selecione um mapa...</option>
              <option v-for="m in maps" :key="m.id" :value="m.id">{{ m.title }}</option>
            </select>
          </div>

          <div class="modal-actions">
            <button class="btn btn-ghost" @click="emit('close')">Cancelar</button>
            <button class="btn btn-gold" @click="handleSave" :disabled="saving || !title.trim()">
              {{ saving ? 'Salvando...' : 'Salvar Marcador' }}
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

.form-row {
  display: flex;
  gap: var(--space-3);
}

.flex-1 { flex: 1; }
.relative { position: relative; }

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

.color-picker-row {
  display: flex;
  gap: 8px;
}

.color-btn {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 2px solid transparent;
  cursor: pointer;
  transition: transform 0.2s;
}
.color-btn--active {
  border-color: #FFFFFF;
  transform: scale(1.15);
}

.article-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  width: 100%;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
  z-index: 600;
  max-height: 160px;
  overflow-y: auto;
}

.dropdown-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 8px 12px;
  background: none;
  border: none;
  color: var(--color-text);
  font-size: 0.85rem;
  cursor: pointer;
  text-align: left;
}
.dropdown-item:hover { background: var(--color-gold-glow); color: var(--color-gold); }

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
