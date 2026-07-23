<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePersonagensStore } from '@/stores/personagens'
import PersonagemForm from '@/components/personagens/PersonagemForm.vue'
import PersonagemList from '@/components/personagens/PersonagemList.vue'

const router = useRouter()
const auth = useAuthStore()
const personagensStore = usePersonagensStore()

const CLASSES = [
  'Guerreiro', 'Mago', 'Ladino', 'Clérigo', 'Druida',
  'Arqueiro', 'Paladino', 'Bardo', 'Monge', 'Necromante',
]

const RACAS = [
  'Humano', 'Elfo', 'Elfo Sombrio', 'Anão', 'Halfling',
  'Gnomo', 'Semi-Orc', 'Tiefling', 'Draconato', 'Aasimar',
]

const limiteAtingido = computed(() => personagensStore.lista.length >= 5)

onMounted(async () => {
  await personagensStore.fetchPersonagens()
})

function logout() {
  auth.logout()
  personagensStore.reset()
  router.push('/login')
}
</script>

<template>
  <div class="pg-wrapper">
    <!-- ── Navbar ── -->
    <header class="navbar">
      <div class="navbar__brand">
        <span class="navbar__crest">⚔</span>
        <span class="navbar__name">BridgeKeeper</span>
      </div>
      <div class="navbar__user">
        <span class="navbar__greeting">Olá, {{ auth.usuario?.nome ?? '…' }}</span>
        <button id="btn-logout" class="navbar__logout" type="button" @click="logout">
          Sair
        </button>
      </div>
    </header>

    <!-- ── Conteúdo ── -->
    <main class="pg-main">
      <!-- Loading inicial -->
      <Transition name="fade">
        <div v-if="personagensStore.loading" class="pg-loading">
          <div class="pg-spinner" />
          <p>Carregando personagens…</p>
        </div>
      </Transition>

      <Transition name="slide-up">
        <div v-if="!personagensStore.loading" class="pg-content">

          <!-- Formulário de criação (oculto quando limite atingido) -->
          <Transition name="fade">
            <PersonagemForm
              v-if="!limiteAtingido"
              :classes="CLASSES"
              :racas="RACAS"
            />
          </Transition>

          <!-- Aviso de limite no lugar do form -->
          <Transition name="fade">
            <div v-if="limiteAtingido" class="pg-limit-banner">
              <span>⚠</span>
              <span>Limite de 5 personagens atingido. Edite ou exclua um para liberar espaço.</span>
            </div>
          </Transition>

          <!-- Divisor -->
          <div class="ornament-divider">Seus Aventureiros</div>

          <!-- Listagem com CRUD -->
          <PersonagemList
            :personagens="personagensStore.lista"
            :classes="CLASSES"
            :racas="RACAS"
          />
        </div>
      </Transition>
    </main>
  </div>
</template>

<style scoped>
.pg-wrapper {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--color-bg);
  background-image:
    radial-gradient(ellipse at 10% 0%, rgba(201, 168, 76, 0.05) 0%, transparent 40%),
    radial-gradient(ellipse at 90% 100%, rgba(74, 80, 128, 0.07) 0%, transparent 40%);
}

/* ── Navbar ── */
.navbar {
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4) var(--space-8);
  background: rgba(20, 23, 32, 0.88);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--color-border);
}

.navbar__brand { display: flex; align-items: center; gap: var(--space-3); }

.navbar__crest {
  font-size: 1.3rem;
  filter: drop-shadow(0 0 8px rgba(201, 168, 76, 0.5));
}

.navbar__name {
  font-family: var(--font-display);
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--color-gold);
  letter-spacing: 0.04em;
}

.navbar__user { display: flex; align-items: center; gap: var(--space-4); }

.navbar__greeting {
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

.navbar__logout {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--color-text-dim);
  background: none;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 4px 12px;
  cursor: pointer;
  transition: color var(--transition-fast), border-color var(--transition-fast);
}
.navbar__logout:hover {
  color: var(--color-danger);
  border-color: var(--color-danger);
}

/* ── Main ── */
.pg-main {
  flex: 1;
  max-width: 900px;
  width: 100%;
  margin: 0 auto;
  padding: var(--space-10) var(--space-6);
}

/* ── Loading ── */
.pg-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-4);
  padding: var(--space-16);
  color: var(--color-text-muted);
  font-size: 0.9rem;
}

.pg-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-gold);
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Content ── */
.pg-content { display: flex; flex-direction: column; gap: 0; }

/* ── Banner de limite ── */
.pg-limit-banner {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  background: rgba(201, 168, 76, 0.07);
  border: 1px solid var(--color-gold-dim);
  border-radius: var(--radius-md);
  color: var(--color-gold);
  font-size: 0.88rem;
  font-weight: 500;
}
</style>
