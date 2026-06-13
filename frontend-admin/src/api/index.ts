import http from './http'

// 后台 4 个模块的 API
export const dashboardApi = {
  overview() {
    return http.get('/admin/dashboard/overview')
  }
}

export const adminOrderApi = {
  list(params: any) {
    return http.get('/admin/orders', { params })
  },
  detail(orderNo: string) {
    return http.get(`/admin/orders/${orderNo}`)
  },
  refund(orderNo: string, amount: number | null, reason: string) {
    return http.post(`/admin/orders/${orderNo}/refund`, { amount, reason })
  }
}

export const adminCodeApi = {
  generate(type: string, count: number, valid_days: number = 365) {
    return http.post('/admin/codes/generate', { type, count, valid_days })
  },
  list(params: any) {
    return http.get('/admin/codes', { params })
  },
  revoke(id: number) {
    return http.post(`/admin/codes/${id}/revoke`)
  },
  exportUrl(batch_id: string) {
    return `/api/admin/codes/export?batch_id=${batch_id}`
  }
}

export const adminUserApi = {
  list(params: any) {
    return http.get('/admin/users', { params })
  },
  detail(id: number) {
    return http.get(`/admin/users/${id}`)
  },
  disable(id: number, reason?: string) {
    return http.post(`/admin/users/${id}/disable`, { reason })
  },
  enable(id: number) {
    return http.post(`/admin/users/${id}/enable`)
  },
  adjustPoints(id: number, change: number, point_type: string, reason: string) {
    return http.post(`/admin/users/${id}/adjust-points`, { change, point_type, reason })
  }
}

export const authApi = {
  login(phone: string, code: string) {
    return http.post('/auth/login', { phone, code })
  }
}
