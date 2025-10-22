import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      'api/questions/upload': 'http://localhost:5003',
      'api/questions/': 'http://localhost:5003'

    },
  },
})
