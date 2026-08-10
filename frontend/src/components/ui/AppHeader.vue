<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useWorldsStore } from '@/stores/worlds'
import { useAuthStore } from '@/stores/auth'
import { useArticlesStore } from '@/stores/articles'

const router = useRouter()
const worldsStore = useWorldsStore()
const authStore = useAuthStore()
const articlesStore = useArticlesStore()

const showWorldDropdown = ref(false)
const showCreateWorld = ref(false)
const newWorldName = ref('')
const newWorldDesc = ref('')
const globalSearch = ref('')

const role = computed(() => worldsStore.activeWorld?.role ?? 'JOGADOR')
const roleBadgeClass = computed(() => role.value === 'MESTRE' ? 'badge--gold' : 'badge--silver')

function selectWorld(world: any) {
  worldsStore.setActiveWorld(world)
  showWorldDropdown.value = false
  router.push('/dashboard')
}

async function handleCreateWorld() {
  if (!newWorldName.value.trim()) return
  const world = await worldsStore.createWorld(newWorldName.value.trim(), newWorldDesc.value.trim())
  if (world) {
    worldsStore.setActiveWorld(world)
    showCreateWorld.value = false
    newWorldName.value = ''
    newWorldDesc.value = ''
    router.push('/codex')
  }
}

function handleSearch(e: KeyboardEvent) {
  if (e.key === 'Enter' && globalSearch.value.trim()) {
    articlesStore.searchQuery = globalSearch.value.trim()
    router.push('/codex')
  }
}

function logout() {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <header class="app-header">
    <!-- Seletor de Mundo -->
    <div class="world-selector" @click="showWorldDropdown = !showWorldDropdown">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/>
        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
      </svg>
      <span class="world-selector__name">{{ worldsStore.activeWorld?.name ?? 'Selecionar Mundo' }}</span>
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="chevron" :class="{ 'chevron--open': showWorldDropdown }">
        <polyline points="6 9 12 15 18 9"/>
      </svg>
    </div>

    <!-- Dropdown de Mundos -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="showWorldDropdown" class="dropdown-overlay" @click="showWorldDropdown = false">
          <div class="world-dropdown" @click.stop>
            <div class="world-dropdown__header">Seus Mundos</div>
            <button
              v-for="world in worldsStore.worlds"
              :key="world.id"
              class="world-item"
              :class="{ 'world-item--active': world.id === worldsStore.activeWorld?.id }"
              @click="selectWorld(world)"
            >
              <span class="world-item__name">{{ world.name }}</span>
              <span class="badge" :class="world.role === 'MESTRE' ? 'badge--gold' : 'badge--silver'">
                {{ world.role }}
              </span>
            </button>
            <button class="world-item world-item--create" @click="showCreateWorld = true; showWorldDropdown = false">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
              </svg>
              Criar Novo Mundo
            </button>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Busca Global -->
    <div class="global-search">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
      <input
        v-model="globalSearch"
        type="text"
        placeholder="Buscar artigos... (Enter)"
        class="global-search__input"
        @keydown="handleSearch"
      />
      <kbd>⌘K</kbd>
    </div>

    <!-- Ações da direita -->
    <div class="header-actions">
      <!-- Badge de role -->
      <span class="badge" :class="roleBadgeClass">{{ role }}</span>

      <!-- Usuário -->
      <button class="user-btn" title="Sair" @click="logout">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
          <polyline points="16 17 21 12 16 7"/>
          <line x1="21" y1="12" x2="9" y2="12"/>
        </svg>
        <span>{{ authStore.user?.username }}</span>
      </button>
    </div>

    <!-- Modal Criar Mundo -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="showCreateWorld" class="modal-overlay" @click.self="showCreateWorld = false">
          <div class="modal">
            <h3 class="modal__title">Criar Novo Mundo</h3>
            <div class="form-group">
              <label>Nome do Mundo</label>
              <input v-model="newWorldName" type="text" placeholder="Ex: Valoria" class="form-input" autofocus />
            </div>
            <div class="form-group">
              <label>Descrição</label>
              <textarea v-model="newWorldDesc" placeholder="Breve descrição..." class="form-input" rows="3" />
            </div>
            <div class="modal__actions">
              <button class="btn btn--ghost" @click="showCreateWorld = false">Cancelar</button>
              <button class="btn btn--gold" @click="handleCreateWorld">Criar Mundo</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </header>
</template>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: 0 var(--space-6);
  height: 56px;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  z-index: 100;
  flex-shrink: 0;
}

/* World Selector */
.world-selector {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
  cursor: pointer;
  color: var(--color-text);
  transition: background var(--transition-fast);
  min-width: 160px;
}
.world-selector:hover { background: var(--color-surface-2); }
.world-selector__name {
  font-weight: 500;
  font-size: 0.9rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 160px;
}
.chevron { transition: transform var(--transition-fast); }
.chevron--open { transform: rotate(180deg); }

/* Dropdown */
.dropdown-overlay {
  position: fixed; inset: 0; z-index: 200;
}
.world-dropdown {
  position: fixed;
  top: 60px; left: var(--space-4);
  min-width: 240px;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
}
.world-dropdown__header {
  padding: var(--space-3) var(--space-4);
  font-size: 0.7rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-muted);
  border-bottom: 1px solid var(--color-border);
}
.world-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
  width: 100%;
  padding: var(--space-3) var(--space-4);
  background: none;
  border: none;
  color: var(--color-text);
  cursor: pointer;
  font-size: 0.875rem;
  font-family: var(--font-body);
  transition: background var(--transition-fast);
}
.world-item:hover { background: var(--color-surface-3); }
.world-item--active { color: var(--color-gold); }
.world-item--create {
  color: var(--color-text-muted);
  border-top: 1px solid var(--color-border);
  gap: var(--space-2);
  justify-content: flex-start;
}
.world-item--create:hover { color: var(--color-gold); }

/* Global Search */
.global-search {
  flex: 1;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: var(--space-2) var(--space-3);
  max-width: 400px;
  transition: border-color var(--transition-fast);
}
.global-search:focus-within { border-color: var(--color-gold-dim); }
.global-search__input {
  flex: 1;
  background: none;
  border: none;
  outline: none;
  color: var(--color-text);
  font-family: var(--font-body);
  font-size: 0.875rem;
}
.global-search__input::placeholder { color: var(--color-text-dim); }
kbd {
  font-size: 0.65rem;
  padding: 2px 5px;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: 3px;
  color: var(--color-text-dim);
}

/* Header Actions */
.header-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

/* Badges */
.badge {
  font-size: 0.65rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  padding: 3px 8px;
  border-radius: 20px;
}
.badge--gold { background: var(--color-gold-glow); color: var(--color-gold); border: 1px solid var(--color-gold-dim); }
.badge--silver { background: rgba(148,163,184,0.1); color: #94A3B8; border: 1px solid rgba(148,163,184,0.2); }

/* User Button */
.user-btn {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  background: none;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text-muted);
  padding: var(--space-2) var(--space-3);
  cursor: pointer;
  font-size: 0.8rem;
  font-family: var(--font-body);
  transition: all var(--transition-fast);
}
.user-btn:hover { border-color: var(--color-danger); color: var(--color-danger); }

/* Modal */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.7);
  z-index: 300;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(4px);
}
.modal {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-8);
  width: 100%;
  max-width: 440px;
  box-shadow: var(--shadow-lg);
}
.modal__title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-gold);
  margin-bottom: var(--space-6);
}
.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
}
.form-group label {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.form-input {
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text);
  font-family: var(--font-body);
  font-size: 0.9rem;
  padding: var(--space-3) var(--space-4);
  resize: none;
  transition: border-color var(--transition-fast);
}
.form-input:focus {
  outline: none;
  border-color: var(--color-gold-dim);
}
.modal__actions { display: flex; gap: var(--space-3); justify-content: flex-end; margin-top: var(--space-6); }
.btn {
  padding: var(--space-2) var(--space-5);
  border-radius: var(--radius-sm);
  border: none;
  font-family: var(--font-body);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.btn--ghost { background: none; border: 1px solid var(--color-border); color: var(--color-text-muted); }
.btn--ghost:hover { border-color: var(--color-text-muted); color: var(--color-text); }
.btn--gold { background: var(--color-gold); color: #0d0f14; font-weight: 600; }
.btn--gold:hover { background: var(--color-gold-light); box-shadow: var(--shadow-gold); }
</style>
