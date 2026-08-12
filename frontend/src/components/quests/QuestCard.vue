<script setup lang="ts">
/**
 * Componente de exibição de Card de Quest (Missão).
 */
import { computed } from 'vue'
import { useQuestsStore, type Quest, type QuestStatus, type QuestCategory } from '@/stores/quests'
import VisibilityBadge from '@/components/ui/VisibilityBadge.vue'
import WikilinkText from '@/components/ui/WikilinkText.vue'

const props = defineProps<{
  quest: Quest
  isMestre: boolean
}>()

const emit = defineEmits<{
  (e: 'edit', quest: Quest): void
  (e: 'delete', quest: Quest): void
  (e: 'change-status', quest: Quest, newStatus: QuestStatus): void
}>()

const questsStore = useQuestsStore()

const completedCount = computed(() => props.quest.objectives.filter((o) => o.is_completed).length)
const totalCount = computed(() => props.quest.objectives.length)
const progressPct = computed(() => (totalCount.value > 0 ? Math.round((completedCount.value / totalCount.value) * 100) : 0))

function getCategoryMeta(category: QuestCategory) {
  switch (category) {
    case 'MAIN_QUEST': return { label: 'Principal', emoji: '👑', color: '#EAB308' }
    case 'MONSTER_HUNT': return { label: 'Caçada', emoji: '☠️', color: '#EF4444' }
    case 'ARTIFACT_SEARCH': return { label: 'Artefato', emoji: '🔮', color: '#8B5CF6' }
    case 'OUTPOST': return { label: 'Posto Avançado', emoji: '🧭', color: '#10B981' }
    case 'FACTION': return { label: 'Facção', emoji: '🛡️', color: '#3B82F6' }
    default: return { label: 'Secundária', emoji: '📜', color: '#9CA3AF' }
  }
}

function getStatusMeta(status: QuestStatus) {
  switch (status) {
    case 'IN_PROGRESS': return { label: 'Em Progresso', class: 'status-progress' }
    case 'COMPLETED': return { label: 'Concluída', class: 'status-completed' }
    case 'FAILED': return { label: 'Falhada', class: 'status-failed' }
    case 'ON_HOLD': return { label: 'Suspensa', class: 'status-hold' }
    default: return { label: 'Não Iniciada', class: 'status-not-started' }
  }
}

async function handleToggle(objId: string) {
  await questsStore.toggleObjective(props.quest.id, objId)
}
</script>

<template>
  <div class="quest-card" :class="{ 'quest-card--locked': quest.is_locked }">
    <!-- Header -->
    <div class="card-header">
      <div class="header-left">
        <span class="cat-badge" :style="{ backgroundColor: getCategoryMeta(quest.category).color }">
          {{ getCategoryMeta(quest.category).emoji }}
        </span>
        <div>
          <span class="cat-label">{{ getCategoryMeta(quest.category).label }}</span>
          <h3 class="quest-title">{{ quest.title }}</h3>
        </div>
      </div>

      <div class="header-right">
        <span class="status-badge" :class="getStatusMeta(quest.status).class">
          {{ getStatusMeta(quest.status).label }}
        </span>
        <VisibilityBadge v-if="isMestre" :visibility="quest.visibility" size="sm" />
      </div>
    </div>

    <!-- Body -->
    <div class="card-body">
      <div v-if="quest.is_locked" class="locked-text">
        <span>🔒 Detalhes da missão protegidos pela Névoa de Guerra Parcial.</span>
      </div>

      <template v-else>
        <!-- Descrição com Wikilinks -->
        <div v-if="quest.description" class="quest-description">
          <WikilinkText :text="quest.description" />
        </div>

        <!-- Barra de Progresso de Objetivos -->
        <div v-if="totalCount > 0" class="progress-box">
          <div class="progress-header">
            <span>Objetivos ({{ completedCount }}/{{ totalCount }})</span>
            <span>{{ progressPct }}%</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: `${progressPct}%` }"></div>
          </div>

          <!-- Lista de Objetivos -->
          <div class="objectives-list">
            <label
              v-for="obj in quest.objectives"
              :key="obj.id"
              class="objective-item"
              :class="{ 'objective-item--done': obj.is_completed }"
            >
              <input
                type="checkbox"
                :checked="obj.is_completed"
                @change="handleToggle(obj.id)"
              />
              <span class="obj-desc">{{ obj.description }}</span>
            </label>
          </div>
        </div>

        <!-- Recompensas -->
        <div v-if="quest.rewards" class="rewards-box">
          <span class="rewards-label">🎁 Recompensas:</span>
          <div class="rewards-text">
            <WikilinkText :text="quest.rewards" />
          </div>
        </div>
      </template>
    </div>

    <!-- Footer para Mestre -->
    <div v-if="isMestre" class="card-footer">
      <select
        :value="quest.status"
        class="status-select"
        @change="(e) => emit('change-status', quest, (e.target as HTMLSelectElement).value as QuestStatus)"
      >
        <option value="NOT_STARTED">Não Iniciada</option>
        <option value="IN_PROGRESS">Em Progresso</option>
        <option value="COMPLETED">Concluída</option>
        <option value="FAILED">Falhada</option>
        <option value="ON_HOLD">Suspensa</option>
      </select>

      <div class="footer-btns">
        <button class="btn-icon" title="Editar Quest" @click="emit('edit', quest)">✏️</button>
        <button class="btn-icon btn-danger" title="Excluir Quest" @click="emit('delete', quest)">🗑️</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.quest-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: all var(--transition-fast);
}

.quest-card:hover {
  border-color: var(--color-gold-dim);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
}

.quest-card--locked {
  opacity: 0.8;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--color-surface-2);
  border-bottom: 1px solid var(--color-border);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.cat-badge {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
  flex-shrink: 0;
}

.cat-label {
  font-size: 0.65rem;
  color: var(--color-text-dim);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.quest-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--color-gold);
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-badge {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
}
.status-not-started { background: rgba(156, 163, 175, 0.2); color: #9CA3AF; }
.status-progress { background: rgba(59, 130, 246, 0.2); color: #3B82F6; }
.status-completed { background: rgba(16, 185, 129, 0.2); color: #10B981; }
.status-failed { background: rgba(239, 68, 68, 0.2); color: #EF4444; }
.status-hold { background: rgba(234, 179, 8, 0.2); color: #EAB308; }

.card-body {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  font-size: 0.85rem;
}

.locked-text {
  color: var(--color-text-dim);
  font-style: italic;
}

.quest-description {
  color: var(--color-text);
  line-height: 1.5;
}

.progress-box {
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 10px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: var(--color-text-dim);
  margin-bottom: 6px;
}

.progress-bar {
  height: 6px;
  background: var(--color-surface-2);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 10px;
}

.progress-fill {
  height: 100%;
  background: var(--color-gold);
  transition: width 0.3s ease;
}

.objectives-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.objective-item {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 0.8rem;
  color: var(--color-text);
}

.objective-item input[type="checkbox"] {
  accent-color: var(--color-gold);
}

.objective-item--done .obj-desc {
  text-decoration: line-through;
  color: var(--color-text-dim);
}

.rewards-box {
  background: rgba(234, 179, 8, 0.08);
  border: 1px solid rgba(234, 179, 8, 0.2);
  border-radius: var(--radius-sm);
  padding: 8px 12px;
  font-size: 0.8rem;
}

.rewards-label {
  font-weight: 600;
  color: var(--color-gold);
  display: block;
  margin-bottom: 2px;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: var(--color-surface-2);
  border-top: 1px solid var(--color-border);
}

.status-select {
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text);
  font-size: 0.75rem;
  padding: 3px 6px;
}

.footer-btns {
  display: flex;
  gap: 6px;
}

.btn-icon {
  background: none;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 0.85rem;
  padding: 2px 6px;
}
.btn-danger:hover { border-color: var(--color-danger); }
</style>
