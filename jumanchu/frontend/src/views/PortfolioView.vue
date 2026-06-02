<script setup>
import { stocks } from '../data/stocks.js'
import { useWatchlist } from '../composables/useWatchlist.js'
import { useFormat } from '../composables/useFormat.js'

const { watchedCodes } = useWatchlist()
const { formatMoney } = useFormat()

const watchedStocks = stocks.filter((s) => ['005930', 'NVDA'].includes(s.code))
</script>

<template>
  <div>
    <header class="topbar">
      <div>
        <p class="eyebrow">My Portfolio</p>
        <h1>포트폴리오</h1>
      </div>
      <span class="profile-pill">초기 예수금 100,000,000원</span>
    </header>

    <!-- 자산 요약 -->
    <section class="panel portfolio-summary" aria-label="자산 요약">
      <div class="panel-head">
        <div>
          <p class="eyebrow">Portfolio</p>
          <h2>신규 유저 자산 골격</h2>
        </div>
      </div>

      <div class="portfolio-grid">
        <div><span>현금</span><strong>₩100,000,000</strong></div>
        <div><span>보유종목</span><strong>0개</strong></div>
        <div><span>평가손익</span><strong class="is-flat">₩0</strong></div>
      </div>

      <p class="panel-note">
        DB에 계좌·보유·주문 row가 아직 없으므로 첫 화면은 온보딩 완료 뒤 가상 예수금과 추천 행동을
        보여주는 빈 상태가 필요합니다.
      </p>
    </section>

    <!-- 자산 배분 플레이스홀더 -->
    <div class="layout-grid" style="margin-top: 18px;">
      <section class="panel" aria-labelledby="allocation-heading">
        <div class="panel-head">
          <div>
            <p class="eyebrow">Asset Allocation</p>
            <h2 id="allocation-heading">자산 배분</h2>
          </div>
        </div>
        <div class="allocation-placeholder">
          <div class="donut-placeholder">
            <span>보유 종목 없음</span>
          </div>
          <p class="panel-note" style="margin-top: 14px; text-align: center;">
            종목을 매수하면 섹터별 자산 배분 차트가 표시됩니다.
          </p>
        </div>
      </section>

      <!-- 관심종목 빠른 보기 -->
      <section class="panel" aria-labelledby="watchlist-heading">
        <div class="panel-head">
          <div>
            <p class="eyebrow">Watchlist</p>
            <h2 id="watchlist-heading">관심종목 현황</h2>
          </div>
        </div>

        <div class="watch-list">
          <RouterLink
            v-for="stock in watchedStocks"
            :key="stock.code"
            to="/stocks"
            class="watch-link"
          >
            <span>{{ stock.name }}</span>
            <strong>{{ formatMoney(stock.price, stock.currency) }}</strong>
          </RouterLink>
        </div>
      </section>
    </div>

    <!-- 거래 내역 빈 상태 -->
    <section class="panel" style="margin-top: 18px;">
      <div class="panel-head">
        <div>
          <p class="eyebrow">Trade History</p>
          <h2>거래 내역</h2>
        </div>
      </div>
      <div class="empty-state">
        아직 거래 내역이 없습니다. 종목 페이지에서 매수를 시작해보세요.
      </div>
    </section>
  </div>
</template>

<style scoped>
.portfolio-summary {
  margin-bottom: 0;
}

.allocation-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px 0;
}

.donut-placeholder {
  width: 160px;
  height: 160px;
  border-radius: 50%;
  border: 14px dashed rgba(180, 200, 255, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--faint);
  font-size: 13px;
  font-weight: 900;
  text-align: center;
}

.watch-link {
  min-height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--radius);
  background: rgba(255, 255, 255, 0.48);
  backdrop-filter: var(--glass-blur-sm);
  -webkit-backdrop-filter: var(--glass-blur-sm);
  border: 1px solid var(--glass-border);
  box-shadow: var(--glass-shadow);
  color: var(--text);
  margin-bottom: 8px;
  transition: background 0.18s ease;
}

.watch-link:hover {
  background: rgba(255, 255, 255, 0.65);
}

.watch-link strong {
  font-size: 14px;
  color: var(--ink);
}
</style>
