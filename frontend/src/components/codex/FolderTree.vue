<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useArticlesStore } from '@/stores/articles'
import FolderItem from './FolderItem.vue'

const props = defineProps<{
  activeArticleId?: string | null
}>()

const emit = defineEmits<{
  (e: 'select-article', articleId: string): void
  (e: 'create-article', folderId?: number | null): void
  (e: 'open-folder-modal', payload: { mode: 'create' | 'rename'; folderId?: number | null; parentId?: number | null; initialName?: string }): void
}>()

const articlesStore = useArticlesStore()
const filterText = ref('')

onMounted(async () => {
  await articlesStore.fetchFolderTree()
})

const filteredRootArticles = computed(() => {
  if (!filterText.value.trim()) return articlesStore.rootArticles
  const search = filterText.value.trim().toLowerCase()
  return articlesStore.rootArticles.filter((a) =>
    a.title.toLowerCase().includes(search)
  )
})

function onSelectArticle(articleId: string) { emit('select-article', articleId) }
function handleCreateRootFolder() { emit('open-folder-modal', { mode: 'create', parentId: null }) }
function handleCreateSubfolder(parentId: number) { emit('open-folder-modal', { mode: 'create', parentId }) }
function handleCreateArticle(folderId?: number | null) { emit('create-article', folderId) }
function handleRenameFolder(payload: { folderId: number; name: string }) {
  emit('open-folder-modal', { mode: 'rename', folderId: payload.folderId, initialName: payload.name })
}
async function handleDeleteFolder(folderId: number) { await articlesStore.removeFolder(folderId) }
</script>

<template>
  <div class="folder-tree-root">
    <div class="folder-tree-header">
      <div class="folder-tree-header__top">
        <h3 class="folder-tree-title">Codex e Cofre</h3>
        <div class="folder-tree-actions">
          <button class="tree-btn tree-btn--secondary" title="Nova Pasta Raiz" @click="handleCreateRootFolder">
            📁+ Pasta
          </button>
          <button class="tree-btn tree-btn--gold" title="Novo Artigo Raiz" @click="() => handleCreateArticle(null)">
            📄+ Artigo
          </button>
        </div>
      </div>
      <div class="folder-tree-search">
        <span class="search-icon">🔍</span>
        <input
          v-model="filterText"
          type="text"
          placeholder="Filtrar por nome..."
          class="tree-search-input"
        />
      </div>
    </div>

    <div class="folder-tree-content">
      <div v-if="articlesStore.loading" class="tree-loading">
        Carregando estrutura...
      </div>

      <template v-else>
        <FolderItem
          v-for="folder in articlesStore.folderTree"
          :key="folder.id"
          :folder="folder"
          :level="0"
          :active-article-id="activeArticleId"
          @select-article="onSelectArticle"
          @create-subfolder="handleCreateSubfolder"
          @create-article-in-folder="(fid) => handleCreateArticle(fid)"
          @rename-folder="handleRenameFolder"
          @delete-folder="handleDeleteFolder"
        />

        <div v-if="filteredRootArticles.length > 0" class="root-articles-section">
          <div class="root-articles-title">Artigos Raiz</div>
          <div
            v-for="article in filteredRootArticles"
            :key="article.id"
            class="tree-article-row"
            :class="{ 'tree-article-row--active': activeArticleId === article.id }"
            @click="onSelectArticle(article.id)"
          >
            <span class="article-icon">📄</span>
            <span class="article-title">{{ article.title }}</span>
            <span v-if="article.visibility === 'NULA'" class="article-lock" title="Visão Nula (Mestre)">🔒</span>
          </div>
        </div>

        <div v-if="articlesStore.folderTree.length === 0 && articlesStore.rootArticles.length === 0" class="tree-empty">
          <p>Nenhuma pasta ou artigo encontrado.</p>
          <button class="tree-btn tree-btn--gold" @click="handleCreateRootFolder">
            Criar Primeira Pasta
          </button>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.folder-tree-root {
  display: flex;
  flex-direction: column;
  height: 100%;
  max-height: 100%;
  min-height: 0;
  flex: 1 1 0%;
  background: var(--color-surface, #141720);
  color: var(--color-text, #e8e4d8);
  user-select: none;
  overflow: hidden;
}

.folder-tree-header {
  padding: 10px 12px;
  border-bottom: 1px solid var(--color-border, #2e3350);
  background: var(--color-bg, #0d0f14);
  flex-shrink: 0;
}

.folder-tree-header__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.folder-tree-title {
  font-size: 0.68rem;
  font-weight: 600;
  color: var(--color-text-dim, #545e72);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin: 0;
}

.folder-tree-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.tree-btn {
  padding: 4px 8px;
  font-size: 0.72rem;
  font-weight: 500;
  border-radius: var(--radius-sm, 6px);
  cursor: pointer;
  line-height: 1.2;
  font-family: inherit;
  transition: all var(--transition-fast, 120ms ease);
}

.tree-btn--secondary {
  background: var(--color-surface-2, #1c2030);
  border: 1px solid var(--color-border, #2e3350);
  color: var(--color-text-muted, #8892a4);
}
.tree-btn--secondary:hover {
  color: var(--color-gold, #c9a84c);
  border-color: var(--color-gold-dim, #7a6030);
  background: var(--color-surface-3, #242840);
}

.tree-btn--gold {
  background: var(--color-gold-glow, rgba(201, 168, 76, 0.15));
  border: 1px solid var(--color-gold-dim, #7a6030);
  color: var(--color-gold, #c9a84c);
}
.tree-btn--gold:hover {
  background: var(--color-gold, #c9a84c);
  color: #0d0f14;
}

.folder-tree-search {
  position: relative;
}

.search-icon {
  position: absolute;
  left: 8px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 0.7rem;
  color: var(--color-text-dim, #545e72);
  pointer-events: none;
}

.tree-search-input {
  width: 100%;
  padding: 5px 10px 5px 26px;
  font-size: 0.75rem;
  background: var(--color-surface, #141720);
  border: 1px solid var(--color-border, #2e3350);
  border-radius: var(--radius-sm, 6px);
  color: var(--color-text, #e8e4d8);
  outline: none;
  font-family: inherit;
  box-sizing: border-box;
  transition: border-color var(--transition-fast, 120ms ease);
}

.tree-search-input:focus {
  border-color: var(--color-gold, #c9a84c);
}

.folder-tree-content {
  flex: 1 1 0%;
  min-height: 0;
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 8px;
  background: var(--color-surface, #141720);
  scrollbar-width: thin;
  scrollbar-color: var(--color-border, #2e3350) transparent;
}

.tree-loading {
  padding: 16px;
  text-align: center;
  font-size: 0.75rem;
  color: var(--color-text-dim, #545e72);
}

.root-articles-section {
  padding-top: 8px;
  border-top: 1px solid var(--color-border, #2e3350);
  margin-top: 6px;
}

.root-articles-title {
  padding: 4px 8px;
  font-size: 0.65rem;
  font-weight: 600;
  color: var(--color-text-dim, #545e72);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.tree-article-row {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 5px 10px;
  border-radius: var(--radius-sm, 6px);
  font-size: 0.78rem;
  cursor: pointer;
  color: var(--color-text-muted, #8892a4);
  transition: all var(--transition-fast, 120ms ease);
}

.tree-article-row:hover {
  background: var(--color-surface-2, #1c2030);
  color: var(--color-text, #e8e4d8);
}

.tree-article-row--active {
  background: var(--color-gold-glow, rgba(201, 168, 76, 0.15)) !important;
  color: var(--color-gold, #c9a84c) !important;
  border-left: 2px solid var(--color-gold, #c9a84c);
  padding-left: 8px;
}

.article-icon {
  font-size: 0.75rem;
  flex-shrink: 0;
  opacity: 0.7;
}

.article-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.article-lock {
  font-size: 0.7rem;
  flex-shrink: 0;
}

.tree-empty {
  padding: 24px 16px;
  text-align: center;
  font-size: 0.78rem;
  color: var(--color-text-dim, #545e72);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}
</style>
