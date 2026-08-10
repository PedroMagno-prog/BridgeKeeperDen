<script setup lang="ts">
/**
 * TELA 6: Manuscritos & Diário de Sessão — com edição inline de capítulos
 */
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useManuscriptsStore, type Manuscript, type Chapter } from '@/stores/manuscripts'
import { useWorldsStore } from '@/stores/worlds'
import VisibilityBadge from '@/components/ui/VisibilityBadge.vue'

const manuscriptsStore = useManuscriptsStore()
const worldsStore = useWorldsStore()
const isMestre = computed(() => worldsStore.isMestre)

const activeChapter = ref<Chapter | null>(null)
const showNewManuscript = ref(false)
const showNewChapter = ref(false)
const newMsTitle = ref('')
const newChTitle = ref('')
const newChContent = ref('')
const newChVisibility = ref<'TOTAL' | 'PARCIAL' | 'NULA'>('NULA')
const creating = ref(false)

// ── Edição ───────────────────────────────────────────────────────────────────
const isEditing = ref(false)
const editTitle = ref('')
const editContent = ref('')
const editVisibility = ref<'TOTAL' | 'PARCIAL' | 'NULA'>('NULA')
const saving = ref(false)
const contentEditorRef = ref<HTMLTextAreaElement>()

onMounted(() => { manuscriptsStore.fetchManuscripts() })

function selectManuscript(ms: Manuscript) {
  manuscriptsStore.selectManuscript(ms)
  activeChapter.value = null
  isEditing.value = false
}

function selectChapter(ch: Chapter) {
  if (isEditing.value && activeChapter.value) {
    if (!confirm('Descartar alterações não salvas?')) return
  }
  activeChapter.value = ch
  isEditing.value = false
}

watch(() => manuscriptsStore.chapters, (chs) => {
  if (chs.length && !activeChapter.value) activeChapter.value = chs[0]
})

async function createManuscript() {
  if (!newMsTitle.value.trim()) return
  creating.value = true
  try {
    const ms = await manuscriptsStore.createManuscript(newMsTitle.value.trim())
    if (ms) { manuscriptsStore.selectManuscript(ms); showNewManuscript.value = false; newMsTitle.value = '' }
  } finally { creating.value = false }
}

async function createChapter() {
  if (!newChTitle.value.trim() || !manuscriptsStore.currentManuscript) return
  creating.value = true
  try {
    const ch = await manuscriptsStore.createChapter(manuscriptsStore.currentManuscript.id, {
      title: newChTitle.value.trim(),
      content: newChContent.value,
      visibility: newChVisibility.value,
      order_index: manuscriptsStore.chapters.length,
    } as any)
    if (ch) { activeChapter.value = ch; showNewChapter.value = false; newChTitle.value = ''; newChContent.value = ''; newChVisibility.value = 'NULA' }
  } finally { creating.value = false }
}

// ── Edição de capítulo ───────────────────────────────────────────────────────
function startEdit() {
  if (!activeChapter.value) return
  editTitle.value = activeChapter.value.title
  editContent.value = activeChapter.value.content
  editVisibility.value = activeChapter.value.visibility as any
  isEditing.value = true
  nextTick(() => contentEditorRef.value?.focus())
}

function cancelEdit() {
  isEditing.value = false
}

async function saveEdit() {
  if (!activeChapter.value || !manuscriptsStore.currentManuscript) return
  saving.value = true
  try {
    const updated = await manuscriptsStore.updateChapter(
      manuscriptsStore.currentManuscript.id,
      activeChapter.value.id,
      { title: editTitle.value, content: editContent.value, visibility: editVisibility.value },
    )
    if (updated) activeChapter.value = updated
    isEditing.value = false
  } finally { saving.value = false }
}

/**
 * Renderiza @mentions no texto como links clicáveis.
 */
function renderContent(text: string): string {
  return text.replace(
    /@\[(article|map|pin):([^\]]+)\]/g,
    (_, type, id) => `<a href="/${type === 'article' ? 'codex' : 'maps'}/${id}" class="mention-link">@${type}:${id.substring(0, 8)}…</a>`
  )
}
</script>

<template>
  <div class="manuscripts">
    <!-- ═══ SIDEBAR ═══ -->
    <aside class="ms-sidebar">
      <div class="ms-sidebar__header">
        <h3 class="ms-sidebar__title">Manuscritos</h3>
        <button v-if="isMestre" class="btn-icon-sm" title="Novo manuscrito" @click="showNewManuscript = true">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        </button>
      </div>

      <div class="ms-list">
        <button v-for="ms in manuscriptsStore.manuscripts" :key="ms.id" class="ms-item" :class="{ 'ms-item--active': manuscriptsStore.currentManuscript?.id === ms.id }" @click="selectManuscript(ms)">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          <span>{{ ms.title }}</span>
        </button>
      </div>

      <Transition name="fade">
        <div v-if="manuscriptsStore.currentManuscript" class="ch-section">
          <div class="ch-section__header">
            <span class="ch-section__label">Capítulos</span>
            <button v-if="isMestre" class="btn-icon-sm" title="Novo capítulo" @click="showNewChapter = true">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            </button>
          </div>
          <div v-if="manuscriptsStore.loading" class="ch-loading">Carregando...</div>
          <button v-for="ch in manuscriptsStore.chapters" :key="ch.id" class="ch-item" :class="{ 'ch-item--active': activeChapter?.id === ch.id }" @click="selectChapter(ch)">
            <span class="ch-item__title">{{ ch.title }}</span>
            <VisibilityBadge v-if="isMestre" :visibility="ch.visibility" />
          </button>
        </div>
      </Transition>
    </aside>

    <!-- ═══ ÁREA DE LEITURA / EDIÇÃO ═══ -->
    <main class="ms-reader">
      <div v-if="!manuscriptsStore.currentManuscript" class="reader-empty">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-dim)" stroke-width="1"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
        <p>Selecione um manuscrito para começar.</p>
      </div>

      <div v-else-if="!activeChapter" class="reader-empty"><p>Selecione um capítulo na barra lateral.</p></div>

      <!-- Modo Leitura -->
      <article v-else-if="!isEditing" class="reader-content">
        <header class="reader-header">
          <h1 class="reader-header__title">{{ activeChapter.title }}</h1>
          <div class="reader-header__actions">
            <VisibilityBadge v-if="isMestre" :visibility="activeChapter.visibility" size="md" />
            <button v-if="isMestre" class="btn-icon" title="Editar capítulo" @click="startEdit">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
            </button>
          </div>
        </header>
        <div class="reader-body" v-html="renderContent(activeChapter.content)" />
      </article>

      <!-- Modo Edição -->
      <div v-else class="editor-content">
        <header class="editor-header">
          <input v-model="editTitle" class="editor-title-input" type="text" placeholder="Título do capítulo" />
          <div class="editor-header__actions">
            <select v-model="editVisibility" class="editor-vis-select">
              <option value="NULA">Nula</option><option value="PARCIAL">Parcial</option><option value="TOTAL">Total</option>
            </select>
            <button class="btn btn--ghost btn--sm" @click="cancelEdit">Cancelar</button>
            <button class="btn btn--gold btn--sm" @click="saveEdit" :disabled="saving || !editTitle.trim()">
              {{ saving ? 'Salvando...' : 'Salvar' }}
            </button>
          </div>
        </header>
        <textarea
          ref="contentEditorRef"
          v-model="editContent"
          class="editor-textarea"
          placeholder="Escreva o conteúdo do capítulo...&#10;Use @[article:id] para mencionar artigos."
        />
      </div>
    </main>

    <!-- ═══ MODAL NOVO MANUSCRITO ═══ -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="showNewManuscript" class="modal-overlay" @click.self="showNewManuscript = false">
          <div class="modal" @click.stop>
            <h3 class="modal__title">Novo Manuscrito</h3>
            <div class="form-group"><label>Título</label><input v-model="newMsTitle" type="text" class="form-input" placeholder="Ex: Diário da Campanha" autofocus @keydown.enter="createManuscript" /></div>
            <div class="modal__actions"><button class="btn btn--ghost" @click="showNewManuscript = false">Cancelar</button><button class="btn btn--gold" @click="createManuscript" :disabled="creating || !newMsTitle.trim()">Criar</button></div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- ═══ MODAL NOVO CAPÍTULO ═══ -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="showNewChapter" class="modal-overlay" @click.self="showNewChapter = false">
          <div class="modal modal--wide" @click.stop>
            <h3 class="modal__title">Novo Capítulo</h3>
            <div class="form-row">
              <div class="form-group form-group--flex"><label>Título</label><input v-model="newChTitle" type="text" class="form-input" placeholder="Sessão 01: O Início" autofocus /></div>
              <div class="form-group" style="width:140px;"><label>Visibilidade</label><select v-model="newChVisibility" class="form-input"><option value="NULA">Nula</option><option value="PARCIAL">Parcial</option><option value="TOTAL">Total</option></select></div>
            </div>
            <div class="form-group"><label>Conteúdo</label><textarea v-model="newChContent" class="form-input form-input--tall" placeholder="Escreva o conteúdo..." rows="10" /></div>
            <div class="modal__actions"><button class="btn btn--ghost" @click="showNewChapter = false">Cancelar</button><button class="btn btn--gold" @click="createChapter" :disabled="creating || !newChTitle.trim()">Criar Capítulo</button></div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.manuscripts { display: flex; height: calc(100vh - 56px); margin: calc(-1 * var(--space-6)) calc(-1 * var(--space-8)); }

/* Sidebar */
.ms-sidebar { width: 260px; min-width: 220px; background: var(--color-surface); border-right: 1px solid var(--color-border); display: flex; flex-direction: column; overflow: hidden; flex-shrink: 0; }
.ms-sidebar__header { display: flex; align-items: center; justify-content: space-between; padding: var(--space-4); border-bottom: 1px solid var(--color-border); }
.ms-sidebar__title { font-family: var(--font-display); font-size: 0.95rem; color: var(--color-gold); }
.btn-icon-sm { width: 26px; height: 26px; border-radius: var(--radius-sm); border: 1px solid var(--color-border); background: none; color: var(--color-text-muted); cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all var(--transition-fast); }
.btn-icon-sm:hover { border-color: var(--color-gold-dim); color: var(--color-gold); }
.ms-list { padding: var(--space-2); }
.ms-item { display: flex; align-items: center; gap: var(--space-2); width: 100%; padding: var(--space-2) var(--space-3); border: none; border-radius: var(--radius-sm); background: none; color: var(--color-text-muted); font-family: var(--font-body); font-size: 0.8rem; cursor: pointer; text-align: left; transition: all var(--transition-fast); }
.ms-item:hover { background: var(--color-surface-2); color: var(--color-text); }
.ms-item--active { background: var(--color-gold-glow); color: var(--color-gold); }

.ch-section { border-top: 1px solid var(--color-border); flex: 1; overflow-y: auto; }
.ch-section__header { display: flex; align-items: center; justify-content: space-between; padding: var(--space-3) var(--space-4); font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--color-text-dim); }
.ch-section__label { font-weight: 600; }
.ch-loading { padding: var(--space-4); text-align: center; font-size: 0.8rem; color: var(--color-text-dim); }
.ch-item { display: flex; align-items: center; justify-content: space-between; width: 100%; padding: var(--space-2) var(--space-4); border: none; background: none; color: var(--color-text-muted); font-family: var(--font-body); font-size: 0.8rem; cursor: pointer; text-align: left; transition: all var(--transition-fast); gap: var(--space-2); }
.ch-item:hover { background: var(--color-surface-2); }
.ch-item--active { background: var(--color-surface-2); color: var(--color-text); border-left: 3px solid var(--color-gold); }
.ch-item__title { flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* Reader */
.ms-reader { flex: 1; overflow-y: auto; display: flex; justify-content: center; padding: var(--space-8) var(--space-6); }
.reader-empty { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: var(--space-4); color: var(--color-text-dim); font-size: 0.9rem; flex: 1; }
.reader-content { max-width: 720px; width: 100%; }
.reader-header { margin-bottom: var(--space-6); display: flex; align-items: center; gap: var(--space-4); }
.reader-header__title { font-family: var(--font-display); font-size: 1.8rem; font-weight: 600; color: var(--color-gold); border-bottom: 2px solid var(--color-gold-dim); padding-bottom: var(--space-3); flex: 1; }
.reader-header__actions { display: flex; align-items: center; gap: var(--space-2); }
.btn-icon { display: flex; align-items: center; justify-content: center; width: 32px; height: 32px; border-radius: var(--radius-sm); border: 1px solid var(--color-border); background: none; color: var(--color-text-muted); cursor: pointer; transition: all var(--transition-fast); }
.btn-icon:hover { border-color: var(--color-gold-dim); color: var(--color-gold); }
.reader-body { font-size: 0.95rem; line-height: 1.9; color: var(--color-text); white-space: pre-wrap; }
.reader-body :deep(.mention-link) { color: var(--color-gold); text-decoration: none; border-bottom: 1px dashed var(--color-gold-dim); cursor: pointer; }
.reader-body :deep(.mention-link:hover) { color: var(--color-gold-light); }

/* Editor */
.editor-content { max-width: 720px; width: 100%; display: flex; flex-direction: column; gap: var(--space-4); }
.editor-header { display: flex; align-items: center; gap: var(--space-3); flex-wrap: wrap; }
.editor-title-input { flex: 1; background: var(--color-bg); border: 1px solid var(--color-border); border-radius: var(--radius-sm); color: var(--color-gold); font-family: var(--font-display); font-size: 1.3rem; font-weight: 600; padding: var(--space-3) var(--space-4); min-width: 200px; }
.editor-title-input:focus { outline: none; border-color: var(--color-gold-dim); }
.editor-header__actions { display: flex; align-items: center; gap: var(--space-2); }
.editor-vis-select { background: var(--color-bg); border: 1px solid var(--color-border); border-radius: var(--radius-sm); color: var(--color-text); font-family: var(--font-body); font-size: 0.8rem; padding: var(--space-2) var(--space-3); }
.editor-vis-select:focus { outline: none; border-color: var(--color-gold-dim); }
.editor-textarea { flex: 1; min-height: 400px; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-md); color: var(--color-text); font-family: var(--font-body); font-size: 0.95rem; line-height: 1.8; padding: var(--space-5); resize: none; }
.editor-textarea:focus { outline: none; border-color: var(--color-gold-dim); }
.editor-textarea::placeholder { color: var(--color-text-dim); }

/* Buttons */
.btn { padding: var(--space-2) var(--space-5); border-radius: var(--radius-sm); border: none; font-family: var(--font-body); font-size: 0.875rem; font-weight: 500; cursor: pointer; transition: all var(--transition-fast); }
.btn--sm { padding: var(--space-2) var(--space-3); font-size: 0.8rem; }
.btn--ghost { background: none; border: 1px solid var(--color-border); color: var(--color-text-muted); }
.btn--ghost:hover { border-color: var(--color-text-muted); color: var(--color-text); }
.btn--gold { background: var(--color-gold); color: #0d0f14; font-weight: 600; }
.btn--gold:hover { background: var(--color-gold-light); box-shadow: var(--shadow-gold); }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* Modal */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.7); z-index: 300; display: flex; align-items: center; justify-content: center; backdrop-filter: blur(4px); }
.modal { background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); padding: var(--space-8); width: 100%; max-width: 440px; box-shadow: var(--shadow-lg); }
.modal--wide { max-width: 600px; }
.modal__title { font-size: 1.1rem; font-weight: 600; color: var(--color-gold); margin-bottom: var(--space-6); }
.form-group { display: flex; flex-direction: column; gap: var(--space-2); margin-bottom: var(--space-4); }
.form-group--flex { flex: 1; }
.form-group label { font-size: 0.75rem; color: var(--color-text-muted); text-transform: uppercase; letter-spacing: 0.06em; }
.form-input { background: var(--color-bg); border: 1px solid var(--color-border); border-radius: var(--radius-sm); color: var(--color-text); font-family: var(--font-body); font-size: 0.85rem; padding: var(--space-2) var(--space-3); resize: none; }
.form-input:focus { outline: none; border-color: var(--color-gold-dim); }
.form-input--tall { min-height: 200px; line-height: 1.7; }
.form-row { display: flex; gap: var(--space-4); }
.modal__actions { display: flex; gap: var(--space-3); justify-content: flex-end; margin-top: var(--space-6); }
</style>
