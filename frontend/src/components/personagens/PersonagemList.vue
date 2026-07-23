<script setup lang="ts">
import { ref } from 'vue'
import type { Personagem } from '@/stores/personagens'
import { usePersonagensStore } from '@/stores/personagens'

defineProps<{ personagens: Personagem[]; classes: string[]; racas: string[] }>()

const store = usePersonagensStore()

// ── Ícones por classe ──────────────────────────────────────────────────────
const classeIcons: Record<string, string> = {
  Guerreiro: '⚔', Mago: '🔮', Ladino: '🗡', Clérigo: '✝', Druida: '🌿',
  Arqueiro: '🏹', Paladino: '🛡', Bardo: '🎵', Monge: '👊', Necromante: '💀',
}
function iconFor(classe: string) { return classeIcons[classe] ?? '⚜' }

// ── Estado de edição ───────────────────────────────────────────────────────
const editingId = ref<number | null>(null)
const editNome = ref('')
const editClasse = ref('')
const editRaca = ref('')
const editError = ref('')

function abrirEdicao(p: Personagem) {
  editingId.value = p.id
  editNome.value = p.nome
  editClasse.value = p.classe
  editRaca.value = p.raca
  editError.value = ''
}

function cancelarEdicao() {
  editingId.value = null
  editError.value = ''
}

async function salvarEdicao(id: number) {
  if (!editNome.value.trim()) { editError.value = 'O nome não pode ficar em branco.'; return }
  try {
    await store.atualizarPersonagem(id, {
      nome: editNome.value.trim(),
      classe: editClasse.value,
      raca: editRaca.value,
    })
    cancelarEdicao()
  } catch (e: unknown) {
    editError.value = e instanceof Error ? e.message : 'Erro ao salvar.'
  }
}

// ── Delete ─────────────────────────────────────────────────────────────────
async function confirmarDelete(id: number, nome: string) {
  if (window.confirm(`Deseja apagar o personagem "${nome}"? Esta ação não pode ser desfeita.`)) {
    await store.deletarPersonagem(id)
    if (editingId.value === id) cancelarEdicao()
  }
}
</script>

<template>
  <section class="plist" aria-label="Seus personagens">
    <header class="plist__header">
      <h2 class="plist__title">Personagens</h2>
      <span class="plist__badge" :class="{ 'plist__badge--full': personagens.length >= 5 }">
        {{ personagens.length }} / 5
      </span>
    </header>

    <!-- Lista vazia -->
    <Transition name="fade">
      <div v-if="personagens.length === 0" class="plist__empty">
        <span class="plist__empty-icon">🗺</span>
        <p>Nenhum personagem criado ainda.</p>
        <p class="plist__empty-hint">Use o formulário acima para criar seu primeiro herói.</p>
      </div>
    </Transition>

    <!-- Cards -->
    <TransitionGroup name="slide-up" tag="ul" class="plist__grid">
      <li v-for="p in personagens" :key="p.id" class="pcard" :class="{ 'pcard--editing': editingId === p.id }">

        <!-- ── Modo visualização ── -->
        <template v-if="editingId !== p.id">
          <div class="pcard__badge">{{ iconFor(p.classe) }}</div>
          <div class="pcard__body">
            <h3 class="pcard__nome">{{ p.nome }}</h3>
            <div class="pcard__tags">
              <span class="pcard__tag pcard__tag--classe">{{ p.classe }}</span>
              <span class="pcard__tag pcard__tag--raca">{{ p.raca }}</span>
            </div>
          </div>
          <div class="pcard__actions">
            <button
              :id="`btn-edit-${p.id}`"
              type="button"
              class="pcard__btn pcard__btn--edit"
              title="Editar personagem"
              @click="abrirEdicao(p)"
            >✏</button>
            <button
              :id="`btn-del-${p.id}`"
              type="button"
              class="pcard__btn pcard__btn--del"
              title="Excluir personagem"
              @click="confirmarDelete(p.id, p.nome)"
            >✕</button>
          </div>
        </template>

        <!-- ── Modo edição inline ── -->
        <template v-else>
          <div class="pcard__edit-form">
            <div class="pcard__edit-header">
              <span>{{ iconFor(editClasse) }}</span>
              <span class="pcard__edit-title">Editando personagem</span>
            </div>

            <!-- Erro de edição -->
            <p v-if="editError" class="pcard__edit-error">⚠ {{ editError }}</p>

            <div class="pcard__edit-fields">
              <div class="efield">
                <label :for="`edit-nome-${p.id}`" class="efield__label">Nome</label>
                <input
                  :id="`edit-nome-${p.id}`"
                  v-model="editNome"
                  class="efield__input"
                  type="text"
                  maxlength="150"
                />
              </div>
              <div class="efield">
                <label :for="`edit-classe-${p.id}`" class="efield__label">Classe</label>
                <div class="efield__select-wrap">
                  <select :id="`edit-classe-${p.id}`" v-model="editClasse" class="efield__select">
                    <option v-for="c in classes" :key="c" :value="c">{{ c }}</option>
                  </select>
                  <span class="efield__arrow">▾</span>
                </div>
              </div>
              <div class="efield">
                <label :for="`edit-raca-${p.id}`" class="efield__label">Raça</label>
                <div class="efield__select-wrap">
                  <select :id="`edit-raca-${p.id}`" v-model="editRaca" class="efield__select">
                    <option v-for="r in racas" :key="r" :value="r">{{ r }}</option>
                  </select>
                  <span class="efield__arrow">▾</span>
                </div>
              </div>
            </div>

            <div class="pcard__edit-btns">
              <button
                :id="`btn-save-${p.id}`"
                type="button"
                class="pcard__save-btn"
                :disabled="store.saving"
                @click="salvarEdicao(p.id)"
              >
                <span v-if="store.saving" class="mini-spinner" />
                {{ store.saving ? 'Salvando…' : 'Salvar' }}
              </button>
              <button
                :id="`btn-cancel-${p.id}`"
                type="button"
                class="pcard__cancel-btn"
                @click="cancelarEdicao"
              >Cancelar</button>
              <button
                :id="`btn-del-edit-${p.id}`"
                type="button"
                class="pcard__del-btn"
                @click="confirmarDelete(p.id, p.nome)"
              >Excluir</button>
            </div>
          </div>
        </template>
      </li>
    </TransitionGroup>

    <!-- Aviso de limite -->
    <Transition name="fade">
      <p v-if="personagens.length >= 5" class="plist__limit-warning">
        ⚠ Limite de 5 personagens atingido. Exclua um para criar outro.
      </p>
    </Transition>
  </section>
</template>

<style scoped>
/* ── Cabeçalho da lista ── */
.plist { display: flex; flex-direction: column; gap: var(--space-5); }

.plist__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.plist__title {
  font-family: var(--font-display);
  font-size: 1.1rem;
  color: var(--color-text);
}

.plist__badge {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--color-gold);
  background: rgba(201, 168, 76, 0.1);
  border: 1px solid var(--color-gold-dim);
  border-radius: 20px;
  padding: 2px 12px;
  transition: color var(--transition-fast), background var(--transition-fast), border-color var(--transition-fast);
}

.plist__badge--full {
  color: var(--color-danger);
  background: var(--color-danger-dim);
  border-color: var(--color-danger);
}

/* ── Vazio ── */
.plist__empty {
  text-align: center;
  padding: var(--space-12) var(--space-8);
  color: var(--color-text-muted);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
}
.plist__empty-icon { font-size: 2.5rem; margin-bottom: var(--space-2); }
.plist__empty-hint { font-size: 0.82rem; color: var(--color-text-dim); }

/* ── Grid ── */
.plist__grid {
  list-style: none;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: var(--space-4);
}

/* ── Card ── */
.pcard {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-4) var(--space-5);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
  display: flex;
  align-items: center;
  gap: var(--space-4);
  position: relative;
}

.pcard:hover:not(.pcard--editing) {
  border-color: var(--color-gold-dim);
  box-shadow: 0 0 14px rgba(201, 168, 76, 0.1);
}

.pcard--editing {
  border-color: var(--color-gold-dim);
  box-shadow: var(--shadow-gold);
  align-items: stretch;
  flex-direction: column;
  gap: 0;
  padding: 0;
}

.pcard__badge {
  font-size: 1.6rem;
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-surface-3);
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
}

.pcard__body { flex: 1; min-width: 0; }

.pcard__nome {
  font-family: var(--font-display);
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: var(--space-2);
}

.pcard__tags { display: flex; flex-wrap: wrap; gap: var(--space-1); }

.pcard__tag {
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  padding: 2px 8px;
  border-radius: 20px;
}
.pcard__tag--classe {
  background: rgba(201, 168, 76, 0.1);
  color: var(--color-gold);
  border: 1px solid var(--color-gold-dim);
}
.pcard__tag--raca {
  background: rgba(74, 80, 128, 0.2);
  color: #8899cc;
  border: 1px solid #2e3350;
}

/* ── Ações do card ── */
.pcard__actions {
  display: flex;
  gap: var(--space-1);
  opacity: 0;
  transition: opacity var(--transition-fast);
}
.pcard:hover .pcard__actions { opacity: 1; }

.pcard__btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  cursor: pointer;
  color: var(--color-text-dim);
  transition: color var(--transition-fast), background var(--transition-fast), border-color var(--transition-fast);
}
.pcard__btn--edit:hover {
  color: var(--color-gold);
  border-color: var(--color-gold-dim);
  background: rgba(201, 168, 76, 0.08);
}
.pcard__btn--del:hover {
  color: var(--color-danger);
  border-color: var(--color-danger);
  background: var(--color-danger-dim);
}

/* ── Formulário de edição inline ── */
.pcard__edit-form {
  padding: var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.pcard__edit-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 1rem;
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--color-border);
}

.pcard__edit-title {
  font-family: var(--font-display);
  font-size: 0.85rem;
  color: var(--color-gold);
}

.pcard__edit-error {
  font-size: 0.8rem;
  color: var(--color-danger);
  background: var(--color-danger-dim);
  border: 1px solid var(--color-danger);
  border-radius: var(--radius-sm);
  padding: var(--space-2) var(--space-3);
}

.pcard__edit-fields { display: flex; flex-direction: column; gap: var(--space-3); }

/* Campos de edição */
.efield { display: flex; flex-direction: column; gap: 4px; }
.efield__label {
  font-size: 0.72rem;
  font-weight: 500;
  color: var(--color-text-dim);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.efield__input,
.efield__select {
  width: 100%;
  padding: 0.5rem 0.75rem;
  background: var(--color-surface-2);
  border: 1.5px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text);
  font-family: var(--font-body);
  font-size: 0.88rem;
  outline: none;
  appearance: none;
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}
.efield__input:focus,
.efield__select:focus {
  border-color: var(--color-gold);
  box-shadow: 0 0 0 2px var(--color-gold-glow);
}
.efield__select-wrap { position: relative; }
.efield__arrow {
  position: absolute;
  right: 0.7rem;
  top: 50%;
  transform: translateY(-50%);
  pointer-events: none;
  font-size: 0.75rem;
  color: var(--color-gold-dim);
}

/* Botões de edição */
.pcard__edit-btns {
  display: flex;
  gap: var(--space-2);
  padding-top: var(--space-2);
  border-top: 1px solid var(--color-border);
}

.pcard__save-btn {
  flex: 1;
  padding: 0.5rem;
  background: linear-gradient(135deg, var(--color-gold), var(--color-gold-light));
  color: #1a1400;
  font-family: var(--font-body);
  font-size: 0.82rem;
  font-weight: 700;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  transition: box-shadow var(--transition-fast), opacity var(--transition-fast);
}
.pcard__save-btn:hover:not(:disabled) {
  box-shadow: 0 0 14px var(--color-gold-glow);
}
.pcard__save-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.pcard__cancel-btn {
  padding: 0.5rem 0.85rem;
  background: none;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text-muted);
  font-size: 0.82rem;
  cursor: pointer;
  transition: border-color var(--transition-fast), color var(--transition-fast);
}
.pcard__cancel-btn:hover {
  border-color: var(--color-border-glow);
  color: var(--color-text);
}

.pcard__del-btn {
  padding: 0.5rem 0.85rem;
  background: none;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-danger);
  font-size: 0.82rem;
  cursor: pointer;
  transition: background var(--transition-fast), border-color var(--transition-fast);
}
.pcard__del-btn:hover {
  background: var(--color-danger-dim);
  border-color: var(--color-danger);
}

/* Mini spinner */
.mini-spinner {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Limit warning */
.plist__limit-warning {
  font-size: 0.82rem;
  color: var(--color-danger);
  padding: var(--space-3) var(--space-4);
  background: var(--color-danger-dim);
  border: 1px solid var(--color-danger);
  border-radius: var(--radius-sm);
}

/* Animações de lista */
.slide-up-enter-active { transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1); }
.slide-up-leave-active { transition: all 0.2s ease; }
.slide-up-enter-from  { opacity: 0; transform: translateY(16px) scale(0.97); }
.slide-up-leave-to    { opacity: 0; transform: scale(0.95); }
</style>
