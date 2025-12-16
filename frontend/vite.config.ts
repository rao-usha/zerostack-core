import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        // In Docker, use 'backend:8000' via Docker network
        // Locally, use 'localhost:8000'
        target: process.env.DOCKER_ENV ? 'http://backend:8000' : 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})

