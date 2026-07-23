<script setup lang="ts">
import { ref } from 'vue'
import { usePersonagensStore } from '@/stores/personagens'

const props = defineProps<{
  classes: string[]
  racas: string[]
}>()

const emit = defineEmits<{
  submit: [payload: { nome: string; classe: string; raca: string }]
}>()

const personagensStore = usePersonagensStore()

const nome = ref('')
const classe = ref('')
const raca = ref('')
const errors = ref({ nome: '', classe: '', raca: '' })

function validate(): boolean {
  errors.value = { nome: '', classe: '', raca: '' }
  let ok = true
  if (!nome.value.trim()) { errors.value.nome = 'Informe o nome do personagem.'; ok = false }
  if (!classe.value) { errors.value.classe = 'Selecione uma classe.'; ok = false }
  if (!raca.value) { errors.value.raca = 'Selecione uma raça.'; ok = false }
  return ok
}

async function handleSubmit() {
  if (!validate()) return
  try {
    await personagensStore.criarPersonagem({
      nome: nome.value.trim(),
      classe: classe.value,
      raca: raca.value,
    })
    nome.value = ''
    classe.value = ''
    raca.value = ''
  } catch { /* erro exibido pelo parent */ }
}
</script>

<template>
  <form id="form-personagem" class="pform" novalidate @submit.prevent="handleSubmit">
    <div class="pform__header">
      <span class="pform__icon">⚔</span>
      <div>
        <h2 class="pform__title">Novo Personagem</h2>
        <p class="pform__subtitle">Preencha os dados do seu herói</p>
      </div>
    </div>

    <!-- Erro da store -->
    <Transition name="fade">
      <div v-if="personagensStore.error" class="pform__api-error" role="alert">
        <span>⚠</span> {{ personagensStore.error }}
      </div>
    </Transition>

    <div class="pform__fields">
      <!-- Nome -->
      <div class="field">
        <label for="pform-nome" class="field__label">Nome do Personagem</label>
        <input
          id="pform-nome"
          v-model="nome"
          class="field__input"
          :class="{ 'field__input--error': errors.nome }"
          type="text"
          placeholder="Ex: Arathorn, o Destemido"
          maxlength="150"
        />
        <span v-if="errors.nome" class="field__error">⚠ {{ errors.nome }}</span>
      </div>

      <!-- Classe -->
      <div class="field">
        <label for="pform-classe" class="field__label">Classe</label>
        <div class="select-wrapper">
          <select
            id="pform-classe"
            v-model="classe"
            class="field__select"
            :class="{ 'field__input--error': errors.classe }"
          >
            <option value="" disabled>Selecione uma classe…</option>
            <option v-for="c in classes" :key="c" :value="c">{{ c }}</option>
          </select>
          <span class="select-arrow">▾</span>
        </div>
        <span v-if="errors.classe" class="field__error">⚠ {{ errors.classe }}</span>
      </div>

      <!-- Raça -->
      <div class="field">
        <label for="pform-raca" class="field__label">Raça</label>
        <div class="select-wrapper">
          <select
            id="pform-raca"
            v-model="raca"
            class="field__select"
            :class="{ 'field__input--error': errors.raca }"
          >
            <option value="" disabled>Selecione uma raça…</option>
            <option v-for="r in racas" :key="r" :value="r">{{ r }}</option>
          </select>
          <span class="select-arrow">▾</span>
        </div>
        <span v-if="errors.raca" class="field__error">⚠ {{ errors.raca }}</span>
      </div>
    </div>

    <button
      id="btn-criar-personagem"
      type="submit"
      class="pform__submit"
      :class="{ 'pform__submit--loading': personagensStore.saving }"
      :disabled="personagensStore.saving"
    >
      <span v-if="personagensStore.saving" class="spinner" />
      <span>{{ personagensStore.saving ? 'Criando…' : 'Criar Personagem' }}</span>
    </button>
  </form>
</template>

<style scoped>
.pform {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-8);
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
  box-shadow: var(--shadow-md);
}

.pform__header {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding-bottom: var(--space-5);
  border-bottom: 1px solid var(--color-border);
}

.pform__icon {
  font-size: 1.8rem;
  filter: drop-shadow(0 0 10px rgba(201, 168, 76, 0.5));
}

.pform__title {
  font-family: var(--font-display);
  font-size: 1.2rem;
  color: var(--color-text);
  margin-bottom: 2px;
}

.pform__subtitle {
  font-size: 0.8rem;
  color: var(--color-text-dim);
}

.pform__api-error {
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

.pform__fields {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

/* Campos reutilizados localmente */
.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field__label {
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--color-text-muted);
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.field__input,
.field__select {
  width: 100%;
  padding: 0.65rem 0.9rem;
  background: var(--color-surface-2);
  border: 1.5px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text);
  font-family: var(--font-body);
  font-size: 0.95rem;
  outline: none;
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
  appearance: none;
}

.field__input:focus,
.field__select:focus {
  border-color: var(--color-gold);
  box-shadow: 0 0 0 3px var(--color-gold-glow);
}

.field__input--error {
  border-color: var(--color-danger) !important;
  box-shadow: 0 0 0 3px var(--color-danger-dim) !important;
}

.field__error {
  font-size: 0.78rem;
  color: var(--color-danger);
}

/* Select wrapper com seta customizada */
.select-wrapper {
  position: relative;
}

.select-arrow {
  position: absolute;
  right: 0.9rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-gold-dim);
  pointer-events: none;
  font-size: 0.8rem;
}

.field__select option {
  background: var(--color-surface-3);
}

/* Botão submit */
.pform__submit {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  width: 100%;
  padding: 0.75rem;
  background: linear-gradient(135deg, var(--color-gold) 0%, var(--color-gold-light) 100%);
  color: #1a1400;
  font-family: var(--font-body);
  font-size: 0.92rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: box-shadow var(--transition-fast), transform var(--transition-fast), opacity var(--transition-fast);
}

.pform__submit:hover:not(:disabled) {
  box-shadow: 0 0 20px var(--color-gold-glow), 0 2px 10px rgba(0, 0, 0, 0.4);
}

.pform__submit:active:not(:disabled) {
  transform: translateY(1px);
}

.pform__submit:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }
</style>
