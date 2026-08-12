<script setup lang="ts">
/**
 * Textarea inteligente com Autocomplete para Wikilinks ([[Artigo]]).
 */
import { ref, watch } from 'vue'
import { useArticlesStore, type MentionSuggestion } from '@/stores/articles'
import VisibilityBadge from '@/components/ui/VisibilityBadge.vue'

const props = withDefaults(
  defineProps<{
    modelValue: string
    rows?: number
    placeholder?: string
  }>(),
  {
    rows: 4,
    placeholder: 'Digite o conteúdo... Use [[Nome do Artigo]] para criar links.',
  }
)

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const articlesStore = useArticlesStore()

const textareaRef = ref<HTMLTextAreaElement | null>(null)
const showSuggestions = ref(false)
const suggestions = ref<MentionSuggestion[]>([])
const selectedIndex = ref(0)
const mentionQuery = ref('')
const mentionMatchStart = ref(-1)

async function handleInput(e: Event) {
  const target = e.target as HTMLTextAreaElement
  const val = target.value
  emit('update:modelValue', val)

  const cursor = target.selectionStart
  const textBeforeCursor = val.slice(0, cursor)

  // Verifica se há um `[[` recente sem um `]]` de fechamento
  const lastOpenIndex = textBeforeCursor.lastIndexOf('[[')
  const lastCloseIndex = textBeforeCursor.lastIndexOf(']]')

  if (lastOpenIndex !== -1 && lastOpenIndex > lastCloseIndex) {
    const query = textBeforeCursor.slice(lastOpenIndex + 2)
    // Se a query não contiver quebras de linha ou pipes adicionais
    if (!query.includes('\n') && !query.includes('|')) {
      mentionQuery.value = query
      mentionMatchStart.value = lastOpenIndex
      const results = await articlesStore.searchMentions(query)
      suggestions.value = results
      selectedIndex.value = 0
      showSuggestions.value = results.length > 0
      return
    }
  }

  showSuggestions.value = false
}

function handleKeyDown(e: KeyboardEvent) {
  if (!showSuggestions.value) return

  if (e.key === 'ArrowDown') {
    e.preventDefault()
    selectedIndex.value = (selectedIndex.value + 1) % suggestions.value.length
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    selectedIndex.value = (selectedIndex.value - 1 + suggestions.value.length) % suggestions.value.length
  } else if (e.key === 'Enter' || e.key === 'Tab') {
    e.preventDefault()
    const selected = suggestions.value[selectedIndex.value]
    if (selected) selectSuggestion(selected)
  } else if (e.key === 'Escape') {
    showSuggestions.value = false
  }
}

function handleBlur() {
  window.setTimeout(() => (showSuggestions.value = false), 200)
}

function selectSuggestion(item: MentionSuggestion) {
  if (!item || !textareaRef.value) return

  const val = props.modelValue
  const cursor = textareaRef.value.selectionStart
  const beforeMatch = val.slice(0, mentionMatchStart.value)
  const afterCursor = val.slice(cursor)

  const replacement = `[[${item.title}]]`
  const newValue = beforeMatch + replacement + afterCursor

  emit('update:modelValue', newValue)
  showSuggestions.value = false

  // Posiciona o cursor após o link inserido
  window.setTimeout(() => {
    if (textareaRef.value) {
      const newCursorPos = beforeMatch.length + replacement.length
      textareaRef.value.setSelectionRange(newCursorPos, newCursorPos)
      textareaRef.value.focus()
    }
  }, 0)
}
</script>

<template>
  <div class="wikilink-input-container">
    <textarea
      ref="textareaRef"
      :value="modelValue"
      :rows="rows"
      :placeholder="placeholder"
      class="wikilink-textarea"
      @input="handleInput"
      @keydown="handleKeyDown"
      @blur="handleBlur"
    ></textarea>

    <!-- Popover de Sugestões / Autocomplete -->
    <div v-if="showSuggestions" class="suggestions-popover">
      <div class="popover-header">Sugestões de Artigos ([[)</div>
      <button
        v-for="(item, idx) in suggestions"
        :key="item.id"
        class="suggestion-item"
        :class="{ 'suggestion-item--active': idx === selectedIndex }"
        @mousedown.prevent="selectSuggestion(item)"
      >
        <span class="item-title">📖 {{ item.title }}</span>
        <VisibilityBadge :visibility="item.visibility" size="sm" />
      </button>
    </div>
  </div>
</template>

<style scoped>
.wikilink-input-container {
  position: relative;
  width: 100%;
}

.wikilink-textarea {
  width: 100%;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: var(--space-3);
  color: var(--color-text);
  font-family: var(--font-body);
  font-size: 0.9rem;
  line-height: 1.5;
  outline: none;
  resize: vertical;
  transition: border-color var(--transition-fast);
}

.wikilink-textarea:focus {
  border-color: var(--color-gold);
}

/* Suggestions Popover */
.suggestions-popover {
  position: absolute;
  left: 0;
  bottom: 100%;
  margin-bottom: 4px;
  width: 100%;
  max-width: 360px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
  z-index: 200;
  max-height: 220px;
  overflow-y: auto;
}

.popover-header {
  padding: 6px 10px;
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--color-text-dim);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface-2);
}

.suggestion-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 8px 12px;
  background: none;
  border: none;
  color: var(--color-text);
  cursor: pointer;
  font-family: var(--font-body);
  font-size: 0.85rem;
  text-align: left;
  transition: background var(--transition-fast);
}

.suggestion-item:hover,
.suggestion-item--active {
  background: var(--color-gold-glow);
  color: var(--color-gold);
}

.item-title {
  font-weight: 500;
}
</style>
