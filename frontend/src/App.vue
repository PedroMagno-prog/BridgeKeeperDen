<template>
  <div class="app-layout" v-if="authStore.token && route.path !== '/login'">
    <AppHeader @toggle-dice="showDiceRoller = !showDiceRoller" />
    <div class="app-body">
      <AppSidebar />
      <main class="main-workspace">
        <router-view />
      </main>
    </div>
    <GlobalDiceRoller :initial-open="showDiceRoller" />
  </div>

  <div class="login-layout" v-else>
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth'
import { useWorldStore } from './stores/world'
import AppHeader from './components/layout/AppHeader.vue'
import AppSidebar from './components/layout/AppSidebar.vue'
import GlobalDiceRoller from './components/layout/GlobalDiceRoller.vue'

const authStore = useAuthStore()
const worldStore = useWorldStore()
const route = useRoute()
const showDiceRoller = ref(false)

onMounted(async () => {
  if (authStore.token) {
    await authStore.fetchMe()
    await worldStore.fetchWorlds()
  }
})
</script>

<style scoped>
.app-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-main);
}

.app-body {
  flex-grow: 1;
  display: flex;
  overflow: hidden;
}

.main-workspace {
  flex-grow: 1;
  overflow-y: auto;
  background-color: var(--bg-main);
}

.login-layout {
  min-height: 100vh;
}
</style>
