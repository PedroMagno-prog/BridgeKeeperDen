<script setup lang="ts">
import { ref, watch, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { useArticlesStore } from '@/stores/articles'
import { useAutoSave } from '@/composables/useAutoSave'
import SaveStatusBadge from '@/components/ui/SaveStatusBadge.vue'
import WikilinkAutocomplete from './WikilinkAutocomplete.vue'
import WikilinkPreviewModal from '@/components/ui/WikilinkPreviewModal.vue'

const props = withDefaults(
  defineProps<{
    articleId: string
    initialContent?: string
    readonly?: boolean
  }>(),
  { initialContent: '', readonly: false }
)

const router = useRouter()
const articlesStore = useArticlesStore()
const editorTextarea = ref<HTMLTextAreaElement | null>(null)
const content = ref(props.initialContent)
const editorMode = ref<'edit' | 'preview' | 'split'>('edit')
const isMaximized = ref(false)

// Estado para Quick Preview Modal de Wikilinks
const activePreviewId = ref<string | null>(null)
const activePreviewTitle = ref<string>('')
const showPreviewModal = ref(false)
// Configuração do Marked com abertura de links externos em nova guia (_blank)
const renderer = new marked.Renderer()
renderer.link = ({ href, title, text }: { href: string; title?: string | null; text: string }) => {
  const titleAttr = title ? ` title="${title}"` : ''
  return `<a href="${href}" target="_blank" rel="noopener noreferrer"${titleAttr} class="external-link">${text} ↗</a>`
}
marked.use({ renderer })
marked.setOptions({ gfm: true, breaks: true })

// Hook do DOMPurify para garantir target="_blank" e rel="noopener noreferrer"
DOMPurify.addHook('afterSanitizeAttributes', function (node) {
  if (node.tagName === 'A' && node.hasAttribute('href')) {
    node.setAttribute('target', '_blank')
    node.setAttribute('rel', 'noopener noreferrer')
  }
})

const renderedMarkdown = computed(() => {
  if (!content.value.trim()) return ''
  const preprocessed = content.value
    .replace(/\[\[([^\]|]+)\|([^\]]+)\]\]/g, '<button type="button" class="md-wikilink" data-target="$1" title="Clique para pré-visualizar | Ctrl+Clique para abrir">&#128279; $2</button>')
    .replace(/\[\[([^\]]+)\]\]/g, '<button type="button" class="md-wikilink" data-target="$1" title="Clique para pré-visualizar | Ctrl+Clique para abrir">&#128279; $1</button>')
  const raw = marked.parse(preprocessed) as string
  return DOMPurify.sanitize(raw, {
    ALLOWED_TAGS: ['h1','h2','h3','h4','h5','h6','p','br','strong','em','del','code','pre',
      'blockquote','ul','ol','li','a','img','table','thead','tbody','tr','th','td','hr','span','div','button'],
    ALLOWED_ATTR: ['href','src','alt','class','title','data-target','type','target','rel'],
  })
})

const { status, lastSavedAt, triggerChange, flushSave, resetStatus } = useAutoSave(
  async (newContent: string) => {
    if (!props.articleId) return
    await articlesStore.patchArticleContent(props.articleId, newContent)
  }, 800
)

watch(() => props.initialContent, (newVal) => {
  content.value = newVal || ''
  resetStatus()
})

function onContentInput() {
  triggerChange(content.value)
  checkWikilinkTrigger()
}

const showAutocomplete = ref(false)
const autocompleteQuery = ref('')
const autocompletePos = ref({ top: 0, left: 0 })
let matchStartIndex = -1

function checkWikilinkTrigger() {
  if (!editorTextarea.value) return
  const ta = editorTextarea.value
  const textBeforeCursor = content.value.slice(0, ta.selectionStart)
  const lastOpen = textBeforeCursor.lastIndexOf('[[')
  const lastClose = textBeforeCursor.lastIndexOf(']]')
  if (lastOpen !== -1 && lastOpen > lastClose) {
    const query = textBeforeCursor.slice(lastOpen + 2)
    if (!query.includes('\n')) {
      matchStartIndex = lastOpen
      autocompleteQuery.value = query
      const rect = ta.getBoundingClientRect()
      const lines = textBeforeCursor.split('\n')
      const lineIndex = lines.length - 1
      const lineCharIndex = (lines[lineIndex] ?? '').length
      autocompletePos.value = {
        top: Math.max(100, rect.top + Math.min(lineIndex * 22 + 30, rect.height - 40)),
        left: Math.max(20, rect.left + Math.min(lineCharIndex * 7.5 + 20, rect.width - 280))
      }
      showAutocomplete.value = true
      return
    }
  }
  showAutocomplete.value = false
}

function handleSelectWikilink(articleTitle: string) {
  if (!editorTextarea.value || matchStartIndex === -1) return
  const ta = editorTextarea.value
  const cursorPos = ta.selectionStart
  const inserted = `[[${articleTitle}]]`
  content.value = content.value.slice(0, matchStartIndex) + inserted + content.value.slice(cursorPos)
  showAutocomplete.value = false
  nextTick(() => {
    ta.focus()
    const pos = matchStartIndex + inserted.length
    ta.setSelectionRange(pos, pos)
    triggerChange(content.value)
  })
}

// ── Interação com Wikilinks e Links na Pré-visualização ───────────────────────
async function handlePreviewClick(e: MouseEvent) {
  const anchor = (e.target as HTMLElement).closest('a') as HTMLAnchorElement | null
  if (anchor && anchor.href) {
    anchor.target = '_blank'
    anchor.rel = 'noopener noreferrer'
    return
  }

  const target = (e.target as HTMLElement).closest('.md-wikilink') as HTMLElement | null
  if (!target) return
  e.preventDefault()
  e.stopPropagation()

  const targetTitle = target.getAttribute('data-target')
  if (!targetTitle) return

  const res = await articlesStore.resolveArticle(targetTitle)

  if (e.ctrlKey || e.metaKey) {
    if (status.value === 'modified' || status.value === 'saving') {
      await flushSave()
    }
    if (res?.exists && res.article_id) {
      router.push(`/codex/${res.article_id}`)
      return
    }
  }

  if (res?.exists && res.article_id) {
    activePreviewId.value = res.article_id
    activePreviewTitle.value = res.title
    showPreviewModal.value = true
  } else {
    if (confirm(`O artigo "${targetTitle}" não existe. Deseja criar um novo artigo no Codex com este título?`)) {
      if (status.value === 'modified' || status.value === 'saving') {
        await flushSave()
      }
      const newArt = await articlesStore.createArticle({
        title: targetTitle,
        content: `Artigo criado a partir do Wikilink [[${targetTitle}]].`,
      } as any)
      if (newArt) {
        router.push(`/codex/${newArt.id}`)
      }
    }
  }
}

// ── Interação com Wikilinks no Textarea (Ctrl+Click) ──────────────────────────
async function handleTextareaClick(e: MouseEvent) {
  checkWikilinkTrigger()
  if (!e.ctrlKey && !e.metaKey && !e.altKey) return
  if (!editorTextarea.value) return

  const ta = editorTextarea.value
  const pos = ta.selectionStart
  const text = content.value

  const lastOpen = text.lastIndexOf('[[', pos)
  const nextClose = text.indexOf(']]', pos)

  if (lastOpen !== -1 && nextClose !== -1 && lastOpen < nextClose) {
    const snippet = text.slice(lastOpen + 2, nextClose)
    if (!snippet.includes('\n')) {
      const targetTitle = (snippet.split('|')[0] ?? '').trim()
      if (targetTitle) {
        e.preventDefault()
        const res = await articlesStore.resolveArticle(targetTitle)
        if (res?.exists && res.article_id) {
          activePreviewId.value = res.article_id
          activePreviewTitle.value = res.title
          showPreviewModal.value = true
        } else {
          if (confirm(`O artigo "${targetTitle}" não existe. Deseja criar um novo artigo no Codex com este título?`)) {
            if (status.value === 'modified' || status.value === 'saving') {
              await flushSave()
            }
            const newArt = await articlesStore.createArticle({
              title: targetTitle,
              content: `Artigo criado a partir do Wikilink [[${targetTitle}]].`,
            } as any)
            if (newArt) {
              router.push(`/codex/${newArt.id}`)
            }
          }
        }
      }
    }
  }
}

function toggleMaximize() {
  isMaximized.value = !isMaximized.value
}

function onGlobalKeyDown(e: KeyboardEvent) {
  if (e.key === 'Escape' && isMaximized.value) {
    isMaximized.value = false
  }
}

onMounted(() => {
  window.addEventListener('keydown', onGlobalKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onGlobalKeyDown)
})
</script>

<template>
  <div class="article-editor" :class="{ 'article-editor--maximized': isMaximized }">
    <div class="editor-header">
      <div class="editor-header__left">
        <span class="editor-label">Editor Live Preview</span>
        <SaveStatusBadge :status="status" :last-saved-at="lastSavedAt" @retry="flushSave" />
        <span class="editor-hint hidden lg:inline-flex items-center gap-1 text-xs text-stone-500">
          💡 Clique no [[link]] para pré-visualizar ou Ctrl+Clique para abrir
        </span>
      </div>

      <div class="editor-header__right flex items-center gap-2">
        <div class="mode-selector">
          <button class="mode-btn" :class="{ 'mode-btn--active': editorMode === 'edit' }" @click="editorMode = 'edit'">Editar</button>
          <button class="mode-btn" :class="{ 'mode-btn--active': editorMode === 'preview' }" @click="editorMode = 'preview'">Leitura</button>
          <button class="mode-btn" :class="{ 'mode-btn--active': editorMode === 'split' }" @click="editorMode = 'split'">Divisão</button>
        </div>

        <button
          class="mode-btn btn-maximize flex items-center gap-1"
          :class="{ 'mode-btn--active': isMaximized }"
          :title="isMaximized ? 'Restaurar Tamanho (Esc)' : 'Maximizar Editor / Modo Foco'"
          @click="toggleMaximize"
        >
          <svg v-if="!isMaximized" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/><line x1="21" y1="3" x2="14" y2="10"/><line x1="3" y1="21" x2="10" y2="14"/>
          </svg>
          <svg v-else width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="4 14 10 14 10 20"/><polyline points="20 10 14 10 14 4"/><line x1="14" y1="10" x2="21" y2="3"/><line x1="3" y1="21" x2="10" y2="14"/>
          </svg>
          <span>{{ isMaximized ? 'Restaurar' : 'Maximizar' }}</span>
        </button>
      </div>
    </div>

    <div class="editor-workspace">
      <div v-if="editorMode === 'edit' || editorMode === 'split'" class="editor-pane" :class="{ 'editor-pane--half': editorMode === 'split' }">
        <textarea
          ref="editorTextarea"
          v-model="content"
          :readonly="readonly"
          placeholder="Escreva em Markdown... Digite [[ para Wikilinks. (Dica: Ctrl+Clique em um [[Wikilink]] para inspecionar)"
          class="editor-textarea"
          @input="onContentInput"
          @keyup="checkWikilinkTrigger"
          @click="handleTextareaClick"
        />
      </div>

      <div v-if="editorMode === 'split'" class="editor-divider" />

      <div
        v-if="editorMode === 'preview' || editorMode === 'split'"
        class="preview-pane"
        :class="{ 'preview-pane--half': editorMode === 'split' }"
        @click="handlePreviewClick"
      >
        <div v-if="content.trim()" class="markdown-body" v-html="renderedMarkdown" />
        <div v-else class="preview-empty">O conteúdo pré-visualizado aparecerá aqui.</div>
      </div>
    </div>

    <WikilinkAutocomplete
      :show="showAutocomplete"
      :search-query="autocompleteQuery"
      :position="autocompletePos"
      @select="handleSelectWikilink"
      @close="showAutocomplete = false"
    />

    <!-- Modal de Pré-visualização Rápida de Wikilink -->
    <WikilinkPreviewModal
      :show="showPreviewModal"
      :article-id="activePreviewId"
      :title="activePreviewTitle"
      @close="showPreviewModal = false"
    />
  </div>
</template>

<style scoped>
.article-editor {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  background: #0c0e15;
  border: 1px solid #1e2335;
  border-radius: 12px;
  overflow: hidden;
  color: #e8e4d8;
  transition: all 0.2s ease;
}

.article-editor--maximized {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  bottom: 0 !important;
  width: 100vw !important;
  height: 100vh !important;
  z-index: 1000 !important;
  border-radius: 0 !important;
  border: none !important;
  box-shadow: 0 0 60px rgba(0, 0, 0, 0.95);
  background: #080a10;
}

.editor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  background: #080a10;
  border-bottom: 1px solid #1a1d28;
  flex-shrink: 0;
  gap: 12px;
}

.editor-header__left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex-wrap: wrap;
}

.editor-label {
  font-size: 0.72rem;
  font-weight: 600;
  color: #c9a84c;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  white-space: nowrap;
}

.editor-hint {
  font-size: 0.72rem;
  color: #64748b;
  margin-left: 8px;
}

.mode-selector {
  display: flex;
  align-items: center;
  gap: 2px;
  background: #101420;
  border: 1px solid #1a1d28;
  border-radius: 8px;
  padding: 3px;
  flex-shrink: 0;
}

.mode-btn {
  padding: 4px 10px;
  border-radius: 6px;
  border: 1px solid transparent;
  background: transparent;
  color: #707890;
  font-size: 0.72rem;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.mode-btn:hover {
  color: #cbd5e1;
  background: #161924;
}

.mode-btn--active {
  background: rgba(201, 168, 76, 0.15);
  color: #c9a84c;
  border-color: rgba(201, 168, 76, 0.3);
  font-weight: 600;
}

.btn-maximize {
  background: #101420;
  border: 1px solid #1a1d28;
  color: #8892b0;
}

.btn-maximize:hover {
  border-color: rgba(201, 168, 76, 0.4);
  color: #c9a84c;
  background: rgba(201, 168, 76, 0.1);
}

.editor-workspace {
  display: flex;
  flex: 1 1 0%;
  min-height: 0;
  overflow: hidden;
}

.editor-pane {
  display: flex;
  flex: 1 1 0%;
  min-height: 0;
  min-width: 0;
  overflow: hidden;
  background: #0c0e15;
}

.editor-pane--half {
  flex: 0 0 50%;
  max-width: 50%;
}

.editor-textarea {
  flex: 1 1 0%;
  width: 100%;
  height: 100%;
  min-height: 0;
  resize: none;
  background: #0c0e15;
  color: #d4d8e4;
  border: none;
  outline: none;
  font-family: 'Fira Code', 'JetBrains Mono', monospace;
  font-size: 0.9rem;
  line-height: 1.75;
  padding: 20px 24px;
  caret-color: #c9a84c;
  scrollbar-width: thin;
  scrollbar-color: #2e3350 transparent;
}

.editor-textarea::placeholder {
  color: #333a50;
}

.editor-textarea::-webkit-scrollbar {
  width: 6px;
}

.editor-textarea::-webkit-scrollbar-thumb {
  background: #2e3350;
  border-radius: 4px;
}

.editor-divider {
  width: 1px;
  background: #1a1d28;
  flex-shrink: 0;
}

.preview-pane {
  flex: 1 1 0%;
  min-height: 0;
  min-width: 0;
  overflow-y: auto;
  background: #090c12;
  padding: 24px 28px;
  scrollbar-width: thin;
  scrollbar-color: #2e3350 transparent;
}

.preview-pane--half {
  flex: 0 0 50%;
  max-width: 50%;
}

.preview-pane::-webkit-scrollbar {
  width: 6px;
}

.preview-pane::-webkit-scrollbar-thumb {
  background: #2e3350;
  border-radius: 4px;
}

.preview-empty {
  color: #3a4258;
  font-style: italic;
  font-size: 0.85rem;
  text-align: center;
  padding: 40px 20px;
}

.markdown-body {
  color: #c8ccd8;
  font-size: 0.92rem;
  line-height: 1.8;
  word-break: break-word;
}

.markdown-body :deep(h1) {
  font-family: 'Cinzel', serif;
  font-size: 1.6rem;
  font-weight: 700;
  color: #c9a84c;
  border-bottom: 1px solid #1e2335;
  padding-bottom: 8px;
  margin: 0 0 16px;
}

.markdown-body :deep(h2) {
  font-family: 'Cinzel', serif;
  font-size: 1.25rem;
  font-weight: 600;
  color: #e8c86a;
  margin: 24px 0 12px;
}

.markdown-body :deep(h3) {
  font-family: 'Inter', sans-serif;
  font-size: 1.05rem;
  font-weight: 600;
  color: #c0c4d0;
  margin: 18px 0 8px;
}

.markdown-body :deep(p) {
  margin: 0 0 12px;
}

.markdown-body :deep(strong) {
  color: #e8e4d8;
  font-weight: 700;
}

.markdown-body :deep(em) {
  color: #aab0c0;
  font-style: italic;
}

.markdown-body :deep(code) {
  background: #141720;
  color: #c9a84c;
  font-family: 'Fira Code', monospace;
  font-size: 0.82rem;
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid #1e2335;
}

.markdown-body :deep(pre) {
  background: #070910;
  border: 1px solid #1a1d28;
  border-radius: 8px;
  padding: 16px;
  overflow-x: auto;
  margin: 12px 0;
}

.markdown-body :deep(pre code) {
  background: none;
  border: none;
  padding: 0;
  color: #a0a8b8;
}

.markdown-body :deep(blockquote) {
  border-left: 3px solid #c9a84c;
  padding: 8px 16px;
  background: rgba(201, 168, 76, 0.06);
  border-radius: 0 6px 6px 0;
  margin: 12px 0;
  color: #8090a0;
  font-style: italic;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 24px;
  margin: 8px 0 12px;
}

.markdown-body :deep(li) {
  margin-bottom: 4px;
}

.markdown-body :deep(ul > li)::marker {
  color: #c9a84c;
}

.markdown-body :deep(ol > li)::marker {
  color: #c9a84c;
}

.markdown-body :deep(hr) {
  border: none;
  border-top: 1px solid #1e2335;
  margin: 20px 0;
}

.markdown-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
  font-size: 0.85rem;
}

.markdown-body :deep(th) {
  background: #131720;
  color: #c9a84c;
  font-weight: 600;
  padding: 8px 12px;
  border: 1px solid #1e2335;
  text-align: left;
}

.markdown-body :deep(td) {
  padding: 7px 12px;
  border: 1px solid #181c26;
  color: #a8b0c0;
}

.markdown-body :deep(tr:nth-child(even) td) {
  background: rgba(255, 255, 255, 0.02);
}

.markdown-body :deep(a) {
  color: #5b9bd5;
  text-decoration-color: transparent;
  transition: text-decoration-color 0.15s;
}

.markdown-body :deep(a:hover) {
  text-decoration-color: #5b9bd5;
}

.markdown-body :deep(img) {
  max-width: 100%;
  border-radius: 8px;
  margin: 8px 0;
}

/* Wikilinks Interativos */
.markdown-body :deep(.md-wikilink) {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: rgba(16, 185, 129, 0.12);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.35);
  padding: 1px 7px;
  border-radius: 4px;
  font-size: 0.84rem;
  font-weight: 500;
  font-family: inherit;
  cursor: pointer;
  vertical-align: baseline;
  transition: all 0.15s ease;
  user-select: text;
}

.markdown-body :deep(.md-wikilink:hover) {
  background: rgba(16, 185, 129, 0.25);
  border-color: #10b981;
  color: #34d399;
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.2);
  transform: translateY(-1px);
}

.markdown-body :deep(.md-wikilink:active) {
  background: rgba(16, 185, 129, 0.4);
  transform: translateY(0);
}
</style>

