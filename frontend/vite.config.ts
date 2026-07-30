import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5600,
    strictPort: true,
  },
  preview: {
    port: 5600,
    strictPort: true,
  },
})
