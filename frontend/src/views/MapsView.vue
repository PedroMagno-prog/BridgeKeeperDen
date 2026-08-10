<script setup lang="ts">
/**
 * TELA 4: Mapas Interativos — Canvas com zoom/pan + pins + layers
 */
import { ref, computed, onMounted, watch, onUnmounted } from 'vue'
import { useMapsStore, type MapDetail, type MapPin } from '@/stores/maps'
import { useWorldsStore } from '@/stores/worlds'
import VisibilityBadge from '@/components/ui/VisibilityBadge.vue'

const mapsStore = useMapsStore()
const worldsStore = useWorldsStore()
const isMestre = computed(() => worldsStore.isMestre)

// Canvas state
const canvasRef = ref<HTMLDivElement>()
const zoom = ref(1)
const pan = ref({ x: 0, y: 0 })
const isPanning = ref(false)
const panStart = ref({ x: 0, y: 0 })
const selectedPin = ref<MapPin | null>(null)
const showMapList = ref(true)
const showLayerDrawer = ref(false)

// Create pin state
const showPinForm = ref(false)
const pinFormPos = ref({ x: 0, y: 0 })
const newPinTitle = ref('')
const newPinIcon = ref('default-pin')
const newPinColor = ref('#D4AF37')
const newPinVisibility = ref<'TOTAL' | 'PARCIAL' | 'NULA'>('NULA')

onMounted(() => {
  mapsStore.fetchMaps()
})

const currentMap = computed(() => mapsStore.current)
const visiblePins = computed(() => {
  if (!currentMap.value) return []
  return currentMap.value.pins.filter((p) => {
    if (mapsStore.activeLayers.size === 0 && p.layer_id) return true
    if (p.layer_id && !mapsStore.activeLayers.has(p.layer_id)) return false
    return true
  })
})

function selectMap(id: string) {
  mapsStore.fetchMap(id)
  showMapList.value = false
}

// Zoom
function handleWheel(e: WheelEvent) {
  e.preventDefault()
  const delta = e.deltaY > 0 ? -0.1 : 0.1
  zoom.value = Math.max(0.3, Math.min(4, zoom.value + delta))
}

function zoomIn() { zoom.value = Math.min(4, zoom.value + 0.2) }
function zoomOut() { zoom.value = Math.max(0.3, zoom.value - 0.2) }

// Pan
function startPan(e: MouseEvent) {
  if (e.button !== 0) return
  isPanning.value = true
  panStart.value = { x: e.clientX - pan.value.x, y: e.clientY - pan.value.y }
}
function movePan(e: MouseEvent) {
  if (!isPanning.value) return
  pan.value = { x: e.clientX - panStart.value.x, y: e.clientY - panStart.value.y }
}
function endPan() { isPanning.value = false }

// Pin interaction
function pinStyle(pin: MapPin) {
  const isNula = pin.visibility === 'NULA'
  const isParcial = pin.visibility === 'PARCIAL'
  return {
    left: `${pin.x_position}%`,
    top: `${pin.y_position}%`,
    '--pin-color': isNula && isMestre.value ? '#EF4444' : isParcial && !isMestre.value ? '#F59E0B' : pin.color,
    opacity: isNula && isMestre.value ? 0.4 : 1,
  }
}

function clickPin(pin: MapPin, e: MouseEvent) {
  e.stopPropagation()
  selectedPin.value = selectedPin.value?.id === pin.id ? null : pin
}

// Right-click to add pin (Mestre only)
function handleContextMenu(e: MouseEvent) {
  if (!isMestre.value || !currentMap.value || !canvasRef.value) return
  e.preventDefault()
  const rect = canvasRef.value.getBoundingClientRect()
  const imgW = canvasRef.value.scrollWidth
  const imgH = canvasRef.value.scrollHeight
  const x = ((e.clientX - rect.left) / rect.width) * 100
  const y = ((e.clientY - rect.top) / rect.height) * 100
  pinFormPos.value = { x: Math.max(0, Math.min(100, x)), y: Math.max(0, Math.min(100, y)) }
  showPinForm.value = true
}

async function createPin() {
  if (!currentMap.value || !newPinTitle.value.trim()) return
  await mapsStore.createPin(currentMap.value.id, {
    title: newPinTitle.value.trim(),
    x_position: +pinFormPos.value.x.toFixed(2),
    y_position: +pinFormPos.value.y.toFixed(2),
    icon: newPinIcon.value,
    color: newPinColor.value,
    visibility: newPinVisibility.value,
  } as any)
  showPinForm.value = false
  newPinTitle.value = ''
}

function backToList() {
  showMapList.value = true
  mapsStore.current = null
  selectedPin.value = null
}
</script>

<template>
  <div class="maps-view">
    <!-- Map List -->
    <Transition name="fade">
      <div v-if="showMapList" class="maps-list">
        <div class="maps-list__header">
          <h2 class="maps-list__title">Mapas</h2>
          <button v-if="isMestre" class="btn-gold-sm" @click="/* TODO: create map modal */">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            Novo Mapa
          </button>
        </div>
        <div v-if="mapsStore.loading" class="list-empty">Carregando...</div>
        <div v-else-if="mapsStore.maps.length === 0" class="list-empty">Nenhum mapa cadastrado.</div>
        <button v-for="m in mapsStore.maps" :key="m.id" class="map-card" @click="selectMap(m.id)">
          <div class="map-card__preview" :style="{ backgroundImage: `url(${m.image_url})` }" />
          <div class="map-card__info">
            <span class="map-card__name">{{ m.title }}</span>
          </div>
        </button>
      </div>
    </Transition>

    <!-- Map Canvas -->
    <Transition name="fade">
      <div v-if="!showMapList && currentMap" class="map-canvas-wrapper">
        <!-- Top bar -->
        <div class="map-toolbar">
          <button class="back-btn" @click="backToList">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="15 18 9 12 15 6"/>
            </svg>
          </button>
          <h2 class="map-toolbar__title">{{ currentMap.title }}</h2>
          <button v-if="currentMap.layers.length" class="layer-toggle" @click="showLayerDrawer = !showLayerDrawer">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>
            </svg>
            Camadas
          </button>
        </div>

        <!-- Canvas -->
        <div
          ref="canvasRef"
          class="map-canvas"
          :style="{ transform: `scale(${zoom}) translate(${pan.x / zoom}px, ${pan.y / zoom}px)`, cursor: isPanning ? 'grabbing' : 'grab' }"
          @wheel.prevent="handleWheel"
          @mousedown="startPan"
          @mousemove="movePan"
          @mouseup="endPan"
          @mouseleave="endPan"
          @contextmenu="handleContextMenu"
        >
          <img :src="currentMap.image_url" class="map-image" draggable="false" alt="Mapa" @load="zoom = 1; pan = { x: 0, y: 0 }" />

          <!-- Pins -->
          <button
            v-for="pin in visiblePins" :key="pin.id"
            class="map-pin"
            :style="pinStyle(pin)"
            :class="{ 'map-pin--selected': selectedPin?.id === pin.id }"
            @click="clickPin(pin, $event)"
          >
            <span v-if="pin.is_locked" class="pin-icon pin-icon--locked">?</span>
            <span v-else class="pin-icon" :style="{ background: pin.color }">●</span>
          </button>
        </div>

        <!-- Pin Tooltip -->
        <Transition name="fade">
          <div v-if="selectedPin" class="pin-tooltip" :class="{ 'pin-tooltip--locked': selectedPin.is_locked }">
            <div class="pin-tooltip__title">
              {{ selectedPin.is_locked ? selectedPin.title : selectedPin.title }}
              <VisibilityBadge v-if="isMestre" :visibility="selectedPin.visibility" />
            </div>
            <p v-if="selectedPin.is_locked" class="pin-tooltip__locked">Conteúdo não descoberto</p>
            <div v-else class="pin-tooltip__actions">
              <button v-if="selectedPin.target_article_id" class="btn-link" @click="$router.push(`/codex/${selectedPin.target_article_id}`)">Abrir Artigo →</button>
            </div>
          </div>
        </Transition>

        <!-- Zoom Controls -->
        <div class="zoom-controls">
          <button class="zoom-btn" @click="zoomIn">+</button>
          <span class="zoom-level">{{ Math.round(zoom * 100) }}%</span>
          <button class="zoom-btn" @click="zoomOut">−</button>
        </div>

        <!-- Layer Drawer -->
        <Transition name="slide-right">
          <div v-if="showLayerDrawer" class="layer-drawer">
            <h4 class="layer-drawer__title">Camadas</h4>
            <label v-for="layer in currentMap.layers" :key="layer.id" class="layer-item">
              <input type="checkbox" :checked="mapsStore.activeLayers.has(layer.id)" @change="mapsStore.toggleLayer(layer.id)" />
              <span>{{ layer.name }}</span>
            </label>
          </div>
        </Transition>

        <!-- Pin Creation Form -->
        <Teleport to="body">
          <Transition name="fade">
            <div v-if="showPinForm" class="modal-overlay" @click.self="showPinForm = false">
              <div class="modal" @click.stop>
                <h3 class="modal__title">Adicionar Marcador</h3>
                <div class="form-group">
                  <label>Título</label>
                  <input v-model="newPinTitle" type="text" class="form-input" placeholder="Nome do local" autofocus />
                </div>
                <div class="form-row">
                  <div class="form-group">
                    <label>Cor</label>
                    <input v-model="newPinColor" type="color" class="form-color" />
                  </div>
                  <div class="form-group form-group--flex">
                    <label>Visibilidade</label>
                    <select v-model="newPinVisibility" class="form-input">
                      <option value="NULA">Nula</option><option value="PARCIAL">Parcial</option><option value="TOTAL">Total</option>
                    </select>
                  </div>
                </div>
                <div class="modal__actions">
                  <button class="btn btn--ghost" @click="showPinForm = false">Cancelar</button>
                  <button class="btn btn--gold" @click="createPin" :disabled="!newPinTitle.trim()">Criar Pin</button>
                </div>
              </div>
            </div>
          </Transition>
        </Teleport>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.maps-view { height: calc(100vh - 56px); margin: calc(-1 * var(--space-6)) calc(-1 * var(--space-8)); display: flex; flex-direction: column; position: relative; overflow: hidden; }

/* Map List */
.maps-list { padding: var(--space-6) var(--space-8); overflow-y: auto; flex: 1; }
.maps-list__header { display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--space-6); }
.maps-list__title { font-family: var(--font-display); font-size: 1.3rem; color: var(--color-gold); }
.map-card {
  display: flex; align-items: center; gap: var(--space-4); width: 100%;
  padding: var(--space-3); margin-bottom: var(--space-3);
  background: var(--color-surface); border: 1px solid var(--color-border);
  border-radius: var(--radius-md); cursor: pointer; font-family: var(--font-body);
  color: var(--color-text); transition: all var(--transition-fast); text-align: left;
}
.map-card:hover { border-color: var(--color-border-glow); transform: translateY(-1px); }
.map-card__preview { width: 80px; height: 50px; border-radius: var(--radius-sm); background-size: cover; background-position: center; background-color: var(--color-surface-3); flex-shrink: 0; }
.map-card__name { font-weight: 500; font-size: 0.9rem; }

/* Map Canvas */
.map-canvas-wrapper { flex: 1; position: relative; overflow: hidden; background: var(--color-bg); }
.map-toolbar {
  display: flex; align-items: center; gap: var(--space-3);
  padding: var(--space-3) var(--space-4); background: var(--color-surface);
  border-bottom: 1px solid var(--color-border); z-index: 10; position: relative;
}
.map-toolbar__title { flex: 1; font-size: 0.9rem; font-weight: 500; }
.layer-toggle {
  display: flex; align-items: center; gap: 6px;
  padding: 4px 10px; background: none; border: 1px solid var(--color-border);
  border-radius: var(--radius-sm); color: var(--color-text-muted);
  font-family: var(--font-body); font-size: 0.75rem; cursor: pointer;
}
.layer-toggle:hover { border-color: var(--color-gold-dim); color: var(--color-gold); }

.map-canvas {
  position: absolute; inset: 44px 0 0 0;
  transform-origin: center center;
  transition: transform 0.15s ease;
  display: flex; align-items: center; justify-content: center;
}
.map-image { max-width: 100%; max-height: 100%; user-select: none; pointer-events: none; }

/* Pins */
.map-pin {
  position: absolute; transform: translate(-50%, -50%);
  border: none; background: none; cursor: pointer; z-index: 5;
  padding: 4px; transition: all var(--transition-fast);
}
.map-pin:hover { transform: translate(-50%, -50%) scale(1.3); z-index: 10; }
.map-pin--selected { transform: translate(-50%, -50%) scale(1.4); z-index: 10; }
.pin-icon {
  display: flex; align-items: center; justify-content: center;
  width: 24px; height: 24px; border-radius: 50%;
  color: white; font-size: 0.65rem; font-weight: 700;
  box-shadow: 0 2px 8px rgba(0,0,0,0.5);
  border: 2px solid rgba(255,255,255,0.3);
}
.pin-icon--locked { background: var(--color-gold-glow); color: var(--color-gold); border: 2px solid var(--color-gold-dim); }

/* Pin Tooltip */
.pin-tooltip {
  position: absolute; bottom: var(--space-6); left: 50%; transform: translateX(-50%);
  background: var(--color-surface-2); border: 1px solid var(--color-border);
  border-radius: var(--radius-md); padding: var(--space-4); min-width: 200px;
  box-shadow: var(--shadow-lg); z-index: 20;
}
.pin-tooltip__title { font-weight: 600; font-size: 0.9rem; display: flex; align-items: center; gap: var(--space-2); margin-bottom: var(--space-2); }
.pin-tooltip__locked { font-size: 0.8rem; color: var(--color-text-dim); font-style: italic; }
.pin-tooltip__actions { display: flex; gap: var(--space-2); }

/* Zoom Controls */
.zoom-controls {
  position: absolute; bottom: var(--space-4); right: var(--space-4);
  display: flex; flex-direction: column; align-items: center; gap: 4px; z-index: 15;
}
.zoom-btn {
  width: 32px; height: 32px; border-radius: var(--radius-sm);
  border: 1px solid var(--color-border); background: var(--color-surface);
  color: var(--color-text); font-size: 1rem; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all var(--transition-fast);
}
.zoom-btn:hover { border-color: var(--color-gold-dim); color: var(--color-gold); }
.zoom-level { font-size: 0.65rem; color: var(--color-text-dim); }

/* Layer Drawer */
.layer-drawer {
  position: absolute; top: 44px; right: 0; width: 200px; height: calc(100% - 44px);
  background: var(--color-surface); border-left: 1px solid var(--color-border);
  padding: var(--space-4); z-index: 15; overflow-y: auto;
}
.layer-drawer__title { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--color-text-dim); margin-bottom: var(--space-4); }
.layer-item {
  display: flex; align-items: center; gap: var(--space-2);
  padding: var(--space-2) 0; font-size: 0.8rem; cursor: pointer;
  color: var(--color-text-muted);
}
.layer-item input[type="checkbox"] { accent-color: var(--color-gold); }

/* Shared */
.back-btn { display: flex; align-items: center; justify-content: center; width: 28px; height: 28px; border-radius: var(--radius-sm); border: 1px solid var(--color-border); background: none; color: var(--color-text-muted); cursor: pointer; }
.back-btn:hover { border-color: var(--color-gold-dim); color: var(--color-gold); }
.btn-gold-sm { display: flex; align-items: center; gap: 4px; padding: 5px 12px; background: var(--color-gold); color: #0d0f14; border: none; border-radius: var(--radius-sm); font-family: var(--font-body); font-weight: 600; font-size: 0.75rem; cursor: pointer; }
.btn-gold-sm:hover { background: var(--color-gold-light); }
.list-empty { padding: var(--space-8); text-align: center; color: var(--color-text-dim); font-size: 0.85rem; }
.btn-link { background: none; border: none; color: var(--color-gold); font-size: 0.8rem; cursor: pointer; font-family: var(--font-body); }
.btn-link:hover { text-decoration: underline; }

/* Modal */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.7); z-index: 300; display: flex; align-items: center; justify-content: center; backdrop-filter: blur(4px); }
.modal { background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); padding: var(--space-8); width: 100%; max-width: 400px; box-shadow: var(--shadow-lg); }
.modal__title { font-size: 1.1rem; font-weight: 600; color: var(--color-gold); margin-bottom: var(--space-6); }
.form-group { display: flex; flex-direction: column; gap: var(--space-2); margin-bottom: var(--space-4); }
.form-group--flex { flex: 1; }
.form-group label { font-size: 0.75rem; color: var(--color-text-muted); text-transform: uppercase; letter-spacing: 0.06em; }
.form-input { background: var(--color-bg); border: 1px solid var(--color-border); border-radius: var(--radius-sm); color: var(--color-text); font-family: var(--font-body); font-size: 0.85rem; padding: var(--space-2) var(--space-3); }
.form-input:focus { outline: none; border-color: var(--color-gold-dim); }
.form-color { width: 100%; height: 36px; border: 1px solid var(--color-border); border-radius: var(--radius-sm); background: var(--color-bg); cursor: pointer; }
.form-row { display: flex; gap: var(--space-4); }
.modal__actions { display: flex; gap: var(--space-3); justify-content: flex-end; margin-top: var(--space-6); }
.btn { padding: var(--space-2) var(--space-5); border-radius: var(--radius-sm); border: none; font-family: var(--font-body); font-size: 0.875rem; font-weight: 500; cursor: pointer; }
.btn--ghost { background: none; border: 1px solid var(--color-border); color: var(--color-text-muted); }
.btn--gold { background: var(--color-gold); color: #0d0f14; font-weight: 600; }
.btn--gold:hover { background: var(--color-gold-light); }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
