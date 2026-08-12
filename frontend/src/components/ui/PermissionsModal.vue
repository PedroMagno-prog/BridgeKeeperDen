<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useArticlesStore, type UserPermission, type Visibility } from '@/stores/articles'
import VisibilityBadge from '@/components/ui/VisibilityBadge.vue'

const props = defineProps<{
  articleId: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const articlesStore = useArticlesStore()
const permissions = ref<UserPermission[]>([])
const loading = ref(true)
const saving = ref(false)
const message = ref('')

onMounted(async () => {
  try {
    permissions.value = await articlesStore.fetchPermissions(props.articleId)
  } finally {
    loading.value = false
  }
})

async function handleSave() {
  saving.value = true
  message.value = ''
  try {
    const payload = permissions.value.map((p) => ({
      user_id: p.user_id,
      visibility: p.visibility,
    }))
    await articlesStore.updatePermissions(props.articleId, payload)
    message.value = 'Permissões atualizadas com sucesso!'
    setTimeout(() => {
      emit('close')
    }, 800)
  } catch (err: any) {
    message.value = 'Erro ao salvar permissões.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal modal--wide" @click.stop>
      <h3 class="modal__title">🛡️ Permissões Individuais por Jogador</h3>
      <p class="modal__subtitle">
        Defina o nível de visibilidade que cada jogador terá para este artigo específico.
      </p>

      <div v-if="loading" class="loading-state">Carregando permissões...</div>

      <div v-else class="perm-table-container">
        <table class="perm-table">
          <thead>
            <tr>
              <th>Usuário</th>
              <th>E-mail</th>
              <th>Visibilidade Atribuída</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in permissions" :key="p.user_id">
              <td>
                <strong>{{ p.username }}</strong>
              </td>
              <td class="email-col">{{ p.email }}</td>
              <td>
                <select v-model="p.visibility" class="perm-select">
                  <option value="NULA">🙈 Nula (Invisível)</option>
                  <option value="PARCIAL">🔒 Parcial (Somente Título)</option>
                  <option value="CONTROLADO">👁️ Controlado (Somente Leitura)</option>
                  <option value="TOTAL">📖 Total (Leitura & Edição)</option>
                </select>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="message" class="perm-msg">{{ message }}</div>

      <div class="modal__actions">
        <button class="btn btn--ghost" @click="emit('close')">Fechar</button>
        <button class="btn btn--gold" :disabled="saving || loading" @click="handleSave">
          {{ saving ? 'Salvando...' : 'Salvar Permissões' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal__subtitle {
  color: var(--color-text-dim, #9ca3af);
  font-size: 0.85rem;
  margin-bottom: 1rem;
}
.loading-state {
  padding: 2rem;
  text-align: center;
  color: #9ca3af;
}
.perm-table-container {
  max-height: 350px;
  overflow-y: auto;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  margin-bottom: 1rem;
}
.perm-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}
.perm-table th,
.perm-table td {
  padding: 0.6rem 0.8rem;
  text-align: left;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}
.perm-table th {
  background: rgba(0, 0, 0, 0.3);
  color: var(--color-gold-light, #f3d17c);
  font-weight: 600;
}
.email-col {
  color: #9ca3af;
  font-size: 0.8rem;
}
.perm-select {
  background: #1f2937;
  color: #f3f4f6;
  border: 1px solid #374151;
  border-radius: 4px;
  padding: 0.35rem 0.5rem;
  font-size: 0.825rem;
  width: 100%;
}
.perm-msg {
  color: #10b981;
  font-size: 0.85rem;
  text-align: center;
  margin-bottom: 0.5rem;
}
</style>
