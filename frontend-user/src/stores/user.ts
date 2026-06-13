import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { userApi } from '../api/user'
import { authApi } from '../api/auth'

export interface UserInfo {
  id: number
  phone: string
  nickname: string
  invite_code: string
  is_admin: boolean
  total_balance?: number
}

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(localStorage.getItem('token') || '')
  const user = ref<UserInfo | null>(null)
  const points = ref<{ trial_balance: number; subscription_balance: number; purchase_balance: number; total_balance: number }>({
    trial_balance: 0, subscription_balance: 0, purchase_balance: 0, total_balance: 0
  })

  const isLogin = computed(() => !!token.value)

  function setToken(t: string) {
    token.value = t
    localStorage.setItem('token', t)
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    location.href = '/login'
  }

  async function fetchMe() {
    const data: any = await userApi.me()
    user.value = data.user
    points.value = data.points
  }

  async function sendSms(phone: string) {
    return authApi.sendSms(phone)
  }

  async function login(phone: string, code: string, invite_code?: string) {
    const data: any = await authApi.login(phone, code, invite_code)
    setToken(data.token)
    await fetchMe()
    return data
  }

  return { token, user, points, isLogin, setToken, logout, fetchMe, sendSms, login }
})
