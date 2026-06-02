<script setup>
import { ref } from 'vue'

const posts = [
  {
    id: 1,
    author: '준수최',
    date: '2026-05-31',
    title: '나의 포트폴리오',
    body: '시작은 미약하지만 앞날은 창대하리라\n\n삼성전자를 첫 매수했습니다. 분기 배당과 HBM 모멘텀을 보고 결정했어요.',
    likes: 12,
    comments: 5,
    tags: ['#삼성전자', '#첫매수', '#초보'],
  },
  {
    id: 2,
    author: '주식러버',
    date: '2026-05-30',
    title: 'NVIDIA 지금 들어가도 될까요?',
    body: '최근 AI 반도체 수요가 계속 늘고 있는데, NVDA 현재가 214불이 매력적으로 보입니다. 의견 부탁드려요!',
    likes: 28,
    comments: 14,
    tags: ['#NVDA', '#AI반도체', '#미국주식'],
  },
  {
    id: 3,
    author: '균형투자자',
    date: '2026-05-29',
    title: '현대차 + SK하이닉스 분산 전략',
    body: '국내주 중심으로 전기차와 AI 반도체를 동시에 노리는 포트폴리오를 구성해봤어요.',
    likes: 9,
    comments: 3,
    tags: ['#현대차', '#SK하이닉스', '#분산투자'],
  },
]

const trendingTags = ['#삼성전자', '#NVDA', '#AI반도체', '#초보', '#분산투자', '#미국주식', '#HBM', '#전기차']
</script>

<template>
  <div>
    <header class="topbar">
      <div>
        <p class="eyebrow">Community</p>
        <h1>커뮤니티</h1>
      </div>
      <div class="top-actions">
        <label class="search-box">
          <span>검색</span>
          <input type="search" placeholder="게시글, 종목 태그 검색" />
        </label>
        <button class="primary-action write-btn" type="button">글쓰기</button>
      </div>
    </header>

    <div class="community-layout">
      <!-- 게시글 목록 -->
      <section aria-label="게시글 목록">
        <div class="post-list">
          <article v-for="post in posts" :key="post.id" class="panel post-card">
            <div class="post-meta">
              <span class="post-author">{{ post.author }}</span>
              <span class="post-date">{{ post.date }}</span>
            </div>
            <h3 class="post-title">{{ post.title }}</h3>
            <p class="post-body">{{ post.body }}</p>
            <div class="post-tags">
              <span v-for="tag in post.tags" :key="tag" class="post-tag">{{ tag }}</span>
            </div>
            <div class="post-footer">
              <button type="button" class="post-action">♥ {{ post.likes }}</button>
              <button type="button" class="post-action">💬 {{ post.comments }}</button>
            </div>
          </article>
        </div>
      </section>

      <!-- 사이드바 -->
      <aside class="community-sidebar" aria-label="커뮤니티 사이드바">
        <section class="panel" aria-labelledby="trending-tags-heading">
          <div class="panel-head">
            <div>
              <p class="eyebrow">Trending</p>
              <h2 id="trending-tags-heading">인기 태그</h2>
            </div>
          </div>
          <div class="sector-cloud">
            <button v-for="tag in trendingTags" :key="tag" type="button">{{ tag }}</button>
          </div>
        </section>

        <section class="panel" style="margin-top: 14px;" aria-labelledby="popular-heading">
          <div class="panel-head">
            <div>
              <p class="eyebrow">Popular</p>
              <h2 id="popular-heading">오늘의 인기글</h2>
            </div>
          </div>
          <div class="popular-list">
            <button v-for="post in posts" :key="post.id" type="button" class="popular-item">
              <span class="popular-title">{{ post.title }}</span>
              <span class="popular-likes">♥ {{ post.likes }}</span>
            </button>
          </div>
        </section>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.community-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 280px;
  gap: 18px;
  align-items: start;
}

.post-list {
  display: grid;
  gap: 14px;
}

.post-card {
  transition: background 0.18s ease;
}

.post-card:hover {
  background: rgba(255, 255, 255, 0.72);
}

.post-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}

.post-author {
  color: var(--ink);
  font-size: 13px;
  font-weight: 900;
}

.post-date {
  color: var(--faint);
  font-size: 12px;
}

.post-title {
  margin: 0 0 8px;
  font-size: 18px;
  color: var(--ink);
  line-height: 1.3;
}

.post-body {
  margin: 0 0 12px;
  color: var(--text);
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-line;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.post-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}

.post-tag {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(49, 93, 255, 0.08);
  border: 1px solid rgba(49, 93, 255, 0.18);
  color: var(--accent);
  font-size: 12px;
  font-weight: 900;
}

.post-footer {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-top: 10px;
  border-top: 1px solid var(--line);
}

.post-action {
  min-height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  border: 1px solid var(--glass-border);
  background: rgba(255, 255, 255, 0.48);
  color: var(--muted);
  font-size: 13px;
  font-weight: 900;
  transition: background 0.18s ease, color 0.18s ease;
}

.post-action:hover {
  background: rgba(255, 255, 255, 0.72);
  color: var(--ink);
}

.write-btn {
  min-width: 90px;
  min-height: 36px;
  width: auto;
  font-size: 13px;
}

.popular-list {
  display: grid;
  gap: 6px;
}

.popular-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-height: 40px;
  padding: 8px 10px;
  border-radius: var(--radius);
  background: rgba(255, 255, 255, 0.42);
  border: 1px solid var(--glass-border);
  color: var(--text);
  font-size: 13px;
  text-align: left;
  transition: background 0.18s ease;
}

.popular-item:hover {
  background: rgba(255, 255, 255, 0.65);
}

.popular-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 900;
  color: var(--ink);
}

.popular-likes {
  flex-shrink: 0;
  color: var(--negative);
  font-size: 12px;
  font-weight: 900;
}

@media (max-width: 900px) {
  .community-layout {
    grid-template-columns: 1fr;
  }
}
</style>
