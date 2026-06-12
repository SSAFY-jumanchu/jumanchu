import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 디자인 프리뷰 전용 — 백엔드 프록시 없음 (UI만 확인하는 용도)
// wire-frame(5173)과 동시에 띄울 수 있게 포트 분리
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5180,
  },
})
