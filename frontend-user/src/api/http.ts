/**
 * Axios 封装 - 统一错误处理 + Token 注入
 */
import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios'
import { showToast, showFailToast } from 'vant'

const http: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 60000,  // 改写可能 30-60s
})

http.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (resp) => {
    const data = resp.data
    if (data && typeof data === 'object' && 'code' in data) {
      if (data.code === 0) {
        return data.data  // 业务成功,直接返回 data
      }
      // 业务失败
      const msg = data.message || '操作失败'
      if (data.code === 40101 || data.code === 40102 || data.code === 40103) {
        localStorage.removeItem('token')
        showFailToast('登录已过期')
        setTimeout(() => location.href = '/login', 1000)
      } else {
        showFailToast(msg)
      }
      return Promise.reject(new Error(msg))
    }
    return data
  },
  (err) => {
    const msg = err.response?.data?.message || err.message || '网络异常'
    showFailToast(msg)
    return Promise.reject(err)
  }
)

export default http
