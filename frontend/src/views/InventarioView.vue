<script setup lang="ts">
/**
 * TELA: Inventário — Gestão de Grupos de Inventário, Inventários e Itens com Links para Codex
 */
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useInventoryStore, type InventoryGroup, type Inventory, type InventoryItem, type Visibility } from '@/stores/inventoryStore'
import { useArticlesStore } from '@/stores/articles'
import { useWorldsStore } from '@/stores/worlds'
import VisibilityBadge from '@/components/ui/VisibilityBadge.vue'

const router = useRouter()
const inventoryStore = useInventoryStore()
const articlesStore = useArticlesStore()
const worldsStore = useWorldsStore()

const activeTab = ref<'groups' | 'flat'>('groups')
const searchFilter = ref('')

const isMestre = computed(() => worldsStore.isMestre)

// ── Modais State ─────────────────────────────────────────────────────────────
const showGroupModal = ref(false)
const editingGroup = ref<InventoryGroup | null>(null)
const groupForm = ref({ name: '', description: '', visibility: 'NULA' as Visibility, icon: 'folder' })

const showInventoryModal = ref(false)
const editingInventory = ref<Inventory | null>(null)
const inventoryForm = ref({
  name: '',
  group_id: '' as string | null,
  owner_article_id: '' as string | null,
  description: '',
  limit: null as number | null,
  visibility: 'NULA' as Visibility,
})

const showItemModal = ref(false)
const targetInventory = ref<Inventory | null>(null)
const editingItem = ref<InventoryItem | null>(null)
const itemForm = ref({
  article_id: '' as string | null,
  custom_name: '',
  quantity: 1,
  notes: '',
})

onMounted(async () => {
  if (!worldsStore.activeWorld) {
    await worldsStore.fetchWorlds()
  }
  if (worldsStore.activeWorld) {
    await Promise.all([
      inventoryStore.fetchGroups(),
      inventoryStore.fetchInventories(),
      articlesStore.fetchArticles(),
    ])
  }
})

// ── Filtros ──────────────────────────────────────────────────────────────────
const filteredGroups = computed(() => {
  if (!searchFilter.value.trim()) return inventoryStore.groups
  const query = searchFilter.value.toLowerCase()
  return inventoryStore.groups.filter(
    (g) =>
      g.name.toLowerCase().includes(query) ||
      g.description?.toLowerCase().includes(query) ||
      g.inventories?.some((inv) => inv.name.toLowerCase().includes(query))
  )
})

const filteredInventories = computed(() => {
  if (!searchFilter.value.trim()) return inventoryStore.inventories
  const query = searchFilter.value.toLowerCase()
  return inventoryStore.inventories.filter(
    (inv) =>
      inv.name.toLowerCase().includes(query) ||
      inv.description?.toLowerCase().includes(query) ||
      inv.items?.some((i) => i.display_name.toLowerCase().includes(query))
  )
})

const standaloneInventories = computed(() => {
  return filteredInventories.value.filter((inv) => !inv.group_id)
})

// ── Handlers Grupo ───────────────────────────────────────────────────────────
function openCreateGroupModal() {
  editingGroup.value = null
  groupForm.value = {
    name: '',
    description: '',
    visibility: isMestre.value ? 'NULA' : 'TOTAL',
    icon: 'folder',
  }
  showGroupModal.value = true
}

function openEditGroupModal(group: InventoryGroup) {
  editingGroup.value = group
  groupForm.value = {
    name: group.name,
    description: group.description || '',
    visibility: group.visibility,
    icon: group.icon || 'folder',
  }
  showGroupModal.value = true
}

async function saveGroup() {
  if (!groupForm.value.name.trim()) return
  try {
    if (editingGroup.value) {
      await inventoryStore.updateGroup(editingGroup.value.id, groupForm.value)
    } else {
      await inventoryStore.createGroup(groupForm.value)
    }
    showGroupModal.value = false
  } catch (err: any) {
    alert(err?.response?.data?.detail || err?.message || 'Erro ao salvar grupo.')
  }
}

async function handleDeleteGroup(group: InventoryGroup) {
  if (confirm(`Tem certeza que deseja deletar o grupo "${group.name}"? Todos os inventários associados serão removidos.`)) {
    try {
      await inventoryStore.deleteGroup(group.id)
    } catch (err: any) {
      alert(err?.response?.data?.detail || err?.message || 'Erro ao deletar grupo.')
    }
  }
}

// ── Handlers Inventário ──────────────────────────────────────────────────────
function openCreateInventoryModal(groupId: string | null = null) {
  editingInventory.value = null
  inventoryForm.value = {
    name: '',
    group_id: groupId,
    owner_article_id: null,
    description: '',
    limit: null,
    visibility: isMestre.value ? 'NULA' : 'TOTAL',
  }
  showInventoryModal.value = true
}

function openEditInventoryModal(inv: Inventory) {
  editingInventory.value = inv
  inventoryForm.value = {
    name: inv.name,
    group_id: inv.group_id,
    owner_article_id: inv.owner_article_id,
    description: inv.description || '',
    limit: inv.limit,
    visibility: inv.visibility,
  }
  showInventoryModal.value = true
}

async function saveInventory() {
  if (!inventoryForm.value.name.trim()) return
  try {
    if (editingInventory.value) {
      await inventoryStore.updateInventory(editingInventory.value.id, inventoryForm.value)
    } else {
      await inventoryStore.createInventory(inventoryForm.value)
    }
    showInventoryModal.value = false
  } catch (err: any) {
    alert(err?.response?.data?.detail || err?.message || 'Erro ao salvar inventário.')
  }
}

async function handleDeleteInventory(inv: Inventory) {
  if (confirm(`Tem certeza que deseja remover o inventário "${inv.name}"?`)) {
    try {
      await inventoryStore.deleteInventory(inv.id)
    } catch (err: any) {
      alert(err?.response?.data?.detail || err?.message || 'Erro ao deletar inventário.')
    }
  }
}

// ── Handlers Itens ───────────────────────────────────────────────────────────
function openAddItemModal(inv: Inventory) {
  targetInventory.value = inv
  editingItem.value = null
  itemForm.value = {
    article_id: '',
    custom_name: '',
    quantity: 1,
    notes: '',
  }
  showItemModal.value = true
}

function openEditItemModal(inv: Inventory, item: InventoryItem) {
  targetInventory.value = inv
  editingItem.value = item
  itemForm.value = {
    article_id: item.article_id || '',
    custom_name: item.custom_name || '',
    quantity: item.quantity,
    notes: item.notes || '',
  }
  showItemModal.value = true
}

async function saveItem() {
  if (!targetInventory.value) return
  if (!itemForm.value.custom_name.trim() && !itemForm.value.article_id) return

  const payload = {
    article_id: itemForm.value.article_id || null,
    custom_name: itemForm.value.custom_name.trim() || null,
    quantity: itemForm.value.quantity,
    notes: itemForm.value.notes.trim() || null,
  }

  if (editingItem.value) {
    await inventoryStore.updateItem(targetInventory.value.id, editingItem.value.id, payload)
  } else {
    await inventoryStore.addItem(targetInventory.value.id, payload)
  }
  showItemModal.value = false
}

async function handleDeleteItem(inv: Inventory, item: InventoryItem) {
  if (confirm(`Remover "${item.display_name}" do inventário?`)) {
    await inventoryStore.deleteItem(inv.id, item.id)
  }
}

function navigateToArticle(articleId: string) {
  router.push(`/codex/${articleId}`)
}
</script>

<template>
  <div class="inventory-view">
    <!-- Topbar & Controles -->
    <header class="page-header">
      <div class="page-title">
        <h1>Inventários & Grupos</h1>
        <p class="subtitle">Organização de lojas, equipamentos e suprimentos do grupo de RPG</p>
      </div>

      <div class="header-actions">
        <!-- Input de Busca -->
        <div class="search-box">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input v-model="searchFilter" type="text" placeholder="Buscar inventário ou item..." />
        </div>

        <!-- Botões de Ação -->
        <button class="btn btn-secondary" @click="openCreateGroupModal">
          <span>+ Criar Grupo</span>
        </button>
        <button class="btn btn-primary" @click="openCreateInventoryModal(null)">
          <span>+ Criar Inventário</span>
        </button>
      </div>
    </header>

    <!-- Navegação de Abas -->
    <div class="view-tabs">
      <button
        class="tab-btn"
        :class="{ 'tab-btn--active': activeTab === 'groups' }"
        @click="activeTab = 'groups'"
      >
        Visão por Grupos ({{ filteredGroups.length }})
      </button>
      <button
        class="tab-btn"
        :class="{ 'tab-btn--active': activeTab === 'flat' }"
        @click="activeTab = 'flat'"
      >
        Todos os Inventários ({{ filteredInventories.length }})
      </button>
    </div>

    <!-- Conteúdo Principal: Grupos -->
    <div v-if="activeTab === 'groups'" class="groups-container">
      <div v-if="inventoryStore.loading" class="loading-state">
        <span>Carregando inventários...</span>
      </div>

      <div v-else-if="filteredGroups.length === 0 && standaloneInventories.length === 0" class="empty-state">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-dim)" stroke-width="1.5">
          <path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/>
          <path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/>
        </svg>
        <h3>Nenhum inventário cadastrado</h3>
        <p>Crie inventários para personagens, estabelecimentos ou baús do seu mundo.</p>
      </div>

      <!-- Lista de Grupos -->
      <div v-else class="groups-list">
        <section v-for="group in filteredGroups" :key="group.id" class="group-card">
          <!-- Cabeçalho do Grupo -->
          <div class="group-card__header">
            <div class="group-info">
              <span class="group-icon">📦</span>
              <div>
                <h2 class="group-title">
                  {{ group.name }}
                  <VisibilityBadge :visibility="group.visibility" size="sm" />
                </h2>
                <p v-if="group.description" class="group-desc">{{ group.description }}</p>
              </div>
            </div>

            <div class="group-actions">
              <button class="btn btn-xs btn-outline" @click="openCreateInventoryModal(group.id)">+ Add Inventário</button>
              <button class="icon-btn" title="Editar Grupo" @click="openEditGroupModal(group)">✏️</button>
              <button class="icon-btn icon-btn--danger" title="Excluir Grupo" @click="handleDeleteGroup(group)">🗑️</button>
            </div>
          </div>

          <!-- Inventários dentro do Grupo -->
          <div class="group-inventories">
            <div v-if="!group.inventories || group.inventories.length === 0" class="empty-group">
              <span>Nenhum inventário neste grupo ainda.</span>
            </div>

            <div v-for="inv in group.inventories" :key="inv.id" class="inventory-card">
              <div class="inv-header">
                <div class="inv-title-area">
                  <h3>
                    {{ inv.name }}
                    <VisibilityBadge :visibility="inv.visibility" size="sm" />
                  </h3>
                  <span v-if="inv.description" class="inv-desc">{{ inv.description }}</span>
                </div>

                <div class="inv-meta">
                  <!-- Badge de Capacidade / Aviso de Limite -->
                  <div
                    class="capacity-badge"
                    :class="{ 'capacity-badge--over': inv.is_over_limit }"
                    :title="inv.is_over_limit ? 'Atenção: A quantidade de itens ultrapassou o limite estipulado!' : 'Contagem de itens em relação ao limite'"
                  >
                    <span>Itens: {{ inv.items_count }}</span>
                    <span v-if="inv.limit !== null">/ {{ inv.limit }}</span>
                    <span v-if="inv.is_over_limit" class="warning-icon">⚠️ Acima do limite!</span>
                  </div>

                  <div class="inv-actions">
                    <button class="btn btn-xs btn-primary" @click="openAddItemModal(inv)">+ Item</button>
                    <button class="icon-btn" title="Editar Inventário" @click="openEditInventoryModal(inv)">✏️</button>
                    <button class="icon-btn icon-btn--danger" title="Excluir Inventário" @click="handleDeleteInventory(inv)">🗑️</button>
                  </div>
                </div>
              </div>

              <!-- Lista de Itens do Inventário -->
              <div class="items-table-wrapper">
                <table v-if="inv.items && inv.items.length > 0" class="items-table">
                  <thead>
                    <tr>
                      <th style="width: 80px;">Qtd</th>
                      <th>Item / Artigo</th>
                      <th>Anotações / Cargas</th>
                      <th style="width: 80px; text-align: right;">Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="item in inv.items" :key="item.id">
                      <td class="qty-col">
                        <span class="qty-badge">{{ item.quantity }}x</span>
                      </td>
                      <td class="name-col">
                        <div class="item-name-box">
                          <span class="display-name">{{ item.display_name }}</span>

                          <!-- Link direto para o Artigo do Codex se vinculado -->
                          <button
                            v-if="item.article"
                            class="article-link-badge"
                            title="Ver artigo no Codex"
                            @click="navigateToArticle(item.article.id)"
                          >
                            📖 {{ item.article.title }}
                          </button>
                        </div>
                      </td>
                      <td class="notes-col">{{ item.notes || '-' }}</td>
                      <td class="actions-col">
                        <button class="icon-btn" title="Editar item" @click="openEditItemModal(inv, item)">✏️</button>
                        <button class="icon-btn icon-btn--danger" title="Remover item" @click="handleDeleteItem(inv, item)">❌</button>
                      </td>
                    </tr>
                  </tbody>
                </table>
                <div v-else class="empty-items">
                  Mochila / Inventário vazio.
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- Inventários sem grupo (Avulsos) -->
        <section v-if="standaloneInventories.length > 0" class="group-card group-card--standalone">
          <div class="group-card__header">
            <div class="group-info">
              <span class="group-icon">📂</span>
              <div>
                <h2 class="group-title">Inventários Individuais (Sem Grupo)</h2>
                <p class="group-desc">Inventários não categorizados em nenhum grupo específico</p>
              </div>
            </div>
          </div>

          <div class="group-inventories">
            <div v-for="inv in standaloneInventories" :key="inv.id" class="inventory-card">
              <div class="inv-header">
                <div class="inv-title-area">
                  <h3>
                    {{ inv.name }}
                    <VisibilityBadge :visibility="inv.visibility" size="sm" />
                  </h3>
                  <span v-if="inv.description" class="inv-desc">{{ inv.description }}</span>
                </div>

                <div class="inv-meta">
                  <div
                    class="capacity-badge"
                    :class="{ 'capacity-badge--over': inv.is_over_limit }"
                  >
                    <span>Itens: {{ inv.items_count }}</span>
                    <span v-if="inv.limit !== null">/ {{ inv.limit }}</span>
                    <span v-if="inv.is_over_limit" class="warning-icon">⚠️ Acima do limite!</span>
                  </div>

                  <div class="inv-actions">
                    <button class="btn btn-xs btn-primary" @click="openAddItemModal(inv)">+ Item</button>
                    <button class="icon-btn" @click="openEditInventoryModal(inv)">✏️</button>
                    <button class="icon-btn icon-btn--danger" @click="handleDeleteInventory(inv)">🗑️</button>
                  </div>
                </div>
              </div>

              <div class="items-table-wrapper">
                <table v-if="inv.items && inv.items.length > 0" class="items-table">
                  <thead>
                    <tr>
                      <th style="width: 80px;">Qtd</th>
                      <th>Item / Artigo</th>
                      <th>Anotações / Cargas</th>
                      <th style="width: 80px; text-align: right;">Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="item in inv.items" :key="item.id">
                      <td class="qty-col"><span class="qty-badge">{{ item.quantity }}x</span></td>
                      <td class="name-col">
                        <div class="item-name-box">
                          <span class="display-name">{{ item.display_name }}</span>
                          <button v-if="item.article" class="article-link-badge" @click="navigateToArticle(item.article.id)">
                            📖 {{ item.article.title }}
                          </button>
                        </div>
                      </td>
                      <td class="notes-col">{{ item.notes || '-' }}</td>
                      <td class="actions-col">
                        <button class="icon-btn" @click="openEditItemModal(inv, item)">✏️</button>
                        <button class="icon-btn icon-btn--danger" @click="handleDeleteItem(inv, item)">❌</button>
                      </td>
                    </tr>
                  </tbody>
                </table>
                <div v-else class="empty-items">Inventário vazio.</div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>

    <!-- Visão Plana (Todos os Inventários) -->
    <div v-else class="flat-container">
      <div v-for="inv in filteredInventories" :key="inv.id" class="inventory-card">
        <div class="inv-header">
          <div class="inv-title-area">
            <h3>
              {{ inv.name }}
              <VisibilityBadge :visibility="inv.visibility" size="sm" />
            </h3>
            <span v-if="inv.description" class="inv-desc">{{ inv.description }}</span>
          </div>

          <div class="inv-meta">
            <div class="capacity-badge" :class="{ 'capacity-badge--over': inv.is_over_limit }">
              <span>Itens: {{ inv.items_count }}</span>
              <span v-if="inv.limit !== null">/ {{ inv.limit }}</span>
              <span v-if="inv.is_over_limit" class="warning-icon">⚠️ Acima do limite!</span>
            </div>

            <div class="inv-actions">
              <button class="btn btn-xs btn-primary" @click="openAddItemModal(inv)">+ Item</button>
              <button class="icon-btn" @click="openEditInventoryModal(inv)">✏️</button>
              <button class="icon-btn icon-btn--danger" @click="handleDeleteInventory(inv)">🗑️</button>
            </div>
          </div>
        </div>

        <div class="items-table-wrapper">
          <table v-if="inv.items && inv.items.length > 0" class="items-table">
            <thead>
              <tr>
                <th style="width: 80px;">Qtd</th>
                <th>Item / Artigo</th>
                <th>Anotações / Cargas</th>
                <th style="width: 80px; text-align: right;">Ações</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in inv.items" :key="item.id">
                <td class="qty-col"><span class="qty-badge">{{ item.quantity }}x</span></td>
                <td class="name-col">
                  <div class="item-name-box">
                    <span class="display-name">{{ item.display_name }}</span>
                    <button v-if="item.article" class="article-link-badge" @click="navigateToArticle(item.article.id)">
                      📖 {{ item.article.title }}
                    </button>
                  </div>
                </td>
                <td class="notes-col">{{ item.notes || '-' }}</td>
                <td class="actions-col">
                  <button class="icon-btn" @click="openEditItemModal(inv, item)">✏️</button>
                  <button class="icon-btn icon-btn--danger" @click="handleDeleteItem(inv, item)">❌</button>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-else class="empty-items">Inventário vazio.</div>
        </div>
      </div>
    </div>

    <!-- ── MODAL: Criar / Editar Grupo ──────────────────────────────────────── -->
    <div v-if="showGroupModal" class="modal-backdrop" @click.self="showGroupModal = false">
      <div class="modal">
        <h3>{{ editingGroup ? 'Editar Grupo de Inventário' : 'Novo Grupo de Inventário' }}</h3>

        <div class="form-group">
          <label>Nome do Grupo *</label>
          <input v-model="groupForm.name" type="text" placeholder="Ex: Lojas da Cidade de Oakhaven, Mochilas do Grupo" />
        </div>

        <div class="form-group">
          <label>Descrição</label>
          <textarea v-model="groupForm.description" rows="3" placeholder="Descrição ou notas sobre o grupo..."></textarea>
        </div>

        <div v-if="isMestre" class="form-group">
          <label>Nível de Visibilidade (Fog of War)</label>
          <select v-model="groupForm.visibility">
            <option value="NULA">Visão Nula (Invisível para Jogadores)</option>
            <option value="PARCIAL">Visão Parcial (Apenas nome visível)</option>
            <option value="TOTAL">Visão Total (Acesso completo)</option>
          </select>
        </div>

        <div class="modal-actions">
          <button class="btn btn-secondary" @click="showGroupModal = false">Cancelar</button>
          <button class="btn btn-primary" @click="saveGroup">Salvar Grupo</button>
        </div>
      </div>
    </div>

    <!-- ── MODAL: Criar / Editar Inventário ─────────────────────────────────── -->
    <div v-if="showInventoryModal" class="modal-backdrop" @click.self="showInventoryModal = false">
      <div class="modal">
        <h3>{{ editingInventory ? 'Editar Inventário' : 'Novo Inventário' }}</h3>

        <div class="form-group">
          <label>Nome do Inventário *</label>
          <input v-model="inventoryForm.name" type="text" placeholder="Ex: Armaria do Ferreiro, Mochila de Thorin" />
        </div>

        <div class="form-group">
          <label>Pertence ao Grupo</label>
          <select v-model="inventoryForm.group_id">
            <option :value="null">-- Nenhum (Inventário Independente) --</option>
            <option v-for="g in inventoryStore.groups" :key="g.id" :value="g.id">{{ g.name }}</option>
          </select>
        </div>

        <div class="form-group">
          <label>Capacidade Máxima / Limite de Itens (Aviso)</label>
          <input v-model.number="inventoryForm.limit" type="number" min="0" placeholder="Ex: 10 (Deixe vazio para ilimitado)" />
          <small class="hint">Caso o número de itens ultrapasse este limite, um aviso visual ⚠️ será exibido na tela.</small>
        </div>

        <div class="form-group">
          <label>Descrição / Notas</label>
          <textarea v-model="inventoryForm.description" rows="2" placeholder="Localização, dono ou peculiaridades..."></textarea>
        </div>

        <div v-if="isMestre" class="form-group">
          <label>Nível de Visibilidade (Fog of War)</label>
          <select v-model="inventoryForm.visibility">
            <option value="NULA">Visão Nula (Invisível para Jogadores)</option>
            <option value="PARCIAL">Visão Parcial (Apenas nome visível)</option>
            <option value="TOTAL">Visão Total (Acesso completo)</option>
          </select>
        </div>

        <div class="modal-actions">
          <button class="btn btn-secondary" @click="showInventoryModal = false">Cancelar</button>
          <button class="btn btn-primary" @click="saveInventory">Salvar Inventário</button>
        </div>
      </div>
    </div>

    <!-- ── MODAL: Criar / Editar Item do Inventário ─────────────────────────── -->
    <div v-if="showItemModal" class="modal-backdrop" @click.self="showItemModal = false">
      <div class="modal">
        <h3>{{ editingItem ? 'Editar Item do Inventário' : 'Adicionar Item ao Inventário' }}</h3>

        <div class="form-group">
          <label>Vincular a um Artigo do Codex (Item/Lore)</label>
          <select v-model="itemForm.article_id">
            <option :value="''">-- Sem vínculo com Artigo --</option>
            <option v-for="art in articlesStore.articles" :key="art.id" :value="art.id">
              {{ art.title }} ({{ art.visibility }})
            </option>
          </select>
          <small class="hint">Vincular a um Artigo permite clicar no item para abrir a lore/ficha completa do Codex.</small>
        </div>

        <div class="form-group">
          <label>Nome do Item / Apelido Customizado</label>
          <input v-model="itemForm.custom_name" type="text" placeholder="Ex: Espada de Família (ou deixe vazio para usar o título do Artigo)" />
        </div>

        <div class="form-group">
          <label>Quantidade</label>
          <input v-model.number="itemForm.quantity" type="number" min="1" />
        </div>

        <div class="form-group">
          <label>Anotações / Cargas / Estado</label>
          <input v-model="itemForm.notes" type="text" placeholder="Ex: 3 cargas de fogo restantes, gasta" />
        </div>

        <div class="modal-actions">
          <button class="btn btn-secondary" @click="showItemModal = false">Cancelar</button>
          <button class="btn btn-primary" @click="saveItem">Salvar Item</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.inventory-view {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
  max-width: 1200px;
  margin: 0 auto;
}

/* Page Header */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-4);
}

.page-title h1 {
  font-family: var(--font-display);
  font-size: 1.6rem;
  color: var(--color-gold);
  margin-bottom: var(--space-1);
}

.subtitle {
  color: var(--color-text-dim);
  font-size: 0.875rem;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
}

/* Search Box */
.search-box {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 6px 12px;
  color: var(--color-text-muted);
}
.search-box input {
  background: none;
  border: none;
  color: var(--color-text);
  outline: none;
  font-size: 0.85rem;
  width: 180px;
}

/* View Tabs */
.view-tabs {
  display: flex;
  gap: var(--space-2);
  border-bottom: 1px solid var(--color-border);
  padding-bottom: var(--space-2);
}

.tab-btn {
  background: none;
  border: none;
  color: var(--color-text-muted);
  font-family: var(--font-body);
  font-size: 0.9rem;
  font-weight: 500;
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.tab-btn:hover {
  background: var(--color-surface-2);
  color: var(--color-text);
}

.tab-btn--active {
  background: var(--color-gold-glow);
  color: var(--color-gold);
  font-weight: 600;
}

/* Group Cards */
.groups-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.group-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-5);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.group-card--standalone {
  border-style: dashed;
}

.group-card__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--color-border);
}

.group-info {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
}

.group-icon {
  font-size: 1.5rem;
}

.group-title {
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--color-text);
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.group-desc {
  font-size: 0.85rem;
  color: var(--color-text-dim);
  margin-top: 2px;
}

.group-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

/* Inventories Inside Group */
.group-inventories {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.inventory-card {
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: var(--space-4);
}

.inv-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-3);
  flex-wrap: wrap;
  gap: var(--space-3);
}

.inv-title-area h3 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-gold);
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.inv-desc {
  font-size: 0.8rem;
  color: var(--color-text-dim);
}

.inv-meta {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

/* Capacity Badge */
.capacity-badge {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--color-border);
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 0.75rem;
  color: var(--color-text-muted);
  display: flex;
  align-items: center;
  gap: 6px;
}

.capacity-badge--over {
  background: rgba(239, 68, 68, 0.15);
  border-color: rgba(239, 68, 68, 0.4);
  color: #EF4444;
  font-weight: 600;
  animation: pulseWarning 2s infinite;
}

@keyframes pulseWarning {
  0% { border-color: rgba(239, 68, 68, 0.4); }
  50% { border-color: rgba(239, 68, 68, 0.8); }
  100% { border-color: rgba(239, 68, 68, 0.4); }
}

.inv-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

/* Items Table */
.items-table-wrapper {
  overflow-x: auto;
}

.items-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.items-table th {
  text-align: left;
  padding: 8px 12px;
  color: var(--color-text-dim);
  border-bottom: 1px solid var(--color-border);
  font-weight: 500;
}

.items-table td {
  padding: 8px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  color: var(--color-text);
  vertical-align: middle;
}

.qty-badge {
  font-weight: 700;
  color: var(--color-gold);
  background: var(--color-gold-glow);
  padding: 2px 6px;
  border-radius: 4px;
}

.item-name-box {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.display-name {
  font-weight: 500;
}

.article-link-badge {
  background: rgba(201, 168, 76, 0.15);
  color: var(--color-gold);
  border: 1px solid rgba(201, 168, 76, 0.3);
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.article-link-badge:hover {
  background: rgba(201, 168, 76, 0.3);
}

.empty-items, .empty-group, .empty-state {
  text-align: center;
  padding: var(--space-6);
  color: var(--color-text-dim);
  font-size: 0.85rem;
}

.empty-state h3 {
  color: var(--color-text);
  margin-top: var(--space-3);
  margin-bottom: var(--space-1);
}

/* Modais */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  backdrop-filter: blur(4px);
}

.modal {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-6);
  width: 100%;
  max-width: 500px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.modal h3 {
  font-family: var(--font-display);
  font-size: 1.2rem;
  color: var(--color-gold);
  border-bottom: 1px solid var(--color-border);
  padding-bottom: var(--space-2);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--color-text-muted);
}

.form-group input, .form-group textarea, .form-group select {
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 8px 12px;
  color: var(--color-text);
  font-family: var(--font-body);
  font-size: 0.875rem;
  outline: none;
}

.form-group input:focus, .form-group textarea:focus, .form-group select:focus {
  border-color: var(--color-gold);
}

.hint {
  font-size: 0.75rem;
  color: var(--color-text-dim);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
  margin-top: var(--space-2);
}

.btn {
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all var(--transition-fast);
}

.btn-primary { background: var(--color-gold); color: #111827; }
.btn-primary:hover { opacity: 0.9; }

.btn-secondary { background: var(--color-surface-2); color: var(--color-text); }
.btn-secondary:hover { background: var(--color-border); }

.btn-outline { background: none; border: 1px solid var(--color-border); color: var(--color-text-muted); }
.btn-outline:hover { border-color: var(--color-gold); color: var(--color-gold); }

.btn-xs { padding: 4px 8px; font-size: 0.75rem; }

.icon-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 0.85rem;
  opacity: 0.7;
  transition: opacity 0.2s;
  padding: 4px;
}

.icon-btn:hover { opacity: 1; }
.icon-btn--danger:hover { opacity: 1; filter: drop-shadow(0 0 4px red); }
</style>
