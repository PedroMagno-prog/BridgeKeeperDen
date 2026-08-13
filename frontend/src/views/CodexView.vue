<script setup lang="ts">
/**
 * TELA 2 + TELA 3: Codex — Lista + Detalhe + Edição de Artigos
 */
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useArticlesStore, type Article, type Visibility } from '@/stores/articles'
import { useWorldsStore } from '@/stores/worlds'
import VisibilityBadge from '@/components/ui/VisibilityBadge.vue'
import WikilinkText from '@/components/ui/WikilinkText.vue'
import WikilinkInput from '@/components/ui/WikilinkInput.vue'
import ObsidianImportModal from '@/components/codex/ObsidianImportModal.vue'
import PermissionsModal from '@/components/ui/PermissionsModal.vue'
import FolderTree from '@/components/codex/FolderTree.vue'
import FolderModal from '@/components/codex/FolderModal.vue'

const route = useRoute()
const router = useRouter()
const articlesStore = useArticlesStore()
const worldsStore = useWorldsStore()

const searchInput = ref('')
const activeTag = ref('')
const showCreateModal = ref(false)
const showEditModal = ref(false)
const showObsidianModal = ref(false)
const showPermModal = ref(false)
const showDetail = ref(false)
const showTagFilters = ref(true)

// Gestão de Pastas (Etapa 10)
const activeViewTab = ref<'tree' | 'flat'>('tree')
const showFolderModal = ref(false)
const folderModalMode = ref<'create' | 'rename'>('create')
const folderModalId = ref<number | null>(null)
const folderModalParentId = ref<number | null>(null)
const folderModalInitialName = ref('')
const createTargetFolderId = ref<number | null>(null)

const isMestre = computed(() => worldsStore.isMestre)
const canEdit = computed(() => isMestre.value || articlesStore.current?.can_edit !== false)
const canDelete = computed(() => isMestre.value || articlesStore.current?.can_delete !== false)

// ── Novo artigo ──────────────────────────────────────────────────────────────
const newTitle = ref('')
const newVisibility = ref<Visibility>('NULA')
const newTags = ref('')
const newInGameDate = ref('')
const newSections = ref([{ title: '', content: '' }])
const creating = ref(false)

// ── Editar artigo ────────────────────────────────────────────────────────────
const editTitle = ref('')
const editVisibility = ref<Visibility>('NULA')
const editTags = ref('')
const editInGameDate = ref('')
const editSections = ref<{ id?: string; title: string; content: string; image_url?: string | null }[]>([])
const editInGameSortOrder = ref<number | null>(null)
const saving = ref(false)
const uploadingImageIndex = ref<number | null>(null)

const allTags = computed(() => {
  const s = new Set<string>()
  articlesStore.articles.forEach((a) => a.tags?.forEach((t) => s.add(t)))
  return Array.from(s).sort()
})

onMounted(async () => {
  await articlesStore.fetchArticles()
  if (route.params.id) openArticle(route.params.id as string)
})

watch(() => route.params.id, (id) => {
  if (id) openArticle(id as string)
  else { showDetail.value = false; articlesStore.current = null }
})

function search() {
  articlesStore.searchQuery = searchInput.value
  articlesStore.tagFilter = activeTag.value
  articlesStore.fetchArticles()
}

function toggleTag(tag: string) {
  activeTag.value = activeTag.value === tag ? '' : tag
  search()
}

function handleOpenFolderModal(payload: { mode: 'create' | 'rename'; folderId?: number | null; parentId?: number | null; initialName?: string }) {
  folderModalMode.value = payload.mode
  folderModalId.value = payload.folderId || null
  folderModalParentId.value = payload.parentId || null
  folderModalInitialName.value = payload.initialName || ''
  showFolderModal.value = true
}

function handleCreateArticleInFolder(folderId?: number | null) {
  createTargetFolderId.value = folderId || null
  showCreateModal.value = true
}

async function openArticle(id: string) {
  const a = await articlesStore.fetchArticle(id)
  if (a) showDetail.value = true
}

function selectArticle(article: Article) {
  if (article.is_locked) return
  router.push(`/codex/${article.id}`)
}

// ── Criar ────────────────────────────────────────────────────────────────────
async function handleCreate() {
  if (!newTitle.value.trim()) return
  creating.value = true
  try {
    const tags = newTags.value.split(',').map((t) => t.trim()).filter(Boolean)
    const sections = newSections.value
      .filter((s) => s.title.trim())
      .map((s, i) => ({ title: s.title, content: s.content, order_index: i }))
    await articlesStore.createArticle({
      title: newTitle.value.trim(),
      folder_id: createTargetFolderId.value || null,
      visibility: newVisibility.value,
      tags,
      sections,
      in_game_date: newInGameDate.value || null,
    } as any)
    showCreateModal.value = false
    resetCreateForm()
  } finally { creating.value = false }
}

function resetCreateForm() {
  newTitle.value = ''; newVisibility.value = 'NULA'; newTags.value = ''
  newInGameDate.value = ''; newSections.value = [{ title: '', content: '' }]
  createTargetFolderId.value = null
}

function addCreateSection() { newSections.value.push({ title: '', content: '' }) }

// ── Editar ───────────────────────────────────────────────────────────────────
function openEditModal() {
  const a = articlesStore.current
  if (!a) return
  editTitle.value = a.title
  editVisibility.value = a.visibility
  editTags.value = a.tags?.join(', ') ?? ''
  editInGameDate.value = a.in_game_date ?? ''
  editInGameSortOrder.value = a.in_game_sort_order ?? null
  editSections.value = (a.sections ?? []).map((s) => ({
    id: s.id,
    title: s.title,
    content: s.content,
    image_url: s.image_url,
  }))
  if (editSections.value.length === 0) editSections.value.push({ title: '', content: '' })
  showEditModal.value = true
}

function addEditSection() { editSections.value.push({ title: '', content: '' }) }
function removeEditSection(i: number) { editSections.value.splice(i, 1) }

async function handleSectionImageUpload(index: number, event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  const a = articlesStore.current
  const sec = editSections.value[index]
  if (!file || !a || !sec || !sec.id) return

  uploadingImageIndex.value = index
  try {
    const url = await articlesStore.uploadSectionImage(a.id, sec.id, file)
    if (url && sec) {
      sec.image_url = url
      await articlesStore.fetchArticle(a.id)
    }
  } catch (err) {
    alert('Erro ao fazer upload da imagem.')
  } finally {
    uploadingImageIndex.value = null
  }
}

async function handleSave() {
  const a = articlesStore.current
  if (!a) return
  saving.value = true
  try {
    const tags = editTags.value.split(',').map((t) => t.trim()).filter(Boolean)
    const sections = editSections.value
      .filter((s) => s.title.trim())
      .map((s, i) => ({ title: s.title, content: s.content, order_index: i }))
    await articlesStore.updateArticle(a.id, {
      title: editTitle.value.trim(),
      visibility: editVisibility.value,
      tags,
      sections,
      in_game_date: editInGameDate.value || null,
      in_game_sort_order: editInGameSortOrder.value,
    } as any)
    showEditModal.value = false
  } finally { saving.value = false }
}

// ── Deletar ──────────────────────────────────────────────────────────────────
async function handleDelete(id: string) {
  if (!confirm('Remover este artigo permanentemente?')) return
  await articlesStore.deleteArticle(id)
  router.push('/codex')
}

function backToList() {
  showDetail.value = false
  articlesStore.current = null
  router.push('/codex')
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' })
}
</script>

<template>
  <div class="codex" :class="{ 'codex--detail-open': showDetail }">
    <!-- ═══ LISTA / ÁRVORE DE ARTIGOS ═══ -->
    <div class="codex__list">
      <div class="codex__toolbar flex items-center justify-between gap-2 p-3 border-b border-stone-800">
        <div class="flex items-center gap-2">
          <h2 class="codex__title text-base font-bold text-stone-200">Codex</h2>
          <div class="flex items-center bg-stone-950 border border-stone-800 rounded-lg p-0.5 text-xs">
            <button
              class="px-2 py-0.5 rounded transition-colors"
              :class="activeViewTab === 'tree' ? 'bg-amber-500/20 text-amber-300 font-semibold' : 'text-stone-400 hover:text-stone-200'"
              @click="activeViewTab = 'tree'"
            >
              📁 Árvore
            </button>
            <button
              class="px-2 py-0.5 rounded transition-colors"
              :class="activeViewTab === 'flat' ? 'bg-amber-500/20 text-amber-300 font-semibold' : 'text-stone-400 hover:text-stone-200'"
              @click="activeViewTab = 'flat'"
            >
              📋 Lista
            </button>
          </div>
        </div>

        <div v-if="isMestre" class="toolbar-btns flex items-center gap-1.5">
          <button class="btn-ghost-sm text-xs" title="Importar Cofre Obsidian (.zip)" @click="showObsidianModal = true">
            📥 Importar
          </button>
          <button class="btn-gold-sm text-xs" @click="handleCreateArticleInFolder(null)">
            + Novo
          </button>
        </div>
      </div>

      <!-- MODO ÁRVORE DE PASTAS (Etapa 10) -->
      <div v-if="activeViewTab === 'tree'" class="flex-1 overflow-hidden">
        <FolderTree
          :active-article-id="articlesStore.current?.id"
          @select-article="openArticle"
          @create-article="handleCreateArticleInFolder"
          @open-folder-modal="handleOpenFolderModal"
        />
      </div>

      <!-- MODO LISTA SIMPLES / BUSCA FLAT -->
      <div v-else class="flex-1 flex flex-col overflow-hidden">
        <div class="search-bar">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <input v-model="searchInput" type="text" placeholder="Buscar artigos..." class="search-bar__input" @keydown.enter="search" />
          <button
            v-if="allTags.length"
            class="btn-tag-toggle"
            :title="showTagFilters ? 'Ocultar Filtros de Tags' : 'Exibir Filtros de Tags'"
            @click="showTagFilters = !showTagFilters"
          >
            🏷️ {{ showTagFilters ? '▴' : '▾' }}
          </button>
        </div>

        <div v-if="showTagFilters && allTags.length" class="tag-pills">
          <button v-for="tag in allTags" :key="tag" class="tag-pill" :class="{ 'tag-pill--active': activeTag === tag }" @click="toggleTag(tag)">{{ tag }}</button>
        </div>

        <div class="article-list">
          <div v-if="articlesStore.loading" class="list-empty">Carregando...</div>
          <div v-else-if="articlesStore.articles.length === 0" class="list-empty">Nenhum artigo encontrado.</div>
          <button
            v-else v-for="article in articlesStore.articles" :key="article.id"
            class="article-row" :class="{ 'article-row--locked': article.is_locked, 'article-row--active': articlesStore.current?.id === article.id }"
            @click="selectArticle(article)"
          >
            <div class="article-row__main">
              <span class="article-row__title">
                {{ article.title }}
                <span v-if="article.is_locked" class="lock-icon">?</span>
              </span>
              <span v-if="article.in_game_date" class="article-row__date">{{ article.in_game_date }}</span>
            </div>
            <div class="article-row__meta">
              <span v-for="tag in article.tags" :key="tag" class="tag-inline">{{ tag }}</span>
              <VisibilityBadge v-if="isMestre" :visibility="article.visibility" />
            </div>
          </button>
        </div>
      </div>
    </div>

    <!-- ═══ DETALHE DO ARTIGO ═══ -->
    <Transition name="slide-right">
      <div v-if="showDetail && articlesStore.current" class="codex__detail">
        <div class="detail-header">
          <button class="back-btn" @click="backToList">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
          </button>
          <h1 class="detail-title">{{ articlesStore.current.title }}</h1>
          <div class="detail-actions">
            <VisibilityBadge v-if="isMestre" :visibility="articlesStore.current.visibility" size="md" />
            <button v-if="isMestre" class="btn-ghost-sm" title="Gerenciar Permissões" @click="showPermModal = true">
              🛡️ Permissões
            </button>
            <button v-if="canEdit" class="btn-icon" title="Editar" @click="openEditModal">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
            </button>
            <button v-if="canDelete" class="btn-icon btn-icon--danger" title="Deletar" @click="handleDelete(articlesStore.current.id)">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
                <path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
              </svg>
            </button>
          </div>
        </div>

        <div class="detail-meta">
          <div v-if="articlesStore.current.in_game_date" class="meta-item">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-dim)" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
            {{ articlesStore.current.in_game_date }}
          </div>
          <div class="meta-tags">
            <span v-for="tag in articlesStore.current.tags" :key="tag" class="tag-inline tag-inline--lg">{{ tag }}</span>
          </div>
          <span class="meta-date">Atualizado: {{ formatDate(articlesStore.current.updated_at) }}</span>
        </div>

        <div class="detail-sections">
          <div v-for="section in articlesStore.current.sections" :key="section.id" class="section-block">
            <h3 class="section-block__title">{{ section.title }}</h3>
            <div v-if="section.image_url" class="section-block__image-container">
              <img :src="section.image_url" alt="Imagem da Seção" class="section-block__image" />
            </div>
            <div class="section-block__content">
              <WikilinkText :text="section.content" />
            </div>
          </div>
          <div v-if="!articlesStore.current.sections?.length" class="list-empty" style="padding: 2rem;">Sem seções.</div>
        </div>


        <!-- ═══ PAINEL DE CONEXÕES & BACKLINKS ═══ -->
        <div class="backlinks-panel">
          <div class="ornament-divider">Conexões & Backlinks ({{ articlesStore.currentBacklinks.length }})</div>
          <div v-if="articlesStore.currentBacklinks.length > 0" class="backlinks-list">
            <div
              v-for="b in articlesStore.currentBacklinks"
              :key="b.article_id + b.section_title"
              class="backlink-card"
              @click="openArticle(b.article_id)"
            >
              <div class="backlink-card__header">
                <span class="backlink-card__title">📖 {{ b.title }}</span>
                <span class="backlink-card__section">Seção: {{ b.section_title }}</span>
              </div>
              <p class="backlink-card__snippet">{{ b.snippet }}</p>
            </div>
          </div>
          <div v-else class="empty-backlinks">
            Nenhum outro artigo cita este documento ainda.
          </div>
        </div>

        <div v-if="articlesStore.current.inventory_items?.length" class="inventory-panel">
          <div class="ornament-divider">Inventário</div>
          <table class="inv-table">
            <thead><tr><th>Item</th><th>Qtd</th><th>Descrição</th></tr></thead>
            <tbody>
              <tr v-for="item in articlesStore.current.inventory_items" :key="item.id">
                <td>{{ item.item_name }}</td>
                <td class="inv-qty">{{ item.quantity }}</td>
                <td class="inv-desc">{{ item.description ?? '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </Transition>

    <!-- ═══ MODAL CRIAR ARTIGO ═══ -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
          <div class="modal modal--wide" @click.stop>
            <h3 class="modal__title">Novo Artigo</h3>
            <div class="form-row">
              <div class="form-group form-group--flex"><label>Título</label><input v-model="newTitle" type="text" class="form-input" placeholder="Nome do artigo" autofocus /></div>
              <div class="form-group" style="width:140px;"><label>Visibilidade</label><select v-model="newVisibility" class="form-input"><option value="NULA">Nula</option><option value="PARCIAL">Parcial</option><option value="TOTAL">Total</option></select></div>
            </div>
            <div class="form-row">
              <div class="form-group form-group--flex"><label>Tags (vírgula)</label><input v-model="newTags" type="text" class="form-input" placeholder=".Local, .NPC" /></div>
              <div class="form-group" style="width:160px;"><label>Data In-Game</label><input v-model="newInGameDate" type="text" class="form-input" placeholder="1200 D.C." /></div>
            </div>
            <div class="ornament-divider" style="margin:0.75rem 0;">Seções</div>
            <div v-for="(sec, i) in newSections" :key="i" class="section-form">
              <input v-model="sec.title" type="text" class="form-input" :placeholder="`Título da seção ${i + 1}`" />
              <WikilinkInput v-model="sec.content" :rows="3" placeholder="Conteúdo da seção... Digite [[ para autocomplete de artigos." />
            </div>
            <button class="btn-link" @click="addCreateSection">+ Seção</button>
            <div class="modal__actions"><button class="btn btn--ghost" @click="showCreateModal = false">Cancelar</button><button class="btn btn--gold" @click="handleCreate" :disabled="creating || !newTitle.trim()">{{ creating ? 'Criando...' : 'Criar' }}</button></div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- ═══ MODAL EDITAR ARTIGO ═══ -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
          <div class="modal modal--wide" @click.stop>
            <h3 class="modal__title">Editar Artigo</h3>
            <div class="form-row">
              <div class="form-group form-group--flex"><label>Título</label><input v-model="editTitle" type="text" class="form-input" autofocus /></div>
              <div class="form-group" style="width:140px;"><label>Visibilidade</label><select v-model="editVisibility" class="form-input"><option value="NULA">Nula</option><option value="PARCIAL">Parcial</option><option value="TOTAL">Total</option></select></div>
            </div>
            <div class="form-row">
              <div class="form-group form-group--flex"><label>Tags (vírgula)</label><input v-model="editTags" type="text" class="form-input" /></div>
              <div class="form-group" style="width:160px;"><label>Data In-Game</label><input v-model="editInGameDate" type="text" class="form-input" /></div>
            </div>
            <div class="ornament-divider" style="margin:0.75rem 0;">Seções</div>
            <div v-for="(sec, i) in editSections" :key="i" class="section-form">
              <div class="section-form__header">
                <input v-model="sec.title" type="text" class="form-input" :placeholder="`Seção ${i + 1}`" />
                <button class="section-remove" title="Remover seção" @click="removeEditSection(i)">×</button>
              </div>
              <WikilinkInput v-model="sec.content" :rows="4" placeholder="Conteúdo da seção... Digite [[ para autocomplete de artigos." />
              <div v-if="sec.id" class="section-img-upload">
                <div v-if="sec.image_url" class="img-preview">
                  <img :src="sec.image_url" alt="Preview da imagem" class="thumb" />
                  <span class="img-filename">Imagem anexada</span>
                </div>
                <label class="btn-file-upload">
                  📷 {{ uploadingImageIndex === i ? 'Enviando...' : (sec.image_url ? 'Alterar Imagem (WebP)' : 'Anexar Imagem (WebP)') }}
                  <input type="file" accept="image/*" class="file-input-hidden" @change="handleSectionImageUpload(i, $event)" />
                </label>
              </div>
            </div>
            <button class="btn-link" @click="addEditSection">+ Adicionar Seção</button>
            <div class="modal__actions">
              <button class="btn btn--ghost" @click="showEditModal = false">Cancelar</button>
              <button class="btn btn--gold" @click="handleSave" :disabled="saving || !editTitle.trim()">{{ saving ? 'Salvando...' : 'Salvar Alterações' }}</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Modal Importar Obsidian -->
    <ObsidianImportModal
      :show="showObsidianModal"
      @close="showObsidianModal = false"
      @imported="articlesStore.fetchArticles()"
    />

    <!-- Modal Permissões Individuais por Jogador -->
    <PermissionsModal
      v-if="showPermModal && articlesStore.current"
      :article-id="articlesStore.current.id"
      @close="showPermModal = false"
    />

    <!-- Modal Gestão de Pastas (Etapa 10) -->
    <FolderModal
      :show="showFolderModal"
      :mode="folderModalMode"
      :folder-id="folderModalId"
      :parent-id="folderModalParentId"
      :initial-name="folderModalInitialName"
      @close="showFolderModal = false"
      @saved="showFolderModal = false"
    />
  </div>
</template>

<style scoped>
.btn-tag-toggle {
  background: var(--color-surface, #1f2937);
  color: var(--color-text-dim, #9ca3af);
  border: 1px solid var(--color-border, #374151);
  border-radius: 4px;
  padding: 0.25rem 0.6rem;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.btn-tag-toggle:hover {
  background: var(--color-surface-hover, #374151);
  color: var(--color-gold, #f3d17c);
}

.section-block__image-container {
  margin: var(--space-3) 0 var(--space-4);
}

.section-block__image {
  max-width: 100%;
  max-height: 400px;
  border-radius: var(--radius-md, 8px);
  border: 1px solid var(--color-border, #374151);
  object-fit: cover;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}

.section-img-upload {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-top: 0.5rem;
  padding: 0.4rem 0.6rem;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
  border: 1px dashed rgba(255, 255, 255, 0.15);
}

.img-preview {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.img-preview .thumb {
  width: 32px;
  height: 32px;
  border-radius: 4px;
  object-fit: cover;
}

.img-filename {
  font-size: 0.75rem;
  color: var(--color-text-dim, #9ca3af);
}

.btn-file-upload {
  font-size: 0.75rem;
  color: var(--color-gold-light, #f3d17c);
  cursor: pointer;
  background: rgba(243, 209, 124, 0.1);
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  border: 1px solid rgba(243, 209, 124, 0.3);
  transition: all 0.15s ease;
}

.btn-file-upload:hover {
  background: rgba(243, 209, 124, 0.2);
}

.file-input-hidden {
  display: none;
}
.ornament-divider {
  font-family: var(--font-display);
  font-size: 0.8rem;
  color: var(--color-gold);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  border-bottom: 1px solid var(--color-border);
  padding-bottom: 4px;
  margin: var(--space-6) 0 var(--space-4);
}

.backlinks-panel {
  margin-top: var(--space-6);
}

.backlinks-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.backlink-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-left: 3px solid var(--color-gold);
  border-radius: var(--radius-sm);
  padding: var(--space-3) var(--space-4);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.backlink-card:hover {
  background: var(--color-surface-2);
  border-color: var(--color-gold);
}

.backlink-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.backlink-card__title {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-gold);
}

.backlink-card__section {
  font-size: 0.75rem;
  color: var(--color-text-dim);
}

.backlink-card__snippet {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  font-style: italic;
}

.empty-backlinks {
  font-size: 0.8rem;
  color: var(--color-text-dim);
  font-style: italic;
  padding: var(--space-2) 0;
}

.codex { display: flex; gap: 0; height: calc(100vh - 56px); margin: calc(-1 * var(--space-6)) calc(-1 * var(--space-8)); }

/* Lista */
.codex__list { width: 380px; min-width: 300px; border-right: 1px solid var(--color-border); display: flex; flex-direction: column; overflow: hidden; flex-shrink: 0; }
.codex--detail-open .codex__list { width: 340px; }
.codex__toolbar { display: flex; align-items: center; justify-content: space-between; padding: var(--space-4); border-bottom: 1px solid var(--color-border); }
.codex__title { font-family: var(--font-display); font-size: 1.1rem; color: var(--color-gold); }

.toolbar-btns {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.btn-ghost-sm {
  padding: 5px 10px;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-gold);
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.btn-ghost-sm:hover {
  background: var(--color-gold-glow);
  border-color: var(--color-gold);
}

.btn-gold-sm { display: flex; align-items: center; gap: var(--space-1); padding: 6px 12px; background: var(--color-gold); color: #0d0f14; border: none; border-radius: var(--radius-sm); font-family: var(--font-body); font-weight: 600; font-size: 0.75rem; cursor: pointer; transition: all var(--transition-fast); }
.btn-gold-sm:hover { background: var(--color-gold-light); box-shadow: var(--shadow-gold); }

.search-bar { display: flex; align-items: center; gap: var(--space-2); margin: var(--space-3) var(--space-4); padding: var(--space-2) var(--space-3); background: var(--color-bg); border: 1px solid var(--color-border); border-radius: var(--radius-sm); color: var(--color-text-dim); }
.search-bar:focus-within { border-color: var(--color-gold-dim); }
.search-bar__input { flex: 1; background: none; border: none; outline: none; color: var(--color-text); font-family: var(--font-body); font-size: 0.8rem; }
.search-bar__input::placeholder { color: var(--color-text-dim); }

.tag-pills { display: flex; flex-wrap: wrap; gap: 6px; padding: 0 var(--space-4) var(--space-3); }
.tag-pill { padding: 3px 10px; border-radius: 14px; background: var(--color-surface-2); border: 1px solid var(--color-border); color: var(--color-text-muted); font-size: 0.7rem; cursor: pointer; font-family: var(--font-body); transition: all var(--transition-fast); }
.tag-pill:hover { border-color: var(--color-gold-dim); color: var(--color-gold); }
.tag-pill--active { background: var(--color-gold-glow); border-color: var(--color-gold-dim); color: var(--color-gold); }

.article-list { flex: 1; overflow-y: auto; }
.article-row { display: flex; flex-direction: column; gap: var(--space-1); width: 100%; padding: var(--space-3) var(--space-4); border: none; border-bottom: 1px solid var(--color-border); background: none; cursor: pointer; text-align: left; font-family: var(--font-body); color: var(--color-text); transition: background var(--transition-fast); }
.article-row:hover { background: var(--color-surface); }
.article-row--active { background: var(--color-surface-2); border-left: 3px solid var(--color-gold); }
.article-row--locked { opacity: 0.6; cursor: default; }
.article-row__main { display: flex; align-items: center; justify-content: space-between; gap: var(--space-2); }
.article-row__title { font-size: 0.875rem; font-weight: 500; display: flex; align-items: center; gap: 6px; }
.lock-icon { display: inline-flex; align-items: center; justify-content: center; width: 18px; height: 18px; border-radius: 50%; background: var(--color-gold-glow); color: var(--color-gold); font-size: 0.65rem; font-weight: 700; }
.article-row__date { font-size: 0.7rem; color: var(--color-text-dim); white-space: nowrap; }
.article-row__meta { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.tag-inline { font-size: 0.6rem; padding: 1px 6px; border-radius: 8px; background: var(--color-surface-2); color: var(--color-text-muted); }
.tag-inline--lg { font-size: 0.7rem; padding: 2px 8px; }

/* Detail */
.codex__detail { flex: 1; overflow-y: auto; padding: var(--space-6) var(--space-8); animation: slideIn 0.25s ease; }
@keyframes slideIn { from { opacity: 0; transform: translateX(12px); } to { opacity: 1; transform: translateX(0); } }
.detail-header { display: flex; align-items: center; gap: var(--space-3); margin-bottom: var(--space-4); }
.back-btn { display: flex; align-items: center; justify-content: center; width: 32px; height: 32px; border-radius: var(--radius-sm); border: 1px solid var(--color-border); background: none; color: var(--color-text-muted); cursor: pointer; transition: all var(--transition-fast); }
.back-btn:hover { border-color: var(--color-gold-dim); color: var(--color-gold); }
.detail-title { flex: 1; font-family: var(--font-display); font-size: 1.5rem; color: var(--color-text); }
.detail-actions { display: flex; align-items: center; gap: var(--space-2); }
.btn-icon { display: flex; align-items: center; justify-content: center; width: 32px; height: 32px; border-radius: var(--radius-sm); border: 1px solid var(--color-border); background: none; color: var(--color-text-muted); cursor: pointer; transition: all var(--transition-fast); }
.btn-icon:hover { border-color: var(--color-gold-dim); color: var(--color-gold); }
.btn-icon--danger:hover { border-color: var(--color-danger); color: var(--color-danger); }

.detail-meta { display: flex; align-items: center; gap: var(--space-4); margin-bottom: var(--space-6); flex-wrap: wrap; }
.meta-item { display: flex; align-items: center; gap: 6px; font-size: 0.8rem; color: var(--color-text-muted); }
.meta-tags { display: flex; gap: 6px; flex-wrap: wrap; }
.meta-date { font-size: 0.7rem; color: var(--color-text-dim); margin-left: auto; }

.detail-sections { display: flex; flex-direction: column; gap: var(--space-5); }
.section-block { padding: var(--space-5); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-md); }
.section-block__title { font-size: 0.9rem; font-weight: 600; color: var(--color-gold); margin-bottom: var(--space-3); }
.section-block__content { font-size: 0.875rem; line-height: 1.7; color: var(--color-text); white-space: pre-wrap; }

.inventory-panel { margin-top: var(--space-6); }
.inv-table { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
.inv-table th { text-align: left; padding: var(--space-2) var(--space-3); font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--color-text-dim); border-bottom: 1px solid var(--color-border); }
.inv-table td { padding: var(--space-2) var(--space-3); border-bottom: 1px solid var(--color-border); }
.inv-qty { font-weight: 600; color: var(--color-gold); text-align: center; width: 50px; }
.inv-desc { color: var(--color-text-muted); font-size: 0.75rem; }

.list-empty { padding: var(--space-8); text-align: center; color: var(--color-text-dim); font-size: 0.85rem; }

/* ═══ Modal ═══ */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.7); z-index: 300; display: flex; align-items: center; justify-content: center; backdrop-filter: blur(4px); }
.modal { background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); padding: var(--space-8); width: 100%; max-width: 440px; box-shadow: var(--shadow-lg); }
.modal--wide { max-width: 660px; max-height: 85vh; overflow-y: auto; }
.modal__title { font-size: 1.1rem; font-weight: 600; color: var(--color-gold); margin-bottom: var(--space-6); }
.form-row { display: flex; gap: var(--space-4); }
.form-group { display: flex; flex-direction: column; gap: var(--space-2); margin-bottom: var(--space-4); }
.form-group--flex { flex: 1; }
.form-group label { font-size: 0.75rem; color: var(--color-text-muted); text-transform: uppercase; letter-spacing: 0.06em; }
.form-input { background: var(--color-bg); border: 1px solid var(--color-border); border-radius: var(--radius-sm); color: var(--color-text); font-family: var(--font-body); font-size: 0.85rem; padding: var(--space-2) var(--space-3); resize: none; transition: border-color var(--transition-fast); }
.form-input:focus { outline: none; border-color: var(--color-gold-dim); }
.form-input--tall { min-height: 120px; line-height: 1.6; }
.section-form { display: flex; flex-direction: column; gap: var(--space-2); margin-bottom: var(--space-3); padding: var(--space-3); background: var(--color-bg); border: 1px solid var(--color-border); border-radius: var(--radius-sm); }
.section-form__header { display: flex; gap: var(--space-2); align-items: center; }
.section-form__header .form-input { flex: 1; }
.section-remove { width: 28px; height: 28px; border: 1px solid var(--color-border); border-radius: var(--radius-sm); background: none; color: var(--color-danger); cursor: pointer; font-size: 1rem; display: flex; align-items: center; justify-content: center; transition: all var(--transition-fast); }
.section-remove:hover { border-color: var(--color-danger); background: var(--color-danger-dim); }
.btn-link { background: none; border: none; color: var(--color-gold); font-family: var(--font-body); font-size: 0.8rem; cursor: pointer; text-align: left; padding: 0; }
.btn-link:hover { text-decoration: underline; }
.modal__actions { display: flex; gap: var(--space-3); justify-content: flex-end; margin-top: var(--space-6); }
.btn { padding: var(--space-2) var(--space-5); border-radius: var(--radius-sm); border: none; font-family: var(--font-body); font-size: 0.875rem; font-weight: 500; cursor: pointer; transition: all var(--transition-fast); }
.btn--ghost { background: none; border: 1px solid var(--color-border); color: var(--color-text-muted); }
.btn--ghost:hover { border-color: var(--color-text-muted); color: var(--color-text); }
.btn--gold { background: var(--color-gold); color: #0d0f14; font-weight: 600; }
.btn--gold:hover { background: var(--color-gold-light); box-shadow: var(--shadow-gold); }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.slide-right-enter-active { transition: all 0.3s ease; }
.slide-right-enter-from { opacity: 0; transform: translateX(20px); }
</style>
