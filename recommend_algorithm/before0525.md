# 💘 주만추 (주식 + 만남 추천 서비스)
## 📌 궁합 기반 장기투자 추천 알고리즘 설계

---

## 🔥 1. 서비스 핵심 컨셉

> **“사용자의 실제 투자 성향을 분석하여, 장기적으로 가장 잘 맞는 ‘이상형 주식’을 추천한다”**

- 기존 서비스: 수익률 기반 추천 ❌  
- 주만추: **궁합 기반 추천 + 행동 학습 기반 추천 ✅**

---

## 🧠 2. 전체 시스템 구조


[온보딩 설문 (8문항)]
↓
[유저 프로필 벡터 생성 (5차원)]
↓
[주식 데이터 정규화 (Stock DNA)]
↓
[궁합 점수 계산 (5개 요소)]
↓
[최종 궁합 지수 (0~100)]
↓
[추천 (스와이프 UI)]


---

## 📊 3. 온보딩 설문 → 유저 프로필 벡터

설문 결과는 단순 점수가 아닌 **투자 성향 벡터로 변환됨**

### 🎯 유저 프로필 구조

```python
user_profile = {
    "risk_tolerance":    1~5,   # 리스크 감수 성향
    "investment_term":   1~5,   # 투자 기간 (장기 성향)
    "experience":        1~5,   # 투자 경험
    "loss_aversion":     1~5,   # 손실 회피 성향
    "behavior":          1~5,   # 투자 스타일
    "preferred_sectors": []     # 관심 산업
}
📝 설문 핵심 로직
투자 목적 + 투자 기간 + 투자 방식 → investment_term
투자 경험 + 리스크 이해도 → experience
손실 대응 방식 → risk_tolerance
투자 스타일 → behavior
관심 테마 → preferred_sectors

👉 각 문항은 특정 벡터 값으로 직접 매핑됨

📈 4. 주식 성격 정의 (Stock DNA)

주식 데이터를 0~1 범위로 정규화하여 사용

stock_profile = {
    "volatility":   beta,         # 변동성
    "value_score":  0~1,          # 저평가 지표 (1/PBR)
    "growth_score": 0~1,          # 성장성 (EPS 기반)
    "stability":    0~1,          # 안정성 (1/β)
    "sector":       str
}
⚙️ 정규화 핵심 로직
변동성 → Beta 사용
가치 → PBR 역수 (1/PBR)
성장 → EPS 정규화
안정성 → Beta 역수
💘 5. 궁합 점수 알고리즘 (핵심)
📌 최종 공식
Total Score (0~100) =
    (risk_match   × 0.35)
  + (term_match   × 0.20)
  + (exp_match    × 0.15)
  + (sector_match × 0.20)
  + (style_match  × 0.10)
  × 100
🔍 6. 세부 궁합 요소
① 리스크 궁합 (35%)
ideal_beta = user["risk_tolerance"] / 2.5
risk_match = 1 - abs(ideal_beta - stock["volatility"])
유저 성향과 주식 변동성의 차이를 기반으로 계산
차이가 적을수록 높은 점수
② 투자 기간 궁합 (20%) ⭐ 핵심
if term >= 4:
    score = (stability + value_score) / 2
elif term == 3:
    score = (stability + value_score + volatility) / 3
else:
    score = volatility 기반
장기 투자자 → 안정성 + 저평가 선호
단기 투자자 → 변동성 선호
③ 경험 기반 궁합 (15%)
if exp <= 2:
    score = 안정성 중심
elif exp == 3:
    score = 균형
else:
    score = 성장성 + 변동성
초보 → 안정성
고수 → 성장성/변동성 허용
④ 테마 궁합 (20%)
if sector in preferred:
    1.0
elif no preference:
    0.5
else:
    0.0
관심 산업과 일치 시 높은 점수
⑤ 스타일 궁합 (10%)
score = (value_score + growth_score) / 2
가치 + 성장 균형 평가
추후 behavior 기반 가중치 적용 예정
🧮 7. 최종 계산 예시

균형형 투자자 × 삼성전자

항목	점수	가중치	기여
리스크	65.0	35%	22.75
테마	100.0	20%	20.00
기간	60.8	20%	12.16
경험	55.3	15%	8.30
스타일	66.5	10%	6.65

👉 최종 궁합 점수: 💘 69.9점

💔 8. 차별화 요소 (핵심 가치)
기존 서비스
단순 수익률 기반 추천
주만추
궁합 기반 추천
유저 성향 반영
장기 투자 최적화
⏱ 9. 확장 방향 (매매일지 연동)
현재
설문 기반 성향 분석
향후
매매일지 기반 행동 학습
📊 추가 반영 요소
평균 보유 기간
손절 비율
추매 패턴
수익/손실 행동

👉 “말이 아닌 행동으로 투자 성향을 학습”

🚀 10. 개선 방향
항목	현재	개선
성장성	EPS 절대값	EPS 증가율
테마	단순 매칭	유사도 점수
스타일	고정 비율	behavior 기반
리스크	단순 Beta	손실 회피 반영
🎯 11. 최종 한줄 정의

“주만추는 투자자의 성향과 주식의 특성을 매칭하여, 장기적으로 가장 잘 맞는 주식을 추천하는 궁합 기반 투자 서비스이다.”