<template>
  <header class="app-header">
    <div class="left-section">
      <div class="logo-area">
        <svg class="logo-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
        <span class="logo-title">BridgeKeeper</span>
      </div>

      <!-- Seletor de Mundo -->
      <div class="world-selector">
        <svg class="world-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <circle cx="12" cy="12" r="10" stroke-width="2"/>
          <path stroke-width="2" d="M2 12h20M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z"/>
        </svg>
        <select :value="worldStore.activeWorldId" @change="onWorldChange" class="world-dropdown">
          <option v-for="w in worldStore.worlds" :key="w.id" :value="w.id">
            {{ w.name }}
          </option>
        </select>
      </div>

      <!-- Badge de Role -->
      <span class="badge" :class="worldStore.activeUserRole === 'MESTRE' ? 'badge-mestre' : 'badge-jogador'">
        {{ worldStore.activeUserRole }}
      </span>
    </div>

    <div class="right-section">
      <!-- Busca Global (Ctrl+K) -->
      <div class="search-box">
        <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
        </svg>
        <input type="text" placeholder="Buscar no mundo... (Ctrl+K)" class="search-input" v-model="searchQuery" @keyup.enter="handleSearch" />
      </div>

      <!-- Botão Rolador de Dados -->
      <button class="dice-btn" @click="$emit('toggle-dice')" title="Rolador de Dados RPG">
        <svg class="dice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
        </svg>
        <span>Dados</span>
      </button>

      <!-- Menu de Usuário -->
      <div class="user-menu" v-if="authStore.user">
        <span class="username">{{ authStore.user.username }}</span>
        <button class="logout-btn" @click="authStore.logout" title="Sair">
          <svg class="logout-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
          </svg>
        </button>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { useWorldStore } from '../../stores/world'

defineEmits(['toggle-dice'])

const authStore = useAuthStore()
const worldStore = useWorldStore()
const router = useRouter()
const searchQuery = ref('')

function onWorldChange(event: Event) {
  const target = event.target as HTMLSelectElement
  if (target.value) {
    worldStore.selectWorld(target.value)
    router.push(`/worlds/${target.value}/codex`)
  }
}

function handleSearch() {
  if (searchQuery.value.trim() && worldStore.activeWorldId) {
    router.push({
      path: `/worlds/${worldStore.activeWorldId}/codex`,
      query: { search: searchQuery.value },
    })
  }
}

function onKeyDown(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault()
    const input = document.querySelector('.search-input') as HTMLInputElement
    if (input) input.focus()
  }
}

onMounted(() => {
  window.addEventListener('keydown', onKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeyDown)
})
</script>

<style scoped>
.app-header {
  height: 60px;
  background-color: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1.5rem;
  z-index: 10;
}

.left-section, .right-section {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.logo-area {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 700;
  font-size: 1.1rem;
  color: var(--accent-gold);
}

.logo-icon {
  width: 1.5rem;
  height: 1.5rem;
}

.world-selector {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  background-color: var(--bg-main);
  border: 1px solid var(--border-color);
  padding: 0.35rem 0.6rem;
  border-radius: 0.375rem;
}

.world-icon {
  width: 1rem;
  height: 1rem;
  color: var(--text-muted);
}

.world-dropdown {
  background: transparent;
  border: none;
  color: var(--text-main);
  font-size: 0.9rem;
  font-weight: 500;
  outline: none;
  cursor: pointer;
}

.world-dropdown option {
  background-color: var(--bg-card);
  color: var(--text-main);
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 0.6rem;
  width: 1rem;
  height: 1rem;
  color: var(--text-muted);
}

.search-input {
  background-color: var(--bg-main);
  border: 1px solid var(--border-color);
  color: var(--text-main);
  padding: 0.35rem 0.6rem 0.35rem 2rem;
  border-radius: 0.375rem;
  font-size: 0.85rem;
  width: 220px;
  outline: none;
  transition: all 0.2s ease;
}

.search-input:focus {
  width: 280px;
  border-color: var(--accent-gold);
}

.dice-btn {
  background-color: rgba(212, 175, 55, 0.1);
  border: 1px solid var(--accent-gold);
  color: var(--accent-gold);
  padding: 0.35rem 0.75rem;
  border-radius: 0.375rem;
  font-weight: 600;
  font-size: 0.85rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  transition: all 0.2s ease;
}

.dice-btn:hover {
  background-color: var(--accent-gold);
  color: #000;
}

.dice-icon {
  width: 1.1rem;
  height: 1.1rem;
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.username {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--text-main);
}

.logout-btn {
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  padding: 0.2rem;
  transition: color 0.2s ease;
}

.logout-btn:hover {
  color: var(--fow-nula);
}

.logout-icon {
  width: 1.2rem;
  height: 1.2rem;
}
</style>
