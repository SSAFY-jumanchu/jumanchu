<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppTopnav from './components/layout/AppTopnav.vue'

const route = useRoute()
const isAuthPage = computed(() => ['/login', '/signup', '/onboarding'].includes(route.path))
</script>

<template>
  <div class="app-shell" :class="{ 'auth-mode': isAuthPage }">
    <AppTopnav v-if="!isAuthPage" />
    <main class="main-area">
      <RouterView />
    </main>
  </div>
</template>
