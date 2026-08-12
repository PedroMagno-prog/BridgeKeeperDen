<script setup lang="ts">
/**
 * Modal de Gerenciamento de Membros e Convites do Mundo (MembersModal.vue).
 */
import { ref, computed, watch } from 'vue'
import { useWorldsStore, type WorldMemberDetail } from '@/stores/worlds'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/api/client'

const props = defineProps<{
  show: boolean
  worldId: string
  isMestre: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const worldsStore = useWorldsStore()
const authStore = useAuthStore()

const activeTab = ref<'link' | 'members' | 'direct'>('link')
const copied = ref(false)
const searchInput = ref('')
const userResults = ref<Array<{ id: string; username: string; email: string }>>([])
const directRole = ref<'MESTRE' | 'JOGADOR'>('JOGADOR')
const loading = ref(false)

const currentWorld = computed(() => {
  return worldsStore.worlds.find((w) => w.id === props.worldId) || worldsStore.activeWorld
})

const inviteUrl = computed(() => {
  const code = currentWorld.value?.invite_code || ''
  return `${window.location.origin}/join/${code}`
})

watch(
  () => [props.show, props.worldId],
  async ([show, worldId]) => {
    if (show && worldId) {
      loading.value = true
      try {
        await worldsStore.fetchMembers(worldId as string)
      } finally {
        loading.value = false
      }
    }
  },
  { immediate: true }
)

function copyLink() {
  navigator.clipboard.writeText(inviteUrl.value)
  copied.value = true
  setTimeout(() => (copied.value = false), 2500)
}

async function handleRotateLink() {
  if (confirm('Deseja gerar um novo link de convite? O link antigo deixará de funcionar imediatamente.')) {
    await worldsStore.rotateInviteCode(props.worldId)
  }
}

async function handleRoleChange(userId: string, newRole: 'MESTRE' | 'JOGADOR') {
  try {
    await worldsStore.updateMemberRole(props.worldId, userId, newRole)
  } catch (err: any) {
    alert(err?.response?.data?.detail || 'Erro ao alterar papel.')
  }
}

async function handleRemoveMember(member: WorldMemberDetail) {
  const isSelf = member.user_id === authStore.user?.id
  const msg = isSelf
    ? 'Tem certeza que deseja sair deste mundo?'
    : `Expulsar o usuário "${member.username}" do mundo?`

  if (confirm(msg)) {
    try {
      await worldsStore.removeMember(props.worldId, member.user_id)
      if (isSelf) {
        emit('close')
        worldsStore.fetchWorlds()
      }
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Erro ao remover membro.')
    }
  }
}

async function searchUsers() {
  if (!searchInput.value.trim()) {
    userResults.value = []
    return
  }
  try {
    const { data } = await api.get('/users/search', { params: { q: searchInput.value.trim() } })
    userResults.value = data
  } catch (e) {
    userResults.value = []
  }
}

async function addDirect(userStr: string) {
  try {
    await worldsStore.addMemberDirect(props.worldId, userStr, directRole.value)
    searchInput.value = ''
    userResults.value = []
    activeTab.value = 'members'
  } catch (err: any) {
    alert(err?.response?.data?.detail || 'Erro ao adicionar membro.')
  }
}
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="show" class="modal-overlay" @click.self="emit('close')">
        <div class="modal modal--wide">
          <!-- Header -->
          <div class="modal-header">
            <div>
              <h3 class="modal-title">👥 Gestão de Membros & Convites</h3>
              <p class="modal-sub">{{ currentWorld?.name }}</p>
            </div>
            <button class="btn-close" @click="emit('close')">✕</button>
          </div>

          <!-- Abas -->
          <div class="tabs-bar">
            <button
              class="tab-btn"
              :class="{ 'tab-btn--active': activeTab === 'link' }"
              @click="activeTab = 'link'"
            >
              🔗 Link de Convite
            </button>
            <button
              class="tab-btn"
              :class="{ 'tab-btn--active': activeTab === 'members' }"
              @click="activeTab = 'members'"
            >
              👥 Membros ({{ worldsStore.members.length }})
            </button>
            <button
              v-if="isMestre"
              class="tab-btn"
              :class="{ 'tab-btn--active': activeTab === 'direct' }"
              @click="activeTab = 'direct'"
            >
              ➕ Convite Direto
            </button>
          </div>

          <!-- Aba 1: Link de Convite -->
          <div v-if="activeTab === 'link'" class="tab-content">
            <div class="invite-box">
              <label class="field-label">Link de Convite Rápido (/join/:code)</label>
              <div class="link-input-group">
                <input type="text" readonly :value="inviteUrl" class="form-input link-input" />
                <button class="btn btn-gold" @click="copyLink">
                  {{ copied ? '✓ Copiado!' : '📋 Copiar Link' }}
                </button>
              </div>
              <p class="field-hint">
                Compartilhe este link com seus jogadores. Qualquer pessoa com a URL poderá se juntar a esta campanha.
              </p>
            </div>

            <div v-if="isMestre" class="rotate-box">
              <div class="rotate-text">
                <span class="rotate-title">Revogar e Gerar Novo Link</span>
                <span class="rotate-sub">O código de convite atual deixará de funcionar imediatamente.</span>
              </div>
              <button class="btn btn-ghost btn-danger" @click="handleRotateLink">
                🔄 Rotacionar Link
              </button>
            </div>
          </div>

          <!-- Aba 2: Membros Atuais -->
          <div v-else-if="activeTab === 'members'" class="tab-content">
            <div v-if="loading" class="list-empty">Carregando membros...</div>
            <div v-else-if="worldsStore.members.length === 0" class="list-empty">Nenhum membro encontrado.</div>

            <div v-else class="members-table">
              <div v-for="m in worldsStore.members" :key="m.id" class="member-row">
                <div class="member-info">
                  <div class="avatar">{{ m.username.substring(0, 2).toUpperCase() }}</div>
                  <div>
                    <span class="member-name">{{ m.username }}</span>
                    <span class="member-email">{{ m.email }}</span>
                  </div>
                </div>

                <div class="member-actions">
                  <!-- Mestre pode alterar role -->
                  <select
                    v-if="isMestre && m.user_id !== currentWorld?.owner_id"
                    :value="m.role"
                    class="role-select"
                    @change="(e) => handleRoleChange(m.user_id, (e.target as HTMLSelectElement).value as any)"
                  >
                    <option value="MESTRE">MESTRE</option>
                    <option value="JOGADOR">JOGADOR</option>
                  </select>

                  <span v-else class="role-badge" :class="m.role === 'MESTRE' ? 'role-gold' : 'role-silver'">
                    {{ m.role }}
                  </span>

                  <!-- Botão de Expulsão / Saída -->
                  <button
                    v-if="m.user_id !== currentWorld?.owner_id && (isMestre || m.user_id === authStore.user?.id)"
                    class="btn-icon btn-danger"
                    :title="m.user_id === authStore.user?.id ? 'Sair do Mundo' : 'Expulsar Membro'"
                    @click="handleRemoveMember(m)"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Aba 3: Convite Direto -->
          <div v-else-if="activeTab === 'direct'" class="tab-content">
            <div class="form-group">
              <label class="field-label">Buscar Usuário por Username ou E-mail</label>
              <div class="search-user-row">
                <input
                  v-model="searchInput"
                  type="text"
                  class="form-input flex-1"
                  placeholder="Digite o e-mail ou username..."
                  @input="searchUsers"
                />
                <select v-model="directRole" class="form-input role-input">
                  <option value="JOGADOR">Como JOGADOR</option>
                  <option value="MESTRE">Como MESTRE</option>
                </select>
              </div>
            </div>

            <div v-if="userResults.length > 0" class="results-list">
              <div v-for="u in userResults" :key="u.id" class="user-result-row">
                <div>
                  <span class="user-name">{{ u.username }}</span>
                  <span class="user-email">({{ u.email }})</span>
                </div>
                <button class="btn btn-sm btn-gold" @click="addDirect(u.email)">
                  + Adicionar
                </button>
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div class="modal-footer">
            <button class="btn btn-ghost" @click="emit('close')">Fechar</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  z-index: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(4px);
}

.modal {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-6);
  width: 100%;
  max-width: 520px;
  box-shadow: var(--shadow-lg);
}

.modal--wide {
  max-width: 580px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
}

.modal-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-gold);
  margin: 0;
}

.modal-sub {
  font-size: 0.8rem;
  color: var(--color-text-dim);
}

.btn-close {
  background: none;
  border: none;
  color: var(--color-text-dim);
  cursor: pointer;
  font-size: 1rem;
}

.tabs-bar {
  display: flex;
  border-bottom: 1px solid var(--color-border);
  margin-bottom: var(--space-4);
}

.tab-btn {
  padding: 8px 14px;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--color-text-muted);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
}

.tab-btn:hover { color: var(--color-gold); }
.tab-btn--active { color: var(--color-gold); border-bottom-color: var(--color-gold); font-weight: 600; }

.tab-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  min-height: 200px;
}

.field-label {
  font-size: 0.75rem;
  color: var(--color-text-dim);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  display: block;
  margin-bottom: 6px;
}

.link-input-group {
  display: flex;
  gap: 8px;
}

.link-input {
  flex: 1;
  font-family: monospace;
  font-size: 0.8rem;
}

.field-hint {
  font-size: 0.75rem;
  color: var(--color-text-dim);
  margin-top: 6px;
}

.rotate-box {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 12px;
}

.rotate-text { display: flex; flex-direction: column; }
.rotate-title { font-size: 0.85rem; font-weight: 600; color: var(--color-text); }
.rotate-sub { font-size: 0.75rem; color: var(--color-text-dim); }

.members-table {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 260px;
  overflow-y: auto;
}

.member-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
}

.member-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--color-gold-glow);
  color: var(--color-gold);
  font-weight: 700;
  font-size: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.member-name { font-size: 0.85rem; font-weight: 600; color: var(--color-text); display: block; }
.member-email { font-size: 0.7rem; color: var(--color-text-dim); }

.member-actions { display: flex; align-items: center; gap: 8px; }

.role-select {
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-gold);
  font-size: 0.75rem;
  font-weight: 600;
  padding: 4px;
}

.role-badge {
  font-size: 0.65rem;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 10px;
}
.role-gold { background: var(--color-gold-glow); color: var(--color-gold); }
.role-silver { background: rgba(148, 163, 184, 0.1); color: #94A3B8; }

.search-user-row {
  display: flex;
  gap: 8px;
}

.role-input { width: 140px; }

.results-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 160px;
  overflow-y: auto;
}

.user-result-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
}

.user-name { font-size: 0.85rem; font-weight: 600; color: var(--color-gold); margin-right: 6px; }
.user-email { font-size: 0.75rem; color: var(--color-text-dim); }

.modal-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--space-4);
}

.btn {
  padding: 6px 14px;
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
}
.btn-sm { padding: 4px 10px; font-size: 0.75rem; }
.btn-ghost { background: none; color: var(--color-text-muted); border: 1px solid var(--color-border); }
.btn-gold { background: var(--color-gold); color: #111827; }
.btn-danger { color: var(--color-danger); }
.btn-icon { background: none; border: 1px solid var(--color-border); border-radius: var(--radius-sm); cursor: pointer; padding: 2px 6px; }
.list-empty { text-align: center; padding: var(--space-6); color: var(--color-text-dim); font-size: 0.85rem; }
.flex-1 { flex: 1; }
</style>
