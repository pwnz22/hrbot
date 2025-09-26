import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3001,
    host: true
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets'
  },
  base: process.env.NODE_ENV === 'production' ? '/REPOSITORY_NAME/' : '/'
})