import http from './http'

export const rewriteApi = {
  partial(
    text: string,
    title?: string,
    style_hint?: string,
    template_code?: string,
    style_options?: { font_size?: number; line_height?: number; section_gap?: number }
  ) {
    return http.post('/rewrite/partial', { text, title, style_hint, template_code, style_options })
  },
  full(
    file_id: number,
    jd_text?: string,
    style_hint?: string,
    template_code?: string,
    style_options?: { font_size?: number; line_height?: number; section_gap?: number }
  ) {
    return http.post('/rewrite/full', { file_id, jd_text, style_hint, template_code, style_options })
  },
  templates() {
    return http.get('/rewrite/templates')
  }
}
