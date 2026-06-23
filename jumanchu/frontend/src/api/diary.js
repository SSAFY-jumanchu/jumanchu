import client from './client'

// 일지 목록. params: { stock_code, action_type, page, size } → { items, page, size, total }
export const fetchDiaries = (params) => client.get('/diaries/', { params }).then((r) => r.data)
export const fetchDiary = (id) => client.get(`/diaries/${id}/`).then((r) => r.data)

// 작성. payload: { stock_code, action_type, reason_category?, confidence, target_price?, stop_loss_price?, memo? }
export const createDiary = (payload) => client.post('/diaries/', payload).then((r) => r.data)
// 수정(부분 가능)
export const updateDiary = (id, payload) => client.patch(`/diaries/${id}/`, payload).then((r) => r.data)
export const deleteDiary = (id) => client.delete(`/diaries/${id}/`).then((r) => r.data)
