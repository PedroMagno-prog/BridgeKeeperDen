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
      meta: { public: true },
    },
    {
      path: '/personagens',
      name: 'personagens',
      component: () => import('@/views/PersonagensView.vue'),
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

  // Rota pública: usuário já logado → redireciona para personagens
  if (to.meta.public && auth.isLoggedIn) {
    return { name: 'personagens' }
  }
})

export default router
