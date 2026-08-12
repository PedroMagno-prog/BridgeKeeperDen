<script setup lang="ts">
/**
 * Modal de Importação em Lote de Cofres Obsidian (.zip) (ObsidianImportModal.vue).
 */
import { ref } from 'vue'
import { useArticlesStore } from '@/stores/articles'

const props = defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'imported'): void
}>()

const articlesStore = useArticlesStore()

const selectedFile = ref<File | null>(null)
const useFoldersAsTags = ref(true)
const uploading = ref(false)
const isDragging = ref(false)
const errorMsg = ref<string | null>(null)
const resultMsg = ref<string | null>(null)

function handleFileSelect(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.files && target.files[0]) {
    validateAndSetFile(target.files[0])
  }
}

function handleDrop(e: DragEvent) {
  isDragging.value = false
  if (e.dataTransfer?.files && e.dataTransfer.files[0]) {
    validateAndSetFile(e.dataTransfer.files[0])
  }
}

function validateAndSetFile(file: File) {
  errorMsg.value = null
  resultMsg.value = null
  if (!file.name.toLowerCase().endsWith('.zip')) {
    errorMsg.value = 'Selecione um arquivo comprimido no formato .zip.'
    selectedFile.value = null
    return
  }
  selectedFile.value = file
}

async function handleImport() {
  if (!selectedFile.value) return
  uploading.value = true
  errorMsg.value = null
  resultMsg.value = null

  try {
    const res = await articlesStore.importObsidianVault(selectedFile.value, useFoldersAsTags.value)
    resultMsg.value = res.message
    emit('imported')
    setTimeout(() => {
      resetState()
      emit('close')
    }, 2500)
  } catch (err: any) {
    errorMsg.value = err?.response?.data?.detail || 'Erro ao importar o cofre Obsidian.'
  } finally {
    uploading.value = false
  }
}

function resetState() {
  selectedFile.value = null
  errorMsg.value = null
  resultMsg.value = null
  uploading.value = false
}

function close() {
  resetState()
  emit('close')
}
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="show" class="modal-overlay" @click.self="close">
        <div class="modal modal--import">
          <!-- Header -->
          <div class="modal-header">
            <div>
              <h3 class="modal-title">📥 Importar Cofre Obsidian (.zip)</h3>
              <p class="modal-sub">Converta notas Markdown do Obsidian em Artigos do Codex</p>
            </div>
            <button class="btn-close" @click="close">✕</button>
          </div>

          <!-- Body -->
          <div class="modal-body">
            <!-- Dropzone -->
            <div
              class="dropzone"
              :class="{ 'dropzone--active': isDragging, 'dropzone--has-file': selectedFile }"
              @dragover.prevent="isDragging = true"
              @dragleave.prevent="isDragging = false"
              @drop.prevent="handleDrop"
            >
              <input
                type="file"
                accept=".zip"
                class="file-input"
                id="obsidian-zip-input"
                @change="handleFileSelect"
              />
              <label for="obsidian-zip-input" class="dropzone-label">
                <div class="drop-icon">📦</div>
                <div v-if="selectedFile" class="file-info">
                  <span class="file-name">{{ selectedFile.name }}</span>
                  <span class="file-size">({{ (selectedFile.size / (1024 * 1024)).toFixed(2) }} MB)</span>
                </div>
                <div v-else class="drop-prompt">
                  <span class="prompt-main">Arraste seu arquivo .zip aqui ou <strong>Clique para navegar</strong></span>
                  <span class="prompt-sub">Apenas cofres exportados em formato .zip</span>
                </div>
              </label>
            </div>

            <!-- Painel de Defaults de RPG & Névoa de Guerra -->
            <div class="defaults-card">
              <span class="card-heading">🛡️ Regras & Valores Padrão Aplicados</span>
              <ul class="defaults-list">
                <li>
                  <strong>Névoa de Guerra:</strong> <code>Obscurecimento Total (Visão Nula)</code> — O cofre fica invisível aos jogadores até liberação manual do Mestre.
                </li>
                <li>
                  <strong>Data In-Game:</strong> Vazio por padrão (a menos que presente no YAML Frontmatter como <code>in_game_date</code>).
                </li>
                <li>
                  <strong>Wikilinks <code>[[Artigo]]</code>:</strong> Sintaxe preservada para sincronização automática com o <strong>Graph View</strong> e <strong>Backlinks</strong>.
                </li>
              </ul>
            </div>

            <!-- Opções -->
            <div class="options-box">
              <label class="checkbox-option">
                <input v-model="useFoldersAsTags" type="checkbox" />
                <span>🏷️ Mapear subpastas do cofre em Tags dos artigos (ex: <code>Locais/Cataratas.md</code> ➔ tag <code>.Locais</code>)</span>
              </label>
            </div>

            <!-- Feedback Messages -->
            <div v-if="errorMsg" class="alert alert-error">
              ⚠️ {{ errorMsg }}
            </div>

            <div v-if="resultMsg" class="alert alert-success">
              ✅ {{ resultMsg }}
            </div>
          </div>

          <!-- Footer -->
          <div class="modal-footer">
            <button class="btn btn-ghost" :disabled="uploading" @click="close">Cancelar</button>
            <button
              class="btn btn-gold"
              :disabled="!selectedFile || uploading"
              @click="handleImport"
            >
              <span v-if="uploading" class="spinner">⏳ Importando...</span>
              <span v-else>📥 Importar Cofre</span>
            </button>
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
  background: rgba(0, 0, 0, 0.75);
  z-index: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(4px);
}

.modal--import {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  width: 100%;
  max-width: 560px;
  box-shadow: var(--shadow-lg);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
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
  margin-top: 2px;
}

.btn-close {
  background: none;
  border: none;
  color: var(--color-text-dim);
  cursor: pointer;
  font-size: 1rem;
}

.modal-body {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

/* Dropzone */
.dropzone {
  position: relative;
  border: 2px dashed var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-6);
  text-align: center;
  background: var(--color-bg);
  transition: all var(--transition-fast);
  cursor: pointer;
}

.dropzone:hover, .dropzone--active {
  border-color: var(--color-gold);
  background: var(--color-surface-2);
}

.dropzone--has-file {
  border-style: solid;
  border-color: var(--color-gold-dim);
  background: var(--color-surface-2);
}

.file-input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
  width: 100%;
  height: 100%;
}

.drop-icon {
  font-size: 2.2rem;
  margin-bottom: 6px;
}

.drop-prompt {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.prompt-main {
  font-size: 0.875rem;
  color: var(--color-text);
}

.prompt-sub {
  font-size: 0.75rem;
  color: var(--color-text-dim);
}

.file-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.file-name {
  font-weight: 600;
  color: var(--color-gold);
  font-size: 0.9rem;
}

.file-size {
  font-size: 0.8rem;
  color: var(--color-text-dim);
}

/* Defaults Card */
.defaults-card {
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 12px 14px;
}

.card-heading {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--color-gold);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  display: block;
  margin-bottom: 8px;
}

.defaults-list {
  margin: 0;
  padding-left: 18px;
  font-size: 0.78rem;
  color: var(--color-text-muted);
  line-height: 1.5;
}

.defaults-list code {
  background: rgba(255, 255, 255, 0.06);
  padding: 1px 4px;
  border-radius: 3px;
  color: var(--color-gold-light);
  font-family: monospace;
}

/* Options Box */
.options-box {
  display: flex;
  align-items: center;
}

.checkbox-option {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.8rem;
  color: var(--color-text);
  cursor: pointer;
}

.checkbox-option input {
  accent-color: var(--color-gold);
  cursor: pointer;
}

.checkbox-option code {
  background: rgba(255, 255, 255, 0.06);
  padding: 1px 4px;
  border-radius: 3px;
  color: var(--color-gold-light);
  font-family: monospace;
}

/* Alerts */
.alert {
  padding: 10px 14px;
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  font-weight: 500;
}
.alert-error {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid var(--color-danger);
  color: var(--color-danger);
}
.alert-success {
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid #22c55e;
  color: #22c55e;
}

/* Footer */
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: var(--space-4);
}

.btn {
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
}
.btn-ghost { background: none; color: var(--color-text-muted); border: 1px solid var(--color-border); }
.btn-gold { background: var(--color-gold); color: #111827; }
.btn-gold:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
