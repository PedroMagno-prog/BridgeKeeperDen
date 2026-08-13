<script setup lang="ts">
/**
 * Visualizador em Grafo de Conexões (Graph View — Etapa 3).
 */
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useQuestsStore, type GraphNode, type GraphEdge } from '@/stores/quests'
import { useWorldsStore } from '@/stores/worlds'
import { useArticlesStore } from '@/stores/articles'
import VisibilityBadge from '@/components/ui/VisibilityBadge.vue'
import WikilinkText from '@/components/ui/WikilinkText.vue'

interface SimNode extends GraphNode {
  x: number
  y: number
  vx: number
  vy: number
  radius: number
  connectionsCount: number
  folder_id?: number | null
}

const questsStore = useQuestsStore()
const worldsStore = useWorldsStore()
const articlesStore = useArticlesStore()
const router = useRouter()

const canvasRef = ref<HTMLCanvasElement | null>(null)
const selectedNode = ref<SimNode | null>(null)
const hoveredNode = ref<SimNode | null>(null)

// Filtros de Nós
const filterArticles = ref(true)
const filterQuests = ref(true)
const filterMaps = ref(true)
const selectedFolderFilter = ref<number | 'ALL'>('ALL')

import type { FolderTreeNode } from '@/api/folders'

function flattenFolderTree(nodes: FolderTreeNode[], depth = 0): Array<{ id: number; name: string; depth: number }> {
  const result: Array<{ id: number; name: string; depth: number }> = []
  for (const node of nodes) {
    result.push({ id: node.id, name: node.name, depth })
    if (node.children?.length) {
      result.push(...flattenFolderTree(node.children, depth + 1))
    }
  }
  return result
}

const flatFolderList = computed(() => flattenFolderTree(articlesStore.folderTree))

// Câmera
const zoom = ref(1)
const panX = ref(0)
const panY = ref(0)
const isPanning = ref(false)
const dragStart = ref({ x: 0, y: 0 })
const draggingNode = ref<SimNode | null>(null)

let animationFrameId: number | null = null
const simNodes = ref<SimNode[]>([])

const filteredNodes = computed(() => {
  return simNodes.value.filter((n) => {
    if (n.type === 'ARTICLE' && !filterArticles.value) return false
    if (n.type === 'QUEST' && !filterQuests.value) return false
    if ((n.type === 'MAP' || n.type === 'PIN') && !filterMaps.value) return false
    if (
      selectedFolderFilter.value !== 'ALL' &&
      n.type === 'ARTICLE' &&
      n.folder_id !== selectedFolderFilter.value
    ) {
      return false
    }
    return true
  })
})

const activeNodeIds = computed(() => new Set(filteredNodes.value.map((n) => n.id)))

const filteredEdges = computed(() => {
  return questsStore.currentGraph.edges.filter(
    (e) => activeNodeIds.value.has(e.source) && activeNodeIds.value.has(e.target)
  )
})

onMounted(async () => {
  if (!worldsStore.activeWorld) {
    await worldsStore.fetchWorlds()
  }
  await articlesStore.fetchFolderTree()
  await questsStore.fetchWorldGraph()
  initPhysics()
  startAnimation()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (animationFrameId !== null) cancelAnimationFrame(animationFrameId)
  window.removeEventListener('resize', handleResize)
})

function handleResize() {
  if (canvasRef.value) {
    canvasRef.value.width = canvasRef.value.parentElement?.clientWidth || 800
    canvasRef.value.height = canvasRef.value.parentElement?.clientHeight || 600
  }
}

function initPhysics() {
  const width = canvasRef.value?.parentElement?.clientWidth || 800
  const height = canvasRef.value?.parentElement?.clientHeight || 600

  // Conta conexões por nó para determinar o tamanho
  const connCounts: Record<string, number> = {}
  questsStore.currentGraph.edges.forEach((e) => {
    connCounts[e.source] = (connCounts[e.source] || 0) + 1
    connCounts[e.target] = (connCounts[e.target] || 0) + 1
  })

  simNodes.value = questsStore.currentGraph.nodes.map((n, idx) => {
    const angle = (idx / questsStore.currentGraph.nodes.length) * Math.PI * 2
    const dist = 120 + Math.random() * 150
    const connections = connCounts[n.id] || 0
    return {
      ...n,
      x: width / 2 + Math.cos(angle) * dist,
      y: height / 2 + Math.sin(angle) * dist,
      vx: 0,
      vy: 0,
      radius: Math.min(22, Math.max(10, 8 + connections * 3)),
      connectionsCount: connections,
    }
  })

  if (canvasRef.value) {
    canvasRef.value.width = width
    canvasRef.value.height = height
  }
}

function updatePhysics() {
  const nodes = filteredNodes.value
  const edges = filteredEdges.value
  if (!nodes.length) return

  const nodeMap = new Map(nodes.map((n) => [n.id, n]))

  // 1. Repulsão entre nós
  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      const n1 = nodes[i]
      const n2 = nodes[j]
      if (!n1 || !n2) continue
      let dx = n2.x - n1.x
      let dy = n2.y - n1.y
      let dist = Math.sqrt(dx * dx + dy * dy) || 1
      if (dist < 200) {
        const force = (200 - dist) / dist * 0.4
        const fx = dx * force
        const fy = dy * force
        if (n1 !== draggingNode.value) { n1.vx -= fx; n1.vy -= fy }
        if (n2 !== draggingNode.value) { n2.vx += fx; n2.vy += fy }
      }
    }
  }

  // 2. Atração pelas Arestas
  for (const e of edges) {
    const source = nodeMap.get(e.source)
    const target = nodeMap.get(e.target)
    if (source && target) {
      const dx = target.x - source.x
      const dy = target.y - source.y
      const dist = Math.sqrt(dx * dx + dy * dy) || 1
      const force = (dist - 100) * 0.02
      const fx = (dx / dist) * force
      const fy = (dy / dist) * force
      if (source !== draggingNode.value) { source.vx += fx; source.vy += fy }
      if (target !== draggingNode.value) { target.vx -= fx; target.vy -= fy }
    }
  }

  // 3. Amortecimento & Atualização de Posição
  for (const n of nodes) {
    if (n === draggingNode.value) continue
    n.vx *= 0.85
    n.vy *= 0.85
    n.x += n.vx
    n.y += n.vy
  }
}

function drawGraph() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  ctx.clearRect(0, 0, canvas.width, canvas.height)

  ctx.save()
  ctx.translate(panX.value, panY.value)
  ctx.scale(zoom.value, zoom.value)

  const nodes = filteredNodes.value
  const edges = filteredEdges.value
  const nodeMap = new Map(nodes.map((n) => [n.id, n]))

  const activeHoverId = hoveredNode.value?.id || selectedNode.value?.id
  const connectedIds = new Set<string>()

  if (activeHoverId) {
    connectedIds.add(activeHoverId)
    edges.forEach((e) => {
      if (e.source === activeHoverId) connectedIds.add(e.target)
      if (e.target === activeHoverId) connectedIds.add(e.source)
    })
  }

  // Desenha Arestas
  for (const e of edges) {
    const s = nodeMap.get(e.source)
    const t = nodeMap.get(e.target)
    if (s && t) {
      const isHighlighted = activeHoverId ? (connectedIds.has(s.id) && connectedIds.has(t.id)) : false
      ctx.beginPath()
      ctx.moveTo(s.x, s.y)
      ctx.lineTo(t.x, t.y)
      ctx.strokeStyle = isHighlighted ? '#EAB308' : (activeHoverId ? 'rgba(255,255,255,0.05)' : 'rgba(255,255,255,0.18)')
      ctx.lineWidth = isHighlighted ? 2.5 : 1.2
      ctx.stroke()
    }
  }

  // Desenha Nós
  for (const n of nodes) {
    const isDimmed = activeHoverId ? !connectedIds.has(n.id) : false
    const isSelected = selectedNode.value?.id === n.id

    ctx.globalAlpha = isDimmed ? 0.2 : 1.0

    // Cor base do nó
    let fillColor = '#3B82F6' // Article
    if (n.type === 'QUEST') fillColor = '#EAB308'
    else if (n.type === 'MAP' || n.type === 'PIN') fillColor = '#10B981'

    ctx.beginPath()
    ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2)
    ctx.fillStyle = fillColor
    ctx.fill()

    ctx.lineWidth = isSelected ? 3 : 1.5
    ctx.strokeStyle = isSelected ? '#FFFFFF' : 'rgba(255,255,255,0.4)'
    ctx.stroke()

    // Rótulo
    ctx.fillStyle = isDimmed ? 'rgba(255,255,255,0.3)' : '#FFFFFF'
    ctx.font = `${n.radius > 14 ? 'bold ' : ''}11px var(--font-body, sans-serif)`
    ctx.textAlign = 'center'
    ctx.fillText(n.label, n.x, n.y + n.radius + 14)
  }

  ctx.restore()
}

function startAnimation() {
  function loop() {
    updatePhysics()
    drawGraph()
    animationFrameId = requestAnimationFrame(loop)
  }
  loop()
}

// ── Eventos de Mouse no Canvas ───────────────────────────────────────────────

function getCanvasCoords(e: MouseEvent) {
  const rect = canvasRef.value?.getBoundingClientRect()
  if (!rect) return { x: 0, y: 0 }
  return {
    x: (e.clientX - rect.left - panX.value) / zoom.value,
    y: (e.clientY - rect.top - panY.value) / zoom.value,
  }
}

function findNodeAt(x: number, y: number): SimNode | null {
  for (const n of filteredNodes.value) {
    const dx = n.x - x
    const dy = n.y - y
    if (Math.sqrt(dx * dx + dy * dy) <= n.radius + 5) {
      return n
    }
  }
  return null
}

function handleMouseDown(e: MouseEvent) {
  const coords = getCanvasCoords(e)
  const node = findNodeAt(coords.x, coords.y)

  if (node) {
    draggingNode.value = node
    selectedNode.value = node
  } else {
    isPanning.value = true
    dragStart.value = { x: e.clientX - panX.value, y: e.clientY - panY.value }
  }
}

function handleMouseMove(e: MouseEvent) {
  const coords = getCanvasCoords(e)
  if (draggingNode.value) {
    draggingNode.value.x = coords.x
    draggingNode.value.y = coords.y
  } else if (isPanning.value) {
    panX.value = e.clientX - dragStart.value.x
    panY.value = e.clientY - dragStart.value.y
  } else {
    hoveredNode.value = findNodeAt(coords.x, coords.y)
  }
}

function handleMouseUp() {
  isPanning.value = false
  draggingNode.value = null
}

function handleWheel(e: WheelEvent) {
  e.preventDefault()
  const delta = e.deltaY < 0 ? 0.15 : -0.15
  zoom.value = Math.min(2.5, Math.max(0.4, zoom.value + delta))
}

function handleDoubleClick(e: MouseEvent) {
  const coords = getCanvasCoords(e)
  const node = findNodeAt(coords.x, coords.y)
  if (node) {
    navigateToEntity(node)
  }
}

function navigateToEntity(node: SimNode) {
  const parts = node.id.split(':')
  const entityType = parts[0]
  const entityId = parts[1]

  if (entityType === 'article') {
    router.push(`/codex/${entityId}`)
  } else if (entityType === 'quest') {
    router.push(`/quests`)
  } else if (entityType === 'map' || entityType === 'pin') {
    router.push(`/maps`)
  }
}
</script>

<template>
  <div class="graph-view">
    <!-- Header & Controles -->
    <div class="graph-header">
      <div>
        <h2 class="graph-title">Teia de Conexões (Graph View)</h2>
        <p class="graph-sub">Visualização interativa das relações de lore, quests e geografia do mundo.</p>
      </div>

      <div class="filter-controls flex items-center gap-3">
        <!-- Filtro por Pasta -->
        <select
          v-model="selectedFolderFilter"
          class="px-2 py-1 text-xs bg-stone-900 border border-stone-800 rounded text-stone-300 focus:outline-none focus:border-amber-500/50"
        >
          <option value="ALL">Todas as Pastas</option>
          <option
            v-for="folder in flatFolderList"
            :key="folder.id"
            :value="folder.id"
          >
            {{ '—'.repeat(folder.depth) }}{{ folder.depth > 0 ? ' ' : '' }}📁 {{ folder.name }}
          </option>
        </select>

        <label class="filter-check filter-article">
          <input type="checkbox" v-model="filterArticles" />
          <span>📖 Artigos</span>
        </label>
        <label class="filter-check filter-quest">
          <input type="checkbox" v-model="filterQuests" />
          <span>👑 Quests</span>
        </label>
        <label class="filter-check filter-map">
          <input type="checkbox" v-model="filterMaps" />
          <span>🗺️ Mapas / Pins</span>
        </label>
      </div>
    </div>

    <!-- Canvas Principal -->
    <div class="canvas-wrapper">
      <canvas
        ref="canvasRef"
        class="graph-canvas"
        @mousedown="handleMouseDown"
        @mousemove="handleMouseMove"
        @mouseup="handleMouseUp"
        @dblclick="handleDoubleClick"
        @wheel="handleWheel"
      ></canvas>

      <!-- Controles de Zoom -->
      <div class="zoom-controls">
        <button class="zoom-btn" @click="zoom = Math.min(2.5, zoom + 0.2)">+</button>
        <span class="zoom-label">{{ Math.round(zoom * 100) }}%</span>
        <button class="zoom-btn" @click="zoom = Math.max(0.4, zoom - 0.2)">-</button>
        <button class="zoom-btn reset-btn" @click="zoom = 1; panX = 0; panY = 0">🔄</button>
      </div>
    </div>

    <!-- Drawer Flutuante de Resumo do Nó Selecionado -->
    <Transition name="slide-right">
      <div v-if="selectedNode" class="node-drawer">
        <div class="drawer-header">
          <div class="header-type">
            <span class="type-pill" :class="`type-${selectedNode.type.toLowerCase()}`">
              {{ selectedNode.type }}
            </span>
            <VisibilityBadge :visibility="selectedNode.visibility" size="sm" />
          </div>
          <button class="btn-close" @click="selectedNode = null">✕</button>
        </div>

        <h3 class="node-title">{{ selectedNode.label }}</h3>

        <div class="drawer-body">
          <div v-if="selectedNode.is_locked" class="locked-msg">
            🔒 Entidade protegida por Névoa de Guerra Parcial.
          </div>
          <div v-else class="node-stats">
            <span>Conexões ativas: <strong>{{ selectedNode.connectionsCount }}</strong></span>
          </div>
        </div>

        <div class="drawer-footer">
          <button class="btn-action" @click="navigateToEntity(selectedNode)">
            Abrir Entidade ➔
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.graph-view {
  height: calc(100vh - 56px);
  margin: calc(-1 * var(--space-6)) calc(-1 * var(--space-8));
  display: flex;
  flex-direction: column;
  position: relative;
  background: #080A0D;
  overflow: hidden;
}

.graph-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-4) var(--space-8);
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  z-index: 100;
}

.graph-title {
  font-family: var(--font-display);
  font-size: 1.3rem;
  color: var(--color-gold);
  margin: 0;
}

.graph-sub {
  font-size: 0.8rem;
  color: var(--color-text-dim);
}

.filter-controls {
  display: flex;
  gap: var(--space-4);
}

.filter-check {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
  color: var(--color-text-muted);
  cursor: pointer;
}

.filter-check input { accent-color: var(--color-gold); }

.canvas-wrapper {
  flex: 1;
  position: relative;
  width: 100%;
  height: 100%;
}

.graph-canvas {
  width: 100%;
  height: 100%;
  display: block;
  cursor: grab;
}
.graph-canvas:active { cursor: grabbing; }

.zoom-controls {
  position: absolute;
  bottom: 20px;
  right: 20px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 4px;
  z-index: 200;
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
.zoom-label { font-size: 0.7rem; color: var(--color-text-dim); text-align: center; }

.node-drawer {
  position: absolute;
  top: 65px;
  right: 20px;
  width: 300px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.6);
  padding: var(--space-4);
  z-index: 300;
}

.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-2);
}

.header-type {
  display: flex;
  align-items: center;
  gap: 6px;
}

.type-pill {
  font-size: 0.65rem;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
  text-transform: uppercase;
}
.type-article { background: rgba(59, 130, 246, 0.2); color: #3B82F6; }
.type-quest { background: rgba(234, 179, 8, 0.2); color: #EAB308; }
.type-map, .type-pin { background: rgba(16, 185, 129, 0.2); color: #10B981; }

.btn-close {
  background: none;
  border: none;
  color: var(--color-text-dim);
  cursor: pointer;
}

.node-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-gold);
  margin-bottom: var(--space-3);
}

.drawer-body {
  font-size: 0.85rem;
  color: var(--color-text-muted);
  margin-bottom: var(--space-4);
}

.btn-action {
  width: 100%;
  padding: 8px;
  background: var(--color-gold);
  color: #111827;
  border: none;
  border-radius: var(--radius-sm);
  font-weight: 600;
  font-size: 0.85rem;
  cursor: pointer;
}
</style>
