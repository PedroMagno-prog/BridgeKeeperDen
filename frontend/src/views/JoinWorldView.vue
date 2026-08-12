<script setup lang="ts">
/**
 * Página de Aceite de Convite de Mundo (/join/:code).
 */
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useWorldsStore } from '@/stores/worlds'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const worldsStore = useWorldsStore()
const authStore = useAuthStore()

const inviteCode = ref(route.params.code as string)
const loading = ref(true)
const joining = ref(false)
const errorMsg = ref<string | null>(null)

onMounted(async () => {
  if (!authStore.isLoggedIn) {
    localStorage.setItem('bk_redirect_after_login', route.fullPath)
    router.push('/login')
    return
  }

  try {
    await worldsStore.fetchInviteInfo(inviteCode.value)
  } catch (err: any) {
    errorMsg.value = err?.response?.data?.detail || 'Código de convite inválido ou expirado.'
  } finally {
    loading.value = false
  }
})

async function handleJoin() {
  joining.value = true
  try {
    const world = await worldsStore.joinWorld(inviteCode.value)
    router.push('/dashboard')
  } catch (err: any) {
    errorMsg.value = err?.response?.data?.detail || 'Erro ao entrar no mundo.'
  } finally {
    joining.value = false
  }
}
</script>

<template>
  <div class="join-world-page">
    <div class="join-card">
      <div class="card-icon">🗺️</div>

      <div v-if="loading" class="loading-state">
        <span>Carregando informações do convite...</span>
      </div>

      <div v-else-if="errorMsg" class="error-state">
        <span class="error-icon">⚠️</span>
        <h3 class="error-title">Convite Inválido</h3>
        <p class="error-sub">{{ errorMsg }}</p>
        <button class="btn btn-gold" @click="router.push('/dashboard')">
          Ir para o Dashboard
        </button>
      </div>

      <div v-else-if="worldsStore.inviteInfo" class="invite-details">
        <span class="invite-label">Você foi convidado para se juntar ao mundo:</span>
        <h2 class="world-title">{{ worldsStore.inviteInfo.world_name }}</h2>
        <p class="world-desc">
          {{ worldsStore.inviteInfo.world_description || 'Campanha e cenário de RPG no BridgeKeeper Portal.' }}
        </p>

        <div class="meta-row">
          <div class="meta-item">
            <span class="meta-label">Mestre Criador:</span>
            <span class="meta-val">👑 {{ worldsStore.inviteInfo.owner_username }}</span>
          </div>

          <div class="meta-item">
            <span class="meta-label">Membros Atuais:</span>
            <span class="meta-val">👥 {{ worldsStore.inviteInfo.members_count }} participantes</span>
          </div>
        </div>

        <button class="btn btn-gold btn-lg" :disabled="joining" @click="handleJoin">
          {{ joining ? 'Entrando no Mundo...' : 'Aceitar Convite & Entrar no Mundo ➔' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.join-world-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg);
  padding: var(--space-4);
}

.join-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.6);
  padding: var(--space-8);
  width: 100%;
  max-width: 480px;
  text-align: center;
}

.card-icon {
  font-size: 3rem;
  margin-bottom: var(--space-4);
}

.invite-label {
  font-size: 0.8rem;
  color: var(--color-text-dim);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.world-title {
  font-family: var(--font-display);
  font-size: 1.6rem;
  color: var(--color-gold);
  margin: 6px 0 12px 0;
}

.world-desc {
  font-size: 0.9rem;
  color: var(--color-text-muted);
  line-height: 1.5;
  margin-bottom: var(--space-6);
}

.meta-row {
  display: flex;
  justify-content: space-around;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 12px;
  margin-bottom: var(--space-6);
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.meta-label {
  font-size: 0.7rem;
  color: var(--color-text-dim);
}

.meta-val {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-text);
}

.btn {
  padding: 10px 20px;
  border-radius: var(--radius-sm);
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
}
.btn-lg { width: 100%; padding: 12px; font-size: 0.95rem; }
.btn-gold { background: var(--color-gold); color: #111827; }
.btn-gold:hover { background: var(--color-gold-light); }

.loading-state, .error-state {
  padding: var(--space-6) 0;
  color: var(--color-text-muted);
}
.error-icon { font-size: 2.5rem; display: block; margin-bottom: 8px; }
.error-title { color: var(--color-danger); margin-bottom: 8px; }
.error-sub { font-size: 0.85rem; color: var(--color-text-dim); margin-bottom: 16px; }
</style>
