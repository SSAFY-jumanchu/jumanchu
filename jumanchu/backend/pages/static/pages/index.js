const questions = JSON.parse(document.getElementById('survey-questions').textContent)
const sectors = JSON.parse(document.getElementById('sector-options').textContent)
const holdingPeriods = JSON.parse(document.getElementById('holding-period-options').textContent)
const recommendations = JSON.parse(document.getElementById('recommendation-data').textContent)
const onboardingApiUrl = JSON.parse(document.getElementById('onboarding-api-url').textContent)

const state = {
  answers: {},
  currentStep: 0,
  selectedSector: sectors[0],
  preferredPeriod: 12,
  deckIndex: 0,
  deck: [],
}

const riskProfiles = {
  CONSERVATIVE: {
    code: 'CONSERVATIVE',
    label: '안정형',
    english: 'Conservative',
    description: '손실 방어와 꾸준한 현금 흐름을 먼저 확인하는 유형입니다.',
    gradient: 'linear-gradient(135deg, #26d39b 0%, #38bdf8 100%)',
  },
  BALANCED: {
    code: 'BALANCED',
    label: '중립형',
    english: 'Balanced',
    description: '안정성과 성장성을 함께 비교하며 비중을 조절하는 유형입니다.',
    gradient: 'linear-gradient(135deg, #38bdf8 0%, #8b5cf6 100%)',
  },
  AGGRESSIVE: {
    code: 'AGGRESSIVE',
    label: '공격형',
    english: 'Aggressive',
    description: '높은 변동성을 감수하고 성장 모멘텀을 적극적으로 찾는 유형입니다.',
    gradient: 'linear-gradient(135deg, #ff365f 0%, #ff3d8b 48%, #8b5cf6 100%)',
  },
}

const elements = {
  overlay: document.querySelector('[data-onboarding-overlay]'),
  onboardingCard: document.querySelector('[data-onboarding-card]'),
  onboardingLoading: document.querySelector('[data-onboarding-loading]'),
  loadingTitle: document.querySelector('[data-loading-title]'),
  loadingCopy: document.querySelector('[data-loading-copy]'),
  progressText: document.querySelector('[data-progress-text]'),
  totalScore: document.querySelector('[data-total-score]'),
  riskLabel: document.querySelector('[data-risk-label]'),
  riskDescription: document.querySelector('[data-risk-description]'),
  profileCard: document.querySelector('[data-profile-card]'),
  stepLabel: document.querySelector('[data-step-label]'),
  questionTitle: document.querySelector('[data-question-title]'),
  questionCaption: document.querySelector('[data-question-caption]'),
  scoreRing: document.querySelector('[data-score-ring]'),
  progressBar: document.querySelector('[data-progress-bar]'),
  optionList: document.querySelector('[data-option-list]'),
  sectorList: document.querySelector('[data-sector-list]'),
  periodList: document.querySelector('[data-period-list]'),
  prevButton: document.querySelector('[data-prev-button]'),
  nextButton: document.querySelector('[data-next-button]'),
  mainProfileCard: document.querySelector('[data-main-profile-card]'),
  riskEnglish: document.querySelector('[data-risk-english]'),
  mainRiskLabel: document.querySelector('[data-main-risk-label]'),
  mainRiskDescription: document.querySelector('[data-main-risk-description]'),
  algorithmName: document.querySelector('[data-algorithm-name]'),
  algorithmDetail: document.querySelector('[data-algorithm-detail]'),
  deckCount: document.querySelector('[data-deck-count]'),
  deckTitle: document.querySelector('[data-deck-title]'),
  swipeDeck: document.querySelector('[data-swipe-deck]'),
  passButton: document.querySelector('[data-pass-button]'),
  saveButton: document.querySelector('[data-save-button]'),
  likeButton: document.querySelector('[data-like-button]'),
  reopenButton: document.querySelector('[data-reopen-onboarding]'),
}

function answeredCount() {
  return questions.filter((question) => state.answers[question.id]).length
}

function weightedBreakdown() {
  return questions.reduce((breakdown, question) => {
    const score = Number(state.answers[question.id] || 0)
    breakdown[question.id] = score * (question.weight || 1)
    return breakdown
  }, {})
}

function totalScore() {
  return Object.values(weightedBreakdown()).reduce((sum, score) => sum + score, 0)
}

function riskProfile() {
  const score = totalScore()

  if (score <= 13) {
    return riskProfiles.CONSERVATIVE
  }
  if (score <= 22) {
    return riskProfiles.BALANCED
  }
  return riskProfiles.AGGRESSIVE
}

function progressPercent() {
  return Math.round((answeredCount() / questions.length) * 100)
}

function currentQuestion() {
  return questions[state.currentStep]
}

function createButton(text, className, onClick) {
  const button = document.createElement('button')
  button.type = 'button'
  button.className = className
  button.textContent = text
  button.addEventListener('click', onClick)
  return button
}

function renderChoices() {
  elements.sectorList.innerHTML = ''
  sectors.forEach((sector) => {
    const button = createButton(sector, state.selectedSector === sector ? 'active' : '', () => {
      state.selectedSector = sector
      renderOnboarding()
    })
    elements.sectorList.appendChild(button)
  })

  elements.periodList.innerHTML = ''
  holdingPeriods.forEach((period) => {
    const button = createButton(period.label, state.preferredPeriod === period.value ? 'active' : '', () => {
      state.preferredPeriod = period.value
      renderOnboarding()
    })
    elements.periodList.appendChild(button)
  })
}

function renderQuestion() {
  const question = currentQuestion()

  elements.stepLabel.textContent = question.label
  elements.questionTitle.textContent = question.title
  elements.questionCaption.textContent = question.caption
  elements.optionList.innerHTML = ''

  question.options.forEach((option) => {
    const button = document.createElement('button')
    button.type = 'button'
    button.className = `answer-option${state.answers[question.id] === option.score ? ' selected' : ''}`
    button.innerHTML = `
      <span class="option-score">${option.score}점</span>
      <span class="option-copy">
        <strong>${option.title}</strong>
        <small>${option.detail}</small>
      </span>
    `
    button.addEventListener('click', () => {
      state.answers[question.id] = option.score
      renderOnboarding()
    })
    elements.optionList.appendChild(button)
  })
}

function renderSummary() {
  const profile = riskProfile()
  const progress = progressPercent()
  const score = totalScore()

  elements.progressText.textContent = `${progress}%`
  elements.totalScore.textContent = String(score)
  elements.scoreRing.textContent = String(score)
  elements.progressBar.style.width = `${progress}%`
  elements.riskLabel.textContent = profile.label
  elements.riskDescription.textContent = profile.description
  elements.profileCard.style.setProperty('--profile-gradient', profile.gradient)
}

function renderActions() {
  const question = currentQuestion()
  const selected = question ? Boolean(state.answers[question.id]) : false

  elements.prevButton.disabled = state.currentStep === 0
  elements.nextButton.disabled = !selected
  elements.nextButton.textContent = state.currentStep === questions.length - 1 ? '매칭 시작' : '다음'
}

function renderOnboarding() {
  renderSummary()
  renderChoices()
  renderQuestion()
  renderActions()
}

function sortedDeckForProfile(profile) {
  const pool = [...(recommendations[profile.code] || [])]
  return pool.sort((left, right) => {
    const leftScore = left.sector === state.selectedSector ? 1 : 0
    const rightScore = right.sector === state.selectedSector ? 1 : 0
    if (leftScore !== rightScore) {
      return rightScore - leftScore
    }
    return right.match - left.match
  })
}

function buildDeck() {
  const profile = riskProfile()
  state.deck = sortedDeckForProfile(profile)
  state.deckIndex = 0
}

function renderMainProfile() {
  const profile = riskProfile()
  elements.mainProfileCard.style.setProperty('--profile-gradient', profile.gradient)
  elements.riskEnglish.textContent = profile.english
  elements.mainRiskLabel.textContent = profile.label
  elements.mainRiskDescription.textContent = profile.description
  elements.algorithmName.textContent = `${profile.label} · ${state.selectedSector} 우선 매칭`
  elements.algorithmDetail.textContent = `${state.preferredPeriod}개월 보유 관점으로 ${state.selectedSector} 종목을 먼저 정렬했습니다.`
}

function stockCardTemplate(stock) {
  return `
    <article class="match-card" style="--card-gradient: ${stock.gradient}">
      <div class="card-top">
        <span class="stock-badge">${stock.theme}</span>
        <div class="match-score">
          <strong>${stock.match}</strong>
          <span>match</span>
        </div>
      </div>
      <div class="stock-main">
        <h3>${stock.name}</h3>
        <p>${stock.code} · ${stock.sector}</p>
      </div>
      <div class="stock-detail-grid">
        <div>
          <span>현재가</span>
          <strong>${stock.price}</strong>
        </div>
        <div>
          <span>오늘 흐름</span>
          <strong>${stock.change}</strong>
        </div>
      </div>
      <p class="stock-reason">${stock.reason}</p>
    </article>
  `
}

function renderDeck() {
  const profile = riskProfile()
  const current = state.deck[state.deckIndex]
  const total = state.deck.length

  elements.deckCount.textContent = total ? `${state.deckIndex + 1} / ${total}` : '0 / 0'
  elements.deckTitle.textContent = total
    ? `${state.selectedSector} 중심 ${profile.label} 추천`
    : '추천 후보가 없습니다'

  if (!current) {
    elements.swipeDeck.innerHTML = `
      <article class="empty-card">
        <span>DONE</span>
        <strong>오늘의 매칭을 모두 봤어요</strong>
        <p>성향을 다시 분석하거나 관심 섹터를 바꿔 새 후보를 열어보세요.</p>
      </article>
    `
    return
  }

  elements.swipeDeck.innerHTML = stockCardTemplate(current)
  attachSwipeGesture()
}

function renderMainExperience() {
  buildDeck()
  renderMainProfile()
  renderDeck()
  document.getElementById('main-index')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

async function saveOnboarding() {
  const token = localStorage.getItem('access') || localStorage.getItem('accessToken')
  const profile = riskProfile()
  const payload = {
    survey_answers: Object.fromEntries(questions.map((question) => [question.id, Number(state.answers[question.id])])),
    investment_style: profile.label,
    preferred_period: state.preferredPeriod,
    preferred_sector: state.selectedSector,
  }

  try {
    const response = await fetch(onboardingApiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(payload),
    })
    return response.ok
  } catch (error) {
    return false
  }
}

function delay(ms) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms)
  })
}

async function completeOnboarding() {
  elements.onboardingCard.hidden = true
  elements.onboardingLoading.hidden = false
  elements.onboardingLoading.classList.remove('matched')
  elements.loadingTitle.textContent = '추천 알고리즘 분석 중'
  elements.loadingCopy.textContent = '성향, 섹터, 보유 기간을 조합해 후보 종목을 불러오고 있습니다.'

  renderSummary()
  await Promise.all([saveOnboarding(), delay(900)])

  elements.onboardingLoading.classList.add('matched')
  elements.loadingTitle.textContent = '주만추 매칭!'
  elements.loadingCopy.textContent = '당신의 성향에 맞춘 종목 카드가 준비됐습니다.'
  await delay(850)

  elements.overlay.hidden = true
  document.body.classList.remove('onboarding-active')
  renderMainExperience()
}

function resetOnboarding() {
  state.answers = {}
  state.currentStep = 0
  state.deckIndex = 0
  elements.overlay.hidden = false
  elements.onboardingCard.hidden = false
  elements.onboardingLoading.hidden = true
  document.body.classList.add('onboarding-active')
  renderOnboarding()
}

function advanceDeck(direction) {
  const card = elements.swipeDeck.querySelector('.match-card')
  if (!card) {
    return
  }

  const x = direction === 'left' ? -620 : direction === 'save' ? 0 : 620
  const y = direction === 'save' ? -80 : 36
  const rotate = direction === 'left' ? -18 : direction === 'right' ? 18 : 0
  card.style.transform = `translate3d(${x}px, ${y}px, 0) rotate(${rotate}deg) scale(${direction === 'save' ? 0.92 : 1})`
  card.style.opacity = '0'

  window.setTimeout(() => {
    state.deckIndex += 1
    renderDeck()
  }, 240)
}

function attachSwipeGesture() {
  const card = elements.swipeDeck.querySelector('.match-card')
  if (!card) {
    return
  }

  let dragging = false
  let startX = 0
  let currentX = 0

  card.addEventListener('pointerdown', (event) => {
    dragging = true
    startX = event.clientX
    currentX = 0
    card.style.transition = 'none'
    card.setPointerCapture?.(event.pointerId)
  })

  card.addEventListener('pointermove', (event) => {
    if (!dragging) {
      return
    }
    currentX = event.clientX - startX
    const rotate = currentX / 18
    const scale = Math.max(0.94, 1 - Math.abs(currentX) / 1800)
    card.style.transform = `translate3d(${currentX}px, 0, 0) rotate(${rotate}deg) scale(${scale})`
  })

  card.addEventListener('pointerup', () => {
    if (!dragging) {
      return
    }
    dragging = false
    card.style.transition = 'transform 0.28s var(--ease), opacity 0.22s ease'
    if (currentX > 120) {
      advanceDeck('right')
      return
    }
    if (currentX < -120) {
      advanceDeck('left')
      return
    }
    card.style.transform = 'translate3d(0, 0, 0) rotate(0deg) scale(1)'
  })
}

elements.prevButton.addEventListener('click', () => {
  state.currentStep = Math.max(0, state.currentStep - 1)
  renderOnboarding()
})

elements.nextButton.addEventListener('click', () => {
  if (state.currentStep < questions.length - 1) {
    state.currentStep += 1
    renderOnboarding()
    return
  }
  completeOnboarding()
})

elements.passButton.addEventListener('click', () => advanceDeck('left'))
elements.saveButton.addEventListener('click', () => advanceDeck('save'))
elements.likeButton.addEventListener('click', () => advanceDeck('right'))
elements.reopenButton.addEventListener('click', resetOnboarding)

renderOnboarding()
