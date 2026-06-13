import http from './http'

export const fileApi = {
  upload(file: File, title?: string) {
    const fd = new FormData()
    fd.append('file', file)
    if (title) fd.append('title', title)
    return http.post('/files/upload', fd, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  list() {
    return http.get('/files')
  },
  remove(id: number) {
    return http.delete(`/files/${id}`)
  }
}
