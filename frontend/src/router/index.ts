import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/login',
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true, fullscreen: true },
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('@/views/DashboardView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/codex',
      name: 'codex',
      component: () => import('@/views/CodexView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/codex/:id',
      name: 'codex-detail',
      component: () => import('@/views/CodexView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/maps',
      name: 'maps',
      component: () => import('@/views/MapsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/timeline',
      name: 'timeline',
      component: () => import('@/views/TimelineView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/manuscripts',
      name: 'manuscripts',
      component: () => import('@/views/ManuscriptsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/inventario',
      name: 'inventario',
      component: () => import('@/views/InventarioView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/quests',
      name: 'quests',
      component: () => import('@/views/QuestJournalView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/graph',
      name: 'graph',
      component: () => import('@/views/GraphView.vue'),
      meta: { requiresAuth: true },
    },
  ],
})

// ── Navigation Guard ──────────────────────────────────────────────────────
router.beforeEach(async (to) => {
  const auth = useAuthStore()

  // Rota protegida: usuário não autenticado → redireciona para login
  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    // Tenta recarregar o usuário do token persistido antes de redirecionar
    await auth.fetchMe()
    if (!auth.isLoggedIn) return { name: 'login' }
  }

  // Rota pública: usuário já logado → redireciona para dashboard
  if (to.meta.public && auth.isLoggedIn) {
    return { name: 'dashboard' }
  }
})

export default router
