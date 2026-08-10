<script setup lang="ts">
/**
 * TELA 5: Linha do Tempo — Trilho vertical cronológico com eras e events.
 */
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTimelineStore, type TimelineEra, type TimelineEvent } from '@/stores/timeline'
import { useWorldsStore } from '@/stores/worlds'
import VisibilityBadge from '@/components/ui/VisibilityBadge.vue'

const router = useRouter()
const timelineStore = useTimelineStore()
const worldsStore = useWorldsStore()
const isMestre = computed(() => worldsStore.isMestre)

const showCreateEra = ref(false)
const eraTitle = ref('')
const eraStart = ref(0)
const eraEnd = ref(0)
const creating = ref(false)

onMounted(() => { timelineStore.fetchTimeline() })

/**
 * Organiza eventos dentro de eras, com uma seção "Sem Era" para órfãos.
 */
const organizedTimeline = computed(() => {
  const eras = [...timelineStore.eras].sort((a, b) => a.start_sort_order - b.start_sort_order)
  const events = [...timelineStore.events].sort((a, b) => (a.in_game_sort_order ?? 0) - (b.in_game_sort_order ?? 0))

  const sections: { era: TimelineEra | null; events: TimelineEvent[] }[] = []
  const usedEvents = new Set<string>()

  for (const era of eras) {
    const eraEvents = events.filter((ev) => {
      const order = ev.in_game_sort_order ?? 0
      return order >= era.start_sort_order && order <= era.end_sort_order
    })
    eraEvents.forEach((e) => usedEvents.add(e.article_id))
    sections.push({ era, events: eraEvents })
  }

  const orphans = events.filter((e) => !usedEvents.has(e.article_id))
  if (orphans.length) sections.push({ era: null, events: orphans })

  return sections
})

async function createEra() {
  if (!eraTitle.value.trim()) return
  creating.value = true
  try {
    await timelineStore.createEra(eraTitle.value.trim(), eraStart.value, eraEnd.value)
    showCreateEra.value = false
    eraTitle.value = ''
    eraStart.value = 0
    eraEnd.value = 0
  } finally { creating.value = false }
}

async function deleteEra(id: string) {
  if (!confirm('Remover esta era?')) return
  await timelineStore.deleteEra(id)
}

function openArticle(articleId: string) {
  router.push(`/codex/${articleId}`)
}
</script>

<template>
  <div class="timeline-page">
    <div class="timeline-header">
      <div>
        <h1 class="timeline-title">Linha do Tempo</h1>
        <p class="timeline-subtitle">Cronologia compilada automaticamente dos artigos com datas</p>
      </div>
      <button v-if="isMestre" class="btn-gold-sm" @click="showCreateEra = true">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        Nova Era
      </button>
    </div>

    <div v-if="timelineStore.loading" class="list-empty">Carregando timeline...</div>

    <div v-else-if="timelineStore.events.length === 0 && timelineStore.eras.length === 0" class="list-empty">
      <p>Nenhum evento na timeline.</p>
      <p style="font-size: 0.75rem; margin-top: 0.5rem; color: var(--color-text-dim);">Adicione datas "In-Game" aos artigos para populá-la.</p>
    </div>

    <!-- Timeline Rail -->
    <div v-else class="timeline-rail">
      <div v-for="(section, si) in organizedTimeline" :key="si" class="tl-section">
        <!-- Era Header -->
        <div v-if="section.era" class="tl-era">
          <div class="tl-era__line" />
          <div class="tl-era__label">
            <span>{{ section.era.title }}</span>
            <button v-if="isMestre" class="tl-era__del" title="Remover era" @click="deleteEra(section.era!.id)">×</button>
          </div>
          <div class="tl-era__line" />
        </div>
        <div v-else class="tl-era">
          <div class="tl-era__line" />
          <div class="tl-era__label tl-era__label--orphan">Eventos Sem Era</div>
          <div class="tl-era__line" />
        </div>

        <!-- Event Cards -->
        <div class="tl-events">
          <div
            v-for="(ev, ei) in section.events" :key="ev.article_id"
            class="tl-event" :class="{ 'tl-event--left': ei % 2 === 0, 'tl-event--right': ei % 2 !== 0 }"
          >
            <div class="tl-event__connector">
              <div class="tl-event__dot" />
            </div>
            <button class="tl-event__card" @click="openArticle(ev.article_id)">
              <span class="tl-event__date">{{ ev.in_game_date ?? '—' }}</span>
              <span class="tl-event__title">{{ ev.title }}</span>
              <VisibilityBadge v-if="isMestre" :visibility="ev.visibility" />
            </button>
          </div>
        </div>
      </div>

      <!-- End marker -->
      <div class="tl-end">
        <div class="tl-end__diamond" />
      </div>
    </div>

    <!-- Create Era Modal -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="showCreateEra" class="modal-overlay" @click.self="showCreateEra = false">
          <div class="modal" @click.stop>
            <h3 class="modal__title">Nova Era</h3>
            <div class="form-group">
              <label>Nome da Era</label>
              <input v-model="eraTitle" type="text" class="form-input" placeholder="Ex: Era dos Deuses" autofocus />
            </div>
            <div class="form-row">
              <div class="form-group form-group--flex">
                <label>Sort Order Início</label>
                <input v-model.number="eraStart" type="number" class="form-input" />
              </div>
              <div class="form-group form-group--flex">
                <label>Sort Order Fim</label>
                <input v-model.number="eraEnd" type="number" class="form-input" />
              </div>
            </div>
            <div class="modal__actions">
              <button class="btn btn--ghost" @click="showCreateEra = false">Cancelar</button>
              <button class="btn btn--gold" @click="createEra" :disabled="creating || !eraTitle.trim()">Criar Era</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.timeline-page { max-width: 800px; margin: 0 auto; }

.timeline-header { display: flex; align-items: flex-end; justify-content: space-between; margin-bottom: var(--space-8); }
.timeline-title { font-family: var(--font-display); font-size: 1.5rem; color: var(--color-gold); }
.timeline-subtitle { font-size: 0.8rem; color: var(--color-text-muted); margin-top: var(--space-1); }

/* Timeline Rail */
.timeline-rail { position: relative; padding: var(--space-4) 0; }
.timeline-rail::before {
  content: ''; position: absolute; left: 50%; top: 0; bottom: 0;
  width: 2px; background: linear-gradient(to bottom, var(--color-gold-dim), var(--color-gold), var(--color-gold-dim));
  transform: translateX(-50%);
}

/* Era Dividers */
.tl-era { display: flex; align-items: center; gap: var(--space-4); margin: var(--space-6) 0 var(--space-4); position: relative; z-index: 2; }
.tl-era__line { flex: 1; height: 1px; background: var(--color-gold-dim); }
.tl-era__label {
  font-family: var(--font-display); font-size: 0.8rem; font-weight: 600;
  color: var(--color-gold); text-transform: uppercase; letter-spacing: 0.1em;
  padding: var(--space-2) var(--space-4);
  background: var(--color-surface); border: 1px solid var(--color-gold-dim);
  border-radius: var(--radius-sm); white-space: nowrap;
  display: flex; align-items: center; gap: var(--space-2);
}
.tl-era__label--orphan { color: var(--color-text-dim); border-color: var(--color-border); }
.tl-era__del {
  background: none; border: none; color: var(--color-danger); cursor: pointer;
  font-size: 1rem; font-weight: 700; line-height: 1; opacity: 0.6;
}
.tl-era__del:hover { opacity: 1; }

/* Events */
.tl-events { display: flex; flex-direction: column; gap: var(--space-4); position: relative; }

.tl-event {
  display: flex; align-items: center;
  position: relative; width: 100%;
}
.tl-event--left { justify-content: flex-end; padding-right: calc(50% + var(--space-6)); }
.tl-event--right { justify-content: flex-start; padding-left: calc(50% + var(--space-6)); }

.tl-event__connector {
  position: absolute; left: 50%; transform: translateX(-50%);
  display: flex; align-items: center; justify-content: center;
}
.tl-event__dot {
  width: 10px; height: 10px; border-radius: 50%;
  background: var(--color-gold); border: 2px solid var(--color-bg);
  box-shadow: 0 0 8px var(--color-gold-glow);
}

.tl-event__card {
  display: flex; flex-direction: column; gap: 4px;
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface); border: 1px solid var(--color-border);
  border-radius: var(--radius-md); cursor: pointer;
  font-family: var(--font-body); color: var(--color-text);
  text-align: left; min-width: 180px;
  transition: all var(--transition-fast);
}
.tl-event__card:hover { border-color: var(--color-gold-dim); transform: translateY(-2px); box-shadow: var(--shadow-sm); }
.tl-event__date { font-size: 0.7rem; color: var(--color-gold); font-weight: 600; }
.tl-event__title { font-size: 0.85rem; font-weight: 500; }

/* End Marker */
.tl-end { display: flex; justify-content: center; padding-top: var(--space-6); position: relative; z-index: 2; }
.tl-end__diamond {
  width: 12px; height: 12px; background: var(--color-gold);
  transform: rotate(45deg); border: 2px solid var(--color-bg);
}

.list-empty { padding: var(--space-12); text-align: center; color: var(--color-text-dim); font-size: 0.9rem; }

/* Shared */
.btn-gold-sm { display: flex; align-items: center; gap: 4px; padding: 6px 14px; background: var(--color-gold); color: #0d0f14; border: none; border-radius: var(--radius-sm); font-family: var(--font-body); font-weight: 600; font-size: 0.8rem; cursor: pointer; }
.btn-gold-sm:hover { background: var(--color-gold-light); }

/* Modal */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.7); z-index: 300; display: flex; align-items: center; justify-content: center; backdrop-filter: blur(4px); }
.modal { background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); padding: var(--space-8); width: 100%; max-width: 440px; box-shadow: var(--shadow-lg); }
.modal__title { font-size: 1.1rem; font-weight: 600; color: var(--color-gold); margin-bottom: var(--space-6); }
.form-group { display: flex; flex-direction: column; gap: var(--space-2); margin-bottom: var(--space-4); }
.form-group--flex { flex: 1; }
.form-group label { font-size: 0.75rem; color: var(--color-text-muted); text-transform: uppercase; letter-spacing: 0.06em; }
.form-input { background: var(--color-bg); border: 1px solid var(--color-border); border-radius: var(--radius-sm); color: var(--color-text); font-family: var(--font-body); font-size: 0.85rem; padding: var(--space-2) var(--space-3); }
.form-input:focus { outline: none; border-color: var(--color-gold-dim); }
.form-row { display: flex; gap: var(--space-4); }
.modal__actions { display: flex; gap: var(--space-3); justify-content: flex-end; margin-top: var(--space-6); }
.btn { padding: var(--space-2) var(--space-5); border-radius: var(--radius-sm); border: none; font-family: var(--font-body); font-size: 0.875rem; font-weight: 500; cursor: pointer; }
.btn--ghost { background: none; border: 1px solid var(--color-border); color: var(--color-text-muted); }
.btn--gold { background: var(--color-gold); color: #0d0f14; font-weight: 600; }
.btn--gold:hover { background: var(--color-gold-light); }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
