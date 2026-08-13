<script setup lang="ts">
import { ref, watch, computed, nextTick } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { useArticlesStore } from '@/stores/articles'
import { useAutoSave } from '@/composables/useAutoSave'
import SaveStatusBadge from '@/components/ui/SaveStatusBadge.vue'
import WikilinkAutocomplete from './WikilinkAutocomplete.vue'

const props = withDefaults(
  defineProps<{
    articleId: string
    initialContent?: string
    readonly?: boolean
  }>(),
  { initialContent: '', readonly: false }
)

const articlesStore = useArticlesStore()
const editorTextarea = ref<HTMLTextAreaElement | null>(null)
const content = ref(props.initialContent)
const editorMode = ref<'edit' | 'preview' | 'split'>('edit')

marked.setOptions({ gfm: true, breaks: true })

const renderedMarkdown = computed(() => {
  if (!content.value.trim()) return ''
  const preprocessed = content.value
    .replace(/\[\[([^\]|]+)\|([^\]]+)\]\]/g, '<span class="md-wikilink">&#128279; $2</span>')
    .replace(/\[\[([^\]]+)\]\]/g, '<span class="md-wikilink">&#128279; $1</span>')
  const raw = marked.parse(preprocessed) as string
  return DOMPurify.sanitize(raw, {
    ALLOWED_TAGS: ['h1','h2','h3','h4','h5','h6','p','br','strong','em','del','code','pre',
      'blockquote','ul','ol','li','a','img','table','thead','tbody','tr','th','td','hr','span','div'],
    ALLOWED_ATTR: ['href','src','alt','class','title'],
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
</script>

<template>
  <div class="article-editor">
    <div class="editor-header">
      <div class="editor-header__left">
        <span class="editor-label">Editor Live Preview</span>
        <SaveStatusBadge :status="status" :last-saved-at="lastSavedAt" @retry="flushSave" />
      </div>
      <div class="mode-selector">
        <button class="mode-btn" :class="{ 'mode-btn--active': editorMode === 'edit' }" @click="editorMode = 'edit'">Editar</button>
        <button class="mode-btn" :class="{ 'mode-btn--active': editorMode === 'preview' }" @click="editorMode = 'preview'">Leitura</button>
        <button class="mode-btn" :class="{ 'mode-btn--active': editorMode === 'split' }" @click="editorMode = 'split'">Divisao</button>
      </div>
    </div>
    <div class="editor-workspace">
      <div v-if="editorMode === 'edit' || editorMode === 'split'" class="editor-pane" :class="{ 'editor-pane--half': editorMode === 'split' }">
        <textarea ref="editorTextarea" v-model="content" :readonly="readonly" placeholder="Escreva em Markdown... Digite [[ para Wikilinks." class="editor-textarea" @input="onContentInput" @keyup="checkWikilinkTrigger" @click="checkWikilinkTrigger" />
      </div>
      <div v-if="editorMode === 'split'" class="editor-divider" />
      <div v-if="editorMode === 'preview' || editorMode === 'split'" class="preview-pane" :class="{ 'preview-pane--half': editorMode === 'split' }">
        <div v-if="content.trim()" class="markdown-body" v-html="renderedMarkdown" />
        <div v-else class="preview-empty">O conteudo pre-visualizado aparecera aqui.</div>
      </div>
    </div>
    <WikilinkAutocomplete :show="showAutocomplete" :search-query="autocompleteQuery" :position="autocompletePos" @select="handleSelectWikilink" @close="showAutocomplete = false" />
  </div>
</template>

<style scoped>
.article-editor { display:flex; flex-direction:column; height:100%; background:#0c0e15; border:1px solid #1e2335; border-radius:12px; overflow:hidden; color:#e8e4d8; }
.editor-header { display:flex; align-items:center; justify-content:space-between; padding:8px 14px; background:#080a10; border-bottom:1px solid #1a1d28; flex-shrink:0; gap:12px; }
.editor-header__left { display:flex; align-items:center; gap:10px; min-width:0; }
.editor-label { font-size:0.72rem; font-weight:600; color:#c9a84c; text-transform:uppercase; letter-spacing:0.06em; white-space:nowrap; }
.mode-selector { display:flex; align-items:center; gap:2px; background:#101420; border:1px solid #1a1d28; border-radius:8px; padding:3px; flex-shrink:0; }
.mode-btn { padding:4px 10px; border-radius:6px; border:none; background:transparent; color:#4a5068; font-size:0.72rem; font-family:inherit; cursor:pointer; transition:all 0.15s ease; white-space:nowrap; }
.mode-btn:hover { color:#9099a8; background:#161924; }
.mode-btn--active { background:rgba(201,168,76,0.15); color:#c9a84c; font-weight:600; }
.editor-workspace { display:flex; flex:1; overflow:hidden; }
.editor-pane { display:flex; flex:1; overflow:hidden; background:#0c0e15; }
.editor-pane--half { flex:0 0 50%; max-width:50%; }
.editor-textarea { flex:1; width:100%; height:100%; resize:none; background:#0c0e15; color:#d4d8e4; border:none; outline:none; font-family:'Fira Code','JetBrains Mono',monospace; font-size:0.88rem; line-height:1.75; padding:20px 24px; caret-color:#c9a84c; scrollbar-width:thin; scrollbar-color:#2e3350 transparent; }
.editor-textarea::placeholder { color:#2e3350; }
.editor-textarea::-webkit-scrollbar { width:5px; }
.editor-textarea::-webkit-scrollbar-thumb { background:#2e3350; border-radius:4px; }
.editor-divider { width:1px; background:#1a1d28; flex-shrink:0; }
.preview-pane { flex:1; overflow-y:auto; background:#090c12; padding:24px 28px; scrollbar-width:thin; scrollbar-color:#2e3350 transparent; }
.preview-pane--half { flex:0 0 50%; max-width:50%; }
.preview-pane::-webkit-scrollbar { width:5px; }
.preview-pane::-webkit-scrollbar-thumb { background:#2e3350; border-radius:4px; }
.preview-empty { color:#2e3350; font-style:italic; font-size:0.85rem; text-align:center; padding:40px 20px; }
.markdown-body { color:#c8ccd8; font-size:0.9rem; line-height:1.8; word-break:break-word; }
.markdown-body :deep(h1) { font-family:'Cinzel',serif; font-size:1.6rem; font-weight:700; color:#c9a84c; border-bottom:1px solid #1e2335; padding-bottom:8px; margin:0 0 16px; }
.markdown-body :deep(h2) { font-family:'Cinzel',serif; font-size:1.25rem; font-weight:600; color:#e8c86a; margin:24px 0 12px; }
.markdown-body :deep(h3) { font-family:'Inter',sans-serif; font-size:1.05rem; font-weight:600; color:#c0c4d0; margin:18px 0 8px; }
.markdown-body :deep(p) { margin:0 0 12px; }
.markdown-body :deep(strong) { color:#e8e4d8; font-weight:700; }
.markdown-body :deep(em) { color:#aab0c0; font-style:italic; }
.markdown-body :deep(code) { background:#141720; color:#c9a84c; font-family:'Fira Code',monospace; font-size:0.82rem; padding:2px 6px; border-radius:4px; border:1px solid #1e2335; }
.markdown-body :deep(pre) { background:#070910; border:1px solid #1a1d28; border-radius:8px; padding:16px; overflow-x:auto; margin:12px 0; }
.markdown-body :deep(pre code) { background:none; border:none; padding:0; color:#a0a8b8; }
.markdown-body :deep(blockquote) { border-left:3px solid #c9a84c; padding:8px 16px; background:rgba(201,168,76,0.06); border-radius:0 6px 6px 0; margin:12px 0; color:#8090a0; font-style:italic; }
.markdown-body :deep(ul),.markdown-body :deep(ol) { padding-left:24px; margin:8px 0 12px; }
.markdown-body :deep(li) { margin-bottom:4px; }
.markdown-body :deep(ul > li)::marker { color:#c9a84c; }
.markdown-body :deep(ol > li)::marker { color:#c9a84c; }
.markdown-body :deep(hr) { border:none; border-top:1px solid #1e2335; margin:20px 0; }
.markdown-body :deep(table) { width:100%; border-collapse:collapse; margin:12px 0; font-size:0.85rem; }
.markdown-body :deep(th) { background:#131720; color:#c9a84c; font-weight:600; padding:8px 12px; border:1px solid #1e2335; text-align:left; }
.markdown-body :deep(td) { padding:7px 12px; border:1px solid #181c26; color:#a8b0c0; }
.markdown-body :deep(tr:nth-child(even) td) { background:rgba(255,255,255,0.02); }
.markdown-body :deep(a) { color:#5b9bd5; text-decoration-color:transparent; transition:text-decoration-color 0.15s; }
.markdown-body :deep(a:hover) { text-decoration-color:#5b9bd5; }
.markdown-body :deep(img) { max-width:100%; border-radius:8px; margin:8px 0; }
.markdown-body :deep(.md-wikilink) { display:inline-flex; align-items:center; gap:3px; background:rgba(16,185,129,0.1); color:#10b981; border:1px solid rgba(16,185,129,0.3); padding:1px 7px; border-radius:4px; font-size:0.84rem; font-weight:500; }
</style>
