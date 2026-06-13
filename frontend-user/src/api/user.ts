import http from './http'

export const userApi = {
  me() {
    return http.get('/user/me')
  }
}
