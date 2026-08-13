<script setup lang="ts">
/**
 * Componente Reativo para Renderização de Textos contendo Wikilinks ([[Artigo|Rótulo]]).
 */
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { parseWikilinks, type ParsedSegment } from '@/utils/wikilinkParser'
import { useArticlesStore, type ArticleResolveResult } from '@/stores/articles'
import WikilinkPreviewModal from './WikilinkPreviewModal.vue'

const props = defineProps<{
  text: string
}>()

const router = useRouter()
const articlesStore = useArticlesStore()

const resolvedLinks = ref<Record<string, ArticleResolveResult>>({})
const activePreviewId = ref<string | null>(null)
const activePreviewTitle = ref<string>('')
const showPreview = ref(false)

const segments = computed<ParsedSegment[]>(() => {
  return parseWikilinks(props.text || '')
})

async function resolveWikilinks() {
  const wikilinkSegments = segments.value.filter((s) => s.type === 'wikilink') as Array<{
    type: 'wikilink'
    targetTitle: string
  }>

  for (const seg of wikilinkSegments) {
    const key = seg.targetTitle.toLowerCase()
    if (!resolvedLinks.value[key]) {
      const res = await articlesStore.resolveArticle(seg.targetTitle)
      if (res) {
        resolvedLinks.value[key] = res
      }
    }
  }
}

onMounted(() => {
  resolveWikilinks()
})

watch(
  () => props.text,
  () => {
    resolveWikilinks()
  }
)

function getResolved(targetTitle: string): ArticleResolveResult | undefined {
  return resolvedLinks.value[targetTitle.toLowerCase()]
}

function handleClick(e: MouseEvent, targetTitle: string) {
  const res = getResolved(targetTitle)
  if (e.ctrlKey || e.metaKey) {
    if (res?.exists && res.article_id) {
      router.push(`/codex/${res.article_id}`)
    }
    return
  }

  if (res?.exists && res.article_id) {
    activePreviewId.value = res.article_id
    activePreviewTitle.value = res.title
    showPreview.value = true
  }
}

function handleDblClick(targetTitle: string) {
  const res = getResolved(targetTitle)
  if (res?.exists && res.article_id) {
    router.push(`/codex/${res.article_id}`)
  }
}

function handleBrokenClick(targetTitle: string) {
  if (confirm(`O artigo "${targetTitle}" não existe. Deseja criar um novo artigo no Codex com este título?`)) {
    articlesStore.createArticle({
      title: targetTitle,
      content: `Artigo criado a partir do Wikilink [[${targetTitle}]].`,
    } as any).then((newArt) => {
      if (newArt) {
        resolveWikilinks()
        router.push(`/codex/${newArt.id}`)
      }
    })
  }
}
</script>

<template>
  <span class="wikilink-container">
    <template v-for="(seg, idx) in segments" :key="idx">
      <!-- Texto Puro -->
      <span v-if="seg.type === 'text'">{{ seg.content }}</span>

      <!-- Wikilink -->
      <template v-else-if="seg.type === 'wikilink'">
        <button
          v-if="getResolved(seg.targetTitle)?.exists"
          class="wikilink"
          :class="{ 'wikilink--locked': getResolved(seg.targetTitle)?.is_locked }"
          @click="(e) => handleClick(e, seg.targetTitle)"
          @dblclick="handleDblClick(seg.targetTitle)"
          :title="
            getResolved(seg.targetTitle)?.is_locked
              ? 'Visão Parcial (Bloqueado)'
              : 'Clique para pré-visualizar | Ctrl+Clique ou Duplo clique para abrir'
          "
        >
          <span class="link-icon">🔗</span>
          <span class="link-text">{{ seg.displayText }}</span>
        </button>

        <button
          v-else
          class="wikilink wikilink--broken"
          @click="handleBrokenClick(seg.targetTitle)"
          title="Artigo não encontrado no Codex. Clique para criar."
        >
          <span class="link-icon">❓</span>
          <span class="link-text">{{ seg.displayText }}</span>
        </button>
      </template>
    </template>

    <!-- Quick Preview Modal -->
    <WikilinkPreviewModal
      :show="showPreview"
      :article-id="activePreviewId"
      :title="activePreviewTitle"
      @close="showPreview = false"
    />
  </span>
</template>

<style scoped>
.wikilink-container {
  line-height: 1.6;
}

.wikilink {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  background: rgba(16, 185, 129, 0.1);
  color: #10B981;
  border: 1px solid rgba(16, 185, 129, 0.3);
  padding: 1px 6px;
  border-radius: 4px;
  font-family: var(--font-body);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  vertical-align: baseline;
  transition: all var(--transition-fast);
  margin: 0 2px;
}

.wikilink:hover {
  background: rgba(16, 185, 129, 0.25);
  border-color: #10B981;
}

.wikilink--locked {
  background: rgba(201, 168, 76, 0.12);
  color: var(--color-gold);
  border-color: rgba(201, 168, 76, 0.3);
}

.wikilink--broken {
  background: rgba(239, 68, 68, 0.1);
  color: #EF4444;
  border: 1px dashed rgba(239, 68, 68, 0.4);
}

.wikilink--broken:hover {
  background: rgba(239, 68, 68, 0.2);
  border-style: solid;
}

.link-icon {
  font-size: 0.75rem;
  opacity: 0.8;
}

.link-text {
  text-decoration: underline;
  text-decoration-color: transparent;
  transition: text-decoration-color 0.2s;
}

.wikilink:hover .link-text {
  text-decoration-color: currentColor;
}
</style>
