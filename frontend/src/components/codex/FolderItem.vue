<script setup lang="ts">
import { computed, ref } from 'vue'
import { useArticlesStore } from '@/stores/articles'
import type { FolderTreeNode, ArticleSummary } from '@/api/folders'

const props = withDefaults(
  defineProps<{
    folder: FolderTreeNode
    level?: number
    activeArticleId?: string | null
  }>(),
  {
    level: 0,
    activeArticleId: null,
  }
)

const emit = defineEmits<{
  (e: 'select-article', articleId: string): void
  (e: 'create-subfolder', parentId: number): void
  (e: 'create-article-in-folder', folderId: number): void
  (e: 'rename-folder', payload: { folderId: number; name: string }): void
  (e: 'delete-folder', folderId: number): void
}>()

const articlesStore = useArticlesStore()
const showMenu = ref(false)

const isExpanded = computed(() => articlesStore.expandedFolderIds.has(props.folder.id))

function handleToggleExpand(e: Event) {
  e.stopPropagation()
  articlesStore.toggleFolderExpand(props.folder.id)
}

function onSelectArticle(articleId: string) {
  emit('select-article', articleId)
}

function handleCreateSubfolder(e: Event) {
  e.stopPropagation()
  showMenu.value = false
  emit('create-subfolder', props.folder.id)
}

function handleCreateArticle(e: Event) {
  e.stopPropagation()
  showMenu.value = false
  emit('create-article-in-folder', props.folder.id)
}

function handleRename(e: Event) {
  e.stopPropagation()
  showMenu.value = false
  emit('rename-folder', { folderId: props.folder.id, name: props.folder.name })
}

function handleDelete(e: Event) {
  e.stopPropagation()
  showMenu.value = false
  if (confirm(`Deseja excluir a pasta "${props.folder.name}"?`)) {
    emit('delete-folder', props.folder.id)
  }
}
</script>

<template>
  <div>
    <!-- Folder Header Row -->
    <div
      class="group"
      style="position:relative; display:flex; align-items:center; justify-content:space-between; padding:5px 8px 5px 8px; border-radius:7px; cursor:pointer; transition:background 0.12s ease; color:#8890b0;"
      :style="{ paddingLeft: `${level * 12 + 8}px` }"
      @click="handleToggleExpand"
      @mouseover="$event.currentTarget.style.background = 'rgba(255,255,255,0.04)'; $event.currentTarget.style.color = '#c4c8d8';"
      @mouseout="$event.currentTarget.style.background = 'transparent'; $event.currentTarget.style.color = '#8890b0';"
    >
      <div style="display:flex; align-items:center; gap:6px; min-width:0; overflow:hidden;">
        <!-- Chevron -->
        <span
          style="display:inline-block; width:12px; font-size:0.6rem; text-align:center; color:#3a3f55; transition:transform 0.15s ease; flex-shrink:0;"
          :style="{ transform: isExpanded ? 'rotate(90deg)' : 'rotate(0deg)' }"
        >â–¶</span>
        <!-- Folder Icon -->
        <span style="font-size:0.9rem; flex-shrink:0;">{{ isExpanded ? 'ðŸ“‚' : 'ðŸ“' }}</span>
        <!-- Folder Name -->
        <span style="font-size:0.78rem; font-weight:500; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">
          {{ folder.name }}
        </span>
      </div>

      <!-- Quick Action Buttons on Hover -->
      <div
        class="group-hover-actions"
        style="display:none; align-items:center; gap:2px; flex-shrink:0;"
      >
        <button title="Nova Subpasta" @click="handleCreateSubfolder"
          style="padding:2px 5px; font-size:0.65rem; background:transparent; border:none; color:#4a5068; cursor:pointer; border-radius:4px;"
          @mouseover="$event.currentTarget.style.color='#c9a84c'; $event.currentTarget.style.background='rgba(201,168,76,0.1)';"
          @mouseout="$event.currentTarget.style.color='#4a5068'; $event.currentTarget.style.background='transparent';"
        >ðŸ“+</button>
        <button title="Novo Artigo nesta Pasta" @click="handleCreateArticle"
          style="padding:2px 5px; font-size:0.65rem; background:transparent; border:none; color:#4a5068; cursor:pointer; border-radius:4px;"
          @mouseover="$event.currentTarget.style.color='#c9a84c'; $event.currentTarget.style.background='rgba(201,168,76,0.1)';"
          @mouseout="$event.currentTarget.style.color='#4a5068'; $event.currentTarget.style.background='transparent';"
        >ðŸ“„+</button>
        <button title="Renomear" @click="handleRename"
          style="padding:2px 5px; font-size:0.65rem; background:transparent; border:none; color:#4a5068; cursor:pointer; border-radius:4px;"
          @mouseover="$event.currentTarget.style.color='#a0a8b8'; $event.currentTarget.style.background='rgba(255,255,255,0.05)';"
          @mouseout="$event.currentTarget.style.color='#4a5068'; $event.currentTarget.style.background='transparent';"
        >âœï¸</button>
        <button title="Excluir" @click="handleDelete"
          style="padding:2px 5px; font-size:0.65rem; background:transparent; border:none; color:#4a5068; cursor:pointer; border-radius:4px;"
          @mouseover="$event.currentTarget.style.color='#f87171'; $event.currentTarget.style.background='rgba(248,113,113,0.08)';"
          @mouseout="$event.currentTarget.style.color='#4a5068'; $event.currentTarget.style.background='transparent';"
        >ðŸ—‘ï¸</button>
      </div>
    </div>

    <!-- Folder Contents -->
    <div v-if="isExpanded">
      <!-- Subfolders Recursion -->
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

      <!-- Articles in Folder -->
      <div
        v-for="article in folder.articles"
        :key="article.id"
        style="display:flex; align-items:center; gap:7px; padding:4px 8px; border-radius:6px; font-size:0.75rem; cursor:pointer; transition:all 0.12s ease;"
        :style="{
          paddingLeft: `${(level + 1) * 12 + 20}px`,
          background: activeArticleId === article.id ? 'rgba(201,168,76,0.14)' : 'transparent',
          color: activeArticleId === article.id ? '#c9a84c' : '#6070a0',
          borderLeft: activeArticleId === article.id ? '2px solid #c9a84c' : 'none',
        }"
        @click="onSelectArticle(article.id)"
        @mouseover="if (activeArticleId !== article.id) ($event.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.04)'; ($event.currentTarget as HTMLElement).style.color = '#a0a8c0';"
        @mouseout="if (activeArticleId !== article.id) ($event.currentTarget as HTMLElement).style.background = 'transparent'; if (activeArticleId !== article.id) ($event.currentTarget as HTMLElement).style.color = '#6070a0';"
      >
        <span style="color:#2e3550; font-size:0.7rem; flex-shrink:0;">ðŸ“„</span>
        <span style="flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{{ article.title }}</span>
        <span v-if="article.visibility === 'NULA'" title="VisÃ£o Nula (Mestre)" style="font-size:0.65rem; flex-shrink:0;">ðŸ”’</span>
      </div>
    </div>
  </div>
</template>
