<template>
  <aside class="app-sidebar" :class="{ collapsed: isCollapsed }">
    <div class="sidebar-header">
      <button class="toggle-btn" @click="isCollapsed = !isCollapsed" title="Alternar Menu">
        <svg class="toggle-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>
    </div>

    <nav class="nav-menu">
      <router-link
        :to="activeWorldId ? `/worlds/${activeWorldId}/codex` : '/dashboard'"
        class="nav-item"
        active-class="active"
        title="Codex / Artigos"
      >
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
        <span class="nav-label" v-if="!isCollapsed">Codex & Lore</span>
      </router-link>

      <router-link
        :to="activeWorldId ? `/worlds/${activeWorldId}/maps` : '/dashboard'"
        class="nav-item"
        active-class="active"
        title="Mapas Interativos"
      >
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
        </svg>
        <span class="nav-label" v-if="!isCollapsed">Mapas Interativos</span>
      </router-link>

      <router-link
        :to="activeWorldId ? `/worlds/${activeWorldId}/timeline` : '/dashboard'"
        class="nav-item"
        active-class="active"
        title="Linha do Tempo"
      >
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span class="nav-label" v-if="!isCollapsed">Linha do Tempo</span>
      </router-link>

      <router-link
        :to="activeWorldId ? `/worlds/${activeWorldId}/manuscripts` : '/dashboard'"
        class="nav-item"
        active-class="active"
        title="Manuscritos & Diário"
      >
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
        </svg>
        <span class="nav-label" v-if="!isCollapsed">Manuscritos</span>
      </router-link>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useWorldStore } from '../../stores/world'

const worldStore = useWorldStore()
const isCollapsed = ref(false)
const activeWorldId = computed(() => worldStore.activeWorldId)
</script>

<style scoped>
.app-sidebar {
  width: 220px;
  background-color: var(--bg-card);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  transition: width 0.25s ease;

  &.collapsed {
    width: 64px;
  }
}

.sidebar-header {
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 0 0.8rem;
}

.toggle-btn {
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 0.3rem;
  border-radius: 0.25rem;
  transition: color 0.2s ease;
}

.toggle-btn:hover {
  color: var(--accent-gold);
}

.toggle-icon {
  width: 1.25rem;
  height: 1.25rem;
}

.nav-menu {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.5rem;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.65rem 0.8rem;
  border-radius: 0.375rem;
  color: var(--text-muted);
  text-decoration: none;
  font-weight: 500;
  font-size: 0.9rem;
  transition: all 0.2s ease;
}

.nav-item:hover {
  background-color: var(--bg-hover);
  color: var(--text-main);
}

.nav-item.active {
  background-color: rgba(212, 175, 55, 0.15);
  color: var(--accent-gold);
  border-left: 3px solid var(--accent-gold);
}

.nav-icon {
  width: 1.25rem;
  height: 1.25rem;
  flex-shrink: 0;
}

.nav-label {
  white-space: nowrap;
}
</style>
