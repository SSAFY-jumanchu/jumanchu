<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppNavbar from './components/AppNavbar.vue'

const route = useRoute()
const isFullscreenPage = computed(() => route.name === 'onboarding')
</script>

<template>
  <div class="app-shell">
    <AppNavbar v-if="!isFullscreenPage" />
    <main class="main-area" :class="{ 'no-nav': isFullscreenPage }">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.main-area.no-nav {
  padding: 0;
}
</style>
