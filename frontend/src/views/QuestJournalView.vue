<script setup lang="ts">
/**
 * Módulo Quest Journal (Missões) — QuestJournalView.vue
 */
import { ref, computed, onMounted } from 'vue'
import { useQuestsStore, type Quest, type QuestStatus, type QuestCategory } from '@/stores/quests'
import { useWorldsStore } from '@/stores/worlds'
import QuestCard from '@/components/quests/QuestCard.vue'
import QuestModal from '@/components/quests/QuestModal.vue'

const questsStore = useQuestsStore()
const worldsStore = useWorldsStore()

const isMestre = computed(() => worldsStore.isMestre)

const viewMode = ref<'kanban' | 'category'>('kanban')
const showModal = ref(false)
const editingQuest = ref<Quest | null>(null)

const searchInput = ref('')
const activeCategory = ref<string>('')

const CATEGORIES = [
  { id: '', label: 'Todas' },
  { id: 'MAIN_QUEST', label: '👑 Principal' },
  { id: 'MONSTER_HUNT', label: '☠️ Caçadas' },
  { id: 'ARTIFACT_SEARCH', label: '🔮 Artefatos' },
  { id: 'OUTPOST', label: '🧭 Postos' },
  { id: 'FACTION', label: '🛡️ Facções' },
  { id: 'SIDE_QUEST', label: '📜 Secundárias' },
]

const STATUS_COLUMNS: Array<{ id: QuestStatus; title: string }> = [
  { id: 'NOT_STARTED', title: 'Não Iniciada' },
  { id: 'IN_PROGRESS', title: 'Em Progresso' },
  { id: 'COMPLETED', title: 'Concluída' },
  { id: 'FAILED', title: 'Falhada / Suspensa' },
]

onMounted(async () => {
  if (!worldsStore.activeWorld) {
    await worldsStore.fetchWorlds()
  }
  questsStore.fetchQuests()
})

const filteredQuests = computed(() => {
  return questsStore.quests.filter((q) => {
    if (activeCategory.value && q.category !== activeCategory.value) return false
    if (searchInput.value.trim()) {
      const query = searchInput.value.toLowerCase()
      return q.title.toLowerCase().includes(query) || q.description.toLowerCase().includes(query)
    }
    return true
  })
})

function getQuestsByStatus(statusId: QuestStatus) {
  return filteredQuests.value.filter((q) => {
    if (statusId === 'FAILED') {
      return q.status === 'FAILED' || q.status === 'ON_HOLD'
    }
    return q.status === statusId
  })
}

function openCreateModal() {
  editingQuest.value = null
  showModal.value = true
}

function openEditModal(quest: Quest) {
  editingQuest.value = quest
  showModal.value = true
}

async function handleDeleteQuest(quest: Quest) {
  if (confirm(`Tem certeza que deseja excluir a missão "${quest.title}"?`)) {
    await questsStore.deleteQuest(quest.id)
  }
}

async function handleChangeStatus(quest: Quest, newStatus: QuestStatus) {
  await questsStore.updateQuest(quest.id, { status: newStatus })
}
</script>

<template>
  <div class="quest-journal">
    <!-- Header -->
    <div class="journal-header">
      <div>
        <h2 class="journal-title">Quest Journal (Diário de Missões)</h2>
        <p class="journal-sub">Acompanhe objetivos, caçadas e o progresso das campanhas do mundo.</p>
      </div>

      <div class="header-actions">
        <!-- Alternância de Visão -->
        <div class="view-toggle">
          <button
            class="toggle-btn"
            :class="{ 'toggle-btn--active': viewMode === 'kanban' }"
            @click="viewMode = 'kanban'"
          >
            📋 Kanban
          </button>
          <button
            class="toggle-btn"
            :class="{ 'toggle-btn--active': viewMode === 'category' }"
            @click="viewMode = 'category'"
          >
            📁 Por Categoria
          </button>
        </div>

        <button v-if="isMestre" class="btn-gold" @click="openCreateModal">
          ➕ Nova Quest
        </button>
      </div>
    </div>

    <!-- Toolbar de Filtros -->
    <div class="journal-toolbar">
      <div class="search-box">
        <span class="search-icon">🔍</span>
        <input
          v-model="searchInput"
          type="text"
          placeholder="Buscar missões..."
          class="search-input"
        />
      </div>

      <div class="category-pills">
        <button
          v-for="cat in CATEGORIES"
          :key="cat.id"
          class="cat-pill"
          :class="{ 'cat-pill--active': activeCategory === cat.id }"
          @click="activeCategory = cat.id"
        >
          {{ cat.label }}
        </button>
      </div>
    </div>

    <!-- Conteúdo Principal -->
    <div v-if="questsStore.loading" class="list-empty">Carregando missões do mundo...</div>
    <div v-else-if="filteredQuests.length === 0" class="list-empty">Nenhuma missão encontrada.</div>

    <!-- Visão 1: Kanban por Status -->
    <div v-else-if="viewMode === 'kanban'" class="kanban-board">
      <div v-for="col in STATUS_COLUMNS" :key="col.id" class="kanban-col">
        <div class="col-header">
          <h4 class="col-title">{{ col.title }}</h4>
          <span class="col-count">{{ getQuestsByStatus(col.id).length }}</span>
        </div>

        <div class="col-cards">
          <QuestCard
            v-for="q in getQuestsByStatus(col.id)"
            :key="q.id"
            :quest="q"
            :is-mestre="isMestre"
            @edit="openEditModal"
            @delete="handleDeleteQuest"
            @change-status="handleChangeStatus"
          />
        </div>
      </div>
    </div>

    <!-- Visão 2: Agrupada por Categoria -->
    <div v-else class="category-view">
      <div
        v-for="cat in CATEGORIES.filter((c) => c.id !== '')"
        :key="cat.id"
        class="category-group"
      >
        <template v-if="filteredQuests.filter((q) => q.category === cat.id).length > 0">
          <h3 class="group-title">{{ cat.label }}</h3>
          <div class="category-grid">
            <QuestCard
              v-for="q in filteredQuests.filter((q) => q.category === cat.id)"
              :key="q.id"
              :quest="q"
              :is-mestre="isMestre"
              @edit="openEditModal"
              @delete="handleDeleteQuest"
              @change-status="handleChangeStatus"
            />
          </div>
        </template>
      </div>
    </div>

    <!-- Modal -->
    <QuestModal
      :show="showModal"
      :quest="editingQuest"
      @close="showModal = false"
      @save="questsStore.fetchQuests()"
    />
  </div>
</template>

<style scoped>
.quest-journal {
  padding: var(--space-6) var(--space-8);
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  height: calc(100vh - 56px);
  overflow-y: auto;
}

.journal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.journal-title {
  font-family: var(--font-display);
  font-size: 1.4rem;
  color: var(--color-gold);
}

.journal-sub {
  font-size: 0.85rem;
  color: var(--color-text-dim);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.view-toggle {
  display: flex;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 2px;
}

.toggle-btn {
  padding: 4px 10px;
  background: none;
  border: none;
  color: var(--color-text-muted);
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  border-radius: var(--radius-sm);
}

.toggle-btn--active {
  background: var(--color-gold-glow);
  color: var(--color-gold);
}

.btn-gold {
  padding: 6px 14px;
  background: var(--color-gold);
  color: #111827;
  border: none;
  border-radius: var(--radius-sm);
  font-weight: 600;
  font-size: 0.85rem;
  cursor: pointer;
}

/* Toolbar */
.journal-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 6px 12px;
  width: 280px;
}

.search-input {
  background: none;
  border: none;
  outline: none;
  color: var(--color-text);
  font-size: 0.85rem;
  width: 100%;
}

.category-pills {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.cat-pill {
  padding: 4px 10px;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  font-size: 0.75rem;
  color: var(--color-text-muted);
  cursor: pointer;
}
.cat-pill:hover { border-color: var(--color-gold-dim); color: var(--color-gold); }
.cat-pill--active { background: var(--color-gold-glow); border-color: var(--color-gold-dim); color: var(--color-gold); }

/* Kanban Board */
.kanban-board {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-4);
  align-items: start;
  flex: 1;
}

.kanban-col {
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - 220px);
}

.col-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border-bottom: 1px solid var(--color-border);
}

.col-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-gold);

  margin: 0;
}

.col-count {
  font-size: 0.75rem;
  background: var(--color-surface);
  padding: 2px 6px;
  border-radius: 10px;
  color: var(--color-text-dim);
}

.col-cards {
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;
}

/* Category View */
.category-view {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.group-title {
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--color-gold);
  border-bottom: 1px solid var(--color-border);
  padding-bottom: 4px;
  margin-bottom: var(--space-3);
}

.category-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--space-4);
}

.list-empty {
  text-align: center;
  padding: var(--space-8);
  color: var(--color-text-dim);
}
</style>
