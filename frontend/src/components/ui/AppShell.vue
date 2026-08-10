<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from './AppHeader.vue'
import AppSidebar from './AppSidebar.vue'

const route = useRoute()
const isFullscreen = computed(() => route.meta?.fullscreen === true)
</script>

<template>
  <div class="app-shell" :class="{ 'app-shell--fullscreen': isFullscreen }">
    <!-- Sidebar esquerda retrátil -->
    <AppSidebar v-if="!isFullscreen" />

    <!-- Coluna principal -->
    <div class="app-shell__main">
      <AppHeader v-if="!isFullscreen" />
      <main class="app-shell__workspace">
        <slot />
      </main>
    </div>
  </div>
</template>

<style scoped>
.app-shell {
  display: flex;
  min-height: 100vh;
  background: var(--color-bg);
}

.app-shell--fullscreen {
  display: block;
}

.app-shell__main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
}

.app-shell__workspace {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-6) var(--space-8);
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0); }
}

@media (max-width: 768px) {
  .app-shell__workspace {
    padding: var(--space-4);
  }
}
</style>
