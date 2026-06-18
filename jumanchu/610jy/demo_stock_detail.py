"""US-06 종목 상세 통합 데모 — 종목 뉴스 + 테마(섹터) 뉴스
==========================================================
종목 클릭 시나리오로 fetch_stock_detail_news를 호출해 두 탭을 모두 출력.
국장(대형/중소형) + 미장 커버리지를 한 번에 검증.

실행:  python 610jy/demo_stock_detail.py
요구:  requests + stdlib. API 키 불필요.
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass

from stock_news import fetch_stock_detail_news

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


@dataclass(frozen=True)
class DemoStock:
    code: str
    name: str
    market: str
    sector: str   # 실제론 Stock.sector (KR=한글 / US=영문)


# 국장 대형 + 국장 중소형 + 미장 대형 + 미장(테마 다른 것)
CLICKED = [
    DemoStock("005930", "삼성전자", "KOSPI", "반도체"),
    DemoStock("247540", "에코프로비엠", "KOSDAQ", "2차전지"),
    DemoStock("AAPL", "Apple", "NASDAQ", "Technology"),
    DemoStock("TSLA", "Tesla", "NASDAQ", "Automobiles"),
]


def _print_list(title: str, items) -> None:
    print(f"  ── {title} ({len(items)}건) ─────────────────────────")
    if not items:
        print("      (없음)")
        return
    for i, it in enumerate(items, 1):
        d = it.published_at.strftime("%m-%d %H:%M") if it.published_at else "?"
        print(f"   {i}. {it.title}")
        print(f"      · {it.source}  |  {d}")


if __name__ == "__main__":
    for stock in CLICKED:
        scope = "국장" if stock.market in ("KOSPI", "KOSDAQ") else "미장"
        print("=" * 74)
        print(f"[{scope}] {stock.name} ({stock.code}) · {stock.market} · 섹터={stock.sector}")
        print("=" * 74)

        t0 = time.perf_counter()
        result = fetch_stock_detail_news(stock, days=7, limit=5)
        dt = time.perf_counter() - t0

        _print_list("종목 뉴스", result["stock_news"])
        _print_list("테마 뉴스", result["theme_news"])
        print(f"  (수집 {dt:.2f}s)\n")
        time.sleep(1.2)

    print("[완료]")
