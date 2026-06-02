<script setup>
import { ref } from 'vue'

const diaryCount = ref(2)
const mbtiThreshold = 5

const diaries = [
  { id: 1, stock: '삼성전자', action: '관심', date: '2026-05-30', reason: '배당주 포트폴리오 편입 검토. 전기전자 섹터 비중 늘리고 싶음.' },
  { id: 2, stock: 'NVDA', action: '관심', date: '2026-05-29', reason: 'AI 반도체 수요 지속. 고변동 감수하고 성장 기대.' },
]
</script>

<template>
  <div>
    <header class="topbar">
      <div>
        <p class="eyebrow">My Profile</p>
        <h1>프로필</h1>
      </div>
    </header>

    <div class="profile-layout">
      <!-- 유저 정보 -->
      <section class="panel user-card" aria-label="유저 정보">
        <div class="avatar-area">
          <div class="avatar-circle">🙂</div>
          <div>
            <h2 class="user-name">송호영</h2>
            <p class="user-email">song82091619@gmail.com</p>
            <span class="profile-pill" style="margin-top: 8px; display: inline-flex;">균형형 투자자</span>
          </div>
        </div>

        <div class="user-stats">
          <div class="user-stat">
            <strong>{{ diaryCount }}</strong>
            <span>투자 일기</span>
          </div>
          <div class="user-stat">
            <strong>2</strong>
            <span>관심종목</span>
          </div>
          <div class="user-stat">
            <strong>0</strong>
            <span>총 매매</span>
          </div>
        </div>
      </section>

      <!-- 투자 MBTI -->
      <section class="panel mbti-card" aria-label="투자 MBTI">
        <div class="panel-head">
          <div>
            <p class="eyebrow">Investment MBTI</p>
            <h2>나의 투자 성향</h2>
          </div>
        </div>

        <div v-if="diaryCount >= mbtiThreshold" class="mbti-result">
          <div class="mbti-type">ESTJ형</div>
          <p class="mbti-desc">체계적이고 계획적인 투자자. 안정적 수익을 추구하며 분산 투자를 선호합니다.</p>
        </div>

        <div v-else class="mbti-pending">
          <div class="mbti-lock">🔒</div>
          <p>투자 일기 <strong>{{ diaryCount }}/{{ mbtiThreshold }}</strong>개 작성 후 리포트가 생성됩니다.</p>
          <RouterLink to="/community" class="mbti-cta">일기 작성하러 가기 →</RouterLink>
        </div>
      </section>
    </div>

    <!-- 최근 투자 일기 -->
    <section class="panel diary-section" aria-labelledby="diary-heading">
      <div class="panel-head">
        <div>
          <p class="eyebrow">Investment Diary</p>
          <h2 id="diary-heading">투자 일기</h2>
        </div>
        <button class="diary-write-btn primary-action" type="button">+ 일기 작성</button>
      </div>

      <div class="diary-list">
        <article v-for="diary in diaries" :key="diary.id" class="diary-item">
          <div class="diary-header">
            <span class="diary-stock">{{ diary.stock }}</span>
            <span class="diary-action" :class="`action-${diary.action}`">{{ diary.action }}</span>
            <span class="diary-date">{{ diary.date }}</span>
          </div>
          <p class="diary-reason">{{ diary.reason }}</p>
        </article>
      </div>

      <div class="empty-state" v-if="diaries.length === 0">
        아직 작성한 일기가 없습니다. 첫 번째 투자 이유를 기록해보세요.
      </div>
    </section>
  </div>
</template>

<style scoped>
.profile-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(280px, 380px);
  gap: 18px;
  margin-bottom: 18px;
}

.user-card {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.avatar-area {
  display: flex;
  align-items: center;
  gap: 16px;
}

.avatar-circle {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent) 0%, var(--purple) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  flex-shrink: 0;
  box-shadow: 0 4px 16px rgba(49, 93, 255, 0.3);
}

.user-name {
  margin: 0;
  font-size: 22px;
  color: var(--ink);
}

.user-email {
  margin: 4px 0 0;
  color: var(--muted);
  font-size: 13px;
}

.user-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1px;
  overflow: hidden;
  border-radius: var(--radius);
  background: rgba(180, 200, 255, 0.3);
  border: 1px solid var(--glass-border);
}

.user-stat {
  padding: 14px;
  background: rgba(255, 255, 255, 0.55);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.user-stat strong {
  font-size: 24px;
  color: var(--ink);
}

.user-stat span {
  font-size: 12px;
  color: var(--muted);
  font-weight: 900;
}

.mbti-result {
  text-align: center;
  padding: 16px 0;
}

.mbti-type {
  font-size: 52px;
  font-weight: 900;
  letter-spacing: -2px;
  background: linear-gradient(135deg, var(--accent) 0%, var(--purple) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
  margin-bottom: 12px;
}

.mbti-desc {
  color: var(--muted);
  font-size: 14px;
  line-height: 1.55;
  word-break: keep-all;
  margin: 0;
}

.mbti-pending {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 16px 0;
  text-align: center;
}

.mbti-lock {
  font-size: 40px;
}

.mbti-pending p {
  margin: 0;
  color: var(--muted);
  font-size: 14px;
  line-height: 1.55;
}

.mbti-cta {
  display: inline-flex;
  align-items: center;
  padding: 8px 16px;
  border-radius: 999px;
  background: rgba(49, 93, 255, 0.1);
  border: 1px solid rgba(49, 93, 255, 0.25);
  color: var(--accent);
  font-size: 13px;
  font-weight: 900;
  transition: background 0.18s ease;
}

.mbti-cta:hover {
  background: rgba(49, 93, 255, 0.18);
}

.diary-section {
  margin-top: 0;
}

.diary-write-btn {
  min-width: 100px;
  width: auto;
  min-height: 36px;
  font-size: 13px;
}

.diary-list {
  display: grid;
  gap: 10px;
}

.diary-item {
  padding: 14px;
  border-radius: var(--radius);
  background: rgba(255, 255, 255, 0.48);
  border: 1px solid var(--glass-border);
  box-shadow: var(--glass-shadow);
}

.diary-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.diary-stock {
  font-size: 14px;
  font-weight: 900;
  color: var(--ink);
}

.diary-action {
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 900;
}

.action-관심 {
  background: rgba(49, 93, 255, 0.1);
  border: 1px solid rgba(49, 93, 255, 0.2);
  color: var(--accent);
}

.action-매수 {
  background: rgba(15, 159, 110, 0.1);
  border: 1px solid rgba(15, 159, 110, 0.2);
  color: var(--positive);
}

.action-매도 {
  background: rgba(207, 61, 61, 0.1);
  border: 1px solid rgba(207, 61, 61, 0.2);
  color: var(--negative);
}

.diary-date {
  margin-left: auto;
  color: var(--faint);
  font-size: 12px;
}

.diary-reason {
  margin: 0;
  color: var(--text);
  font-size: 13px;
  line-height: 1.55;
  word-break: keep-all;
}

@media (max-width: 900px) {
  .profile-layout {
    grid-template-columns: 1fr;
  }
}
</style>
