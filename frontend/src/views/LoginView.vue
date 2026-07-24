<template>
  <div class="login-container">
    <div class="login-card card">
      <div class="brand">
        <svg class="brand-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
        <h1>BridgeKeeper Portal</h1>
        <p class="subtitle">Gestão de Lore, Cartografia e Sessões de RPG</p>
      </div>

      <div class="tabs">
        <button class="tab-btn" :class="{ active: isLoginTab }" @click="isLoginTab = true">Entrar</button>
        <button class="tab-btn" :class="{ active: !isLoginTab }" @click="isLoginTab = false">Criar Conta</button>
      </div>

      <form @submit.prevent="handleSubmit" class="form">
        <div class="input-group" v-if="!isLoginTab">
          <label>Nome de Usuário</label>
          <input type="text" v-model="username" class="input-field" placeholder="Ex: MestreGuilherme" required />
        </div>

        <div class="input-group">
          <label>E-mail</label>
          <input type="email" v-model="email" class="input-field" placeholder="seu@email.com" required />
        </div>

        <div class="input-group">
          <label>Senha</label>
          <input type="password" v-model="password" class="input-field" placeholder="••••••••" required />
        </div>

        <p class="error-msg" v-if="errorMessage">{{ errorMessage }}</p>

        <button type="submit" class="btn-primary submit-btn" :disabled="authStore.loading">
          {{ authStore.loading ? 'Carregando...' : (isLoginTab ? 'Acessar Plataforma' : 'Cadastrar Conta') }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const router = useRouter()

const isLoginTab = ref(true)
const username = ref('')
const email = ref('')
const password = ref('')
const errorMessage = ref('')

async function handleSubmit() {
  errorMessage.value = ''
  try {
    if (isLoginTab.value) {
      await authStore.login(email.value, password.value)
    } else {
      await authStore.register(username.value, email.value, password.value)
    }
    router.push('/dashboard')
  } catch (err: any) {
    errorMessage.value = err.message || 'Falha na autenticação.'
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--bg-main);
  padding: 1.5rem;
}

.login-card {
  width: 100%;
  max-width: 400px;
  background-color: var(--bg-card);
  border: 1px solid var(--border-color);
  padding: 2rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.brand {
  text-align: center;

  h1 {
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--accent-gold);
    margin-top: 0.5rem;
  }

  .subtitle {
    font-size: 0.8rem;
    color: var(--text-muted);
  }
}

.brand-icon {
  width: 2.5rem;
  height: 2.5rem;
  color: var(--accent-gold);
}

.tabs {
  display: flex;
  border-bottom: 1px solid var(--border-color);
}

.tab-btn {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--text-muted);
  padding: 0.5rem 0;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  border-bottom: 2px solid transparent;

  &.active {
    color: var(--accent-gold);
    border-bottom-color: var(--accent-gold);
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
    font-size: 0.8rem;
    font-weight: 500;
    color: var(--text-muted);
  }
}

.error-msg {
  font-size: 0.8rem;
  color: var(--fow-nula);
  text-align: center;
}

.submit-btn {
  width: 100%;
  justify-content: center;
  margin-top: 0.5rem;
}
</style>
