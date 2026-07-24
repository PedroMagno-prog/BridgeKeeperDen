<template>
  <div class="timeline-page">
    <header class="timeline-header">
      <h1 class="page-title">Linha do Tempo Cronológica</h1>
      <p class="page-sub">Compilação automática de eventos históricos do mundo.</p>
    </header>

    <!-- Trilho Cronológico Vertical -->
    <div class="timeline-container" v-if="timelineStore.timelineData.timeline_events.length > 0">
      <div class="golden-trail"></div>

      <div
        v-for="(evt, idx) in timelineStore.timelineData.timeline_events"
        :key="idx"
        class="timeline-item"
        @click="openArticle(evt.article_id)"
      >
        <div class="timeline-node">
          <div class="node-dot"></div>
        </div>

        <div class="timeline-card card" :class="{ locked: evt.is_locked }">
          <div class="card-header">
            <span class="event-date">📅 {{ evt.in_game_date || 'Data Antiga' }}</span>
            <span
              class="badge"
              :class="evt.visibility === 'TOTAL' ? 'badge-total' : 'badge-parcial'"
            >
              {{ evt.visibility }}
            </span>
          </div>

          <h3 class="event-title">{{ evt.title }}</h3>
          <p class="event-snippet" v-if="evt.snippet && !evt.is_locked">
            {{ evt.snippet }}...
          </p>
          <p class="event-snippet locked" v-else-if="evt.is_locked">
            🔒 Evento histórico parcialmente oculto pelo mestre.
          </p>
        </div>
      </div>
    </div>

    <div class="empty-state card" v-else>
      <p>Nenhum artigo com data in-game cadastrado para compor a Linha do Tempo.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTimelineStore } from '../stores/timeline'
import { useWorldStore } from '../stores/world'

const timelineStore = useTimelineStore()
const worldStore = useWorldStore()
const router = useRouter()

onMounted(async () => {
  if (worldStore.activeWorldId) {
    await timelineStore.fetchTimeline(worldStore.activeWorldId)
  }
})

function openArticle(articleId: string) {
  if (worldStore.activeWorldId) {
    router.push(`/worlds/${worldStore.activeWorldId}/codex/${articleId}`)
  }
}
</script>

<style scoped>
.timeline-page {
  padding: 2rem;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.page-title {
  font-size: 1.6rem;
  font-weight: 700;
  color: var(--accent-gold);
}

.page-sub {
  font-size: 0.9rem;
  color: var(--text-muted);
}

.timeline-container {
  position: relative;
  max-width: 800px;
  margin: 0 auto;
  padding: 1rem 0;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.golden-trail {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 20px;
  width: 3px;
  background: linear-gradient(180deg, var(--accent-gold) 0%, rgba(212, 175, 55, 0.2) 100%);

  @media (min-width: 768px) {
    left: 50%;
    transform: translateX(-50%);
  }
}

.timeline-item {
  display: flex;
  gap: 1.5rem;
  cursor: pointer;
  position: relative;

  @media (min-width: 768px) {
    &:nth-child(even) {
      flex-direction: row-reverse;
    }
  }
}

.timeline-node {
  position: absolute;
  left: 20px;
  transform: translateX(-50%);
  z-index: 2;

  @media (min-width: 768px) {
    left: 50%;
  }
}

.node-dot {
  width: 16px;
  height: 16px;
  background-color: var(--bg-main);
  border: 3px solid var(--accent-gold);
  border-radius: 50%;
  box-shadow: 0 0 10px rgba(212, 175, 55, 0.5);
}

.timeline-card {
  margin-left: 45px;
  flex-grow: 1;
  transition: transform 0.2s ease, border-color 0.2s ease;

  &:hover {
    transform: translateY(-2px);
    border-color: var(--accent-gold);
  }

  &.locked {
    opacity: 0.8;
  }

  @media (min-width: 768px) {
    margin-left: 0;
    width: 45%;
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.event-date {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--accent-gold);
}

.event-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text-main);
  margin-bottom: 0.4rem;
}

.event-snippet {
  font-size: 0.85rem;
  color: var(--text-muted);
  line-height: 1.4;

  &.locked {
    color: var(--fow-parcial);
    font-style: italic;
  }
}

.empty-state {
  text-align: center;
  padding: 3rem;
}
</style>
