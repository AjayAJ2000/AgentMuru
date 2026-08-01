import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'node',
    include: ['src/**/*.test.{ts,tsx}'],
  },
  build: {
    outDir: '../brickflowui/frontend/dist',
    emptyOutDir: true,
    minify: false,
    cssMinify: false,
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules/recharts')) {
            return 'charts'
          }
          if (
            id.includes('node_modules/react/') ||
            id.includes('node_modules/react-dom/')
          ) {
            return 'vendor'
          }
          return undefined
        },
      },
    },
  },
  server: {
    proxy: {
      '/events': {
        target: 'ws://localhost:8050',
        ws: true,
      },
      '/api': 'http://localhost:8050',
    },
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
    },
  },
})
