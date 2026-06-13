/**
 * Vitest 全局 setup
 * - 引入 Vue Test Utils 扩展
 * - Mock window.matchMedia(避免 Vant 报错)
 * - Mock IntersectionObserver(Vant LazyRender 需要)
 */
import { vi } from 'vitest'

// 扩展 expect
// import '@vue/test-utils'

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock IntersectionObserver
class MockIntersectionObserver {
  observe = vi.fn()
  unobserve = vi.fn()
  disconnect = vi.fn()
  takeRecords = vi.fn()
  root = null
  rootMargin = ''
  thresholds = []
}
;(globalThis as any).IntersectionObserver = MockIntersectionObserver

// Mock ResizeObserver
class MockResizeObserver {
  observe = vi.fn()
  unobserve = vi.fn()
  disconnect = vi.fn()
}
;(globalThis as any).ResizeObserver = MockResizeObserver

// Mock scrollTo
;(window as any).scrollTo = vi.fn()

// Mock URL.createObjectURL
;(globalThis as any).URL.createObjectURL = vi.fn(() => 'blob:mock-url')
;(globalThis as any).URL.revokeObjectURL = vi.fn()
