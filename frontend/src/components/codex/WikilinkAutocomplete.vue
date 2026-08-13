<script setup lang="ts">
import { computed, ref, watch, onMounted, onUnmounted } from 'vue'
import { useArticlesStore } from '@/stores/articles'

const props = defineProps<{
  show: boolean
  searchQuery: string
  position: { top: number; left: number }
}>()

const emit = defineEmits<{
  (e: 'select', title: string): void
  (e: 'close'): void
}>()

const articlesStore = useArticlesStore()
const selectedIndex = ref(0)

const filteredArticles = computed(() => {
  const q = props.searchQuery.trim().toLowerCase()
  if (!q) {
    return articlesStore.articles.slice(0, 8)
  }
  return articlesStore.articles
    .filter((a) => a.title.toLowerCase().includes(q))
    .slice(0, 8)
})

watch(
  () => props.searchQuery,
  () => {
    selectedIndex.value = 0
  }
)

function selectItem(index: number) {
  if (filteredArticles.value[index]) {
    emit('select', filteredArticles.value[index].title)
  }
}

function handleKeyDown(e: KeyboardEvent) {
  if (!props.show) return

  if (e.key === 'ArrowDown') {
    e.preventDefault()
    if (filteredArticles.value.length > 0) {
      selectedIndex.value = (selectedIndex.value + 1) % filteredArticles.value.length
    }
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    if (filteredArticles.value.length > 0) {
      selectedIndex.value =
        (selectedIndex.value - 1 + filteredArticles.value.length) % filteredArticles.value.length
    }
  } else if (e.key === 'Enter' || e.key === 'Tab') {
    e.preventDefault()
    if (filteredArticles.value[selectedIndex.value]) {
      selectItem(selectedIndex.value)
    }
  } else if (e.key === 'Escape') {
    e.preventDefault()
    emit('close')
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown, true)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown, true)
})
</script>

<template>
  <div
    v-if="show && filteredArticles.length > 0"
    class="fixed z-50 w-72 max-h-60 overflow-y-auto bg-stone-900 border border-amber-500/40 rounded-lg shadow-2xl p-1 text-stone-100 backdrop-blur-md custom-scrollbar"
    :style="{ top: `${position.top}px`, left: `${position.left}px` }"
  >
    <div class="px-2 py-1 text-[10px] font-semibold text-amber-400 uppercase tracking-wider border-b border-stone-800 flex items-center justify-between">
      <span>🔗 Wikilink Autocomplete</span>
      <span class="text-stone-500 font-mono text-[9px]">↑↓ Enter</span>
    </div>

    <div class="py-1">
      <div
        v-for="(art, idx) in filteredArticles"
        :key="art.id"
        class="flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs cursor-pointer transition-colors"
        :class="[
          idx === selectedIndex
            ? 'bg-amber-500/20 text-amber-300 font-medium'
            : 'text-stone-300 hover:bg-stone-800 hover:text-stone-100'
        ]"
        @click="selectItem(idx)"
        @mouseenter="selectedIndex = idx"
      >
        <div class="flex items-center gap-2 truncate">
          <span class="text-amber-400">📄</span>
          <span class="truncate">{{ art.title }}</span>
        </div>
        <span v-if="art.in_game_date" class="text-[10px] text-stone-500 whitespace-nowrap ml-2">
          {{ art.in_game_date }}
        </span>
      </div>
    </div>
  </div>
</template>
