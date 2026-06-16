"""BE ↔ Algo 연동 stub — 뉴스 섹터 추출
=========================================
정율(Algo)이 제공하는 순수 함수 `extract_sectors`를 BE가 Django view에서
어떻게 호출하는지 보여주는 *통합 시작용 더미*다. (실제 Django 코드는 BE 담당)

핵심 계약:
  - Algo 입력: 뉴스 text(+summary), Stock 목록(StockRef)
  - Algo 출력: list[SectorTag]  → t.to_dict() 로 REST 직렬화
  - 뉴스 섹터는 별도 컬럼 없이 NewsRelatedStock → Stock.sector 로 역산 가능
    (이 함수는 '태깅 시점'에 어떤 종목/섹터를 달지 결정하는 용도)
"""

from __future__ import annotations

from news_sector import StockRef, extract_sectors


# --- BE가 채울 부분 (시그니처만; 실제 구현은 Django ORM) ---------------------- #
def _load_stock_refs() -> list[StockRef]:
    """BE: Stock.objects.values_list('code','name','sector') 로 1회 로드 후 캐시.

    여기선 더미. 실제:
        return [StockRef(c, n, s) for c, n, s in
                Stock.objects.values_list('code', 'name', 'sector')]
    """
    return [
        StockRef("005930", "삼성전자", "반도체"),
        StockRef("373220", "LG에너지솔루션", "2차전지"),
    ]


def tag_news_sectors(title: str, summary: str = "") -> list[dict]:
    """BE view에서 호출할 진입점. 뉴스 1건 → 섹터 태그 dict 리스트.

    BE 사용 예 (DRF):
        class NewsSectorView(APIView):
            def get(self, request, news_id):
                news = get_object_or_404(StockNews, pk=news_id)
                tags = tag_news_sectors(news.title)   # summary 컬럼 생기면 전달
                # tags 기반으로 NewsRelatedStock 저장 or 응답
                return Response(tags)
    """
    stocks = _load_stock_refs()
    tags = extract_sectors(title, stocks, summary=summary)
    return [t.to_dict() for t in tags]


if __name__ == "__main__":
    sample = "삼성전자·LG에너지솔루션 동반 상승…외국인 순매수"
    print(f"입력: {sample}")
    for tag in tag_news_sectors(sample):
        print(f"  → {tag}")
