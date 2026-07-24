<template>
  <div class="dice-roller-widget" :class="{ open: isOpen }">
    <div class="widget-header" @click="isOpen = !isOpen">
      <div class="header-title">
        <svg class="dice-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
        </svg>
        <span>Rolador de Dados</span>
      </div>
      <button class="minimize-btn">{{ isOpen ? '▼' : '▲' }}</button>
    </div>

    <div class="widget-body" v-if="isOpen">
      <!-- Seletor do tipo de dado -->
      <div class="dice-selector">
        <button
          v-for="d in diceTypes"
          :key="d"
          class="dice-chip"
          :class="{ selected: selectedDice === d }"
          @click="selectedDice = d"
        >
          d{{ d }}
        </button>
      </div>

      <!-- Modificador & Quantidade -->
      <div class="inputs-row">
        <div class="input-group">
          <label>Qtd:</label>
          <input type="number" min="1" max="20" v-model.number="diceCount" class="num-input" />
        </div>
        <div class="input-group">
          <label>Mod:</label>
          <input type="number" v-model.number="modifier" class="num-input" />
        </div>
      </div>

      <!-- Botão Rolar -->
      <button class="roll-action-btn" @click="rollDice">
        Rolar {{ diceCount }}d{{ selectedDice }}{{ modifier >= 0 ? `+${modifier}` : modifier }}
      </button>

      <!-- Última Rolagem em Destaque -->
      <div class="latest-result" v-if="latestRoll">
        <div class="result-total">{{ latestRoll.total }}</div>
        <div class="result-breakdown">
          [{{ latestRoll.rolls.join(', ') }}] {{ latestRoll.modifier >= 0 ? `+ ${latestRoll.modifier}` : `- ${Math.abs(latestRoll.modifier)}` }}
        </div>
      </div>

      <!-- Histórico (5 últimas) -->
      <div class="history-section" v-if="history.length > 0">
        <div class="history-title">Histórico Recente</div>
        <div class="history-list">
          <div v-for="(h, idx) in history" :key="idx" class="history-item">
            <span>{{ h.count }}d{{ h.dice }}{{ h.modifier >= 0 ? `+${h.modifier}` : h.modifier }}</span>
            <span class="hist-total">{{ h.total }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  initialOpen?: boolean
}>()

const isOpen = ref(props.initialOpen ?? false)
const diceTypes = [4, 6, 8, 10, 12, 20, 100]
const selectedDice = ref(20)
const diceCount = ref(1)
const modifier = ref(0)

interface RollHistory {
  dice: number
  count: number
  modifier: number
  rolls: number[]
  total: number
}

const latestRoll = ref<RollHistory | null>(null)
const history = ref<RollHistory[]>([])

function rollDice() {
  const rolls: number[] = []
  let sum = 0
  for (let i = 0; i < diceCount.value; i++) {
    const roll = Math.floor(Math.random() * selectedDice.value) + 1
    rolls.push(roll)
    sum += roll
  }
  const total = sum + modifier.value
  const resultRecord: RollHistory = {
    dice: selectedDice.value,
    count: diceCount.value,
    modifier: modifier.value,
    rolls,
    total,
  }

  latestRoll.value = resultRecord
  history.value.unshift(resultRecord)
  if (history.value.length > 5) {
    history.value.pop()
  }
}
</script>

<style scoped>
.dice-roller-widget {
  position: fixed;
  bottom: 1.5rem;
  right: 1.5rem;
  width: 280px;
  background-color: var(--bg-card);
  border: 1px solid var(--accent-gold);
  border-radius: 0.5rem;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
  z-index: 100;
  overflow: hidden;
  transition: all 0.3s ease;
}

.widget-header {
  background-color: #162032;
  padding: 0.6rem 0.8rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-weight: 600;
  font-size: 0.9rem;
  color: var(--accent-gold);
}

.dice-svg {
  width: 1.1rem;
  height: 1.1rem;
}

.minimize-btn {
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 0.75rem;
}

.widget-body {
  padding: 0.8rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.dice-selector {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.dice-chip {
  flex: 1 1 28%;
  background-color: var(--bg-main);
  border: 1px solid var(--border-color);
  color: var(--text-main);
  padding: 0.3rem 0;
  border-radius: 0.25rem;
  font-weight: 600;
  font-size: 0.8rem;
  cursor: pointer;

  &.selected {
    background-color: var(--accent-gold);
    color: #000;
    border-color: var(--accent-gold);
  }
}

.inputs-row {
  display: flex;
  gap: 0.5rem;
}

.input-group {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.8rem;
  color: var(--text-muted);
}

.num-input {
  width: 50px;
  background-color: var(--bg-main);
  border: 1px solid var(--border-color);
  color: var(--text-main);
  padding: 0.25rem 0.4rem;
  border-radius: 0.25rem;
  font-size: 0.85rem;
  outline: none;
}

.roll-action-btn {
  background-color: var(--accent-gold);
  color: #000;
  border: none;
  font-weight: 700;
  padding: 0.5rem;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.roll-action-btn:hover {
  background-color: var(--accent-gold-hover);
}

.latest-result {
  text-align: center;
  background-color: var(--bg-main);
  border: 1px dashed var(--accent-gold);
  padding: 0.5rem;
  border-radius: 0.375rem;
}

.result-total {
  font-size: 1.8rem;
  font-weight: 800;
  color: var(--accent-gold);
  line-height: 1;
}

.result-breakdown {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 0.25rem;
}

.history-section {
  border-top: 1px solid var(--border-color);
  padding-top: 0.5rem;
}

.history-title {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
  margin-bottom: 0.3rem;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.history-item {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.hist-total {
  font-weight: 700;
  color: var(--text-main);
}
</style>
