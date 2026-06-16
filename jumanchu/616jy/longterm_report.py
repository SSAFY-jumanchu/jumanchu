"""장투케어 AI 리포트 생성기 (Long-Term Care AI Report) — 순수 Algo 로직 (정율 → BE)
=========================================================================================
정식 명칭 : 장투케어 AI 리포트 생성기 (Long-Term Care AI Report)
코드명     : longterm_report   |   진입함수 : build_longterm_report()
LLM        : GMS(SSAFY) GPT-4o  (gms_client.make_gms_caller)
-----------------------------------------------------------------------------------------
장투 케어(포트폴리오) 화면의 **사용자 보유 종목별** 4개 LLM 문장을 만든다.

  1. 재무(Financial) 요약   2. 성장성(Growth) 요약
  3. 적합도(Userfit) 요약    4. 최종 종합의견(Final opinion)

핵심 계약 (610jy 컨벤션과 동일):
  - **점수·지표는 BE가 DB에서 뽑아 입력 dataclass로 넘긴다.** 이 모듈은 DB/ORM을
    모르고, 숫자를 받아 프롬프트를 만들고 문장을 돌려줄 뿐이다.
  - **LLM 호출(외부 API)은 BE 담당** → `llm: LLMCaller` 콜러블을 주입한다.
    (news 모듈에서 fetcher를 주입한 것과 같은 패턴)
  - 순수 부분(프롬프트 build / 응답 parse / 등급·라벨)은 LLM 없이 테스트 가능.

데이터 출처 (참고):
  - 재무 지표: stocks_financialsummary + stocks_stockindicator
  - 점수: recommend_longtermscore (financial_score/growth_score/total_score)
          + 적합도(개인궁합)는 recommend_recommendationcache.match_score 기반
  - 유저 프로필: accounts_investmentprofile (+ userpreferredsector), 포트비중은
    portfolio_holding 계산값

설계 메모:
  - 종목 1개당 LLM 호출 1번 (4개 문장을 JSON 한 방에 받음) — 보유종목 N개면 N콜.
  - 환각 방지: 프롬프트에 "제공된 수치만 사용, 목표가·전망 지어내지 말 것" 명시.
    None(데이터 없음) 지표는 '데이터 없음'으로 라벨해 추측 차단.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Callable, Optional

# 프롬프트 문자열을 받아 LLM 응답 문자열을 돌려주는 함수. BE가 OpenAI 등으로 구현해 주입.
LLMCaller = Callable[[str], str]


# ============================================================================ #
# 입력 dataclass — BE가 DB row를 그대로 매핑해서 채운다
# ============================================================================ #
@dataclass
class StockMeta:
    """종목 식별 정보 (stocks_stock)."""
    code: str
    name: str
    market: str        # KOSPI / KOSDAQ / NASDAQ / NYSE
    sector: str
    currency: str = "KRW"

    @property
    def is_domestic(self) -> bool:
        return self.market in ("KOSPI", "KOSDAQ")


@dataclass
class FinancialMetrics:
    """재무 지표 (financialsummary + stockindicator). 없으면 None."""
    debt_ratio: Optional[float] = None         # 부채비율 %
    current_ratio: Optional[float] = None      # 유동비율 %
    operating_margin: Optional[float] = None   # 영업이익률 %
    net_margin: Optional[float] = None          # 순이익률 %
    roe: Optional[float] = None                 # ROE %
    roa: Optional[float] = None                 # ROA %
    dividend_yield: Optional[float] = None      # 배당수익률 %
    payout_ratio: Optional[float] = None        # 배당성향 %
    fiscal_period: str = ""                      # "2025Q3" 등 (맥락용)


@dataclass
class GrowthMetrics:
    """성장성 지표 (financialsummary YoY). 없으면 None."""
    revenue_yoy: Optional[float] = None          # 매출 성장률 %
    operating_profit_yoy: Optional[float] = None # 영업이익 성장률 %
    net_profit_yoy: Optional[float] = None        # 순이익 성장률 %


@dataclass
class LongTermScores:
    """이미 계산된 점수 (recommend_longtermscore + 개인궁합). 0~100."""
    financial: float
    growth: float
    total: float
    userfit: Optional[float] = None   # 개인 궁합(적합도). per-user, 없으면 None


@dataclass
class UserProfile:
    """적합도 문장용 유저 컨텍스트 (accounts_investmentprofile 등)."""
    risk_type: str = ""                          # "안정형"/"균형형"/"공격형"
    preferred_period_months: Optional[int] = None
    preferred_sectors: list[str] = field(default_factory=list)
    portfolio_weight_pct: Optional[float] = None  # 이 종목의 포트 비중 %


# ============================================================================ #
# 출력 dataclass — BE가 to_dict()로 REST 직렬화 / reason JSON에 저장
# ============================================================================ #
@dataclass
class SectionAnalysis:
    section: str       # "financial" / "growth" / "userfit"
    score: float
    grade: str
    summary: str       # LLM 생성 문장

    def to_dict(self) -> dict:
        return {
            "section": self.section,
            "score": self.score,
            "grade": self.grade,
            "summary": self.summary,
        }


@dataclass
class LongTermReport:
    stock_code: str
    financial: SectionAnalysis
    growth: SectionAnalysis
    userfit: Optional[SectionAnalysis]
    total_score: float
    total_grade: str
    total_label: str
    final_opinion: str

    def to_dict(self) -> dict:
        return {
            "stock_code": self.stock_code,
            "financial": self.financial.to_dict(),
            "growth": self.growth.to_dict(),
            "userfit": self.userfit.to_dict() if self.userfit else None,
            "total": {
                "score": self.total_score,
                "grade": self.total_grade,
                "label": self.total_label,
                "opinion": self.final_opinion,
            },
        }


# ============================================================================ #
# 등급 · 라벨 (화면 JS와 동일 기준 — 결정적, LLM 아님)
# ============================================================================ #
def grade_of(score: Optional[float]) -> str:
    if score is None:
        return "—"
    if score >= 90:
        return "A"
    if score >= 80:
        return "B+"
    if score >= 70:
        return "B"
    if score >= 60:
        return "C+"
    if score >= 50:
        return "C"
    return "D"


def label_of(total_score: float) -> str:
    """총점 → 한 줄 추천 라벨. (밴드는 팀 합의로 조정 가능)"""
    if total_score >= 90:
        return "장기 핵심 보유 추천"
    if total_score >= 80:
        return "장기 보유 추천"
    if total_score >= 70:
        return "보유 유지 · 모니터링"
    if total_score >= 60:
        return "비중 조절 검토"
    return "보유 재검토"


# ============================================================================ #
# 포맷 헬퍼 — None은 '데이터 없음'으로 (LLM 추측 차단)
# ============================================================================ #
_NO_DATA = "데이터 없음"


def _pct(v: Optional[float]) -> str:
    return f"{v:.1f}%" if v is not None else _NO_DATA


def _fact_lines(pairs: list[tuple[str, str]]) -> str:
    return "\n".join(f"  - {label}: {value}" for label, value in pairs)


# ============================================================================ #
# 적합도 결정적 사실 — 점수 외 매칭 플래그를 프롬프트 근거로 제공
# ============================================================================ #
def _userfit_facts(meta: StockMeta, profile: UserProfile) -> list[tuple[str, str]]:
    sector_match = any(
        meta.sector in s or s in meta.sector for s in profile.preferred_sectors
    )
    weight = profile.portfolio_weight_pct
    if weight is None:
        weight_note = _NO_DATA
    elif weight >= 30:
        weight_note = f"{weight:.1f}% (집중도 높음 · 분산 주의)"
    else:
        weight_note = f"{weight:.1f}% (적정 범위)"
    return [
        ("투자 성향", profile.risk_type or _NO_DATA),
        ("선호 보유기간",
         f"{profile.preferred_period_months}개월" if profile.preferred_period_months else _NO_DATA),
        ("종목 섹터", meta.sector),
        ("선호 섹터 일치", "일치" if sector_match else "불일치"),
        ("포트폴리오 비중", weight_note),
    ]


# ============================================================================ #
# 프롬프트 빌더 (순수 — LLM 없이 테스트 가능)
# ============================================================================ #
_GUARDRAIL = (
    "규칙:\n"
    "- 한국어 존댓말, 주식 입문자(주린이)도 이해할 친근하고 차분한 톤.\n"
    "- 아래 '근거 수치'에 있는 값만 사용한다. 목표가·미래 전망·없는 지표를 지어내지 않는다.\n"
    "- '데이터 없음' 항목은 언급하지 않거나 '데이터가 아직 부족하다'고만 표현한다.\n"
    "- 사용자가 이미 보유 중인 종목에 대한 분석이며, 매수·매도 권유가 아니다.\n"
    "- 숫자를 한두 개만 골라 근거로 인용하고, 나열식이 아닌 자연스러운 문장으로 쓴다.\n"
)


def build_report_prompt(
    meta: StockMeta,
    financial: FinancialMetrics,
    growth: GrowthMetrics,
    scores: LongTermScores,
    profile: Optional[UserProfile],
) -> str:
    """4개 문장을 JSON 한 번에 받기 위한 통합 프롬프트를 만든다."""
    fin_facts = _fact_lines([
        ("재무 점수", f"{scores.financial:.0f}/100 ({grade_of(scores.financial)}등급)"),
        ("부채비율", _pct(financial.debt_ratio)),
        ("유동비율", _pct(financial.current_ratio)),
        ("영업이익률", _pct(financial.operating_margin)),
        ("순이익률", _pct(financial.net_margin)),
        ("ROE", _pct(financial.roe)),
        ("ROA", _pct(financial.roa)),
        ("배당수익률", _pct(financial.dividend_yield)),
        ("배당성향", _pct(financial.payout_ratio)),
    ])
    grw_facts = _fact_lines([
        ("성장 점수", f"{scores.growth:.0f}/100 ({grade_of(scores.growth)}등급)"),
        ("매출 성장률(YoY)", _pct(growth.revenue_yoy)),
        ("영업이익 성장률(YoY)", _pct(growth.operating_profit_yoy)),
        ("순이익 성장률(YoY)", _pct(growth.net_profit_yoy)),
    ])

    sections = (
        '  "financial": "재무 건전성 요약 2~3문장",\n'
        '  "growth": "성장성 요약 2~3문장",\n'
    )
    blocks = [
        f"[재무 근거 수치]\n{fin_facts}",
        f"[성장성 근거 수치]\n{grw_facts}",
    ]

    if profile is not None:
        uf_facts = _fact_lines(
            [("적합도 점수",
              f"{scores.userfit:.0f}/100 ({grade_of(scores.userfit)}등급)"
              if scores.userfit is not None else _NO_DATA)]
            + _userfit_facts(meta, profile)
        )
        blocks.append(f"[적합도 근거 수치]\n{uf_facts}")
        sections += '  "userfit": "사용자 적합도 요약 2~3문장",\n'

    sections += '  "final_opinion": "총점 기반 종합의견 3~4문장"'

    total_line = (
        f"총점 {scores.total:.0f}/100 ({grade_of(scores.total)}등급) — {label_of(scores.total)}"
    )

    return (
        f"당신은 장기투자 분석을 돕는 애널리스트입니다.\n"
        f"대상 종목: {meta.name} ({meta.code}, {meta.market}, {meta.sector})\n"
        f"{total_line}\n\n"
        + "\n\n".join(blocks)
        + "\n\n"
        + _GUARDRAIL
        + "\n출력은 아래 키를 가진 JSON 하나만. 다른 텍스트 금지:\n"
        + "{\n" + sections + "\n}"
    )


# ============================================================================ #
# 응답 파서 (순수)
# ============================================================================ #
def _strip_fence(raw: str) -> str:
    s = raw.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else s
        if s.endswith("```"):
            s = s[: -3]
        if s.lstrip().startswith("json"):
            s = s.lstrip()[4:]
    # 본문 중 첫 '{' ~ 마지막 '}'만 취해 잡텍스트 방어
    i, j = s.find("{"), s.rfind("}")
    return s[i : j + 1] if i != -1 and j != -1 else s


def parse_report_response(
    raw: str,
    meta: StockMeta,
    scores: LongTermScores,
    *,
    has_userfit: bool,
) -> LongTermReport:
    """LLM JSON 응답 → LongTermReport. 점수·등급·라벨은 입력값으로 신뢰(결정적)."""
    data = json.loads(_strip_fence(raw))

    fin = SectionAnalysis("financial", scores.financial,
                          grade_of(scores.financial), str(data.get("financial", "")).strip())
    grw = SectionAnalysis("growth", scores.growth,
                          grade_of(scores.growth), str(data.get("growth", "")).strip())
    uf = None
    if has_userfit and scores.userfit is not None:
        uf = SectionAnalysis("userfit", scores.userfit,
                             grade_of(scores.userfit), str(data.get("userfit", "")).strip())

    return LongTermReport(
        stock_code=meta.code,
        financial=fin,
        growth=grw,
        userfit=uf,
        total_score=scores.total,
        total_grade=grade_of(scores.total),
        total_label=label_of(scores.total),
        final_opinion=str(data.get("final_opinion", "")).strip(),
    )


# ============================================================================ #
# 진입점 — BE가 view/배치에서 호출
# ============================================================================ #
def build_longterm_report(
    meta: StockMeta,
    financial: FinancialMetrics,
    growth: GrowthMetrics,
    scores: LongTermScores,
    profile: Optional[UserProfile],
    *,
    llm: LLMCaller,
) -> LongTermReport:
    """보유 종목 1개 → 장투 케어 분석 리포트(4개 문장).

    BE 사용 예:
        report = build_longterm_report(meta, fin, grw, scores, profile, llm=call_openai)
        cache.reason = report.to_dict()      # recommend_recommendationcache.reason(JSON)
    """
    prompt = build_report_prompt(meta, financial, growth, scores, profile)
    raw = llm(prompt)
    return parse_report_response(
        raw, meta, scores, has_userfit=profile is not None
    )
