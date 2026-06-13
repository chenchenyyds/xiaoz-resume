import http from './http'

export const productApi = {
  list() {
    return http.get('/products')
  }
}

export const orderApi = {
  create(product_code: string, invite_code?: string) {
    return http.post('/orders', { product_code, invite_code })
  },
  payUrl(order_no: string) {
    return http.get(`/orders/${order_no}/pay-url`)
  }
}

export const redeemApi = {
  activate(code: string) {
    return http.post('/redeem', { code })
  }
}
