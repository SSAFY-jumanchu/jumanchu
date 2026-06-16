"""fetch_stock_news 실제 RSS 검증 데모 (독립 실행) — US-06 종목 상세 뉴스 탭
============================================================================
종목을 '클릭'했다고 가정하고, 그 종목 상세에 들어갈 뉴스 리스트를 뽑아 출력.

실행:  python 610jy/demo_stock_news.py
요구:  requests + stdlib. API 키 불필요.
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass

from stock_news import fetch_stock_news

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


@dataclass(frozen=True)
class DemoStock:
    """StockLike 더미 (실제론 Stock 모델 행)."""
    code: str
    name: str
    market: str


# 종목 클릭 시나리오 (국내 대형/중소형 + 해외)
CLICKED = [
    DemoStock("005930", "삼성전자", "KOSPI"),
    DemoStock("373220", "LG에너지솔루션", "KOSPI"),
    DemoStock("090360", "로보스타", "KOSDAQ"),
    DemoStock("AAPL", "Apple", "NASDAQ"),
]


if __name__ == "__main__":
    for stock in CLICKED:
        print("=" * 72)
        print(f"[{stock.name} ({stock.code}) · {stock.market}] 클릭 → 뉴스 탭")
        print("=" * 72)

        t0 = time.perf_counter()
        items = fetch_stock_news(stock, days=7, limit=8)
        dt = time.perf_counter() - t0

        if not items:
            print("  (뉴스 없음 / 화이트리스트·최근성 통과 0)\n")
        else:
            print(f"  {len(items)}건 · 수집 {dt:.2f}s\n")
            for i, it in enumerate(items, 1):
                d = it.published_at.strftime("%m-%d %H:%M") if it.published_at else "?"
                print(f"  {i}. {it.title}")
                print(f"     · {it.source}  |  {d}")
        print()
        time.sleep(1.0)

    print("[완료]")
