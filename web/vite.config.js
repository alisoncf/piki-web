import { fileURLToPath, URL } from 'node:url'

import vue from '@vitejs/plugin-vue'
import { quasar, transformAssetUrls } from '@quasar/vite-plugin'
import { defineConfig } from 'vite'

// Endereço da API em desenvolvimento. O front chama /api/... e o Vite repassa,
// assim não é preciso liberar CORS na API.
const API = process.env.PIKI_API_URL || 'http://localhost:8000'

export default defineConfig({
  plugins: [
    vue({ template: { transformAssetUrls } }),
    quasar({ sassVariables: fileURLToPath(new URL('./src/css/quasar.variables.scss', import.meta.url)) }),
  ],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  server: {
    port: 9000,
    proxy: {
      '/api': { target: API, changeOrigin: true, rewrite: (caminho) => caminho.replace(/^\/api/, '') },
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./tests/preparar.js'],
    server: { deps: { inline: ['quasar'] } },
  },
})
