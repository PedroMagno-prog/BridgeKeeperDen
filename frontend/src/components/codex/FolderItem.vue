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
  <div class="user-select-none">
    <!-- Folder Header Row -->
    <div
      class="group relative flex items-center justify-between py-1.5 px-2 rounded-lg text-sm transition-colors cursor-pointer text-stone-300 hover:text-stone-100 hover:bg-stone-800/60"
      :style="{ paddingLeft: `${level * 12 + 8}px` }"
      @click="handleToggleExpand"
    >
      <div class="flex items-center gap-1.5 min-w-0 truncate">
        <!-- Chevron -->
        <span
          class="inline-block w-4 h-4 text-center text-xs text-stone-400 group-hover:text-amber-400 transition-transform"
          :class="{ 'rotate-90': isExpanded }"
        >
          ▶
        </span>
        <!-- Folder Icon -->
        <span class="text-amber-400 text-base">
          {{ isExpanded ? '📂' : '📁' }}
        </span>
        <!-- Folder Name -->
        <span class="truncate font-medium text-stone-200 group-hover:text-stone-100">
          {{ folder.name }}
        </span>
      </div>

      <!-- Quick Action Buttons on Hover -->
      <div class="hidden group-hover:flex items-center gap-1 text-stone-400 text-xs">
        <button
          title="Nova Subpasta"
          @click="handleCreateSubfolder"
          class="p-1 hover:text-amber-300 hover:bg-stone-700/80 rounded"
        >
          📁+
        </button>
        <button
          title="Novo Artigo nesta Pasta"
          @click="handleCreateArticle"
          class="p-1 hover:text-amber-300 hover:bg-stone-700/80 rounded"
        >
          📄+
        </button>
        <button
          title="Renomear"
          @click="handleRename"
          class="p-1 hover:text-stone-200 hover:bg-stone-700/80 rounded"
        >
          ✏️
        </button>
        <button
          title="Excluir"
          @click="handleDelete"
          class="p-1 hover:text-rose-400 hover:bg-stone-700/80 rounded"
        >
          🗑️
        </button>
      </div>
    </div>

    <!-- Folder Contents (Children Folders + Folder Articles) -->
    <div v-if="isExpanded" class="mt-0.5">
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
        class="flex items-center gap-2 py-1 px-2 rounded-md text-xs cursor-pointer transition-colors"
        :style="{ paddingLeft: `${(level + 1) * 12 + 16}px` }"
        :class="[
          activeArticleId === article.id
            ? 'bg-amber-500/20 text-amber-300 font-medium border-l-2 border-amber-400'
            : 'text-stone-400 hover:text-stone-200 hover:bg-stone-800/40'
        ]"
        @click="onSelectArticle(article.id)"
      >
        <span class="text-stone-500">📄</span>
        <span class="truncate">{{ article.title }}</span>
        <span v-if="article.visibility === 'NULA'" title="Visão Nula (Mestre)" class="text-xs">🔒</span>
      </div>
    </div>
  </div>
</template>
