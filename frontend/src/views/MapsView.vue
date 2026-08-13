<script setup lang="ts">
/**
 * Módulos de Cartografia Interativa (Etapa 2) — MapsView.vue
 */
import { ref, computed, onMounted } from 'vue'
import { useMapsStore, type MapItem, type MapPin } from '@/stores/maps'
import { useWorldsStore } from '@/stores/worlds'
import MapCanvas from '@/components/maps/MapCanvas.vue'
import PinModal from '@/components/maps/PinModal.vue'
import MapModal from '@/components/maps/MapModal.vue'

const mapsStore = useMapsStore()
const worldsStore = useWorldsStore()
const isMestre = computed(() => worldsStore.isMestre)

const showMapList = ref(true)
const showLayerDrawer = ref(false)
const isDragMode = ref(false)

// Modais
const showMapModal = ref(false)
const editingMap = ref<MapItem | null>(null)
const showPinModal = ref(false)
const editingPin = ref<MapPin | null>(null)

onMounted(async () => {
  if (!worldsStore.activeWorld) {
    await worldsStore.fetchWorlds()
  }
  mapsStore.fetchMaps()
})

const currentMap = computed(() => mapsStore.current)

function selectMap(id: string) {
  mapsStore.fetchMap(id)
  showMapList.value = false
}

function openBreadcrumb(mapId: string) {
  mapsStore.fetchMap(mapId)
}

function backToList() {
  showMapList.value = true
  mapsStore.current = null
  mapsStore.clearBreadcrumbs()
}

function openCreateMapModal() {
  editingMap.value = null
  showMapModal.value = true
}

function openEditMapModal() {
  if (currentMap.value) {
    editingMap.value = {
      id: currentMap.value.id,
      title: currentMap.value.title,
      image_url: currentMap.value.image_url,
      created_at: currentMap.value.created_at,
    }
    showMapModal.value = true
  }
}

async function handleDeleteMap() {
  if (!currentMap.value) return
  if (confirm(`Tem certeza que deseja excluir o mapa "${currentMap.value.title}"? Todos os seus marcadores e camadas serão removidos.`)) {
    await mapsStore.deleteMap(currentMap.value.id)
    backToList()
  }
}

function openCreatePinModal() {
  editingPin.value = null
  showPinModal.value = true
}

function openEditPinModal(pin: MapPin) {
  editingPin.value = pin
  showPinModal.value = true
}

async function handleDeletePin(pin: MapPin) {
  if (!currentMap.value) return
  if (confirm(`Excluir o marcador "${pin.title}"?`)) {
    await mapsStore.deletePin(currentMap.value.id, pin.id)
  }
}

function exploreSubMap(mapId: string) {
  mapsStore.fetchMap(mapId)
}
</script>

<template>
  <div class="maps-view">
    <!-- Lista de Mapas -->
    <Transition name="fade">
      <div v-if="showMapList" class="maps-list">
        <div class="maps-list__header">
          <div>
            <h2 class="maps-list__title">Atlas do Mundo</h2>
            <p class="maps-list__sub">Explore a cartografia, locais de interesse e sub-mapas.</p>
          </div>
          <button v-if="isMestre" class="btn-gold-sm" @click="openCreateMapModal">
            ➕ Novo Mapa
          </button>
        </div>

        <div v-if="mapsStore.loading" class="list-empty">Carregando cartografia...</div>
        <div v-else-if="mapsStore.maps.length === 0" class="list-empty">
          Nenhum mapa cadastrado neste mundo.
        </div>

        <div v-else class="maps-grid">
          <button v-for="m in mapsStore.maps" :key="m.id" class="map-card" @click="selectMap(m.id)">
            <div class="map-card__preview" :style="{ backgroundImage: `url(${m.image_url})` }" />
            <div class="map-card__info">
              <h4 class="map-card__name">{{ m.title }}</h4>
              <span class="map-card__date">Criado em: {{ new Date(m.created_at).toLocaleDateString() }}</span>
            </div>
          </button>
        </div>
      </div>
    </Transition>

    <!-- Canvas do Mapa Ativo -->
    <Transition name="fade">
      <div v-if="!showMapList && currentMap" class="map-canvas-wrapper">
        <!-- Barra de Ferramentas Superior com Breadcrumbs -->
        <div class="map-toolbar">
          <button class="back-btn" title="Voltar à lista" @click="backToList">
            ⬅ Lista
          </button>

          <!-- Breadcrumbs -->
          <div class="breadcrumbs">
            <template v-for="(crumb, idx) in mapsStore.breadcrumbs" :key="crumb.id">
              <span v-if="idx > 0" class="crumb-separator">➔</span>
              <button
                class="crumb-btn"
                :class="{ 'crumb-btn--active': crumb.id === currentMap.id }"
                @click="openBreadcrumb(crumb.id)"
              >
                {{ crumb.title }}
              </button>
            </template>
          </div>

          <!-- Ações do Mestre e Camadas -->
          <div class="toolbar-actions">
            <button
              class="toolbar-btn"
              :class="{ 'toolbar-btn--active': isDragMode }"
              title="Alterna modo para arrastar coordenadas de pins"
              @click="isDragMode = !isDragMode"
            >
              🖐️ {{ isDragMode ? 'Mover Marcadores ON' : 'Mover Marcadores' }}
            </button>

            <button class="toolbar-btn" @click="openCreatePinModal">
              📍 Novo Marcador
            </button>

            <button v-if="currentMap.layers.length > 0" class="toolbar-btn" @click="showLayerDrawer = !showLayerDrawer">
              🥞 Camadas ({{ currentMap.layers.length }})
            </button>

            <button v-if="isMestre" class="toolbar-btn" title="Editar Mapa" @click="openEditMapModal">
              ✏️ Editar Mapa
            </button>

            <button v-if="isMestre" class="toolbar-btn toolbar-btn--danger" title="Excluir Mapa" @click="handleDeleteMap">
              🗑️
            </button>
          </div>
        </div>

        <!-- Canvas Component -->
        <div class="canvas-container">
          <MapCanvas
            :map-detail="currentMap"
            :is-mestre="isMestre"
            :is-drag-mode="isDragMode"
            @edit-pin="openEditPinModal"
            @delete-pin="handleDeletePin"
            @explore-map="exploreSubMap"
          />
        </div>

        <!-- Layer Drawer (Gaveta Lateral de Camadas) -->
        <Transition name="slide-right">
          <div v-if="showLayerDrawer" class="layer-drawer">
            <div class="drawer-header">
              <h4 class="drawer-title">Camadas de Marcadores</h4>
              <button class="btn-close" @click="showLayerDrawer = false">✕</button>
            </div>
            <div class="layer-list">
              <label v-for="layer in currentMap.layers" :key="layer.id" class="layer-item">
                <input
                  type="checkbox"
                  :checked="mapsStore.activeLayers.has(layer.id)"
                  @change="mapsStore.toggleLayer(layer.id)"
                />
                <span>{{ layer.name }}</span>
              </label>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>

    <!-- Modais -->
    <MapModal
      :show="showMapModal"
      :map-item="editingMap"
      @close="showMapModal = false"
      @save="(map) => selectMap(map.id)"
    />

    <PinModal
      v-if="currentMap"
      :show="showPinModal"
      :map-id="currentMap.id"
      :pin="editingPin"
      :layers="currentMap.layers"
      :maps="mapsStore.maps.filter((m) => m.id !== currentMap?.id)"
      @close="showPinModal = false"
      @save="mapsStore.fetchMap(currentMap.id)"
    />
  </div>
</template>

<style scoped>
.maps-view {
  height: calc(100vh - 56px);
  margin: calc(-1 * var(--space-6)) calc(-1 * var(--space-8));
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

/* Map List */
.maps-list {
  padding: var(--space-6) var(--space-8);
  overflow-y: auto;
  flex: 1;
}

.maps-list__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-6);
}

.maps-list__title {
  font-family: var(--font-display);
  font-size: 1.4rem;
  color: var(--color-gold);
}

.maps-list__sub {
  font-size: 0.85rem;
  color: var(--color-text-dim);
}

.maps-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-4);
}

.map-card {
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
  cursor: pointer;
  text-align: left;
  transition: all var(--transition-fast);
}

.map-card:hover {
  border-color: var(--color-gold-dim);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}

.map-card__preview {
  width: 100%;
  height: 160px;
  background-size: cover;
  background-position: center;
  background-color: var(--color-surface-2);
}

.map-card__info {
  padding: var(--space-3) var(--space-4);
}

.map-card__name {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-gold);
  margin-bottom: 2px;
}

.map-card__date {
  font-size: 0.75rem;
  color: var(--color-text-dim);
}

/* Map Canvas Wrapper */
.map-canvas-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

.map-toolbar {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  z-index: 200;
}

.back-btn {
  padding: 4px 10px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: var(--color-surface-2);
  color: var(--color-text);
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
}

.breadcrumbs {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  overflow-x: auto;
}

.crumb-btn {
  background: none;
  border: none;
  color: var(--color-text-muted);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
}
.crumb-btn:hover { color: var(--color-gold); }
.crumb-btn--active { color: var(--color-gold); font-weight: 700; }
.crumb-separator { color: var(--color-text-dim); font-size: 0.75rem; }

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.toolbar-btn {
  padding: 5px 10px;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text);
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.toolbar-btn:hover {
  border-color: var(--color-gold-dim);
  color: var(--color-gold);
}

.toolbar-btn--active {
  background: var(--color-gold-glow);
  border-color: var(--color-gold);
  color: var(--color-gold);
}

.toolbar-btn--danger:hover {
  border-color: var(--color-danger);
  color: var(--color-danger);
}

.canvas-container {
  flex: 1;
  position: relative;
}

/* Layer Drawer */
.layer-drawer {
  position: absolute;
  top: 50px;
  right: 0;
  width: 220px;
  height: calc(100% - 50px);
  background: var(--color-surface);
  border-left: 1px solid var(--color-border);
  padding: var(--space-4);
  z-index: 300;
  box-shadow: -8px 0 24px rgba(0, 0, 0, 0.5);
}

.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-border);
  padding-bottom: var(--space-2);
}

.drawer-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--color-gold);
  text-transform: uppercase;
}

.btn-close {
  background: none;
  border: none;
  color: var(--color-text-dim);
  cursor: pointer;
}

.layer-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.layer-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  color: var(--color-text);
  cursor: pointer;
}

.btn-gold-sm {
  padding: 6px 14px;
  background: var(--color-gold);
  color: #111827;
  border: none;
  border-radius: var(--radius-sm);
  font-weight: 600;
  font-size: 0.85rem;
  cursor: pointer;
}

.list-empty {
  text-align: center;
  padding: var(--space-8);
  color: var(--color-text-dim);
}
</style>
