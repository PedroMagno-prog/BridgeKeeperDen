<script setup lang="ts">
/**
 * Modal para criação e edição de Quests / Missões.
 */
import { ref, watch } from 'vue'
import { useQuestsStore, type Quest, type QuestStatus, type QuestCategory } from '@/stores/quests'
import { useArticlesStore, type MentionSuggestion, type Visibility } from '@/stores/articles'
import WikilinkInput from '@/components/ui/WikilinkInput.vue'
import VisibilityBadge from '@/components/ui/VisibilityBadge.vue'

const props = defineProps<{
  show: boolean
  quest?: Quest | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'save'): void
}>()

const questsStore = useQuestsStore()
const articlesStore = useArticlesStore()

const title = ref('')
const category = ref<QuestCategory>('SIDE_QUEST')
const status = ref<QuestStatus>('NOT_STARTED')
const visibility = ref<Visibility>('NULA')
const description = ref('')
const rewards = ref('')

const articleId = ref<string | null>(null)
const articleSearch = ref('')
const articleSuggestions = ref<MentionSuggestion[]>([])
const showArticleDropdown = ref(false)

const objectives = ref<Array<{ description: string; is_completed: boolean; order_index: number }>>([])
const newObjectiveText = ref('')
const saving = ref(false)

watch(
  () => props.show,
  (show) => {
    if (show) {
      const q = props.quest
      if (q) {
        title.value = q.title
        category.value = q.category
        status.value = q.status
        visibility.value = q.visibility
        description.value = q.description || ''
        rewards.value = q.rewards || ''
        articleId.value = q.article_id || null
        articleSearch.value = q.article_title || ''
        objectives.value = q.objectives
          ? q.objectives.map((o) => ({ description: o.description, is_completed: o.is_completed, order_index: o.order_index }))
          : []
      } else {
        title.value = ''
        category.value = 'SIDE_QUEST'
        status.value = 'NOT_STARTED'
        visibility.value = 'NULA'
        description.value = ''
        rewards.value = ''
        articleId.value = null
        articleSearch.value = ''
        objectives.value = []
      }
      newObjectiveText.value = ''
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
  articleId.value = item.id
  articleSearch.value = item.title
  showArticleDropdown.value = false
}

function addObjective() {
  if (!newObjectiveText.value.trim()) return
  objectives.value.push({
    description: newObjectiveText.value.trim(),
    is_completed: false,
    order_index: objectives.value.length,
  })
  newObjectiveText.value = ''
}

function removeObjective(idx: number) {
  objectives.value.splice(idx, 1)
}

async function handleSave() {
  if (!title.value.trim()) return
  saving.value = true
  try {
    const payload = {
      title: title.value.trim(),
      category: category.value,
      status: status.value,
      visibility: visibility.value,
      description: description.value,
      rewards: rewards.value.trim() || null,
      article_id: articleId.value,
      objectives: objectives.value,
    }

    if (props.quest) {
      await questsStore.updateQuest(props.quest.id, payload as any)
    } else {
      await questsStore.createQuest(payload as any)
    }
    emit('save')
    emit('close')
  } catch (err: any) {
    alert(err?.response?.data?.detail || 'Erro ao salvar missão.')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="show" class="modal-overlay" @click.self="emit('close')">
        <div class="modal modal--wide">
          <h3 class="modal-title">{{ quest ? 'Editar Quest' : 'Nova Quest / Missão' }}</h3>

          <div class="form-row">
            <div class="form-group flex-2">
              <label>Título da Quest</label>
              <input v-model="title" type="text" class="form-input" placeholder="Ex: Em Busca da Forja Lendária" autofocus />
            </div>

            <div class="form-group flex-1">
              <label>Categoria</label>
              <select v-model="category" class="form-input">
                <option value="MAIN_QUEST">👑 Principal</option>
                <option value="SIDE_QUEST">📜 Secundária</option>
                <option value="MONSTER_HUNT">☠️ Caçada</option>
                <option value="ARTIFACT_SEARCH">🔮 Artefato</option>
                <option value="OUTPOST">🧭 Posto Avançado</option>
                <option value="FACTION">🛡️ Facção</option>
              </select>
            </div>
          </div>

          <div class="form-row">
            <div class="form-group flex-1">
              <label>Status Inicial</label>
              <select v-model="status" class="form-input">
                <option value="NOT_STARTED">Não Iniciada</option>
                <option value="IN_PROGRESS">Em Progresso</option>
                <option value="COMPLETED">Concluída</option>
                <option value="FAILED">Falhada</option>
                <option value="ON_HOLD">Suspensa</option>
              </select>
            </div>

            <div class="form-group flex-1">
              <label>Visibilidade (Névoa)</label>
              <select v-model="visibility" class="form-input">
                <option value="NULA">Nula</option>
                <option value="PARCIAL">Parcial</option>
                <option value="TOTAL">Total</option>
              </select>
            </div>

            <div class="form-group flex-2 relative">
              <label>Artigo de Lore Vinculado (Codex)</label>
              <input
                type="text"
                :value="articleSearch"
                class="form-input"
                placeholder="Buscar artigo..."
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
          </div>

          <!-- Descrição com Autocomplete [[ -->
          <div class="form-group">
            <label>Descrição da Quest (Suporta [[Artigo]])</label>
            <WikilinkInput v-model="description" :rows="3" placeholder="Insira a narrativa da missão... Digite [[ para citar um artigo." />
          </div>

          <!-- Gerenciador de Objetivos -->
          <div class="form-group">
            <label>Checklist de Objetivos</label>

            <div class="add-objective-row">
              <input
                v-model="newObjectiveText"
                type="text"
                class="form-input flex-1"
                placeholder="Novo objetivo (ex: Derrotar o Guardião)"
                @keydown.enter.prevent="addObjective"
              />
              <button class="btn btn-sm btn-gold" @click="addObjective">+ Add</button>
            </div>

            <div v-if="objectives.length > 0" class="objectives-edit-list">
              <div v-for="(obj, i) in objectives" :key="i" class="obj-edit-item">
                <input type="checkbox" v-model="obj.is_completed" />
                <input type="text" v-model="obj.description" class="form-input flex-1 obj-input" />
                <button class="btn-remove" title="Remover" @click="removeObjective(i)">×</button>
              </div>
            </div>
          </div>

          <!-- Recompensas -->
          <div class="form-group">
            <label>Recompensas (PO, XP, Itens, [[Artigo]])</label>
            <WikilinkInput v-model="rewards" :rows="2" placeholder="Ex: 500 PO, [[Espada Mágica]]" />
          </div>

          <div class="modal-actions">
            <button class="btn btn-ghost" @click="emit('close')">Cancelar</button>
            <button class="btn btn-gold" @click="handleSave" :disabled="saving || !title.trim()">
              {{ saving ? 'Salvando...' : 'Salvar Quest' }}
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
  max-width: 520px;
  box-shadow: var(--shadow-lg);
}

.modal--wide {
  max-width: 640px;
  max-height: 88vh;
  overflow-y: auto;
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
.flex-2 { flex: 2; }
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

.add-objective-row {
  display: flex;
  gap: 8px;
}

.objectives-edit-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 8px;
}

.obj-edit-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.obj-input {
  padding: 4px 8px;
  font-size: 0.8rem;
}

.btn-remove {
  background: none;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-danger);
  cursor: pointer;
  width: 24px;
  height: 24px;
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
.btn-sm { padding: 4px 10px; font-size: 0.8rem; }
.btn-ghost { background: none; color: var(--color-text-muted); border: 1px solid var(--color-border); }
.btn-gold { background: var(--color-gold); color: #111827; }
</style>
