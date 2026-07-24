<template>
  <div class="map-page" v-if="mapStore.currentMap">
    <div class="map-toolbar card">
      <div class="map-title-area">
        <h2 class="map-title">{{ mapStore.currentMap.title }}</h2>
        <span class="pins-count">{{ mapStore.currentMap.pins.length }} marcadores</span>
      </div>

      <div class="toolbar-actions">
        <!-- Seletor de Mapa se houver múltiplos -->
        <select :value="mapStore.currentMap.id" @change="onMapChange" class="input-field map-select">
          <option v-for="m in mapStore.maps" :key="m.id" :value="m.id">
            {{ m.title }}
          </option>
        </select>

        <button class="btn-secondary" @click="showLayersDrawer = !showLayersDrawer">
          🗂️ Camadas ({{ mapStore.currentMap.layers.length }})
        </button>

        <button class="btn-primary" v-if="worldStore.activeUserRole === 'MESTRE'" @click="showAddMapModal = true">
          + Novo Mapa
        </button>
      </div>
    </div>

    <!-- Canvas do Mapa -->
    <div
      class="map-viewport"
      ref="viewportRef"
      @mousedown="startPan"
      @mousemove="doPan"
      @mouseup="stopPan"
      @mouseleave="stopPan"
      @click="onMapClick"
    >
      <div
        class="map-container"
        :style="{
          transform: `translate(${panX}px, ${panY}px) scale(${zoomLevel})`,
        }"
      >
        <img :src="mapStore.currentMap.image_url" class="map-image" alt="Mapa Interativo" draggable="false" />

        <!-- Renderizador de Pins -->
        <div
          v-for="pin in mapStore.currentMap.pins"
          :key="pin.id"
          class="map-pin-marker"
          :class="{
            locked: pin.is_locked,
            'vis-nula': pin.visibility === 'NULA'
          }"
          :style="{
            left: `${pin.x_position}%`,
            top: `${pin.y_position}%`,
            borderColor: pin.color || '#FF0000',
          }"
          @click.stop="openPinPopover(pin)"
        >
          <!-- Ícone do Pin -->
          <span v-if="pin.visibility === 'PARCIAL' && worldStore.activeUserRole === 'JOGADOR'" class="pin-symbol">?</span>
          <span v-else class="pin-symbol">📍</span>
        </div>
      </div>

      <!-- Controles de Zoom Float -->
      <div class="zoom-controls">
        <button class="zoom-btn" @click="zoomIn">+</button>
        <button class="zoom-btn" @click="resetZoom">100%</button>
        <button class="zoom-btn" @click="zoomOut">-</button>
      </div>

      <!-- Pop-over de Marcador -->
      <div class="pin-popover card" v-if="activePin" :style="popoverStyle" @click.stop>
        <div class="popover-header">
          <h4>{{ activePin.title }}</h4>
          <button class="close-btn" @click="activePin = null">&times;</button>
        </div>
        <div class="popover-body">
          <p v-if="activePin.is_locked" class="locked-msg">
            🔒 Local misterioso ou conteúdo ainda não descoberto pelo grupo.
          </p>
          <p v-else class="discovered-msg">
            Marcador visível. Clique abaixo para abrir as notas de lore vinculadas.
          </p>

          <button
            v-if="activePin.target_article_id && !activePin.is_locked"
            class="btn-primary open-article-btn"
            @click="navigateToArticle(activePin.target_article_id)"
          >
            Abrir Artigo &rarr;
          </button>
        </div>
      </div>
    </div>

    <!-- Drawer de Camadas -->
    <div class="layers-drawer card" v-if="showLayersDrawer">
      <div class="drawer-header">
        <h4>Camadas do Mapa</h4>
        <button class="close-btn" @click="showLayersDrawer = false">&times;</button>
      </div>
      <div class="layers-list">
        <label v-for="l in mapStore.currentMap.layers" :key="l.id" class="layer-item">
          <input type="checkbox" :checked="l.is_default_active" />
          <span>{{ l.name }}</span>
        </label>
      </div>
    </div>

    <!-- Modal Novo Marcador (Mestre) -->
    <div class="modal-backdrop" v-if="showAddPinModal">
      <div class="modal-card card">
        <div class="modal-header">
          <h3>Adicionar Marcador no Mapa</h3>
          <button class="close-btn" @click="showAddPinModal = false">&times;</button>
        </div>
        <form @submit.prevent="handleCreatePin" class="form">
          <div class="input-group">
            <label>Título do Marcador *</label>
            <input type="text" v-model="newPinTitle" class="input-field" placeholder="Ex: Ruínas de Eldoria" required />
          </div>

          <div class="input-group">
            <label>Visibilidade (Mestre)</label>
            <select v-model="newPinVisibility" class="input-field">
              <option value="NULA">Visão Nula (Invisível para Jogadores)</option>
              <option value="PARCIAL">Visão Parcial (Apenas ícone ? e Título)</option>
              <option value="TOTAL">Visão Total (Público)</option>
            </select>
          </div>

          <div class="input-group">
            <label>Posição X / Y (%)</label>
            <div class="pos-row">
              <input type="number" v-model.number="newPinX" step="0.1" class="input-field" readonly />
              <input type="number" v-model.number="newPinY" step="0.1" class="input-field" readonly />
            </div>
          </div>

          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="showAddPinModal = false">Cancelar</button>
            <button type="submit" class="btn-primary">Adicionar Marcador</button>
          </div>
        </form>
      </div>
    </div>
  </div>

  <div class="empty-state card" v-else>
    <h3>Nenhum mapa cadastrado</h3>
    <button class="btn-primary" v-if="worldStore.activeUserRole === 'MESTRE'" @click="showAddMapModal = true">
      + Cadastrar Primeiro Mapa
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMapStore, type MapPin } from '../stores/map'
import { useWorldStore } from '../stores/world'

const mapStore = useMapStore()
const worldStore = useWorldStore()
const route = useRoute()
const router = useRouter()

const zoomLevel = ref(1)
const panX = ref(0)
const panY = ref(0)
const isPanning = ref(false)
const startX = ref(0)
const startY = ref(0)

const activePin = ref<MapPin | null>(null)
const popoverStyle = ref({})
const showLayersDrawer = ref(false)
const showAddMapModal = ref(false)

const showAddPinModal = ref(false)
const newPinTitle = ref('')
const newPinVisibility = ref<'TOTAL' | 'PARCIAL' | 'NULA'>('NULA')
const newPinX = ref(0)
const newPinY = ref(0)

onMounted(async () => {
  if (worldStore.activeWorldId) {
    await mapStore.fetchMaps(worldStore.activeWorldId)
    if (mapStore.maps.length > 0 && mapStore.maps[0]) {
      await mapStore.fetchMapById(worldStore.activeWorldId, mapStore.maps[0].id)
    }
  }
})

function zoomIn() {
  if (zoomLevel.value < 3) zoomLevel.value += 0.25
}

function zoomOut() {
  if (zoomLevel.value > 0.5) zoomLevel.value -= 0.25
}

function resetZoom() {
  zoomLevel.value = 1
  panX.value = 0
  panY.value = 0
}

function startPan(e: MouseEvent) {
  isPanning.value = true
  startX.value = e.clientX - panX.value
  startY.value = e.clientY - panY.value
}

function doPan(e: MouseEvent) {
  if (!isPanning.value) return
  panX.value = e.clientX - startX.value
  panY.value = e.clientY - startY.value
}

function stopPan() {
  isPanning.value = false
}

function onMapClick(e: MouseEvent) {
  if (worldStore.activeUserRole !== 'MESTRE') return
  const img = e.currentTarget as HTMLElement
  const rect = img.getBoundingClientRect()
  const xPercent = ((e.clientX - rect.left) / rect.width) * 100
  const yPercent = ((e.clientY - rect.top) / rect.height) * 100

  newPinX.value = Math.round(xPercent * 10) / 10
  newPinY.value = Math.round(yPercent * 10) / 10
  showAddPinModal.value = true
}

function openPinPopover(pin: MapPin) {
  activePin.value = pin
}

function navigateToArticle(articleId: string) {
  if (worldStore.activeWorldId) {
    router.push(`/worlds/${worldStore.activeWorldId}/codex/${articleId}`)
  }
}

async function onMapChange(e: Event) {
  const target = e.target as HTMLSelectElement
  if (target.value && worldStore.activeWorldId) {
    await mapStore.fetchMapById(worldStore.activeWorldId, target.value)
  }
}

async function handleCreatePin() {
  if (!newPinTitle.value.trim() || !mapStore.currentMap || !worldStore.activeWorldId) return
  await mapStore.createPin(worldStore.activeWorldId, mapStore.currentMap.id, {
    title: newPinTitle.value,
    x_position: newPinX.value,
    y_position: newPinY.value,
    visibility: newPinVisibility.value,
  })
  showAddPinModal.value = false
  newPinTitle.value = ''
}
</script>

<style scoped>
.map-page {
  height: calc(100vh - 60px);
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

.map-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 1rem 1.5rem 0.5rem;
  z-index: 5;
}

.map-title {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--accent-gold);
}

.pins-count {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.toolbar-actions {
  display: flex;
  gap: 0.75rem;
}

.map-select {
  width: auto;
}

.map-viewport {
  flex-grow: 1;
  background-color: #050811;
  position: relative;
  overflow: hidden;
  cursor: grab;

  &:active {
    cursor: grabbing;
  }
}

.map-container {
  position: absolute;
  top: 0;
  left: 0;
  transform-origin: 0 0;
  transition: transform 0.1s linear;
}

.map-image {
  display: block;
  max-width: none;
}

.map-pin-marker {
  position: absolute;
  transform: translate(-50%, -100%);
  cursor: pointer;
  background-color: var(--bg-card);
  border: 2px solid var(--accent-gold);
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 10px rgba(0,0,0,0.5);
  transition: transform 0.2s ease;

  &:hover {
    transform: translate(-50%, -110%) scale(1.2);
  }

  &.locked {
    border-color: var(--fow-parcial);
  }

  &.vis-nula {
    opacity: 0.5;
    border-style: dashed;
  }
}

.pin-symbol {
  font-size: 1rem;
}

.zoom-controls {
  position: absolute;
  bottom: 1.5rem;
  left: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  z-index: 10;
}

.zoom-btn {
  background-color: var(--bg-card);
  border: 1px solid var(--border-color);
  color: var(--text-main);
  font-weight: 700;
  width: 36px;
  height: 36px;
  border-radius: 0.375rem;
  cursor: pointer;

  &:hover {
    border-color: var(--accent-gold);
    color: var(--accent-gold);
  }
}

.pin-popover {
  position: absolute;
  top: 20%;
  left: 50%;
  transform: translateX(-50%);
  width: 280px;
  z-index: 20;

  .popover-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 0.5rem;
    margin-bottom: 0.5rem;

    h4 {
      color: var(--accent-gold);
    }
  }

  .open-article-btn {
    width: 100%;
    margin-top: 0.75rem;
    justify-content: center;
  }
}

.layers-drawer {
  position: absolute;
  top: 4.5rem;
  right: 1.5rem;
  width: 220px;
  z-index: 15;
}

/* Modal */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
}

.modal-card {
  width: 100%;
  max-width: 420px;
}

.pos-row {
  display: flex;
  gap: 0.5rem;
}
</style>
