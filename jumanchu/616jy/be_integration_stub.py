"""BE ↔ Algo 연동 stub — 장투 케어 LLM 리포트
=================================================
정율(Algo) `build_longterm_report`를 BE가 어떻게 호출하는지 보여주는 *통합 시작용
더미*. 실제 Django ORM / OpenAI 호출은 BE가 채운다.

핵심 계약:
  - Algo 입력: StockMeta / FinancialMetrics / GrowthMetrics / LongTermScores / UserProfile
               → 전부 DB row를 그대로 매핑한 순수 dataclass (ORM 객체 아님)
  - Algo 출력: LongTermReport.to_dict()  → REST 응답 / reason JSON 저장
  - 외부 호출: llm 콜러블만 주입 (GMS GPT-4o는 gms_client로, 키/캐싱은 BE)
"""

from __future__ import annotations

from longterm_report import (
    FinancialMetrics,
    GrowthMetrics,
    LongTermReport,
    LongTermScores,
    StockMeta,
    UserProfile,
    build_longterm_report,
)


# --- BE가 채울 부분 1: LLM 콜러블 = GMS GPT-4o (0615jy 패턴) ------------------- #
def make_llm_caller():
    """GMS(SSAFY) GPT-4o 콜러블. 실제 BE:

        from gms_client import make_gms_caller
        return make_gms_caller(api_key=settings.GMS_API_KEY, model="gpt-4o")

    (gms_client는 OpenAI SDK + base_url=https://gms.ssafy.io/... + GMS_API_KEY)
    여기선 import/키 없이 동작하도록 더미 반환.
    """
    def _stub(prompt: str) -> str:  # 더미: 실제론 make_gms_caller()로 교체
        return ('{"financial":"…","growth":"…","userfit":"…","final_opinion":"…"}')
    return _stub


# --- BE가 채울 부분 2: DB row → dataclass 매핑 -------------------------------- #
def _load_inputs(user, holding):
    """실제 (BE):
        stock = holding.stock
        ind   = stock.indicators.latest("calculated_date")
        fs    = stock.financial_summaries.latest("fetched_at")
        lt    = stock.long_term_scores.latest("calculated_date")
        cache = RecommendationCache.objects.get(user=user, stock=stock, rec_type="long_term")
        prof  = user.investmentprofile

        meta = StockMeta(stock.code, stock.name, stock.market, stock.sector, stock.currency)
        fin  = FinancialMetrics(
            debt_ratio=fs.debt_ratio, current_ratio=fs.current_ratio,
            operating_margin=fs.operating_margin, net_margin=fs.net_margin,
            roe=ind.roe, roa=ind.roa, dividend_yield=ind.dividend_yield,
            payout_ratio=fs.payout_ratio, fiscal_period=fs.fiscal_period)
        grw  = GrowthMetrics(fs.revenue_yoy, fs.operating_profit_yoy, fs.net_profit_yoy)
        scores = LongTermScores(
            financial=lt.financial_score, growth=lt.growth_score,
            total=cache.match_score, userfit=cache.match_score)   # 개인궁합=적합도
        profile = UserProfile(
            risk_type=prof.risk_type, preferred_period_months=prof.preferred_period,
            preferred_sectors=[s.sector for s in user.preferred_sectors.all()],
            portfolio_weight_pct=_weight_pct(holding))
        return meta, fin, grw, scores, profile
    """
    meta = StockMeta("000660", "SK하이닉스", "KOSPI", "반도체", "KRW")
    fin = FinancialMetrics(debt_ratio=22.4, current_ratio=198.3,
                           operating_margin=32.1, net_margin=24.5, roe=26.78)
    grw = GrowthMetrics(revenue_yoy=48.2, operating_profit_yoy=120.5, net_profit_yoy=90.1)
    scores = LongTermScores(financial=78, growth=92, total=86, userfit=87)
    profile = UserProfile("공격형", 12, ["반도체", "전기전자"], 38.4)
    return meta, fin, grw, scores, profile


# --- BE view 진입점 --------------------------------------------------------- #
def generate_holding_report(user, holding) -> dict:
    """BE 사용 예 (DRF):

        class LongTermReportView(APIView):
            def get(self, request, holding_id):
                holding = get_object_or_404(Holding, pk=holding_id, account__user=request.user)
                data = generate_holding_report(request.user, holding)
                # 비싸므로 RecommendationCache.reason 에 캐싱(TTL) 후 반환 권장
                return Response(data)
    """
    meta, fin, grw, scores, profile = _load_inputs(user, holding)
    llm = make_llm_caller()
    report: LongTermReport = build_longterm_report(meta, fin, grw, scores, profile, llm=llm)
    return report.to_dict()


if __name__ == "__main__":
    import json
    print(json.dumps(generate_holding_report(None, None), ensure_ascii=False, indent=2))
