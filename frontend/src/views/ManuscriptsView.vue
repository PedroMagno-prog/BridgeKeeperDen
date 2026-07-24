<template>
  <div class="manuscripts-page">
    <!-- Sidebar de Manuscritos & Capítulos -->
    <aside class="manuscripts-sidebar card">
      <div class="sidebar-top">
        <h3 class="title">Manuscritos</h3>
        <button
          class="btn-primary btn-sm"
          v-if="worldStore.activeUserRole === 'MESTRE'"
          @click="showCreateMsModal = true"
        >
          + Diário
        </button>
      </div>

      <!-- Lista de Livros / Manuscritos -->
      <div class="ms-list">
        <div
          v-for="ms in manuscriptStore.manuscripts"
          :key="ms.id"
          class="ms-item"
          :class="{ active: selectedMsId === ms.id }"
          @click="selectManuscript(ms.id)"
        >
          📖 {{ ms.title }}
        </div>
      </div>

      <div class="chapters-header" v-if="selectedMsId">
        <span class="chap-title">Capítulos & Sessões</span>
        <button
          class="btn-secondary btn-sm"
          v-if="worldStore.activeUserRole === 'MESTRE'"
          @click="showCreateChapterModal = true"
        >
          + Capítulo
        </button>
      </div>

      <!-- Lista de Capítulos -->
      <div class="chapters-list" v-if="selectedMsId">
        <div
          v-for="ch in manuscriptStore.currentChapters"
          :key="ch.id"
          class="chap-item"
          :class="{ active: selectedChapId === ch.id, locked: ch.is_locked }"
          @click="selectChapter(ch)"
        >
          <span class="chap-name">{{ ch.title }}</span>
          <span class="badge" :class="ch.visibility === 'TOTAL' ? 'badge-total' : 'badge-parcial'">
            {{ ch.visibility }}
          </span>
        </div>
      </div>
    </aside>

    <!-- Área de Leitura em Modo Foco -->
    <main class="manuscript-reader card" v-if="activeChapter">
      <header class="reader-header">
        <h1 class="chapter-main-title">{{ activeChapter.title }}</h1>
        <div class="header-line"></div>
      </header>

      <div class="reader-content" v-if="!activeChapter.is_locked">
        <div class="formatted-text" v-html="renderMentions(activeChapter.content)"></div>
      </div>

      <div class="locked-chapter card" v-else>
        <h3>🔒 Capítulo Oculto pelo Mestre</h3>
        <p>Os eventos deste diário de sessão ainda não foram revelados aos jogadores.</p>
      </div>
    </main>

    <div class="empty-reader card" v-else>
      <p>Selecione um manuscrito e capítulo na barra lateral para iniciar a leitura.</p>
    </div>

    <!-- Modal Criar Manuscrito -->
    <div class="modal-backdrop" v-if="showCreateMsModal">
      <div class="modal-card card">
        <div class="modal-header">
          <h3>Novo Manuscrito</h3>
          <button class="close-btn" @click="showCreateMsModal = false">&times;</button>
        </div>
        <form @submit.prevent="handleCreateMs" class="form">
          <div class="input-group">
            <label>Título do Diário / Livro *</label>
            <input type="text" v-model="newMsTitle" class="input-field" placeholder="Ex: Crônicas da Campanha Principal" required />
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="showCreateMsModal = false">Cancelar</button>
            <button type="submit" class="btn-primary">Criar</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal Criar Capítulo -->
    <div class="modal-backdrop" v-if="showCreateChapterModal">
      <div class="modal-card card">
        <div class="modal-header">
          <h3>Novo Capítulo de Sessão</h3>
          <button class="close-btn" @click="showCreateChapterModal = false">&times;</button>
        </div>
        <form @submit.prevent="handleCreateChapter" class="form">
          <div class="input-group">
            <label>Título da Sessão / Capítulo *</label>
            <input type="text" v-model="newChapTitle" class="input-field" placeholder="Ex: Sessão 01: O Resgate na Taverna" required />
          </div>
          <div class="input-group">
            <label>Conteúdo da Sessão</label>
            <textarea v-model="newChapContent" class="input-field textarea" placeholder="Escreva o resumo... Suporta @Mentions"></textarea>
          </div>
          <div class="input-group">
            <label>Visibilidade (Mestre)</label>
            <select v-model="newChapVisibility" class="input-field">
              <option value="NULA">Visão Nula (Invisível para Jogadores)</option>
              <option value="PARCIAL">Visão Parcial (Apenas Título)</option>
              <option value="TOTAL">Visão Total (Público)</option>
            </select>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="showCreateChapterModal = false">Cancelar</button>
            <button type="submit" class="btn-primary">Criar Capítulo</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useManuscriptStore, type ManuscriptChapter } from '../stores/manuscript'
import { useWorldStore } from '../stores/world'

const manuscriptStore = useManuscriptStore()
const worldStore = useWorldStore()

const selectedMsId = ref<string | null>(null)
const selectedChapId = ref<string | null>(null)
const activeChapter = ref<ManuscriptChapter | null>(null)

const showCreateMsModal = ref(false)
const newMsTitle = ref('')

const showCreateChapterModal = ref(false)
const newChapTitle = ref('')
const newChapContent = ref('')
const newChapVisibility = ref<'TOTAL' | 'PARCIAL' | 'NULA'>('NULA')

onMounted(async () => {
  if (worldStore.activeWorldId) {
    await manuscriptStore.fetchManuscripts(worldStore.activeWorldId)
    if (manuscriptStore.manuscripts.length > 0 && manuscriptStore.manuscripts[0]) {
      await selectManuscript(manuscriptStore.manuscripts[0].id)
    }
  }
})

async function selectManuscript(msId: string) {
  selectedMsId.value = msId
  if (worldStore.activeWorldId) {
    await manuscriptStore.fetchChapters(worldStore.activeWorldId, msId)
    if (manuscriptStore.currentChapters.length > 0 && manuscriptStore.currentChapters[0]) {
      selectChapter(manuscriptStore.currentChapters[0])
    } else {
      activeChapter.value = null
    }
  }
}

function selectChapter(chap: ManuscriptChapter) {
  selectedChapId.value = chap.id
  activeChapter.value = chap
}

async function handleCreateMs() {
  if (!newMsTitle.value.trim() || !worldStore.activeWorldId) return
  const created = await manuscriptStore.createManuscript(worldStore.activeWorldId, newMsTitle.value)
  showCreateMsModal.value = false
  newMsTitle.value = ''
  await selectManuscript(created.id)
}

async function handleCreateChapter() {
  if (!newChapTitle.value.trim() || !selectedMsId.value || !worldStore.activeWorldId) return
  await manuscriptStore.createChapter(worldStore.activeWorldId, selectedMsId.value, {
    title: newChapTitle.value,
    content: newChapContent.value,
    visibility: newChapVisibility.value,
  })
  showCreateChapterModal.value = false
  newChapTitle.value = ''
  newChapContent.value = ''
}

function renderMentions(text: string) {
  if (!text) return ''
  return text.replace(/@\[(article|pin):([a-f0-9-]+)\]/gi, (match, type, id) => {
    return `<span class="mention-tag" data-type="${type}" data-id="${id}">@[${type}:${id.substring(0, 8)}]</span>`
  })
}
</script>

<style scoped>
.manuscripts-page {
  display: flex;
  height: calc(100vh - 60px);
  padding: 1.5rem;
  gap: 1.5rem;
}

.manuscripts-sidebar {
  width: 300px;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  overflow-y: auto;
}

.sidebar-top {
  display: flex;
  justify-content: space-between;
  align-items: center;

  .title {
    color: var(--accent-gold);
    font-size: 1.1rem;
  }
}

.ms-list {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.ms-item {
  padding: 0.5rem 0.75rem;
  border-radius: 0.375rem;
  background-color: var(--bg-main);
  border: 1px solid var(--border-color);
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    border-color: var(--accent-gold);
  }

  &.active {
    background-color: rgba(212, 175, 55, 0.15);
    border-color: var(--accent-gold);
    color: var(--accent-gold);
    font-weight: 600;
  }
}

.chapters-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid var(--border-color);
  padding-top: 0.75rem;

  .chap-title {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text-muted);
  }
}

.chapters-list {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.chap-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0.75rem;
  border-radius: 0.375rem;
  background-color: var(--bg-main);
  border: 1px solid var(--border-color);
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover:not(.locked) {
    border-color: var(--accent-gold);
  }

  &.active {
    border-color: var(--accent-gold);
    background-color: var(--bg-hover);
  }

  &.locked {
    opacity: 0.6;
  }
}

.manuscript-reader {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  overflow-y: auto;
  padding: 2.5rem;
}

.reader-header {
  text-align: center;
}

.chapter-main-title {
  font-size: 2rem;
  font-weight: 700;
  color: var(--accent-gold);
  margin-bottom: 0.75rem;
}

.header-line {
  height: 2px;
  width: 100px;
  background-color: var(--accent-gold);
  margin: 0 auto;
}

.formatted-text {
  font-size: 1.05rem;
  line-height: 1.8;
  color: var(--text-main);
  max-width: 800px;
  margin: 0 auto;
}

.empty-reader {
  flex-grow: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
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
  max-width: 450px;
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

  .textarea {
    min-height: 120px;
  }
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 0.5rem;
}
</style>
