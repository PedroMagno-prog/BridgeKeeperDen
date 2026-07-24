<template>
  <div class="article-detail-page" v-if="article">
    <div class="top-nav">
      <router-link :to="`/worlds/${worldStore.activeWorldId}/codex`" class="back-link">
        &larr; Voltar ao Codex
      </router-link>
      <div class="actions">
        <button class="btn-secondary" @click="isEditing = !isEditing" v-if="canEdit">
          {{ isEditing ? 'Visualizar' : 'Editar Artigo' }}
        </button>
        <button class="btn-primary" v-if="isEditing" @click="saveChanges">
          Salvar Alterações
        </button>
      </div>
    </div>

    <!-- Cabeçalho do Artigo -->
    <header class="article-header card">
      <div class="header-main">
        <input
          v-if="isEditing"
          type="text"
          v-model="editTitle"
          class="input-field title-input"
        />
        <h1 v-else class="article-title">{{ article.title }}</h1>

        <!-- Selector de Visibilidade (Mestre) -->
        <div class="visibility-selector" v-if="worldStore.activeUserRole === 'MESTRE'">
          <label>Nível de Visão:</label>
          <select v-model="editVisibility" @change="saveVisibility" class="visibility-dropdown">
            <option value="TOTAL">Visão Total</option>
            <option value="PARCIAL">Visão Parcial</option>
            <option value="NULA">Visão Nula (Mestre Apenas)</option>
          </select>
        </div>
        <span v-else class="badge" :class="article.visibility === 'TOTAL' ? 'badge-total' : 'badge-parcial'">
          Visão: {{ article.visibility }}
        </span>
      </div>

      <div class="meta-bar">
        <div class="meta-item" v-if="article.in_game_date || isEditing">
          <span class="meta-label">Data In-Game:</span>
          <input v-if="isEditing" type="text" v-model="editDate" class="input-field small-input" placeholder="Ex: 1442 D.C." />
          <span v-else class="meta-val">{{ article.in_game_date || 'Não informada' }}</span>
        </div>

        <div class="tags-row">
          <span v-for="t in article.tags" :key="t" class="tag-chip">{{ t }}</span>
        </div>
      </div>
    </header>

    <!-- Seções de Conteúdo -->
    <main class="sections-container">
      <div v-for="(sec, idx) in editSections" :key="idx" class="section-card card">
        <div class="section-header">
          <input
            v-if="isEditing"
            type="text"
            v-model="sec.title"
            class="input-field section-title-input"
            placeholder="Título da Seção"
          />
          <h2 v-else class="section-title">{{ sec.title }}</h2>
          <button v-if="isEditing" class="remove-sec-btn" @click="removeSection(idx)">&times;</button>
        </div>

        <div class="section-body">
          <textarea
            v-if="isEditing"
            v-model="sec.content"
            class="input-field section-textarea"
            placeholder="Escreva aqui o conteúdo da seção... Suporta Markdown e @Mentions (ex: @[article:uuid])"
          ></textarea>
          <div v-else class="rendered-content" v-html="renderMentions(sec.content)"></div>
        </div>
      </div>

      <button v-if="isEditing" class="btn-secondary add-sec-btn" @click="addSection">
        + Adicionar Nova Seção
      </button>
    </main>

    <!-- Painel da Mochila / Inventário -->
    <section class="inventory-section card">
      <div class="inventory-header">
        <div class="inv-title">
          <svg class="inv-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
          </svg>
          <h3>Mochila & Inventário do Personagem</h3>
        </div>
        <button class="btn-secondary" @click="showAddInventoryModal = true" v-if="canEdit">
          + Item
        </button>
      </div>

      <table class="inventory-table" v-if="article.inventory_items && article.inventory_items.length > 0">
        <thead>
          <tr>
            <th>Item / Equipamento</th>
            <th>Qtd</th>
            <th>Descrição / Notas</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in article.inventory_items" :key="item.id">
            <td class="item-name">{{ item.item_name }}</td>
            <td class="item-qty">{{ item.quantity }}</td>
            <td class="item-desc">{{ item.description || '-' }}</td>
          </tr>
        </tbody>
      </table>

      <div class="empty-inv" v-else>
        <p>Nenhum item cadastrado no inventário deste personagem.</p>
      </div>
    </section>

    <!-- Modal Adicionar Item de Inventário -->
    <div class="modal-backdrop" v-if="showAddInventoryModal">
      <div class="modal-card card">
        <div class="modal-header">
          <h3>Adicionar Item à Mochila</h3>
          <button class="close-btn" @click="showAddInventoryModal = false">&times;</button>
        </div>
        <form @submit.prevent="handleAddItem" class="form">
          <div class="input-group">
            <label>Nome do Item *</label>
            <input type="text" v-model="newItemName" class="input-field" placeholder="Ex: Espada Longa de Aço Valiriano" required />
          </div>
          <div class="input-group">
            <label>Quantidade</label>
            <input type="number" v-model.number="newItemQty" class="input-field" min="1" required />
          </div>
          <div class="input-group">
            <label>Descrição / Detalhes</label>
            <input type="text" v-model="newItemDesc" class="input-field" placeholder="Dano 1d8+2, Mágica" />
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="showAddInventoryModal = false">Cancelar</button>
            <button type="submit" class="btn-primary">Adicionar Item</button>
          </div>
        </form>
      </div>
    </div>
  </div>

  <div class="loading-state card" v-else>
    <p>Carregando artigo...</p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useArticleStore } from '../stores/article'
import { useWorldStore } from '../stores/world'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const articleStore = useArticleStore()
const worldStore = useWorldStore()
const authStore = useAuthStore()

const isEditing = ref(false)
const editTitle = ref('')
const editVisibility = ref<'TOTAL' | 'PARCIAL' | 'NULA'>('NULA')
const editDate = ref('')
const editSections = ref<Array<{ title: string; content: string; order_index: number }>>([])

const showAddInventoryModal = ref(false)
const newItemName = ref('')
const newItemQty = ref(1)
const newItemDesc = ref('')

const article = computed(() => articleStore.currentArticle)
const canEdit = computed(() => {
  if (!article.value) return false
  return (
    worldStore.activeUserRole === 'MESTRE' ||
    article.value.created_by === authStore.user?.id
  )
})

onMounted(async () => {
  const articleId = route.params.articleId as string
  const worldId = route.params.worldId as string
  if (worldId && articleId) {
    await articleStore.fetchArticleById(worldId, articleId)
    if (article.value) {
      initEditState()
    }
  }
})

function initEditState() {
  if (!article.value) return
  editTitle.value = article.value.title
  editVisibility.value = article.value.visibility
  editDate.value = article.value.in_game_date || ''
  editSections.value = article.value.sections.map((s) => ({
    title: s.title,
    content: s.content,
    order_index: s.order_index,
  }))
}

function addSection() {
  editSections.value.push({
    title: 'Nova Seção',
    content: '',
    order_index: editSections.value.length,
  })
}

function removeSection(index: number) {
  editSections.value.splice(index, 1)
}

async function saveChanges() {
  if (!article.value || !worldStore.activeWorldId) return
  await articleStore.updateArticle(worldStore.activeWorldId, article.value.id, {
    title: editTitle.value,
    visibility: editVisibility.value,
    in_game_date: editDate.value || undefined,
    sections: editSections.value,
  })
  isEditing.value = false
}

async function saveVisibility() {
  if (!article.value || !worldStore.activeWorldId) return
  await articleStore.updateArticle(worldStore.activeWorldId, article.value.id, {
    visibility: editVisibility.value,
  })
}

async function handleAddItem() {
  if (!newItemName.value.trim() || !article.value || !worldStore.activeWorldId) return
  await articleStore.addInventoryItem(worldStore.activeWorldId, article.value.id, {
    item_name: newItemName.value,
    quantity: newItemQty.value,
    description: newItemDesc.value || undefined,
  })
  showAddInventoryModal.value = false
  newItemName.value = ''
  newItemQty.value = 1
  newItemDesc.value = ''
}

function renderMentions(text: string) {
  if (!text) return ''
  // Converte tags @[article:uuid] para marcação visual simples
  return text.replace(/@\[(article|pin):([a-f0-9-]+)\]/gi, (match, type, id) => {
    return `<span class="mention-tag" data-type="${type}" data-id="${id}">@[${type}:${id.substring(0, 8)}]</span>`
  })
}
</script>

<style scoped>
.article-detail-page {
  padding: 2rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.top-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.back-link {
  color: var(--accent-gold);
  text-decoration: none;
  font-weight: 500;

  &:hover {
    text-decoration: underline;
  }
}

.actions {
  display: flex;
  gap: 0.75rem;
}

.article-header {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.header-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.article-title {
  font-size: 1.8rem;
  font-weight: 700;
  color: var(--accent-gold);
}

.title-input {
  font-size: 1.5rem;
  font-weight: 700;
}

.visibility-selector {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  color: var(--text-muted);
}

.visibility-dropdown {
  background-color: var(--bg-main);
  border: 1px solid var(--border-color);
  color: var(--text-main);
  padding: 0.3rem 0.6rem;
  border-radius: 0.25rem;
}

.meta-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid var(--border-color);
  padding-top: 0.75rem;
  font-size: 0.85rem;
}

.meta-label {
  color: var(--text-muted);
  margin-right: 0.4rem;
}

.meta-val {
  color: var(--text-main);
  font-weight: 500;
}

.tag-chip {
  background-color: var(--bg-main);
  border: 1px solid var(--border-color);
  padding: 0.2rem 0.5rem;
  border-radius: 0.25rem;
  color: var(--accent-gold);
  font-size: 0.8rem;

  & + .tag-chip {
    margin-left: 0.4rem;
  }
}

.sections-container {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.section-card {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 0.5rem;
}

.section-title {
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--text-main);
}

.remove-sec-btn {
  background: transparent;
  border: none;
  color: var(--fow-nula);
  font-size: 1.2rem;
  cursor: pointer;
}

.section-textarea {
  min-height: 120px;
  resize: vertical;
}

.rendered-content {
  font-size: 0.95rem;
  line-height: 1.6;
  color: var(--text-main);
}

.add-sec-btn {
  align-self: flex-start;
}

/* Inventário */
.inventory-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.inventory-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.inv-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--accent-gold);
}

.inv-icon {
  width: 1.25rem;
  height: 1.25rem;
}

.inventory-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;

  th, td {
    padding: 0.6rem 0.8rem;
    text-align: left;
    border-bottom: 1px solid var(--border-color);
  }

  th {
    color: var(--text-muted);
    font-weight: 600;
    background-color: var(--bg-main);
  }

  .item-name {
    font-weight: 600;
    color: var(--text-main);
  }

  .item-qty {
    color: var(--accent-gold);
    font-weight: 700;
  }
}

.empty-inv {
  font-size: 0.85rem;
  color: var(--text-muted);
  font-style: italic;
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
  max-width: 420px;

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
