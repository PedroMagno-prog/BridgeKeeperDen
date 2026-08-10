<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import BaseInput from '@/components/ui/BaseInput.vue'
import BaseButton from '@/components/ui/BaseButton.vue'

const router = useRouter()
const auth = useAuthStore()

// ── Controle de aba ────────────────────────────────────────────────────────
type Tab = 'login' | 'cadastro'
const activeTab = ref<Tab>('login')

function switchTab(tab: Tab) {
  activeTab.value = tab
  auth.error = null
  clearForms()
}

// ── Formulário de Login ────────────────────────────────────────────────────
const loginEmail = ref('')
const loginSenha = ref('')
const loginErrors = ref({ email: '', senha: '' })

function validateLogin(): boolean {
  loginErrors.value = { email: '', senha: '' }
  let ok = true
  if (!loginEmail.value) { loginErrors.value.email = 'Informe o e-mail.'; ok = false }
  if (!loginSenha.value) { loginErrors.value.senha = 'Informe a senha.'; ok = false }
  return ok
}

async function handleLogin() {
  if (!validateLogin()) return
  try {
    await auth.login(loginEmail.value, loginSenha.value)
    router.push('/dashboard')
  } catch { /* error já está em auth.error */ }
}

// ── Formulário de Cadastro ─────────────────────────────────────────────────
const cadNome = ref('')
const cadEmail = ref('')
const cadSenha = ref('')
const cadSenhaConf = ref('')
const cadErrors = ref({ nome: '', email: '', senha: '', senhaConf: '' })

function validateCadastro(): boolean {
  cadErrors.value = { nome: '', email: '', senha: '', senhaConf: '' }
  let ok = true
  if (!cadNome.value.trim()) { cadErrors.value.nome = 'Informe seu nome.'; ok = false }
  if (!cadEmail.value) { cadErrors.value.email = 'Informe o e-mail.'; ok = false }
  else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(cadEmail.value)) {
    cadErrors.value.email = 'E-mail inválido.'; ok = false
  }
  if (!cadSenha.value) { cadErrors.value.senha = 'Escolha uma senha.'; ok = false }
  else if (cadSenha.value.length < 6) { cadErrors.value.senha = 'Mínimo 6 caracteres.'; ok = false }
  if (cadSenha.value !== cadSenhaConf.value) {
    cadErrors.value.senhaConf = 'As senhas não coincidem.'; ok = false
  }
  return ok
}

async function handleCadastro() {
  if (!validateCadastro()) return
  try {
    await auth.register(cadNome.value.trim(), cadEmail.value, cadSenha.value)
    router.push('/dashboard')
  } catch { /* error já está em auth.error */ }
}

// ── Senha visível ──────────────────────────────────────────────────────────
const showLoginPass = ref(false)
const showCadPass = ref(false)

function clearForms() {
  loginEmail.value = ''; loginSenha.value = ''
  loginErrors.value = { email: '', senha: '' }
  cadNome.value = ''; cadEmail.value = ''; cadSenha.value = ''; cadSenhaConf.value = ''
  cadErrors.value = { nome: '', email: '', senha: '', senhaConf: '' }
}
</script>

<template>
  <div class="auth-page">
    <!-- Painel esquerdo: branding -->
    <aside class="auth-brand">
      <div class="auth-brand__inner">
        <div class="auth-brand__crest">⚔</div>
        <h1 class="auth-brand__title">BridgeKeeper<br /><span>Portal</span></h1>
        <p class="auth-brand__tagline">
          Gerencie seus heróis.<br />Conquiste os reinos.
        </p>
        <ul class="auth-brand__features">
          <li>
            <span class="feature-icon">🛡</span>
            Até 5 personagens por conta
          </li>
          <li>
            <span class="feature-icon">📜</span>
            Classes e raças ilimitadas
          </li>
          <li>
            <span class="feature-icon">🏰</span>
            Sua guilda na palma da mão
          </li>
        </ul>
      </div>
    </aside>

    <!-- Painel direito: formulários -->
    <main class="auth-form-panel">
      <div class="auth-card">
        <!-- Abas -->
        <nav class="auth-tabs" role="tablist">
          <button
            id="tab-login"
            role="tab"
            class="auth-tab"
            :class="{ 'auth-tab--active': activeTab === 'login' }"
            :aria-selected="activeTab === 'login'"
            @click="switchTab('login')"
          >
            Entrar
          </button>
          <button
            id="tab-cadastro"
            role="tab"
            class="auth-tab"
            :class="{ 'auth-tab--active': activeTab === 'cadastro' }"
            :aria-selected="activeTab === 'cadastro'"
            @click="switchTab('cadastro')"
          >
            Criar Conta
          </button>
          <div
            class="auth-tab-indicator"
            :class="{ 'auth-tab-indicator--right': activeTab === 'cadastro' }"
          />
        </nav>

        <!-- Erro da API -->
        <Transition name="fade">
          <div v-if="auth.error" class="auth-api-error" role="alert">
            <span>⚠</span> {{ auth.error }}
          </div>
        </Transition>

        <!-- ── Formulário Login ── -->
        <Transition name="fade" mode="out-in">
          <form
            v-if="activeTab === 'login'"
            id="form-login"
            key="login"
            class="auth-form"
            novalidate
            @submit.prevent="handleLogin"
          >
            <BaseInput
              id="login-email"
              v-model="loginEmail"
              label="E-mail"
              type="email"
              placeholder="seu@email.com"
              :error="loginErrors.email"
            />

            <div class="field-password">
              <BaseInput
                id="login-senha"
                v-model="loginSenha"
                label="Senha"
                :type="showLoginPass ? 'text' : 'password'"
                placeholder="••••••••"
                :error="loginErrors.senha"
              />
              <button
                type="button"
                class="pass-toggle"
                :aria-label="showLoginPass ? 'Ocultar senha' : 'Mostrar senha'"
                @click="showLoginPass = !showLoginPass"
              >
                {{ showLoginPass ? '🙈' : '👁' }}
              </button>
            </div>

            <BaseButton
              id="btn-login"
              type="submit"
              variant="primary"
              full-width
              :loading="auth.loading"
            >
              Entrar no Portal
            </BaseButton>

            <p class="auth-switch-hint">
              Ainda não tem conta?
              <button type="button" class="link-btn" @click="switchTab('cadastro')">
                Criar agora
              </button>
            </p>
          </form>

          <!-- ── Formulário Cadastro ── -->
          <form
            v-else
            id="form-cadastro"
            key="cadastro"
            class="auth-form"
            novalidate
            @submit.prevent="handleCadastro"
          >
            <BaseInput
              id="cad-nome"
              v-model="cadNome"
              label="Nome completo"
              placeholder="Seu nome de aventureiro"
              :error="cadErrors.nome"
            />
            <BaseInput
              id="cad-email"
              v-model="cadEmail"
              label="E-mail"
              type="email"
              placeholder="seu@email.com"
              :error="cadErrors.email"
            />

            <div class="field-password">
              <BaseInput
                id="cad-senha"
                v-model="cadSenha"
                label="Senha"
                :type="showCadPass ? 'text' : 'password'"
                placeholder="Mínimo 6 caracteres"
                :error="cadErrors.senha"
              />
              <button
                type="button"
                class="pass-toggle"
                :aria-label="showCadPass ? 'Ocultar senha' : 'Mostrar senha'"
                @click="showCadPass = !showCadPass"
              >
                {{ showCadPass ? '🙈' : '👁' }}
              </button>
            </div>

            <BaseInput
              id="cad-senha-conf"
              v-model="cadSenhaConf"
              label="Confirmar senha"
              :type="showCadPass ? 'text' : 'password'"
              placeholder="Repita a senha"
              :error="cadErrors.senhaConf"
            />

            <BaseButton
              id="btn-cadastro"
              type="submit"
              variant="primary"
              full-width
              :loading="auth.loading"
            >
              Criar Conta
            </BaseButton>

            <p class="auth-switch-hint">
              Já tem uma conta?
              <button type="button" class="link-btn" @click="switchTab('login')">
                Entrar
              </button>
            </p>
          </form>
        </Transition>
      </div>
    </main>
  </div>
</template>

<style scoped>
/* ── Layout ── */
.auth-page {
  display: flex;
  min-height: 100vh;
}

/* ── Painel esquerdo: branding ── */
.auth-brand {
  flex: 1;
  display: none;
  background:
    linear-gradient(160deg, #1a1c2a 0%, #0d0f14 60%),
    radial-gradient(ellipse at 30% 40%, rgba(201, 168, 76, 0.12) 0%, transparent 60%);
  border-right: 1px solid var(--color-border);
  padding: var(--space-12) var(--space-10);
  align-items: center;
  justify-content: center;
}

@media (min-width: 900px) {
  .auth-brand { display: flex; }
}

.auth-brand__inner {
  max-width: 360px;
}

.auth-brand__crest {
  font-size: 3.5rem;
  margin-bottom: var(--space-4);
  filter: drop-shadow(0 0 20px rgba(201, 168, 76, 0.5));
  animation: float 4s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50%       { transform: translateY(-8px); }
}

.auth-brand__title {
  font-family: var(--font-display);
  font-size: 2.4rem;
  font-weight: 700;
  line-height: 1.15;
  color: var(--color-text);
  margin-bottom: var(--space-3);
}

.auth-brand__title span {
  color: var(--color-gold);
}

.auth-brand__tagline {
  font-size: 1rem;
  color: var(--color-text-muted);
  line-height: 1.7;
  margin-bottom: var(--space-10);
}

.auth-brand__features {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.auth-brand__features li {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  font-size: 0.88rem;
  color: var(--color-text-muted);
}

.feature-icon {
  font-size: 1.1rem;
  width: 28px;
  text-align: center;
}

/* ── Painel direito: form ── */
.auth-form-panel {
  flex: 0 0 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-8) var(--space-4);
  background-color: var(--color-bg);
}

@media (min-width: 900px) {
  .auth-form-panel { flex: 0 0 420px; }
}

.auth-card {
  width: 100%;
  max-width: 400px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-lg);
}

/* ── Abas ── */
.auth-tabs {
  display: flex;
  position: relative;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface-2);
}

.auth-tab {
  flex: 1;
  padding: var(--space-4) var(--space-6);
  background: none;
  border: none;
  color: var(--color-text-muted);
  font-family: var(--font-body);
  font-size: 0.88rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  cursor: pointer;
  transition: color var(--transition-fast);
  position: relative;
  z-index: 1;
}

.auth-tab--active {
  color: var(--color-gold);
}

.auth-tab-indicator {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 50%;
  height: 2px;
  background: var(--color-gold);
  border-radius: 2px 2px 0 0;
  transition: left var(--transition-normal) cubic-bezier(0.34, 1.56, 0.64, 1);
}

.auth-tab-indicator--right {
  left: 50%;
}

/* ── Formulário ── */
.auth-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  padding: var(--space-8);
}

/* ── Erro API ── */
.auth-api-error {
  margin: var(--space-5) var(--space-8) 0;
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-sm);
  background: var(--color-danger-dim);
  border: 1px solid var(--color-danger);
  color: var(--color-danger);
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

/* ── Campo com toggle de senha ── */
.field-password {
  position: relative;
}

.pass-toggle {
  position: absolute;
  right: 0.75rem;
  bottom: 0.6rem;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  color: var(--color-text-dim);
  padding: 2px;
  transition: color var(--transition-fast);
}

.pass-toggle:hover { color: var(--color-gold); }

/* ── Rodapé da form ── */
.auth-switch-hint {
  text-align: center;
  font-size: 0.82rem;
  color: var(--color-text-dim);
}

.link-btn {
  background: none;
  border: none;
  color: var(--color-gold);
  font-size: inherit;
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 3px;
  padding: 0;
  transition: color var(--transition-fast);
}

.link-btn:hover { color: var(--color-gold-light); }
</style>
