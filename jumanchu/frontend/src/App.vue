<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppSidebar from './components/layout/AppSidebar.vue'

const route = useRoute()
const isAuthPage = computed(() => ['/login', '/signup', '/onboarding'].includes(route.path))
</script>

<template>
  <div class="app-shell" :class="{ 'auth-mode': isAuthPage }">
    <AppSidebar v-if="!isAuthPage" />
    <main class="main-area">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.app-shell.auth-mode {
  grid-template-columns: 1fr;
}
</style>
