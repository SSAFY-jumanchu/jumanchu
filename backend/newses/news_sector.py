"""뉴스 섹터 추출 — 순수 Python 알고리즘 모듈.

원본: 정율(Algo) `610jy/news_sector.py` — Django 비의존 순수 함수를 newses 앱으로
그대로 이식(로직 변경 없음).

역할: 뉴스 텍스트(제목+요약)에서 **종목을 태깅**하고, 그 종목의 업종/섹터
      (DB `Stock.sector`)를 역산해 **뉴스의 섹터 태그**를 만든다.

설계: 섹터 어휘를 `Stock.sector`에서 역산하므로 사용자 `preferred_sector`와 자동 일치.
      `StockNews`엔 섹터 컬럼이 없지만 `NewsRelatedStock → Stock.sector` 조인으로
      조회 시점 역산 가능 → 모델 변경 불필요.

BE ↔ Algo 인터페이스:
    sectors = extract_sectors(text, stocks)          # 핵심
    payload = [t.to_dict() for t in sectors]         # REST 직렬화
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


# --------------------------------------------------------------------------- #
# 입력/출력 타입 (명시적 dataclass — BE↔Algo 계약)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class StockRef:
    """BE가 `Stock` 행에서 추려 넘기는 최소 정보."""
    code: str            # 종목코드 (KR 6자리 / US 티커) — Stock.code
    name: str            # 종목명 — Stock.name
    sector: str = ""     # 업종/섹터 — Stock.sector (진실의 원천; 비어있을 수 있음)


@dataclass(frozen=True)
class SectorTag:
    """뉴스 1건에 대한 섹터 추출 결과 1개."""
    sector: str               # 섹터명 (= 매칭 종목들의 Stock.sector)
    score: float              # 언급 강도(0~1). 제목 매칭 1.0 / 본문만 0.5 등 가중 합산 정규화
    stock_codes: list[str] = field(default_factory=list)  # 이 섹터로 묶인 종목코드들

    def to_dict(self) -> dict:
        return {
            "sector": self.sector,
            "score": round(self.score, 3),
            "stock_codes": self.stock_codes,
        }


# --------------------------------------------------------------------------- #
# 종목 태깅
# --------------------------------------------------------------------------- #
_KR_CODE_RE = re.compile(r"\b(\d{6})\b")          # 한국 6자리 코드 직접 노출
_US_TICKER_RE = re.compile(r"\b([A-Z]{1,5})\b")   # 영문 대문자 토큰(오탐 多 → 사전 교차검증)


# 큐레이션 종목 별칭 사전: 별칭 → 종목코드 리스트.
# DB(Stock)엔 정식명만 있어 한국 뉴스의 약어/별칭("삼전","하닉","엔솔")이 누락된다.
# 합성 별칭("삼전닉스"=삼성전자+SK하이닉스)은 여러 코드를 가리키므로 list로 둔다.
# 정식명은 이미 name 매칭으로 잡히므로 여기엔 *약어/이형 표기만* 넣는다.
COMMON_KR_ALIASES: dict[str, list[str]] = {
    "삼전": ["005930"],                       # 삼성전자
    "삼전닉스": ["005930", "000660"],          # 삼성전자 + SK하이닉스
    "삼성전닉스": ["005930", "000660"],
    "하닉": ["000660"],                        # SK하이닉스
    "엔솔": ["373220"],                        # LG에너지솔루션
    "LG엔솔": ["373220"],
    "삼바": ["207940"],                        # 삼성바이오로직스
    "현차": ["005380"],                        # 현대차
    "네이버": ["035420"],                      # DB name이 'NAVER'라 한글 표기 누락 방지
    "포스코": ["005490"],                      # POSCO홀딩스
}


@dataclass(frozen=True)
class _StockHit:
    code: str
    sector: str
    in_title: bool   # 제목에서 매칭됐는지(가중치용)


def _tag_stocks(
    title: str,
    body: str,
    stocks: list[StockRef],
    *,
    min_name_len: int,
    aliases: dict[str, list[str]] | None,
) -> list[_StockHit]:
    """제목/본문에서 종목을 태깅. 제목 매칭은 가중치를 위해 따로 표시."""
    by_name = {s.name: s for s in stocks if len(s.name) >= min_name_len}
    valid_codes = {s.code for s in stocks}
    by_code = {s.code: s for s in stocks}

    hits: dict[str, _StockHit] = {}

    def _consider(stock: StockRef, in_title: bool) -> None:
        prev = hits.get(stock.code)
        # 이미 본문에서만 잡혔는데 제목에서도 잡히면 in_title 승격
        if prev is None or (in_title and not prev.in_title):
            hits[stock.code] = _StockHit(stock.code, stock.sector, in_title)

    for text, in_title in ((title, True), (body, False)):
        if not text:
            continue
        # 1) 종목명 부분 매칭
        for name, stock in by_name.items():
            if name in text:
                _consider(stock, in_title)
        # 2) 한국 6자리 코드 직접 노출
        for m in _KR_CODE_RE.findall(text):
            if m in by_code:
                _consider(by_code[m], in_title)
        # 3) 미국 티커 — 사전에 있는 것만 채택(IT/CEO/USA 등 오탐 차단)
        for m in _US_TICKER_RE.findall(text):
            if m in valid_codes:
                _consider(by_code[m], in_title)
        # 4) 약어/별칭 — 큐레이션 사전(길이 필터 미적용). 합성 별칭은 다중 종목.
        if aliases:
            for alias, codes in aliases.items():
                if alias in text:
                    for code in codes:
                        if code in by_code:
                            _consider(by_code[code], in_title)

    return list(hits.values())


# --------------------------------------------------------------------------- #
# 핵심 공개 함수
# --------------------------------------------------------------------------- #
def extract_sectors(
    text: str,
    stocks: list[StockRef],
    *,
    summary: str = "",
    min_name_len: int = 2,
    title_weight: float = 1.0,
    body_weight: float = 0.5,
    aliases: dict[str, list[str]] | None = COMMON_KR_ALIASES,
) -> list[SectorTag]:
    """뉴스 텍스트에서 종목을 태깅하고 그 종목의 섹터로 **뉴스 섹터 태그**를 산출.

    Args:
        text: 뉴스 제목(가중치 높음).
        stocks: BE가 DB `Stock`에서 넘긴 종목 목록(code/name/sector).
        summary: 뉴스 요약/본문(가중치 낮음). 없으면 제목만 사용.
        min_name_len: 이 길이 미만 종목명은 오탐 위험으로 제외(예: "DB", "SK").
        title_weight / body_weight: 제목/본문 매칭 가중치.
        aliases: 약어/별칭 → 종목코드 리스트. 기본은 `COMMON_KR_ALIASES`. None이면 비활성.

    Returns:
        score 내림차순 SectorTag 리스트. sector가 빈 종목만 매칭되면 빈 리스트.

    Note:
        섹터 어휘는 `Stock.sector`(DB) 그대로다 → `preferred_sector`와 일치.
        거시 뉴스(금리/환율 등 종목 미언급)는 여기서 빈 결과 → 추후 fallback 영역.
    """
    hits = _tag_stocks(
        text, summary, stocks, min_name_len=min_name_len, aliases=aliases
    )

    # 섹터별로 종목 묶고 강도 합산
    bucket: dict[str, dict] = {}
    for h in hits:
        sector = h.sector.strip()
        if not sector:           # sector 미기재 종목은 섹터 산출 불가 → 스킵
            continue
        b = bucket.setdefault(sector, {"score": 0.0, "codes": []})
        b["score"] += title_weight if h.in_title else body_weight
        b["codes"].append(h.code)

    if not bucket:
        return []

    # 정규화(최대값 기준 0~1) 후 score 내림차순
    max_raw = max(b["score"] for b in bucket.values())
    tags = [
        SectorTag(
            sector=sector,
            score=b["score"] / max_raw if max_raw else 0.0,
            stock_codes=sorted(b["codes"]),
        )
        for sector, b in bucket.items()
    ]
    tags.sort(key=lambda t: (-t.score, t.sector))
    return tags


def primary_sector(
    text: str,
    stocks: list[StockRef],
    *,
    summary: str = "",
) -> str | None:
    """뉴스의 대표 섹터 1개(최고 강도)만 필요할 때의 편의 함수. 없으면 None."""
    tags = extract_sectors(text, stocks, summary=summary)
    return tags[0].sector if tags else None
