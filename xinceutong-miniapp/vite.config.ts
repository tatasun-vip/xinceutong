import { defineConfig } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'
import path from 'node:path'

export default defineConfig({
  plugins: [uni()],
  resolve: {
    alias: {
      '@': '/src',
    },
  },
  css: {
    preprocessorOptions: {
      scss: {
        // 所有 .scss / .vue <style lang="scss"> 顶部都自动注入全局变量
        additionalData: `
          @import "@/utils/styles/uni-globals.scss";
        `,
      },
    },
  },
})
