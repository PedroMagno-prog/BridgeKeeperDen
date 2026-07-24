import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import DashboardView from '../views/DashboardView.vue'
import CodexView from '../views/CodexView.vue'
import ArticleDetailView from '../views/ArticleDetailView.vue'
import MapView from '../views/MapView.vue'
import TimelineView from '../views/TimelineView.vue'
import ManuscriptsView from '../views/ManuscriptsView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/dashboard',
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: DashboardView,
      meta: { requiresAuth: true },
    },
    {
      path: '/worlds/:worldId/codex',
      name: 'codex',
      component: CodexView,
      meta: { requiresAuth: true },
    },
    {
      path: '/worlds/:worldId/codex/:articleId',
      name: 'article-detail',
      component: ArticleDetailView,
      meta: { requiresAuth: true },
    },
    {
      path: '/worlds/:worldId/maps',
      name: 'maps',
      component: MapView,
      meta: { requiresAuth: true },
    },
    {
      path: '/worlds/:worldId/timeline',
      name: 'timeline',
      component: TimelineView,
      meta: { requiresAuth: true },
    },
    {
      path: '/worlds/:worldId/manuscripts',
      name: 'manuscripts',
      component: ManuscriptsView,
      meta: { requiresAuth: true },
    },
  ],
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router
