import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/auth': 'http://localhost:8000',
      '/documents': 'http://localhost:8000',
      '/emails': 'http://localhost:8000',
      '/progress': 'http://localhost:8000',
      '/view-api': 'http://localhost:8000',
      '/security': 'http://localhost:8000',
      '/leak': 'http://localhost:8000',
      '/activity': 'http://localhost:8000',
    }
  }
})
