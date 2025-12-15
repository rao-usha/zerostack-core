import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        // In Docker, backend is at 'backend:8000' via Docker network
        // Locally, it's at 'localhost:8000'
        target: 'http://backend:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})

