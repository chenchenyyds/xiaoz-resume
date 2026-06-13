/**
 * auth 相关 store 测试
 * 测试内容:
 *  1. setToken / logout 行为
 *  2. sendSms 验证码发送
 *  3. login 登录/注册(成功/失败)
 *  4. fetchMe 拉取用户信息
 *  5. isLogin 计算属性
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUserStore } from '../../src/stores/user'

// Mock API 模块
vi.mock('../../src/api/auth', () => ({
  authApi: {
    sendSms: vi.fn(),
    login: vi.fn(),
  },
}))

vi.mock('../../src/api/user', () => ({
  userApi: {
    me: vi.fn(),
  },
}))

import { authApi } from '../../src/api/auth'
import { userApi } from '../../src/api/user'

describe('UserStore - Auth', () => {
  beforeEach(() => {
    // 每个测试用例前重置 Pinia + localStorage
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // ---------- Test 1: setToken / logout ----------
  it('setToken should store token in state and localStorage', () => {
    const store = useUserStore()
    expect(store.token).toBe('')
    expect(store.isLogin).toBe(false)

    store.setToken('test-token-abc123')

    expect(store.token).toBe('test-token-abc123')
    expect(store.isLogin).toBe(true)
    expect(localStorage.getItem('token')).toBe('test-token-abc123')
  })

  it('logout should clear token and redirect to /login', () => {
    const store = useUserStore()
    store.setToken('test-token')

    // Mock location.href 赋值
    const originalLocation = window.location
    delete (window as any).location
    ;(window as any).location = { ...originalLocation, href: '' }

    store.logout()

    expect(store.token).toBe('')
    expect(store.user).toBeNull()
    expect(localStorage.getItem('token')).toBeNull()
    expect(window.location.href).toBe('/login')

    // 恢复
    ;(window as any).location = originalLocation
  })

  // ---------- Test 2: sendSms ----------
  it('sendSms should call authApi.sendSms with phone', async () => {
    const store = useUserStore()
    vi.mocked(authApi.sendSms).mockResolvedValue({
      sent: true,
      dev_code: '123456',
    } as any)

    const result = await store.sendSms('13800000000')

    expect(authApi.sendSms).toHaveBeenCalledWith('13800000000')
    expect(authApi.sendSms).toHaveBeenCalledTimes(1)
    expect(result).toEqual({ sent: true, dev_code: '123456' })
  })

  it('sendSms should propagate API errors', async () => {
    const store = useUserStore()
    vi.mocked(authApi.sendSms).mockRejectedValue(new Error('RATE_LIMIT'))

    await expect(store.sendSms('13800000000')).rejects.toThrow('RATE_LIMIT')
  })

  // ---------- Test 3: login ----------
  it('login should set token and fetch user info', async () => {
    const store = useUserStore()
    vi.mocked(authApi.login).mockResolvedValue({
      token: 'jwt-token-xyz',
      user_id: 42,
      is_new: false,
      invite_code: 'ABCD1234',
    } as any)
    vi.mocked(userApi.me).mockResolvedValue({
      user: {
        id: 42,
        phone: '13800000000',
        nickname: 'TestUser',
        invite_code: 'ABCD1234',
        is_admin: false,
      },
      points: {
        trial_balance: 50,
        subscription_balance: 0,
        purchase_balance: 100,
        total_balance: 150,
      },
    } as any)

    const data = await store.login('13800000000', '123456')

    expect(authApi.login).toHaveBeenCalledWith('13800000000', '123456', undefined)
    expect(store.token).toBe('jwt-token-xyz')
    expect(localStorage.getItem('token')).toBe('jwt-token-xyz')
    expect(store.user).not.toBeNull()
    expect(store.user?.id).toBe(42)
    expect(store.points.total_balance).toBe(150)
    expect(data.user_id).toBe(42)
  })

  it('login should pass invite_code to API when provided', async () => {
    const store = useUserStore()
    vi.mocked(authApi.login).mockResolvedValue({
      token: 'token',
      user_id: 1,
      is_new: true,
      invite_code: 'NEWCODE',
    } as any)
    vi.mocked(userApi.me).mockResolvedValue({
      user: { id: 1, phone: '138', invite_code: 'NEWCODE', is_admin: false } as any,
      points: { trial_balance: 0, subscription_balance: 0, purchase_balance: 0, total_balance: 0 },
    } as any)

    await store.login('13800000000', '123456', 'INVITE2025')

    expect(authApi.login).toHaveBeenCalledWith('13800000000', '123456', 'INVITE2025')
  })

  // ---------- Test 4: fetchMe ----------
  it('fetchMe should update user and points from /user/me', async () => {
    const store = useUserStore()
    vi.mocked(userApi.me).mockResolvedValue({
      user: {
        id: 1,
        phone: '13800000001',
        nickname: 'Alice',
        invite_code: 'XYZ',
        is_admin: true,
      },
      points: {
        trial_balance: 10,
        subscription_balance: 200,
        purchase_balance: 1000,
        total_balance: 1210,
      },
    } as any)

    await store.fetchMe()

    expect(userApi.me).toHaveBeenCalledTimes(1)
    expect(store.user?.nickname).toBe('Alice')
    expect(store.user?.is_admin).toBe(true)
    expect(store.points.subscription_balance).toBe(200)
    expect(store.points.purchase_balance).toBe(1000)
  })

  // ---------- Test 5: isLogin computed ----------
  it('isLogin should reflect token state', () => {
    const store = useUserStore()

    expect(store.isLogin).toBe(false)

    store.token = 'manual-set'
    expect(store.isLogin).toBe(true)

    store.token = ''
    expect(store.isLogin).toBe(false)
  })
})
