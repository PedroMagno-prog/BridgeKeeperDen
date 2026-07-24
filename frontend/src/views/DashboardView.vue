<template>
  <div class="dashboard-page">
    <div class="header-banner">
      <div>
        <h1 class="page-title">Seus Mundos & Campanhas</h1>
        <p class="page-sub">Escolha um mundo para acessar o Codex, Mapas e Linha do Tempo.</p>
      </div>
      <button class="btn-primary" @click="showCreateModal = true">
        <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Criar Novo Mundo
      </button>
    </div>

    <!-- Grade de Cards de Mundos -->
    <div class="worlds-grid" v-if="worldStore.worlds.length > 0">
      <div
        v-for="w in worldStore.worlds"
        :key="w.id"
        class="world-card card"
        @click="openWorld(w.id)"
      >
        <div class="world-card-header">
          <h2 class="world-title">{{ w.name }}</h2>
          <span class="badge" :class="w.user_role === 'MESTRE' ? 'badge-mestre' : 'badge-jogador'">
            {{ w.user_role }}
          </span>
        </div>
        <p class="world-desc">{{ w.description || 'Sem descrição cadastrada.' }}</p>
        <div class="world-card-footer">
          <span class="created-at">Criado em {{ formatDate(w.created_at) }}</span>
          <span class="enter-link">Acessar &rarr;</span>
        </div>
      </div>
    </div>

    <div class="empty-state card" v-else>
      <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <circle cx="12" cy="12" r="10" stroke-width="2"/>
        <path stroke-width="2" d="M2 12h20M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z"/>
      </svg>
      <h3>Nenhum mundo encontrado</h3>
      <p>Crie seu primeiro mundo ou peça ao Mestre para lhe adicionar como Jogador.</p>
    </div>

    <!-- Modal Criar Mundo -->
    <div class="modal-backdrop" v-if="showCreateModal">
      <div class="modal-card card">
        <div class="modal-header">
          <h3>Criar Novo Mundo</h3>
          <button class="close-btn" @click="showCreateModal = false">&times;</button>
        </div>
        <form @submit.prevent="handleCreateWorld" class="form">
          <div class="input-group">
            <label>Nome do Mundo / Campanha *</label>
            <input type="text" v-model="newWorldName" class="input-field" placeholder="Ex: Valoria, Reino dos Anões" required />
          </div>
          <div class="input-group">
            <label>Descrição Curta</label>
            <textarea v-model="newWorldDesc" class="input-field textarea" placeholder="Resumo do cenário..."></textarea>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="showCreateModal = false">Cancelar</button>
            <button type="submit" class="btn-primary">Criar Mundo</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useWorldStore } from '../stores/world'

const worldStore = useWorldStore()
const router = useRouter()

const showCreateModal = ref(false)
const newWorldName = ref('')
const newWorldDesc = ref('')

onMounted(async () => {
  await worldStore.fetchWorlds()
})

function openWorld(worldId: string) {
  worldStore.selectWorld(worldId)
  router.push(`/worlds/${worldId}/codex`)
}

async function handleCreateWorld() {
  if (!newWorldName.value.trim()) return
  const created = await worldStore.createWorld(newWorldName.value, newWorldDesc.value)
  showCreateModal.value = false
  newWorldName.value = ''
  newWorldDesc.value = ''
  router.push(`/worlds/${created.id}/codex`)
}

function formatDate(isoStr: string) {
  if (!isoStr) return ''
  return new Date(isoStr).toLocaleDateString('pt-BR')
}
</script>

<style scoped>
.dashboard-page {
  padding: 2rem;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.header-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
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

.btn-icon {
  width: 1.1rem;
  height: 1.1rem;
}

.worlds-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.world-card {
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  transition: transform 0.2s ease, border-color 0.2s ease;
}

.world-card:hover {
  transform: translateY(-3px);
  border-color: var(--accent-gold);
}

.world-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.world-title {
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--text-main);
}

.world-desc {
  font-size: 0.85rem;
  color: var(--text-muted);
  flex-grow: 1;
}

.world-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid var(--border-color);
  padding-top: 0.75rem;
  font-size: 0.8rem;

  .created-at {
    color: var(--text-muted);
  }

  .enter-link {
    color: var(--accent-gold);
    font-weight: 600;
  }
}

.empty-state {
  text-align: center;
  padding: 3rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;

  .empty-icon {
    width: 3rem;
    height: 3rem;
    color: var(--text-muted);
  }
}

/* Modal */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
}

.modal-card {
  width: 100%;
  max-width: 450px;

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;

    h3 {
      color: var(--accent-gold);
    }

    .close-btn {
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-size: 1.5rem;
      cursor: pointer;
    }
  }
}

.form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;

  label {
    font-size: 0.85rem;
    color: var(--text-muted);
  }

  .textarea {
    min-height: 80px;
    resize: vertical;
  }
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 0.5rem;
}
</style>
