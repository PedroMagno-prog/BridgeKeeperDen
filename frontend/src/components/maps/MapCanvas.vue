<script setup lang="ts">
/**
 * Canvas Interativo 2D de Cartografia (Zoom, Pan, Drag-and-Drop de Marcadores).
 */
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useMapsStore, type MapDetail, type MapPin } from '@/stores/maps'
import PinPopover from './PinPopover.vue'

const props = defineProps<{
  mapDetail: MapDetail
  isMestre: boolean
  isDragMode: boolean
}>()

const emit = defineEmits<{
  (e: 'edit-pin', pin: MapPin): void
  (e: 'delete-pin', pin: MapPin): void
  (e: 'explore-map', mapId: string): void
}>()

const mapsStore = useMapsStore()

const containerRef = ref<HTMLDivElement | null>(null)
const imageRef = ref<HTMLImageElement | null>(null)

// Transformação da Câmera (Pan & Zoom)
const zoom = ref(1)
const mapOpacity = ref(1)
const panX = ref(0)
const panY = ref(0)
const isPanning = ref(false)
const dragStart = ref({ x: 0, y: 0 })

// Seleção de Marcador e Popover
const selectedPin = ref<MapPin | null>(null)
const popoverCoords = ref({ x: 0, y: 0 })

// Drag and Drop de Marcadores (Modo Mestre)
const draggingPin = ref<MapPin | null>(null)

const visiblePins = computed(() => {
  if (!props.mapDetail?.pins) return []
  return props.mapDetail.pins.filter((p) => {
    if (!p.layer_id) return true
    return mapsStore.activeLayers.has(p.layer_id)
  })
})

function clampPan(x: number, y: number, currentZoom: number) {
  if (!containerRef.value || !imageRef.value) return { x, y }
  const containerRect = containerRef.value.getBoundingClientRect()

  const imgWidth = (imageRef.value.naturalWidth || imageRef.value.clientWidth || 800) * currentZoom
  const imgHeight = (imageRef.value.naturalHeight || imageRef.value.clientHeight || 600) * currentZoom

  // Margem máxima da borda preta permitida (ex: 80px)
  const marginX = Math.min(80, containerRect.width * 0.2)
  const marginY = Math.min(80, containerRect.height * 0.2)

  const minX = marginX - imgWidth
  const maxX = containerRect.width - marginX

  const minY = marginY - imgHeight
  const maxY = containerRect.height - marginY

  const clampedX = Math.min(maxX, Math.max(minX, x))
  const clampedY = Math.min(maxY, Math.max(minY, y))

  return { x: clampedX, y: clampedY }
}

function applyZoomFocal(newZoom: number, focalX?: number, focalY?: number) {
  if (!containerRef.value) {
    zoom.value = newZoom
    return
  }
  const containerRect = containerRef.value.getBoundingClientRect()
  const fx = focalX ?? containerRect.width / 2
  const fy = focalY ?? containerRect.height / 2

  const oldZoom = zoom.value
  if (newZoom === oldZoom) return

  const worldX = (fx - panX.value) / oldZoom
  const worldY = (fy - panY.value) / oldZoom

  const rawPanX = fx - worldX * newZoom
  const rawPanY = fy - worldY * newZoom

  const clamped = clampPan(rawPanX, rawPanY, newZoom)

  zoom.value = newZoom
  panX.value = clamped.x
  panY.value = clamped.y
}

function zoomIn() {
  const target = Math.min(5, Number((zoom.value + 0.25).toFixed(2)))
  applyZoomFocal(target)
}

function zoomOut() {
  const target = Math.max(0.1, Number((zoom.value - 0.25).toFixed(2)))
  applyZoomFocal(target)
}

function resetView() {
  zoom.value = 1
  if (containerRef.value && imageRef.value) {
    const containerRect = containerRef.value.getBoundingClientRect()
    const imgWidth = imageRef.value.naturalWidth || imageRef.value.clientWidth || 800
    const imgHeight = imageRef.value.naturalHeight || imageRef.value.clientHeight || 600
    const centerX = Math.max(0, (containerRect.width - imgWidth) / 2)
    const centerY = Math.max(0, (containerRect.height - imgHeight) / 2)
    const clamped = clampPan(centerX, centerY, 1)
    panX.value = clamped.x
    panY.value = clamped.y
  } else {
    panX.value = 0
    panY.value = 0
  }
}

function handleWheel(e: WheelEvent) {
  e.preventDefault()
  if (!containerRef.value) return

  const containerRect = containerRef.value.getBoundingClientRect()
  const mouseX = e.clientX - containerRect.left
  const mouseY = e.clientY - containerRect.top

  const delta = e.deltaY < 0 ? 0.15 : -0.15
  const targetZoom = Math.min(5, Math.max(0.1, Number((zoom.value + delta).toFixed(2))))

  applyZoomFocal(targetZoom, mouseX, mouseY)
}

// ── Eventos de Pan e Drag ──────────────────────────────────────────────────

function handleMouseDown(e: MouseEvent) {
  // Se clicou no fundo do canvas, inicia o Pan da câmera
  if ((e.target as HTMLElement).classList.contains('canvas-area') || (e.target as HTMLElement).tagName === 'IMG') {
    selectedPin.value = null
    isPanning.value = true
    dragStart.value = { x: e.clientX - panX.value, y: e.clientY - panY.value }
  }
}

function handleMouseMove(e: MouseEvent) {
  if (isPanning.value) {
    const rawX = e.clientX - dragStart.value.x
    const rawY = e.clientY - dragStart.value.y
    const clamped = clampPan(rawX, rawY, zoom.value)
    panX.value = clamped.x
    panY.value = clamped.y
  } else if (draggingPin.value && containerRef.value && imageRef.value) {
    const rect = imageRef.value.getBoundingClientRect()
    const xPct = Math.min(100, Math.max(0, ((e.clientX - rect.left) / rect.width) * 100))
    const yPct = Math.min(100, Math.max(0, ((e.clientY - rect.top) / rect.height) * 100))
    draggingPin.value.x_position = xPct
    draggingPin.value.y_position = yPct
  }
}

function handleMouseUp() {
  if (isPanning.value) {
    isPanning.value = false
  }
  if (draggingPin.value) {
    const pin = draggingPin.value
    draggingPin.value = null
    // Salva a nova coordenada no backend
    mapsStore.updatePinPosition(props.mapDetail.id, pin.id, pin.x_position, pin.y_position)
  }
}

function canUserDragPin(pin: MapPin): boolean {
  return props.isMestre || !!pin.can_edit
}

function startPinDrag(e: MouseEvent, pin: MapPin) {
  if (canUserDragPin(pin) && (props.isDragMode || e.shiftKey)) {
    e.stopPropagation()
    draggingPin.value = pin
    selectedPin.value = null
  }
}

function selectPin(e: MouseEvent, pin: MapPin) {
  e.stopPropagation()
  if (draggingPin.value) return

  const target = e.currentTarget as HTMLElement
  const containerRect = containerRef.value?.getBoundingClientRect()
  if (target && containerRect) {
    const pinRect = target.getBoundingClientRect()
    popoverCoords.value = {
      x: pinRect.left - containerRect.left + pinRect.width / 2,
      y: pinRect.top - containerRect.top,
    }
    selectedPin.value = pin
  }
}

function getIconEmoji(icon: string): string {
  switch (icon) {
    case 'city': return '🏙️'
    case 'castle': return '🏰'
    case 'dungeon': return '🗝️'
    case 'ruins': return '🏛️'
    case 'cave': return '⛰️'
    case 'tavern': return '🍺'
    case 'monster': return '👾'
    default: return '📍'
  }
}
</script>

<template>
  <div
    ref="containerRef"
    class="map-canvas-container"
    @mousedown="handleMouseDown"
    @mousemove="handleMouseMove"
    @mouseup="handleMouseUp"
    @mouseleave="handleMouseUp"
    @wheel="handleWheel"
  >
    <!-- Controles de Zoom e Opacidade -->
    <div class="zoom-controls">
      <button class="zoom-btn" title="Aumentar Zoom (+)" @click="zoomIn">+</button>
      <span class="zoom-label">{{ Math.round(zoom * 100) }}%</span>
      <button class="zoom-btn" title="Diminuir Zoom (-)" @click="zoomOut">-</button>
      <button class="zoom-btn reset-btn" title="Resetar Câmera" @click="resetView">🔄</button>

      <div class="control-divider"></div>

      <!-- Slider de Opacidade -->
      <div class="opacity-control" title="Opacidade da Imagem de Fundo">
        <span class="opacity-label">👁️ {{ Math.round(mapOpacity * 100) }}%</span>
        <input
          type="range"
          min="0.1"
          max="1"
          step="0.05"
          v-model.number="mapOpacity"
          class="opacity-slider"
        />
      </div>
    </div>

    <!-- Área Transformada do Mapa -->
    <div
      class="canvas-area"
      :style="{
        transform: `translate(${panX}px, ${panY}px) scale(${zoom})`,
        transformOrigin: '0 0',
      }"
    >
      <img
        ref="imageRef"
        :src="mapDetail.image_url"
        :alt="mapDetail.title"
        class="map-image"
        :style="{ opacity: mapOpacity }"
        draggable="false"
      />

      <!-- Marcadores (Pins) -->
      <div
        v-for="pin in visiblePins"
        :key="pin.id"
        class="map-pin"
        :class="{
          'map-pin--locked': pin.is_locked,
          'map-pin--selected': selectedPin?.id === pin.id,
          'map-pin--draggable': canUserDragPin(pin) && (isDragMode || draggingPin?.id === pin.id),
        }"
        :style="{
          left: `${pin.x_position}%`,
          top: `${pin.y_position}%`,
        }"
        @mousedown="(e) => startPinDrag(e, pin)"
        @click="(e) => selectPin(e, pin)"
      >
        <div class="pin-marker" :style="{ backgroundColor: pin.color }">
          <span class="pin-icon">{{ pin.is_locked ? '❓' : getIconEmoji(pin.icon) }}</span>
        </div>
        <span class="pin-title">{{ pin.title }}</span>
      </div>
    </div>

    <!-- Popover do Marcador -->
    <PinPopover
      v-if="selectedPin"
      :pin="selectedPin"
      :is-mestre="isMestre"
      :x="popoverCoords.x"
      :y="popoverCoords.y"
      @close="selectedPin = null"
      @edit="(p) => emit('edit-pin', p)"
      @delete="(p) => emit('delete-pin', p)"
      @explore-map="(id) => emit('explore-map', id)"
    />
  </div>
</template>

<style scoped>
.map-canvas-container {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: #090B0E;
  user-select: none;
  cursor: grab;
}

.map-canvas-container:active {
  cursor: grabbing;
}

/* Zoom Controls */
.zoom-controls {
  position: absolute;
  top: 16px;
  right: 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 4px;
  z-index: 300;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}

.zoom-btn {
  width: 32px;
  height: 32px;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text);
  font-weight: bold;
  font-size: 1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}
.zoom-btn:hover { background: var(--color-gold-glow); color: var(--color-gold); }

.zoom-label {
  font-size: 0.7rem;
  color: var(--color-text-dim);
  text-align: center;
  padding: 2px 0;
}

.reset-btn { font-size: 0.8rem; }

.control-divider {
  width: 100%;
  border-top: 1px solid var(--color-border);
  margin: 4px 0;
}

.opacity-control {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding-top: 2px;
}

.opacity-label {
  font-size: 0.65rem;
  color: var(--color-text-dim);
  text-align: center;
  font-weight: 600;
}

.opacity-slider {
  width: 50px;
  height: 4px;
  accent-color: var(--color-gold);
  cursor: pointer;
}

/* Canvas Area */
.canvas-area {
  position: absolute;
  top: 0;
  left: 0;
  will-change: transform;
}

.map-image {
  display: block;
  max-width: none;
  pointer-events: auto;
}

/* Map Pins */
.map-pin {
  position: absolute;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  z-index: 100;
  transition: transform 0.15s ease;
}

.map-pin:hover {
  transform: translate(-50%, -50%) scale(1.15);
  z-index: 150;
}

.map-pin--selected {
  transform: translate(-50%, -50%) scale(1.25);
  z-index: 200;
}

.map-pin--draggable {
  cursor: move;
}

.pin-marker {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.6);
  border: 2px solid #FFFFFF;
}

.pin-icon {
  font-size: 0.85rem;
}

.pin-title {
  font-size: 0.7rem;
  font-weight: 600;
  color: #FFFFFF;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.9), 0 0 8px rgba(0, 0, 0, 0.8);
  white-space: nowrap;
  margin-top: 2px;
  background: rgba(0, 0, 0, 0.5);
  padding: 1px 6px;
  border-radius: 4px;
}
</style>
