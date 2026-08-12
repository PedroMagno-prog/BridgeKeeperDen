<script setup lang="ts">
/**
 * Modal / Drawer de pré-visualização rápida de Artigos (Quick Preview via Wikilink).
 */
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useArticlesStore, type Article } from '@/stores/articles'
import VisibilityBadge from '@/components/ui/VisibilityBadge.vue'

const props = defineProps<{
  articleId: string | null
  title?: string
  show: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const router = useRouter()
const articlesStore = useArticlesStore()

const loading = ref(false)
const articleData = ref<Article | null>(null)

watch(
  () => [props.show, props.articleId],
  async ([show, articleId]) => {
    if (show && articleId) {
      loading.value = true
      try {
        const data = await articlesStore.fetchArticle(articleId as string)
        articleData.value = data || null
      } finally {
        loading.value = false
      }
    } else {
      articleData.value = null
    }
  },
  { immediate: true }
)

function navigateToFull() {
  if (props.articleId) {
    emit('close')
    router.push(`/codex/${props.articleId}`)
  }
}
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="show" class="preview-backdrop" @click.self="emit('close')">
        <div class="preview-card">
          <!-- Header -->
          <div class="preview-card__header">
            <div class="header-left">
              <span class="preview-icon">📖</span>
              <div>
                <h3 class="preview-title">
                  {{ articleData?.title || title || 'Artigo' }}
                  <VisibilityBadge v-if="articleData" :visibility="articleData.visibility" size="sm" />
                </h3>
                <span v-if="articleData?.in_game_date" class="preview-date">
                  📅 {{ articleData.in_game_date }}
                </span>
              </div>
            </div>
            <button class="close-btn" @click="emit('close')">✕</button>
          </div>

          <!-- Body -->
          <div class="preview-card__body">
            <div v-if="loading" class="loading-box">
              <span>Carregando resumo...</span>
            </div>

            <div v-else-if="articleData" class="content-box">
              <!-- Tags -->
              <div v-if="articleData.tags && articleData.tags.length > 0" class="tags-row">
                <span v-for="tag in articleData.tags" :key="tag" class="tag-pill">{{ tag }}</span>
              </div>

              <!-- Seções -->
              <div v-if="articleData.sections && articleData.sections.length > 0" class="sections-list">
                <div v-for="sec in articleData.sections" :key="sec.id" class="sec-preview">
                  <h4 class="sec-title">{{ sec.title }}</h4>
                  <p class="sec-text">{{ sec.content }}</p>
                </div>
              </div>
              <div v-else class="no-sections">
                Nenhum conteúdo detalhado nesta ficha.
              </div>
            </div>

            <div v-else class="empty-box">
              <span>Artigo não encontrado ou protegido por Névoa de Guerra.</span>
            </div>
          </div>

          <!-- Footer -->
          <div class="preview-card__footer">
            <button class="btn btn-secondary" @click="emit('close')">Fechar</button>
            <button v-if="articleId" class="btn btn-primary" @click="navigateToFull">
              Abrir Artigo Completo ➔
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.preview-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.65);
  z-index: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(4px);
}

.preview-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  width: 100%;
  max-width: 520px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 16px 36px rgba(0, 0, 0, 0.6);
  overflow: hidden;
}

.preview-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-4) var(--space-5);
  background: var(--color-surface-2);
  border-bottom: 1px solid var(--color-border);
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.preview-icon {
  font-size: 1.4rem;
}

.preview-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-gold);
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.preview-date {
  font-size: 0.75rem;
  color: var(--color-text-dim);
}

.close-btn {
  background: none;
  border: none;
  color: var(--color-text-dim);
  font-size: 1.1rem;
  cursor: pointer;
}
.close-btn:hover { color: var(--color-text); }

.preview-card__body {
  padding: var(--space-5);
  overflow-y: auto;
  flex: 1;
}

.loading-box, .empty-box {
  text-align: center;
  padding: var(--space-6);
  color: var(--color-text-dim);
}

.tags-row {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: var(--space-4);
}

.tag-pill {
  background: var(--color-gold-glow);
  color: var(--color-gold);
  border: 1px solid var(--color-gold-dim);
  border-radius: 12px;
  font-size: 0.7rem;
  padding: 2px 8px;
}

.sections-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.sec-preview {
  border-left: 2px solid var(--color-gold);
  padding-left: var(--space-3);
}

.sec-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 2px;
}

.sec-text {
  font-size: 0.85rem;
  color: var(--color-text-muted);
  white-space: pre-wrap;
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.preview-card__footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  background: var(--color-surface-2);
  border-top: 1px solid var(--color-border);
}

.btn {
  padding: 6px 14px;
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  border: none;
}
.btn-primary { background: var(--color-gold); color: #111827; }
.btn-secondary { background: var(--color-surface-3); color: var(--color-text); }
</style>
