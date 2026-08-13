<script setup lang="ts">
/**
 * Popover flutuante para marcadores de mapa (Pins).
 */
import { useRouter } from 'vue-router'
import type { MapPin } from '@/stores/maps'
import VisibilityBadge from '@/components/ui/VisibilityBadge.vue'
import WikilinkText from '@/components/ui/WikilinkText.vue'

const props = defineProps<{
  pin: MapPin
  isMestre: boolean
  x: number
  y: number
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'edit', pin: MapPin): void
  (e: 'delete', pin: MapPin): void
  (e: 'explore-map', mapId: string): void
}>()

const router = useRouter()

function openCodexArticle(articleId: string) {
  router.push(`/codex/${articleId}`)
}
</script>

<template>
  <div
    class="pin-popover"
    :style="{ left: `${x}px`, top: `${y}px` }"
    @click.stop
  >
    <!-- Header -->
    <div class="popover-header">
      <div class="header-title">
        <span class="pin-badge" :style="{ backgroundColor: pin.color }"></span>
        <h4 class="title-text">{{ pin.title }}</h4>
        <VisibilityBadge :visibility="pin.visibility" size="sm" />
      </div>
      <button class="btn-close" @click="emit('close')">✕</button>
    </div>

    <!-- Body -->
    <div class="popover-body">
      <!-- Caso Bloqueado (Parcial) -->
      <div v-if="pin.is_locked" class="locked-box">
        <span class="lock-icon">🔒</span>
        <span>Local conhecido na cartografia, mas os detalhes detalhados permanecem ocultos pela Névoa de Guerra.</span>
      </div>

      <!-- Vínculo a Artigo do Codex -->
      <div v-else-if="pin.target_article" class="article-box">
        <div class="article-header">
          <span class="article-label">📖 Artigo do Codex:</span>
          <span class="article-title">{{ pin.target_article.title }}</span>
        </div>

        <div v-if="pin.target_article.tags.length > 0" class="tags-row">
          <span v-for="tag in pin.target_article.tags" :key="tag" class="tag-pill">{{ tag }}</span>
        </div>

        <div v-if="pin.target_article.first_section_preview" class="preview-text">
          <WikilinkText :text="pin.target_article.first_section_preview" />
        </div>

        <button class="btn-link-action" @click="openCodexArticle(pin.target_article.id)">
          Abrir Artigo no Codex ➔
        </button>
      </div>

      <!-- Vínculo a Sub-Mapa -->
      <div v-else-if="pin.target_map_id" class="submap-box">
        <div class="submap-header">
          <span class="submap-icon">🗺️</span>
          <div>
            <span class="submap-label">Sub-Mapa Vinculado</span>
            <h5 class="submap-title">{{ pin.target_map_title || 'Mapa Secundário' }}</h5>
          </div>
        </div>
        <button class="btn-submap-action" @click="emit('explore-map', pin.target_map_id)">
          Explorar Sub-Mapa ➔
        </button>
      </div>

      <!-- Sem Vínculo -->
      <div v-else class="empty-box">
        Ponto de interesse marcado no mapa.
      </div>
    </div>

    <!-- Footer para Mestre ou Criador -->
    <div v-if="isMestre || pin.can_edit" class="popover-footer">
      <button v-if="isMestre || pin.can_edit" class="btn-sm btn-ghost" @click="emit('edit', pin)">✏️ Editar</button>
      <button v-if="isMestre || pin.can_delete" class="btn-sm btn-danger" @click="emit('delete', pin)">🗑️ Excluir</button>
    </div>
  </div>
</template>

<style scoped>
.pin-popover {
  position: absolute;
  transform: translate(-50%, -100%) translateY(-12px);
  width: 280px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.6);
  z-index: 400;
  overflow: hidden;
  animation: popIn 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes popIn {
  from { opacity: 0; transform: translate(-50%, -95%) scale(0.95); }
  to { opacity: 1; transform: translate(-50%, -100%) scale(1); }
}

.popover-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: var(--color-surface-2);
  border-bottom: 1px solid var(--color-border);
}

.header-title {
  display: flex;
  align-items: center;
  gap: 6px;
}

.pin-badge {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.title-text {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
}

.btn-close {
  background: none;
  border: none;
  color: var(--color-text-dim);
  cursor: pointer;
  font-size: 0.9rem;
}
.btn-close:hover { color: var(--color-text); }

.popover-body {
  padding: 12px;
  font-size: 0.85rem;
}

.locked-box {
  display: flex;
  gap: 8px;
  color: var(--color-text-dim);
  font-style: italic;
  font-size: 0.8rem;
  line-height: 1.4;
}

.article-box, .submap-box, .empty-box {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.article-label, .submap-label {
  font-size: 0.7rem;
  color: var(--color-text-dim);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.article-title {
  font-weight: 600;
  color: var(--color-gold);
}

.tags-row {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.tag-pill {
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  font-size: 0.65rem;
  padding: 1px 6px;
  color: var(--color-text-muted);
}

.preview-text {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  max-height: 80px;
  overflow-y: auto;
  line-height: 1.4;
}

.submap-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.submap-icon { font-size: 1.2rem; }
.submap-title { font-size: 0.9rem; font-weight: 600; color: var(--color-gold); margin: 0; }

.btn-link-action, .btn-submap-action {
  margin-top: 4px;
  padding: 6px;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-gold);
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  text-align: center;
  transition: all var(--transition-fast);
}

.btn-link-action:hover, .btn-submap-action:hover {
  background: var(--color-gold-glow);
  border-color: var(--color-gold-dim);
}

.popover-footer {
  display: flex;
  justify-content: flex-end;
  gap: 6px;
  padding: 6px 12px;
  background: var(--color-surface-2);
  border-top: 1px solid var(--color-border);
}

.btn-sm {
  padding: 3px 8px;
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  border: none;
  cursor: pointer;
}
.btn-ghost { background: none; color: var(--color-text-muted); border: 1px solid var(--color-border); }
.btn-ghost:hover { border-color: var(--color-gold-dim); color: var(--color-gold); }
.btn-danger { background: none; color: var(--color-danger); border: 1px solid rgba(239, 68, 68, 0.3); }
.btn-danger:hover { background: rgba(239, 68, 68, 0.2); }
</style>
