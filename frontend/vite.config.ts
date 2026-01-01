import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        // IMPORTANT: This proxy forwards all /api requests to the backend
        // DO NOT change the target - it must always be http://backend:8000
        // The API client (src/api/client.ts) should use relative URLs (empty baseURL)
        // so that requests like '/api/...' are proxied correctly
        target: 'http://backend:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})

