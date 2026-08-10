<script setup lang="ts">
/**
 * Widget Global: Rolador de Dados Simplificado
 * Painel gaveta (drawer) no canto inferior direito.
 */
import { ref, computed } from 'vue'

const isOpen = ref(false)
const selectedDie = ref(20)
const modifier = ref(0)
const rolling = ref(false)

interface RollResult {
  die: number
  natural: number
  modifier: number
  total: number
}

const history = ref<RollResult[]>([])
const lastResult = ref<RollResult | null>(null)

const dice = [4, 6, 8, 10, 12, 20, 100]

function selectDie(d: number) { selectedDie.value = d }

async function roll() {
  rolling.value = true
  // Simulação de animação
  await new Promise((r) => setTimeout(r, 400))
  const natural = Math.floor(Math.random() * selectedDie.value) + 1
  const result: RollResult = {
    die: selectedDie.value,
    natural,
    modifier: modifier.value,
    total: natural + modifier.value,
  }
  lastResult.value = result
  history.value.unshift(result)
  if (history.value.length > 5) history.value.pop()
  rolling.value = false
}

function formatMod(m: number) {
  if (m === 0) return ''
  return m > 0 ? ` + ${m}` : ` - ${Math.abs(m)}`
}

function formatResult(r: RollResult) {
  return `1d${r.die}${formatMod(r.modifier)} = ${r.total} [${r.natural}]`
}

const isCrit = computed(() => lastResult.value?.natural === lastResult.value?.die)
const isFail = computed(() => lastResult.value?.natural === 1)
</script>

<template>
  <!-- Toggle Button -->
  <button class="dice-toggle" :class="{ 'dice-toggle--open': isOpen }" @click="isOpen = !isOpen" title="Rolador de Dados">
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
      <rect x="2" y="2" width="20" height="20" rx="4"/>
      <circle cx="8" cy="8" r="1.5" fill="currentColor"/><circle cx="16" cy="8" r="1.5" fill="currentColor"/>
      <circle cx="12" cy="12" r="1.5" fill="currentColor"/>
      <circle cx="8" cy="16" r="1.5" fill="currentColor"/><circle cx="16" cy="16" r="1.5" fill="currentColor"/>
    </svg>
  </button>

  <!-- Drawer -->
  <Transition name="slide-up-drawer">
    <div v-if="isOpen" class="dice-drawer">
      <div class="dice-drawer__header">
        <span class="dice-drawer__title">Rolar Dados</span>
        <button class="dice-close" @click="isOpen = false">×</button>
      </div>

      <!-- Dice Buttons -->
      <div class="dice-grid">
        <button
          v-for="d in dice" :key="d"
          class="die-btn" :class="{ 'die-btn--active': selectedDie === d }"
          @click="selectDie(d)"
        >d{{ d }}</button>
      </div>

      <!-- Modifier -->
      <div class="mod-row">
        <label>Modificador</label>
        <div class="mod-controls">
          <button class="mod-btn" @click="modifier--">−</button>
          <span class="mod-value" :class="{ 'mod-value--positive': modifier > 0, 'mod-value--negative': modifier < 0 }">
            {{ modifier >= 0 ? `+${modifier}` : modifier }}
          </span>
          <button class="mod-btn" @click="modifier++">+</button>
        </div>
      </div>

      <!-- Roll Button -->
      <button class="roll-btn" :class="{ 'roll-btn--rolling': rolling }" @click="roll" :disabled="rolling">
        {{ rolling ? '🎲' : 'Rolar' }} 1d{{ selectedDie }}{{ formatMod(modifier) }}
      </button>

      <!-- Result -->
      <Transition name="fade">
        <div v-if="lastResult" class="result-display" :class="{ 'result--crit': isCrit, 'result--fail': isFail }">
          <span class="result-total">{{ lastResult.total }}</span>
          <span class="result-detail">1d{{ lastResult.die }}{{ formatMod(lastResult.modifier) }} [{{ lastResult.natural }}]</span>
        </div>
      </Transition>

      <!-- History -->
      <div v-if="history.length > 1" class="roll-history">
        <div v-for="(r, i) in history.slice(1)" :key="i" class="history-item">{{ formatResult(r) }}</div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.dice-toggle {
  position: fixed; bottom: var(--space-4); right: var(--space-4);
  width: 44px; height: 44px;
  border-radius: 50%; border: 2px solid var(--color-gold-dim);
  background: var(--color-surface); color: var(--color-gold);
  cursor: pointer; z-index: 200;
  display: flex; align-items: center; justify-content: center;
  box-shadow: var(--shadow-md);
  transition: all 0.25s ease;
}
.dice-toggle:hover { border-color: var(--color-gold); box-shadow: var(--shadow-gold); transform: scale(1.08); }
.dice-toggle--open { background: var(--color-gold); color: #0d0f14; border-color: var(--color-gold); }

.dice-drawer {
  position: fixed; bottom: 64px; right: var(--space-4);
  width: 280px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  z-index: 200;
  padding: var(--space-4);
  display: flex; flex-direction: column; gap: var(--space-3);
}

.dice-drawer__header { display: flex; align-items: center; justify-content: space-between; }
.dice-drawer__title { font-family: var(--font-display); font-size: 0.85rem; color: var(--color-gold); }
.dice-close { background: none; border: none; color: var(--color-text-dim); cursor: pointer; font-size: 1.2rem; }
.dice-close:hover { color: var(--color-text); }

.dice-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; }
.die-btn {
  padding: 6px 0; border-radius: var(--radius-sm);
  border: 1px solid var(--color-border); background: var(--color-bg);
  color: var(--color-text-muted); font-family: var(--font-body);
  font-size: 0.75rem; font-weight: 600; cursor: pointer;
  transition: all var(--transition-fast);
}
.die-btn:hover { border-color: var(--color-gold-dim); color: var(--color-gold); }
.die-btn--active { background: var(--color-gold-glow); border-color: var(--color-gold-dim); color: var(--color-gold); }

.mod-row { display: flex; align-items: center; justify-content: space-between; }
.mod-row label { font-size: 0.7rem; color: var(--color-text-dim); text-transform: uppercase; letter-spacing: 0.06em; }
.mod-controls { display: flex; align-items: center; gap: var(--space-2); }
.mod-btn {
  width: 26px; height: 26px; border-radius: var(--radius-sm);
  border: 1px solid var(--color-border); background: none;
  color: var(--color-text-muted); font-size: 0.9rem; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
}
.mod-btn:hover { border-color: var(--color-gold-dim); color: var(--color-gold); }
.mod-value { font-size: 0.85rem; font-weight: 600; min-width: 36px; text-align: center; }
.mod-value--positive { color: var(--color-success); }
.mod-value--negative { color: var(--color-danger); }

.roll-btn {
  padding: var(--space-3); border-radius: var(--radius-sm);
  border: none; background: var(--color-gold); color: #0d0f14;
  font-family: var(--font-body); font-weight: 700; font-size: 0.85rem;
  cursor: pointer; transition: all 0.2s ease;
}
.roll-btn:hover { background: var(--color-gold-light); box-shadow: var(--shadow-gold); }
.roll-btn--rolling { animation: shake 0.4s ease; }
.roll-btn:disabled { opacity: 0.7; }

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-4px) rotate(-2deg); }
  50% { transform: translateX(4px) rotate(2deg); }
  75% { transform: translateX(-2px) rotate(-1deg); }
}

.result-display {
  text-align: center; padding: var(--space-3);
  background: var(--color-bg); border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}
.result-total { display: block; font-size: 2rem; font-weight: 700; color: var(--color-text); line-height: 1.2; }
.result-detail { font-size: 0.7rem; color: var(--color-text-dim); }
.result--crit { border-color: var(--color-success); }
.result--crit .result-total { color: var(--color-success); text-shadow: 0 0 12px rgba(76,175,132,0.4); }
.result--fail { border-color: var(--color-danger); }
.result--fail .result-total { color: var(--color-danger); text-shadow: 0 0 12px rgba(224,92,92,0.4); }

.roll-history { display: flex; flex-direction: column; gap: 2px; }
.history-item { font-size: 0.7rem; color: var(--color-text-dim); padding: 2px 0; }

/* Transition */
.slide-up-drawer-enter-active { transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1); }
.slide-up-drawer-leave-active { transition: all 0.2s ease; }
.slide-up-drawer-enter-from, .slide-up-drawer-leave-to { opacity: 0; transform: translateY(16px) scale(0.95); }
</style>
