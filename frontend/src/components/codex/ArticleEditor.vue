<script setup lang="ts">
import { ref, watch, onMounted, computed, nextTick } from 'vue'
import { useArticlesStore } from '@/stores/articles'
import { useAutoSave } from '@/composables/useAutoSave'
import SaveStatusBadge from '@/components/ui/SaveStatusBadge.vue'
import WikilinkAutocomplete from './WikilinkAutocomplete.vue'
import WikilinkText from '@/components/ui/WikilinkText.vue'

const props = withDefaults(
  defineProps<{
    articleId: string
    initialContent?: string
    readonly?: boolean
  }>(),
  {
    initialContent: '',
    readonly: false,
  }
)

const articlesStore = useArticlesStore()
const editorTextarea = ref<HTMLTextAreaElement | null>(null)
const content = ref(props.initialContent)
const editorMode = ref<'edit' | 'preview' | 'split'>('edit')

// ── Autosave Integration ─────────────────────────────────────────────────────
const { status, lastSavedAt, triggerChange, flushSave, resetStatus } = useAutoSave(
  async (newContent: string) => {
    if (!props.articleId) return
    await articlesStore.patchArticleContent(props.articleId, newContent)
  },
  800
)

watch(
  () => props.initialContent,
  (newVal) => {
    content.value = newVal || ''
    resetStatus()
  }
)

function onContentInput() {
  triggerChange(content.value)
  checkWikilinkTrigger()
}

// ── Wikilink Autocomplete Logic ──────────────────────────────────────────────
const showAutocomplete = ref(false)
const autocompleteQuery = ref('')
const autocompletePos = ref({ top: 0, left: 0 })
let matchStartIndex = -1

function checkWikilinkTrigger() {
  if (!editorTextarea.value) return
  const ta = editorTextarea.value
  const cursorPos = ta.selectionStart
  const textBeforeCursor = content.value.slice(0, cursorPos)

  // Buscar última ocorrência de [[ antes do cursor sem fechar ]]
  const lastOpenBracket = textBeforeCursor.lastIndexOf('[[')
  const lastCloseBracket = textBeforeCursor.lastIndexOf(']]')

  if (lastOpenBracket !== -1 && lastOpenBracket > lastCloseBracket) {
    const query = textBeforeCursor.slice(lastOpenBracket + 2)
    // Garantir que a busca não tenha quebras de linha
    if (!query.includes('\n')) {
      matchStartIndex = lastOpenBracket
      autocompleteQuery.value = query
      calculatePopoverPosition(ta)
      showAutocomplete.value = true
      return
    }
  }

  showAutocomplete.value = false
}

function calculatePopoverPosition(ta: HTMLTextAreaElement) {
  const rect = ta.getBoundingClientRect()
  // Aproximação da posição do popover baseado nas linhas
  const textUpToCursor = content.value.slice(0, ta.selectionStart)
  const lines = textUpToCursor.split('\n')
  const lineIndex = lines.length - 1
  const currentLine = lines[lineIndex] ?? ''
  const lineCharIndex = currentLine.length

  const lineHeight = 22
  const charWidth = 7.5

  const top = rect.top + Math.min(lineIndex * lineHeight + 30, rect.height - 40)
  const left = rect.left + Math.min(lineCharIndex * charWidth + 20, rect.width - 280)

  autocompletePos.value = {
    top: Math.max(100, top),
    left: Math.max(20, left),
  }
}

function handleSelectWikilink(articleTitle: string) {
  if (!editorTextarea.value || matchStartIndex === -1) return
  const ta = editorTextarea.value
  const cursorPos = ta.selectionStart

  const before = content.value.slice(0, matchStartIndex)
  const after = content.value.slice(cursorPos)

  const inserted = `[[${articleTitle}]]`
  content.value = before + inserted + after
  showAutocomplete.value = false

  nextTick(() => {
    ta.focus()
    const newCursorPos = matchStartIndex + inserted.length
    ta.setSelectionRange(newCursorPos, newCursorPos)
    triggerChange(content.value)
  })
}

function handleManualSave() {
  flushSave()
}
</script>

<template>
  <div class="flex flex-col h-full bg-stone-900 border border-stone-800 rounded-xl overflow-hidden shadow-xl text-stone-100">
    <!-- Header Bar -->
    <div class="flex items-center justify-between px-4 py-2.5 bg-stone-950/80 border-b border-stone-800/80 select-none">
      <div class="flex items-center gap-3">
        <span class="text-amber-400 font-semibold text-xs tracking-wider uppercase flex items-center gap-1.5">
          <span>📝</span> Editor Live Preview
        </span>

        <!-- Save Status Badge -->
        <SaveStatusBadge
          :status="status"
          :last-saved-at="lastSavedAt"
          @retry="handleManualSave"
        />
      </div>

      <!-- Mode Selector Controls -->
      <div class="flex items-center gap-1 bg-stone-900 border border-stone-800 rounded-lg p-0.5 text-xs">
        <button
          class="px-2.5 py-1 rounded transition-colors"
          :class="editorMode === 'edit' ? 'bg-amber-500/20 text-amber-300 font-medium' : 'text-stone-400 hover:text-stone-200'"
          @click="editorMode = 'edit'"
        >
          ✏️ Editar
        </button>
        <button
          class="px-2.5 py-1 rounded transition-colors"
          :class="editorMode === 'preview' ? 'bg-amber-500/20 text-amber-300 font-medium' : 'text-stone-400 hover:text-stone-200'"
          @click="editorMode = 'preview'"
        >
          👁️ Leitura
        </button>
        <button
          class="px-2.5 py-1 rounded transition-colors"
          :class="editorMode === 'split' ? 'bg-amber-500/20 text-amber-300 font-medium' : 'text-stone-400 hover:text-stone-200'"
          @click="editorMode = 'split'"
        >
          📖 Divisão
        </button>
      </div>
    </div>

    <!-- Main Workspace Container -->
    <div class="flex-1 flex overflow-hidden relative">
      <!-- Editor Textarea Area -->
      <div
        v-if="editorMode === 'edit' || editorMode === 'split'"
        class="flex-1 flex flex-col h-full border-r border-stone-800/40 p-4"
        :class="{ 'w-1/2': editorMode === 'split' }"
      >
        <textarea
          ref="editorTextarea"
          v-model="content"
          :readonly="readonly"
          placeholder="Escreva seu artigo em Markdown... Digite [[ para inserir Wikilinks."
          class="w-full h-full bg-transparent resize-none border-none outline-none font-mono text-sm leading-relaxed text-stone-100 placeholder-stone-600 custom-scrollbar"
          @input="onContentInput"
          @keyup="checkWikilinkTrigger"
          @click="checkWikilinkTrigger"
        ></textarea>
      </div>

      <!-- Live Preview Area -->
      <div
        v-if="editorMode === 'preview' || editorMode === 'split'"
        class="flex-1 h-full overflow-y-auto p-6 bg-stone-950/40 custom-scrollbar"
        :class="{ 'w-1/2': editorMode === 'split' }"
      >
        <div v-if="content.trim()" class="prose prose-invert max-w-none text-stone-200 text-sm leading-relaxed space-y-4">
          <WikilinkText :text="content" />
        </div>
        <div v-else class="text-stone-600 italic text-sm p-4 text-center">
          O conteúdo pré-visualizado aparecerá aqui.
        </div>
      </div>
    </div>

    <!-- Wikilink Autocomplete Popover -->
    <WikilinkAutocomplete
      :show="showAutocomplete"
      :search-query="autocompleteQuery"
      :position="autocompletePos"
      @select="handleSelectWikilink"
      @close="showAutocomplete = false"
    />
  </div>
</template>
