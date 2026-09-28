import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:6000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/db': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/db/, ''),
      },
      '/calc': {
        target: 'http://127.0.0.1:7000',
        changeOrigin: true,
        ws: true,
        rewrite: (path) => path.replace(/^\/calc/, ''),
      },
    },
  },
})
