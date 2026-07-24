<template>
  <span class="mention-link" :title="type === 'article' ? 'Abrir Artigo' : 'Ver no Mapa'" @click="handleClick">
    <svg v-if="type === 'article'" class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
    </svg>
    <svg v-else class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
    <span class="text"><slot /></span>
  </span>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useWorldStore } from '../../stores/world'

const props = defineProps<{
  id: string
  type: 'article' | 'pin'
}>()

const router = useRouter()
const worldStore = useWorldStore()

function handleClick() {
  const worldId = worldStore.activeWorldId
  if (!worldId) return

  if (props.type === 'article') {
    router.push(`/worlds/${worldId}/codex/${props.id}`)
  } else {
    router.push(`/worlds/${worldId}/maps`)
  }
}
</script>

<style scoped>
.mention-link {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  color: var(--accent-gold);
  background-color: rgba(212, 175, 55, 0.1);
  padding: 0.1rem 0.4rem;
  border-radius: 0.25rem;
  border: 1px solid rgba(212, 175, 55, 0.3);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mention-link:hover {
  background-color: rgba(212, 175, 55, 0.25);
  border-color: var(--accent-gold);
}

.icon {
  width: 0.85rem;
  height: 0.85rem;
}
</style>
