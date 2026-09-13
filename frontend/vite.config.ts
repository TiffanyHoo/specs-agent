import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  // 开发期代理到 FastAPI，免去跨域配置；生产可换 nginx
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
