import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        // Docker network: frontend container connects to backend container
        target: 'http://backend:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})

