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
    <div class="flex flex-col h-full text-stone-200 select-none" style="background:#111520; border-right:1px solid #1e2335;">
    <!-- Top Action Bar -->
    <div style="padding:10px 12px; border-bottom:1px solid #1a1d28; background:#0c0e18; flex-shrink:0;">
      <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px;">
        <h2 style="font-size:0.68rem; font-weight:600; color:#5a6080; text-transform:uppercase; letter-spacing:0.08em; display:flex; align-items:center; gap:6px; margin:0;">
          📚 Codex &amp; Cofre
        </h2>
        <div style="display:flex; align-items:center; gap:4px;">
          <button
            @click="handleCreateRootFolder"
            title="Nova Pasta Raiz"
            style="padding:4px 8px; font-size:0.72rem; background:rgba(30,36,60,0.9); border:1px solid #2e3560; border-radius:6px; color:#8890b0; cursor:pointer; transition:all 0.15s ease; line-height:1;"
            onmouseover="this.style.color='#c9a84c'; this.style.borderColor='rgba(201,168,76,0.4)';"
            onmouseout="this.style.color='#8890b0'; this.style.borderColor='#2e3560';"
          >
            📁+
          </button>
          <button
            @click="() => handleCreateArticle(null)"
            title="Novo Artigo Raiz"
            style="padding:4px 8px; font-size:0.72rem; background:rgba(201,168,76,0.1); border:1px solid rgba(201,168,76,0.25); border-radius:6px; color:#c9a84c; cursor:pointer; transition:all 0.15s ease; line-height:1;"
            onmouseover="this.style.background='rgba(201,168,76,0.2)';"
            onmouseout="this.style.background='rgba(201,168,76,0.1)';"
          >
            📄+
          </button>
        </div>
      </div>

      <!-- Quick Filter Input -->
      <div style="position:relative;">
        <input
          v-model="filterText"
          type="text"
          placeholder="Filtrar por nome..."
          style="width:100%; padding:5px 10px 5px 28px; font-size:0.75rem; background:#080b14; border:1px solid #1e2335; border-radius:6px; color:#c4c8d8; outline:none; font-family:inherit; box-sizing:border-box;"
          @focus="$event.target.style.borderColor='rgba(201,168,76,0.4)'"
          @blur="$event.target.style.borderColor='#1e2335'"
        />
        <span style="position:absolute; left:8px; top:50%; transform:translateY(-50%); font-size:0.7rem; color:#3a3f55; pointer-events:none;">🔍</span>
      </div>
    </div>

    <!-- Tree Content Scroll Area -->
    <div style="flex:1; overflow-y:auto; padding:8px; scrollbar-width:thin; scrollbar-color:#2e3350 transparent;">
      <!-- Loading State -->
      <div v-if="articlesStore.loading" style="padding:16px; text-align:center; font-size:0.75rem; color:#3a3f55;">
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
        <div v-if="filteredRootArticles.length > 0" style="padding-top:8px; border-top:1px solid #1a1d28; margin-top:4px;">
          <div style="padding:4px 8px; font-size:0.65rem; font-weight:600; color:#3a3f55; text-transform:uppercase; letter-spacing:0.08em;">
            Artigos Raiz
          </div>
          <div
            v-for="article in filteredRootArticles"
            :key="article.id"
            style="display:flex; align-items:center; gap:7px; padding:5px 10px; border-radius:6px; font-size:0.78rem; cursor:pointer; transition:all 0.12s ease;"
            :style="activeArticleId === article.id
              ? 'background:rgba(201,168,76,0.14); color:#c9a84c; border-left:2px solid #c9a84c; padding-left:8px;'
              : 'color:#7080a0;'"
            @click="onSelectArticle(article.id)"
            @mouseover="$event.currentTarget.style.background = activeArticleId === article.id ? 'rgba(201,168,76,0.14)' : 'rgba(255,255,255,0.04)'"
            @mouseout="$event.currentTarget.style.background = activeArticleId === article.id ? 'rgba(201,168,76,0.14)' : 'transparent'"
          >
            <span style="color:#3a3f55; font-size:0.75rem;">📄</span>
            <span style="flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{{ article.title }}</span>
            <span v-if="article.visibility === 'NULA'" title="Visão Nula (Mestre)" style="font-size:0.7rem;">🔒</span>
          </div>
        </div>

        <!-- Empty State -->
        <div
          v-if="articlesStore.folderTree.length === 0 && articlesStore.rootArticles.length === 0"
          style="padding:24px 16px; text-align:center; font-size:0.78rem; color:#3a3f55;"
        >
          <p style="margin-bottom:12px;">Nenhuma pasta ou artigo encontrado.</p>
          <button
            @click="handleCreateRootFolder"
            style="padding:6px 14px; background:#1a1d28; border:1px solid #2e3560; border-radius:6px; color:#c9a84c; font-size:0.78rem; cursor:pointer;"
          >
            Criar Primeira Pasta
          </button>
        </div>
        </div>
      </template>
    </div>
  </div>
</template>
