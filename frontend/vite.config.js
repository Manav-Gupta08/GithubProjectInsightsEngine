import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],

  // In development, Vite runs on :5173 and proxies /api/* to Flask on :5000.
  // In production, Flask serves the built dist/ folder directly.
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },

  build: {
    // Output into frontend/dist — Flask's static_folder points here
    outDir: 'dist',
    emptyOutDir: true,
  },
})
