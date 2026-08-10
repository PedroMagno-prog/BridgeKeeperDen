<script setup lang="ts">
import { computed } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import AppShell from '@/components/ui/AppShell.vue'
import DiceRoller from '@/components/ui/DiceRoller.vue'

const route = useRoute()
const isAuthPage = computed(() => route.meta?.public === true)
</script>

<template>
  <!-- Auth pages: sem shell -->
  <RouterView v-if="isAuthPage" />

  <!-- App pages: com shell completo -->
  <AppShell v-else>
    <RouterView />
    <DiceRoller />
  </AppShell>
</template>

<style>
@import '@/assets/css/main.css';
</style>
