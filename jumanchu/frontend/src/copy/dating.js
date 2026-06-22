// 연애모드(장기연애 컨셉) 문구 사전.
// key는 화면의 의미 단위. 값은 연애모드일 때 보여줄 문구.
// 기본(normal) 문구는 각 컴포넌트에 그대로 둔다(팀원 영역) — 연애모드에서만 여기 값으로 치환된다.
// 사용: const { t } = useCopy();  {{ t('home.match.title', '오늘의 추천 종목') }}
export const datingCopy = {
  // ===== 네비게이션 메뉴 (장기연애 컨셉) — '홈'은 그대로(fallback) =====
  'nav.community': '연애 상담소',
  'nav.stocks': '인연 찾기',
  'nav.holdings': '만나는 중',
  'nav.diary': '데이트 기록',
  'nav.portfolio': '관계 점검',

  // 홈 — 궁합 추천 섹션
  'home.match.title': '오늘, 당신과 잘 맞는 인연 💝',
  'home.match.sub': '김주만님과 잘 맞는 종목들이에요. 넘기면서 끌리는 상대를 골라보세요.',

  // 홈 — 액션 카드
  'home.action.diary': '데이트 기록 남기기',
  'home.action.diary.sub': '기록 안 한 데이트 1건',
  'home.action.care.title': '관계 점검하기',
  'home.action.care.desc': '내 종목, 잘 만나고 있나요?',

  // 홈 — 자산 현황 패널
  'home.asset.eyebrow': '나의 연애',
  'home.asset.title': '우리 연애는 지금',
  'home.asset.total': '자산 현황',
  'home.asset.return': '총 수익률',
  'home.asset.news': '📰 만나는 종목 소식',

  // 홈 — 궁합 추천 카드
  'home.match.count': '인연',
  'home.match.interest': '명이 이 인연에 관심 있어요',

  // 홈 — 하단 섹션 (관심 종목 뉴스 / 보유 종목 / 매매 일기)
  'home.watch.eyebrow': '내가 끌린 종목 소식',
  'home.watch.title': '관심 종목 소식',
  'home.holdings.eyebrow': '나의 인연들',
  'home.holdings.title': '만나는 중',
  'home.diary.eyebrow': '나의 연애 기록',
  'home.diary.title': '데이트 기록',
  'home.diary.write': '+ 오늘 데이트 기록',

  // ===== 온보딩 설문 (장기연애 컨셉) =====
  'ob.pageTitle': '우리, 얼마나 잘 맞을까? 💞',
  'ob.step.intro': '첫 만남 준비',
  'ob.scoreInline': '마음 점수',

  // 사전 설정 (Step 0)
  'ob.s0.title': '어떤 사람한테 끌리세요?',
  'ob.s0.desc': '김주만님과 오래 함께할 인연을 찾아드릴게요. 어떤 분야에 끌리는지, 얼마나 오래 함께하고 싶은지 알려주세요.',
  'ob.s0.sectorLabel': '끌리는 분야',
  'ob.s0.sectorHint': '여러 개 골라도 좋아요',
  'ob.s0.periodLabel': '함께하고 싶은 기간',
  'ob.s0.periodHint': '하나만 골라주세요',

  // Q1 — 관계의 목적
  'ob.q1.label': '관계의 목적',
  'ob.q1.desc': '이 만남에서 가장 바라는 게 뭔가요? 첫 단추가 관계의 방향을 정해요.',
  'ob.q1.opt1.title': '상처받지 않는 게 우선',
  'ob.q1.opt1.desc': '마음 다칠 일 없이 안전하게 만나고 싶어요.',
  'ob.q1.opt3.title': '잔잔한 행복',
  'ob.q1.opt3.desc': '큰 욕심 없이, 은은하지만 분명한 설렘을 원해요.',
  'ob.q1.opt5.title': '뜨겁게 사랑',
  'ob.q1.opt5.desc': '상처를 감수하더라도 크게 빠지는 사랑을 원해요.',

  // Q2 — 연애 경험
  'ob.q2.label': '연애 경험',
  'ob.q2.desc': '지금까지 어떤 만남을 거쳐오셨나요?',
  'ob.q2.opt1.title': '거의 없어요',
  'ob.q2.opt1.desc': '진지한 만남은 아직 1년이 안 됐어요.',
  'ob.q2.opt3.title': '몇 번 있었어요',
  'ob.q2.opt3.desc': '나름의 연애 경험이 쌓여 있어요.',
  'ob.q2.opt5.title': '연애 고수',
  'ob.q2.opt5.desc': '다양한 만남을 두루 겪어봤어요.',

  // Q3 — 흔들림 허용치
  'ob.q3.label': '흔들림 허용치',
  'ob.q3.desc': '이 관계에서, 어디까지 흔들려도 괜찮으신가요?',
  'ob.q3.opt1.title': '조금만 흔들려도 불안',
  'ob.q3.opt1.desc': '작은 다툼도 견디기 힘들어요.',
  'ob.q3.opt3.title': '어느 정도는 괜찮아',
  'ob.q3.opt3.desc': '잠깐의 위기는 견디지만 곧 회복돼야 해요.',
  'ob.q3.opt5.title': '크게 흔들려도 OK',
  'ob.q3.opt5.desc': '큰 갈등도 감수하고 더 깊어지길 바라요.',

  // Q4 — 마음의 무게
  'ob.q4.label': '마음의 무게',
  'ob.q4.desc': "이 사람은 '없으면 안 되는 사이'인가요, '설레는 썸'인가요?",
  'ob.q4.opt1.title': '없으면 안 되는 사이',
  'ob.q4.opt1.desc': '이 사람 없으면 일상이 무너져요.',
  'ob.q4.opt3.title': '소중하지만 여유 있는',
  'ob.q4.opt3.desc': '없어도 살지만 무척 아끼는 사이예요.',
  'ob.q4.opt5.title': '가벼운 마음',
  'ob.q4.opt5.desc': '잘 안 돼도 내 일상엔 지장 없어요.',

  // Q5 — 만남의 기간
  'ob.q5.label': '만남의 기간',
  'ob.q5.desc': '이 인연을 어느 정도의 시간으로 생각하고 계신가요?',
  'ob.q5.opt1.title': '짧고 굵게',
  'ob.q5.opt1.desc': '오래 끌기보다 짧게 만나고 싶어요.',
  'ob.q5.opt3.title': '몇 년은 함께',
  'ob.q5.opt3.desc': '중기적으로 곁에 두고 싶어요.',
  'ob.q5.opt5.title': '오래오래',
  'ob.q5.opt5.desc': '길게 안정적으로 함께하고 싶어요.',

  // Q6 — 위기의 순간
  'ob.q6.label': '위기의 순간',
  'ob.q6.desc': '관계가 크게 흔들릴 때, 당신은 어떻게 하시겠어요?',
  'ob.q6.opt1.title': '바로 정리',
  'ob.q6.opt1.desc': '더 다치기 전에 빠르게 마음을 접어요.',
  'ob.q6.opt3.title': '지켜본 뒤 결정',
  'ob.q6.opt3.desc': '상황을 좀 더 보고 마음을 정해요.',
  'ob.q6.opt5.title': '더 다가가기',
  'ob.q6.opt5.desc': '흔들릴 때일수록 더 마음을 쏟아요.',

  'ob.weightedNote': '💞 이 질문은 마음 점수에 2배로 반영돼요.',
  'ob.nav.next': '다음',
  'ob.nav.result': '우리 궁합 보기',

  // 결과 화면
  'ob.result.eyebrow': '우리 궁합 분석 완료 💕',
  'ob.result.scoreLabel': '궁합 점수',
  'ob.result.sectorKey': '끌리는 분야',
  'ob.result.periodKey': '함께할 기간',
  'ob.finish.loading': '저장 중…',
  'ob.finish.go': '주만추 시작하기 💞',

  // 성향 결과 타입 (label은 로직 키라 그대로, 표시 문구만 치환)
  'ob.risk.안정형.name': '신중한 사랑꾼',
  'ob.risk.안정형.desc': '상처받지 않는 안정적인 관계를 가장 소중히 여겨요.',
  'ob.risk.중립형.name': '균형 잡힌 연인',
  'ob.risk.중립형.desc': '설렘과 안정 사이에서 균형을 잡는 연애를 추구해요.',
  'ob.risk.공격형.name': '열정적인 사랑꾼',
  'ob.risk.공격형.desc': '뜨겁게 빠지는 사랑을 위해 위험도 기꺼이 감수해요.',

  // ===== 매매일기 → 데이트 기록 (장기연애 컨셉) =====
  'td.title': '데이트 기록 💌',
  'td.sub': '왜 끌렸는지 고르기만 하면 끝 — 나중에 돌아보며 좋은 만남의 습관을 만들어요.',

  // 작성 대기
  'td.pending.title': '기록 안 한 데이트 1건',
  'td.pending.desc': '만났는데 아직 기록 안 한 종목이에요.',

  // 목록
  'td.list.title': '나의 데이트 기록',
  'td.list.countPre': '총',
  'td.list.countSuf': '번의 만남',
  'td.status.done': '돌아봄 완료',
  'td.status.pending': '돌아보기 전',
  'td.tag.target': '바라는 만큼',
  'td.tag.stop': '헤어질 선',
  'td.review.actualLabel': '💞 실제',
  'td.review.verdictLabel': '마음',

  // 새 기록 작성 폼
  'td.form.titlePre': '💌 새 데이트 기록',
  'td.form.titleSuf': '다 고르기만!',
  'td.field.type': '만남의 종류',
  'td.field.reason': '끌린 이유 (복수 선택)',
  'td.field.confidence': '마음의 크기',
  'td.field.target': '바라는 정도',
  'td.field.stop': '헤어질 선',
  'td.save': '데이트 기록 저장',
  'td.form.hint': '고민·눈치 전부 없이, 선택만으로 1초 기록',

  // 판단(verdict) — 값(성공/보류/실패)은 로직 키라 그대로, 표시만 치환
  'td.verdict.성공': '잘 맞았어',
  'td.verdict.보류': '글쎄',
  'td.verdict.실패': '아니었어',

  // ===== 보유 종목 → 지금 만나는 종목들 (장기연애 컨셉) =====
  'hv.title': '지금 만나는 중 💑',
  'hv.badge': '설렘 연습 계좌',
  'hv.summary.title': '우리 사이 요약',
  'hv.sum.eval': '지금까지 쌓은 가치',
  'hv.sum.pnl': '우리 사이 변화',
  'hv.sum.cost': '첫 설렘',
  'hv.shortcut.orders': '연애 기록',
  'hv.shortcut.diary': '데이트 기록',
  'hv.list.title': '만나는 종목들',
  'hv.alloc.title': '관심 지수 (국내·해외)',
  'hv.detail.buy': '더 다가가기',
  'hv.detail.sell': '멀어지기',
  'hv.detail.go': '이 사람 더 알아보기 →',
  'hv.news.title': '주변 지인 소식 · 이야기',

  // ===== 장투 케어 → 우리 관계 점검 (장기연애 컨셉) =====
  'lt.title': '우리 관계 점검 💕',
  'lt.sub': '지금 만나는 종목, 계속 함께해도 될까요? — 재무 30% · 성장 40% · 궁합 30%로 우리 사이를 점검해드려요.',
  'lt.list.title': '만나는 종목들',
  'lt.overview.go': '이 사람 더 알아보기 →',
  'lt.score.재무': '안정감',
  'lt.score.성장': '성장 가능성',
  // 'lt.score.궁합'은 그대로 '궁합'(fallback) 사용
  'lt.journal.title': '📒 이 종목 데이트 기록',
  'lt.side.buy': '더 다가감',
  'lt.side.sell': '멀어짐',
  'lt.history.title': '📈 우리 사이 점수 변화',
  'lt.news.title': '📰 주위 소식',

  // ===== 마이페이지 (장기연애 컨셉) — 정식 계좌/거래/개인정보 데이터는 그대로 =====
  'mp.tab.invest': '내 연애',
  'mp.invest.analysis': '우리 사이 분석',
  'mp.invest.holdings': '만나는 종목 현황',
  'mp.invest.trades': '우리 만남 기록',
  'mp.profile.investType': '연애 성향',
  'mp.profile.retest': '연애 성향 재검사',
  'mp.profile.community': '연애 상담소 프로필',
  'mp.act.posts': '쓴 이야기',

  // ===== 종목 상세 (가볍게만 — 주문/지정가/시장가/호가 등 기능 용어는 그대로) =====
  'sd.watch': '💗 관심 인연 추가',
  'sd.community.title': '이 종목 수다방',
  'sd.comm.detailBtn': '이 사람 더 알아보기 →',
}
