"""네이버 검색 API 국장 종목 뉴스 + 본문 전체 데모 (독립 실행)
================================================================
종목을 '클릭'했다고 가정하고 네이버로 뉴스 검색 → 본문 전체까지 출력.

사전: 네이버 키 설정 (환경변수 NAVER_CLIENT_ID/SECRET 또는 naver_keys.local)
실행: python 610jy/demo_naver_news.py
"""

from __future__ import annotations

import sys

from naver_news import fetch_stock_articles, load_credentials

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TARGETS = ["삼성전자", "에코프로비엠", "로보스타"]   # 대형 + 중소형


if __name__ == "__main__":
    try:
        load_credentials()
    except RuntimeError as e:
        print(f"[키 없음] {e}")
        sys.exit(1)

    for name in TARGETS:
        print("=" * 76)
        print(f"[{name}] 클릭 → 네이버 뉴스")
        print("=" * 76)
        articles = fetch_stock_articles(name, display=30, sort="date", limit=4, body_limit=4)
        for i, a in enumerate(articles, 1):
            d = a.published_at.strftime("%m-%d %H:%M") if a.published_at else "?"
            print(f"\n{i}. {a.title}  ({d})")
            print(f"   원문: {a.origin_link}")
            print(f"   요약: {a.summary[:120]}")
            if a.body:
                print(f"   ── 본문 전체 ({len(a.body)}자) ──")
                print("   " + a.body[:600].replace("\n", "\n   "))
                if len(a.body) > 600:
                    print(f"   …(이하 {len(a.body) - 600}자 생략)")
            else:
                print("   (본문: 네이버 비호스팅 → 요약으로 대체)")
        print()

    print("[완료]")
