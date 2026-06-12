# 주만추 Design Preview

와이어프레임(`wire-frame/`)을 **Claude Design 스타일**로 리스킨한 UI 전용 프리뷰 앱.
백엔드 없이 화면만 확인하는 용도다 — 모든 API는 스텁이고, 각 화면은 목업 데이터로 렌더링된다.

## 실행

```sh
cd design
npm install
npm run dev   # http://localhost:5180 (wire-frame의 5173과 분리)
```

로그인/온보딩 가드가 없어서 모든 화면을 URL로 바로 볼 수 있다.

## 테마

우측 상단 스위처(☀️ 🌙 📰)로 전환. `html[data-theme]` + CSS 변수로 구현 — [src/style.css](src/style.css), [src/composables/useTheme.js](src/composables/useTheme.js).

| 테마 | 컨셉 |
|---|---|
| `light` | Claude Design 크림 톤 (기본) |
| `dark` | 따뜻한 차콜 다크 |
| `paper` | 빛바랜 신문 용지 + 이중 괘선 패널 |

## 신문지 스와이프 배너

홈의 추천 배너는 신문 1면을 넘기는 인터랙션 — [src/components/NewspaperSwipeBanner.vue](src/components/NewspaperSwipeBanner.vue).
카드를 왼쪽으로 드래그하면 책등을 축으로 페이지가 넘어가고, ♡는 "관심 등록" 스탬프를 찍은 뒤 넘어간다.

## wire-frame과의 관계

- `wire-frame/`은 BE 연동용 원본 그대로 유지, `design/`은 디자인 검증용 사본
- 디자인이 확정되면 토큰(style.css)과 컴포넌트를 본 프론트엔드로 이식한다
