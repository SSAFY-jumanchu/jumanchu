import client from './client'

// 글 목록. params: { stock_code, category, sort: 'latest'|'popular', page, size } → { items, page, size, total }
export const fetchPosts = (params) => client.get('/posts/', { params }).then((r) => r.data)
export const fetchPost = (id) => client.get(`/posts/${id}/`).then((r) => r.data)

// 글 작성. payload: { stock_code, category?, title, body }
export const createPost = (payload) => client.post('/posts/', payload).then((r) => r.data)
export const updatePost = (id, payload) => client.patch(`/posts/${id}/`, payload).then((r) => r.data)
export const deletePost = (id) => client.delete(`/posts/${id}/`).then((r) => r.data)

// 좋아요 토글 → { liked, like_count }
export const togglePostLike = (id) => client.post(`/posts/${id}/like/`).then((r) => r.data)

// 댓글
export const fetchComments = (postId, params) =>
  client.get(`/posts/${postId}/comments/`, { params }).then((r) => r.data)
export const createComment = (postId, body) =>
  client.post(`/posts/${postId}/comments/`, { body }).then((r) => r.data)
export const toggleCommentLike = (id) => client.post(`/comments/${id}/like/`).then((r) => r.data)

// 팔로우
export const followUser = (userId) => client.post(`/users/${userId}/follow/`).then((r) => r.data)
export const unfollowUser = (userId) => client.delete(`/users/${userId}/follow/`).then((r) => r.data)
