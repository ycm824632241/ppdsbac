import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        // 明确写 127.0.0.1 而非 localhost
        // Node 18+ 将 localhost 解析为 ::1 (IPv6)，而 Flask 默认只监听 IPv4
        target: 'http://127.0.0.1:5000',
        changeOrigin: true
      }
    }
  }
})
