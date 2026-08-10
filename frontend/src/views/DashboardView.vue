<script setup lang="ts">
/**
 * TELA 1: Dashboard e Seleção de Mundo
 * Grade de cards de mundos + atividades recentes.
 */
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useWorldsStore, type World } from '@/stores/worlds'
import { useArticlesStore } from '@/stores/articles'

const router = useRouter()
const worldsStore = useWorldsStore()
const articlesStore = useArticlesStore()

const showCreateModal = ref(false)
const newName = ref('')
const newDesc = ref('')
const creating = ref(false)

onMounted(async () => {
  await worldsStore.fetchWorlds()
  if (worldsStore.activeWorld) {
    await articlesStore.fetchArticles()
  }
})

function selectWorld(world: World) {
  worldsStore.setActiveWorld(world)
  articlesStore.fetchArticles()
  router.push('/codex')
}

async function handleCreate() {
  if (!newName.value.trim()) return
  creating.value = true
  try {
    const world = await worldsStore.createWorld(newName.value.trim(), newDesc.value.trim())
    if (world) {
      worldsStore.setActiveWorld(world)
      showCreateModal.value = false
      newName.value = ''
      newDesc.value = ''
      router.push('/codex')
    }
  } finally {
    creating.value = false
  }
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' })
}
</script>

<template>
  <div class="dashboard">
    <!-- Header -->
    <div class="dashboard__header">
      <div>
        <h1 class="dashboard__title">Seus Mundos</h1>
        <p class="dashboard__subtitle">Selecione uma campanha para explorar</p>
      </div>
      <button class="btn-create" @click="showCreateModal = true">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        Criar Novo Mundo
      </button>
    </div>

    <!-- Grade de Cards -->
    <div v-if="worldsStore.loading" class="loading-state">Carregando mundos...</div>

    <div v-else-if="worldsStore.worlds.length === 0" class="empty-state">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-dim)" stroke-width="1">
        <circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/>
        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
      </svg>
      <p>Nenhum mundo criado ainda.</p>
      <button class="btn-create btn-create--sm" @click="showCreateModal = true">Criar seu primeiro mundo</button>
    </div>

    <div v-else class="worlds-grid">
      <button
        v-for="world in worldsStore.worlds"
        :key="world.id"
        class="world-card"
        :class="{ 'world-card--active': world.id === worldsStore.activeWorld?.id }"
        @click="selectWorld(world)"
      >
        <div class="world-card__header">
          <span class="world-card__title">{{ world.name }}</span>
          <span class="role-badge" :class="world.role === 'MESTRE' ? 'role-badge--gold' : 'role-badge--silver'">
            {{ world.role }}
          </span>
        </div>
        <p class="world-card__desc">{{ world.description || 'Sem descrição' }}</p>
        <div class="world-card__footer">
          <span class="world-card__date">{{ formatDate(world.created_at) }}</span>
        </div>
        <div class="world-card__glow" />
      </button>
    </div>

    <!-- Atividades Recentes -->
    <div v-if="worldsStore.activeWorld && articlesStore.articles.length" class="recent-activity">
      <div class="ornament-divider">Atividade Recente</div>
      <div class="activity-list">
        <div v-for="article in articlesStore.articles.slice(0, 5)" :key="article.id" class="activity-item"
          @click="router.push(`/codex/${article.id}`)">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-dim)" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
          </svg>
          <span class="activity-item__title">{{ article.title }}</span>
          <span class="activity-item__date">{{ formatDate(article.updated_at) }}</span>
        </div>
      </div>
    </div>

    <!-- Modal Criar Mundo -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
          <div class="modal" @click.stop>
            <h3 class="modal__title">Criar Novo Mundo</h3>
            <div class="form-group">
              <label>Nome do Mundo</label>
              <input v-model="newName" type="text" placeholder="Ex: Terras de Valoria" class="form-input" autofocus @keydown.enter="handleCreate" />
            </div>
            <div class="form-group">
              <label>Descrição</label>
              <textarea v-model="newDesc" placeholder="Breve descrição da campanha..." class="form-input" rows="3" />
            </div>
            <div class="modal__actions">
              <button class="btn btn--ghost" @click="showCreateModal = false" :disabled="creating">Cancelar</button>
              <button class="btn btn--gold" @click="handleCreate" :disabled="creating || !newName.trim()">
                {{ creating ? 'Criando...' : 'Criar Mundo' }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.dashboard { max-width: 960px; margin: 0 auto; }

.dashboard__header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-bottom: var(--space-8);
}
.dashboard__title {
  font-family: var(--font-display);
  font-size: 1.8rem;
  font-weight: 600;
  color: var(--color-gold);
}
.dashboard__subtitle { color: var(--color-text-muted); font-size: 0.9rem; margin-top: var(--space-1); }

/* Create Button */
.btn-create {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-5);
  background: var(--color-gold);
  color: #0d0f14;
  border: none;
  border-radius: var(--radius-sm);
  font-family: var(--font-body);
  font-weight: 600;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.btn-create:hover { background: var(--color-gold-light); box-shadow: var(--shadow-gold); }
.btn-create--sm { font-size: 0.8rem; padding: var(--space-2) var(--space-4); margin-top: var(--space-4); }

/* Worlds Grid */
.worlds-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-4);
}

.world-card {
  position: relative;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-5);
  cursor: pointer;
  text-align: left;
  font-family: var(--font-body);
  transition: all 0.25s ease;
  overflow: hidden;
  color: var(--color-text);
}
.world-card:hover {
  border-color: var(--color-border-glow);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}
.world-card--active { border-color: var(--color-gold-dim); }
.world-card--active .world-card__glow {
  opacity: 1;
}
.world-card__glow {
  position: absolute;
  top: -1px; left: -1px; right: -1px;
  height: 3px;
  background: linear-gradient(90deg, var(--color-gold-dim), var(--color-gold), var(--color-gold-dim));
  opacity: 0;
  transition: opacity 0.3s;
}
.world-card:hover .world-card__glow { opacity: 0.6; }

.world-card__header { display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--space-3); }
.world-card__title { font-weight: 600; font-size: 1rem; }
.world-card__desc { font-size: 0.8rem; color: var(--color-text-muted); line-height: 1.5; margin-bottom: var(--space-4); min-height: 36px; }
.world-card__footer { display: flex; align-items: center; justify-content: space-between; }
.world-card__date { font-size: 0.7rem; color: var(--color-text-dim); }

/* Role Badge */
.role-badge {
  font-size: 0.6rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  padding: 2px 8px;
  border-radius: 10px;
}
.role-badge--gold { background: var(--color-gold-glow); color: var(--color-gold); border: 1px solid var(--color-gold-dim); }
.role-badge--silver { background: rgba(148,163,184,0.1); color: #94A3B8; border: 1px solid rgba(148,163,184,0.2); }

/* Empty / Loading */
.empty-state, .loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-4);
  padding: var(--space-16);
  color: var(--color-text-dim);
  font-size: 0.9rem;
}

/* Recent Activity */
.recent-activity { margin-top: var(--space-10); }
.activity-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}
.activity-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background var(--transition-fast);
}
.activity-item:hover { background: var(--color-surface); }
.activity-item__title { flex: 1; font-size: 0.875rem; }
.activity-item__date { font-size: 0.7rem; color: var(--color-text-dim); }

/* Modal shared styles */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.7);
  z-index: 300;
  display: flex; align-items: center; justify-content: center;
  backdrop-filter: blur(4px);
}
.modal {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-8);
  width: 100%; max-width: 440px;
  box-shadow: var(--shadow-lg);
}
.modal__title { font-size: 1.1rem; font-weight: 600; color: var(--color-gold); margin-bottom: var(--space-6); }
.form-group { display: flex; flex-direction: column; gap: var(--space-2); margin-bottom: var(--space-4); }
.form-group label { font-size: 0.75rem; color: var(--color-text-muted); text-transform: uppercase; letter-spacing: 0.06em; }
.form-input {
  background: var(--color-bg); border: 1px solid var(--color-border); border-radius: var(--radius-sm);
  color: var(--color-text); font-family: var(--font-body); font-size: 0.9rem;
  padding: var(--space-3) var(--space-4); resize: none;
  transition: border-color var(--transition-fast);
}
.form-input:focus { outline: none; border-color: var(--color-gold-dim); }
.modal__actions { display: flex; gap: var(--space-3); justify-content: flex-end; margin-top: var(--space-6); }
.btn {
  padding: var(--space-2) var(--space-5); border-radius: var(--radius-sm); border: none;
  font-family: var(--font-body); font-size: 0.875rem; font-weight: 500; cursor: pointer;
  transition: all var(--transition-fast);
}
.btn--ghost { background: none; border: 1px solid var(--color-border); color: var(--color-text-muted); }
.btn--ghost:hover { border-color: var(--color-text-muted); color: var(--color-text); }
.btn--gold { background: var(--color-gold); color: #0d0f14; font-weight: 600; }
.btn--gold:hover { background: var(--color-gold-light); box-shadow: var(--shadow-gold); }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
