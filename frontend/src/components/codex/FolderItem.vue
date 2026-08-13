<script setup lang="ts">
import { computed } from 'vue'
import { useArticlesStore } from '@/stores/articles'
import type { FolderTreeNode } from '@/api/folders'

const props = withDefaults(
  defineProps<{
    folder: FolderTreeNode
    level?: number
    activeArticleId?: string | null
  }>(),
  { level: 0, activeArticleId: null }
)

const emit = defineEmits<{
  (e: 'select-article', articleId: string): void
  (e: 'create-subfolder', parentId: number): void
  (e: 'create-article-in-folder', folderId: number): void
  (e: 'rename-folder', payload: { folderId: number; name: string }): void
  (e: 'delete-folder', folderId: number): void
}>()

const articlesStore = useArticlesStore()

const isExpanded = computed(() => articlesStore.expandedFolderIds.has(props.folder.id))

function handleToggleExpand(e: Event) { e.stopPropagation(); articlesStore.toggleFolderExpand(props.folder.id) }
function onSelectArticle(articleId: string) { emit('select-article', articleId) }
function handleCreateSubfolder(e: Event) { e.stopPropagation(); emit('create-subfolder', props.folder.id) }
function handleCreateArticle(e: Event) { e.stopPropagation(); emit('create-article-in-folder', props.folder.id) }
function handleRename(e: Event) { e.stopPropagation(); emit('rename-folder', { folderId: props.folder.id, name: props.folder.name }) }
function handleDelete(e: Event) {
  e.stopPropagation()
  if (confirm(`Deseja excluir a pasta "${props.folder.name}"?`)) emit('delete-folder', props.folder.id)
}
</script>

<template>
  <div>
    <!-- Folder Row -->
    <div
      class="folder-row"
      :style="{ paddingLeft: `${level * 12 + 8}px` }"
      @click="handleToggleExpand"
    >
      <div class="folder-row__left">
        <span class="folder-chevron" :class="{ 'is-expanded': isExpanded }">&#9654;</span>
        <span class="folder-icon">{{ isExpanded ? '&#128194;' : '&#128193;' }}</span>
        <span class="folder-name">{{ folder.name }}</span>
      </div>
      <div class="folder-actions">
        <button class="folder-btn" title="Nova Subpasta" @click="handleCreateSubfolder">&#128193;+</button>
        <button class="folder-btn" title="Novo Artigo nesta Pasta" @click="handleCreateArticle">&#128196;+</button>
        <button class="folder-btn" title="Renomear" @click="handleRename">&#9998;</button>
        <button class="folder-btn folder-btn--danger" title="Excluir" @click="handleDelete">&#128465;</button>
      </div>
    </div>

    <!-- Folder Contents -->
    <div v-if="isExpanded">
      <FolderItem
        v-for="child in folder.children"
        :key="child.id"
        :folder="child"
        :level="level + 1"
        :active-article-id="activeArticleId"
        @select-article="onSelectArticle"
        @create-subfolder="(pid) => emit('create-subfolder', pid)"
        @create-article-in-folder="(fid) => emit('create-article-in-folder', fid)"
        @rename-folder="(p) => emit('rename-folder', p)"
        @delete-folder="(fid) => emit('delete-folder', fid)"
      />

      <div
        v-for="article in folder.articles"
        :key="article.id"
        class="article-row"
        :class="{ 'article-row--active': activeArticleId === article.id }"
        :style="{ paddingLeft: `${(level + 1) * 12 + 20}px` }"
        @click="onSelectArticle(article.id)"
      >
        <span class="article-icon">&#128196;</span>
        <span class="article-title">{{ article.title }}</span>
        <span v-if="article.visibility === 'NULA'" class="article-lock" title="Visao Nula (Mestre)">&#128274;</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.folder-row {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 5px 8px;
  border-radius: 7px;
  cursor: pointer;
  color: #8890b0;
  transition: background 0.12s ease, color 0.12s ease;
}
.folder-row:hover {
  background: rgba(255, 255, 255, 0.04);
  color: #c4c8d8;
}
.folder-row__left {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  overflow: hidden;
  flex: 1;
}
.folder-chevron {
  display: inline-block;
  width: 12px;
  font-size: 0.55rem;
  text-align: center;
  color: #3a3f55;
  transition: transform 0.15s ease;
  flex-shrink: 0;
}
.folder-chevron.is-expanded {
  transform: rotate(90deg);
}
.folder-icon {
  font-size: 0.9rem;
  flex-shrink: 0;
}
.folder-name {
  font-size: 0.78rem;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
/* Action buttons - hidden by default, shown on hover */
.folder-actions {
  display: none;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
}
.folder-row:hover .folder-actions {
  display: flex;
}
.folder-btn {
  padding: 2px 5px;
  font-size: 0.65rem;
  background: transparent;
  border: none;
  color: #4a5068;
  cursor: pointer;
  border-radius: 4px;
  transition: color 0.1s ease, background 0.1s ease;
  line-height: 1.4;
}
.folder-btn:hover {
  color: #c9a84c;
  background: rgba(201, 168, 76, 0.1);
}
.folder-btn--danger:hover {
  color: #f87171;
  background: rgba(248, 113, 113, 0.08);
}
/* Article rows */
.article-row {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 0.75rem;
  cursor: pointer;
  color: #6070a0;
  transition: background 0.12s ease, color 0.12s ease;
}
.article-row:hover {
  background: rgba(255, 255, 255, 0.04);
  color: #a0a8c0;
}
.article-row--active {
  background: rgba(201, 168, 76, 0.14) !important;
  color: #c9a84c !important;
  border-left: 2px solid #c9a84c;
}
.article-icon {
  color: #2e3550;
  font-size: 0.7rem;
  flex-shrink: 0;
}
.article-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.article-lock {
  font-size: 0.65rem;
  flex-shrink: 0;
}
</style>
