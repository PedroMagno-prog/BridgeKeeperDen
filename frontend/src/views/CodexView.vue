<template>
  <div class="codex-page">
    <div class="header-toolbar">
      <div>
        <h1 class="page-title">Codex & Enciclopédia</h1>
        <p class="page-sub">Acervo de lore, artigos, facções e personagens do mundo.</p>
      </div>
      <button class="btn-primary" @click="showCreateModal = true">
        <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        + Novo Artigo
      </button>
    </div>

    <!-- Barra de Filtros por Tag & Busca -->
    <div class="filter-bar card">
      <div class="search-input-wrapper">
        <input
          type="text"
          v-model="searchQuery"
          placeholder="Buscar artigos por título..."
          class="input-field"
          @input="onSearchInput"
        />
      </div>

      <div class="tags-pills">
        <span
          class="tag-pill"
          :class="{ active: selectedTag === null }"
          @click="selectTag(null)"
        >
          Todas as Tags
        </span>
        <span
          v-for="t in availableTags"
          :key="t"
          class="tag-pill"
          :class="{ active: selectedTag === t }"
          @click="selectTag(t)"
        >
          {{ t }}
        </span>
      </div>
    </div>

    <!-- Lista de Artigos -->
    <div class="articles-list" v-if="articleStore.articles.length > 0">
      <div
        v-for="art in articleStore.articles"
        :key="art.id"
        class="article-item card"
        :class="{ locked: art.is_locked }"
        @click="openArticle(art)"
      >
        <div class="article-info">
          <div class="title-row">
            <h3 class="article-title">{{ art.title }}</h3>
            <!-- Badge de Fog of War -->
            <span
              class="badge"
              :class="{
                'badge-total': art.visibility === 'TOTAL',
                'badge-parcial': art.visibility === 'PARCIAL',
                'badge-nula': art.visibility === 'NULA'
              }"
            >
              {{ art.visibility === 'PARCIAL' ? 'PARCIAL (?)' : art.visibility }}
            </span>
          </div>

          <div class="meta-row">
            <span class="in-game-date" v-if="art.in_game_date">
              📅 {{ art.in_game_date }}
            </span>
            <div class="tags-container" v-if="art.tags && art.tags.length > 0">
              <span v-for="t in art.tags" :key="t" class="article-tag-chip">
                {{ t }}
              </span>
            </div>
          </div>
        </div>

        <div class="article-action">
          <span v-if="art.is_locked" class="locked-indicator" title="Conteúdo Não Descoberto">🔒 Oculto</span>
          <span v-else class="read-link">Ler Artigo &rarr;</span>
        </div>
      </div>
    </div>

    <div class="empty-state card" v-else>
      <p>Nenhum artigo encontrado com os filtros selecionados.</p>
    </div>

    <!-- Modal Novo Artigo -->
    <div class="modal-backdrop" v-if="showCreateModal">
      <div class="modal-card card">
        <div class="modal-header">
          <h3>Novo Artigo no Codex</h3>
          <button class="close-btn" @click="showCreateModal = false">&times;</button>
        </div>
        <form @submit.prevent="handleCreateArticle" class="form">
          <div class="input-group">
            <label>Título do Artigo *</label>
            <input type="text" v-model="newTitle" class="input-field" placeholder="Ex: Reino dos Anões de Ferro" required />
          </div>

          <div class="input-group">
            <label>Data In-Game (Opcional - Usado para Timeline)</label>
            <input type="text" v-model="newDate" class="input-field" placeholder="Ex: 1442 D.C." />
          </div>

          <div class="input-group">
            <label>Tags (separadas por vírgula)</label>
            <input type="text" v-model="newTagsInput" class="input-field" placeholder=".Facção, .NPC, .Hostil" />
          </div>

          <div class="input-group" v-if="worldStore.activeUserRole === 'MESTRE'">
            <label>Visibilidade (Mestre)</label>
            <select v-model="newVisibility" class="input-field">
              <option value="NULA">Visão Nula (Invisível para Jogadores)</option>
              <option value="PARCIAL">Visão Parcial (Apenas Título / Locked)</option>
              <option value="TOTAL">Visão Total (Público)</option>
            </select>
          </div>

          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="showCreateModal = false">Cancelar</button>
            <button type="submit" class="btn-primary">Criar Artigo</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useArticleStore, type Article } from '../stores/article'
import { useWorldStore } from '../stores/world'

const articleStore = useArticleStore()
const worldStore = useWorldStore()
const router = useRouter()
const route = useRoute()

const searchQuery = ref((route.query.search as string) || '')
const selectedTag = ref<string | null>(null)
const availableTags = ['.Facção', '.NPC', '.Local', '.Hostil', '.Cultura', '.Item']

const showCreateModal = ref(false)
const newTitle = ref('')
const newDate = ref('')
const newTagsInput = ref('')
const newVisibility = ref<'TOTAL' | 'PARCIAL' | 'NULA'>('NULA')

onMounted(async () => {
  if (worldStore.activeWorldId) {
    await loadArticles()
  }
})

async function loadArticles() {
  if (!worldStore.activeWorldId) return
  await articleStore.fetchArticles(
    worldStore.activeWorldId,
    selectedTag.value || undefined,
    searchQuery.value || undefined
  )
}

function selectTag(t: string | null) {
  selectedTag.value = t
  loadArticles()
}

function onSearchInput() {
  loadArticles()
}

function openArticle(art: Article) {
  if (art.is_locked) return
  router.push(`/worlds/${worldStore.activeWorldId}/codex/${art.id}`)
}

async function handleCreateArticle() {
  if (!newTitle.value.trim() || !worldStore.activeWorldId) return
  const tags = newTagsInput.value
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)

  const created = await articleStore.createArticle(worldStore.activeWorldId, {
    title: newTitle.value,
    in_game_date: newDate.value || undefined,
    visibility: worldStore.activeUserRole === 'MESTRE' ? newVisibility.value : 'TOTAL',
    tags,
  })

  showCreateModal.value = false
  newTitle.value = ''
  newDate.value = ''
  newTagsInput.value = ''
  router.push(`/worlds/${worldStore.activeWorldId}/codex/${created.id}`)
}
</script>

<style scoped>
.codex-page {
  padding: 2rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.header-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-size: 1.6rem;
  font-weight: 700;
  color: var(--accent-gold);
}

.page-sub {
  font-size: 0.9rem;
  color: var(--text-muted);
}

.filter-bar {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.tags-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.tag-pill {
  background-color: var(--bg-main);
  border: 1px solid var(--border-color);
  color: var(--text-muted);
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    border-color: var(--accent-gold);
    color: var(--text-main);
  }

  &.active {
    background-color: var(--accent-gold);
    color: #000;
    font-weight: 600;
    border-color: var(--accent-gold);
  }
}

.articles-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.article-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover:not(.locked) {
    border-color: var(--accent-gold);
    transform: translateX(3px);
  }

  &.locked {
    opacity: 0.7;
    cursor: not-allowed;
  }
}

.article-info {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.article-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-main);
}

.meta-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  font-size: 0.8rem;
  color: var(--text-muted);
}

.article-tag-chip {
  background-color: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border-color);
  padding: 0.1rem 0.4rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;

  & + .article-tag-chip {
    margin-left: 0.3rem;
  }
}

.locked-indicator {
  font-size: 0.85rem;
  color: var(--fow-parcial);
  font-weight: 600;
}

.read-link {
  font-size: 0.9rem;
  color: var(--accent-gold);
  font-weight: 600;
}

/* Modal */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
}

.modal-card {
  width: 100%;
  max-width: 480px;

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;

    h3 {
      color: var(--accent-gold);
    }

    .close-btn {
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-size: 1.5rem;
      cursor: pointer;
    }
  }
}

.form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;

  label {
    font-size: 0.85rem;
    color: var(--text-muted);
  }
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 0.5rem;
}
</style>
