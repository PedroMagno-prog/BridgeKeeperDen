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

function onSelectArticle(articleId: string) {
  emit('select-article', articleId)
}

function handleCreateRootFolder() {
  emit('open-folder-modal', { mode: 'create', parentId: null })
}

function handleCreateSubfolder(parentId: number) {
  emit('open-folder-modal', { mode: 'create', parentId })
}

function handleCreateArticle(folderId?: number | null) {
  emit('create-article', folderId)
}

function handleRenameFolder(payload: { folderId: number; name: string }) {
  emit('open-folder-modal', {
    mode: 'rename',
    folderId: payload.folderId,
    initialName: payload.name,
  })
}

async function handleDeleteFolder(folderId: number) {
  await articlesStore.removeFolder(folderId)
}
</script>

<template>
  <div class="flex flex-col h-full bg-stone-900/90 border-r border-stone-800/80 text-stone-200 select-none">
    <!-- Top Action Bar -->
    <div class="p-3 border-b border-stone-800 space-y-2">
      <div class="flex items-center justify-between">
        <h2 class="text-xs font-semibold text-stone-400 uppercase tracking-wider flex items-center gap-1.5">
          <span>📚</span> Codex & Cofre
        </h2>
        <div class="flex items-center gap-1">
          <button
            @click="handleCreateRootFolder"
            title="Nova Pasta Raiz"
            class="p-1 text-xs bg-stone-800 hover:bg-stone-700 text-stone-300 hover:text-amber-300 rounded border border-stone-700/60 transition-colors"
          >
            📁+
          </button>
          <button
            @click="() => handleCreateArticle(null)"
            title="Novo Artigo Raiz"
            class="p-1 text-xs bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 rounded border border-amber-500/30 transition-colors"
          >
            📄+
          </button>
        </div>
      </div>

      <!-- Quick Filter Input -->
      <div class="relative">
        <input
          v-model="filterText"
          type="text"
          placeholder="Filtrar por nome..."
          class="w-full pl-7 pr-3 py-1 text-xs bg-stone-950/80 border border-stone-800 rounded-md text-stone-200 placeholder-stone-500 focus:outline-none focus:border-amber-500/50"
        />
        <span class="absolute left-2 top-1.5 text-xs text-stone-500">🔍</span>
      </div>
    </div>

    <!-- Tree Content Scroll Area -->
    <div class="flex-1 overflow-y-auto p-2 space-y-1 custom-scrollbar">
      <!-- Loading State -->
      <div v-if="articlesStore.loading" class="p-4 text-center text-xs text-stone-500 animate-pulse">
        Carregando estrutura...
      </div>

      <template v-else>
        <!-- Root Folders List -->
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

        <!-- Root Articles (folder_id === null) -->
        <div v-if="filteredRootArticles.length > 0" class="pt-2 border-t border-stone-800/40">
          <div class="px-2 py-1 text-[11px] font-semibold text-stone-500 uppercase tracking-wider">
            Artigos Raiz
          </div>
          <div
            v-for="article in filteredRootArticles"
            :key="article.id"
            class="flex items-center gap-2 py-1 px-2.5 rounded-md text-xs cursor-pointer transition-colors"
            :class="[
              activeArticleId === article.id
                ? 'bg-amber-500/20 text-amber-300 font-medium border-l-2 border-amber-400'
                : 'text-stone-400 hover:text-stone-200 hover:bg-stone-800/40'
            ]"
            @click="onSelectArticle(article.id)"
          >
            <span class="text-stone-500">📄</span>
            <span class="truncate flex-1">{{ article.title }}</span>
            <span v-if="article.visibility === 'NULA'" title="Visão Nula (Mestre)" class="text-xs">🔒</span>
          </div>
        </div>

        <!-- Empty State -->
        <div
          v-if="articlesStore.folderTree.length === 0 && articlesStore.rootArticles.length === 0"
          class="p-6 text-center text-xs text-stone-500 space-y-2"
        >
          <p>Nenhuma pasta ou artigo encontrado.</p>
          <button
            @click="handleCreateRootFolder"
            class="px-3 py-1 bg-stone-800 hover:bg-stone-700 text-amber-400 rounded-md transition-colors"
          >
            Criar Primeira Pasta
          </button>
        </div>
      </template>
    </div>
  </div>
</template>
