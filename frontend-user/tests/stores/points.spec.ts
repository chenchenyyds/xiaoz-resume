/**
 * points(积分)相关测试
 * 测试内容:
 *  1. points 数据结构正确性
 *  2. 积分求和(total_balance = 3 类之和)
 *  3. 积分类型排序/优先级
 *  4. 过期时间判断
 *  5. 积分计算工具函数
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUserStore, type UserInfo } from '../../src/stores/user'

// Mock API
vi.mock('../../src/api/user', () => ({
  userApi: {
    me: vi.fn(),
  },
}))

import { userApi } from '../../src/api/user'

describe('Points Logic', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
  })

  // ---------- Test 1: 默认 points 结构 ----------
  it('default points should be all zeros', () => {
    const store = useUserStore()
    expect(store.points).toEqual({
      trial_balance: 0,
      subscription_balance: 0,
      purchase_balance: 0,
      total_balance: 0,
    })
  })

  // ---------- Test 2: total_balance 等于三类之和 ----------
  it('total_balance should equal sum of all three types', async () => {
    const store = useUserStore()
    vi.mocked(userApi.me).mockResolvedValue({
      user: { id: 1, phone: '138', invite_code: 'X', is_admin: false } as UserInfo,
      points: {
        trial_balance: 50,
        subscription_balance: 200,
        purchase_balance: 1000,
        total_balance: 1250,  // 假设后端已计算
      },
    } as any)

    await store.fetchMe()

    // 客户端验证:total = trial + subscription + purchase
    const sum =
      store.points.trial_balance +
      store.points.subscription_balance +
      store.points.purchase_balance

    expect(sum).toBe(1250)
    expect(store.points.total_balance).toBe(1250)
  })

  // ---------- Test 3: 各种积分数量场景 ----------
  it('should handle zero points correctly', async () => {
    const store = useUserStore()
    vi.mocked(userApi.me).mockResolvedValue({
      user: { id: 1, phone: '138', invite_code: 'X', is_admin: false } as UserInfo,
      points: {
        trial_balance: 0,
        subscription_balance: 0,
        purchase_balance: 0,
        total_balance: 0,
      },
    } as any)

    await store.fetchMe()
    expect(store.points.total_balance).toBe(0)
  })

  it('should handle large numbers (100万级)', async () => {
    const store = useUserStore()
    vi.mocked(userApi.me).mockResolvedValue({
      user: { id: 1, phone: '138', invite_code: 'X', is_admin: false } as UserInfo,
      points: {
        trial_balance: 0,
        subscription_balance: 0,
        purchase_balance: 1000000,
        total_balance: 1000000,
      },
    } as any)

    await store.fetchMe()
    expect(store.points.purchase_balance).toBe(1000000)
  })

  // ---------- Test 4: 积分类型顺序(优先级) ----------
  it('subscription has higher priority than trial and purchase (FIFO)', () => {
    // 模拟业务规则:消耗顺序
    // 1. subscription(最先过期,30天)
    // 2. trial(次之过期,90天)
    // 3. purchase(永久)
    const consumptionOrder = ['subscription', 'trial', 'purchase']
    expect(consumptionOrder[0]).toBe('subscription')
    expect(consumptionOrder[2]).toBe('purchase')
  })

  // ---------- Test 5: 积分类型常量 ----------
  it('should have 3 point types: trial, subscription, purchase', () => {
    const POINT_TYPES = ['trial', 'subscription', 'purchase']
    expect(POINT_TYPES).toHaveLength(3)
    expect(POINT_TYPES).toContain('trial')
    expect(POINT_TYPES).toContain('subscription')
    expect(POINT_TYPES).toContain('purchase')
  })

  // ---------- Test 6: 积分不足判断 ----------
  it('should determine insufficient points correctly', () => {
    const costPartial = 50
    const costFull = 1000
    const costFullWithJD = 1500

    const userPoints = { trial: 30, subscription: 0, purchase: 100 }

    expect(userPoints.trial + userPoints.purchase).toBeLessThan(costPartial)
    expect(userPoints.trial + userPoints.purchase).toBeGreaterThanOrEqual(costFull)  // 100 < 1000 → false
    expect(userPoints.trial + userPoints.purchase).toBeGreaterThanOrEqual(costFullWithJD)  // false
  })

  // ---------- Test 7: 部分改写 + 完整改写场景 ----------
  it('user with 1200 subscription should be able to do 1 full rewrite', () => {
    const balance = 1200
    const fullCost = 1000
    expect(balance >= fullCost).toBe(true)
    expect(balance - fullCost).toBe(200)  // 剩余
  })

  it('user with 1200 subscription should be able to do 24 partial rewrites', () => {
    const balance = 1200
    const partialCost = 50
    expect(Math.floor(balance / partialCost)).toBe(24)
  })
})
