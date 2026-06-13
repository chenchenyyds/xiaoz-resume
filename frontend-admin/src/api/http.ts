import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'

const http: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

http.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('admin_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (resp) => {
    const data = resp.data
    if (data && typeof data === 'object' && 'code' in data) {
      if (data.code === 0) return data.data
      if ([40101, 40102, 40103].includes(data.code)) {
        localStorage.removeItem('admin_token')
        ElMessage.error('登录已过期')
        setTimeout(() => location.href = '/login', 1000)
      } else {
        ElMessage.error(data.message || '操作失败')
      }
      return Promise.reject(new Error(data.message))
    }
    return data
  },
  (err) => {
    const msg = err.response?.data?.message || err.message || '网络异常'
    ElMessage.error(msg)
    return Promise.reject(err)
  }
)

export default http
