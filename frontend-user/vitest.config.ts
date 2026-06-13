/**
 * Vitest 配置 - 小Z简历用户端
 *
 * 运行:
 *   npm run test          # 监听模式
 *   npm run test:run      # 单次跑
 *   npm run test:coverage # 生成覆盖率
 */
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
    include: ['tests/**/*.{spec,test}.{ts,js}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'json', 'lcov'],
      reportsDirectory: './coverage',
      include: ['src/**/*.{ts,vue}'],
      exclude: [
        'src/main.ts',
        'src/**/index.ts',
        'src/**/*.d.ts',
      ],
    },
  },
})
