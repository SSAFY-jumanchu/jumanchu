import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    proxy: {
      // Django 백엔드(runserver :8000)로 프록시 — 쿠키(refresh_token)도 same-origin으로 전달됨
      // 127.0.0.1 고정: 'localhost'면 Windows에서 IPv6(::1) 먼저 시도→runserver는 IPv4만 리슨→
      //               연결이 ~2s 막혔다 폴백(요청마다 2초 지연). IPv4 직지정으로 회피.
      // 다른 포트로 띄웠으면: VITE_BACKEND_URL=http://127.0.0.1:8001 npm run dev
      '/api': {
        target: process.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
