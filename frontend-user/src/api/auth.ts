import http from './http'

export const authApi = {
  sendSms(phone: string) {
    return http.post('/auth/send-sms', { phone })
  },
  login(phone: string, code: string, invite_code?: string) {
    return http.post('/auth/login', { phone, code, invite_code })
  }
}
