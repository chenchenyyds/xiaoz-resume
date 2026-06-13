/**
 * Home (Workbench) 视图测试
 * 测试内容:
 *  1. 渲染空状态
 *  2. 渲染积分余额卡
 *  3. 显示用户推广码
 *  4. 点击部分改写弹出弹窗
 *  5. 点击完整改写弹出弹窗
 *  6. 文件列表加载
 *  7. 切换 tab 跳转路由
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import Workbench from '../../src/views/Workbench.vue'

// Mock API
vi.mock('../../src/api/files', () => ({
  fileApi: {
    list: vi.fn(),
    upload: vi.fn(),
    remove: vi.fn(),
  },
}))

vi.mock('../../src/api/rewrite', () => ({
  rewriteApi: {
    partial: vi.fn(),
    full: vi.fn(),
  },
}))

vi.mock('../../src/api/user', () => ({
  userApi: {
    me: vi.fn(),
  },
}))

import { fileApi } from '../../src/api/files'
import { userApi } from '../../src/api/user'
import { useUserStore } from '../../src/stores/user'

// Mock Vant 组件(避免 jsdom 环境下的副作用)
vi.mock('vant', async () => {
  const actual = await vi.importActual<any>('vant')
  return {
    ...actual,
    showToast: vi.fn(),
    showDialog: vi.fn(() => Promise.resolve()),
  }
})

// 创建测试用 router
function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: { template: '<div></div>' } },
      { path: '/workbench', component: Workbench },
      { path: '/files', component: { template: '<div></div>' } },
      { path: '/redeem', component: { template: '<div></div>' } },
      { path: '/me', component: { template: '<div></div>' } },
    ],
  })
}

describe('Home (Workbench) View', () => {
  let router: ReturnType<typeof createTestRouter>
  let pinia: ReturnType<typeof createPinia>

  beforeEach(async () => {
    pinia = createPinia()
    setActivePinia(pinia)
    router = createTestRouter()
    await router.push('/workbench')
    await router.isReady()

    localStorage.clear()
    vi.clearAllMocks()

    // 默认 mock
    vi.mocked(userApi.me).mockResolvedValue({
      user: {
        id: 1,
        phone: '13800000000',
        nickname: 'TestUser',
        invite_code: 'TEST1234',
        is_admin: false,
      },
      points: {
        trial_balance: 0,
        subscription_balance: 1200,
        purchase_balance: 100,
        total_balance: 1300,
      },
    } as any)
    vi.mocked(fileApi.list).mockResolvedValue({
      items: [],
      total: 0,
    } as any)
  })

  // ---------- Test 1: 基础渲染 ----------
  it('should render the page with points card', async () => {
    const wrapper = mount(Workbench, {
      global: { plugins: [router, pinia] },
    })

    await flushPromises()

    expect(wrapper.find('.page').exists()).toBe(true)
    expect(wrapper.find('.points-card').exists()).toBe(true)
  })

  // ---------- Test 2: 显示积分余额 ----------
  it('should display total points balance', async () => {
    const wrapper = mount(Workbench, {
      global: { plugins: [router, pinia] },
    })

    await flushPromises()

    const pointsNum = wrapper.find('.points-num')
    expect(pointsNum.exists()).toBe(true)
    expect(pointsNum.text()).toContain('1300')
  })

  // ---------- Test 3: 显示分项积分 ----------
  it('should display 3 sub-balance types (订阅/试用/增购)', async () => {
    const wrapper = mount(Workbench, {
      global: { plugins: [router, pinia] },
    })

    await flushPromises()

    const html = wrapper.html()
    expect(html).toContain('订阅')
    expect(html).toContain('试用')
    expect(html).toContain('增购')
    expect(html).toContain('1200')  // subscription
    expect(html).toContain('100')   // purchase
  })

  // ---------- Test 4: 显示推广码 ----------
  it('should display user invite code', async () => {
    const wrapper = mount(Workbench, {
      global: { plugins: [router, pinia] },
    })

    await flushPromises()

    const html = wrapper.html()
    expect(html).toContain('TEST1234')
    expect(html).toContain('邀请好友')
  })

  // ---------- Test 5: 文件列表空状态 ----------
  it('should show empty state when no files', async () => {
    vi.mocked(fileApi.list).mockResolvedValue({ items: [], total: 0 } as any)

    const wrapper = mount(Workbench, {
      global: { plugins: [router, pinia] },
    })

    await flushPromises()

    expect(fileApi.list).toHaveBeenCalled()
    // 空状态文案
    expect(wrapper.html()).toContain('还没有上传简历')
  })

  // ---------- Test 6: 文件列表非空 ----------
  it('should render file list when files exist', async () => {
    vi.mocked(fileApi.list).mockResolvedValue({
      items: [
        {
          id: 1,
          file_name: '我的简历.docx',
          file_format: 'docx',
          file_url: 'https://oss.example.com/1.docx',
          file_size: 1024 * 50,
          type: 'uploaded',
          with_jd: false,
          created_at: '2025-06-13T10:00:00Z',
        },
        {
          id: 2,
          file_name: 'AI改写_工作经历.docx',
          file_format: 'docx',
          file_url: 'https://oss.example.com/2.docx',
          file_size: 1024 * 30,
          type: 'generated',
          with_jd: false,
          created_at: '2025-06-13T11:00:00Z',
        },
      ],
      total: 2,
    } as any)

    const wrapper = mount(Workbench, {
      global: { plugins: [router, pinia] },
    })

    await flushPromises()

    expect(wrapper.html()).toContain('我的简历.docx')
    expect(wrapper.html()).toContain('AI改写_工作经历.docx')
  })

  // ---------- Test 7: 点击改写功能入口 ----------
  it('should open partial rewrite popup when clicking 部分改写', async () => {
    const wrapper = mount(Workbench, {
      global: { plugins: [router, pinia] },
    })

    await flushPromises()

    // 初始状态:弹窗关闭
    expect(wrapper.vm.showPartial).toBe(false)

    // 点击部分改写
    const items = wrapper.findAll('.van-grid-item')
    expect(items.length).toBeGreaterThanOrEqual(2)

    await items[0].trigger('click')
    expect(wrapper.vm.showPartial).toBe(true)
  })

  it('should open full rewrite popup when clicking 完整改写', async () => {
    const wrapper = mount(Workbench, {
      global: { plugins: [router, pinia] },
    })

    await flushPromises()

    expect(wrapper.vm.showFull).toBe(false)

    const items = wrapper.findAll('.van-grid-item')
    await items[1].trigger('click')
    expect(wrapper.vm.showFull).toBe(true)
  })

  // ---------- Test 8: 充值弹窗 ----------
  it('should open shop popup when clicking 充值', async () => {
    const wrapper = mount(Workbench, {
      global: { plugins: [router, pinia] },
    })

    await flushPromises()

    expect(wrapper.vm.showShop).toBe(false)

    const rechargeBtn = wrapper.find('button.van-button--primary')
    await rechargeBtn.trigger('click')
    expect(wrapper.vm.showShop).toBe(true)
  })

  // ---------- Test 9: 初始挂载调用 API ----------
  it('should call userApi.me and fileApi.list on mount', async () => {
    mount(Workbench, {
      global: { plugins: [router, pinia] },
    })

    await flushPromises()

    expect(userApi.me).toHaveBeenCalled()
    expect(fileApi.list).toHaveBeenCalled()
  })
})
