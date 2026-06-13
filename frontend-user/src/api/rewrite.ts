import http from './http'

export const rewriteApi = {
  partial(text: string, title?: string, style_hint?: string) {
    return http.post('/rewrite/partial', { text, title, style_hint })
  },
  full(file_id: number, jd_text?: string, style_hint?: string) {
    return http.post('/rewrite/full', { file_id, jd_text, style_hint })
  }
}
